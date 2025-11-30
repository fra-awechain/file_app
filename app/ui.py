from datetime import datetime
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QTextCursor

# 引用我們拆分出去的模組
from app.workers import Worker
import app.logic as logic

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
        
        # UI 調整: 高度 80px
        self.setMinimumHeight(80) 

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # 左側藍色邊條
        self.indicator = QWidget()
        self.indicator.setFixedWidth(6)
        self.indicator.setStyleSheet("background-color: transparent;") 
        
        # 🔥 圖示
        self.icon_label = QLabel("🔥")
        self.icon_label.setStyleSheet("color: #66cfff; font-size: 16px;")
        self.icon_label.hide()
        
        # 文字標籤
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
        self.setWindowTitle("Python 圖片批次處理工具 (Pro UI)")
        self.resize(1150, 900) 
        self.worker = None 
        self.settings = QSettings("MyCompany", "ImageToolApp")
        
        self.init_style()
        self.init_ui()

    def init_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f0f0f0; }
            
            /* 文字顏色 */
            QWidget#RightFrame QLabel, 
            QWidget#RightFrame QCheckBox, 
            QWidget#RightFrame QGroupBox,
            QWidget#RightFrame QLineEdit,
            QWidget#RightFrame QComboBox {
                color: #000000;
                font-size: 16px;
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

            /* 執行按鈕 */
            QPushButton#ExecBtn { 
                background-color: #0078D7; 
                color: white; 
                border: none; 
                padding: 15px; 
                border-radius: 5px; 
                font-size: 18px; 
                font-weight: bold;
            }
            QPushButton#ExecBtn:hover { background-color: #005a9e; }
            QPushButton#ExecBtn:pressed { background-color: #004578; }

            /* 瀏覽按鈕 (資料夾) */
            QPushButton#BrowseFolderBtn {
                background-color: #666; 
                color: white;
                font-size: 14px; 
                padding: 6px;
                border-radius: 3px;
            }
            /* 瀏覽按鈕 (檔案) */
            QPushButton#BrowseFileBtn {
                background-color: #009688; 
                color: white;
                font-size: 14px; 
                padding: 6px;
                border-radius: 3px;
            }
            
            /* 清除 Log 按鈕 */
            QPushButton#ClearLogBtn {
                background-color: #888888;
                color: white;
                font-size: 13px;
                padding: 5px 10px;
                border-radius: 3px;
                min-width: 70px;
            }
            QPushButton#ClearLogBtn:hover {
                background-color: #666666;
            }

            /* Scrollbar */
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
            QScrollBar::handle:vertical:hover {
                background: #0078D7;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            
            QScrollArea { border: none; background: transparent; }
            QWidget#ScrollContents { background-color: #f0f0f0; }
            
            /* 底部按鈕區背景 */
            QWidget#BottomArea {
                background-color: #e6e6e6;
                border-top: 1px solid #cccccc;
            }
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
        self.add_menu_item("圖片縮放", 0)
        self.add_menu_item("PNG 轉 JPG", 1)
        self.add_menu_item("縮小至 1920px", 2)
        self.add_menu_item("檔名 Prefix", 3)
        self.add_menu_item("多尺寸生成", 4)
        
        self.menu_layout.addStretch()

        # --- 右側內容 ---
        right_frame = QWidget()
        right_frame.setObjectName("RightFrame")
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. StackedWidget (參數設定區)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_scaling_ui())
        self.stack.addWidget(self.page_convert_ui())
        self.stack.addWidget(self.page_resize1920_ui())
        self.stack.addWidget(self.page_rename_ui())
        self.stack.addWidget(self.page_multi_ui())

        # 2. Log 區域容器 (含清除按鈕)
        log_widget = QWidget()
        log_layout = QHBoxLayout(log_widget)
        log_layout.setContentsMargins(10, 10, 10, 10)
        log_layout.setSpacing(10)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("等待執行指令...")
        
        btn_clear = QPushButton("清除 Log")
        btn_clear.setObjectName("ClearLogBtn")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self.log_area.clear)
        
        log_layout.addWidget(self.log_area)
        log_layout.addWidget(btn_clear, 0, Qt.AlignTop)

        # 3. Splitter
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.stack)   
        splitter.addWidget(log_widget) 
        
        # 設定比例： 1:1
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

    def select_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if folder:
            line_edit.setText(folder)

    def select_file(self, line_edit):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇圖片檔案", "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.tiff *.heic);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)

    # 封裝 GroupBox + Path Input
    def create_path_group(self, need_output=True):
        group = QGroupBox("檔案路徑")
        layout = QFormLayout()
        layout.setSpacing(15)
        
        # 輸入路徑
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

        # 輸出路徑
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

    # --- 頁面建構器 ---
    def _create_page_structure(self):
        page_root = QWidget()
        
        root_layout = QVBoxLayout(page_root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        
        # 1. 捲動區域
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
        
        # 2. 底部固定區域
        bottom_area = QWidget()
        bottom_area.setObjectName("BottomArea") 
        bottom_layout = QVBoxLayout(bottom_area)
        bottom_layout.setContentsMargins(20, 15, 20, 15)
        
        root_layout.addWidget(bottom_area)
        
        return page_root, content_layout, bottom_layout

    # --------------------------------------------------------
    # 執行邏輯 (修改點：增加路徑防呆)
    # --------------------------------------------------------

    def run_worker(self, func, **kwargs):
        # 檢查輸入路徑
        if 'input_path' in kwargs and not kwargs['input_path']:
            self.log("⚠️ 錯誤：請先選擇輸入路徑 (Input Path)")
            return
        
        # 檢查輸出路徑 (如果 kwargs 中包含 output_path 鍵值，且值為空)
        if 'output_path' in kwargs and not kwargs['output_path']:
            self.log("⚠️ 錯誤：請先選擇輸出資料夾 (Output Path)")
            return

        self.log("⏳ 準備開始任務...")
        self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log)
        self.worker.start()

    # --------------------------------------------------------
    # 各頁面 UI 與 功能綁定
    # --------------------------------------------------------
    
    def page_scaling_ui(self):
        w, content, bottom = self._create_page_structure()

        grp_path, self.sc_in, self.sc_out = self.create_path_group()
        content.addWidget(grp_path)

        grp_opts = QGroupBox("設定參數")
        form = QFormLayout()
        form.setSpacing(15)
        
        self.sc_ratio = QLineEdit("1.0") 
        self.sc_prefix = QLineEdit()
        self.sc_postfix = QLineEdit("") 
        
        last_author = self.settings.value("author", "")
        self.sc_author = QLineEdit(str(last_author))
        
        self.sc_sharpness = QLineEdit("1.0")
        row_sharp = QHBoxLayout()
        row_sharp.addWidget(self.sc_sharpness)
        row_sharp.addWidget(SelectableLabel("(0.0 ~ 2.0+, 1.0為原始)"))
        
        self.sc_brightness = QLineEdit("1.0")
        row_bright = QHBoxLayout()
        row_bright.addWidget(self.sc_brightness)
        row_bright.addWidget(SelectableLabel("(0.0 ~ 2.0+, 1.0為原始)"))

        form.addRow(SelectableLabel("縮放比例:"), self.sc_ratio)
        form.addRow(SelectableLabel("銳利度:"), row_sharp)
        form.addRow(SelectableLabel("亮度:"), row_bright)
        form.addRow(SelectableLabel("檔名前綴:"), self.sc_prefix)
        form.addRow(SelectableLabel("檔名後綴:"), self.sc_postfix)
        form.addRow(SelectableLabel("作者標記:"), self.sc_author)
        
        grp_opts.setLayout(form)
        content.addWidget(grp_opts)
        
        self.sc_rec = QCheckBox("遞歸處理 (含子資料夾)")
        self.sc_rec.setChecked(True)
        self.sc_jpg = QCheckBox("強制轉 JPG")
        self.sc_jpg.setChecked(True)
        self.sc_low = QCheckBox("副檔名轉小寫")
        self.sc_low.setChecked(True)
        self.sc_del = QCheckBox("轉檔後刪除原始檔")
        self.sc_del.setChecked(True)
        self.sc_crop = QCheckBox("豆包圖裁切 (去除右下角水印)")
        
        chk_layout = QVBoxLayout()
        chk_layout.setSpacing(10)
        chk_layout.addWidget(self.sc_rec)
        chk_layout.addWidget(self.sc_jpg)
        chk_layout.addWidget(self.sc_low)
        chk_layout.addWidget(self.sc_del)
        chk_layout.addWidget(self.sc_crop)
        content.addLayout(chk_layout)
        
        content.addStretch()

        btn = QPushButton("開始執行")
        btn.setObjectName("ExecBtn")
        btn.clicked.connect(self.run_scaling)
        bottom.addWidget(btn)

        return w

    def page_convert_ui(self):
        w, content, bottom = self._create_page_structure()
        grp_path, self.cv_in, _ = self.create_path_group(False)
        content.addWidget(grp_path)
        
        self.cv_rec = QCheckBox("包含子資料夾")
        self.cv_rec.setChecked(True)
        self.cv_del = QCheckBox("轉換後刪除原始 PNG/JPEG")
        self.cv_del.setChecked(True)
        
        content.addWidget(self.cv_rec)
        content.addWidget(self.cv_del)
        content.addStretch()
        
        btn = QPushButton("開始轉檔")
        btn.setObjectName("ExecBtn")
        btn.clicked.connect(self.run_convert)
        bottom.addWidget(btn)
        return w

    def page_resize1920_ui(self):
        w, content, bottom = self._create_page_structure()
        grp_path, self.rs_in, self.rs_out = self.create_path_group()
        content.addWidget(grp_path)
        
        self.rs_rec = QCheckBox("包含子資料夾")
        self.rs_rec.setChecked(True)
        content.addWidget(self.rs_rec)
        content.addStretch()
        
        btn = QPushButton("開始縮小至 1920px")
        btn.setObjectName("ExecBtn")
        btn.clicked.connect(self.run_resize1920)
        bottom.addWidget(btn)
        return w

    def page_rename_ui(self):
        w, content, bottom = self._create_page_structure()
        grp_path, self.rn_in, _ = self.create_path_group(False)
        content.addWidget(grp_path)
        
        form = QFormLayout()
        form.setSpacing(15)
        self.rn_pre = QLineEdit()
        self.rn_post = QLineEdit()
        form.addRow(SelectableLabel("新增前綴:"), self.rn_pre)
        form.addRow(SelectableLabel("新增後綴:"), self.rn_post)
        content.addLayout(form)
        
        self.rn_rec = QCheckBox("包含子資料夾")
        self.rn_rec.setChecked(True)
        content.addWidget(self.rn_rec)
        content.addStretch()
        
        btn = QPushButton("執行重新命名")
        btn.setObjectName("ExecBtn")
        btn.clicked.connect(self.run_rename)
        bottom.addWidget(btn)
        return w

    def page_multi_ui(self):
        w, content, bottom = self._create_page_structure()
        grp_path, self.mt_in, self.mt_out = self.create_path_group()
        content.addWidget(grp_path)
        
        form = QFormLayout()
        form.setSpacing(15)
        self.mt_ori = QComboBox()
        self.mt_ori.addItems(["水平 (以寬度為準)", "垂直 (以高度為準)"])
        form.addRow(SelectableLabel("參考方向:"), self.mt_ori)
        content.addLayout(form)
        
        self.mt_rec = QCheckBox("包含子資料夾")
        self.mt_rec.setChecked(True)
        self.mt_low = QCheckBox("副檔名轉小寫")
        self.mt_low.setChecked(True)
        content.addWidget(self.mt_rec)
        content.addWidget(self.mt_low)
        content.addStretch()
        
        btn = QPushButton("生成多尺寸")
        btn.setObjectName("ExecBtn")
        btn.clicked.connect(self.run_multi)
        bottom.addWidget(btn)
        return w

    # --------------------------------------------------------
    # 執行轉發
    # --------------------------------------------------------

    def run_scaling(self):
        try:
            ratio = float(self.sc_ratio.text())
            sharp = float(self.sc_sharpness.text())
            bright = float(self.sc_brightness.text())
        except ValueError:
            self.log("❌ 錯誤：比例、銳利度或亮度必須是數字")
            return
            
        author = self.sc_author.text()
        self.settings.setValue("author", author)
        
        self.run_worker(
            logic.task_scaling,
            input_path=self.sc_in.text(),
            output_path=self.sc_out.text(),
            scale_ratio=ratio,
            recursive=self.sc_rec.isChecked(),
            convert_jpg=self.sc_jpg.isChecked(),
            lower_ext=self.sc_low.isChecked(),
            delete_original=self.sc_del.isChecked(),
            prefix=self.sc_prefix.text(),
            postfix=self.sc_postfix.text(),
            crop_doubao=self.sc_crop.isChecked(),
            sharpen_factor=sharp,
            brightness_factor=bright,
            author=author
        )

    def run_convert(self):
        self.run_worker(
            logic.task_convert_jpg,
            input_path=self.cv_in.text(),
            recursive=self.cv_rec.isChecked(),
            delete_original=self.cv_del.isChecked()
        )

    def run_resize1920(self):
        self.run_worker(
            logic.task_resize_1920,
            input_path=self.rs_in.text(),
            output_path=self.rs_out.text(),
            recursive=self.rs_rec.isChecked()
        )

    def run_rename(self):
        self.run_worker(
            logic.task_rename,
            input_path=self.rn_in.text(),
            prefix=self.rn_pre.text(),
            postfix=self.rn_post.text(),
            recursive=self.rn_rec.isChecked()
        )

    def run_multi(self):
        self.run_worker(
            logic.task_multi_res,
            input_path=self.mt_in.text(),
            output_path=self.mt_out.text(),
            recursive=self.mt_rec.isChecked(),
            lower_ext=self.mt_low.isChecked(),
            orientation='h' if self.mt_ori.currentIndex() == 0 else 'v'
        )