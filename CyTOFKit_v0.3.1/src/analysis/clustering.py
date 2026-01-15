import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings

# Try importing phenograph
try:
    import phenograph
    PHENOGRAPH_AVAILABLE = True
except ImportError:
    PHENOGRAPH_AVAILABLE = False

try:
    import anndata as ad
    from flowsom import FlowSOM
    FLOWSOM_AVAILABLE = True
except ImportError:
    FLOWSOM_AVAILABLE = False

class ClusterManager:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.labels = None
        self.scaled_data = None
        self.cluster_centers = None

    def preprocess(self):
        """Standardize the data before clustering"""
        data = self.data_loader.get_feature_data()
        if data is None:
            raise ValueError("No data loaded")
        
        scaler = StandardScaler()
        self.scaled_data = scaler.fit_transform(data)
        return self.scaled_data

    def run_kmeans(self, n_clusters=10, max_iter=300, random_state=42):
        if self.scaled_data is None:
            self.preprocess()
            
        kmeans = KMeans(n_clusters=n_clusters, max_iter=max_iter, random_state=random_state, n_init=10)
        self.labels = kmeans.fit_predict(self.scaled_data) + 1 # Start from 1
        self.cluster_centers = kmeans.cluster_centers_
        return self.labels

    def run_phenograph(self, k=30, metric='euclidean', random_state=None):
        if not PHENOGRAPH_AVAILABLE:
            raise ImportError("Phenograph is not installed. Please install it to use this feature.")
            
        if self.scaled_data is None:
            self.preprocess()

        # Phenograph implementation
        # Note: phenograph.cluster returns (communities, graph, Q)
        # We handle random_state if possible, but standard phenograph might not expose it directly in all versions,
        # usually it uses numpy seed.
        if random_state is not None:
            np.random.seed(random_state)
            
        communities, _, _ = phenograph.cluster(self.scaled_data, k=k, metric=metric)
        self.labels = communities + 1 # Start from 1
        return self.labels

    def run_flowsom(self, n_clusters=10, xdim=10, ydim=10, rlen=10, seed=None):
        if not FLOWSOM_AVAILABLE:
            raise ImportError("flowsom is not installed. Please install it to use this feature.")

        if self.scaled_data is None:
            self.preprocess()

        adata = ad.AnnData(self.scaled_data)
        feature_data = self.data_loader.get_feature_data()
        if feature_data is not None:
            try:
                adata.var_names = feature_data.columns.astype(str)
            except Exception:
                pass

        FlowSOM(adata, n_clusters=int(n_clusters), xdim=int(xdim), ydim=int(ydim), rlen=int(rlen), seed=None if seed in (None, "") else int(seed))
        if "metaclustering" not in adata.obs:
            raise RuntimeError("FlowSOM did not produce metaclustering labels.")

        self.labels = adata.obs["metaclustering"].to_numpy() + 1
        return self.labels

    def get_results_df(self):
        """Returns the merged dataframe with cluster labels"""
        if self.labels is None:
            return None
        
        df = self.data_loader.get_merged_data().copy()
        df.insert(0, 'cluster_label', self.labels)
        return df

    def get_cluster_marker_means_df(self):
        """
        Returns a DataFrame where rows are cluster labels and columns are markers/features,
        values are the mean expression per cluster.
        """
        if self.labels is None:
            return None

        feature_df = self.data_loader.get_feature_data()
        if feature_df is None:
            raise ValueError("No feature data loaded")

        if len(feature_df) != len(self.labels):
            raise ValueError("Feature data rows do not match label length")

        df = feature_df.copy()
        df.insert(0, "cluster_label", self.labels)
        means = df.groupby("cluster_label").mean(numeric_only=True)
        means.index = means.index.astype(int, copy=False)
        means = means.sort_index()
        means.index.name = "cluster_label"
        return means

    def save_cluster_marker_means(self, output_dir, filename="cluster_marker_means.csv"):
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        means = self.get_cluster_marker_means_df()
        if means is None:
            raise ValueError("No clustering results to summarize")

        output_path = out_path / filename
        means.to_csv(output_path, index=True)
        return str(output_path)

    def save_results(self, output_dir):
        """
        Save results as per requirements:
        1. Individual CSVs with cluster label
        2. Merged CSV
        """
        import os
        from pathlib import Path
        
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        full_df = self.get_results_df()
        if full_df is None:
            raise ValueError("No results to save")
            
        # Save merged
        full_df.to_csv(out_path / "combined_results.csv", index=False)
        
        # Save individual
        grouped = full_df.groupby('_file_id')
        for file_id, group in grouped:
            # Remove internal columns
            save_df = group.drop(columns=['_file_id', '_original_index'])
            save_df.to_csv(out_path / f"{file_id}_clustered.csv", index=False)
            
        return str(out_path)
