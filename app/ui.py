from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame, 
                               QMessageBox, QProgressBar, QColorDialog, QSlider, QSpinBox,
                               QDialog, QSizePolicy, QGridLayout)
from PySide6.QtCore import Qt, QSettings, Signal, QSize
from PySide6.QtGui import QTextCursor, QPixmap, QImage, QColor, QCursor, QIcon, QDragEnterEvent, QDropEvent

from app.workers import Worker
import app.logic as logic
import app.utils as utils

# -----------------------------------------------------------
# 自定義元件：SelectableLabel (可選取文字的 Label)
# -----------------------------------------------------------
class SelectableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.IBeamCursor)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

# -----------------------------------------------------------
# 自定義元件：DragDropArea (拖曳區塊)
# -----------------------------------------------------------
class DragDropArea(QLabel):
    fileDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__("拖放至此", parent)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        # 設定虛線邊框與樣式
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #888;
                border-radius: 6px;
                color: #666;
                background-color: rgba(255, 255, 255, 0.6);
                font-size: 12px;
                min-width: 70px;
                max-width: 80px;
            }
            QLabel:hover {
                border-color: #3b82f6;
                color: #3b82f6;
                background-color: rgba(59, 130, 246, 0.1);
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.fileDropped.emit(file_path)

# -----------------------------------------------------------
# 自定義元件：SidebarButton
# -----------------------------------------------------------
class SidebarButton(QFrame):
    clicked = Signal(int)

    def __init__(self, text, icon_char, index, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarBtn")
        self.index = index
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(60)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(15)

        self.indicator = QWidget()
        self.indicator.setFixedSize(4, 24)
        self.indicator.setStyleSheet("background-color: transparent; border-radius: 2px;")
        
        self.icon_label = QLabel(icon_char)
        self.icon_label.setStyleSheet("color: #94a3b8; font-size: 20px; background: transparent;")
        
        self.text_label = QLabel(text)
        self.text_label.setObjectName("SidebarBtnText")
        self.text_label.setStyleSheet("font-size: 16px; background: transparent;")
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def set_selected(self, selected):
        if selected:
            self.indicator.setStyleSheet("background-color: #38bdf8;")
            self.icon_label.setStyleSheet("color: #38bdf8; font-size: 20px; background: transparent;")
            self.text_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 16px; background: transparent;")
            self.setStyleSheet("background-color: #334155; border-radius: 8px;")
        else:
            self.indicator.setStyleSheet("background-color: transparent;")
            self.icon_label.setStyleSheet("color: #94a3b8; font-size: 20px; background: transparent;")
            self.text_label.setStyleSheet("color: #cbd5e1; font-weight: normal; font-size: 16px; background: transparent;")
            self.setStyleSheet("background-color: transparent;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)

# -----------------------------------------------------------
# 自定義元件：WhiteComboBox (強制白底黑字 + 自動寬度)
# -----------------------------------------------------------
class WhiteComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #9ca3af;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 24px;
            }
            QComboBox:focus {
                border: 2px solid #3b82f6;
            }
            QComboBox::drop-down {
                border: none;
                background: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #333333;
                selection-background-color: #3b82f6;
                selection-color: #ffffff;
                border: 1px solid #cbd5e1;
                outline: none;
            }
        """)

    def showPopup(self):
        width = self.width()
        fm = self.fontMetrics()
        max_item_width = 0
        for i in range(self.count()):
            item_width = fm.horizontalAdvance(self.itemText(i)) + 40 
            if item_width > max_item_width:
                max_item_width = item_width
        
        if max_item_width > width:
            self.view().setFixedWidth(max_item_width)
        else:
            self.view().setFixedWidth(width)
        super().showPopup()

# -----------------------------------------------------------
# 圖片填色 - 紋理選擇 Popup
# -----------------------------------------------------------
class TextureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("選擇填充圖片")
        self.resize(500, 600)
        self.image_path = ""
        self.scale = 100
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: #f0f0f0; color: #333;")
        
        self.preview_lbl = SelectableLabel("請選擇圖片")
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setStyleSheet("border: 2px dashed #ccc; background: #fff; color: #888;")
        self.preview_lbl.setMinimumHeight(300)
        layout.addWidget(self.preview_lbl)

        btn_browse = QPushButton("瀏覽圖片...")
        btn_browse.clicked.connect(self.browse_image)
        layout.addWidget(btn_browse)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(SelectableLabel("縮放比例 (%):"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 400)
        self.slider.setValue(100)
        self.slider.valueChanged.connect(self.update_preview)
        
        self.spin = QSpinBox()
        self.spin.setRange(1, 400)
        self.spin.setValue(100)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.spin.setValue)
        
        scale_layout.addWidget(self.slider)
        scale_layout.addWidget(self.spin)
        layout.addLayout(scale_layout)

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("確定")
        btn_ok.setStyleSheet("background-color: #2563eb; color: white; border:none; font-weight: bold; padding: 6px 16px; border-radius: 4px;")
        btn_ok.clicked.connect(self.accept)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        layout.addLayout(btn_box)

    def browse_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "選擇圖片", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.image_path = path
            self.update_preview()

    def update_preview(self):
        if not self.image_path: return
        self.scale = self.slider.value()
        try:
            pix = QPixmap(self.image_path)
            if pix.isNull(): return
            w = int(pix.width() * (self.scale / 100))
            h = int(pix.height() * (self.scale / 100))
            if w <= 0: w = 1
            if h <= 0: h = 1
            scaled_pix = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            preview_w = min(400, self.preview_lbl.width())
            preview_h = min(300, self.preview_lbl.height())
            tiled = QPixmap(preview_w, preview_h)
            from PySide6.QtGui import QPainter
            painter = QPainter(tiled)
            painter.drawTiledPixmap(0, 0, preview_w, preview_h, scaled_pix)
            painter.end()
            self.preview_lbl.setPixmap(tiled)
        except Exception as e:
            print(f"Preview Error: {e}")

# -----------------------------------------------------------
# 圖片填色 - 單一區塊控制面板
# -----------------------------------------------------------
class RegionControl(QGroupBox):
    settings_changed = Signal()

    def __init__(self, title, has_target_select=False, parent=None):
        super().__init__(title, parent)
        self.has_target_select = has_target_select
        self.current_fill_color = "#FFFFFF"
        self.current_target_color = "#FFFFFF"
        self.image_path = ""
        self.image_scale = 100
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        if self.has_target_select:
            layout.addWidget(SelectableLabel("目標區塊:"))
            self.combo_target = WhiteComboBox()
            base_title = self.title().replace("區塊", "")
            self.combo_target.addItems([f"全部「{base_title}」區塊", "指定色塊", "非指定色塊"])
            self.combo_target.currentIndexChanged.connect(self.toggle_target_ui)
            self.combo_target.currentIndexChanged.connect(self.settings_changed.emit)
            layout.addWidget(self.combo_target)

            self.target_color_widget = QWidget()
            tc_layout = QVBoxLayout(self.target_color_widget)
            tc_layout.setContentsMargins(0,0,0,0)
            
            self.lbl_target_color = SelectableLabel("目標色塊色值:")
            tc_layout.addWidget(self.lbl_target_color)

            tc_row = QHBoxLayout()
            self.edt_target_hex = QLineEdit()
            self.edt_target_hex.setPlaceholderText("#FFFFFF")
            self.edt_target_hex.setStyleSheet("font-size: 16px; font-weight: bold; color: #444; border: 1px solid #999; border-radius: 4px; padding: 4px;")
            self.edt_target_hex.textChanged.connect(self.sync_target_color_from_hex)
            self.edt_target_hex.editingFinished.connect(self.settings_changed.emit)
            
            self.target_color_box = QLabel()
            self.target_color_box.setFixedSize(36, 36)
            self.target_color_box.setStyleSheet("border: 1px solid #999; background-color: #FFFFFF; border-radius: 4px;")
            self.target_color_box.setCursor(Qt.PointingHandCursor)
            self.target_color_box.mousePressEvent = lambda e: self.pick_target_color()
            
            btn_pick = QPushButton("選色")
            btn_pick.setFixedWidth(60)
            btn_pick.clicked.connect(self.pick_target_color)
            
            tc_row.addWidget(self.edt_target_hex, 1)
            tc_row.addWidget(self.target_color_box)
            tc_row.addWidget(btn_pick)
            tc_layout.addLayout(tc_row)
            
            self.target_color_widget.hide()
            layout.addWidget(self.target_color_widget)
            layout.addSpacing(4)

        layout.addWidget(SelectableLabel("透明度設定:"))
        self.combo_trans = WhiteComboBox()
        self.combo_trans.addItems(["維持現狀", "改變透明度"])
        self.combo_trans.currentIndexChanged.connect(self.toggle_trans_ui)
        self.combo_trans.currentIndexChanged.connect(self.settings_changed.emit)
        layout.addWidget(self.combo_trans)

        self.trans_widget = QWidget()
        trans_layout = QVBoxLayout(self.trans_widget)
        trans_layout.setContentsMargins(0,0,0,0)
        
        slider_row = QHBoxLayout()
        self.slider_trans = QSlider(Qt.Horizontal)
        self.slider_trans.setRange(0, 100)
        self.slider_trans.setValue(100) 
        self.slider_trans.setFixedWidth(120)
        
        self.spin_trans = QSpinBox()
        self.spin_trans.setRange(0, 100)
        self.spin_trans.setValue(100)
        self.spin_trans.setSuffix("%")
        
        self.slider_trans.valueChanged.connect(self.spin_trans.setValue)
        self.spin_trans.valueChanged.connect(self.slider_trans.setValue)
        self.slider_trans.sliderReleased.connect(self.settings_changed.emit)
        self.spin_trans.valueChanged.connect(self.settings_changed.emit)

        slider_row.addWidget(self.slider_trans)
        slider_row.addWidget(self.spin_trans)
        slider_row.addStretch()
        
        lbl_hint = QLabel("0=全透, 100=不透")
        lbl_hint.setStyleSheet("font-size: 12px; color: #666;")
        slider_row.addWidget(lbl_hint)

        trans_layout.addLayout(slider_row)
        self.trans_widget.hide()
        layout.addWidget(self.trans_widget)
        layout.addSpacing(4)

        layout.addWidget(SelectableLabel("填充內容:"))
        self.combo_mode = WhiteComboBox()
        self.combo_mode.addItems(["維持現狀", "填充顏色", "填充圖片"])
        self.combo_mode.currentIndexChanged.connect(self.toggle_mode_ui)
        self.combo_mode.currentIndexChanged.connect(self.settings_changed.emit)
        layout.addWidget(self.combo_mode)

        self.stack_mode = QStackedWidget()
        self.stack_mode.addWidget(QWidget()) 
        
        p1 = QWidget()
        l1 = QVBoxLayout(p1); l1.setContentsMargins(0,0,0,0)
        l1.addWidget(SelectableLabel("填充色值:"))
        
        c_row = QHBoxLayout()
        self.edt_fill_hex = QLineEdit()
        self.edt_fill_hex.setPlaceholderText("#FFFFFF")
        self.edt_fill_hex.setStyleSheet("font-size: 16px; font-weight: bold; color: #444; border: 1px solid #999; border-radius: 4px; padding: 4px;")
        self.edt_fill_hex.textChanged.connect(self.sync_fill_color_from_hex)
        self.edt_fill_hex.editingFinished.connect(self.settings_changed.emit)
        
        self.fill_color_box = QLabel()
        self.fill_color_box.setFixedSize(36, 36)
        self.fill_color_box.setStyleSheet("border: 1px solid #999; background-color: #FFFFFF; border-radius: 4px;")
        self.fill_color_box.setCursor(Qt.PointingHandCursor)
        self.fill_color_box.mousePressEvent = lambda e: self.pick_fill_color()
        
        btn_set_fill = QPushButton("選色")
        btn_set_fill.setFixedWidth(60)
        btn_set_fill.clicked.connect(self.pick_fill_color)
        
        c_row.addWidget(self.edt_fill_hex, 1) 
        c_row.addWidget(self.fill_color_box)
        c_row.addWidget(btn_set_fill)
        l1.addLayout(c_row)
        self.stack_mode.addWidget(p1)

        p2 = QWidget()
        l2 = QVBoxLayout(p2); l2.setContentsMargins(0,0,0,0)
        l2.addWidget(SelectableLabel("紋理圖片:"))
        
        img_row = QHBoxLayout()
        self.lbl_img_status = SelectableLabel("尚未選擇")
        self.lbl_img_status.setStyleSheet("color: #666; font-size: 13px; font-style: italic;")
        btn_img = QPushButton("選擇...")
        btn_img.clicked.connect(self.pick_texture)
        img_row.addWidget(self.lbl_img_status, 1)
        img_row.addWidget(btn_img)
        l2.addLayout(img_row)
        self.stack_mode.addWidget(p2)

        layout.addWidget(self.stack_mode)
        layout.addStretch()

    def toggle_target_ui(self, idx):
        self.target_color_widget.setVisible(idx > 0)
        if idx == 1: self.lbl_target_color.setText("指定目標色值:")
        elif idx == 2: self.lbl_target_color.setText("非目標色值 (排除此色):")

    def toggle_trans_ui(self, idx):
        self.trans_widget.setVisible(idx == 1)

    def toggle_mode_ui(self, idx):
        self.stack_mode.setCurrentIndex(idx)

    def pick_target_color(self):
        col = QColorDialog.getColor(QColor(self.current_target_color), self, "選擇顏色")
        if col.isValid():
            self.current_target_color = col.name().upper()
            self.edt_target_hex.setText(self.current_target_color)
            self.target_color_box.setStyleSheet(f"border: 1px solid #999; background-color: {self.current_target_color}; border-radius: 4px;")
            self.settings_changed.emit()

    def sync_target_color_from_hex(self, text):
        if QColor.isValidColor(text):
            self.target_color_box.setStyleSheet(f"border: 1px solid #999; background-color: {text}; border-radius: 4px;")
            self.current_target_color = text

    def pick_fill_color(self):
        col = QColorDialog.getColor(QColor(self.current_fill_color), self, "選擇填充顏色")
        if col.isValid():
            self.current_fill_color = col.name().upper()
            self.edt_fill_hex.setText(self.current_fill_color)
            self.fill_color_box.setStyleSheet(f"border: 1px solid #999; background-color: {self.current_fill_color}; border-radius: 4px;")
            self.settings_changed.emit()

    def sync_fill_color_from_hex(self, text):
        if QColor.isValidColor(text):
            self.fill_color_box.setStyleSheet(f"border: 1px solid #999; background-color: {text}; border-radius: 4px;")
            self.current_fill_color = text

    def pick_texture(self):
        dlg = TextureDialog(self)
        if dlg.exec():
            self.image_path = dlg.image_path
            self.image_scale = dlg.scale
            self.lbl_img_status.setText(f"{Path(self.image_path).name} ({self.image_scale}%)")
            self.settings_changed.emit()

    def get_settings(self):
        target_mode = 'all'
        if self.has_target_select:
            idx = self.combo_target.currentIndex()
            if idx == 1: target_mode = 'specific'
            elif idx == 2: target_mode = 'non_specific'

        return {
            'target_mode': target_mode,
            'target_color': self.current_target_color,
            'trans_mode': 'change' if self.combo_trans.currentIndex() == 1 else 'maintain',
            'trans_val': self.slider_trans.value(),
            'fill_mode': ['maintain', 'color', 'image'][self.combo_mode.currentIndex()],
            'fill_color': self.current_fill_color,
            'fill_image_path': self.image_path,
            'fill_image_scale': self.image_scale
        }

# -----------------------------------------------------------
# 主視窗 (MainWindow)
# -----------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Media Batch Processor")
        self.resize(1280, 850)
        self.worker = None 
        self.settings = QSettings("MyCompany", "ImageToolApp")
        
        self.active_pbar = None
        self.active_plbl = None
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. 左側 Sidebar
        self.sidebar = QWidget()
        self.sidebar.setObjectName("SidebarFrame")
        self.sidebar.setFixedWidth(260)
        
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(0, 30, 0, 20)
        sb_layout.setSpacing(8)

        title = QLabel("Media Batcher")
        title.setStyleSheet("color: #38bdf8; font-size: 24px; font-weight: bold; margin-left: 20px; margin-bottom: 5px;")
        sb_layout.addWidget(title)
        ver = QLabel("Python Port v1.0")
        ver.setStyleSheet("color: #64748b; font-size: 13px; margin-left: 20px; margin-bottom: 20px;")
        sb_layout.addWidget(ver)

        self.btn_group = []
        menu_items = [
            ("圖片批次處理", "🖼️", 0),
            ("影片銳利化", "🎥", 1),
            ("檔名修改", "📝", 2),
            ("Icon 生成", "📦", 3),
            ("圖片填色", "🎨", 4),
        ]
        
        for txt, icon, idx in menu_items:
            btn = SidebarButton(txt, icon, idx)
            btn.clicked.connect(self.switch_page)
            sb_layout.addWidget(btn)
            self.btn_group.append(btn)
        
        sb_layout.addStretch()
        
        copy = QLabel("© 2024 ImageTool")
        copy.setStyleSheet("color: #475569; font-size: 12px; margin-left: 20px;")
        sb_layout.addWidget(copy)

        # 2. 右側內容區
        right_frame = QWidget()
        right_frame.setObjectName("RightFrame")
        
        rf_layout = QVBoxLayout(right_frame)
        rf_layout.setContentsMargins(0,0,0,0)
        rf_layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setFixedHeight(70)
        self.header.setStyleSheet("background-color: white; border-bottom: 1px solid #cbd5e1;")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(30, 0, 30, 0)
        self.header_title = QLabel("功能標題")
        self.header_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b;")
        header_layout.addWidget(self.header_title)
        rf_layout.addWidget(self.header)

        # Content
        self.stack = QStackedWidget()
        self.stack.setObjectName("ScrollContent")
        self.stack.addWidget(self.page_scaling_ui())
        self.stack.addWidget(self.page_video_ui())
        self.stack.addWidget(self.page_rename_ui())
        self.stack.addWidget(self.page_multi_ui())
        self.stack.addWidget(self.page_fill_ui()) 
        
        rf_layout.addWidget(self.stack, 1)

        # Footer Status
        status_bar = QWidget()
        status_bar.setStyleSheet("background-color: #f1f5f9; border-top: 1px solid #cbd5e1;")
        status_layout = QVBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 10, 20, 10)
        
        fp_row = QHBoxLayout()
        self.lbl_current = SelectableLabel("準備就緒")
        self.lbl_current.setStyleSheet("color: #475569; font-weight: 500;")
        fp_row.addWidget(self.lbl_current)
        fp_row.addStretch()
        self.pbar_file = QProgressBar()
        self.pbar_file.setObjectName("FileProgress") # 確保套用隱藏文字的樣式
        self.pbar_file.setFixedWidth(200)
        fp_row.addWidget(self.pbar_file)
        status_layout.addLayout(fp_row)

        # Log Area and Clear Button
        log_header_layout = QHBoxLayout()
        log_header_layout.addWidget(SelectableLabel("執行紀錄:"))
        log_header_layout.addStretch()
        
        btn_clear = QPushButton("清除 Log")
        btn_clear.setObjectName("ClearLogBtn")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(lambda: self.log_area.clear())
        log_header_layout.addWidget(btn_clear)
        
        status_layout.addLayout(log_header_layout)

        self.log_area = QTextEdit()
        self.log_area.setFixedHeight(80)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("border: 1px solid #cbd5e1; background: white; border-radius: 4px; font-family: Consolas; color: #333;")
        status_layout.addWidget(self.log_area)
        
        rf_layout.addWidget(status_bar)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(right_frame)

        self.switch_page(0)

    # --- Page Switching ---
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        titles = ["圖片批次處理", "影片銳利化", "檔名修改工具", "Icon 多尺寸生成", "智慧圖片填色"]
        if 0 <= index < len(titles):
            self.header_title.setText(titles[index])
        
        for btn in self.btn_group:
            btn.set_selected(btn.index == index)

    # --- Helpers ---
    def _create_scroll_page(self, btn_text, on_click):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0,0,0,0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        content.setObjectName("ScrollContent")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(40, 30, 40, 40)
        cl.setSpacing(20)
        scroll.setWidget(content)
        pl.addWidget(scroll)

        cl.addStretch()
        
        btn_area = QWidget()
        bl = QHBoxLayout(btn_area)
        bl.setContentsMargins(0, 20, 0, 0)
        
        btn = QPushButton(btn_text)
        btn.setObjectName("ExecBtn")
        btn.setCursor(Qt.PointingHandCursor)
        if on_click: btn.clicked.connect(on_click)
        
        pbar = QProgressBar()
        pbar.setObjectName("TotalProgress") # 套用樣式
        pbar.setRange(0, 100)
        pbar.setFixedHeight(18)
        
        # 總進度文字改由 ProgressBar 內建顯示 (QSS 中 text-align: center)
        # 所以這裡不需要額外的 plbl，但為了相容你的邏輯保留它，可以設為隱藏
        plbl = SelectableLabel("") 
        plbl.setVisible(False)
        
        bl.addWidget(btn)
        bl.addSpacing(20)
        bl.addWidget(SelectableLabel("總進度:"))
        bl.addWidget(pbar)
        
        cl.addWidget(btn_area)
        
        return page, cl, pbar, plbl

    # --- [待修復項目 1] 路徑設定 UI 復原 ---
    def create_path_group(self, title="檔案來源", with_output=True):
        grp = QGroupBox(title)
        layout = QFormLayout()
        layout.setVerticalSpacing(15)
        
        # 1. Input Row
        edt_in = QLineEdit()
        edt_in.setPlaceholderText("請選擇檔案或資料夾...")
        btn_in_dir = QPushButton("📂 資料夾")
        btn_in_dir.clicked.connect(lambda: self.select_folder(edt_in))
        btn_in_file = QPushButton("📄 檔案")
        btn_in_file.clicked.connect(lambda: self.select_file(edt_in))
        
        # 拖曳區塊
        drop_in = DragDropArea()
        drop_in.fileDropped.connect(edt_in.setText)
        
        row_in = QHBoxLayout()
        row_in.addWidget(edt_in)
        row_in.addWidget(btn_in_dir)
        row_in.addWidget(btn_in_file)
        row_in.addWidget(drop_in)
        
        layout.addRow(SelectableLabel("輸入路徑:"), row_in)

        # 2. Output Row (Optional)
        edt_out = None
        if with_output:
            edt_out = QLineEdit()
            edt_out.setPlaceholderText("預設為來源資料夾")
            btn_out = QPushButton("📂 選擇")
            btn_out.clicked.connect(lambda: self.select_folder(edt_out))
            
            drop_out = DragDropArea()
            drop_out.fileDropped.connect(edt_out.setText)
            
            row_out = QHBoxLayout()
            row_out.addWidget(edt_out)
            row_out.addWidget(btn_out)
            row_out.addWidget(drop_out)
            
            layout.addRow(SelectableLabel("輸出位置:"), row_out)
        
        grp.setLayout(layout)
        return grp, edt_in, edt_out

    # -------------------------------------------------------------------------
    # Page 0: Scaling / Batch Process
    # -------------------------------------------------------------------------
    def page_scaling_ui(self):
        w, layout, self.sc_pbar, self.sc_plbl = self._create_scroll_page("開始處理圖片", self.run_scaling)
        
        # 恢復輸出路徑
        grp_path, self.sc_in, self.sc_out = self.create_path_group(with_output=True)
        layout.insertWidget(0, grp_path)

        # 2. Main Options
        grp_opt = QGroupBox("處理參數")
        fl = QFormLayout()
        
        self.sc_mode = WhiteComboBox()
        self.sc_mode.addItems(["Ratio (比例縮放)", "Fixed Width (固定寬度)", "Fixed Height (固定高度)"])
        self.sc_stack = QStackedWidget()
        
        # Ratio Input
        w1 = QWidget(); l1 = QHBoxLayout(w1); l1.setContentsMargins(0,0,0,0)
        self.sc_val_ratio = QLineEdit("1.0"); l1.addWidget(self.sc_val_ratio); l1.addWidget(SelectableLabel("x (0.1 - 5.0)"))
        self.sc_stack.addWidget(w1)
        
        # Width Input
        w2 = QWidget(); l2 = QHBoxLayout(w2); l2.setContentsMargins(0,0,0,0)
        self.sc_val_width = QLineEdit("1920"); l2.addWidget(self.sc_val_width); l2.addWidget(SelectableLabel("px"))
        self.sc_stack.addWidget(w2)

        # Height Input
        w3 = QWidget(); l3 = QHBoxLayout(w3); l3.setContentsMargins(0,0,0,0)
        self.sc_val_height = QLineEdit("1080"); l3.addWidget(self.sc_val_height); l3.addWidget(SelectableLabel("px"))
        self.sc_stack.addWidget(w3)
        
        self.sc_mode.currentIndexChanged.connect(self.sc_stack.setCurrentIndex)
        
        # Enhancements
        enhance_row = QHBoxLayout()
        self.sc_sharpness = QLineEdit("1.0"); self.sc_sharpness.setFixedWidth(80)
        self.sc_brightness = QLineEdit("1.0"); self.sc_brightness.setFixedWidth(80)
        enhance_row.addWidget(SelectableLabel("銳利度:"))
        enhance_row.addWidget(self.sc_sharpness)
        enhance_row.addSpacing(20)
        enhance_row.addWidget(SelectableLabel("亮度:"))
        enhance_row.addWidget(self.sc_brightness)
        enhance_row.addStretch()

        # Meta info
        self.sc_prefix = QLineEdit(); self.sc_postfix = QLineEdit()
        self.sc_author = QLineEdit(self.settings.value("img_author", "")); self.sc_desc = QLineEdit()

        fl.addRow(SelectableLabel("縮放模式:"), self.sc_mode)
        fl.addRow(SelectableLabel("數值:"), self.sc_stack)
        fl.addRow(SelectableLabel("影像增強:"), enhance_row)
        fl.addRow(SelectableLabel("檔名前綴:"), self.sc_prefix)
        fl.addRow(SelectableLabel("檔名後綴:"), self.sc_postfix)
        fl.addRow(SelectableLabel("作者 Meta:"), self.sc_author)
        fl.addRow(SelectableLabel("描述 Meta:"), self.sc_desc)
        
        grp_opt.setLayout(fl)
        layout.insertWidget(1, grp_opt)
        
        # 3. Checkboxes (Grid Layout)
        grp_chk = QGroupBox("進階選項")
        gl = QGridLayout()
        self.sc_rec = QCheckBox("包含子資料夾"); self.sc_rec.setChecked(True)
        self.sc_jpg = QCheckBox("強制轉 JPG"); self.sc_jpg.setChecked(True)
        self.sc_low = QCheckBox("副檔名轉小寫"); self.sc_low.setChecked(True)
        self.sc_del = QCheckBox("刪除原始檔"); self.sc_del.setChecked(False)
        self.sc_crop = QCheckBox("豆包圖裁切 (去除頂底雜訊)"); self.sc_crop.setChecked(False)
        self.sc_meta = QCheckBox("移除 Metadata"); self.sc_meta.setChecked(False)
        
        gl.addWidget(self.sc_rec, 0, 0)
        gl.addWidget(self.sc_jpg, 0, 1)
        gl.addWidget(self.sc_low, 0, 2)
        gl.addWidget(self.sc_del, 1, 0)
        gl.addWidget(self.sc_crop, 1, 1)
        gl.addWidget(self.sc_meta, 1, 2)
        
        grp_chk.setLayout(gl)
        layout.insertWidget(2, grp_chk)
        
        return w
    
    def run_scaling(self):
        idx = self.sc_mode.currentIndex()
        mode = ['ratio', 'width', 'height'][idx]
        try:
            if idx == 0: val1 = float(self.sc_val_ratio.text())
            elif idx == 1: val1 = float(self.sc_val_width.text())
            else: val1 = float(self.sc_val_height.text())
            sharp = float(self.sc_sharpness.text())
            bright = float(self.sc_brightness.text())
        except:
            self.log("❌ 參數格式錯誤，請檢查數值")
            return

        self.settings.setValue("img_author", self.sc_author.text())

        self.run_worker(logic.task_scaling, target_pbar=self.sc_pbar, target_plbl=self.sc_plbl, 
                        input_path=self.sc_in.text(), output_path=self.sc_out.text(), 
                        mode=mode, mode_value_1=val1, mode_value_2=0, 
                        recursive=self.sc_rec.isChecked(), convert_jpg=self.sc_jpg.isChecked(), 
                        lower_ext=self.sc_low.isChecked(), delete_original=self.sc_del.isChecked(), 
                        prefix=self.sc_prefix.text(), postfix=self.sc_postfix.text(), 
                        crop_doubao=self.sc_crop.isChecked(), 
                        sharpen_factor=sharp, brightness_factor=bright, 
                        remove_metadata=self.sc_meta.isChecked(), 
                        author=self.sc_author.text(), description=self.sc_desc.text())

    # -------------------------------------------------------------------------
    # Page 1: Video Sharpen
    # -------------------------------------------------------------------------
    def page_video_ui(self):
        w, layout, self.vd_pbar, self.vd_plbl = self._create_scroll_page("開始影片處理", self.run_video)
        
        # 恢復輸出路徑
        grp_path, self.vd_in, self.vd_out = self.create_path_group(with_output=True)
        layout.insertWidget(0, grp_path)

        grp_sets = QGroupBox("銳利化設定")
        fl = QFormLayout()
        
        # --- [待修復項目 5] 調整 Luma 選單寬度 ---
        # 使用 QHBoxLayout 讓它們並排且寬度足夠，或者直接設 setMinimumWidth
        row_luma = QHBoxLayout()
        
        self.vd_luma_size = WhiteComboBox()
        self.vd_luma_size.addItems(["3", "5", "7", "9", "11", "13"])
        self.vd_luma_size.setCurrentText("7")
        self.vd_luma_size.setMinimumWidth(150) # 加寬
        
        self.vd_luma_amount = QLineEdit("1.0")
        self.vd_luma_amount.setFixedWidth(100)
        
        row_luma.addWidget(SelectableLabel("Size:"))
        row_luma.addWidget(self.vd_luma_size)
        row_luma.addSpacing(20)
        row_luma.addWidget(SelectableLabel("Amount:"))
        row_luma.addWidget(self.vd_luma_amount)
        row_luma.addStretch()

        fl.addRow(SelectableLabel("銳化參數 (Luma):"), row_luma)
        grp_sets.setLayout(fl)
        layout.insertWidget(1, grp_sets)

        grp_scale = QGroupBox("解析度與轉檔")
        fl2 = QFormLayout()
        self.vd_scale_mode = WhiteComboBox()
        self.vd_scale_mode.addItems(["不改變", "1080p (Auto Fit)", "720p (Auto Fit)", "480p (Auto Fit)", "Scale Ratio"])
        
        self.vd_scale_val = QLineEdit("1.0")
        self.vd_scale_val.setEnabled(False)
        self.vd_scale_mode.currentIndexChanged.connect(lambda i: self.vd_scale_val.setEnabled(i == 4))

        self.vd_prefix = QLineEdit(); self.vd_postfix = QLineEdit()
        self.vd_author = QLineEdit(self.settings.value("vd_author", "")); self.vd_desc = QLineEdit()

        fl2.addRow(SelectableLabel("解析度控制:"), self.vd_scale_mode)
        fl2.addRow(SelectableLabel("縮放比例 (若選Ratio):"), self.vd_scale_val)
        fl2.addRow(SelectableLabel("檔名前綴:"), self.vd_prefix)
        fl2.addRow(SelectableLabel("檔名後綴:"), self.vd_postfix)
        fl2.addRow(SelectableLabel("作者 Meta:"), self.vd_author)
        fl2.addRow(SelectableLabel("描述 Meta:"), self.vd_desc)
        grp_scale.setLayout(fl2)
        layout.insertWidget(2, grp_scale)

        grp_chk = QGroupBox("其他選項")
        gl = QGridLayout()
        self.vd_rec = QCheckBox("包含子資料夾"); self.vd_rec.setChecked(True)
        self.vd_h264 = QCheckBox("強制轉 H.264 (mp4)"); self.vd_h264.setChecked(True)
        self.vd_low = QCheckBox("副檔名轉小寫"); self.vd_low.setChecked(True)
        self.vd_del = QCheckBox("刪除原始檔"); self.vd_del.setChecked(False)
        self.vd_meta = QCheckBox("移除 Metadata"); self.vd_meta.setChecked(False)
        
        gl.addWidget(self.vd_rec, 0, 0)
        gl.addWidget(self.vd_h264, 0, 1)
        gl.addWidget(self.vd_low, 0, 2)
        gl.addWidget(self.vd_del, 1, 0)
        gl.addWidget(self.vd_meta, 1, 1)
        
        grp_chk.setLayout(gl)
        layout.insertWidget(3, grp_chk)
        
        return w

    def run_video(self):
        try:
            l_size = int(self.vd_luma_size.currentText())
            l_amount = float(self.vd_luma_amount.text())
            scale_idx = self.vd_scale_mode.currentIndex()
            s_mode = 'none'
            if scale_idx == 1: s_mode = 'hd1080'
            elif scale_idx == 2: s_mode = 'hd720'
            elif scale_idx == 3: s_mode = 'hd480'
            elif scale_idx == 4: s_mode = 'ratio'
            
            s_val = float(self.vd_scale_val.text())
        except:
             self.log("❌ 參數格式錯誤")
             return

        self.settings.setValue("vd_author", self.vd_author.text())

        self.run_worker(logic.task_video_sharpen, target_pbar=self.vd_pbar, target_plbl=self.vd_plbl,
                       input_path=self.vd_in.text(), output_path=self.vd_out.text(), recursive=self.vd_rec.isChecked(), 
                       lower_ext=self.vd_low.isChecked(), delete_original=self.vd_del.isChecked(), 
                       prefix=self.vd_prefix.text(), postfix=self.vd_postfix.text(),
                       luma_m_size=l_size, luma_amount=l_amount, 
                       scale_mode=s_mode, scale_value=s_val, 
                       convert_h264=self.vd_h264.isChecked(), 
                       remove_metadata=self.vd_meta.isChecked(), 
                       author=self.vd_author.text(), description=self.vd_desc.text())

    # -------------------------------------------------------------------------
    # Page 2: Rename
    # -------------------------------------------------------------------------
    def page_rename_ui(self):
        w, layout, self.rn_pbar, self.rn_plbl = self._create_scroll_page("執行更名", self.run_rename)
        
        # 更名工具只需要輸入路徑 (with_output=False)
        grp, self.rn_in, _ = self.create_path_group(title="目標資料夾", with_output=False)
        
        layout.insertWidget(0, grp)
        
        grp_act = QGroupBox("規則設定")
        fl = QFormLayout()
        
        self.chk_prefix = QCheckBox("修改前綴")
        row_pre = QHBoxLayout()
        self.edt_old_prefix = QLineEdit(); self.edt_old_prefix.setPlaceholderText("舊前綴")
        self.edt_new_prefix = QLineEdit(); self.edt_new_prefix.setPlaceholderText("新前綴")
        row_pre.addWidget(self.edt_old_prefix); row_pre.addWidget(SelectableLabel("➜")); row_pre.addWidget(self.edt_new_prefix)
        
        self.chk_suffix = QCheckBox("修改後綴")
        row_suf = QHBoxLayout()
        self.edt_old_suffix = QLineEdit(); self.edt_old_suffix.setPlaceholderText("舊後綴")
        self.edt_new_suffix = QLineEdit(); self.edt_new_suffix.setPlaceholderText("新後綴")
        row_suf.addWidget(self.edt_old_suffix); row_suf.addWidget(SelectableLabel("➜")); row_suf.addWidget(self.edt_new_suffix)

        fl.addRow(self.chk_prefix, row_pre)
        fl.addRow(self.chk_suffix, row_suf)
        grp_act.setLayout(fl)
        layout.insertWidget(1, grp_act)
        
        self.rn_rec = QCheckBox("包含子資料夾"); self.rn_rec.setChecked(True)
        layout.insertWidget(2, self.rn_rec)
        
        return w

    def run_rename(self):
        self.run_worker(logic.task_rename_replace, target_pbar=self.rn_pbar, target_plbl=self.rn_plbl,
                        input_path=self.rn_in.text(), recursive=self.rn_rec.isChecked(), 
                        do_prefix=self.chk_prefix.isChecked(), old_prefix=self.edt_old_prefix.text(), new_prefix=self.edt_new_prefix.text(),
                        do_suffix=self.chk_suffix.isChecked(), old_suffix=self.edt_old_suffix.text(), new_suffix=self.edt_new_suffix.text())

    # -------------------------------------------------------------------------
    # Page 3: Multi Res (Icon)
    # -------------------------------------------------------------------------
    def page_multi_ui(self):
        w, layout, self.mt_pbar, self.mt_plbl = self._create_scroll_page("生成 Icons", self.run_multi)
        
        # 恢復輸出路徑
        grp, self.mt_in, self.mt_out = self.create_path_group(with_output=True)
        layout.insertWidget(0, grp)
        
        grp_opt = QGroupBox("設定")
        fl = QFormLayout()
        self.mt_ori = WhiteComboBox()
        self.mt_ori.addItems(["水平基準 (以寬度為準)", "垂直基準 (以高度為準)"])
        fl.addRow(SelectableLabel("縮放基準:"), self.mt_ori)
        grp_opt.setLayout(fl)
        layout.insertWidget(1, grp_opt)
        
        self.mt_rec = QCheckBox("包含子資料夾"); self.mt_rec.setChecked(True)
        layout.insertWidget(2, self.mt_rec)
        
        return w

    def run_multi(self):
        self.run_worker(logic.task_multi_res, target_pbar=self.mt_pbar, target_plbl=self.mt_plbl,
                        input_path=self.mt_in.text(), output_path=self.mt_out.text(), recursive=self.mt_rec.isChecked(),
                        lower_ext=True, orientation='h' if self.mt_ori.currentIndex()==0 else 'v')

    # -------------------------------------------------------------------------
    # Page 4: Image Fill (Advanced)
    # -------------------------------------------------------------------------
    def page_fill_ui(self):
        w, layout, self.fill_pbar, self.fill_plbl = self._create_scroll_page("開始填色處理", self.run_fill)
        self.fill_page_widget = w

        # 1. Path (恢復輸出路徑)
        grp_path, self.fill_in, self.fill_out = self.create_path_group("檔案路徑設定", with_output=True)
        layout.insertWidget(0, grp_path)

        # 2. Region Controls
        row_regions = QHBoxLayout()
        row_regions.setSpacing(20)
        
        self.reg_opaque = RegionControl("不透明區塊", has_target_select=True)
        self.reg_trans = RegionControl("透明區塊", has_target_select=False)
        self.reg_semi = RegionControl("半透明區塊", has_target_select=True)
        
        row_regions.addWidget(self.reg_opaque)
        row_regions.addWidget(self.reg_trans)
        row_regions.addWidget(self.reg_semi)
        
        layout.insertLayout(1, row_regions)

        # 3. Output Options
        grp_opts = QGroupBox("輸出設定")
        opt_layout = QHBoxLayout()
        
        self.fill_rec = QCheckBox("包含子資料夾")
        self.fill_rec.setChecked(self.settings.value("fill_rec", False, type=bool))
        
        self.fill_del = QCheckBox("刪除原始圖片")
        self.fill_del.setChecked(self.settings.value("fill_del", False, type=bool))
        
        self.fill_fmt = WhiteComboBox()
        self.fill_fmt.addItems(["png", "jpg", "webp"])
        self.fill_fmt.setCurrentText(self.settings.value("fill_fmt", "png", type=str))
        self.fill_fmt.setFixedWidth(100)
        
        opt_layout.addWidget(self.fill_rec)
        opt_layout.addSpacing(20)
        opt_layout.addWidget(self.fill_del)
        opt_layout.addStretch()
        opt_layout.addWidget(SelectableLabel("輸出格式:"))
        opt_layout.addWidget(self.fill_fmt)
        
        grp_opts.setLayout(opt_layout)
        layout.insertWidget(2, grp_opts)

        return w

    def run_fill(self):
        self.settings.setValue("fill_rec", self.fill_rec.isChecked())
        self.settings.setValue("fill_del", self.fill_del.isChecked())
        self.settings.setValue("fill_fmt", self.fill_fmt.currentText())

        kwargs = {
            'input_path': self.fill_in.text(),
            'output_path': self.fill_out.text(),
            'recursive': self.fill_rec.isChecked(),
            'settings_opaque': self.reg_opaque.get_settings(),
            'settings_trans': self.reg_trans.get_settings(),
            'settings_semi': self.reg_semi.get_settings(),
            'delete_original': self.fill_del.isChecked(),
            'output_format': self.fill_fmt.currentText()
        }
        
        self.run_worker(logic.task_image_fill, target_pbar=self.fill_pbar, target_plbl=self.fill_plbl, **kwargs)

    # -------------------------------------------------------------------------
    # Common Helpers
    # -------------------------------------------------------------------------
    def select_folder(self, edt):
        d = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if d: edt.setText(d)
    
    def select_file(self, edt):
        f, _ = QFileDialog.getOpenFileName(self, "選擇檔案", "", "Images (*.png *.jpg *.jpeg *.webp);;Video (*.mp4 *.mov *.mkv *.avi);;All (*)")
        if f: edt.setText(f)

    def log(self, msg):
        t = datetime.now().strftime("%H:%M:%S")
        self.log_area.append(f"[{t}] {msg}")

    # --- [待修復項目 4] 修復 Worker 信號連接 (確保 current_file 與 pbar_file 會動) ---
    def run_worker(self, func, target_pbar, target_plbl, **kwargs):
        if not kwargs.get('input_path'):
            self.log("❌ 請選擇輸入路徑")
            return
        
        self.active_pbar = target_pbar
        self.active_plbl = target_plbl
        
        self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log)
        
        # 總進度
        self.worker.progress_signal.connect(lambda v: self.active_pbar.setValue(v) if self.active_pbar else None)
        
        # 單一檔案進度 (更新底部狀態列)
        self.worker.file_progress_signal.connect(lambda v: self.pbar_file.setValue(v))
        
        # 當前檔名 (更新底部狀態列)
        self.worker.current_file_signal.connect(lambda s: self.lbl_current.setText(f"處理中: {s}"))
        
        self.worker.finished_signal.connect(lambda: self.log("✅ 任務完成"))
        self.worker.start()