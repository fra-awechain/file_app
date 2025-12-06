from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame, 
                               QProgressBar, QColorDialog, QDialog, QSpinBox, QDoubleSpinBox, QGridLayout, QSlider)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QTextCursor
from app.workers import Worker
import app.logic as logic
from pathlib import Path

# -----------------------------------------------------------
# 元件：SelectableLabel
# -----------------------------------------------------------
class SelectableLabel(QLabel):
    def __init__(self, text="", parent=None, **kwargs):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.IBeamCursor)
        if 'alignment' in kwargs: self.setAlignment(kwargs['alignment'])
        if 'styleSheet' in kwargs: self.setStyleSheet(kwargs['styleSheet'])
        if 'fixedHeight' in kwargs: self.setFixedHeight(kwargs['fixedHeight'])

# -----------------------------------------------------------
# 元件：DragDropArea
# -----------------------------------------------------------
class DragDropArea(QLabel):
    fileDropped = Signal(str)
    def __init__(self, parent=None):
        super().__init__("拖放至此", parent)
        self.setObjectName("DragDrop")
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls(): e.acceptProposedAction()
    def dropEvent(self, e: QDropEvent):
        u = e.mimeData().urls()
        if u: self.fileDropped.emit(u[0].toLocalFile())

# -----------------------------------------------------------
# 元件：WhiteComboBox
# -----------------------------------------------------------
class WhiteComboBox(QComboBox):
    def __init__(self, parent=None): super().__init__(parent)

# -----------------------------------------------------------
# 元件：SliderInput (滑桿+輸入框)
# -----------------------------------------------------------
class SliderInput(QWidget):
    valueChanged = Signal(float)
    def __init__(self, min_val, max_val, step=0.1, default=1.0, suffix=""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        self.scale = 10 if isinstance(step, float) else 1
        
        self.sl = QSlider(Qt.Horizontal)
        self.sl.setRange(int(min_val*self.scale), int(max_val*self.scale))
        self.sl.setValue(int(default*self.scale))
        
        if isinstance(step, float):
            self.sb = QDoubleSpinBox()
            self.sb.setSingleStep(step)
        else:
            self.sb = QSpinBox()
            self.sb.setSingleStep(int(step))
            
        self.sb.setRange(min_val, max_val)
        self.sb.setValue(default)
        self.sb.setSuffix(suffix)
        self.sb.setFixedWidth(80)
        
        self.sl.valueChanged.connect(self._on_slider_change)
        self.sb.valueChanged.connect(self._on_spin_change)
        
        layout.addWidget(self.sl)
        layout.addWidget(self.sb)
    
    def _on_slider_change(self, v):
        val = v / self.scale
        self.sb.blockSignals(True)
        self.sb.setValue(val)
        self.sb.blockSignals(False)
        self.valueChanged.emit(val)

    def _on_spin_change(self, v):
        val = int(v * self.scale)
        self.sl.blockSignals(True)
        self.sl.setValue(val)
        self.sl.blockSignals(False)
        self.valueChanged.emit(v)

    def value(self): return self.sb.value()

# -----------------------------------------------------------
# 元件：SidebarButton
# -----------------------------------------------------------
class SidebarButton(QFrame):
    clicked = Signal(int)
    def __init__(self, text, icon_char, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(60)
        self.setObjectName("SidebarBtn")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20,0,20,0)
        layout.setSpacing(15)
        
        self.ind = QWidget()
        self.ind.setFixedSize(4,24)
        self.ind.setStyleSheet("background:transparent;border-radius:2px;")
        
        self.ic = QLabel(icon_char)
        self.ic.setStyleSheet("color:#94a3b8;font-size:20px;background:transparent;")
        
        self.txt = QLabel(text)
        self.txt.setObjectName("SidebarBtnText")
        self.txt.setStyleSheet("font-size:16px;background:transparent;")
        
        layout.addWidget(self.ind)
        layout.addWidget(self.ic)
        layout.addWidget(self.txt)
        layout.addStretch()

    def set_selected(self, s):
        if s:
            self.ind.setStyleSheet("background:#38bdf8;")
            self.ic.setStyleSheet("color:#38bdf8;font-size:20px;background:transparent;")
            self.txt.setStyleSheet("color:white;font-weight:bold;font-size:16px;background:transparent;")
            self.setStyleSheet("background:#334155;border-radius:8px;")
        else:
            self.ind.setStyleSheet("background:transparent;")
            self.ic.setStyleSheet("color:#94a3b8;font-size:20px;background:transparent;")
            self.txt.setStyleSheet("color:#cbd5e1;font-weight:normal;font-size:16px;background:transparent;")
            self.setStyleSheet("background:transparent;")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self.index)

