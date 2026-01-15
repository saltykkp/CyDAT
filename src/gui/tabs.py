from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFileDialog, QComboBox, QSpinBox, 
                             QDoubleSpinBox, QProgressBar, QGroupBox, QFormLayout, 
                             QTextEdit, QSplitter, QScrollArea, QFrame, QTableView, QHeaderView,
                             QListWidget, QAbstractItemView, QCheckBox, QListWidgetItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QAbstractTableModel
from PyQt6.QtGui import QPixmap
import os
import pandas as pd

class ResizingLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; border: 1px solid #333;")
        self.setMinimumHeight(400)

    def set_image(self, image_path):
        self._pixmap = QPixmap(image_path)
        self._update_display()

    def resizeEvent(self, event):
        self._update_display()
        super().resizeEvent(event)

    def _update_display(self):
        if self._pixmap and not self._pixmap.isNull():
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled)

class PandasModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame()):
        super().__init__()
        self._df = df

    def rowCount(self, parent=None):
        return self._df.shape[0]

    def columnCount(self, parent=None):
        return self._df.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._df.iloc[index.row(), index.column()])
        return None

    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._df.columns[col]
        return None

    def set_data(self, df):
        self.beginResetModel()
        self._df = df
        self.endResetModel()

class ClusteringTab(QWidget):
    run_analysis_signal = pyqtSignal(dict) # Emit config dict
    stop_analysis_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main layout: Horizontal split
        # Left Panel (Settings) | Right Panel (Preview)
        main_layout = QHBoxLayout(self)
        
        # Left Panel
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)
        
        # 1. Data Input
        input_group = QGroupBox("Data Input")
        input_layout = QVBoxLayout()
        self.dir_btn = QPushButton("Select Folder")
        self.dir_btn.setMinimumHeight(40)
        self.dir_btn.clicked.connect(self.select_directory)
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dir_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        
        input_layout.addWidget(self.dir_btn)
        input_layout.addWidget(self.dir_label)
        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)

        # 2. Algorithm Settings
        algo_group = QGroupBox("Algorithm Settings")
        algo_layout = QFormLayout()
        algo_layout.setSpacing(15)
        
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["KMeans", "Phenograph", "FlowSOM"])
        self.algo_combo.currentTextChanged.connect(self.update_params)
        self.algo_combo.setMinimumHeight(30)
        algo_layout.addRow("Algorithm:", self.algo_combo)
        
        self.param_widget = QWidget()
        self.param_layout = QFormLayout(self.param_widget)
        self.param_layout.setSpacing(10)
        algo_layout.addRow(self.param_widget)
        
        algo_group.setLayout(algo_layout)
        left_layout.addWidget(algo_group)
        
        left_layout.addStretch()

        # 3. Execution (Moved to Bottom Left)
        exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout()
        self.run_btn = QPushButton("Run Clustering")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a3a5a, stop:1 #3a4a7a);
                font-size: 16px;
                border-radius: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a4a7a, stop:1 #4a5a8a);
            }
        """)
        self.run_btn.clicked.connect(self.on_run)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a2a2a, stop:1 #a03a3a);
                font-size: 16px;
                border-radius: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a03a3a, stop:1 #b04a4a);
            }
            QPushButton:disabled {
                background: #444;
                color: #888;
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar { height: 5px; border: none; background: #2d2d2d; } QProgressBar::chunk { background: #5a7a9a; }")
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.run_btn, 2)
        btn_layout.addWidget(self.stop_btn, 1)
        
        exec_layout.addLayout(btn_layout)
        exec_layout.addWidget(self.progress)
        exec_group.setLayout(exec_layout)
        left_layout.addWidget(exec_group)
        
        # Right Panel
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)
        
        # 4. Results Preview (Main Area)
        preview_group = QGroupBox("Results Preview")
        preview_layout = QVBoxLayout()
        
        self.image_label = ResizingLabel()
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setStyleSheet("background-color: #1e1e1e; border: none; color: #888; font-size: 11px;")

        preview_layout.addWidget(self.image_label, 1) # High stretch factor
        preview_layout.addWidget(self.log_area)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group, 1)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self.update_params("KMeans") # Init params

    def select_directory(self):
        d = QFileDialog.getExistingDirectory(self, "Select Data Directory")
        if d:
            self.dir_label.setText(d)

    def update_params(self, algo):
        # Clear existing params
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.params = {}
        if algo == "KMeans":
            sb_clusters = QSpinBox()
            sb_clusters.setRange(2, 100)
            sb_clusters.setValue(10)
            self.params['n_clusters'] = sb_clusters
            self.param_layout.addRow("Clusters (n):", sb_clusters)
            
            sb_iter = QSpinBox()
            sb_iter.setRange(10, 1000)
            sb_iter.setValue(300)
            self.params['max_iter'] = sb_iter
            self.param_layout.addRow("Max Iter:", sb_iter)
            
            sb_seed = QSpinBox()
            sb_seed.setRange(0, 10000)
            sb_seed.setValue(42)
            self.params['random_state'] = sb_seed
            self.param_layout.addRow("Random Seed:", sb_seed)

        elif algo == "Phenograph":
            sb_k = QSpinBox()
            sb_k.setRange(5, 200)
            sb_k.setValue(30)
            self.params['k'] = sb_k
            self.param_layout.addRow("Neighbors (k):", sb_k)
            
            cb_metric = QComboBox()
            cb_metric.addItems(["euclidean", "manhattan", "cosine"])
            self.params['metric'] = cb_metric
            self.param_layout.addRow("Metric:", cb_metric)
            
            # Phenograph typically uses numpy seed globally or not exposed easily, 
            # but we'll include it for the logic
            sb_seed = QSpinBox()
            sb_seed.setRange(0, 10000)
            sb_seed.setValue(42)
            self.params['random_state'] = sb_seed
            self.param_layout.addRow("Random Seed:", sb_seed)

        elif algo == "FlowSOM":
            sb_n_clusters = QSpinBox()
            sb_n_clusters.setRange(2, 200)
            sb_n_clusters.setValue(10)
            self.params['n_clusters'] = sb_n_clusters
            self.param_layout.addRow("Metaclusters (n):", sb_n_clusters)

            sb_xdim = QSpinBox()
            sb_xdim.setRange(2, 50)
            sb_xdim.setValue(10)
            self.params['xdim'] = sb_xdim
            self.param_layout.addRow("Grid xdim:", sb_xdim)

            sb_ydim = QSpinBox()
            sb_ydim.setRange(2, 50)
            sb_ydim.setValue(10)
            self.params['ydim'] = sb_ydim
            self.param_layout.addRow("Grid ydim:", sb_ydim)

            sb_rlen = QSpinBox()
            sb_rlen.setRange(1, 200)
            sb_rlen.setValue(10)
            self.params['rlen'] = sb_rlen
            self.param_layout.addRow("Training iters:", sb_rlen)

            sb_seed = QSpinBox()
            sb_seed.setRange(0, 100000)
            sb_seed.setValue(42)
            self.params['seed'] = sb_seed
            self.param_layout.addRow("Seed:", sb_seed)

    def on_run(self):
        input_dir = self.dir_label.text()
        if not os.path.isdir(input_dir):
            self.log_area.append("Error: Invalid directory selected.")
            return

        config = {
            'type': 'clustering',
            'input_dir': input_dir,
            'algorithm': self.algo_combo.currentText(),
            'params': {k: v.value() if isinstance(v, QSpinBox) else v.currentText() 
                       for k, v in self.params.items()}
        }
        self.run_analysis_signal.emit(config)

    def on_stop(self):
        self.stop_analysis_signal.emit()
        self.log_area.append("Stopping analysis...")

    def update_log(self, text):
        self.log_area.append(text)
    
    def update_progress(self, val):
        self.progress.setValue(val)

    def show_preview(self, image_path):
        self.image_label.set_image(image_path)


class DimReductionTab(QWidget):
    run_analysis_signal = pyqtSignal(dict)
    stop_analysis_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main layout: Horizontal split
        # Left Panel (Settings) | Right Panel (Preview)
        main_layout = QHBoxLayout(self)
        
        # Left Panel
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)

        # 0. Data Source
        data_group = QGroupBox("Data Source (Optional)")
        data_layout = QVBoxLayout()
        self.file_btn = QPushButton("Select CSV File")
        self.file_btn.setMinimumHeight(40)
        self.file_btn.clicked.connect(self.select_file)
        
        self.file_label = QLabel("Default: Use Clustering Results")
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        
        self.clear_btn = QPushButton("Clear Selection")
        self.clear_btn.clicked.connect(self.clear_file)
        
        data_layout.addWidget(self.file_btn)
        data_layout.addWidget(self.file_label)
        data_layout.addWidget(self.clear_btn)
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)

        # 1. Algorithm Settings
        algo_group = QGroupBox("Algorithm Settings")
        algo_layout = QFormLayout()
        algo_layout.setSpacing(15)
        
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["t-SNE", "UMAP"])
        self.algo_combo.currentTextChanged.connect(self.update_params)
        self.algo_combo.setMinimumHeight(30)
        algo_layout.addRow("Algorithm:", self.algo_combo)
        
        self.param_widget = QWidget()
        self.param_layout = QFormLayout(self.param_widget)
        self.param_layout.setSpacing(10)
        algo_layout.addRow(self.param_widget)
        
        algo_group.setLayout(algo_layout)
        left_layout.addWidget(algo_group)
        
        self.update_params("t-SNE")
        
        left_layout.addStretch()

        # 2. Execution (Moved to Bottom Left)
        exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout()
        self.run_btn = QPushButton("Run Visualization")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a3a5a, stop:1 #3a4a7a);
                font-size: 16px;
                border-radius: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a4a7a, stop:1 #4a5a8a);
            }
        """)
        self.run_btn.clicked.connect(self.on_run)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8a2a2a, stop:1 #a03a3a);
                font-size: 16px;
                border-radius: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a03a3a, stop:1 #b04a4a);
            }
            QPushButton:disabled {
                background: #444;
                color: #888;
            }
        """)
        self.stop_btn.clicked.connect(self.on_stop)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar { height: 5px; border: none; background: #2d2d2d; } QProgressBar::chunk { background: #5a7a9a; }")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.run_btn, 2)
        btn_layout.addWidget(self.stop_btn, 1)

        exec_layout.addLayout(btn_layout)
        exec_layout.addWidget(self.progress)
        exec_group.setLayout(exec_layout)
        left_layout.addWidget(exec_group)

        # Right Panel
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)

        # 3. Preview
        preview_group = QGroupBox("Results Preview")
        preview_layout = QVBoxLayout()
        
        self.image_label = ResizingLabel()
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setStyleSheet("background-color: #1e1e1e; border: none; color: #888; font-size: 11px;")

        preview_layout.addWidget(self.image_label, 1)
        preview_layout.addWidget(self.log_area)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group, 1)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select CSV Data File", filter="CSV Files (*.csv)")
        if f:
            self.file_label.setText(f)

    def clear_file(self):
        self.file_label.setText("Default: Use Clustering Results")

    def update_params(self, algo):
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        self.params = {}
        if algo == "t-SNE":
            sb_perp = QSpinBox()
            sb_perp.setRange(5, 100)
            sb_perp.setValue(30)
            self.params['perplexity'] = sb_perp
            self.param_layout.addRow("Perplexity:", sb_perp)
            
            sb_lr = QDoubleSpinBox()
            sb_lr.setRange(10, 1000)
            sb_lr.setValue(200)
            self.params['learning_rate'] = sb_lr
            self.param_layout.addRow("Learning Rate:", sb_lr)
            
            sb_iter = QSpinBox()
            sb_iter.setRange(250, 5000)
            sb_iter.setValue(1000)
            self.params['n_iter'] = sb_iter
            self.param_layout.addRow("Iterations:", sb_iter)

            sb_seed = QSpinBox()
            sb_seed.setRange(0, 10000)
            sb_seed.setValue(42)
            self.params['random_state'] = sb_seed
            self.param_layout.addRow("Random Seed:", sb_seed)

        elif algo == "UMAP":
            sb_n = QSpinBox()
            sb_n.setRange(2, 100)
            sb_n.setValue(15)
            self.params['n_neighbors'] = sb_n
            self.param_layout.addRow("Neighbors:", sb_n)
            
            sb_dist = QDoubleSpinBox()
            sb_dist.setRange(0.0, 1.0)
            sb_dist.setSingleStep(0.1)
            sb_dist.setValue(0.1)
            self.params['min_dist'] = sb_dist
            self.param_layout.addRow("Min Dist:", sb_dist)
            
            cb_metric = QComboBox()
            cb_metric.addItems(["euclidean", "manhattan", "cosine", "correlation"])
            self.params['metric'] = cb_metric
            self.param_layout.addRow("Metric:", cb_metric)

            sb_seed = QSpinBox()
            sb_seed.setRange(0, 10000)
            sb_seed.setValue(42)
            self.params['random_state'] = sb_seed
            self.param_layout.addRow("Random Seed:", sb_seed)

    def on_run(self):
        # Note: We assume data is already loaded from Clustering tab or shared state
        config = {
            'type': 'visualization',
            'algorithm': self.algo_combo.currentText(),
            'params': {k: v.value() if isinstance(v, (QSpinBox, QDoubleSpinBox)) else v.currentText() 
                       for k, v in self.params.items()},
            'custom_file': self.file_label.text() if "Default" not in self.file_label.text() else None
        }
        self.run_analysis_signal.emit(config)

    def on_stop(self):
        self.stop_analysis_signal.emit()
        self.log_area.append("Stopping visualization...")

    def update_log(self, text):
        self.log_area.append(text)
        
    def show_preview(self, image_path):
        self.image_label.set_image(image_path)

class CsvProcessorTab(QWidget):
    run_process_signal = pyqtSignal(dict) # To main window or worker
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Panel
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)

        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["CSV Splitter", "CSV Mapper"])
        self.mode_combo.currentTextChanged.connect(self.set_mode)
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        mode_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(mode_group)
        
        # 1. Data Input
        self.input_group = QGroupBox("CSV Input")
        input_layout = QVBoxLayout()
        self.file_btn = QPushButton("Select CSV File")
        self.file_btn.clicked.connect(self.select_file)
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        
        self.folder_btn = QPushButton("Select Folder (Check Consistency)")
        self.folder_btn.clicked.connect(self.select_folder)
        
        input_layout.addWidget(self.file_btn)
        input_layout.addWidget(self.file_label)
        input_layout.addWidget(self.folder_btn)
        self.input_group.setLayout(input_layout)
        left_layout.addWidget(self.input_group)
        
        # 2. Split Options
        self.split_group = QGroupBox("Split Options")
        split_layout = QVBoxLayout()
        
        # Row selection
        split_layout.addWidget(QLabel("Select Rows (Group by Label):"))
        self.row_list = QListWidget()
        # Use checkboxes for selection
        self.row_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        split_layout.addWidget(self.row_list)
        
        # Column selection
        split_layout.addWidget(QLabel("Select Columns:"))
        self.col_list = QListWidget()
        # Use checkboxes for selection
        self.col_list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        split_layout.addWidget(self.col_list)
        
        self.split_group.setLayout(split_layout)
        left_layout.addWidget(self.split_group)
        
        self.map_group = QGroupBox("CSV Mapper")
        map_layout = QVBoxLayout()
        self.map_folder_btn = QPushButton("Select Folder for Mapping")
        self.map_folder_btn.clicked.connect(self.select_map_folder)
        self.map_folder_label = QLabel("No folder selected")
        self.map_folder_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")

        self.map_file_btn = QPushButton("Select Mapping CSV")
        self.map_file_btn.clicked.connect(self.select_map_file)
        self.map_file_label = QLabel("No mapping file selected")
        self.map_file_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")

        map_layout.addWidget(self.map_folder_btn)
        map_layout.addWidget(self.map_folder_label)
        map_layout.addWidget(self.map_file_btn)
        map_layout.addWidget(self.map_file_label)
        self.map_group.setLayout(map_layout)
        left_layout.addWidget(self.map_group)

        left_layout.addStretch(1)

        exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout()

        self.run_btn = QPushButton("Run Processing")
        self.run_btn.setMinimumHeight(40)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a3a5a, stop:1 #3a4a7a);
                font-size: 14px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a4a7a, stop:1 #4a5a8a);
            }
        """)
        self.run_btn.clicked.connect(self.on_process)
        exec_layout.addWidget(self.run_btn)

        self.map_run_btn = QPushButton("Run Mapping")
        self.map_run_btn.setMinimumHeight(40)
        self.map_run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a3a5a, stop:1 #3a4a7a);
                font-size: 14px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a4a7a, stop:1 #4a5a8a);
            }
        """)
        self.map_run_btn.clicked.connect(self.on_map)
        exec_layout.addWidget(self.map_run_btn)

        exec_group.setLayout(exec_layout)
        exec_group.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        left_layout.addWidget(exec_group)
        
        # Right Panel: Data Preview
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        preview_group = QGroupBox("Data Preview (First 100 rows)")
        preview_layout = QVBoxLayout()
        
        self.table_view = QTableView()
        self.model = PandasModel()
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.setStyleSheet("QTableView { background-color: #1e1e1e; gridline-color: #333; } QHeaderView::section { background-color: #2d2d2d; padding: 4px; border: 1px solid #333; }")
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(80)
        self.log_area.setStyleSheet("background-color: #1e1e1e; border: none; color: #888; font-size: 11px;")
        
        preview_layout.addWidget(self.table_view)
        preview_layout.addWidget(self.log_area)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)
        
        self.row_options = {} # {label_name: [indices]}
        self.current_file_path = None
        self.current_folder_path = None
        self.current_map_folder_path = None
        self.current_map_file_path = None
        self.mode_combo.setCurrentText("CSV Splitter")
        self.set_mode("CSV Splitter")

    def set_mode(self, mode):
        splitter_mode = mode == "CSV Splitter"
        self.input_group.setVisible(splitter_mode)
        self.split_group.setVisible(splitter_mode)
        self.run_btn.setVisible(splitter_mode)
        self.map_group.setVisible(not splitter_mode)
        self.map_run_btn.setVisible(not splitter_mode)

    def select_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select CSV", filter="CSV Files (*.csv)")
        if f:
            self.file_label.setText(f)
            self.current_file_path = f
            self.current_folder_path = None
            # Emit signal or load directly to populate lists?
            # We need to read it to populate lists. 
            # Ideally done via worker, but for metadata reading small files is ok.
            # We'll emit a signal to MainWindow to load it via splitter logic.
            self.run_process_signal.emit({'type': 'load_file', 'path': f})

    def select_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder")
        if d:
            self.file_label.setText(d)
            self.current_folder_path = d
            self.current_file_path = None
            self.run_process_signal.emit({'type': 'load_folder', 'path': d})

    def select_map_folder(self):
        d = QFileDialog.getExistingDirectory(self, "Select Folder to Map")
        if d:
            self.current_map_folder_path = d
            self.map_folder_label.setText(d)

    def select_map_file(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Mapping CSV", filter="CSV Files (*.csv)")
        if f:
            self.current_map_file_path = f
            self.map_file_label.setText(f)

    def on_map(self):
        if not self.current_map_folder_path:
            self.log_area.append("Error: No folder selected for mapping.")
            return
        if not self.current_map_file_path:
            self.log_area.append("Error: No mapping CSV selected.")
            return

        self.run_process_signal.emit({
            'type': 'map_folder',
            'folder_path': self.current_map_folder_path,
            'mapping_csv_path': self.current_map_file_path
        })

    def on_file_loaded(self, df_head, row_opts, col_opts):
        """Called by MainWindow when file is loaded successfully"""
        # Update Table
        self.model.set_data(df_head)
        self.log_area.append(f"Loaded file. Shape: {df_head.shape} (preview)")
        
        # Update Row List
        self.row_list.clear()
        self.row_options = row_opts
        if row_opts:
            # Custom sort key to handle numeric sorting (1, 2, ... 10) instead of string sorting (1, 10, 2...)
            def natural_sort_key(s):
                import re
                return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', str(s))]

            for label in sorted(row_opts.keys(), key=natural_sort_key):
                item = QListWidgetItem(label)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.row_list.addItem(item)
            self.log_area.append(f"Found row groups: {list(row_opts.keys())}")
        else:
            item = QListWidgetItem("All Rows (No group column found)")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            self.row_list.addItem(item)
            self.row_options = {"All Rows": []}
        
        # Update Col List
        self.col_list.clear()
        
        # Determine default check state
        # If 'cluster_label' or 'cell_type' is present, default check only them.
        # Otherwise, default uncheck all.
        special_cols = {'cluster_label', 'cell_type'}
        found_special = any(c in special_cols for c in col_opts)
        
        for col in col_opts:
            item = QListWidgetItem(col)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            if found_special:
                if col in special_cols:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
            else:
                # No special columns found -> Uncheck all
                item.setCheckState(Qt.CheckState.Unchecked)
                
            self.col_list.addItem(item)

    def on_process(self):
        if not self.current_file_path and not self.current_folder_path:
            self.log_area.append("Error: No file or folder selected.")
            return

        selected_row_labels = []
        for i in range(self.row_list.count()):
            item = self.row_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_row_labels.append(item.text())

        selected_cols = []
        for i in range(self.col_list.count()):
            item = self.col_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_cols.append(item.text())
        
        if not selected_cols:
            self.log_area.append("Error: No columns selected.")
            return
            
        # If no rows selected, assume all? Or error?
        # Let's assume if nothing selected, we select nothing (empty csv).
        # But typically user might want all.
        if not selected_row_labels:
            self.log_area.append("Warning: No row groups selected. Output might be empty.")
        
        # Collect indices
        final_row_indices = []
        if "All Rows" in self.row_options and "All Rows" in selected_row_labels:
             # Logic for all rows
             final_row_indices = None # None means all
        else:
            for label in selected_row_labels:
                if label in self.row_options:
                    val = self.row_options[label]
                    if isinstance(val, list):
                        final_row_indices.extend(val)
                    else:
                        final_row_indices.append(val)
            # If we had labels but user selected none, final_row_indices is empty.

        if self.current_folder_path:
            config = {
                'type': 'split_folder',
                'row_values': final_row_indices if final_row_indices is not None else None,
                'col_indices': selected_cols,
                'folder_path': self.current_folder_path,
                'output_base_dir': self.current_folder_path
            }
        else:
            config = {
                'type': 'split_csv',
                'row_indices': final_row_indices,
                'col_indices': selected_cols,
                'output_base_dir': os.path.dirname(self.current_file_path)
            }
        self.run_process_signal.emit(config)

    def update_log(self, text):
        self.log_area.append(text)


class DifferenceAnalysisTab(QWidget):
    run_analysis_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(20)

        mode_group = QGroupBox("Mode")
        mode_layout = QVBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Percentage Stacked Bar Chart"])
        self.mode_combo.currentTextChanged.connect(self.set_mode)
        mode_layout.addWidget(self.mode_combo)
        mode_group.setLayout(mode_layout)
        left_layout.addWidget(mode_group)

        self.input_group = QGroupBox("Data Input")
        input_layout = QVBoxLayout()
        self.dir_btn = QPushButton("Select Folder")
        self.dir_btn.setMinimumHeight(40)
        self.dir_btn.clicked.connect(self.select_directory)
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dir_label.setStyleSheet("color: #a0a0a0; font-size: 11px;")
        input_layout.addWidget(self.dir_btn)
        input_layout.addWidget(self.dir_label)
        self.input_group.setLayout(input_layout)
        left_layout.addWidget(self.input_group)

        left_layout.addStretch(1)

        self.exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout()
        self.run_btn = QPushButton("Run Difference Analysis")
        self.run_btn.setMinimumHeight(50)
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2a3a5a, stop:1 #3a4a7a);
                font-size: 16px;
                border-radius: 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3a4a7a, stop:1 #4a5a8a);
            }
        """)
        self.run_btn.clicked.connect(self.on_run)

        self.progress = QProgressBar()
        self.progress.setStyleSheet("QProgressBar { height: 5px; border: none; background: #2d2d2d; } QProgressBar::chunk { background: #5a7a9a; }")

        exec_layout.addWidget(self.run_btn)
        exec_layout.addWidget(self.progress)
        self.exec_group.setLayout(exec_layout)
        left_layout.addWidget(self.exec_group)

        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(20)

        preview_group = QGroupBox("Results Preview")
        preview_layout = QVBoxLayout()

        self.image_label = ResizingLabel()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setStyleSheet("background-color: #1e1e1e; border: none; color: #888; font-size: 11px;")

        preview_layout.addWidget(self.image_label, 1)
        preview_layout.addWidget(self.log_area)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group, 1)

        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self.mode_combo.setCurrentText("Percentage Stacked Bar Chart")
        self.set_mode("Percentage Stacked Bar Chart")

    def set_mode(self, mode):
        self.input_group.setVisible(True)
        self.exec_group.setVisible(True)

    def select_directory(self):
        d = QFileDialog.getExistingDirectory(self, "Select Data Directory")
        if d:
            self.dir_label.setText(d)

    def on_run(self):
        input_dir = self.dir_label.text()
        if not os.path.isdir(input_dir):
            self.update_log("Error: Invalid directory selected.")
            return

        self.run_analysis_signal.emit({
            "type": "difference_analysis",
            "mode": self.mode_combo.currentText(),
            "input_dir": input_dir,
        })

    def update_log(self, text):
        self.log_area.append(text)

    def show_preview(self, image_path):
        self.image_label.set_image(image_path)
