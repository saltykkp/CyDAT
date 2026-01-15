import pandas as pd
from pathlib import Path
from datetime import datetime
import os

class CsvSplitter:
    def __init__(self):
        self.df = None
        self.file_path = None
        self.folder_path = None
        self.folder_files = None
        self.folder_special_col = None

    def load_file(self, file_path):
        """
        Load a CSV file.
        """
        self.file_path = file_path
        try:
            self.df = pd.read_csv(file_path)
            return True, f"Successfully loaded {Path(file_path).name}"
        except Exception as e:
            return False, str(e)

    def load_folder(self, folder_path):
        folder = Path(folder_path)
        csv_files = list(folder.glob("*.csv"))
        if not csv_files:
            return False, "No CSV files found in the folder.", None, None, None

        is_consistent, msg, common_columns = self.check_folder_consistency(folder_path)
        if not is_consistent:
            return False, msg, None, None, None

        self.folder_path = str(folder)
        self.folder_files = csv_files

        columns_set = {str(c).strip().lower() for c in common_columns}
        if "cluster_label" in columns_set:
            self.folder_special_col = next(c for c in common_columns if str(c).strip().lower() == "cluster_label")
        elif "cell_type" in columns_set:
            self.folder_special_col = next(c for c in common_columns if str(c).strip().lower() == "cell_type")
        else:
            self.folder_special_col = None

        preview_df = pd.read_csv(csv_files[0]).head(100)

        row_options = {}
        if self.folder_special_col is not None:
            values = set()
            for f in csv_files:
                s = pd.read_csv(f, usecols=[self.folder_special_col])[self.folder_special_col]
                values.update(set(s.dropna().astype(str).unique().tolist()))
            for v in values:
                row_options[str(v)] = str(v)

        return True, msg, preview_df, row_options, list(common_columns)

    def check_folder_consistency(self, folder_path):
        """
        Check if all CSV files in the folder have the same columns.
        Returns (is_consistent, message, common_columns)
        """
        folder = Path(folder_path)
        csv_files = list(folder.glob("*.csv"))
        
        if not csv_files:
            return False, "No CSV files found in the folder.", None

        first_file = csv_files[0]
        try:
            first_cols = set(pd.read_csv(first_file, nrows=0).columns)
        except Exception as e:
            return False, f"Error reading {first_file.name}: {e}", None

        for f in csv_files[1:]:
            try:
                cols = set(pd.read_csv(f, nrows=0).columns)
                if cols != first_cols:
                    return False, f"Column mismatch in {f.name}", None
            except Exception as e:
                return False, f"Error reading {f.name}: {e}", None

        return True, "All CSV files have consistent columns.", list(first_cols)

    def split_csv(self, row_indices, col_indices, output_base_dir):
        if self.df is None:
            raise ValueError("No CSV file loaded.")

        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = Path(output_base_dir) / "csv_proc" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        if row_indices is None:
            subset = self.df
        else:
            valid_rows = [r for r in row_indices if 0 <= r < len(self.df)]
            subset = self.df.iloc[valid_rows]
            
        if col_indices is not None:
             valid_cols = [c for c in col_indices if c in self.df.columns]
             subset = subset[valid_cols]
             
        output_filename = f"split_{Path(self.file_path).stem}.csv"
        output_path = output_dir / output_filename
        subset.to_csv(output_path, index=False)
        return str(output_path)

    def split_folder(self, row_values, col_indices, folder_path, output_base_dir):
        folder = Path(folder_path)
        csv_files = list(folder.glob("*.csv"))
        if not csv_files:
            raise ValueError("No CSV files found in the folder.")

        is_consistent, msg, common_columns = self.check_folder_consistency(folder_path)
        if not is_consistent:
            raise ValueError(msg)

        columns_set = {str(c).strip().lower() for c in common_columns}
        if "cluster_label" in columns_set:
            special_col = next(c for c in common_columns if str(c).strip().lower() == "cluster_label")
        elif "cell_type" in columns_set:
            special_col = next(c for c in common_columns if str(c).strip().lower() == "cell_type")
        else:
            special_col = None

        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = Path(output_base_dir) / "csv_proc" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        valid_cols = [c for c in col_indices if c in common_columns]
        if not valid_cols:
            raise ValueError("No valid columns selected.")

        selected_values = None
        if row_values is not None:
            selected_values = {str(v) for v in row_values}

        out_paths = []
        for f in csv_files:
            df = pd.read_csv(f)
            if special_col is not None and selected_values is not None:
                df = df[df[special_col].fillna("").astype(str).isin(selected_values)]
            df = df[valid_cols]
            out_path = output_dir / f"split_{f.stem}.csv"
            df.to_csv(out_path, index=False)
            out_paths.append(str(out_path))

        return out_paths

    def get_split_criteria(self):
        """
        Analyze the loaded DF to determine available row splitting criteria.
        If 'cluster_label' or 'cell_type' exists, use it as row index source.
        Otherwise, return None or range.
        
        Returns: 
            row_options: dict {label: [indices]}
            col_options: list of column names
        """
        if self.df is None:
            return {}, []

        col_options = list(self.df.columns)
        row_options = {}

        # Check for specific columns for row indexing
        target_cols = ['cluster_label', 'cell_type']
        found_col = None
        for col in target_cols:
            if col in self.df.columns:
                found_col = col
                break
        
        if found_col:
            # Group by this column
            groups = self.df.groupby(found_col).groups
            # groups is a dict {value: Index([...])}
            # Convert Index to list
            for key, val in groups.items():
                row_options[str(key)] = val.tolist()
        else:
            # If no special column, maybe just offer range or all?
            # Requirement says: "If exists... use data as row index; otherwise..." 
            # It implies we use the column values to categorize rows.
            # If not present, maybe we don't offer categorical split, or just raw indices?
            # The prompt says: "If 'cluster_label' or 'cell_type' exists... use as row index"
            # It doesn't explicitly say what to do if NOT exists for row selection specifically, 
            # other than "for other columns, use title as col index".
            # I will assume if not present, we treat the whole file as one group or handle generic index.
            pass

        return row_options, col_options


