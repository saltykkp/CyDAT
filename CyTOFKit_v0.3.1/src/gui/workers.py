from PyQt6.QtCore import QThread, pyqtSignal
import traceback
import sys

class WorkerSignals(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class AnalysisWorker(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            output = self.func(*self.args, **self.kwargs)
            self.result.emit(output)
        except Exception as e:
            # traceback.print_exc()
            self.error.emit(str(e))
        finally:
            self.finished.emit()
