import pandas as pd
from pathlib import Path
import os

class DataLoader:
    def __init__(self):
        self.data_map = {}  # filename -> dataframe
        self.merged_data = None
        self.feature_columns = None
        self.filenames = []

    def _is_reserved_column(self, column_name: str) -> bool:
        return column_name.strip().lower() in {"cluster_label", "cell_type"}

    def load_directory(self, directory_path):
        """
        Load all CSV files from a directory.
        Checks for consistency in columns.
        """
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")

        csv_files = list(directory.glob("*.csv"))
        if not csv_files:
            raise ValueError(f"No CSV files found in {directory_path}")

        self.data_map = {}
        self.filenames = []
        first_columns = None
        
        all_dfs = []

        for file_path in csv_files:
            try:
                df = pd.read_csv(file_path)
                
                # Check columns consistency
                current_columns = list(df.columns)
                if first_columns is None:
                    first_columns = current_columns
                else:
                    if current_columns != first_columns:
                        raise ValueError(f"Column mismatch in file {file_path.name}. Expected {first_columns}, got {current_columns}")
                
                file_id = file_path.stem
                self.filenames.append(file_id)
                self.data_map[file_id] = df
                
                # Add identifier for merging
                df_copy = df.copy()
                df_copy['_file_id'] = file_id
                df_copy['_original_index'] = df.index
                all_dfs.append(df_copy)
                
            except Exception as e:
                raise ValueError(f"Error reading {file_path.name}: {str(e)}")

        self.feature_columns = [c for c in first_columns if not self._is_reserved_column(c)]
        self.merged_data = pd.concat(all_dfs, ignore_index=True)
        
        return self.filenames, self.feature_columns

    def get_merged_data(self):
        return self.merged_data

    def get_feature_data(self):
        if self.merged_data is not None:
            feature_columns = [c for c in self.feature_columns if not self._is_reserved_column(c)]
            return self.merged_data[feature_columns]
        return None
