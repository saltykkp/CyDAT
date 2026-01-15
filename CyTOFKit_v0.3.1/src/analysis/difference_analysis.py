from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.analysis.visualization import Visualizer


@dataclass(frozen=True)
class DifferenceAnalysisResult:
    output_dir: Path
    plot_path: Path
    percentages: pd.DataFrame


class DifferenceAnalyzer:
    def __init__(self):
        pass

    @staticmethod
    def _find_cell_type_column(columns) -> str | None:
        lower_to_original = {str(c).strip().lower(): c for c in columns}
        if "cell_type" in lower_to_original:
            return lower_to_original["cell_type"]
        return None

    def compute_cell_type_percentages(self, input_dir: str | Path) -> pd.DataFrame:
        input_dir = Path(input_dir)
        csv_files = sorted(input_dir.glob("*.csv"))
        if not csv_files:
            raise ValueError("No CSV files found in the selected folder.")

        rows = []
        all_cell_types = set()
        for f in csv_files:
            df = pd.read_csv(f)
            col = self._find_cell_type_column(df.columns)
            if col is None:
                raise ValueError(f"Missing 'cell_type' column in {f.name}")

            s = df[col].fillna("Unknown").astype(str)
            pct = s.value_counts(normalize=True, dropna=False) * 100.0
            all_cell_types.update(pct.index.tolist())
            rows.append((f.stem, pct))

        all_cell_types = sorted(all_cell_types)
        out = pd.DataFrame(index=[name for name, _ in rows], columns=all_cell_types, dtype=float)
        out.index.name = "sample"
        for name, pct in rows:
            out.loc[name, pct.index.tolist()] = pct.values
        out = out.fillna(0.0)
        return out

    def run_percentage_stacked_bar_chart(self, input_dir: str | Path) -> DifferenceAnalysisResult:
        input_dir = Path(input_dir)
        percentages = self.compute_cell_type_percentages(input_dir)

        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = input_dir / "Difference Analysis" / "Percentage Stacked Bar Chart" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        plot_path = output_dir / "percentage_stacked_bar_chart.png"
        Visualizer.plot_percentage_stacked_bar_chart(percentages, str(plot_path))

        return DifferenceAnalysisResult(
            output_dir=output_dir,
            plot_path=plot_path,
            percentages=percentages,
        )