class CsvMapper:
    def __init__(self):
        pass

    def _normalize_cols(self, cols):
        return {str(c).strip().lower(): c for c in cols}

    def _load_mapping(self, mapping_csv_path):
        mapping_df = pd.read_csv(mapping_csv_path)
        if mapping_df.shape[1] < 2:
            raise ValueError("Mapping CSV must have at least 2 columns.")

        norm = self._normalize_cols(mapping_df.columns)
        if "cluster_label" in norm and "cell_type" in norm:
            kcol = norm["cluster_label"]
            vcol = norm["cell_type"]
        else:
            kcol = mapping_df.columns[0]
            vcol = mapping_df.columns[1]

        keys = mapping_df[kcol].astype(str)
        vals = mapping_df[vcol].astype(str)
        return dict(zip(keys.tolist(), vals.tolist()))

    def map_folder(self, folder_path, mapping_csv_path):
        folder = Path(folder_path)
        csv_files = list(folder.glob("*.csv"))
        if not csv_files:
            raise ValueError("No CSV files found in the folder.")

        mapping = self._load_mapping(mapping_csv_path)
        mapping_path = Path(mapping_csv_path).resolve()
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        output_dir = folder / "anno_result" / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        out_paths = []
        for f in csv_files:
            if f.resolve() == mapping_path:
                continue
            df = pd.read_csv(f)
            norm = self._normalize_cols(df.columns)
            if "cluster_label" not in norm:
                raise ValueError(f"Missing cluster_label in {f.name}")
            cl_col = norm["cluster_label"]
            if "cell_type" in norm:
                df = df.drop(columns=[norm["cell_type"]])

            original = df[cl_col].astype(str)
            mapped = original.map(mapping)
            mapped = mapped.where(~mapped.isna(), original)

            insert_pos = list(df.columns).index(cl_col)
            df = df.drop(columns=[cl_col])
            df.insert(insert_pos, "cell_type", mapped)

            out_path = output_dir / f.name
            df.to_csv(out_path, index=False)
            out_paths.append(str(out_path))

        return str(output_dir), out_paths
