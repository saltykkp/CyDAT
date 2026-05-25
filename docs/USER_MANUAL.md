# CyTOF Data Analysis Software - User Manual

## Introduction
This software is designed for high-dimensional single-cell CyTOF data analysis, providing clustering and dimensionality reduction visualization capabilities.

## Features
- **Clustering Analysis**: Support for KMeans / Phenograph (optional) / FlowSOM (flowsom).
- **Utils**:
  - CSV Splitter: split CSV by selected rows/columns (single file or folder batch).
  - CSV Mapper: map `cluster_label` to `cell_type` using a mapping CSV (folder batch).
  - Arcsinh: batch-apply `arcsinh(x / 5)` to all non-label columns in a folder of CSV files.
- **Heatmap**: Support for independent heatmap generation from clustering results or a custom CSV.
- **Dim Reduction & Visualization**: Support for t-SNE and UMAP (supports custom CSV), with PNG preview and saved outputs.
- **Difference Analysis**:
  - Percentage Stacked Bar Chart: compare `cell_type` composition across samples.

## Installation
1. Ensure Python 3.13 is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Notes:
   - Phenograph is optional and may require platform-specific installation.
   - FlowSOM requires `flowsom` and `anndata` (already included in requirements.txt).

## Usage Guide

### Starting the Application
Run the main script:
```bash
python src/main.py
```

### Module 1: Clustering Analysis
1. **Select Data**: Click "Select Folder" to choose a directory containing your CSV files.
2. **Choose Algorithm**: Select "KMeans", "Phenograph" (optional) or "FlowSOM" from the dropdown.
3. **Configure Parameters**:
   - For KMeans: Adjust Clusters (n), Max Iterations, Random Seed.
   - For Phenograph: Adjust Neighbors (k), Metric, Louvain Time Limit (s), Random Seed.
   - For FlowSOM: Adjust Metaclusters (n), Grid xdim/ydim, Training iters (rlen), Seed.
   - Choose a heatmap palette for the clustering heatmap output: `Blue to Red`, `Viridis`, `Plasma`, `Cividis`, `Coolwarm`, `RdYlBu`, `RdBu`, `YlOrRd`, `YlGnBu`, or `Turbo`.
4. **Run**: Click "Run Clustering".
5. **Results**:
   - Progress bar shows status.
   - Heatmap preview appears upon completion.
   - Results are saved under `results/cluster_results/<timestamp>/` within your input directory:
     - `combined_results.csv`
     - `*_clustered.csv` for each input file
     - `heatmap.png`
     - `cluster_marker_means.csv` (mean expression per cluster for each marker)

### Module 2: Dim Reduction & Visualization
Prerequisite: You must run Clustering first to generate labels, or select a custom CSV file.
Labels are automatically read from `batch_label`, `cell_type`, `cluster`, `cluster_label`, or `label` when available.
1. **Choose Algorithm**: Select "t-SNE" or "UMAP".
2. **Configure Parameters**:
   - t-SNE: Perplexity, Learning Rate, Iterations.
   - UMAP: Neighbors, Min Distance, Metric.
3. **Run**: Click "Run Visualization".
4. **Results**:
   - Scatter plot preview appears.
   - Outputs:
     - PNG plot: `results/vis_results/<timestamp>/` (or `vis_results/<timestamp>/` when using a custom CSV)
     - Coordinate CSV: `<algo>_coordinates.csv`
     - If the label used for visualization is `batch_label`, additional highlight plots are saved in `<algo>_batch_label_highlights/`, where only one batch is colored and all other cells are shown in gray for each output image.

### Module 3: Heatmap
Prerequisite: Run Clustering first to reuse the current clustering results, or select a custom CSV file.
1. **Select Data Source**:
   - Leave the default option to use the current clustering results.
   - Or select a custom CSV file that contains numeric marker columns.
2. **Select Palette**: Choose one of `Blue to Red`, `Viridis`, `Plasma`, `Cividis`, `Coolwarm`, `RdYlBu`, `RdBu`, `YlOrRd`, `YlGnBu`, or `Turbo`.
3. **Run**: Click **Generate Heatmap**.
4. **Results**:
   - Heatmap preview appears on the right panel.
   - Outputs:
     - `results/heatmap_results/<timestamp>/heatmap.png` when using current clustering results
     - `heatmap_results/<timestamp>/heatmap.png` when using a custom CSV

### Module 4: Utils
The Utils module provides three modes (select from the Mode dropdown).

#### Mode: CSV Splitter
1. Choose **CSV Splitter** mode.
2. Select a CSV file or a folder of CSV files.
3. Select row groups (based on `cluster_label` or `cell_type` if present) and select columns.
4. Click **Run Processing**.
5. Outputs:
   - `csv_proc/<timestamp>/split_<filename>.csv` (for each processed file)

#### Mode: CSV Mapper
1. Choose **CSV Mapper** mode.
2. Select the folder containing the CSVs to be mapped.
3. Select the mapping CSV:
   - recommended columns: `cluster_label`, `cell_type` (case-insensitive)
4. Click **Run Mapping**.
5. Outputs:
   - `anno_result/<timestamp>/<filename>.csv` (the `cluster_label` column is mapped and renamed to `cell_type`)

#### Mode: Arcsinh
1. Choose **Arcsinh** mode.
2. Select a folder containing CSV files.
3. Click **Run Arcsinh**.
4. Processing rule:
   - Apply `arcsinh(x / 5)` to every non-label column.
   - Label columns such as `cluster_label`, `cell_type`, `batch_label`, `cluster`, and `label` are kept unchanged.
5. Outputs:
   - `arcsinh_result/<timestamp>/<filename>.csv`

### Module 5: Difference Analysis
The Difference Analysis module supports multiple modes (via Mode dropdown). Currently implemented:

#### Mode: Percentage Stacked Bar Chart
1. Select a folder containing multiple sample CSV files.
2. Each CSV must contain a `cell_type` column (case-insensitive).
3. Click **Run Difference Analysis**.
4. Results:
   - Preview: percentage stacked bar chart displayed on the right panel.
   - Output PNG saved to:
     - `Difference Analysis/Percentage Stacked Bar Chart/<timestamp>/percentage_stacked_bar_chart.png`

## Output Files
- `combined_results.csv`: Merged data with `cluster_label`.
- `[filename]_clustered.csv`: Individual files with labels.
- `heatmap.png`: Hierarchical clustering heatmap.
- `results/heatmap_results/<timestamp>/heatmap.png`: Independent heatmap output from the Heatmap module.
- `[algorithm]_plot.png`: Dimensionality reduction plot.
- `cluster_marker_means.csv`: Mean marker expression per cluster.
- `csv_proc/<timestamp>/split_<filename>.csv`: CSV Splitter outputs.
- `anno_result/<timestamp>/<filename>.csv`: CSV Mapper outputs.
- `arcsinh_result/<timestamp>/<filename>.csv`: Arcsinh outputs.
- `Difference Analysis/Percentage Stacked Bar Chart/<timestamp>/percentage_stacked_bar_chart.png`: Difference Analysis output.

## Performance
- Optimized for datasets with 100k+ cells.
- Downsampling is automatically applied for visualization if data exceeds limits, while full data is preserved in CSV outputs.