# -----------------------------------------------------------
# 元件：ImageEditorDialog
# -----------------------------------------------------------
class ImageEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("圖片編輯器")
        self.resize(500, 400)
        layout = QVBoxLayout(self)
        self.path = ""
        
        top = QHBoxLayout()
        btn_load = QPushButton("選擇圖片")
        btn_load.clicked.connect(self.load_img)
        self.dd = DragDropArea()
        self.dd.fileDropped.connect(self.load_img_path)
        top.addWidget(btn_load)
        top.addWidget(self.dd)
        layout.addLayout(top)
        
        self.preview = QLabel("預覽")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("border:1px dashed #999;")
        self.preview.setMinimumHeight(200)
        layout.addWidget(self.preview)
        
        ctrl = QFormLayout()
        self.sl_s = SliderInput(10, 200, 1, 100, "%")
        ctrl.addRow(SelectableLabel("縮放:"), self.sl_s)
        self.sl_r = SliderInput(0, 360, 1, 0, "°")
        ctrl.addRow(SelectableLabel("旋轉:"), self.sl_r)
        self.sl_x = SliderInput(-500, 500, 1, 0, "px")
        ctrl.addRow(SelectableLabel("X 位移:"), self.sl_x)
        self.sl_y = SliderInput(-500, 500, 1, 0, "px")
        ctrl.addRow(SelectableLabel("Y 位移:"), self.sl_y)
        layout.addLayout(ctrl)
        
        btn = QPushButton("確定")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def load_img(self):
        f, _ = QFileDialog.getOpenFileName(self)
        if f: self.load_img_path(f)

    def load_img_path(self, f):
        self.path = f
        self.preview.setText(f"已載入: {Path(f).name}")

