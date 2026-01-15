from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                             QApplication, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QPen, QColor, QBrush

class TitleBarButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Explicitly set fixed size to ensure compact look
        # Adjusted to 32px based on user feedback
        self.setFixedSize(32, 35)
        self.setText("")  # No text, we paint ourselves

    def get_bg_color(self):
        if self.objectName() == "btnClose" and self.underMouse():
            return QColor("#e81123")
        if self.underMouse():
            return QColor("#3d3d3d")
        return QColor("#2b2b2b")

    def paintEvent(self, event):
        # We handle background painting to ensure it matches exactly before drawing icon
        # But we can also let stylesheet handle bg if we want, but manual control is safer for custom paint
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw background manually to ensure we are on top of it correctly
        bg_color = self.get_bg_color()
        painter.fillRect(self.rect(), bg_color)

        # Icon Style
        icon_color = QColor("#eaeaea")
        pen = QPen(icon_color)
        pen.setWidth(1)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        cx = self.width() / 2
        cy = self.height() / 2
        
        # Adjust cy slightly down to center visually in 35px height
        # The button is 35px high. Center is 17.5. 
        # But visuals might look better if integer aligned or tweaked.
        # Let's try to ensure integer coordinates for crisp lines
        cx = int(cx)
        cy = int(cy)
        
        self.draw_icon(painter, cx, cy)

    def draw_icon(self, painter, cx, cy):
        pass

class MinimizeButton(TitleBarButton):
    def draw_icon(self, painter, cx, cy):
        # Draw a horizontal line
        painter.drawLine(int(cx - 5), int(cy), int(cx + 5), int(cy))

class MaximizeButton(TitleBarButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_maximized = False

    def set_maximized(self, state):
        self.is_maximized = state
        self.update()

    def draw_icon(self, painter, cx, cy):
        bg_color = self.get_bg_color()
        
        if self.is_maximized:
            # Restore Icon (Two overlapping squares)
            # Back rect (top-right)
            painter.drawRoundedRect(int(cx - 3), int(cy - 5), 8, 8, 1, 1)
            
            # Front rect (bottom-left) - fill with bg to mask lines behind it
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(int(cx - 5), int(cy - 3), 8, 8, 1, 1)
        else:
            # Maximize Icon (Rounded Rect)
            painter.drawRoundedRect(int(cx - 5), int(cy - 5), 10, 10, 2, 2)

class CloseButton(TitleBarButton):
    def draw_icon(self, painter, cx, cy):
        # Draw X
        painter.drawLine(int(cx - 5), int(cy - 5), int(cx + 5), int(cy + 5))
        painter.drawLine(int(cx + 5), int(cy - 5), int(cx - 5), int(cy + 5))


from pathlib import Path

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.parent_window = parent
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(10) # Spacing between icon and title
        
        # Icon
        self.icon_label = QLabel()
        icon_path = str(Path(__file__).resolve().parent.parent.parent / "resources" / "icon.png")
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            self.icon_label.setPixmap(pixmap.scaled(20, 20, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_label)
        
        # Title
        self.title_label = QLabel("CyDAT")
        self.title_label.setStyleSheet("""
            color: white;
            font-family: 'Segoe UI', sans-serif;
            font-weight: bold;
            font-size: 14px;
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Window Controls Layout
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)

        # Minimize - use a lighter/thinner dash
        self.btn_min = MinimizeButton()
        self.btn_min.clicked.connect(self.minimize_window)
        controls_layout.addWidget(self.btn_min)
        
        # Maximize/Restore - use a thinner box
        self.btn_max = MaximizeButton()
        self.btn_max.clicked.connect(self.maximize_restore_window)
        controls_layout.addWidget(self.btn_max)
        
        # Close - use a thinner X
        self.btn_close = CloseButton()
        self.btn_close.clicked.connect(self.close_window)
        self.btn_close.setObjectName("btnClose") # For custom hover style
        controls_layout.addWidget(self.btn_close)

        layout.addLayout(controls_layout)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
            }
        """)

    def minimize_window(self):
        if self.parent_window:
            if hasattr(self.parent_window, 'toggle_minimize'):
                self.parent_window.toggle_minimize()
            else:
                self.parent_window.showMinimized()

    def maximize_restore_window(self):
        if self.parent_window:
            if hasattr(self.parent_window, 'toggle_maximize'):
                self.parent_window.toggle_maximize()
            elif self.parent_window.isMaximized():
                self.parent_window.showNormal()
                self.btn_max.set_maximized(False)
            else:
                self.parent_window.showMaximized()
                self.btn_max.set_maximized(True)

    def close_window(self):
        if self.parent_window:
            if hasattr(self.parent_window, 'toggle_close'):
                self.parent_window.toggle_close()
            else:
                self.parent_window.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_window.windowHandle().startSystemMove()
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_restore_window()
            event.accept()
