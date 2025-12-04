from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame, 
                               QMessageBox, QProgressBar, QColorDialog, QSlider, QSpinBox,
                               QDialog, QSizePolicy)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QTextCursor, QPixmap, QImage, QColor

from PIL import Image, ImageQt
from app.workers import Worker
import app.logic as logic
import app.utils as utils

# -----------------------------------------------------------
# 自定義控制項
# -----------------------------------------------------------

class SelectableLabel(QLabel):
    def __init__(self, text=""):
        super().__init__(text)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.IBeamCursor)

class SidebarButton(QFrame):
    clicked = Signal(int)

    def __init__(self, text, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setCursor(Qt.PointingHandCursor)
        self.is_selected = False
        self.setMinimumHeight(80) 

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        self.indicator = QWidget()
        self.indicator.setFixedWidth(6)
        self.indicator.setStyleSheet("background-color: transparent;") 
        
        self.icon_label = QLabel("🔥")
        self.icon_label.setStyleSheet("color: #66cfff; font-size: 16px;")
        self.icon_label.hide()
        
        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
        
        layout.addWidget(self.indicator)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()

    def set_selected(self, selected):
        self.is_selected = selected
        if selected:
            self.indicator.setStyleSheet("background-color: #66cfff;") 
            self.icon_label.show() 
            self.text_label.setStyleSheet("color: #66cfff; font-weight: normal; font-size: 16px;")
            self.setStyleSheet("background-color: #333333;") 
        else:
            self.indicator.setStyleSheet("background-color: transparent;")
            self.icon_label.hide() 
            self.text_label.setStyleSheet("color: #aaaaaa; font-weight: normal; font-size: 16px;")
            self.setStyleSheet("background-color: transparent;")

    def enterEvent(self, event):
        if not self.is_selected:
            self.text_label.setStyleSheet("color: #ffffff; font-size: 16px;") 
            self.setStyleSheet("background-color: #3d3d3d;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_selected:
            self.text_label.setStyleSheet("color: #aaaaaa; font-size: 16px;")
            self.setStyleSheet("background-color: transparent;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)

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
        
        self.preview_lbl = SelectableLabel("請選擇圖片")
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setStyleSheet("border: 1px dashed #999; background: #eee;")
        self.preview_lbl.setMinimumHeight(300)
        self.preview_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.preview_lbl)

        btn_browse = QPushButton("選擇圖片...")
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
        btn_ok.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        btn_ok.clicked.connect(self.accept)
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
        layout.setSpacing(10)

        # 0. 目標區塊篩選 (僅不透明/半透明有)
        if self.has_target_select:
            layout.addWidget(SelectableLabel("目標區塊:"))
            self.combo_target = QComboBox()
            self.combo_target.addItems([f"全部 {self.title()}", "指定色塊", "非指定色塊"])
            self.combo_target.currentIndexChanged.connect(self.toggle_target_ui)
            self.combo_target.currentIndexChanged.connect(self.settings_changed.emit)
            layout.addWidget(self.combo_target)

            # 目標色設定區 (初始隱藏)
            self.target_color_widget = QWidget()
            tc_layout = QVBoxLayout(self.target_color_widget)
            tc_layout.setContentsMargins(0,0,0,0)
            
            self.lbl_target_color = SelectableLabel("目標色塊色值:")
            tc_layout.addWidget(self.lbl_target_color)

            # 色值選取 Row
            tc_row = QHBoxLayout()
            self.edt_target_hex = QLineEdit()
            self.edt_target_hex.setPlaceholderText("#FFFFFF")
            self.edt_target_hex.textChanged.connect(self.sync_target_color_from_hex)
            self.edt_target_hex.editingFinished.connect(self.settings_changed.emit)
            
            self.target_color_box = QLabel()
            self.target_color_box.setFixedSize(30, 30)
            self.target_color_box.setStyleSheet("border: 1px solid #ccc; background-color: #FFFFFF;")
            
            btn_set_target = QPushButton("設定顏色")
            btn_set_target.clicked.connect(self.pick_target_color)
            
            tc_row.addWidget(self.edt_target_hex, 1) # Stretch factor 1
            tc_row.addWidget(self.target_color_box)
            tc_row.addWidget(btn_set_target)
            tc_layout.addLayout(tc_row)
            
            self.target_color_widget.hide()
            layout.addWidget(self.target_color_widget)
            layout.addSpacing(10)

        # 1. 透明度設定
        layout.addWidget(SelectableLabel("透明度設定:"))
        self.combo_trans = QComboBox()
        self.combo_trans.addItems(["維持現狀", "改變透明度"])
        self.combo_trans.currentIndexChanged.connect(self.toggle_trans_ui)
        self.combo_trans.currentIndexChanged.connect(self.settings_changed.emit)
        layout.addWidget(self.combo_trans)

        self.trans_widget = QWidget()
        trans_layout = QVBoxLayout(self.trans_widget)
        trans_layout.setContentsMargins(0,0,0,0)
        
        lbl_layout = QHBoxLayout()
        lbl_layout.addWidget(SelectableLabel("不透明"))
        lbl_layout.addStretch()
        lbl_layout.addWidget(SelectableLabel("透明"))
        trans_layout.addLayout(lbl_layout)

        slider_row = QHBoxLayout()
        self.slider_trans = QSlider(Qt.Horizontal)
        self.slider_trans.setRange(0, 100)
        self.slider_trans.setValue(0)
        self.slider_trans.setFixedWidth(120) # 縮小寬度
        
        self.spin_trans = QSpinBox()
        self.spin_trans.setRange(0, 100)
        
        self.slider_trans.valueChanged.connect(self.spin_trans.setValue)
        self.spin_trans.valueChanged.connect(self.slider_trans.setValue)
        self.slider_trans.sliderReleased.connect(self.settings_changed.emit)
        self.spin_trans.valueChanged.connect(self.settings_changed.emit)

        slider_row.addWidget(self.slider_trans)
        slider_row.addWidget(self.spin_trans)
        trans_layout.addLayout(slider_row)
        
        self.trans_widget.hide()
        layout.addWidget(self.trans_widget)
        layout.addSpacing(10)

        # 2. 填充模式
        layout.addWidget(SelectableLabel("填充模式:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["維持現狀", "填充顏色", "填充圖片"])
        self.combo_mode.currentIndexChanged.connect(self.toggle_mode_ui)
        self.combo_mode.currentIndexChanged.connect(self.settings_changed.emit)
        layout.addWidget(self.combo_mode)

        self.stack_mode = QStackedWidget()
        self.stack_mode.addWidget(QWidget()) # P0
        
        # P1: 顏色
        p1 = QWidget()
        l1 = QVBoxLayout(p1); l1.setContentsMargins(0,0,0,0)
        l1.addWidget(SelectableLabel("區塊色值:"))
        
        c_row = QHBoxLayout()
        self.edt_fill_hex = QLineEdit()
        self.edt_fill_hex.setPlaceholderText("#FFFFFF")
        self.edt_fill_hex.textChanged.connect(self.sync_fill_color_from_hex)
        self.edt_fill_hex.editingFinished.connect(self.settings_changed.emit)
        
        self.fill_color_box = QLabel()
        self.fill_color_box.setFixedSize(30, 30)
        self.fill_color_box.setStyleSheet("border: 1px solid #ccc; background-color: #FFFFFF;")
        
        btn_set_fill = QPushButton("設定顏色")
        btn_set_fill.clicked.connect(self.pick_fill_color)
        
        c_row.addWidget(self.edt_fill_hex, 1) # 加大輸入框
        c_row.addWidget(self.fill_color_box)
        c_row.addWidget(btn_set_fill)
        l1.addLayout(c_row)
        self.stack_mode.addWidget(p1)

        # P2: 圖片
        p2 = QWidget()
        l2 = QVBoxLayout(p2); l2.setContentsMargins(0,0,0,0)
        l2.addWidget(SelectableLabel("紋理圖片:"))
        btn_img = QPushButton("選擇並設定圖片...")
        btn_img.clicked.connect(self.pick_texture)
        self.lbl_img_status = SelectableLabel("尚未選擇")
        self.lbl_img_status.setStyleSheet("color: #666; font-size: 13px;")
        l2.addWidget(btn_img)
        l2.addWidget(self.lbl_img_status)
        self.stack_mode.addWidget(p2)

        layout.addWidget(self.stack_mode)
        layout.addStretch()

    def toggle_target_ui(self, idx):
        # 0: All, 1: Specific, 2: Non-Specific
        self.target_color_widget.setVisible(idx > 0)
        if idx == 1:
            self.lbl_target_color.setText("目標色塊色值:")
        elif idx == 2:
            self.lbl_target_color.setText("非目標色塊色值:")

    def toggle_trans_ui(self, idx):
        self.trans_widget.setVisible(idx == 1)

    def toggle_mode_ui(self, idx):
        self.stack_mode.setCurrentIndex(idx)

    # --- Target Color Logic ---
    def pick_target_color(self):
        col = QColorDialog.getColor(QColor(self.current_target_color), self, "選擇目標顏色")
        if col.isValid():
            hex_code = col.name()
            self.current_target_color = hex_code
            self.edt_target_hex.setText(hex_code)
            self.target_color_box.setStyleSheet(f"border: 1px solid #ccc; background-color: {hex_code};")
            self.settings_changed.emit()

    def sync_target_color_from_hex(self, text):
        if QColor.isValidColor(text):
            self.target_color_box.setStyleSheet(f"border: 1px solid #ccc; background-color: {text};")
            self.current_target_color = text

    # --- Fill Color Logic ---
    def pick_fill_color(self):
        col = QColorDialog.getColor(QColor(self.current_fill_color), self, "選擇填充顏色")
        if col.isValid():
            hex_code = col.name()
            self.current_fill_color = hex_code
            self.edt_fill_hex.setText(hex_code)
            self.fill_color_box.setStyleSheet(f"border: 1px solid #ccc; background-color: {hex_code};")
            self.settings_changed.emit()

    def sync_fill_color_from_hex(self, text):
        if QColor.isValidColor(text):
            self.fill_color_box.setStyleSheet(f"border: 1px solid #ccc; background-color: {text};")
            self.current_fill_color = text

    def pick_texture(self):
        dlg = TextureDialog(self)
        if dlg.exec():
            self.image_path = dlg.image_path
            self.image_scale = dlg.scale
            self.lbl_img_status.setText(f"{Path(self.image_path).name} (Scale: {self.image_scale}%)")
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
# 主視窗
# -----------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python 多媒體批次處理工具 (Pro UI)")
        self.resize(1300, 950) 
        self.worker = None 
        self.settings = QSettings("MyCompany", "ImageToolApp")
        self.active_pbar = None
        self.active_plbl = None
        
        self.init_style()
        self.init_ui()

    def init_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            /* 右側面板樣式與字體加大 */
            QWidget#RightFrame { background-color: #dfd4ba; }
            QWidget#RightFrame QLabel, QWidget#RightFrame QCheckBox, 
            QWidget#RightFrame QGroupBox, QWidget#RightFrame QLineEdit, 
            QWidget#RightFrame QComboBox, QWidget#RightFrame QPushButton {
                color: #000000; font-size: 16px; 
            }
            QGroupBox { font-weight: bold; border: 1px solid #aaa; border-radius: 5px; margin-top: 20px; font-size: 16px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #000000; }
            QPushButton#ExecBtn { background-color: #0078D7; color: white; border: none; padding: 12px; border-radius: 5px; font-size: 18px; font-weight: bold; min-width: 150px; }
            QPushButton#ExecBtn:hover { background-color: #005a9e; }
            QComboBox { padding: 5px; }
            QLineEdit { padding: 5px; }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左側選單
        self.menu_frame = QWidget()
        self.menu_frame.setStyleSheet("background-color: #2d2d2d;")
        self.menu_frame.setFixedWidth(240)
        self.menu_layout = QVBoxLayout(self.menu_frame)
        self.menu_layout.setContentsMargins(0, 20, 0, 0)
        self.menu_layout.setSpacing(0)

        self.menu_buttons = []
        self.add_menu_item("圖片處理", 0)
        self.add_menu_item("影片銳利化", 1)
        self.add_menu_item("修改檔名前後綴", 2)
        self.add_menu_item("圖片多尺寸生成", 3)
        self.add_menu_item("圖片填色", 4)
        self.menu_layout.addStretch()

        # 右側內容
        right_frame = QWidget()
        right_frame.setObjectName("RightFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_scaling_ui())
        self.stack.addWidget(self.page_video_ui())
        self.stack.addWidget(self.page_rename_ui())
        self.stack.addWidget(self.page_multi_ui())
        self.stack.addWidget(self.page_fill_ui())

        # 底部狀態與Log
        self.file_prog_widget = QWidget()
        self.file_prog_widget.setFixedHeight(60) 
        fp_layout = QVBoxLayout(self.file_prog_widget); fp_layout.setContentsMargins(15, 5, 15, 5)
        self.lbl_current_file = SelectableLabel("等待執行..."); fp_layout.addWidget(self.lbl_current_file)
        row_fp = QHBoxLayout()
        self.pbar_file = QProgressBar(); self.pbar_file.setRange(0, 100)
        self.lbl_file_pct = SelectableLabel("0%"); row_fp.addWidget(self.pbar_file); row_fp.addWidget(self.lbl_file_pct)
        fp_layout.addLayout(row_fp)

        log_widget = QWidget()
        log_layout = QHBoxLayout(log_widget); log_layout.setContentsMargins(10, 5, 10, 10)
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setFixedHeight(100)
        btn_clear = QPushButton("清除"); btn_clear.clicked.connect(self.log_area.clear)
        log_layout.addWidget(self.log_area); log_layout.addWidget(btn_clear, 0, Qt.AlignTop)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.stack)
        bottom = QWidget(); bl = QVBoxLayout(bottom); bl.setContentsMargins(0,0,0,0)
        bl.addWidget(self.file_prog_widget); bl.addWidget(log_widget)
        splitter.addWidget(bottom)
        splitter.setStretchFactor(0, 1); splitter.setStretchFactor(1, 0)

        right_layout.addWidget(splitter)
        main_layout.addWidget(self.menu_frame)
        main_layout.addWidget(right_frame)

        self.switch_page(0)

    def add_menu_item(self, text, index):
        btn = SidebarButton(text, index)
        btn.clicked.connect(self.switch_page)
        self.menu_layout.addWidget(btn)
        self.menu_buttons.append(btn)

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for btn in self.menu_buttons:
            btn.set_selected(btn.index == index)

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.moveCursor(QTextCursor.Start)
        self.log_area.insertPlainText(f"[{timestamp}] {message}\n")
        self.log_area.moveCursor(QTextCursor.Start)

    def update_overall_progress(self, val):
        if self.active_pbar: self.active_pbar.setValue(val)
        if self.active_plbl: self.active_plbl.setText(f"{val}%")
    def update_current_file(self, filename): self.lbl_current_file.setText(f"正在處理: {filename}")
    def update_file_progress(self, val): self.pbar_file.setValue(val); self.lbl_file_pct.setText(f"{val}%")

    def run_worker(self, func, target_pbar=None, target_plbl=None, **kwargs):
        if 'input_path' in kwargs and not kwargs['input_path']:
            self.log("⚠️ 錯誤：請先選擇輸入資料夾")
            return
        if 'output_path' in kwargs and not kwargs['output_path']:
            self.log("⚠️ 錯誤：請先選擇輸出資料夾")
            return

        self.active_pbar = target_pbar
        self.active_plbl = target_plbl
        self.log("⏳ 準備開始任務...")
        if self.active_pbar: self.active_pbar.setValue(0)
        if self.active_plbl: self.active_plbl.setText("0%")
        self.update_file_progress(0)
        
        self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_overall_progress)
        self.worker.current_file_signal.connect(self.update_current_file)
        self.worker.file_progress_signal.connect(self.update_file_progress)
        self.worker.finished.connect(lambda: utils.show_notification("處理完成", "作業已結束！"))
        self.worker.start()

    # --- Helper Functions ---
    def select_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder: line_edit.setText(folder)

    def select_file(self, line_edit, png_only=False):
        # 修正：允許所有圖片格式
        filters = "Media (*.png *.jpg *.jpeg *.webp *.bmp *.tiff);;All (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇檔案", "", filters)
        if file_path: line_edit.setText(file_path)

    def check_file_info(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "選擇檔案", "", "All Files (*)")
        if file_path:
            info = logic.get_media_info(file_path)
            msg = QMessageBox(self)
            msg.setWindowTitle("檔案資訊"); msg.setText(f"檔案: {file_path}"); msg.setDetailedText(info); msg.exec()

    def create_path_group(self, need_output=True, png_only_input=False):
        group = QGroupBox("檔案路徑")
        layout = QFormLayout(); layout.setSpacing(10)
        
        edt_in = QLineEdit()
        edt_in.textChanged.connect(self.on_path_changed)
        
        btn_folder = QPushButton("📁 資料夾")
        btn_folder.setFixedWidth(80)
        btn_folder.clicked.connect(lambda: self.select_folder(edt_in))

        btn_file = QPushButton("📄 檔案")
        btn_file.setFixedWidth(80)
        btn_file.clicked.connect(lambda: self.select_file(edt_in, png_only=png_only_input))
        
        row_in = QHBoxLayout(); row_in.addWidget(edt_in); row_in.addWidget(btn_folder); row_in.addWidget(btn_file)
        layout.addRow(SelectableLabel("輸入路徑:"), row_in)

        edt_out = None
        if need_output:
            edt_out = QLineEdit()
            btn_out = QPushButton("📂 資料夾")
            btn_out.setFixedWidth(80)
            btn_out.clicked.connect(lambda: self.select_folder(edt_out))
            row_out = QHBoxLayout(); row_out.addWidget(edt_out); row_out.addWidget(btn_out)
            layout.addRow(SelectableLabel("輸出資料夾:"), row_out)
            
        group.setLayout(layout)
        return group, edt_in, edt_out
    
    def on_path_changed(self):
        if self.stack.currentWidget() == self.fill_page_widget:
            self.update_fill_preview()

    def _create_page_structure(self, btn_text="開始執行", on_click=None):
        page_root = QWidget()
        root_layout = QVBoxLayout(page_root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll)
        
        bottom_area = QWidget()
        bottom_layout = QHBoxLayout(bottom_area)
        btn = QPushButton(btn_text); btn.setObjectName("ExecBtn")
        if on_click: btn.clicked.connect(on_click)
        pbar = QProgressBar(); pbar.setRange(0, 100); pbar.setTextVisible(False)
        plbl = SelectableLabel("0%"); plbl.setFixedWidth(50)
        
        bottom_layout.addWidget(btn); bottom_layout.addWidget(SelectableLabel("總進度:")); bottom_layout.addWidget(pbar); bottom_layout.addWidget(plbl)
        root_layout.addWidget(bottom_area)
        return page_root, content_layout, pbar, plbl

    # --- 1. Scaling ---
    def page_scaling_ui(self):
        w, content, self.sc_pbar, self.sc_plbl = self._create_page_structure("開始處理", self.run_scaling)
        grp, self.sc_in, self.sc_out = self.create_path_group()
        content.addWidget(grp)
        
        grp_opts = QGroupBox("設定參數")
        form = QFormLayout()
        self.sc_mode = QComboBox()
        self.sc_mode.addItems(["模式 1: 指定縮放比例 (Ratio)", "模式 2: 指定寬度 (Target Width)", "模式 3: 指定高度 (Target Height)"])
        self.stack_modes = QStackedWidget()
        
        w_m1 = QWidget(); l1 = QHBoxLayout(w_m1); l1.setContentsMargins(0,0,0,0)
        self.sc_val_ratio = QLineEdit("1.0"); l1.addWidget(self.sc_val_ratio); l1.addWidget(SelectableLabel("(範圍 0.1~5.0)"))
        self.stack_modes.addWidget(w_m1)
        
        w_m2 = QWidget(); l2 = QHBoxLayout(w_m2); l2.setContentsMargins(0,0,0,0)
        self.sc_val_width = QLineEdit("1920"); l2.addWidget(self.sc_val_width); l2.addWidget(SelectableLabel("px"))
        self.stack_modes.addWidget(w_m2)

        w_m3 = QWidget(); l3 = QHBoxLayout(w_m3); l3.setContentsMargins(0,0,0,0)
        self.sc_val_height = QLineEdit("1080"); l3.addWidget(self.sc_val_height); l3.addWidget(SelectableLabel("px"))
        self.stack_modes.addWidget(w_m3)

        self.sc_mode.currentIndexChanged.connect(self.stack_modes.setCurrentIndex)
        self.sc_prefix = QLineEdit(); self.sc_postfix = QLineEdit("")
        self.sc_author = QLineEdit(str(self.settings.value("img_author", ""))); self.sc_desc = QLineEdit()
        self.sc_sharpness = QLineEdit("1.0"); self.sc_brightness = QLineEdit("1.0")

        form.addRow(SelectableLabel("縮放模式:"), self.sc_mode); form.addRow(SelectableLabel("參數:"), self.stack_modes)
        form.addRow(SelectableLabel("銳利度:"), self.sc_sharpness); form.addRow(SelectableLabel("亮度:"), self.sc_brightness)
        form.addRow(SelectableLabel("前綴:"), self.sc_prefix); form.addRow(SelectableLabel("後綴:"), self.sc_postfix)
        form.addRow(SelectableLabel("作者:"), self.sc_author); form.addRow(SelectableLabel("描述:"), self.sc_desc)
        grp_opts.setLayout(form); content.addWidget(grp_opts)

        self.sc_rec = QCheckBox("含子資料夾"); self.sc_rec.setChecked(self.settings.value("sc_rec", True, type=bool))
        self.sc_jpg = QCheckBox("強制轉 JPG"); self.sc_jpg.setChecked(self.settings.value("sc_jpg", True, type=bool))
        self.sc_low = QCheckBox("副檔名轉小寫"); self.sc_low.setChecked(self.settings.value("sc_low", True, type=bool))
        self.sc_del = QCheckBox("轉檔後刪除原始檔"); self.sc_del.setChecked(self.settings.value("sc_del", True, type=bool))
        self.sc_crop = QCheckBox("豆包圖裁切"); self.sc_crop.setChecked(self.settings.value("sc_crop", False, type=bool))
        self.sc_meta = QCheckBox("移除檔案 Meta"); self.sc_meta.setChecked(self.settings.value("sc_meta", False, type=bool))
        
        content.addWidget(self.sc_rec); content.addWidget(self.sc_jpg); content.addWidget(self.sc_low)
        content.addWidget(self.sc_del); content.addWidget(self.sc_crop); content.addWidget(self.sc_meta); content.addStretch()
        return w
    
    def run_scaling(self):
        mode = ['ratio', 'width', 'height'][self.sc_mode.currentIndex()]
        try:
            val1 = float(self.sc_val_ratio.text()) if mode == 'ratio' else int(self.sc_val_width.text()) if mode == 'width' else int(self.sc_val_height.text())
            sharp=float(self.sc_sharpness.text()); bright=float(self.sc_brightness.text())
        except: self.log("❌ 參數錯誤"); return
        
        self.settings.setValue("img_author", self.sc_author.text())
        self.settings.setValue("sc_rec", self.sc_rec.isChecked())
        self.settings.setValue("sc_jpg", self.sc_jpg.isChecked())
        self.settings.setValue("sc_low", self.sc_low.isChecked())
        self.settings.setValue("sc_del", self.sc_del.isChecked())
        self.settings.setValue("sc_crop", self.sc_crop.isChecked())
        self.settings.setValue("sc_meta", self.sc_meta.isChecked())

        self.run_worker(logic.task_scaling, target_pbar=self.sc_pbar, target_plbl=self.sc_plbl, 
                        input_path=self.sc_in.text(), output_path=self.sc_out.text(), mode=mode, mode_value_1=val1, mode_value_2=0, 
                        recursive=self.sc_rec.isChecked(), convert_jpg=self.sc_jpg.isChecked(), 
                        lower_ext=self.sc_low.isChecked(), delete_original=self.sc_del.isChecked(), 
                        prefix=self.sc_prefix.text(), postfix=self.sc_postfix.text(), crop_doubao=self.sc_crop.isChecked(), 
                        sharpen_factor=sharp, brightness_factor=bright, 
                        remove_metadata=self.sc_meta.isChecked(), author=self.sc_author.text(), description=self.sc_desc.text())

    # --- 2. Video ---
    def page_video_ui(self):
        w, content, self.vd_pbar, self.vd_plbl = self._create_page_structure("開始影片處理", self.run_video)
        grp, self.vd_in, self.vd_out = self.create_path_group()
        content.addWidget(grp)
        # Simplified placeholder for video ui to keep code manageable in one block
        self.vd_rec = QCheckBox("含子資料夾"); self.vd_rec.setChecked(self.settings.value("vd_rec", True, type=bool))
        content.addWidget(self.vd_rec)
        content.addStretch()
        return w
    
    def run_video(self):
        self.log("請依照 scaling 頁面模式補齊 video UI") 

    # --- 3. Rename ---
    def page_rename_ui(self):
        w, content, self.rn_pbar, self.rn_plbl = self._create_page_structure("執行更名", self.run_rename)
        grp, self.rn_in, _ = self.create_path_group(False)
        content.addWidget(grp)
        
        self.chk_prefix = QCheckBox("修改前綴"); self.edt_old_prefix = QLineEdit(); self.edt_new_prefix = QLineEdit()
        self.chk_suffix = QCheckBox("修改後綴"); self.edt_old_suffix = QLineEdit(); self.edt_new_suffix = QLineEdit()
        content.addWidget(self.chk_prefix); content.addWidget(self.edt_old_prefix); content.addWidget(self.edt_new_prefix)
        content.addWidget(self.chk_suffix); content.addWidget(self.edt_old_suffix); content.addWidget(self.edt_new_suffix)
        
        self.rn_rec = QCheckBox("含子資料夾"); self.rn_rec.setChecked(True)
        content.addWidget(self.rn_rec); content.addStretch()
        return w

    def run_rename(self):
        self.run_worker(logic.task_rename_replace, target_pbar=self.rn_pbar, target_plbl=self.rn_plbl,
                        input_path=self.rn_in.text(), recursive=self.rn_rec.isChecked(), 
                        do_prefix=self.chk_prefix.isChecked(), old_prefix=self.edt_old_prefix.text(), new_prefix=self.edt_new_prefix.text(),
                        do_suffix=self.chk_suffix.isChecked(), old_suffix=self.edt_old_suffix.text(), new_suffix=self.edt_new_suffix.text())

    # --- 4. Multi Res ---
    def page_multi_ui(self):
        w, content, self.mt_pbar, self.mt_plbl = self._create_page_structure("生成多尺寸", self.run_multi)
        grp, self.mt_in, self.mt_out = self.create_path_group()
        content.addWidget(grp)
        self.mt_ori = QComboBox(); self.mt_ori.addItems(["水平", "垂直"])
        content.addWidget(self.mt_ori)
        self.mt_rec = QCheckBox("含子資料夾"); self.mt_rec.setChecked(True)
        content.addWidget(self.mt_rec); content.addStretch()
        return w

    def run_multi(self):
        self.run_worker(logic.task_multi_res, target_pbar=self.mt_pbar, target_plbl=self.mt_plbl,
                        input_path=self.mt_in.text(), output_path=self.mt_out.text(), recursive=self.mt_rec.isChecked(),
                        lower_ext=True, orientation='h' if self.mt_ori.currentIndex()==0 else 'v')

    # --- 5. Image Fill ---
    def page_fill_ui(self):
        w, content, self.fill_pbar, self.fill_plbl = self._create_page_structure("開始執行", self.run_fill)
        self.fill_page_widget = w 

        grp, self.fill_in, self.fill_out = self.create_path_group(png_only_input=False) # 支援所有圖片
        content.addWidget(grp)

        row_regions = QHBoxLayout()
        row_regions.setSpacing(15)
        
        self.reg_opaque = RegionControl("不透明區塊", has_target_select=True)
        self.reg_trans = RegionControl("透明區塊", has_target_select=False)
        self.reg_semi = RegionControl("半透明區塊", has_target_select=True)
        
        self.reg_opaque.settings_changed.connect(self.update_fill_preview)
        self.reg_trans.settings_changed.connect(self.update_fill_preview)
        self.reg_semi.settings_changed.connect(self.update_fill_preview)

        row_regions.addWidget(self.reg_opaque)
        row_regions.addWidget(self.reg_trans)
        row_regions.addWidget(self.reg_semi)
        
        content.addLayout(row_regions)

        content.addWidget(SelectableLabel("效果預覽:"))
        self.fill_preview_lbl = SelectableLabel()
        self.fill_preview_lbl.setAlignment(Qt.AlignCenter)
        self.fill_preview_lbl.setStyleSheet("border: 2px dashed #bbb; background: #ddd; min-height: 250px;")
        self.fill_preview_lbl.setScaledContents(False) 
        content.addWidget(self.fill_preview_lbl)

        # 選項
        self.fill_rec = QCheckBox("含子資料夾")
        self.fill_rec.setChecked(self.settings.value("fill_rec", False, type=bool))
        content.addWidget(self.fill_rec)

        self.fill_del = QCheckBox("刪除原始圖片")
        self.fill_del.setChecked(self.settings.value("fill_del", False, type=bool))
        content.addWidget(self.fill_del)

        row_fmt = QHBoxLayout()
        row_fmt.addWidget(SelectableLabel("輸出格式:"))
        self.fill_format = QComboBox()
        self.fill_format.addItems(["png", "jpg", "webp"])
        last_fmt = self.settings.value("fill_fmt", "png", type=str)
        self.fill_format.setCurrentText(last_fmt)
        row_fmt.addWidget(self.fill_format)
        row_fmt.addStretch()
        content.addLayout(row_fmt)
        
        content.addStretch()
        return w

    def update_fill_preview(self):
        input_path = self.fill_in.text()
        if not input_path:
            self.fill_preview_lbl.setText("請選擇輸入檔案或資料夾")
            return
        
        sample_file = None
        p = Path(input_path)
        if p.is_file():
            sample_file = p
        elif p.is_dir():
            files = list(p.glob("*.*"))
            # 找第一張是圖片的
            for f in files:
                if f.suffix.lower() in ['.jpg', '.png', '.jpeg', '.webp']:
                    sample_file = f
                    break
        
        if not sample_file:
            self.fill_preview_lbl.setText("找不到圖片進行預覽")
            return
        
        try:
            with Image.open(sample_file) as img:
                preview_size = (600, 600)
                img.thumbnail(preview_size) 
                
                settings_opaque = self.reg_opaque.get_settings()
                settings_trans = self.reg_trans.get_settings()
                settings_semi = self.reg_semi.get_settings()
                
                res_img = logic.process_single_image_fill(img, settings_opaque, settings_trans, settings_semi)
                
                qim = ImageQt.ImageQt(res_img)
                pix = QPixmap.fromImage(qim)
                self.fill_preview_lbl.setPixmap(pix)
        except Exception as e:
            self.fill_preview_lbl.setText(f"預覽錯誤: {e}")

    def run_fill(self):
        settings_opaque = self.reg_opaque.get_settings()
        settings_trans = self.reg_trans.get_settings()
        settings_semi = self.reg_semi.get_settings()
        
        self.settings.setValue("fill_rec", self.fill_rec.isChecked())
        self.settings.setValue("fill_del", self.fill_del.isChecked())
        self.settings.setValue("fill_fmt", self.fill_format.currentText())

        self.run_worker(logic.task_image_fill, target_pbar=self.fill_pbar, target_plbl=self.fill_plbl,
                        input_path=self.fill_in.text(), output_path=self.fill_out.text(),
                        recursive=self.fill_rec.isChecked(),
                        settings_opaque=settings_opaque, settings_trans=settings_trans, settings_semi=settings_semi,
                        delete_original=self.fill_del.isChecked(), output_format=self.fill_format.currentText())