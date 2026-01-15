from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QMessageBox, QStatusBar)
import os
import pandas as pd
import numpy as np
from pathlib import Path
from src.gui.tabs import ClusteringTab, DimReductionTab, CsvProcessorTab, DifferenceAnalysisTab
from src.gui.workers import AnalysisWorker
from src.utils.data_loader import DataLoader
from src.analysis.clustering import ClusterManager
from src.analysis.dim_reduction import DimReductionManager
from src.analysis.visualization import Visualizer
from src.analysis.csv_processor import CsvSplitter, CsvMapper
from src.analysis.difference_analysis import DifferenceAnalyzer

from datetime import datetime

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyDAT")
        self.resize(1200, 800)
        
        # State
        self.data_loader = DataLoader()
        self.cluster_manager = ClusterManager(self.data_loader)
        self.dim_manager = DimReductionManager(self.data_loader)
        self.csv_splitter = CsvSplitter()
        self.csv_mapper = CsvMapper()
        self.difference_analyzer = DifferenceAnalyzer()
        self.output_dir = None
        
        self.init_ui()

    def init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.clustering_tab = ClusteringTab()
        self.clustering_tab.run_analysis_signal.connect(self.start_clustering)
        self.clustering_tab.stop_analysis_signal.connect(self.stop_analysis)
        
        self.dim_tab = DimReductionTab()
        self.dim_tab.run_analysis_signal.connect(self.start_visualization)
        self.dim_tab.stop_analysis_signal.connect(self.stop_analysis)
        
        self.csv_tab = CsvProcessorTab()
        self.csv_tab.run_process_signal.connect(self.handle_csv_process)

        self.diff_tab = DifferenceAnalysisTab()
        self.diff_tab.run_analysis_signal.connect(self.start_difference_analysis)
        
        self.tabs.addTab(self.clustering_tab, "Clustering Analysis")
        self.tabs.addTab(self.dim_tab, "Dim Reduction & Visualization")
        self.tabs.addTab(self.csv_tab, "CSV Processor")
        self.tabs.addTab(self.diff_tab, "Difference Analysis")
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

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
        timestamp = datetime.now().strftime("%y%m%d_%H%M")
        self.output_dir = Path(input_dir) / "results" / "cluster_results" / timestamp
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_path = self.cluster_manager.save_results(self.output_dir)

        marker_means_path = self.cluster_manager.save_cluster_marker_means(self.output_dir)
        
        # 4. Generate Heatmap
        heatmap_path = self.output_dir / "heatmap.png"
        data = self.data_loader.get_feature_data().values
        labels = self.cluster_manager.labels
        features = self.data_loader.feature_columns
        
        Visualizer.plot_heatmap(data, labels, features, str(heatmap_path))
         
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

    def on_clustering_finished(self, result):
        self.clustering_tab.update_log(result['message'])
        if 'marker_means' in result:
            self.clustering_tab.update_log(f"Cluster marker means saved to {result['marker_means']}")
        self.clustering_tab.update_log(f"Found {result['n_clusters']} clusters.")
        self.clustering_tab.show_preview(result['heatmap'])
        self.status_bar.showMessage("Clustering completed successfully.")
        
        # Update DimTab state if needed (e.g. enable it)
        self.dim_tab.update_log("Clustering data available for visualization.")

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
            for key in ['cell_type', 'cluster', 'cluster_label', 'label']:
                if key in lower_to_original:
                    label_col = lower_to_original[key]
                    break
            
            if label_col:
                labels = df[label_col].fillna("Unknown").astype(str).values
                cols_to_drop = [label_col, '_file_id', '_original_index']
                feature_cols = [c for c in df.columns if c not in cols_to_drop]
                # Check if features are numeric
                data = df[feature_cols].select_dtypes(include=[np.number])
                if data.shape[1] == 0:
                     raise ValueError("No numeric feature columns found in CSV.")
            else:
                # No label, use default
                labels = np.zeros(len(df), dtype=int)
                cols_to_drop = ['_file_id', '_original_index']
                feature_cols = [c for c in df.columns if c not in cols_to_drop]
                data = df[feature_cols].select_dtypes(include=[np.number])
                if data.shape[1] == 0:
                     raise ValueError("No numeric feature columns found in CSV.")

            self.dim_manager.set_custom_data(data)
            timestamp = datetime.now().strftime("%y%m%d_%H%M")
            output_dir = Path(custom_file).parent / "vis_results" / timestamp
            output_dir.mkdir(parents=True, exist_ok=True)
            self.output_dir = output_dir
            
        else:
            self.dim_manager.set_custom_data(None)
            merged_df = self.data_loader.get_merged_data()
            if merged_df is not None and 'cell_type' in {str(c).strip().lower() for c in merged_df.columns}:
                cell_type_col = next(c for c in merged_df.columns if str(c).strip().lower() == 'cell_type')
                labels = merged_df[cell_type_col].fillna("Unknown").astype(str).values
            else:
                labels = self.cluster_manager.labels
            
            # For clustering results, we save in the same parent dir structure as clustering if possible,
            # or in a new vis_results folder relative to data input.
            # Assuming current_input_dir is available from clustering context
            if hasattr(self, 'current_input_dir'):
                base_dir = Path(self.current_input_dir)
            else:
                # Fallback if somehow running without context (shouldn't happen for clustering flow)
                base_dir = Path(".")
            
            timestamp = datetime.now().strftime("%y%m%d_%H%M")
            self.output_dir = base_dir / "results" / "vis_results" / timestamp
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
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
        
        # 3. Save Coordinates CSV
        # We need to construct a DataFrame with original data + coordinates
        if custom_file:
            # We already have df loaded above
            pass # df is available
        else:
            # Re-construct df from DataLoader
            # We might have multiple files merged.
            # Ideally DataLoader should provide a way to export merged df with metadata if needed.
            # But currently `get_merged_data()` returns the merged DataFrame including file_id etc.
            df = self.data_loader.get_merged_data().copy()
        
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
            'message': f"Visualization saved to {output_path}\nCoordinates saved to {csv_output_path}",
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
        Types: 'load_file', 'load_folder', 'check_folder', 'split_csv', 'split_folder'
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
                    QMessageBox.warning(self, "CSV Processor", msg)
                    return
                self.csv_tab.on_file_loaded(preview_df, row_opts, col_opts)

            def on_load_error(err):
                self.csv_tab.update_log(f"Error: {err}")
                QMessageBox.critical(self, "CSV Processor", str(err))

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
                QMessageBox.information(self, "CSV Mapper", f"Saved {len(out_paths)} files to:\n{out_dir}")

            def on_map_error(err):
                self.csv_tab.update_log(f"Error mapping: {err}")
                QMessageBox.critical(self, "CSV Mapper", str(err))

            worker.result.connect(on_map_finished)
            worker.error.connect(on_map_error)
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
