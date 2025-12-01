from PySide6.QtCore import QThread, Signal

class Worker(QThread):
    # log_signal: 文字 Log
    # progress_signal: 總體進度 (0-100)
    # current_file_signal: 當前處理的檔名 (str)
    # file_progress_signal: 當前檔案的進度 (0-100)
    # finished_signal: 任務完成
    log_signal = Signal(str)
    progress_signal = Signal(int)
    current_file_signal = Signal(str)
    file_progress_signal = Signal(int)
    finished_signal = Signal()

    def __init__(self, task_func, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.kwargs = kwargs

    def run(self):
        try:
            self.task_func(
                log_callback=self.log_signal.emit, 
                progress_callback=self.progress_signal.emit,
                current_file_callback=self.current_file_signal.emit,
                file_progress_callback=self.file_progress_signal.emit,
                **self.kwargs
            )
        except Exception as e:
            self.log_signal.emit(f"❌ 執行緒發生嚴重錯誤: {str(e)}")
        finally:
            self.finished_signal.emit()