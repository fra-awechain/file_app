###### ------- [安裝程式]打包指令：pyinstaller --noconsole --onefile main.py

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.ui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # 設定全域字型
    font_name = "PingFang TC" if sys.platform == "darwin" else "Microsoft JhengHei UI"
    app.setFont(QFont(font_name, 10))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()