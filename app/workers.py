from PySide6.QtCore import QThread, Signal

class Worker(QThread):
    # 定義兩個信號：一個傳送文字 Log，一個通知任務完成
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, task_func, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.kwargs = kwargs

    def run(self):
        """
        QThread 的入口點。
        """
        try:
            # 這裡我們將 self.log_signal.emit 傳遞給 logic 函式
            # 這樣 logic 函式就可以透過這個 callback 發送 log 到 UI
            self.task_func(self.log_signal.emit, **self.kwargs)
        except Exception as e:
            self.log_signal.emit(f"❌ 執行緒發生嚴重錯誤: {str(e)}")
        finally:
            self.finished_signal.emit()