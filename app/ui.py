from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame, 
                               QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QTextCursor

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
# 主視窗
# -----------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python 多媒體批次處理工具 (Pro UI)")
        self.resize(1200, 950) 
        self.worker = None 
        self.settings = QSettings("MyCompany", "ImageToolApp")
        self.active_pbar = None
        self.active_plbl = None
        
        self.init_style()
        self.init_ui()

    def init_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            
            /* --- 基本元件文字與字體 --- */
            QWidget#RightFrame QLabel, 
            QWidget#RightFrame QCheckBox, 
            QWidget#RightFrame QGroupBox, 
            QWidget#RightFrame QLineEdit {
                color: #000000;
                font-size: 16px;
            }
            
            /* --- QComboBox (下拉選單) 強制白底黑字 --- */
            QComboBox {
                color: #000000;
                background-color: #ffffff;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                font-size: 16px;
                selection-background-color: #0078D7;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #000000;
                selection-background-color: #0078D7;
                selection-color: #ffffff;
                outline: none;
            }
            
            QCheckBox { spacing: 8px; font-size: 16px; color: #000000; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            
            QLineEdit { 
                padding: 6px; 
                border: 1px solid #ccc; 
                border-radius: 4px; 
                background: #ffffff; 
                color: #000000;
                font-size: 16px;
            }
            
            QTextEdit { 
                font-family: Consolas, monospace; 
                font-size: 14px;
                border: 1px solid #ccc;
                background-color: #ffffff;
                color: #000000;
            }
            
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #aaa; 
                border-radius: 5px; 
                margin-top: 20px; 
                font-size: 16px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px; 
                color: #000000;
            }

            /* --- 按鈕 --- */
            QPushButton#ExecBtn { 
                background-color: #0078D7; 
                color: white; 
                border: none; 
                padding: 15px; 
                border-radius: 5px; 
                font-size: 18px; 
                font-weight: bold;
                min-width: 150px;
            }
            QPushButton#ExecBtn:hover { background-color: #005a9e; }
            QPushButton#ExecBtn:pressed { background-color: #004578; }

            QPushButton#BrowseFolderBtn, QPushButton#BrowseFileBtn {
                background-color: #666; color: white; font-size: 14px; padding: 6px; border-radius: 3px;
            }
            QPushButton#ClearLogBtn {
                background-color: #888888; color: white; font-size: 13px; padding: 5px; border-radius: 3px; min-width: 70px;
            }
            QPushButton#CheckInfoBtn {
                background-color: #FF9800; color: white; font-size: 13px; padding: 5px; border-radius: 3px;
            }

            /* --- 進度條 --- */
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 5px;
                text-align: center;
                height: 20px;
                background: #fff;
                color: #000;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #0078D7;
                width: 10px;
            }
            QProgressBar#FileProgressBar::chunk { background-color: #4CAF50; }

            /* --- Scrollbar --- */
            QScrollBar:vertical {
                border: none;
                background: #e0e0e0;
                width: 16px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #909090;
                min-height: 30px;
                border-radius: 8px;
                border: 2px solid #e0e0e0;
            }
            QScrollBar::handle:vertical:hover { background: #0078D7; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            
            QScrollArea { border: none; background: transparent; }
            QWidget#ScrollContents { background-color: #f0f0f0; }
            QWidget#BottomArea { background-color: #e6e6e6; border-top: 1px solid #cccccc; }
            QWidget#FileProgressPanel { background-color: #e8e8e8; border: 1px solid #ccc; border-radius: 5px; }
        """)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 左側選單 ---
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
        self.menu_layout.addStretch()

        # --- 右側內容 ---
        right_frame = QWidget()
        right_frame.setObjectName("RightFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. StackedWidget
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_scaling_ui())
        self.stack.addWidget(self.page_video_ui())
        self.stack.addWidget(self.page_rename_ui())
        self.stack.addWidget(self.page_multi_ui())

        # 2. 單一檔案進度面板
        self.file_prog_widget = QWidget()
        self.file_prog_widget.setObjectName("FileProgressPanel")
        self.file_prog_widget.setFixedHeight(80) 
        fp_layout = QVBoxLayout(self.file_prog_widget)
        fp_layout.setContentsMargins(15, 10, 15, 10)
        fp_layout.setSpacing(5)
        
        self.lbl_current_file = QLabel("等待執行...")
        self.lbl_current_file.setStyleSheet("font-weight: bold; color: #333;")
        
        row_fp = QHBoxLayout()
        self.pbar_file = QProgressBar()
        self.pbar_file.setObjectName("FileProgressBar") 
        self.pbar_file.setRange(0, 100)
        self.pbar_file.setValue(0)
        self.lbl_file_pct = QLabel("0%")
        self.lbl_file_pct.setFixedWidth(40)
        self.lbl_file_pct.setAlignment(Qt.AlignCenter)
        row_fp.addWidget(self.pbar_file)
        row_fp.addWidget(self.lbl_file_pct)
        
        fp_layout.addWidget(self.lbl_current_file)
        fp_layout.addLayout(row_fp)

        # 3. Log 區域
        log_widget = QWidget()
        log_layout = QHBoxLayout(log_widget)
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("等待執行指令...")
        
        btn_clear = QPushButton("清除 Log")
        btn_clear.setObjectName("ClearLogBtn")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self.log_area.clear)
        
        log_layout.addWidget(self.log_area)
        log_layout.addWidget(btn_clear, 0, Qt.AlignTop)

        # 4. Splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.stack)   
        
        bottom_group = QWidget()
        bg_layout = QVBoxLayout(bottom_group)
        bg_layout.setContentsMargins(0,0,0,0)
        bg_layout.setSpacing(0)
        bg_layout.addWidget(self.file_prog_widget)
        bg_layout.addWidget(log_widget)
        
        splitter.addWidget(bottom_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

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
        self.lbl_current_file.setText("準備中...")
        
        self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_overall_progress)
        self.worker.current_file_signal.connect(self.update_current_file)
        self.worker.file_progress_signal.connect(self.update_file_progress)
        self.worker.finished.connect(lambda: utils.show_notification("處理完成", "您的批次作業已結束！"))
        self.worker.start()

    # --- Helper Functions ---
    
    def select_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            line_edit.setText(folder)

    def select_file(self, line_edit):
        # 修正：擴充支援的格式清單 (包含 jpeg, webp, heic, tiff 等)
        filters = "Media (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.heic *.mp4 *.mov *.avi *.mkv *.webm *.flv);;Images (*.png *.jpg *.jpeg *.webp *.bmp *.tiff *.heic);;Videos (*.mp4 *.mov *.avi *.mkv *.webm *.flv);;All (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇檔案", "", 
            filters
        )
        if file_path:
            line_edit.setText(file_path)

    def check_file_info(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇檔案", "", "All Files (*)"
        )
        if file_path:
            info = logic.get_media_info(file_path)
            msg = QMessageBox(self)
            msg.setWindowTitle("檔案資訊")
            msg.setText(f"檔案: {file_path}")
            msg.setDetailedText(info)
            msg.setIcon(QMessageBox.Information)
            msg.exec()

    def create_path_group(self, need_output=True):
        group = QGroupBox("檔案路徑")
        layout = QFormLayout()
        layout.setSpacing(15)
        
        edt_in = QLineEdit()
        btn_folder = QPushButton("📁 資料夾")
        btn_folder.setObjectName("BrowseFolderBtn")
        btn_folder.setFixedWidth(80)
        btn_folder.clicked.connect(lambda: self.select_folder(edt_in))

        btn_file = QPushButton("📄 檔案")
        btn_file.setObjectName("BrowseFileBtn")
        btn_file.setFixedWidth(80)
        btn_file.clicked.connect(lambda: self.select_file(edt_in))
        
        row_in = QHBoxLayout()
        row_in.addWidget(edt_in)
        row_in.addWidget(btn_folder)
        row_in.addWidget(btn_file)
        layout.addRow(SelectableLabel("輸入路徑:"), row_in)

        edt_out = None
        if need_output:
            edt_out = QLineEdit()
            btn_out = QPushButton("📂 資料夾")
            btn_out.setObjectName("BrowseFolderBtn")
            btn_out.setFixedWidth(80)
            btn_out.clicked.connect(lambda: self.select_folder(edt_out))
            
            row_out = QHBoxLayout()
            row_out.addWidget(edt_out)
            row_out.addWidget(btn_out)
            layout.addRow(SelectableLabel("輸出資料夾:"), row_out)
            
        group.setLayout(layout)
        return group, edt_in, edt_out

    def _create_page_structure(self, btn_text="開始執行", on_click=None):
        page_root = QWidget()
        root_layout = QVBoxLayout(page_root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_content = QWidget()
        scroll_content.setObjectName("ScrollContents")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        scroll.setWidget(scroll_content)
        root_layout.addWidget(scroll)
        
        bottom_area = QWidget()
        bottom_area.setObjectName("BottomArea")
        bottom_layout = QHBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(20, 15, 20, 15)
        
        btn = QPushButton(btn_text)
        btn.setObjectName("ExecBtn")
        if on_click:
            btn.clicked.connect(on_click)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(False)
        
        progress_label = QLabel("0%")
        progress_label.setFixedWidth(50)
        progress_label.setAlignment(Qt.AlignCenter)
        
        bottom_layout.addWidget(btn)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(SelectableLabel("總進度:"))
        bottom_layout.addWidget(progress_bar)
        bottom_layout.addWidget(progress_label)
        
        root_layout.addWidget(bottom_area)
        return page_root, content_layout, progress_bar, progress_label

    # --- 1. 圖片處理 ---
    def page_scaling_ui(self):
        w, content, p_bar, p_lbl = self._create_page_structure("開始處理", self.run_scaling)
        self.sc_pbar = p_bar
        self.sc_plbl = p_lbl
        
        grp_path, self.sc_in, self.sc_out = self.create_path_group()
        content.addWidget(grp_path)
        grp_opts = QGroupBox("設定參數")
        form = QFormLayout()
        form.setSpacing(15)
        
        self.sc_mode = QComboBox()
        # 更新：移除模式 4，更新模式 2 與 3 的名稱
        self.sc_mode.addItems(["模式 1: 指定縮放比例 (Ratio)", "模式 2: 指定寬度 (Target Width)", "模式 3: 指定高度 (Target Height)"])
        self.stack_modes = QStackedWidget()
        
        # Mode 1: Ratio
        w_m1 = QWidget(); l1 = QHBoxLayout(w_m1); l1.setContentsMargins(0,0,0,0)
        self.sc_val_ratio = QLineEdit("1.0"); l1.addWidget(self.sc_val_ratio); l1.addWidget(SelectableLabel("(範圍 0.1~5.0)"))
        self.stack_modes.addWidget(w_m1)
        
        # Mode 2: Width
        w_m2 = QWidget(); l2 = QHBoxLayout(w_m2); l2.setContentsMargins(0,0,0,0)
        self.sc_val_width = QLineEdit("1920"); l2.addWidget(self.sc_val_width); l2.addWidget(SelectableLabel("px (強制縮放至此寬度)"))
        self.stack_modes.addWidget(w_m2)
        
        # Mode 3: Height
        w_m3 = QWidget(); l3 = QHBoxLayout(w_m3); l3.setContentsMargins(0,0,0,0)
        self.sc_val_height = QLineEdit("1080"); l3.addWidget(self.sc_val_height); l3.addWidget(SelectableLabel("px (強制縮放至此高度)"))
        self.stack_modes.addWidget(w_m3)
        
        self.sc_mode.currentIndexChanged.connect(self.stack_modes.setCurrentIndex)
        
        self.sc_prefix = QLineEdit(); self.sc_postfix = QLineEdit("")
        self.sc_author = QLineEdit(str(self.settings.value("img_author", ""))); self.sc_desc = QLineEdit()
        btn_check = QPushButton("檢查檔案資訊"); btn_check.setObjectName("CheckInfoBtn"); btn_check.clicked.connect(self.check_file_info)
        row_desc = QHBoxLayout(); row_desc.addWidget(self.sc_desc); row_desc.addWidget(btn_check)
        
        self.sc_sharpness = QLineEdit("1.0"); row_sharp = QHBoxLayout(); row_sharp.addWidget(self.sc_sharpness); row_sharp.addWidget(SelectableLabel("(0.0 ~ 2.0+, 1.0為原始)"))
        self.sc_brightness = QLineEdit("1.0"); row_bright = QHBoxLayout(); row_bright.addWidget(self.sc_brightness); row_bright.addWidget(SelectableLabel("(0.0 ~ 2.0+, 1.0為原始)"))
        
        form.addRow(SelectableLabel("縮放模式:"), self.sc_mode)
        form.addRow(SelectableLabel("模式參數:"), self.stack_modes)
        form.addRow(SelectableLabel("銳利度:"), row_sharp)
        form.addRow(SelectableLabel("亮度:"), row_bright)
        form.addRow(SelectableLabel("檔名前綴:"), self.sc_prefix)
        form.addRow(SelectableLabel("檔名後綴:"), self.sc_postfix)
        form.addRow(SelectableLabel("作者標記:"), self.sc_author)
        form.addRow(SelectableLabel("圖片描述:"), row_desc)
        grp_opts.setLayout(form); content.addWidget(grp_opts)
        
        # 修正：將「遞歸處理」改為「含子資料夾」
        self.sc_rec = QCheckBox("含子資料夾"); self.sc_rec.setChecked(self.settings.value("sc_rec", True, type=bool))
        self.sc_jpg = QCheckBox("強制轉 JPG"); self.sc_jpg.setChecked(self.settings.value("sc_jpg", True, type=bool))
        self.sc_low = QCheckBox("副檔名轉小寫"); self.sc_low.setChecked(self.settings.value("sc_low", True, type=bool))
        self.sc_del = QCheckBox("轉檔後刪除原始檔"); self.sc_del.setChecked(self.settings.value("sc_del", True, type=bool))
        self.sc_crop = QCheckBox("豆包圖裁切"); self.sc_crop.setChecked(self.settings.value("sc_crop", False, type=bool))
        self.sc_meta = QCheckBox("移除檔案 Meta (作者、描述、地理資訊)"); self.sc_meta.setChecked(self.settings.value("sc_meta", False, type=bool))
        
        chk_layout = QVBoxLayout(); chk_layout.setSpacing(10)
        chk_layout.addWidget(self.sc_rec); chk_layout.addWidget(self.sc_jpg); chk_layout.addWidget(self.sc_low)
        chk_layout.addWidget(self.sc_del); chk_layout.addWidget(self.sc_crop); chk_layout.addWidget(self.sc_meta)
        content.addLayout(chk_layout); content.addStretch()
        return w

    # --- 2. 影片銳利化 ---
    def page_video_ui(self):
        w, content, p_bar, p_lbl = self._create_page_structure("開始影片處理", self.run_video)
        self.vd_pbar = p_bar; self.vd_plbl = p_lbl
        
        grp_path, self.vd_in, self.vd_out = self.create_path_group()
        content.addWidget(grp_path)
        grp_opts = QGroupBox("設定參數")
        form = QFormLayout()
        form.setSpacing(15)
        
        self.vd_luma_size = QLineEdit("5"); row_size = QHBoxLayout(); row_size.addWidget(self.vd_luma_size); row_size.addWidget(SelectableLabel("(範圍: 3-13 奇數)"))
        self.vd_luma_amount = QLineEdit("1.2"); row_amt = QHBoxLayout(); row_amt.addWidget(self.vd_luma_amount); row_amt.addWidget(SelectableLabel("(範圍: 0.0-5.0)"))
        
        self.vd_mode = QComboBox()
        self.vd_mode.addItems(["保持原始尺寸 (Original)", "1080p HD (自動適應)", "720p HD (自動適應)", "480p SD (自動適應)", "自定義縮放比例 (Ratio)"])
        self.stack_vd_modes = QStackedWidget()
        self.stack_vd_modes.addWidget(QLabel(""))
        self.stack_vd_modes.addWidget(QLabel(""))
        self.stack_vd_modes.addWidget(QLabel(""))
        self.stack_vd_modes.addWidget(QLabel(""))
        w_vratio = QWidget(); l_vratio = QHBoxLayout(w_vratio); l_vratio.setContentsMargins(0,0,0,0)
        self.vd_val_ratio = QLineEdit("1.0"); l_vratio.addWidget(self.vd_val_ratio); l_vratio.addWidget(SelectableLabel("(範圍 0.1~5.0)"))
        self.stack_vd_modes.addWidget(w_vratio)
        self.vd_mode.currentIndexChanged.connect(self.stack_vd_modes.setCurrentIndex)

        self.vd_author = QLineEdit(str(self.settings.value("vid_author", ""))); self.vd_desc = QLineEdit()
        btn_check = QPushButton("檢查檔案資訊"); btn_check.setObjectName("CheckInfoBtn"); btn_check.clicked.connect(self.check_file_info)
        row_desc = QHBoxLayout(); row_desc.addWidget(self.vd_desc); row_desc.addWidget(btn_check)
        self.vd_prefix = QLineEdit(); self.vd_postfix = QLineEdit("")
        
        form.addRow(SelectableLabel("銳利化核心:"), row_size); form.addRow(SelectableLabel("強度:"), row_amt)
        form.addRow(SelectableLabel("縮放模式:"), self.vd_mode); form.addRow(SelectableLabel(""), self.stack_vd_modes)
        form.addRow(SelectableLabel("作者:"), self.vd_author); form.addRow(SelectableLabel("描述:"), row_desc)
        form.addRow(SelectableLabel("前綴:"), self.vd_prefix); form.addRow(SelectableLabel("後綴:"), self.vd_postfix)
        grp_opts.setLayout(form); content.addWidget(grp_opts)
        
        # 修正：將「遞歸處理」改為「含子資料夾」
        self.vd_rec = QCheckBox("含子資料夾"); self.vd_rec.setChecked(self.settings.value("vd_rec", True, type=bool))
        self.vd_low = QCheckBox("副檔名轉小寫"); self.vd_low.setChecked(self.settings.value("vd_low", True, type=bool))
        self.vd_del = QCheckBox("刪除原始檔"); self.vd_del.setChecked(self.settings.value("vd_del", False, type=bool))
        self.vd_h264 = QCheckBox("強制轉 MP4 (H.264)"); self.vd_h264.setChecked(self.settings.value("vd_h264", True, type=bool))
        self.vd_meta = QCheckBox("移除檔案 Meta (作者、描述、地理資訊)"); self.vd_meta.setChecked(self.settings.value("vd_meta", False, type=bool))
        
        chk_layout = QVBoxLayout(); chk_layout.setSpacing(10)
        chk_layout.addWidget(self.vd_rec); chk_layout.addWidget(self.vd_low); chk_layout.addWidget(self.vd_del)
        chk_layout.addWidget(self.vd_h264); chk_layout.addWidget(self.vd_meta)
        content.addLayout(chk_layout); content.addStretch()
        return w

    # --- 3. 改名 ---
    def page_rename_ui(self):
        w, content, p_bar, p_lbl = self._create_page_structure("執行更名", self.run_rename)
        self.rn_pbar = p_bar; self.rn_plbl = p_lbl
        grp_path, self.rn_in, _ = self.create_path_group(False); content.addWidget(grp_path)
        grp_opts = QGroupBox("設定更名規則"); layout = QVBoxLayout()
        self.chk_prefix = QCheckBox("修改前綴"); row_pre = QHBoxLayout()
        self.edt_old_prefix = QLineEdit(); self.edt_old_prefix.setPlaceholderText("舊"); self.edt_new_prefix = QLineEdit(); self.edt_new_prefix.setPlaceholderText("新")
        row_pre.addWidget(self.edt_old_prefix); row_pre.addWidget(SelectableLabel("->")); row_pre.addWidget(self.edt_new_prefix)
        self.chk_suffix = QCheckBox("修改後綴"); row_suf = QHBoxLayout()
        self.edt_old_suffix = QLineEdit(); self.edt_old_suffix.setPlaceholderText("舊"); self.edt_new_suffix = QLineEdit(); self.edt_new_suffix.setPlaceholderText("新")
        row_suf.addWidget(self.edt_old_suffix); row_suf.addWidget(SelectableLabel("->")); row_suf.addWidget(self.edt_new_suffix)
        layout.addWidget(self.chk_prefix); layout.addLayout(row_pre); layout.addWidget(self.chk_suffix); layout.addLayout(row_suf)
        grp_opts.setLayout(layout); content.addWidget(grp_opts)
        self.rn_rec = QCheckBox("含子資料夾"); self.rn_rec.setChecked(True); content.addWidget(self.rn_rec); content.addStretch()
        return w

    # --- 4. 多尺寸 ---
    def page_multi_ui(self):
        w, content, p_bar, p_lbl = self._create_page_structure("生成多尺寸", self.run_multi)
        self.mt_pbar = p_bar; self.mt_plbl = p_lbl
        lbl_info = QLabel("ℹ️ 自動生成 [1024, 512, 256, 128, 64, 32] px"); lbl_info.setStyleSheet("color: #555; font-style: italic;")
        content.addWidget(lbl_info)
        grp_path, self.mt_in, self.mt_out = self.create_path_group(); content.addWidget(grp_path)
        form = QFormLayout(); self.mt_ori = QComboBox(); self.mt_ori.addItems(["水平", "垂直"]); form.addRow(SelectableLabel("參考方向:"), self.mt_ori)
        content.addLayout(form)
        self.mt_rec = QCheckBox("含子資料夾"); self.mt_rec.setChecked(True); self.mt_low = QCheckBox("副檔名轉小寫"); self.mt_low.setChecked(True)
        content.addWidget(self.mt_rec); content.addWidget(self.mt_low); content.addStretch()
        return w

    # --- Run Methods ---
    def run_scaling(self):
        # 更新：只剩下 mode 1(ratio), 2(width), 3(height)
        mode = ['ratio', 'width', 'height'][self.sc_mode.currentIndex()]
        val1=0.0; val2=0.0
        try:
            if mode=='ratio': val1=float(self.sc_val_ratio.text())
            elif mode=='width': val1=int(self.sc_val_width.text())
            elif mode=='height': val1=int(self.sc_val_height.text())
            # 移除了 both
            sharp=float(self.sc_sharpness.text()); bright=float(self.sc_brightness.text())
        except: self.log("❌ 參數錯誤"); return
        
        in_p=self.sc_in.text(); out_p=self.sc_out.text(); pre=self.sc_prefix.text(); post=self.sc_postfix.text()
        if in_p==out_p and not self.sc_del.isChecked() and not pre and not post:
            QMessageBox.warning(self, "警告", "輸入輸出路徑相同且無前後綴，請修正避免覆蓋。"); return
            
        # Save Settings
        self.settings.setValue("img_author", self.sc_author.text())
        self.settings.setValue("sc_rec", self.sc_rec.isChecked())
        self.settings.setValue("sc_jpg", self.sc_jpg.isChecked())
        self.settings.setValue("sc_low", self.sc_low.isChecked())
        self.settings.setValue("sc_del", self.sc_del.isChecked())
        self.settings.setValue("sc_crop", self.sc_crop.isChecked())
        self.settings.setValue("sc_meta", self.sc_meta.isChecked())

        self.run_worker(logic.task_scaling, target_pbar=self.sc_pbar, target_plbl=self.sc_plbl, 
                        input_path=in_p, output_path=out_p, mode=mode, mode_value_1=val1, mode_value_2=val2, 
                        recursive=self.sc_rec.isChecked(), convert_jpg=self.sc_jpg.isChecked(), 
                        lower_ext=self.sc_low.isChecked(), delete_original=self.sc_del.isChecked(), 
                        prefix=pre, postfix=post, crop_doubao=self.sc_crop.isChecked(), 
                        sharpen_factor=sharp, brightness_factor=bright, 
                        remove_metadata=self.sc_meta.isChecked(),
                        author=self.sc_author.text(), description=self.sc_desc.text())

    def run_video(self):
        idx = self.vd_mode.currentIndex()
        scale_mode = ""
        scale_val = 1.0
        if idx == 0: scale_mode = "original"
        elif idx == 1: scale_mode = "hd1080"
        elif idx == 2: scale_mode = "hd720"
        elif idx == 3: scale_mode = "hd480"
        elif idx == 4: 
            scale_mode = "ratio"
            try: scale_val = float(self.vd_val_ratio.text())
            except: self.log("❌ 縮放比例錯誤"); return

        try: size=int(self.vd_luma_size.text()); amt=float(self.vd_luma_amount.text())
        except: self.log("❌ 銳利化參數錯誤"); return
        
        self.settings.setValue("vid_author", self.vd_author.text())
        self.settings.setValue("vd_rec", self.vd_rec.isChecked())
        self.settings.setValue("vd_low", self.vd_low.isChecked())
        self.settings.setValue("vd_del", self.vd_del.isChecked())
        self.settings.setValue("vd_h264", self.vd_h264.isChecked())
        self.settings.setValue("vd_meta", self.vd_meta.isChecked())

        self.run_worker(logic.task_video_sharpen, target_pbar=self.vd_pbar, target_plbl=self.vd_plbl,
                        input_path=self.vd_in.text(), output_path=self.vd_out.text(), 
                        recursive=self.vd_rec.isChecked(), lower_ext=self.vd_low.isChecked(), 
                        delete_original=self.vd_del.isChecked(), prefix=self.vd_prefix.text(), 
                        postfix=self.vd_postfix.text(), luma_m_size=size, luma_amount=amt, 
                        scale_mode=scale_mode, scale_value=scale_val, 
                        convert_h264=self.vd_h264.isChecked(), 
                        remove_metadata=self.vd_meta.isChecked(),
                        author=self.vd_author.text(), description=self.vd_desc.text())

    def run_rename(self):
        if not self.chk_prefix.isChecked() and not self.chk_suffix.isChecked(): QMessageBox.warning(self, "警告", "請勾選修改項目"); return
        self.run_worker(logic.task_rename_replace, target_pbar=self.rn_pbar, target_plbl=self.rn_plbl,
                        input_path=self.rn_in.text(), recursive=self.rn_rec.isChecked(), do_prefix=self.chk_prefix.isChecked(), old_prefix=self.edt_old_prefix.text(), new_prefix=self.edt_new_prefix.text(), do_suffix=self.chk_suffix.isChecked(), old_suffix=self.edt_old_suffix.text(), new_suffix=self.edt_new_suffix.text())

    def run_multi(self):
        self.run_worker(logic.task_multi_res, target_pbar=self.mt_pbar, target_plbl=self.mt_plbl,
                        input_path=self.mt_in.text(), output_path=self.mt_out.text(), recursive=self.mt_rec.isChecked(), lower_ext=self.mt_low.isChecked(), orientation='h' if self.mt_ori.currentIndex()==0 else 'v')