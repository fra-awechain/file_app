import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from app.ui import MainWindow

# 定義全域樣式表 (QSS)
STYLESHEET = """
/* 全域字體與顏色 */
QWidget {
    font-family: 'Segoe UI', 'Microsoft JhengHei UI', sans-serif;
    font-size: 14px;
    color: #333333;
}

/* 右側面板背景 */
QWidget#RightFrame, QScrollArea, QWidget#ScrollContent {
    background-color: #dfd4ba;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background-color: #dfd4ba;
}

/* 通用按鈕 */
QPushButton {
    background-color: #f8f9fa;
    border: 1px solid #999;
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 600;
    color: #333;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #e2e6ea;
    border-color: #666;
}
QPushButton:pressed {
    background-color: #dae0e5;
}

/* 開始執行按鈕 (強制藍底) */
QPushButton#ExecBtn {
    background-color: #2563eb; /* Blue-600 */
    color: white;
    border: none; /* 移除邊框以確保底色滿版 */
    font-size: 16px;
    padding: 10px 24px;
    border-radius: 6px;
    font-weight: bold;
}
QPushButton#ExecBtn:hover {
    background-color: #1d4ed8; /* Blue-700 */
}
QPushButton#ExecBtn:pressed {
    background-color: #1e40af; /* Blue-800 */
}

/* 清除 Log 按鈕 (小顆) */
QPushButton#ClearLogBtn {
    background-color: #64748b;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 12px;
}
QPushButton#ClearLogBtn:hover {
    background-color: #475569;
}

/* 輸入框與選單 */
QLineEdit, QComboBox, QSpinBox {
    border: 1px solid #888;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #ffffff;
    selection-background-color: #3b82f6;
    min-height: 26px;
    color: #333;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #3b82f6;
}

/* ComboBox 下拉選單背景為白色 */
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    selection-background-color: #3b82f6;
    selection-color: #ffffff;
    border: 1px solid #888;
    outline: none;
}

/* 通用 Checkbox (加上底色塊) */
QCheckBox {
    spacing: 8px;
    padding: 8px;
    background-color: #f1f5f9; /* 淺灰底 */
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

/* 特殊樣式：貼合尺寸裁切 Checkbox (粉紅色底) */
QCheckBox#PinkCheck {
    background-color: #fce7f3; /* Pink-100 */
    color: #9d174d; /* Pink-800 */
    border: 1px solid #fbcfe8;
}

/* 總進度條 (藍色，文字置中) */
QProgressBar#TotalProgress {
    border: 1px solid #94a3b8;
    background-color: #e2e8f0; /* 預設底色 (Slate-200) */
    border-radius: 6px;
    height: 20px;
    text-align: center;
    color: #0f172a; /* 文字顏色 */
    font-weight: bold;
}
QProgressBar#TotalProgress::chunk {
    background-color: #3b82f6; /* Blue */
    border-radius: 5px;
}

/* 檔案進度條 (綠色，無文字) */
QProgressBar#FileProgress {
    border: 1px solid #cbd5e1;
    background-color: #e2e8f0; /* 預設底色 */
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: transparent; 
}
QProgressBar#FileProgress::chunk {
    background-color: #22c55e; /* Green */
    border-radius: 3px;
}

/* Scrollbar */
QScrollBar:vertical {
    border: none;
    background: #e0e0e0;
    width: 14px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #999;
    min-height: 20px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #777;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* GroupBox */
QGroupBox {
    font-weight: bold;
    border: 1px solid #a89f8a;
    border-radius: 8px;
    margin-top: 20px;
    padding-top: 20px;
    background-color: rgba(255, 255, 255, 0.5); 
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #222;
}

/* 側邊欄樣式 */
QWidget#SidebarFrame {
    background-color: #1e293b; 
    border-right: 1px solid #0f172a;
}
QFrame#SidebarBtn {
    background-color: transparent;
    border-radius: 8px;
    margin: 4px 12px;
}
QFrame#SidebarBtn:hover {
    background-color: #334155;
}
QLabel#SidebarBtnText {
    color: #cbd5e1;
    font-weight: 500;
}

/* 拖曳區塊樣式 */
QLabel#DragDrop {
    border: 2px dashed #999;
    border-radius: 6px;
    color: #666;
    background-color: rgba(255, 255, 255, 0.6);
    font-size: 12px;
    min-width: 70px;
    qproperty-alignment: AlignCenter;
}
QLabel#DragDrop:hover {
    border-color: #2563eb;
    background-color: rgba(37, 99, 235, 0.1);
    color: #2563eb;
    font-weight: bold;
}
"""

def main():
    app = QApplication(sys.argv)
    
    font_family = "Segoe UI" if os.name == "nt" else "PingFang TC"
    app.setFont(QFont(font_family, 10))
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()