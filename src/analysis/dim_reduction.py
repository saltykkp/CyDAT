import numpy as np
from sklearn.manifold import TSNE
import umap
from sklearn.preprocessing import StandardScaler

class DimReductionManager:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.embedding = None
        self.scaled_data = None
        self.custom_data = None

    def set_custom_data(self, data):
        """Set custom data for analysis, bypassing data_loader"""
        self.custom_data = data
        self.scaled_data = None # Reset scaled data

    def preprocess(self):
        if self.custom_data is not None:
            data = self.custom_data
        else:
            data = self.data_loader.get_feature_data()
            
        if data is None:
            raise ValueError("No data loaded")
        
        scaler = StandardScaler()
        self.scaled_data = scaler.fit_transform(data)
        return self.scaled_data

    def run_tsne(self, perplexity=30, learning_rate=200.0, n_iter=1000, random_state=42):
        if self.scaled_data is None:
            self.preprocess()
            
        # Note: scikit-learn uses max_iter instead of n_iter in newer versions
        tsne = TSNE(n_components=2, perplexity=perplexity, learning_rate=learning_rate, 
                    max_iter=n_iter, random_state=random_state, init='pca', verbose=1)
        self.embedding = tsne.fit_transform(self.scaled_data)
        return self.embedding

    def run_umap(self, n_neighbors=15, min_dist=0.1, metric='euclidean', random_state=42):
        if self.scaled_data is None:
            self.preprocess()
            
        reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=min_dist, metric=metric, 
                            random_state=random_state, verbose=True)
        self.embedding = reducer.fit_transform(self.scaled_data)
        return self.embedding

    def run_3d_reduction(self, method='tsne', **kwargs):
        """Helper for 3D reduction if needed, though requirements say 2D/3D visualization, usually implies 3D coords"""
        if self.scaled_data is None:
            self.preprocess()
            
        if method == 'tsne':
            tsne = TSNE(n_components=3, **kwargs)
            self.embedding = tsne.fit_transform(self.scaled_data)
        elif method == 'umap':
            reducer = umap.UMAP(n_components=3, **kwargs)
            self.embedding = reducer.fit_transform(self.scaled_data)
            
        return self.embedding
