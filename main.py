import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.ui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # --- 全域字型設定 ---
    # 針對不同作業系統設定最佳顯示字型
    if sys.platform == "darwin": # Mac OS
        # Mac 預設 PingFang TC 顯示效果較佳
        font = QFont("PingFang TC", 10) 
    else: # Windows
        # Windows 使用微軟正黑體 UI
        font = QFont("Microsoft JhengHei UI", 10)
    
    app.setFont(font)
    
    # 啟動主視窗
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()