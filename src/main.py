import sys
import os
import time
import warnings
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# 1. Suppress specific warnings
# Suppress joblib/loky warning about physical cores
warnings.filterwarnings("ignore", message="Could not find the number of physical cores")
# Suppress seaborn/matplotlib GUI thread warning
warnings.filterwarnings("ignore", message="Starting a Matplotlib GUI outside of the main thread")

# 2. Fix joblib/loky warning about physical cores (wmic missing on Windows)
os.environ['LOKY_MAX_CPU_COUNT'] = str(os.cpu_count() or 4) # Fallback to 4 if None

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from src.app_info import APP_NAME, APP_USER_MODEL_ID
from src.gui.splash import StartupSplash
from src.gui.theme import apply_dark_theme, apply_windows_dark_title_bar, set_window_title_bar_color
from src.utils.runtime_paths import get_resource_path

def main():
    try:
        if os.name == "nt":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)

    resources_dir = get_resource_path("resources")
    icon_png_path = resources_dir / "icon.png"
    icon_ico_path = resources_dir / "icon.ico"
    splash_icon_path = icon_png_path if icon_png_path.exists() else icon_ico_path
    splash_started_at = time.perf_counter()

    splash = StartupSplash(splash_icon_path)
    splash.show()
    splash.center_on_screen()
    splash.show_stage("Launching application...", 8)
    app.processEvents()

    apply_dark_theme(app)
    splash.show_stage("Loading plotting backend...", 18)
    app.processEvents()

    # Import matplotlib only after the splash is visible, so the splash can appear sooner.
    import matplotlib
    matplotlib.use('Agg')

    if (not icon_ico_path.exists()) and icon_png_path.exists():
        try:
            from PIL import Image
            splash.show_stage("Preparing application icon...", 28)
            app.processEvents()
            img = Image.open(icon_png_path)
            img.save(icon_ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        except Exception:
            pass

    icon_path = icon_ico_path if icon_ico_path.exists() else icon_png_path
    app_icon = QIcon(str(icon_path))
    app.setWindowIcon(app_icon)
    splash.show_stage("Loading application modules...", 45)
    app.processEvents()

    from src.gui.main_window import MainWindow

    splash.show_stage("Preparing main workspace...", 72)
    app.processEvents()
    window = MainWindow()
    window.setWindowIcon(app_icon)
    splash.show_stage("Applying window style...", 88)
    app.processEvents()
    window.show()
    window.setWindowIcon(app_icon)
    
    # Apply dark title bar (Windows only)
    try:
        hwnd = int(window.winId())
        apply_windows_dark_title_bar(hwnd)
        # Set title bar to darker gray (#2D2D2D -> 45, 45, 45) to match theme background
        set_window_title_bar_color(hwnd, 45, 45, 45)

        if os.name == "nt" and icon_ico_path.exists():
            import ctypes
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x0010
            LR_DEFAULTSIZE = 0x0040
            hicon = ctypes.windll.user32.LoadImageW(None, str(icon_ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
            if hicon:
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
    except Exception as e:
        print(f"Failed to set dark title bar: {e}")

    min_splash_seconds = 1.4
    while time.perf_counter() - splash_started_at < min_splash_seconds:
        app.processEvents()
        time.sleep(0.02)

    splash.finish_and_close(window)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
