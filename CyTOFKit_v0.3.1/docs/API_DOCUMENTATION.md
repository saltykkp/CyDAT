# API Documentation

## src.utils.data_loader
### `DataLoader`
Handles batch loading of CSV files.

- `load_directory(directory_path)`: Loads all `.csv` files from the specified directory. Checks for column consistency.
- `get_merged_data()`: Returns the concatenated DataFrame of all loaded files.
- `get_feature_data()`: Returns the DataFrame containing only feature columns (excluding metadata).

## src.analysis.clustering
### `ClusterManager`
Manages clustering operations.

- `__init__(data_loader)`: Initializes with a DataLoader instance.
- `preprocess()`: Standardizes the data (StandardScaler).
- `run_kmeans(n_clusters, max_iter, random_state)`: Executes KMeans clustering.
- `run_phenograph(k, metric, random_state)`: Executes Phenograph clustering.
- `save_results(output_dir)`: Saves individual and combined CSVs with cluster labels.

## src.analysis.dim_reduction
### `DimReductionManager`
Manages dimensionality reduction.

- `__init__(data_loader)`: Initializes with a DataLoader instance.
- `run_tsne(perplexity, learning_rate, n_iter)`: Computes t-SNE embedding.
- `run_umap(n_neighbors, min_dist, metric)`: Computes UMAP embedding.

## src.analysis.visualization
### `Visualizer`
Static utilities for plotting.

- `plot_heatmap(data, labels, feature_names, output_path)`: Generates and saves a hierarchical clustering heatmap.
- `plot_embedding_2d(embedding, labels, output_path)`: Generates and saves a 2D scatter plot colored by cluster.
- `plot_embedding_3d(embedding, labels, output_path)`: Generates and saves a 3D scatter plot.

## src.gui
### `MainWindow`
The main application window (PyQt6).
- Orchestrates the flow between tabs and backend logic.
- Manages `AnalysisWorker` threads to keep UI responsive.
