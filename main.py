import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from app.ui import MainWindow

# 定義全域樣式表 (QSS)
STYLESHEET = """
/* 全域設定 */
QWidget {
    font-family: 'Segoe UI', 'Microsoft JhengHei UI', sans-serif;
    font-size: 16px;
    color: #333333;
}

/* 側邊欄樣式 (模擬 Slate-800) */
QWidget#SidebarFrame {
    background-color: #1e293b; 
    border-right: 1px solid #0f172a;
}

/* 側邊欄按鈕 (未選中) */
QFrame#SidebarBtn {
    background-color: transparent;
    border-radius: 8px;
    margin: 4px 12px;
}
QFrame#SidebarBtn:hover {
    background-color: #334155; /* slate-700 */
}
/* 側邊欄按鈕文字 */
QLabel#SidebarBtnText {
    color: #cbd5e1; /* slate-300 */
    font-weight: 500;
}
/* 側邊欄按鈕 (選中狀態) - 在 Python Code 中動態切換 Style，這裡定義通用部分 */

/* 右側面板樣式 (強制底色 #dfd4ba) */
QWidget#RightFrame, QScrollArea, QWidget#ScrollContent {
    background-color: #dfd4ba;
}

/* 右側面板內的元件樣式 */
QGroupBox {
    font-weight: bold;
    border: 1px solid #a89f8a;
    border-radius: 8px;
    margin-top: 24px;
    padding-top: 16px;
    background-color: rgba(255, 255, 255, 0.2); 
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #4b5563; /* gray-600 */
}

/* 輸入框與下拉選單 - 加大與現代化 */
QLineEdit, QComboBox, QSpinBox {
    border: 1px solid #9ca3af;
    border-radius: 6px;
    padding: 6px 8px; /* 加大內距 */
    background-color: #ffffff;
    selection-background-color: #3b82f6;
    min-height: 24px; 
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #3b82f6; /* Focus ring */
}

/* 按鈕樣式 */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 600;
    color: #475569;
}
QPushButton:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
}
QPushButton:pressed {
    background-color: #e2e8f0;
}

/* 主要執行按鈕 (Action Button) */
QPushButton#ExecBtn {
    background-color: #2563eb; /* blue-600 */
    color: white;
    border: none;
    font-size: 18px;
    padding: 12px 24px;
    border-radius: 8px;
}
QPushButton#ExecBtn:hover {
    background-color: #1d4ed8;
}

/* 進度條 */
QProgressBar {
    border: none;
    background-color: #e2e8f0;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #3b82f6;
    border-radius: 4px;
}

/* 滑桿 */
QSlider::groove:horizontal {
    border: 1px solid #bbb;
    background: white;
    height: 6px;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #3b82f6;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #f8fafc;
    border: 1px solid #64748b;
    width: 18px;
    height: 18px;
    margin: -7px 0;
    border-radius: 9px;
}
"""

def main():
    app = QApplication(sys.argv)
    
    # 設定字型
    font_family = "Segoe UI" if os.name == "nt" else "PingFang TC"
    app.setFont(QFont(font_family, 10)) # 這裡設 10pt 約等於 13px，主要靠 QSS 的 16px 覆蓋
    
    # 應用樣式表
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()