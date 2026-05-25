from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QMessageBox, QStatusBar, QLabel)
import os
import pandas as pd
import numpy as np
from pathlib import Path
from src.app_info import APP_NAME, APP_VERSION_LABEL
from src.gui.tabs import ClusteringTab, DimReductionTab, HeatmapTab, CsvProcessorTab, DifferenceAnalysisTab
from src.gui.workers import AnalysisWorker
from src.utils.data_loader import DataLoader
from src.utils.output_paths import create_unique_output_dir
from src.analysis.clustering import ClusterManager
from src.analysis.dim_reduction import DimReductionManager
from src.analysis.heatmap import HeatmapGenerator
from src.analysis.visualization import Visualizer
from src.analysis.csv_processor import CsvSplitter, CsvMapper, ArcsinhTransformer
from src.analysis.difference_analysis import DifferenceAnalyzer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        
        # State
        self.data_loader = DataLoader()
        self.cluster_manager = ClusterManager(self.data_loader)
        self.dim_manager = DimReductionManager(self.data_loader)
        self.heatmap_generator = HeatmapGenerator()
        self.csv_splitter = CsvSplitter()
        self.csv_mapper = CsvMapper()
        self.arcsinh_transformer = ArcsinhTransformer(cofactor=5.0)
        self.difference_analyzer = DifferenceAnalyzer()
        self.output_dir = None
        
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.clustering_tab = ClusteringTab()
        self.clustering_tab.run_analysis_signal.connect(self.start_clustering)
        self.clustering_tab.stop_analysis_signal.connect(self.stop_analysis)
        
        self.csv_tab = CsvProcessorTab()
        self.csv_tab.run_process_signal.connect(self.handle_csv_process)

        self.heatmap_tab = HeatmapTab()
        self.heatmap_tab.run_analysis_signal.connect(self.start_heatmap_generation)
        self.heatmap_tab.stop_analysis_signal.connect(self.stop_analysis)

        self.dim_tab = DimReductionTab()
        self.dim_tab.run_analysis_signal.connect(self.start_visualization)
        self.dim_tab.stop_analysis_signal.connect(self.stop_analysis)

        self.diff_tab = DifferenceAnalysisTab()
        self.diff_tab.run_analysis_signal.connect(self.start_difference_analysis)
        
        self.tabs.addTab(self.clustering_tab, "Clustering Analysis")
        self.tabs.addTab(self.dim_tab, "Dim Reduction && Visualization")
        self.tabs.addTab(self.heatmap_tab, "Heatmap")
        self.tabs.addTab(self.csv_tab, "Utils")
        self.tabs.addTab(self.diff_tab, "Difference Analysis")
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        self.version_label = QLabel(APP_VERSION_LABEL)
        self.version_label.setStyleSheet("color: #888; padding-left: 8px;")
        self.status_bar.addPermanentWidget(self.version_label)

    def start_clustering(self, config):
        self.clustering_tab.run_btn.setEnabled(False)
        self.clustering_tab.stop_btn.setEnabled(True)
        self.clustering_tab.progress.setRange(0, 0) # Indeterminate
        self.clustering_tab.update_log("Starting clustering analysis...")
        
        worker = AnalysisWorker(self.run_clustering_logic, config)
        worker.result.connect(self.on_clustering_finished)
        worker.error.connect(self.on_clustering_error)
        worker.finished.connect(lambda: self.clustering_tab.run_btn.setEnabled(True))
        worker.finished.connect(lambda: self.clustering_tab.stop_btn.setEnabled(False))
        worker.finished.connect(lambda: self.clustering_tab.progress.setRange(0, 100))
        worker.finished.connect(lambda: self.clustering_tab.progress.setValue(100))
        worker.start()
        self.worker = worker # Keep reference

    def run_clustering_logic(self, config):
        input_dir = config['input_dir']
        heatmap_cmap = config.get('heatmap_cmap', 'Spectral_r')
        
        # 1. Load Data
        if not self.data_loader.get_merged_data() is not None or self.input_dir_changed(input_dir):
            self.data_loader.load_directory(input_dir)
            self.current_input_dir = input_dir
            
        # 2. Clustering
        algo = config['algorithm']
        params = config['params']
        
        if algo == "KMeans":
            self.cluster_manager.run_kmeans(**params)
        elif algo == "Phenograph":
            self.cluster_manager.run_phenograph(**params)
        elif algo == "FlowSOM":
            self.cluster_manager.run_flowsom(**params)
             
        # 3. Save Results
        self.output_dir = create_unique_output_dir(Path(input_dir) / "results" / "cluster_results")
        
        saved_path = self.cluster_manager.save_results(self.output_dir)

        marker_means_path = self.cluster_manager.save_cluster_marker_means(self.output_dir)
        
        # 4. Generate Heatmap
        heatmap_path = self.output_dir / "heatmap.png"
        feature_df = self.data_loader.get_feature_data()
        labels = self.cluster_manager.labels

        self.heatmap_generator.generate_from_dataframe(feature_df, labels, heatmap_path, cmap=heatmap_cmap)
         
        return {
            'message': f"Clustering completed. Results saved to {saved_path}",
            'heatmap': str(heatmap_path),
            'marker_means': str(marker_means_path),
            'n_clusters': len(set(labels))
        }

    def input_dir_changed(self, new_dir):
        # Helper to check if we need to reload
        if not hasattr(self, 'current_input_dir'):
            return True
        return self.current_input_dir != new_dir

    def _sample_dataframe_for_visualization(self, df, max_cells, labels=None, random_state=42):
        if df is None or df.empty:
            raise ValueError("No data available for visualization.")

        if max_cells is None or max_cells <= 0 or len(df) <= max_cells:
            sampled_df = df.reset_index(drop=True).copy()
            sampled_labels = None if labels is None else np.asarray(labels).copy()
            return sampled_df, sampled_labels, len(sampled_df), len(df)

        rng = np.random.default_rng(random_state)
        labels_array = None if labels is None else np.asarray(labels)

        if labels_array is None or len(labels_array) != len(df):
            chosen_idx = np.sort(rng.choice(len(df), size=max_cells, replace=False))
            sampled_df = df.iloc[chosen_idx].reset_index(drop=True).copy()
            return sampled_df, None, len(sampled_df), len(df)

        label_series = pd.Series(labels_array, index=df.index)
        counts = label_series.value_counts(sort=False)

        if len(counts) <= 1:
            chosen_idx = np.sort(rng.choice(len(df), size=max_cells, replace=False))
            sampled_df = df.iloc[chosen_idx].reset_index(drop=True).copy()
            sampled_labels = labels_array[chosen_idx]
            return sampled_df, sampled_labels, len(sampled_df), len(df)

        raw_targets = counts / counts.sum() * max_cells
        target_counts = np.floor(raw_targets).astype(int)
        remainder = int(max_cells - target_counts.sum())
        if remainder > 0:
            fractional = (raw_targets - target_counts).sort_values(ascending=False)
            for label in fractional.index[:remainder]:
                target_counts[label] += 1

        selected_indices = []
        for label, target in target_counts.items():
            group_indices = np.flatnonzero(labels_array == label)
            if len(group_indices) == 0 or target <= 0:
                continue
            take = min(int(target), len(group_indices))
            selected_indices.extend(rng.choice(group_indices, size=take, replace=False).tolist())

        selected_indices = np.array(sorted(selected_indices))
        sampled_df = df.iloc[selected_indices].reset_index(drop=True).copy()
        sampled_labels = labels_array[selected_indices]
        return sampled_df, sampled_labels, len(sampled_df), len(df)

    def on_clustering_finished(self, result):
        self.clustering_tab.update_log(result['message'])
        if 'marker_means' in result:
            self.clustering_tab.update_log(f"Cluster marker means saved to {result['marker_means']}")
        self.clustering_tab.update_log(f"Found {result['n_clusters']} clusters.")
        self.clustering_tab.show_preview(result['heatmap'])
        self.status_bar.showMessage("Clustering completed successfully.")
        
        # Update DimTab state if needed (e.g. enable it)
        self.dim_tab.update_log("Clustering data available for visualization.")
        self.heatmap_tab.update_log("Clustering data available for heatmap generation.")

    def on_clustering_error(self, error_msg):
        self.clustering_tab.update_log(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", str(error_msg))
        self.clustering_tab.progress.setRange(0, 100)
        self.clustering_tab.progress.setValue(0)
        self.clustering_tab.run_btn.setEnabled(True)
        self.clustering_tab.stop_btn.setEnabled(False)

    def stop_analysis(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.status_bar.showMessage("Analysis stopped by user.")
            
            # Reset UI
            self.clustering_tab.run_btn.setEnabled(True)
            self.clustering_tab.stop_btn.setEnabled(False)
            self.clustering_tab.progress.setRange(0, 100)
            self.clustering_tab.progress.setValue(0)
            
            self.dim_tab.run_btn.setEnabled(True)
            self.dim_tab.stop_btn.setEnabled(False)
            self.dim_tab.progress.setRange(0, 100)
            self.dim_tab.progress.setValue(0)

            self.heatmap_tab.run_btn.setEnabled(True)
            self.heatmap_tab.stop_btn.setEnabled(False)
            self.heatmap_tab.progress.setRange(0, 100)
            self.heatmap_tab.progress.setValue(0)

    def start_heatmap_generation(self, config):
        custom_file = config.get('custom_file')
        if not custom_file and self.cluster_manager.labels is None:
            QMessageBox.warning(self, "Warning", "Please run clustering first or select a CSV file.")
            return

        self.heatmap_tab.run_btn.setEnabled(False)
        self.heatmap_tab.stop_btn.setEnabled(True)
        self.heatmap_tab.progress.setRange(0, 0)
        self.heatmap_tab.update_log("Starting heatmap generation...")

        worker = AnalysisWorker(self.run_heatmap_logic, config)
        worker.result.connect(self.on_heatmap_finished)
        worker.error.connect(self.on_heatmap_error)
        worker.finished.connect(lambda: self.heatmap_tab.run_btn.setEnabled(True))
        worker.finished.connect(lambda: self.heatmap_tab.stop_btn.setEnabled(False))
        worker.finished.connect(lambda: self.heatmap_tab.progress.setRange(0, 100))
        worker.finished.connect(lambda: self.heatmap_tab.progress.setValue(100))
        worker.start()
        self.worker = worker

    def run_heatmap_logic(self, config):
        custom_file = config.get('custom_file')
        heatmap_cmap = config.get('heatmap_cmap', 'Spectral_r')
        if custom_file:
            output_dir = create_unique_output_dir(Path(custom_file).parent / "heatmap_results")
            output_path = output_dir / "heatmap.png"
            self.heatmap_generator.generate_from_csv(custom_file, output_path, cmap=heatmap_cmap)
            message = f"Heatmap generated from {custom_file}\nSaved to {output_path}"
        else:
            feature_df = self.data_loader.get_feature_data()
            if feature_df is None:
                raise ValueError("No clustering data loaded")

            base_dir = Path(self.current_input_dir) if hasattr(self, 'current_input_dir') else Path(".")
            output_dir = create_unique_output_dir(base_dir / "results" / "heatmap_results")
            output_path = output_dir / "heatmap.png"
            self.heatmap_generator.generate_from_dataframe(
                feature_df,
                self.cluster_manager.labels,
                output_path,
                cmap=heatmap_cmap,
            )
            message = f"Heatmap generated from current clustering results\nSaved to {output_path}"

        self.output_dir = output_dir
        return {
            'message': message,
            'image': str(output_path),
        }

    def on_heatmap_finished(self, result):
        self.heatmap_tab.update_log(result['message'])
        self.heatmap_tab.show_preview(result['image'])
        self.status_bar.showMessage("Heatmap generation completed.")

    def on_heatmap_error(self, error_msg):
        self.heatmap_tab.update_log(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", str(error_msg))
        self.heatmap_tab.run_btn.setEnabled(True)
        self.heatmap_tab.stop_btn.setEnabled(False)
        self.heatmap_tab.progress.setRange(0, 100)
        self.heatmap_tab.progress.setValue(0)

    def start_visualization(self, config):
        custom_file = config.get('custom_file')
        if not custom_file and self.cluster_manager.labels is None:
            QMessageBox.warning(self, "Warning", "Please run clustering first or select a CSV file.")
            return

        self.dim_tab.run_btn.setEnabled(False)
        self.dim_tab.stop_btn.setEnabled(True)
        self.dim_tab.progress.setRange(0, 0)
        self.dim_tab.update_log("Starting dimensionality reduction...")
        
        worker = AnalysisWorker(self.run_vis_logic, config)
        worker.result.connect(self.on_vis_finished)
        worker.error.connect(self.on_vis_error)
        worker.finished.connect(lambda: self.dim_tab.run_btn.setEnabled(True))
        worker.finished.connect(lambda: self.dim_tab.stop_btn.setEnabled(False))
        worker.finished.connect(lambda: self.dim_tab.progress.setRange(0, 100))
        worker.finished.connect(lambda: self.dim_tab.progress.setValue(100))
        worker.start()
        self.worker = worker

    def run_vis_logic(self, config):
        algo = config['algorithm']
        params = config['params']
        custom_file = config.get('custom_file')
        max_cells = int(config.get('max_cells', 20000))
        sample_seed = int(params.get('random_state', 42))
        label_key_used = None
        
        # Determine data and labels
        if custom_file:
            # Load custom file
            try:
                df = pd.read_csv(custom_file)
            except Exception as e:
                raise ValueError(f"Failed to load file: {e}")
            
            # Identify label column
            label_col = None
            lower_to_original = {str(c).strip().lower(): c for c in df.columns}
            for key in ['batch_label', 'cell_type', 'cluster', 'cluster_label', 'label']:
                if key in lower_to_original:
                    label_col = lower_to_original[key]
                    label_key_used = key
                    break
            
            sampled_df = df.copy()
            if label_col:
                labels = df[label_col].fillna("Unknown").astype(str).values
                sampled_df, labels, sampled_n, original_n = self._sample_dataframe_for_visualization(
                    df,
                    max_cells,
                    labels=labels,
                    random_state=sample_seed,
                )
                cols_to_drop = [label_col, '_file_id', '_original_index']
                feature_cols = [c for c in sampled_df.columns if c not in cols_to_drop]
                data = sampled_df[feature_cols].select_dtypes(include=[np.number])
                if data.shape[1] == 0:
                     raise ValueError("No numeric feature columns found in CSV.")
            else:
                sampled_df, _, sampled_n, original_n = self._sample_dataframe_for_visualization(
                    df,
                    max_cells,
                    labels=None,
                    random_state=sample_seed,
                )
                labels = np.zeros(len(sampled_df), dtype=int)
                cols_to_drop = ['_file_id', '_original_index']
                feature_cols = [c for c in sampled_df.columns if c not in cols_to_drop]
                data = sampled_df[feature_cols].select_dtypes(include=[np.number])
                if data.shape[1] == 0:
                     raise ValueError("No numeric feature columns found in CSV.")

            self.dim_manager.set_custom_data(data)
            output_dir = create_unique_output_dir(Path(custom_file).parent / "vis_results")
            self.output_dir = output_dir
            
        else:
            merged_df = self.data_loader.get_merged_data()
            if merged_df is None:
                raise ValueError("No clustering data loaded")

            lower_to_original = {str(c).strip().lower(): c for c in merged_df.columns}
            label_col = None
            for key in ['batch_label', 'cell_type']:
                if key in lower_to_original:
                    label_col = lower_to_original[key]
                    label_key_used = key
                    break

            if label_col is not None:
                labels = merged_df[label_col].fillna("Unknown").astype(str).values
            else:
                labels = self.cluster_manager.labels

            sampled_df, labels, sampled_n, original_n = self._sample_dataframe_for_visualization(
                merged_df,
                max_cells,
                labels=labels,
                random_state=sample_seed,
            )
            feature_cols = self.data_loader.feature_columns
            data = sampled_df[feature_cols]
            self.dim_manager.set_custom_data(data)
            
            # For clustering results, we save in the same parent dir structure as clustering if possible,
            # or in a new vis_results folder relative to data input.
            # Assuming current_input_dir is available from clustering context
            if hasattr(self, 'current_input_dir'):
                base_dir = Path(self.current_input_dir)
            else:
                # Fallback if somehow running without context (shouldn't happen for clustering flow)
                base_dir = Path(".")
            
            self.output_dir = create_unique_output_dir(base_dir / "results" / "vis_results")
        
        # 1. Run Reduction
        if algo == "t-SNE":
            embedding = self.dim_manager.run_tsne(**params)
        elif algo == "UMAP":
            embedding = self.dim_manager.run_umap(**params)
            
        # 2. Plot
        output_path = self.output_dir / f"{algo}_plot.png"
        
        # 2D or 3D? Requirements say "Generate 2D/3D dim reduction map".
        # I'll generate 2D by default as t-SNE/UMAP defaults are 2 dims.
        # If I want 3D, I should check params or offer a checkbox.
        # For now, I implemented run_tsne/run_umap returning what was configured.
        # But my Visualizer has plot_embedding_2d and 3d.
        # The default implementation in DimManager uses n_components=2 (default for TSNE/UMAP).
        # I'll stick to 2D for this iteration unless I add a "Dimensions" toggle in GUI.
        # The requirements say "Generate 2D/3D". I'll generate 2D for the preview.
        # Ideally, I'd save both or let user choose.
        
        Visualizer.plot_embedding_2d(embedding, labels, str(output_path))
        highlight_paths = []
        if label_key_used == 'batch_label':
            highlight_dir = self.output_dir / f"{algo}_batch_label_highlights"
            highlight_paths = Visualizer.plot_embedding_2d_highlight_series(
                embedding,
                labels,
                highlight_dir,
                prefix=f"{algo}_batch_label",
            )
        
        # 3. Save Coordinates CSV
        df = sampled_df.copy()
        
        # Determine column names based on algorithm
        if algo == "t-SNE":
            coord_cols = ["tSNE1", "tSNE2"]
        elif algo == "UMAP":
            coord_cols = ["UMAP1", "UMAP2"]
        else:
            coord_cols = ["Dim1", "Dim2"]
            
        # Check dimensions match
        if embedding.shape[1] >= 2:
            df[coord_cols[0]] = embedding[:, 0]
            df[coord_cols[1]] = embedding[:, 1]
            
            # If 3D, add 3rd col? Current logic is 2D.
            if embedding.shape[1] > 2:
                for i in range(2, embedding.shape[1]):
                    df[f"{algo}{i+1}"] = embedding[:, i]
        
        csv_output_path = self.output_dir / f"{algo}_coordinates.csv"
        df.to_csv(csv_output_path, index=False)
        
        return {
            'message': (
                f"Downsampled cells: {sampled_n}/{original_n}\n"
                f"Visualization saved to {output_path}\n"
                f"Coordinates saved to {csv_output_path}"
                + (
                    f"\nBatch label highlight plots saved to {highlight_dir} ({len(highlight_paths)} files)"
                    if highlight_paths else ""
                )
            ),
            'image': str(output_path)
        }

    def on_vis_finished(self, result):
        self.dim_tab.update_log(result['message'])
        self.dim_tab.show_preview(result['image'])
        self.status_bar.showMessage("Visualization completed.")

    def on_vis_error(self, error_msg):
        self.dim_tab.update_log(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", str(error_msg))
        self.dim_tab.run_btn.setEnabled(True)
        self.dim_tab.stop_btn.setEnabled(False)

    def handle_csv_process(self, config):
        """
        Handle requests from CsvProcessorTab.
        Types: 'load_file', 'load_folder', 'check_folder', 'split_csv', 'split_folder', 'map_folder', 'arcsinh_folder'
        """
        task_type = config.get('type')
        
        if task_type == 'load_file':
            file_path = config.get('path')
            # Run in worker or direct? Loading small/medium CSV is usually fast enough for main thread
            # but better use worker for responsiveness. For now let's try direct to simplify state update.
            # Actually, CsvProcessorTab expects data back.
            success, msg = self.csv_splitter.load_file(file_path)
            if success:
                # Analyze options
                row_opts, col_opts = self.csv_splitter.get_split_criteria()
                # Send back to tab
                self.csv_tab.on_file_loaded(self.csv_splitter.df.head(100), row_opts, col_opts)
                self.csv_tab.update_log(msg)
            else:
                self.csv_tab.update_log(f"Error loading file: {msg}")

        elif task_type == 'load_folder':
            folder_path = config.get('path')

            def run_load_folder(path):
                return self.csv_splitter.load_folder(path)

            worker = AnalysisWorker(run_load_folder, folder_path)

            def on_loaded(result):
                ok, msg, preview_df, row_opts, col_opts = result
                self.csv_tab.update_log(msg)
                if not ok:
                    QMessageBox.warning(self, "Utils", msg)
                    return
                self.csv_tab.on_file_loaded(preview_df, row_opts, col_opts)

            def on_load_error(err):
                self.csv_tab.update_log(f"Error: {err}")
                QMessageBox.critical(self, "Utils", str(err))

            worker.result.connect(on_loaded)
            worker.error.connect(on_load_error)
            worker.start()
            self.worker = worker

        elif task_type == 'check_folder':
            folder_path = config.get('path')
            # This can be slow, run in worker
            worker = AnalysisWorker(self.csv_splitter.check_folder_consistency, folder_path)
            
            def on_check_finished(result):
                # result is (is_consistent, message, common_cols)
                is_cons, msg, cols = result
                self.csv_tab.update_log(msg)
                if is_cons:
                     QMessageBox.information(self, "Consistency Check", msg)
                else:
                     QMessageBox.warning(self, "Consistency Check", msg)
            
            worker.result.connect(on_check_finished)
            worker.start()
            self.worker = worker # Keep ref

        elif task_type == 'split_csv':
            # Run splitting in worker
            self.csv_tab.run_btn.setEnabled(False)
            self.csv_tab.update_log("Splitting CSV...")
            
            def run_split(cfg):
                # Wrapper for worker
                return self.csv_splitter.split_csv(
                    cfg['row_indices'], 
                    cfg['col_indices'], 
                    cfg['output_base_dir']
                )
                
            worker = AnalysisWorker(run_split, config)
            
            def on_split_finished(path):
                self.csv_tab.update_log(f"Split complete. Saved to: {path}")
                self.csv_tab.run_btn.setEnabled(True)
                QMessageBox.information(self, "Success", f"File saved to:\n{path}")
                
            def on_split_error(err):
                self.csv_tab.update_log(f"Error splitting: {err}")
                self.csv_tab.run_btn.setEnabled(True)
                QMessageBox.critical(self, "Error", str(err))

            worker.result.connect(on_split_finished)
            worker.error.connect(on_split_error)
            worker.start()
            self.worker = worker

        elif task_type == 'split_folder':
            self.csv_tab.run_btn.setEnabled(False)
            self.csv_tab.update_log("Splitting CSV folder...")

            def run_split_folder(cfg):
                return self.csv_splitter.split_folder(
                    cfg.get('row_values'),
                    cfg['col_indices'],
                    cfg['folder_path'],
                    cfg['output_base_dir']
                )

            worker = AnalysisWorker(run_split_folder, config)

            def on_split_finished(paths):
                self.csv_tab.run_btn.setEnabled(True)
                self.csv_tab.update_log(f"Split complete. Saved {len(paths)} files.")
                if paths:
                    self.csv_tab.update_log(f"Output folder: {Path(paths[0]).parent}")
                QMessageBox.information(self, "Success", f"Saved {len(paths)} files.")

            def on_split_error(err):
                self.csv_tab.run_btn.setEnabled(True)
                self.csv_tab.update_log(f"Error splitting: {err}")
                QMessageBox.critical(self, "Error", str(err))

            worker.result.connect(on_split_finished)
            worker.error.connect(on_split_error)
            worker.start()
            self.worker = worker

        elif task_type == 'map_folder':
            folder_path = config.get('folder_path')
            mapping_csv_path = config.get('mapping_csv_path')
            self.csv_tab.update_log("Mapping cluster_label to cell_type...")

            def run_map(cfg):
                return self.csv_mapper.map_folder(cfg['folder_path'], cfg['mapping_csv_path'])

            worker = AnalysisWorker(run_map, {'folder_path': folder_path, 'mapping_csv_path': mapping_csv_path})

            def on_map_finished(result):
                out_dir, out_paths = result
                self.csv_tab.update_log(f"Mapping complete. Saved {len(out_paths)} files.")
                self.csv_tab.update_log(f"Output folder: {out_dir}")
                QMessageBox.information(self, "Utils", f"Saved {len(out_paths)} files to:\n{out_dir}")

            def on_map_error(err):
                self.csv_tab.update_log(f"Error mapping: {err}")
                QMessageBox.critical(self, "Utils", str(err))

            worker.result.connect(on_map_finished)
            worker.error.connect(on_map_error)
            worker.start()
            self.worker = worker

        elif task_type == 'arcsinh_folder':
            folder_path = config.get('folder_path')
            self.csv_tab.arcsinh_run_btn.setEnabled(False)
            self.csv_tab.update_log("Applying arcsinh transform with cofactor 5...")

            def run_arcsinh(cfg):
                return self.arcsinh_transformer.transform_folder(cfg['folder_path'])

            worker = AnalysisWorker(run_arcsinh, {'folder_path': folder_path})

            def on_arcsinh_finished(result):
                out_dir, out_paths = result
                self.csv_tab.arcsinh_run_btn.setEnabled(True)
                self.csv_tab.update_log(f"Arcsinh complete. Saved {len(out_paths)} files.")
                self.csv_tab.update_log(f"Output folder: {out_dir}")
                QMessageBox.information(self, "Utils", f"Saved {len(out_paths)} files to:\n{out_dir}")

            def on_arcsinh_error(err):
                self.csv_tab.arcsinh_run_btn.setEnabled(True)
                self.csv_tab.update_log(f"Error in arcsinh: {err}")
                QMessageBox.critical(self, "Utils", str(err))

            worker.result.connect(on_arcsinh_finished)
            worker.error.connect(on_arcsinh_error)
            worker.start()
            self.worker = worker

    def start_difference_analysis(self, config):
        input_dir = config.get("input_dir")
        if not input_dir:
            return

        self.diff_tab.run_btn.setEnabled(False)
        self.diff_tab.progress.setRange(0, 0)
        self.diff_tab.update_log("Running difference analysis...")

        worker = AnalysisWorker(self.run_difference_analysis_logic, config)
        worker.result.connect(self.on_difference_analysis_finished)
        worker.error.connect(self.on_difference_analysis_error)
        worker.finished.connect(lambda: self.diff_tab.run_btn.setEnabled(True))
        worker.finished.connect(lambda: self.diff_tab.progress.setRange(0, 100))
        worker.finished.connect(lambda: self.diff_tab.progress.setValue(100))
        worker.start()
        self.worker = worker

    def run_difference_analysis_logic(self, config):
        input_dir = config["input_dir"]
        mode = config.get("mode", "Percentage Stacked Bar Chart")
        if mode == "Percentage Stacked Bar Chart":
            result = self.difference_analyzer.run_percentage_stacked_bar_chart(input_dir)
        else:
            result = self.difference_analyzer.run_percentage_stacked_bar_chart(input_dir)
        return {
            "message": f"Saved stacked bar chart to {result.plot_path}",
            "image": str(result.plot_path),
            "output_dir": str(result.output_dir),
        }

    def on_difference_analysis_finished(self, result):
        self.diff_tab.update_log(result.get("message", "Done."))
        if "image" in result:
            self.diff_tab.show_preview(result["image"])
        self.status_bar.showMessage("Difference analysis completed.")

    def on_difference_analysis_error(self, error_msg):
        self.diff_tab.update_log(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", str(error_msg))
        self.diff_tab.run_btn.setEnabled(True)
        self.diff_tab.progress.setRange(0, 100)
        self.diff_tab.progress.setValue(0)
