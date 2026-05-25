from pathlib import Path

import numpy as np
import pandas as pd

from src.analysis.visualization import Visualizer


class HeatmapGenerator:
    """Prepare heatmap inputs and delegate rendering to the visualizer."""

    LABEL_CANDIDATES = ("batch_label", "cell_type", "cluster_label", "cluster", "label")
    EXCLUDED_COLUMNS = {"_file_id", "_original_index"}

    def generate_from_dataframe(self, feature_df, labels, output_path, cmap="Spectral_r"):
        if feature_df is None or len(feature_df) == 0:
            raise ValueError("No data available for heatmap generation.")

        if labels is None:
            raise ValueError("No labels available for heatmap generation.")

        labels_array = np.asarray(labels)
        if len(feature_df) != len(labels_array):
            raise ValueError("Feature rows do not match label length.")

        numeric_df = feature_df.select_dtypes(include=[np.number]).copy()
        if numeric_df.empty:
            raise ValueError("No numeric feature columns available for heatmap generation.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        Visualizer.plot_heatmap(
            numeric_df.to_numpy(),
            labels_array,
            numeric_df.columns.tolist(),
            str(output_path),
            cmap=cmap,
        )
        return str(output_path)

    def generate_from_csv(self, csv_path, output_path, cmap="Spectral_r"):
        csv_path = Path(csv_path)
        if not csv_path.is_file():
            raise ValueError(f"CSV file not found: {csv_path}")

        df = pd.read_csv(csv_path)
        if df.empty:
            raise ValueError("Selected CSV is empty.")

        lower_to_original = {str(col).strip().lower(): col for col in df.columns}
        label_col = next(
            (lower_to_original[name] for name in self.LABEL_CANDIDATES if name in lower_to_original),
            None,
        )

        numeric_df = df.drop(
            columns=[col for col in self.EXCLUDED_COLUMNS if col in df.columns],
            errors="ignore",
        )
        if label_col is not None:
            labels = df[label_col].fillna("Unknown").to_numpy()
            numeric_df = numeric_df.drop(columns=[label_col], errors="ignore")
        else:
            # Without a grouping column, a heatmap per row is not meaningful and can
            # explode memory during hierarchical clustering. Fall back to one summary row.
            labels = np.repeat("All Cells", len(df))

        numeric_df = numeric_df.select_dtypes(include=[np.number]).copy()
        if numeric_df.empty:
            raise ValueError("No numeric feature columns found in the selected CSV.")

        return self.generate_from_dataframe(numeric_df, labels, output_path, cmap=cmap)
