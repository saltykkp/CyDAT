from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from src.app_info import APP_NAME, APP_VERSION_LABEL


class StartupSplash(QWidget):
    def __init__(self, icon_path=None):
        super().__init__(None)
        self._icon_path = Path(icon_path) if icon_path else None
        self._status_prefix = "Starting"
        self._build_ui()

    def _build_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(720, 420)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 18, 18, 18)

        card = QFrame()
        card.setObjectName("splashCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(18)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(22)

        icon_label = QLabel()
        icon_label.setFixedSize(108, 108)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setObjectName("iconLabel")
        pixmap = self._load_icon_pixmap()
        if not pixmap.isNull():
            icon_label.setPixmap(
                pixmap.scaled(
                    96,
                    96,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        title_layout = QVBoxLayout()
        title_layout.setSpacing(6)

        app_name_label = QLabel(APP_NAME)
        app_name_label.setObjectName("appNameLabel")

        subtitle_label = QLabel("CyTOF Analysis Toolkit")
        subtitle_label.setObjectName("subtitleLabel")

        version_label = QLabel(APP_VERSION_LABEL)
        version_label.setObjectName("versionLabel")

        title_layout.addWidget(app_name_label)
        title_layout.addWidget(subtitle_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()

        header_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)
        header_layout.addLayout(title_layout, 1)

        desc_label = QLabel(
            "Integrated desktop workspace for CyTOF data analysis : "
            "Clustering ,Dim Reduction and Differential Analysis"
        )
        desc_label.setWordWrap(True)
        desc_label.setObjectName("descLabel")

        chips_layout = QHBoxLayout()
        chips_layout.setSpacing(10)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        for chip_text in [
            "Clustering Analysis",
            "Dim Reduction",
            "Heatmap",
            "Utils",
            "Difference Analysis",
        ]:
            chips_layout.addWidget(self._create_chip(chip_text))
        chips_layout.addStretch()

        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(8)

        self.status_label = QLabel("Starting...")
        self.status_label.setObjectName("statusLabel")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setObjectName("progressBar")

        hint_label = QLabel("Please wait while the application initializes.")
        hint_label.setObjectName("hintLabel")

        footer_layout.addWidget(self.status_label)
        footer_layout.addWidget(self.progress_bar)
        footer_layout.addWidget(hint_label)

        card_layout.addLayout(header_layout)
        card_layout.addWidget(desc_label)
        card_layout.addLayout(chips_layout)
        card_layout.addStretch()
        card_layout.addLayout(footer_layout)

        root_layout.addWidget(card)

        self.setStyleSheet(
            """
            QWidget {
                background: transparent;
            }
            QFrame#splashCard {
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #121827,
                    stop: 0.55 #1d1836,
                    stop: 1 #101728
                );
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
            }
            QLabel#iconLabel {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 18px;
            }
            QLabel#appNameLabel {
                color: #f4f7fb;
                font-size: 28px;
                font-weight: 700;
            }
            QLabel#subtitleLabel {
                color: #b8c2d6;
                font-size: 14px;
                letter-spacing: 0.3px;
            }
            QLabel#versionLabel {
                color: #8bd6ff;
                font-size: 13px;
                font-weight: 600;
                padding-top: 2px;
            }
            QLabel#descLabel {
                color: #d9dfeb;
                font-size: 14px;
                line-height: 1.4;
                padding: 8px 2px 0 2px;
            }
            QLabel#statusLabel {
                color: #f4f7fb;
                font-size: 13px;
                font-weight: 600;
            }
            QLabel#hintLabel {
                color: #a8b1c2;
                font-size: 12px;
            }
            QProgressBar#progressBar {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 5px;
            }
            QProgressBar#progressBar::chunk {
                border-radius: 5px;
                background-color: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #5b8cff,
                    stop: 0.5 #a55cff,
                    stop: 1 #13c296
                );
            }
            """
        )

    def _create_chip(self, text):
        chip = QLabel(text)
        chip.setStyleSheet(
            """
            QLabel {
                color: #edf2fb;
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 14px;
                padding: 6px 12px;
                font-size: 12px;
            }
            """
        )
        return chip

    def _load_icon_pixmap(self):
        if self._icon_path and self._icon_path.exists():
            return QPixmap(str(self._icon_path))
        return QPixmap()

    def center_on_screen(self):
        screen = self.screen()
        if screen is None:
            return
        geometry = screen.availableGeometry()
        self.move(geometry.center().x() - self.width() // 2, geometry.center().y() - self.height() // 2)

    def show_stage(self, message, progress):
        self._status_prefix = message
        self.status_label.setText(message)
        self.progress_bar.setValue(max(0, min(int(progress), 100)))

    def finish_and_close(self, window):
        self.show_stage("Startup complete.", 100)
        self.close()
        if window is not None:
            window.raise_()
            window.activateWindow()
