# CyTOF Data Analysis Software - User Manual

## Introduction
This software is designed for high-dimensional single-cell CyTOF data analysis, providing clustering and dimensionality reduction visualization capabilities.

## Features
- **Clustering Analysis**: Support for KMeans / Phenograph (optional) / FlowSOM (flowsom).
- **Dimensionality Reduction**: Support for t-SNE and UMAP (supports custom CSV).
- **Visualization**: Heatmap and 2D embedding plots (PNG preview and saved outputs).
- **CSV Processor**:
  - CSV Splitter: split CSV by selected rows/columns (single file or folder batch).
  - CSV Mapper: map `cluster_label` to `cell_type` using a mapping CSV (folder batch).
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
   - For Phenograph: Adjust Neighbors (k), Metric, Random Seed.
   - For FlowSOM: Adjust Metaclusters (n), Grid xdim/ydim, Training iters (rlen), Seed.
4. **Run**: Click "Run Clustering".
5. **Results**:
   - Progress bar shows status.
   - Heatmap preview appears upon completion.
   - Results are saved under `results/cluster_results/<timestamp>/` within your input directory:
     - `combined_results.csv`
     - `*_clustered.csv` for each input file
     - `heatmap.png`
     - `cluster_marker_means.csv` (mean expression per cluster for each marker)

### Module 2: Dimensionality Reduction & Visualization
Prerequisite: You must run Clustering first to generate labels, or select a custom CSV file.
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

### Module 3: CSV Processor
The CSV Processor provides two modes (select from the Mode dropdown).

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

### Module 4: Difference Analysis
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
- `[algorithm]_plot.png`: Dimensionality reduction plot.
- `cluster_marker_means.csv`: Mean marker expression per cluster.
- `csv_proc/<timestamp>/split_<filename>.csv`: CSV Splitter outputs.
- `anno_result/<timestamp>/<filename>.csv`: CSV Mapper outputs.
- `Difference Analysis/Percentage Stacked Bar Chart/<timestamp>/percentage_stacked_bar_chart.png`: Difference Analysis output.

## Performance
- Optimized for datasets with 100k+ cells.
- Downsampling is automatically applied for visualization if data exceeds limits, while full data is preserved in CSV outputs.
