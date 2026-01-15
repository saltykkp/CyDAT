from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
import sys
import platform

def apply_dark_theme(app: QApplication):
    """Applies a dark theme to the Qt Application using Fusion style."""
    app.setStyle("Fusion")
    
    dark_palette = QPalette()
    
    # Define colors
    dark_color = QColor(45, 45, 45)
    disabled_color = QColor(127, 127, 127)
    text_color = QColor(220, 220, 220)
    highlight_color = QColor(102, 102, 102)
    
    # Set palette colors
    dark_palette.setColor(QPalette.ColorRole.Window, dark_color)
    dark_palette.setColor(QPalette.ColorRole.WindowText, text_color)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, text_color)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
    dark_palette.setColor(QPalette.ColorRole.Text, text_color)
    dark_palette.setColor(QPalette.ColorRole.Button, dark_color)
    dark_palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, highlight_color)
    dark_palette.setColor(QPalette.ColorRole.Highlight, highlight_color)
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    
    # Disabled states
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, disabled_color)

    app.setPalette(dark_palette)
    
    # Additional styling via stylesheet
    app.setStyleSheet("""
        QToolTip { 
            color: #ffffff; 
            background-color: #666666; 
            border: 1px solid white; 
        }
        QGroupBox {
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
        }
        QProgressBar {
            border: 1px solid #555555;
            border-radius: 3px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #666666;
            width: 10px; 
            margin: 0.5px;
        }
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTextEdit {
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 2px;
            background-color: #1e1e1e;
            selection-background-color: #666666;
        }
        QPushButton {
            background-color: #505050;
            border: 1px solid #6b6b6b;
            color: #ffffff;
            border-radius: 4px;
            padding: 6px;
            min-width: 80px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #606060;
            border-color: #808080;
        }
        QPushButton:pressed {
            background-color: #3a3a3a;
            border-color: #555555;
        }
        QHeaderView::section {
            background-color: #3d3d3d;
            border: 1px solid #555555;
            padding: 2px;
        }
        QTabWidget::pane {
            border: 1px solid #555555;
        }
    """)

def apply_windows_dark_title_bar(window_handle):
    """
    Applies Windows 10/11 dark mode to the title bar using DWM API.
    window_handle: The HWND (int) of the window.
    """
    if platform.system() != "Windows":
        return

    try:
        import ctypes
        from ctypes import c_int, byref, windll
        
        # DWMWA_USE_IMMERSIVE_DARK_MODE is 20 (Windows 11 build 22000+ and Windows 10 build 19041+)
        # Prior to that it was 19, but 20 is the documented one for recent versions.
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19
        
        hwnd = window_handle
        attribute = DWMWA_USE_IMMERSIVE_DARK_MODE
        
        # Try setting attribute 20
        value = c_int(1)
        result = windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, byref(value), 4)
        
        if result != 0:
            # Fallback for older Windows 10 versions
            attribute = DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1
            windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, byref(value), 4)
            
    except Exception as e:
        print(f"Failed to set dark title bar: {e}")

def set_window_title_bar_color(window_handle, r, g, b):
    """
    Sets the title bar color using Windows DWM API.
    Only works on Windows 11 Build 22000+.
    """
    if platform.system() != "Windows":
        return

    try:
        import ctypes
        from ctypes import c_int, byref, windll
        
        # DWMWA_CAPTION_COLOR = 35
        DWMWA_CAPTION_COLOR = 35
        
        # Color format: 0x00BBGGRR
        color = r | (g << 8) | (b << 16)
        
        hwnd = window_handle
        value = c_int(color)
        
        windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 
            DWMWA_CAPTION_COLOR, 
            byref(value), 
            4
        )
            
    except Exception as e:
        print(f"Failed to set title bar color: {e}")