# -----------------------------------------------------------
# 元件：RegionControl (填色區塊)
# -----------------------------------------------------------
class RegionControl(QGroupBox):
    def __init__(self, title, has_target_select=False, parent=None):
        super().__init__(title, parent)
        self.has_target = has_target_select
        self.sets = {'target_color':'#FFFFFF', 'fill_color':'#FFFFFF', 'fill_gradient':{}, 'fill_image_path':''}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        if self.has_target:
            layout.addWidget(SelectableLabel("目標區塊:"))
            self.cb_t = WhiteComboBox()
            base = self.title().replace('區塊','')
            self.cb_t.addItems([f"全部{base}", "指定色值", "非指定色值"])
            self.cb_t.currentIndexChanged.connect(lambda i: self.w_tc.setVisible(i>0))
            layout.addWidget(self.cb_t)
            
            self.w_tc = QWidget()
            lt = QHBoxLayout(self.w_tc)
            lt.setContentsMargins(0,0,0,0)
            self.edt_tc = QLineEdit("#FFFFFF")
            b = QPushButton("選")
            b.setFixedWidth(30)
            b.clicked.connect(lambda: self.pick(self.edt_tc))
            lt.addWidget(SelectableLabel("色值:"))
            lt.addWidget(self.edt_tc)
            lt.addWidget(b)
            layout.addWidget(self.w_tc)
            self.w_tc.hide()

        layout.addWidget(SelectableLabel("透明度:"))
        self.cb_tr = WhiteComboBox()
        self.cb_tr.addItems(["維持", "改變"])
        self.cb_tr.currentIndexChanged.connect(lambda i: self.w_tr.setVisible(i==1))
        layout.addWidget(self.cb_tr)
        
        self.w_tr = QWidget()
        lr = QHBoxLayout(self.w_tr)
        lr.setContentsMargins(0,0,0,0)
        self.sl_tr = SliderInput(0, 100, 1, 100, "%")
        lr.addWidget(self.sl_tr)
        layout.addWidget(self.w_tr)
        self.w_tr.hide()

        layout.addWidget(SelectableLabel("填充內容:"))
        self.cb_c = WhiteComboBox()
        self.cb_c.addItems(["維持", "填充顏色", "填充漸層", "填充圖片"])
        self.cb_c.currentIndexChanged.connect(lambda i: self.st_c.setCurrentIndex(i))
        layout.addWidget(self.cb_c)
        
        self.st_c = QStackedWidget()
        self.st_c.addWidget(QWidget()) # Index 0: Maintain
        
        # Color
        pc = QWidget()
        lc = QHBoxLayout(pc)
        lc.setContentsMargins(0,0,0,0)
        self.edt_fc = QLineEdit("#FFFFFF")
        bfc = QPushButton("選")
        bfc.setFixedWidth(30)
        bfc.clicked.connect(lambda: self.pick(self.edt_fc))
        lc.addWidget(SelectableLabel("色值:"))
        lc.addWidget(self.edt_fc)
        lc.addWidget(bfc)
        self.st_c.addWidget(pc)

        # Gradient
        pg = QWidget()
        lg = QVBoxLayout(pg)
        lg.setContentsMargins(0,0,0,0)
        self.sl_ga = SliderInput(0, 360, 1, 0, "°")
        lg.addWidget(SelectableLabel("角度:"))
        lg.addWidget(self.sl_ga)
        lgs = QHBoxLayout()
        self.edt_gs = QLineEdit("#000000")
        self.edt_ge = QLineEdit("#FFFFFF")
        bgs = QPushButton("起")
        bgs.clicked.connect(lambda: self.pick(self.edt_gs))
        bge = QPushButton("結")
        bge.clicked.connect(lambda: self.pick(self.edt_ge))
        lgs.addWidget(bgs)
        lgs.addWidget(self.edt_gs)
        lgs.addWidget(bge)
        lgs.addWidget(self.edt_ge)
        lg.addLayout(lgs)
        self.st_c.addWidget(pg)
        
        # Image
        pi = QWidget()
        li = QVBoxLayout(pi)
        btn_img = QPushButton("選擇圖片")
        btn_img.clicked.connect(self.pk_img)
        li.addWidget(btn_img)
        self.st_c.addWidget(pi)
        
        layout.addWidget(self.st_c)
        layout.addStretch()

    def pick(self, edt):
        c = QColorDialog.getColor()
        if c.isValid():
            edt.setText(c.name().upper())

    def pk_img(self):
        f, _ = QFileDialog.getOpenFileName(self, "選圖")
        if f:
            self.sets['fill_image_path'] = f

    def get_settings(self):
        target_mode = 'all'
        if self.has_target:
            idx = self.cb_t.currentIndex()
            if idx == 1: target_mode = 'specific'
            elif idx == 2: target_mode = 'non_specific'
        
        g_conf = {'start':self.edt_gs.text(), 'end':self.edt_ge.text(), 'angle':self.sl_ga.value()}
        
        return {
            'target_mode': target_mode, 
            'target_color': self.edt_tc.text(), 
            'trans_mode': 'change' if self.cb_tr.currentIndex()==1 else 'maintain',
            'trans_val': self.sl_tr.value(), 
            'fill_mode': ['maintain','color','gradient','image'][self.cb_c.currentIndex()],
            'fill_color': self.edt_fc.text(), 
            'fill_gradient': g_conf,
            'fill_image_path': self.sets['fill_image_path']
        }

