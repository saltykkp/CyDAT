# CyDAT (CyTOFKit_v02)

High-dimensional single-cell CyTOF data analysis desktop app (PyQt6).

## Features
- Clustering Analysis: KMeans / Phenograph (optional) / FlowSOM (flowsom)
- Dim Reduction & Visualization: t-SNE / UMAP (supports custom CSV input)
- CSV Processor:
  - CSV Splitter: split one CSV or a folder of CSVs by selected rows/columns
  - CSV Mapper: map `cluster_label` → `cell_type` using a mapping CSV (batch over a folder)
- Difference Analysis:
  - Percentage Stacked Bar Chart: compare sample `cell_type` composition across a folder of CSVs

## Quick Start
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
   Notes:
   - Phenograph is optional and may require platform-specific installation.

2. Run the application
   ```bash
   python src/main.py
   ```

## Input Data Conventions
- Each sample is a `.csv` file. When loading a folder, all CSVs should share the same columns.
- Clustering uses numeric marker columns (feature columns). Reserved columns are `cluster_label` and `cell_type`.
- CSV Mapper expects:
  - Input CSVs contain a `cluster_label` column (case-insensitive).
  - Mapping CSV contains `cluster_label` and `cell_type` columns (case-insensitive), or the first two columns are used.
- Difference Analysis (Percentage Stacked Bar Chart) expects `cell_type` in each CSV (case-insensitive).

## Outputs (Summary)
- Clustering:
  - `results/cluster_results/<timestamp>/combined_results.csv`
  - `results/cluster_results/<timestamp>/heatmap.png`
  - `results/cluster_results/<timestamp>/cluster_marker_means.csv`
- CSV Splitter:
  - `csv_proc/<timestamp>/split_<filename>.csv`
- CSV Mapper:
  - `anno_result/<timestamp>/<filename>.csv` (with `cell_type` column)
- Difference Analysis:
  - `Difference Analysis/Percentage Stacked Bar Chart/<timestamp>/percentage_stacked_bar_chart.png`

## Documentation
- User Manual: [docs/USER_MANUAL.md](docs/USER_MANUAL.md)
- API Documentation: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

## Requirements
- Python 3.13+
- Windows/macOS/Linux (tested mainly on Windows)
