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
    font-size: 16px;
    color: #333333;
}

/* 1. 修正 Checkbox (回歸系統樣式，但微調間距) */
QCheckBox {
    spacing: 8px;
    padding: 4px;
}
/* 移除所有自定義 indicator 樣式，讓它顯示原生勾選框，確保功能正常 */

/* 2. 右側面板背景 (米黃色) */
QWidget#RightFrame, QScrollArea, QWidget#ScrollContent {
    background-color: #dfd4ba;
    border: none;
}
/* 強制 ScrollArea 的 viewport 也是米黃色 */
QScrollArea > QWidget > QWidget {
    background-color: #dfd4ba;
}

/* 3. 按鈕樣式 (一般按鈕) */
QPushButton {
    background-color: #f8f9fa;
    border: 1px solid #999;
    border-radius: 6px;
    padding: 8px 16px;
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

/* 4. 執行按鈕 (Action Button - 強制藍色) */
QPushButton#ExecBtn {
    background-color: #2563eb;
    color: white;
    border: 1px solid #1d4ed8;
    font-size: 18px;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: bold;
}
QPushButton#ExecBtn:hover {
    background-color: #1d4ed8;
}
QPushButton#ExecBtn:pressed {
    background-color: #1e40af;
}

/* 5. 輸入框 (白底 + 加高) */
QLineEdit, QComboBox, QSpinBox {
    border: 1px solid #888;
    border-radius: 6px;
    padding: 4px 8px; /* 內距 */
    background-color: #ffffff; /* 白底 */
    selection-background-color: #3b82f6;
    min-height: 28px; /* 加高 */
    color: #333;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border: 2px solid #3b82f6;
}

/* 6. 進度條 (修復樣式) */
QProgressBar {
    border: 1px solid #999;
    background-color: #e0e0e0; /* 灰色底 */
    border-radius: 6px;
    height: 16px; /* 加高 */
    text-align: center;
    color: black;
}
QProgressBar::chunk {
    background-color: #3b82f6; /* 藍色進度 */
    border-radius: 5px;
}

/* 7. Scrollbar (灰色樣式) */
QScrollBar:vertical {
    border: none;
    background: #e0e0e0; /* 淺灰軌道 */
    width: 14px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #999; /* 深灰拉桿 */
    min-height: 20px;
    border-radius: 7px;
}
QScrollBar::handle:vertical:hover {
    background: #777;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 8. GroupBox */
QGroupBox {
    font-weight: bold;
    border: 1px solid #a89f8a;
    border-radius: 8px;
    margin-top: 24px;
    padding-top: 24px;
    background-color: rgba(255, 255, 255, 0.4); 
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #222;
}

/* 9. 側邊欄樣式 */
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

/* 10. 拖曳區塊 (DragDrop) - 確保樣式生效 */
QLabel#DragDrop {
    border: 2px dashed #777;
    border-radius: 6px;
    color: #555;
    background-color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
    min-width: 60px;
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
    
    # 設定字型
    font_family = "Segoe UI" if os.name == "nt" else "PingFang TC"
    app.setFont(QFont(font_family, 10))
    
    # 應用樣式表
    app.setStyleSheet(STYLESHEET)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()