# -----------------------------------------------------------
# 主視窗
# -----------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self): 
        super().__init__() 
        self.setWindowTitle("Python Media Batch Processor")
        self.resize(1400, 950)
        self.settings = QSettings("MediaBatcher", "AppConfig")
        self.bg_sets = {} # Initialize dictionary for background settings
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        ml = QHBoxLayout(central)
        ml.setContentsMargins(0,0,0,0)
        ml.setSpacing(0)
        
        # 側邊欄
        self.sb = QWidget()
        self.sb.setFixedWidth(260)
        self.sb.setObjectName("SidebarFrame")
        sl = QVBoxLayout(self.sb)
        sl.setContentsMargins(0,30,0,20)
        sl.setSpacing(8)
        
        lbl_title = SelectableLabel("Media Batcher", parent=self.sb)
        lbl_title.setStyleSheet("color:#38bdf8;font-size:24px;font-weight:bold;margin-left:20px;")
        sl.addWidget(lbl_title)
        
        self.btns = []
        items = [("修改檔名","📝",0), ("圖片處理","🖼️",1), ("智慧填色","🎨",2), ("影片銳利化","🎥",3), ("Icon 生成","📦",4)]
        for t, i, idx in items:
            b = SidebarButton(t, i, idx, self.sb)
            b.clicked.connect(self.switch_page)
            sl.addWidget(b)
            self.btns.append(b)
        
        sl.addStretch()
        ml.addWidget(self.sb)
        
        # 右側面板
        right = QWidget()
        right.setObjectName("RightFrame")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0,0,0,0)
        
        self.header = SelectableLabel("功能")
        self.header.setFixedHeight(60)
        self.header.setStyleSheet("background:white;padding-left:30px;font-size:24px;font-weight:bold;")
        rl.addWidget(self.header)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_rename_ui())  # 0
        self.stack.addWidget(self.page_scaling_ui()) # 1
        self.stack.addWidget(self.page_fill_ui())    # 2
        self.stack.addWidget(self.page_video_ui())   # 3
        self.stack.addWidget(self.page_multi_ui())   # 4
        rl.addWidget(self.stack, 1)

        # 底部狀態列 & Log
        stat_bar = QWidget()
        stat_bar.setObjectName("StatusBar")
        sl = QHBoxLayout(stat_bar)
        sl.setContentsMargins(20,10,20,10)
        
        v_info = QVBoxLayout()
        h_inf = QHBoxLayout()
        self.lbl_cur = SelectableLabel("準備就緒")
        h_inf.addWidget(self.lbl_cur)
        h_inf.addStretch()
        
        self.pb_file = QProgressBar()
        self.pb_file.setObjectName("FileProgress")
        self.pb_file.setFixedWidth(200)
        self.pb_file.setRange(0,100)
        
        self.lbl_pct = SelectableLabel("0%")
        h_inf.addWidget(self.pb_file)
        h_inf.addWidget(self.lbl_pct)
        v_info.addLayout(h_inf)
        sl.addLayout(v_info)
        
        # Console + Clear Button
        con_area = QHBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(80)
        # [修正 3] 樣式改為白字黑底
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #f0f0f0; border:1px solid #555; font-family: Consolas;")
        
        btn_cls = QPushButton("清除 Log")
        btn_cls.setObjectName("ClearLogBtn")
        btn_cls.setCursor(Qt.PointingHandCursor)
        btn_cls.clicked.connect(self.log_area.clear)
        
        con_area.addWidget(self.log_area, 1)
        con_area.addWidget(btn_cls)
        v_info.addLayout(con_area)
        
        rl.addWidget(stat_bar)
        ml.addWidget(right)
        self.switch_page(0)

    def switch_page(self, idx): 
        self.stack.setCurrentIndex(idx)
        for b in self.btns:
            b.set_selected(b.index == idx)
        self.header.setText(["修改檔名","圖片處理","智慧填色","影片銳利化","Icon 生成"][idx])

    def _create_scroll(self, click_func):
        wrapper = QWidget()
        wl = QVBoxLayout(wrapper)
        wl.setContentsMargins(0,0,0,0)
        
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        ct = QWidget()
        ct.setObjectName("ScrollContent")
        self.cl = QVBoxLayout(ct)
        self.cl.setContentsMargins(40,30,40,30)
        self.cl.setSpacing(20)
        sc.setWidget(ct)
        wl.addWidget(sc, 1)
        
        # 固定底部區塊
        bot = QWidget()
        bot.setStyleSheet("background:#e6e6e6;border-top:none;")
        bl = QHBoxLayout(bot)
        bl.setContentsMargins(40,15,40,15)
        
        btn = QPushButton("開始執行")
        btn.setObjectName("ExecBtn")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(click_func)
        
        pb = QProgressBar()
        pb.setObjectName("TotalProgress")
        pb.setRange(0,100)
        
        bl.addWidget(btn)
        bl.addSpacing(20)
        bl.addWidget(SelectableLabel("總進度:"))
        bl.addWidget(pb)
        
        wl.addWidget(bot)
        return wrapper, self.cl, pb

    def create_path_group(self, with_output=True):
        g = QGroupBox("路徑")
        l = QFormLayout()
        
        ri = QHBoxLayout()
        ei = QLineEdit()
        bd = QPushButton("資料夾")
        bf = QPushButton("檔案")
        dd = DragDropArea()
        
        bd.clicked.connect(lambda: self.select_folder(ei))
        bf.clicked.connect(lambda: self.select_file(ei))
        dd.fileDropped.connect(ei.setText)
        
        ri.addWidget(ei)
        ri.addWidget(bd)
        ri.addWidget(bf)
        ri.addWidget(dd)
        l.addRow(SelectableLabel("輸入:"), ri)
        
        eo = None
        if with_output:
            ro = QHBoxLayout()
            eo = QLineEdit()
            bo = QPushButton("資料夾")
            do = DragDropArea()
            
            bo.clicked.connect(lambda: self.select_folder(eo))
            do.fileDropped.connect(eo.setText)
            
            ro.addWidget(eo)
            ro.addWidget(bo)
            ro.addWidget(do)
            l.addRow(SelectableLabel("輸出:"), ro)
            
        g.setLayout(l)
        return g, ei, eo

    def select_folder(self, line_edit):
        d = QFileDialog.getExistingDirectory(self, "選擇資料夾")
        if d: line_edit.setText(d)

    def select_file(self, line_edit):
        f, _ = QFileDialog.getOpenFileName(self, "選擇檔案")
        if f: line_edit.setText(f)

    # [修正 4] Log 倒序顯示：插入最上方
    def log(self, msg):
        from datetime import datetime
        t = datetime.now().strftime("%H:%M:%S")
        txt = f"[{t}] {msg}\n"
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.Start)
        cursor.insertText(txt)
        self.log_area.setTextCursor(cursor)

    # ------------------ Page 1: Rename ------------------
    def page_rename_ui(self):
        p, l, self.rn_pb = self._create_scroll(self.run_rename)
        gp, self.rn_i, _ = self.create_path_group(False)
        l.addWidget(gp)
        
        gr = QGroupBox("規則")
        lr = QFormLayout(gr)
        self.ck_rp = QCheckBox("改前綴")
        self.p1 = QLineEdit()
        self.p2 = QLineEdit()
        rp = QHBoxLayout()
        rp.addWidget(self.p1)
        rp.addWidget(SelectableLabel("->"))
        rp.addWidget(self.p2)
        
        self.ck_rs = QCheckBox("改後綴")
        self.s1 = QLineEdit()
        self.s2 = QLineEdit()
        rs = QHBoxLayout()
        rs.addWidget(self.s1)
        rs.addWidget(SelectableLabel("->"))
        rs.addWidget(self.s2)
        
        lr.addRow(self.ck_rp, rp)
        lr.addRow(self.ck_rs, rs)
        l.addWidget(gr)
        
        gm = QGroupBox("Meta (隱藏資訊)")
        lm = QFormLayout(gm)
        self.rn_rm = QCheckBox("移除 Meta(隱藏資訊)")
        lm.addRow(self.rn_rm)
        self.rn_au = QLineEdit(self.settings.value("rn_au",""))
        self.rn_de = QLineEdit()
        lm.addRow(SelectableLabel("作者:"), self.rn_au)
        lm.addRow(SelectableLabel("描述:"), self.rn_de)
        l.addWidget(gm)
        
        self.rn_rec = QCheckBox("含子資料夾")
        self.rn_rec.setChecked(True)
        l.addWidget(self.rn_rec)
        l.addStretch()
        return p

    def run_rename(self):
        self.settings.setValue("rn_au", self.rn_au.text())
        self.run_worker(logic.task_rename_replace, self.rn_pb, input_path=self.rn_i.text(), recursive=self.rn_rec.isChecked(), 
                        do_prefix=self.ck_rp.isChecked(), old_prefix=self.p1.text(), new_prefix=self.p2.text(),
                        do_suffix=self.ck_rs.isChecked(), old_suffix=self.s1.text(), new_suffix=self.s2.text(),
                        remove_metadata=self.rn_rm.isChecked(), author=self.rn_au.text(), description=self.rn_de.text())

    # ------------------ Page 2: Scaling ------------------
    def page_scaling_ui(self):
        p,l,self.sc_pb = self._create_scroll(self.run_scaling)
        gp, self.sc_i, self.sc_o = self.create_path_group()
        l.addWidget(gp)
        
        go = QGroupBox("參數")
        lo = QFormLayout(go)
        self.sc_mode = WhiteComboBox()
        self.sc_mode.addItems(["維持", "Ratio", "Fixed Width", "Fixed Height"])
        self.sc_v1 = QLineEdit("1.0")
        lo.addRow(SelectableLabel("模式:"), self.sc_mode)
        lo.addRow(SelectableLabel("數值:"), self.sc_v1)
        
        self.sc_sh = SliderInput(0, 5, 0.1, 1.0)
        lo.addRow(SelectableLabel("銳利度:"), self.sc_sh)
        self.sc_br = SliderInput(0, 5, 0.1, 1.0)
        lo.addRow(SelectableLabel("亮度:"), self.sc_br)
        
        self.sc_pre = QLineEdit()
        self.sc_post = QLineEdit()
        lo.addRow(SelectableLabel("前綴:"), self.sc_pre)
        lo.addRow(SelectableLabel("後綴:"), self.sc_post)
        l.addWidget(go)
        
        gc = QGroupBox("選項")
        lc = QGridLayout(gc)
        self.sc_rec = QCheckBox("含子資料夾")
        self.sc_rec.setChecked(True)
        self.sc_jpg = QCheckBox("轉JPG")
        self.sc_jpg.setChecked(True)
        self.sc_low = QCheckBox("小寫副檔名")
        self.sc_low.setChecked(True)
        self.sc_del = QCheckBox("刪除原始")
        self.sc_crop = QCheckBox("豆包裁切")
        self.sc_meta = QCheckBox("移除 Meta(隱藏資訊)")
        self.sc_au = QLineEdit(self.settings.value("sc_au",""))
        self.sc_de = QLineEdit()
        
        lc.addWidget(self.sc_rec,0,0)
        lc.addWidget(self.sc_jpg,0,1)
        lc.addWidget(self.sc_low,0,2)
        lc.addWidget(self.sc_del,1,0)
        lc.addWidget(self.sc_crop,1,1)
        lc.addWidget(self.sc_meta,1,2)
        lo.addRow(SelectableLabel("作者:"), self.sc_au)
        lo.addRow(SelectableLabel("描述:"), self.sc_de)
        l.addWidget(gc)
        l.addStretch()
        return p

    def run_scaling(self):
        self.settings.setValue("sc_au", self.sc_au.text())
        self.run_worker(logic.task_scaling, self.sc_pb, input_path=self.sc_i.text(), output_path=self.sc_o.text(),
                        mode=['none','ratio','width','height'][self.sc_mode.currentIndex()], mode_value_1=float(self.sc_v1.text() or 0),
                        recursive=self.sc_rec.isChecked(), convert_jpg=self.sc_jpg.isChecked(), lower_ext=self.sc_low.isChecked(),
                        delete_original=self.sc_del.isChecked(), prefix=self.sc_pre.text(), postfix=self.sc_post.text(),
                        crop_doubao=self.sc_crop.isChecked(), sharpen_factor=self.sc_sh.value(), brightness_factor=self.sc_br.value(),
                        remove_metadata=self.sc_meta.isChecked(), author=self.sc_au.text(), description=self.sc_de.text())

    # ------------------ Page 3: Smart Fill ------------------
    def page_fill_ui(self):
        p,l,self.fill_pb = self._create_scroll(self.run_fill)
        gp, self.fi, self.fo = self.create_path_group()
        l.addWidget(gp)
        
        rr = QHBoxLayout()
        self.rop = RegionControl("不透明區塊", True)
        self.rtr = RegionControl("透明區塊")
        self.rse = RegionControl("半透明區塊", True)
        rr.addWidget(self.rop)
        rr.addWidget(self.rtr)
        rr.addWidget(self.rse)
        l.insertLayout(1, rr)
        
        # 背景與裁切
        adv = QHBoxLayout()
        gb = QGroupBox("背景設定")
        lb = QFormLayout(gb)
        self.bg_mode = WhiteComboBox()
        self.bg_mode.addItems(["疊加", "鏤空背景"])
        self.bg_mat = WhiteComboBox()
        self.bg_mat.addItems(["色塊", "漸層", "圖片"])
        
        self.bg_st = QStackedWidget()
        
        p1 = QWidget()
        l1 = QHBoxLayout(p1)
        self.bg_c = QLineEdit("#FFF")
        b1 = QPushButton("選")
        b1.clicked.connect(lambda: self.pick(self.bg_c))
        l1.addWidget(self.bg_c)
        l1.addWidget(b1)
        self.bg_st.addWidget(p1)
        
        p2 = QWidget()
        l2 = QVBoxLayout(p2)
        self.bg_ga = SliderInput(0,360,1,0,"°")
        self.bg_gs = QLineEdit("#000")
        self.bg_ge = QLineEdit("#FFF")
        b2 = QPushButton("起")
        b2.clicked.connect(lambda:self.pick(self.bg_gs))
        b3 = QPushButton("結")
        b3.clicked.connect(lambda:self.pick(self.bg_ge))
        h2 = QHBoxLayout()
        h2.addWidget(b2)
        h2.addWidget(self.bg_gs)
        h2.addWidget(b3)
        h2.addWidget(self.bg_ge)
        l2.addWidget(self.bg_ga)
        l2.addLayout(h2)
        self.bg_st.addWidget(p2)
        
        p3 = QWidget()
        l3 = QVBoxLayout(p3)
        b4 = QPushButton("設定圖片")
        b4.clicked.connect(self.set_bg_img)
        l3.addWidget(b4)
        self.bg_st.addWidget(p3)
        
        self.bg_mat.currentIndexChanged.connect(self.bg_st.setCurrentIndex)
        
        self.bg_cut = WhiteComboBox()
        self.bg_cut.addItems(["不透明像素", "透明像素", "指定色值"])
        self.bg_cc = QLineEdit("#FFF")
        b5 = QPushButton("選")
        b5.clicked.connect(lambda:self.pick(self.bg_cc))
        h5 = QHBoxLayout()
        h5.addWidget(self.bg_cut)
        h5.addWidget(self.bg_cc)
        h5.addWidget(b5)
        
        lb.addRow(SelectableLabel("模式:"), self.bg_mode)
        lb.addRow(SelectableLabel("素材:"), self.bg_mat)
        lb.addRow(SelectableLabel("設定:"), self.bg_st)
        lb.addRow(SelectableLabel("鏤空:"), h5)
        
        adv.addWidget(gb, 1)
        
        gc = QGroupBox("裁切設定")
        lc = QVBoxLayout(gc)
        self.ck_shp = QCheckBox("形狀裁切")
        self.cb_shp = WhiteComboBox()
        self.cb_shp.hide()
        self.ck_shp.toggled.connect(self.cb_shp.setVisible)
        self.cb_shp.addItems(["圓形","正方形","正三角形","正五邊形","正六邊形","四角星形(圓角)","四角星形(尖角)","五角星形(圓角)","五角星形(尖角)","隨機雲狀(正圓內)","隨機雲狀"])
        self.ck_trim = QCheckBox("貼合尺寸裁切")
        self.ck_trim.setObjectName("PinkCheck")
        lc.addWidget(self.ck_shp)
        lc.addWidget(self.cb_shp)
        lc.addWidget(self.ck_trim)
        lc.addStretch()
        adv.addWidget(gc, 1)
        l.insertLayout(2, adv)
        
        # 輸出設定與預覽
        out_row = QHBoxLayout()
        gout = QGroupBox("輸出設定")
        lout = QVBoxLayout(gout)
        self.fi_fmt = WhiteComboBox()
        self.fi_fmt.addItems(["png","jpg"])
        lout.addWidget(SelectableLabel("格式:"))
        lout.addWidget(self.fi_fmt)
        
        self.fill_rec = QCheckBox("含子資料夾")
        lout.addWidget(self.fill_rec)
        
        self.fill_del = QCheckBox("刪除原始")
        lout.addWidget(self.fill_del)
        
        out_row.addWidget(gout, 1)
        prev = QLabel("預覽區塊")
        prev.setAlignment(Qt.AlignCenter)
        prev.setStyleSheet("border:2px dashed #999;background:#eee;min-height:100px;")
        out_row.addWidget(prev, 1)
        l.insertLayout(3, out_row)
        
        return p

    def set_bg_img(self):
        d = ImageEditorDialog(self)
        if d.exec():
            self.bg_sets['image_path'] = d.path

    def pick(self, e):
        c = QColorDialog.getColor()
        if c.isValid():
            e.setText(c.name())

    def run_fill(self):
        bg = {
            'enabled': True, 
            'mode': ['overlay','cutout'][self.bg_mode.currentIndex()], 
            'material_type': ['color','gradient','image'][self.bg_mat.currentIndex()],
            'color': self.bg_c.text(), 
            'gradient': {'start':self.bg_gs.text(),'end':self.bg_ge.text(),'angle':self.bg_ga.value()},
            'image_path': self.bg_sets.get('image_path',''), 
            'cutout_target': ['opaque','transparent','color'][self.bg_cut.currentIndex()], 
            'cutout_color': self.bg_cc.text()
        }
        crop = {'shape': self.cb_shp.currentText() if self.ck_shp.isChecked() else '無', 'trim': self.ck_trim.isChecked()}
        
        self.run_worker(logic.task_image_fill, self.fill_pb, input_path=self.fi.text(), output_path=self.fo.text(), 
                        recursive=self.fill_rec.isChecked(),
                        settings_opaque=self.rop.get_settings(), 
                        settings_trans=self.rtr.get_settings(), 
                        settings_semi=self.rse.get_settings(),
                        bg_settings=bg, crop_settings=crop, delete_original=self.fill_del.isChecked(), 
                        output_format=self.fi_fmt.currentText())

    # ------------------ Page 4: Video ------------------
    def page_video_ui(self):
        p,l,self.vd_pb = self._create_scroll(self.run_video)
        gp, self.vi, self.vo = self.create_path_group()
        l.addWidget(gp)
        
        gs = QGroupBox("參數")
        ls = QFormLayout(gs)
        self.vd_ls = SliderInput(3, 13, 2, 7)
        ls.addRow(SelectableLabel("Luma Size (3-13):"), self.vd_ls)
        self.vd_la = SliderInput(0, 5, 0.1, 1.0)
        ls.addRow(SelectableLabel("Luma Amount:"), self.vd_la)
        self.vd_pre = QLineEdit()
        self.vd_post = QLineEdit()
        ls.addRow(SelectableLabel("前綴:"), self.vd_pre)
        ls.addRow(SelectableLabel("後綴:"), self.vd_post)
        l.addWidget(gs)
        
        gr = QGroupBox("輸出")
        lr = QFormLayout(gr)
        self.vd_sm = WhiteComboBox()
        self.vd_sm.addItems(["None","1080p","720p","Ratio"])
        self.vd_sv = SliderInput(0.1, 5.0, 0.1, 1.0)
        lr.addRow(SelectableLabel("縮放模式:"), self.vd_sm)
        lr.addRow(SelectableLabel("比例 (Ratio):"), self.vd_sv)
        l.addWidget(gr)
        
        gc = QGroupBox("選項")
        lc = QGridLayout(gc)
        self.vd_rec = QCheckBox("含子資料夾")
        self.vd_rec.setChecked(True)
        self.vd_mp4 = QCheckBox("轉MP4")
        self.vd_mp4.setChecked(True)
        self.vd_low = QCheckBox("小寫")
        self.vd_low.setChecked(True)
        self.vd_del = QCheckBox("刪除原始")
        self.vd_meta = QCheckBox("移除 Meta(隱藏資訊)")
        self.vd_au = QLineEdit(self.settings.value("vd_au",""))
        self.vd_de = QLineEdit()
        
        lc.addWidget(self.vd_rec,0,0)
        lc.addWidget(self.vd_mp4,0,1)
        lc.addWidget(self.vd_low,0,2)
        lc.addWidget(self.vd_del,1,0)
        lc.addWidget(self.vd_meta,1,1)
        lr.addRow(SelectableLabel("作者:"), self.vd_au)
        lr.addRow(SelectableLabel("描述:"), self.vd_de)
        l.addWidget(gc)
        l.addStretch()
        return p
    
    def run_video(self):
        self.settings.setValue("vd_au", self.vd_au.text())
        sm = ['none','hd1080','hd720','ratio'][self.vd_sm.currentIndex()]
        self.run_worker(logic.task_video_sharpen, self.vd_pb, input_path=self.vi.text(), output_path=self.vo.text(), recursive=self.vd_rec.isChecked(),
                        lower_ext=self.vd_low.isChecked(), delete_original=self.vd_del.isChecked(), prefix=self.vd_pre.text(), postfix=self.vd_post.text(),
                        luma_m_size=int(self.vd_ls.value()), luma_amount=self.vd_la.value(), scale_mode=sm, scale_value=self.vd_sv.value(),
                        convert_h264=self.vd_mp4.isChecked(), remove_metadata=self.vd_meta.isChecked(), author=self.vd_au.text(), description=self.vd_de.text())

    # ------------------ Page 5: Icon ------------------
    def page_multi_ui(self):
        p,l,self.mt_pb = self._create_scroll(self.run_multi)
        gp, self.mi, self.mo = self.create_path_group()
        l.addWidget(gp)
        opt = QGroupBox("設定")
        lo = QFormLayout(opt)
        self.mt_ori = WhiteComboBox()
        self.mt_ori.addItems(["水平","垂直"])
        lo.addRow(SelectableLabel("基準:"), self.mt_ori)
        l.addWidget(opt)
        self.mt_rec = QCheckBox("含子資料夾")
        self.mt_rec.setChecked(True)
        l.addWidget(self.mt_rec)
        l.addStretch()
        return p

    def run_multi(self):
        self.run_worker(logic.task_multi_res, self.mt_pb, input_path=self.mi.text(), output_path=self.mo.text(), recursive=self.mt_rec.isChecked(), lower_ext=True, orientation='h' if self.mt_ori.currentIndex()==0 else 'v')

    # ------------------ Worker Helper ------------------
    def run_worker(self, func, pb, **kwargs):
        if not kwargs.get('input_path'):
            self.log("❌ 路徑未設定")
            return
        self.active_pb = pb
        self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log) # 這裡連接到已經修正的倒序 log 函式
        self.worker.progress_signal.connect(pb.setValue)
        self.worker.current_file_signal.connect(lambda s: self.lbl_cur.setText(f"處理中: {s}"))
        self.worker.file_progress_signal.connect(lambda v: (self.pb_file.setValue(v), self.lbl_pct.setText(f"{v}%")))
        self.worker.finished_signal.connect(lambda: self.log("✅ 完成"))
        self.worker.start()