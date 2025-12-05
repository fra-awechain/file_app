from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame, 
                               QMessageBox, QProgressBar, QColorDialog, QSlider, QSpinBox,
                               QDialog, QSizePolicy, QGridLayout)
from PySide6.QtCore import Qt, QSettings, Signal, QSize, QPoint
from PySide6.QtGui import QTextCursor, QPixmap, QImage, QColor, QCursor, QIcon, QDragEnterEvent, QDropEvent, QPainter, QTransform

from app.workers import Worker
import app.logic as logic
import app.utils as utils

# -----------------------------------------------------------
# UI Components
# -----------------------------------------------------------
class SelectableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.IBeamCursor)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setStyleSheet("color: #333; font-size: 16px;")

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

class WhiteComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QComboBox { background: white; color: #333; border: 1px solid #888; padding: 5px; border-radius: 4px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: white; color: #333; selection-background-color: #3b82f6; selection-color: white; }
        """)
    def showPopup(self):
        w = self.width(); fm = self.fontMetrics(); mw = 0
        for i in range(self.count()): mw = max(mw, fm.horizontalAdvance(self.itemText(i)) + 40)
        self.view().setFixedWidth(max(w, mw))
        super().showPopup()

class SidebarButton(QFrame):
    clicked = Signal(int)
    def __init__(self, text, icon_char, index, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarBtn"); self.index = index; self.setCursor(Qt.PointingHandCursor); self.setMinimumHeight(60)
        l = QHBoxLayout(self); l.setContentsMargins(20,0,20,0); l.setSpacing(15)
        self.ind = QWidget(); self.ind.setFixedSize(4,24); self.ind.setStyleSheet("background:transparent;border-radius:2px;")
        self.ic = QLabel(icon_char); self.ic.setStyleSheet("color:#94a3b8;font-size:20px;background:transparent;")
        self.txt = QLabel(text); self.txt.setObjectName("SidebarBtnText"); self.txt.setStyleSheet("font-size:16px;background:transparent;")
        l.addWidget(self.ind); l.addWidget(self.ic); l.addWidget(self.txt); l.addStretch()
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
        if e.button() == Qt.LeftButton: self.clicked.emit(self.index)

# -----------------------------------------------------------
# Dialogs & RegionControl
# -----------------------------------------------------------
class GradientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("漸層設定"); self.resize(300, 250); self.data = {'start':'#000', 'end':'#FFF', 'dir':'水平', 'angle':0}
        self.init_ui()
    def init_ui(self):
        l = QVBoxLayout(self); self.setStyleSheet("background:#f0f0f0;color:#333;")
        r1=QHBoxLayout(); self.bs=QPushButton(); self.bs.setFixedSize(30,30); self.bs.clicked.connect(lambda:self.pk(1))
        r1.addWidget(SelectableLabel("起始:")); r1.addWidget(self.bs); r1.addStretch(); l.addLayout(r1)
        r2=QHBoxLayout(); self.be=QPushButton(); self.be.setFixedSize(30,30); self.be.clicked.connect(lambda:self.pk(0))
        r2.addWidget(SelectableLabel("結束:")); r2.addWidget(self.be); r2.addStretch(); l.addLayout(r2)
        r3=QHBoxLayout(); self.cb=WhiteComboBox(); self.cb.addItems(["水平","垂直","角度"]); self.cb.currentTextChanged.connect(self.od)
        r3.addWidget(SelectableLabel("方向:")); r3.addWidget(self.cb); l.addLayout(r3)
        self.wa=QWidget(); la=QHBoxLayout(self.wa); la.setContentsMargins(0,0,0,0); self.sp=QSpinBox(); self.sp.setRange(0,360)
        la.addWidget(SelectableLabel("角度:")); la.addWidget(self.sp); l.addWidget(self.wa); self.wa.hide()
        bs=QHBoxLayout(); ok=QPushButton("確定"); ok.clicked.connect(self.accept); bs.addStretch(); bs.addWidget(ok); l.addLayout(bs)
        self.pk(1, init=True); self.pk(0, init=True)
    def pk(self, s, init=False):
        if init: h = self.data['start'] if s else self.data['end']
        else:
            c = QColorDialog.getColor(QColor(self.data['start'] if s else self.data['end']), self)
            if not c.isValid(): return
            h = c.name()
        if s: self.data['start']=h; self.bs.setStyleSheet(f"background:{h};border:1px solid #888")
        else: self.data['end']=h; self.be.setStyleSheet(f"background:{h};border:1px solid #888")
    def od(self, t): self.data['dir']=t; self.wa.setVisible(t=="角度")
    def get_data(self): self.data['angle']=self.sp.value(); return self.data

class ImageEditorDialog(QDialog): 
    def __init__(self, parent=None): super().__init__(parent); self.resize(500,600); self.path=None; self.data={}; self.init_ui()
    def init_ui(self):
        l=QVBoxLayout(self); self.setStyleSheet("background:#f0f0f0;color:#333;")
        h=QHBoxLayout(); self.lb=SelectableLabel("未選"); b=QPushButton("瀏覽"); b.clicked.connect(self.ld); h.addWidget(self.lb,1); h.addWidget(b); l.addLayout(h)
        l.addWidget(QLabel("預覽功能略 (請保留完整版代碼)"), 1)
        bs=QHBoxLayout(); ok=QPushButton("確定"); ok.clicked.connect(self.accept); bs.addStretch(); bs.addWidget(ok); l.addLayout(bs)
    def ld(self): 
        f,_=QFileDialog.getOpenFileName(self,"選圖","","Img (*.png *.jpg)"); 
        if f: self.path=f; self.lb.setText(Path(f).name)

class RegionControl(QGroupBox):
    settings_changed = Signal()
    def __init__(self, title, has_target_select=False, parent=None):
        super().__init__(title, parent)
        self.has_target = has_target_select
        self.sets = {'target_color':'#FFFFFF', 'fill_color':'#FFFFFF', 'fill_gradient':{}, 'fill_image_path':'', 'fill_image_transform':{}}
        self.init_ui()

    def init_ui(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(10, 20, 10, 30) 
        l.setSpacing(12)

        if self.has_target:
            l.addWidget(SelectableLabel("目標區塊:"))
            self.cb_t = WhiteComboBox(); base = self.title().replace("區塊","")
            self.cb_t.addItems([f"全部{base}", "指定色值", "非指定色值"])
            self.cb_t.currentIndexChanged.connect(self.tog_t); self.cb_t.currentIndexChanged.connect(self.settings_changed.emit)
            l.addWidget(self.cb_t)
            
            self.w_tc = QWidget(); lt = QHBoxLayout(self.w_tc); lt.setContentsMargins(0,0,0,0)
            self.edt_tc = QLineEdit("#FFFFFF"); self.edt_tc.textChanged.connect(self.sync_tc)
            self.btn_tc = QPushButton(); self.btn_tc.setFixedSize(30,24) # Fix: Reduce height to 24
            self.btn_tc.clicked.connect(self.pick_tc)
            self.btn_tc.setStyleSheet("background:#FFFFFF; border:1px solid #aaa;")
            # Fix: Add enough space for color picker row
            self.w_tc.setMinimumHeight(40)
            lt.addWidget(SelectableLabel("色值:")); lt.addWidget(self.edt_tc); lt.addWidget(self.btn_tc)
            l.addWidget(self.w_tc); self.w_tc.hide()

        l.addWidget(SelectableLabel("透明度:"))
        self.cb_tr = WhiteComboBox(); self.cb_tr.addItems(["維持", "改變"])
        self.cb_tr.currentIndexChanged.connect(self.settings_changed.emit)
        l.addWidget(self.cb_tr)

        l.addWidget(SelectableLabel("填充內容:"))
        self.cb_c = WhiteComboBox(); self.cb_c.addItems(["維持", "填充顏色", "填充漸層", "填充圖片"])
        self.cb_c.currentIndexChanged.connect(self.tog_c); self.cb_c.currentIndexChanged.connect(self.settings_changed.emit)
        l.addWidget(self.cb_c)

        self.st_c = QStackedWidget(); self.st_c.addWidget(QWidget())
        
        pc = QWidget(); lc = QHBoxLayout(pc); lc.setContentsMargins(0,0,0,0); pc.setMinimumHeight(40)
        self.edt_fc = QLineEdit("#FFFFFF"); self.edt_fc.textChanged.connect(self.sync_fc)
        self.btn_fc = QPushButton(); self.btn_fc.setFixedSize(30,24) # Fix: Reduce height to 24
        self.btn_fc.clicked.connect(self.pick_fc)
        self.btn_fc.setStyleSheet("background:#FFFFFF; border:1px solid #aaa;")
        lc.addWidget(SelectableLabel("色值:")); lc.addWidget(self.edt_fc); lc.addWidget(self.btn_fc)
        self.st_c.addWidget(pc)

        pg = QWidget(); lg = QHBoxLayout(pg); lg.setContentsMargins(0,0,0,0)
        bg = QPushButton("設定漸層"); bg.clicked.connect(self.cfg_g)
        lg.addWidget(bg); lg.addStretch()
        self.st_c.addWidget(pg)

        pi = QWidget(); li = QHBoxLayout(pi); li.setContentsMargins(0,0,0,0)
        self.lbl_i = SelectableLabel("無"); bi = QPushButton("選擇/編輯"); bi.clicked.connect(self.cfg_i)
        li.addWidget(self.lbl_i,1); li.addWidget(bi)
        self.st_c.addWidget(pi)
        
        l.addWidget(self.st_c)
        l.addStretch() 

    def tog_t(self, i): self.w_tc.setVisible(i>0)
    def tog_c(self, i): self.st_c.setCurrentIndex(i)
    def pick_tc(self):
        c = QColorDialog.getColor(QColor(self.sets['target_color']), self)
        if c.isValid(): self.edt_tc.setText(c.name().upper())
    def sync_tc(self, t):
        if QColor.isValidColor(t):
            self.sets['target_color']=t; self.btn_tc.setStyleSheet(f"background:{t}; border:1px solid #aaa;")
            self.settings_changed.emit()
    def pick_fc(self):
        c = QColorDialog.getColor(QColor(self.sets['fill_color']), self)
        if c.isValid(): self.edt_fc.setText(c.name().upper())
    def sync_fc(self, t):
        if QColor.isValidColor(t):
            self.sets['fill_color']=t; self.btn_fc.setStyleSheet(f"background:{t}; border:1px solid #aaa;")
            self.settings_changed.emit()
    def cfg_g(self):
        d = GradientDialog(self)
        if d.exec(): self.sets['fill_gradient']=d.get_data(); self.settings_changed.emit()
    def cfg_i(self):
        d = ImageEditorDialog(self)
        if d.exec(): self.sets['fill_image_path']=d.path; self.sets['fill_image_transform']=d.data; self.lbl_i.setText("已設定"); self.settings_changed.emit()

    def get_settings(self):
        # Fix: Check has_target before accessing cb_t
        idx = 0
        if self.has_target:
            idx = self.cb_t.currentIndex()
            
        tm = 'all'
        if self.has_target:
            if idx == 1: tm = 'specific'
            elif idx == 2: tm = 'non_specific'
            
        fm = ['maintain', 'color', 'gradient', 'image'][self.cb_c.currentIndex()]
        return {
            'target_mode': tm, 'target_color': self.sets['target_color'],
            'trans_mode': 'change' if self.cb_tr.currentIndex()==1 else 'maintain', 'trans_val': 100,
            'fill_mode': fm, 'fill_color': self.sets['fill_color'],
            'fill_gradient': self.sets['fill_gradient'],
            'fill_image_path': self.sets['fill_image_path'],
            'fill_image_transform': self.sets['fill_image_transform']
        }

# -----------------------------------------------------------
# MainWindow
# -----------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Media Batch Processor"); self.resize(1400, 900)
        self.settings = QSettings("MyCompany", "ImageToolApp"); self.worker = None; self.active_pbar = None
        self.init_ui()

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        ml = QHBoxLayout(central); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # Sidebar
        self.sb = QWidget(); self.sb.setFixedWidth(260); self.sb.setObjectName("SidebarFrame")
        sl = QVBoxLayout(self.sb); sl.setContentsMargins(0,30,0,20); sl.setSpacing(8)
        t = QLabel("Media Batcher"); t.setStyleSheet("color:#38bdf8;font-size:24px;font-weight:bold;margin-left:20px;")
        sl.addWidget(t); sl.addWidget(QLabel("Python Port v1.0", parent=self.sb))
        self.btns = []
        items = [("圖片處理","🖼️",0), ("智慧填色","🎨",1), ("影片銳化","🎥",2), ("更名工具","📝",3), ("Icon 生成","📦",4)]
        for txt, ic, idx in items:
            b = SidebarButton(txt, ic, idx, self.sb); b.clicked.connect(self.switch_page)
            sl.addWidget(b); self.btns.append(b)
        sl.addStretch(); ml.addWidget(self.sb)

        # Right
        right = QWidget(); right.setObjectName("RightFrame")
        rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0)
        self.header = QLabel("功能"); self.header.setFixedHeight(60)
        self.header.setStyleSheet("background:white;padding-left:30px;font-size:24px;font-weight:bold;")
        rl.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_scaling_ui()) 
        self.stack.addWidget(self.page_fill_ui())    
        self.stack.addWidget(self.page_video_ui())   
        self.stack.addWidget(self.page_rename_ui())  
        self.stack.addWidget(self.page_multi_ui())   
        
        self.log_con = QWidget(); self.log_con.setStyleSheet("background-color:#2b2b2b;color:white;border:none;")
        ll = QVBoxLayout(self.log_con); ll.setContentsMargins(0,0,0,0); ll.setSpacing(0)
        
        lh = QWidget(); lh.setStyleSheet("background-color:#333;border-bottom:1px solid #444;")
        lh.setFixedHeight(40)
        hl = QHBoxLayout(lh); hl.setContentsMargins(10,0,10,0)
        lbl = QLabel("執行紀錄 (Console)"); lbl.setStyleSheet("color:#ccc;font-weight:bold;")
        
        # Fix: Widen Clear Button
        btn_c = QPushButton("清除 log"); btn_c.setFixedSize(100, 28) 
        btn_c.setStyleSheet("background:#555;color:white;border:none;border-radius:3px;")
        btn_c.clicked.connect(lambda: self.log_area.clear())
        hl.addWidget(lbl); hl.addStretch(); hl.addWidget(btn_c)
        ll.addWidget(lh)

        self.log_area = QTextEdit(); self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color:#2b2b2b;color:#eee;border:none;font-family:Consolas;padding:5px;")
        ll.addWidget(self.log_area)
        
        sp = QSplitter(Qt.Vertical); sp.addWidget(self.stack); sp.addWidget(self.log_con)
        sp.setStretchFactor(0, 2); sp.setStretchFactor(1, 1)
        rl.addWidget(sp)
        ml.addWidget(right); self.switch_page(0)

    def switch_page(self, idx):
        self.stack.setCurrentIndex(idx)
        for b in self.btns: b.set_selected(b.index == idx)
        ts = ["圖片處理", "智慧填色", "影片銳化", "更名工具", "Icon 生成"]
        if 0<=idx<len(ts): self.header.setText(ts[idx])

    def _create_scroll(self):
        page = QWidget(); pl = QVBoxLayout(page); pl.setContentsMargins(0,0,0,0); pl.setSpacing(0)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        ct = QWidget(); ct.setObjectName("ScrollContent"); cl = QVBoxLayout(ct); cl.setContentsMargins(40,30,40,30); cl.setSpacing(20)
        sc.setWidget(ct); pl.addWidget(sc)

        btn_area = QWidget(); btn_area.setStyleSheet("background-color: rgba(223, 212, 186, 0.9); border: none;")
        bl = QVBoxLayout(btn_area); bl.setContentsMargins(40, 15, 40, 15)
        
        fp_row = QHBoxLayout()
        self.lbl_curr = SelectableLabel("等待中..."); self.lbl_curr.setStyleSheet("color:#555;font-size:14px;")
        fp_row.addWidget(self.lbl_curr); fp_row.addStretch()
        bl.addLayout(fp_row)

        main_row = QHBoxLayout()
        btn = QPushButton("開始執行"); btn.setObjectName("ExecBtn"); btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("QPushButton#ExecBtn { background-color: #2563eb; color: white; border-radius: 8px; font-weight: bold; font-size: 16px; padding: 10px 24px; } QPushButton#ExecBtn:hover { background-color: #1d4ed8; }")
        
        pb = QProgressBar(); pb.setRange(0, 100); pb.setTextVisible(True); pb.setFixedWidth(250)
        pb.setStyleSheet("QProgressBar { border: 1px solid #999; background: #eee; border-radius: 4px; text-align: center; color: black; } QProgressBar::chunk { background: #3b82f6; }")
        
        main_row.addWidget(btn); main_row.addStretch(); main_row.addWidget(SelectableLabel("總進度:")); main_row.addWidget(pb)
        bl.addLayout(main_row)
        
        pl.addWidget(btn_area)
        return page, cl, btn, pb

    def create_path_group(self):
        g = QGroupBox("路徑"); l = QFormLayout()
        
        ri = QHBoxLayout(); ei = QLineEdit()
        bd = QPushButton("資料夾"); bf = QPushButton("檔案"); di = DragDropArea()
        bd.clicked.connect(lambda _,e=ei: self.sd(e)); bf.clicked.connect(lambda _,e=ei: self.sf(e)); di.fileDropped.connect(ei.setText)
        ri.addWidget(ei); ri.addWidget(bd); ri.addWidget(bf); ri.addWidget(di)
        
        ro = QHBoxLayout(); eo = QLineEdit()
        bo = QPushButton("資料夾"); do = DragDropArea()
        bo.clicked.connect(lambda _,e=eo: self.sd(e)); do.fileDropped.connect(eo.setText)
        ro.addWidget(eo); ro.addWidget(bo); ro.addWidget(do)
        
        l.addRow(SelectableLabel("輸入:"), ri); l.addRow(SelectableLabel("輸出:"), ro)
        g.setLayout(l)
        return g, ei, eo

    # --- Pages ---
    def page_scaling_ui(self):
        p,l,b,pb = self._create_scroll(); self.sc_pb = pb; self.btn_sc = b
        gp, self.sc_i, self.sc_o = self.create_path_group(); l.addWidget(gp)
        
        go = QGroupBox("參數"); lo = QFormLayout(go)
        self.sc_mode = WhiteComboBox(); self.sc_mode.addItems(["Ratio", "Fixed Width", "Fixed Height"])
        self.sc_st = QStackedWidget()
        w1=QWidget(); l1=QHBoxLayout(w1); l1.setContentsMargins(0,0,0,0); self.sc_v1=QLineEdit("1.0"); l1.addWidget(self.sc_v1); l1.addWidget(SelectableLabel("x")); self.sc_st.addWidget(w1)
        w2=QWidget(); l2=QHBoxLayout(w2); l2.setContentsMargins(0,0,0,0); self.sc_v2=QLineEdit("1920"); l2.addWidget(self.sc_v2); l2.addWidget(SelectableLabel("px")); self.sc_st.addWidget(w2)
        w3=QWidget(); l3=QHBoxLayout(w3); l3.setContentsMargins(0,0,0,0); self.sc_v3=QLineEdit("1080"); l3.addWidget(self.sc_v3); l3.addWidget(SelectableLabel("px")); self.sc_st.addWidget(w3)
        self.sc_mode.currentIndexChanged.connect(self.sc_st.setCurrentIndex)
        reh = QHBoxLayout(); self.sc_sh = QLineEdit("1.0"); self.sc_br = QLineEdit("1.0"); reh.addWidget(SelectableLabel("銳利:")); reh.addWidget(self.sc_sh); reh.addWidget(SelectableLabel("亮度:")); reh.addWidget(self.sc_br)
        self.sc_pre = QLineEdit(); self.sc_post = QLineEdit(); self.sc_auth = QLineEdit(); self.sc_desc = QLineEdit()
        lo.addRow(SelectableLabel("模式:"), self.sc_mode); lo.addRow(SelectableLabel("數值:"), self.sc_st); lo.addRow(SelectableLabel("增強:"), reh)
        lo.addRow(SelectableLabel("前綴:"), self.sc_pre); lo.addRow(SelectableLabel("後綴:"), self.sc_post); lo.addRow(SelectableLabel("作者:"), self.sc_auth); lo.addRow(SelectableLabel("描述:"), self.sc_desc)
        l.addWidget(go)

        gc = QGroupBox("選項"); lc = QGridLayout(gc)
        self.sc_rec = QCheckBox("含子資料夾"); self.sc_rec.setChecked(True); self.sc_jpg = QCheckBox("轉JPG"); self.sc_jpg.setChecked(True); self.sc_low = QCheckBox("小寫副檔名"); self.sc_low.setChecked(True)
        self.sc_del = QCheckBox("刪原始檔"); self.sc_crop = QCheckBox("豆包裁切"); self.sc_meta = QCheckBox("除Meta")
        lc.addWidget(self.sc_rec,0,0); lc.addWidget(self.sc_jpg,0,1); lc.addWidget(self.sc_low,0,2); lc.addWidget(self.sc_del,1,0); lc.addWidget(self.sc_crop,1,1); lc.addWidget(self.sc_meta,1,2)
        l.addWidget(gc)
        self.btn_sc.clicked.connect(self.run_scaling)
        return p
    
    def run_scaling(self):
        m = ['ratio','width','height'][self.sc_mode.currentIndex()]
        try: v1 = float(self.sc_v1.text()) if m=='ratio' else float(self.sc_v2.text()) if m=='width' else float(self.sc_v3.text()); sh = float(self.sc_sh.text()); br = float(self.sc_br.text())
        except: self.log("參數錯誤"); return
        self.run_worker(logic.task_scaling, self.sc_pb, self.sc_pb, input_path=self.sc_i.text(), output_path=self.sc_o.text(), mode=m, mode_value_1=v1, mode_value_2=0, recursive=self.sc_rec.isChecked(), convert_jpg=self.sc_jpg.isChecked(), lower_ext=self.sc_low.isChecked(), delete_original=self.sc_del.isChecked(), prefix=self.sc_pre.text(), postfix=self.sc_post.text(), crop_doubao=self.sc_crop.isChecked(), sharpen_factor=sh, brightness_factor=br, remove_metadata=self.sc_meta.isChecked(), author=self.sc_auth.text(), description=self.sc_desc.text())

    def page_fill_ui(self):
        p,l,b,pb = self._create_scroll(); self.fill_pb = pb; self.btn_fill = b
        gp, self.fi, self.fo = self.create_path_group(); l.addWidget(gp)
        
        rr=QHBoxLayout()
        self.rop=RegionControl("不透明",True); self.rtr=RegionControl("透明",False); self.rse=RegionControl("半透明",True)
        rr.addWidget(self.rop); rr.addWidget(self.rtr); rr.addWidget(self.rse); l.insertLayout(1, rr)
        
        sa=QHBoxLayout()
        gb=QGroupBox("背景"); lb=QVBoxLayout(gb)
        self.ck_bg=QCheckBox("設定背景"); self.ck_bg.toggled.connect(lambda c: self.w_bg.setVisible(c)); lb.addWidget(self.ck_bg)
        self.w_bg=QWidget(); lp=QFormLayout(self.w_bg)
        self.cb_bgt=WhiteComboBox(); self.cb_bgt.addItems(["色塊", "漸層", "圖片"])
        self.cb_bgm=WhiteComboBox(); self.cb_bgm.addItems(["疊加", "背景鏤空"])
        
        self.st_bg=QStackedWidget()
        wb1=QWidget(); lb1=QHBoxLayout(wb1); lb1.setContentsMargins(0,0,0,0)
        self.bg_hex=QLineEdit("#FFFFFF"); self.btn_bg_c=QPushButton(); self.btn_bg_c.setFixedSize(30,30)
        self.btn_bg_c.setStyleSheet("background:#FFFFFF;border:1px solid #aaa")
        self.bg_hex.textChanged.connect(lambda t: self.btn_bg_c.setStyleSheet(f"background:{t};border:1px solid #aaa") if QColor.isValidColor(t) else None)
        self.btn_bg_c.clicked.connect(lambda: (c:=QColorDialog.getColor(QColor(self.bg_hex.text()), self)) and c.isValid() and self.bg_hex.setText(c.name().upper()))
        lb1.addWidget(SelectableLabel("色值:")); lb1.addWidget(self.bg_hex); lb1.addWidget(self.btn_bg_c); lb1.addStretch(); self.st_bg.addWidget(wb1)
        
        wb2=QWidget(); lb2=QHBoxLayout(wb2); btn_bg=QPushButton("漸層"); lb2.addWidget(btn_bg); lb2.addStretch(); self.st_bg.addWidget(wb2)
        wb3=QWidget(); lb3=QHBoxLayout(wb3); btn_bi=QPushButton("圖"); lb3.addWidget(btn_bi); lb3.addStretch(); self.st_bg.addWidget(wb3)
        self.cb_bgt.currentIndexChanged.connect(self.st_bg.setCurrentIndex)
        lp.addRow(SelectableLabel("類型:"), self.cb_bgt); lp.addRow(SelectableLabel("內容:"), self.st_bg); lp.addRow(SelectableLabel("模式:"), self.cb_bgm)
        lb.addWidget(self.w_bg); self.w_bg.hide(); sa.addWidget(gb, 1)

        gc=QGroupBox("裁切"); lc=QVBoxLayout(gc)
        self.cb_cs=WhiteComboBox()
        self.cb_cs.addItems(["無", "圓形", "水平橢圓形", "垂直橢圓形", "正三角形", "正方形", "正五邊形", "正六邊形", "四角星形(圓角)", "四角星形(銳角)", "五角星形(圓角)", "五角星形(銳角)", "隨機雲狀(在圓形內)", "隨機雲狀(符合原始圖)", "上傳自定義圖片形狀"])
        lc.addWidget(SelectableLabel("形狀:")); lc.addWidget(self.cb_cs)
        self.ck_tm=QCheckBox("符合尺寸"); lc.addWidget(self.ck_tm); sa.addWidget(gc, 1)
        l.insertLayout(2, sa)

        so=QHBoxLayout()
        go=QGroupBox("輸出"); lo=QVBoxLayout(go)
        self.ck_fr=QCheckBox("含子資料夾"); self.ck_fd=QCheckBox("刪除原始"); lo.addWidget(self.ck_fr); lo.addWidget(self.ck_fd)
        rf=QHBoxLayout(); rf.addWidget(SelectableLabel("格式:")); self.cb_ff=WhiteComboBox(); self.cb_ff.addItems(["png","jpg","webp"])
        rf.addWidget(self.cb_ff); rf.addStretch(); lo.addLayout(rf); so.addWidget(go, 1)
        
        gpv=QGroupBox("預覽"); lpv=QVBoxLayout(gpv)
        self.pv=QLabel("Preview"); self.pv.setAlignment(Qt.AlignCenter); self.pv.setStyleSheet("background:#eee; border:2px dashed #ccc")
        self.pv.setMinimumHeight(200); btn_u=QPushButton("刷新"); btn_u.clicked.connect(self.upd_pv)
        lpv.addWidget(self.pv, 1); lpv.addWidget(btn_u); so.addWidget(gpv, 1)
        l.insertLayout(3, so)
        self.btn_fill.clicked.connect(self.run_fill)
        return p
    
    def upd_pv(self):
        path = self.fi.text(); rec = self.ck_fr.isChecked()
        if not path: return
        p = Path(path); sample = None
        if p.is_file(): sample = p
        elif p.is_dir():
            pat = "**/*" if rec else "*"
            for f in p.glob(pat):
                if f.suffix.lower() in ['.png','.jpg','.jpeg']: sample = f; break
        if sample:
            try:
                img = Image.open(sample); img.thumbnail((400,400))
                op = self.rop.get_settings(); tr = self.rtr.get_settings(); se = self.rse.get_settings()
                bg = {'enabled':self.ck_bg.isChecked(), 'type':['color','gradient','image'][self.cb_bgt.currentIndex()], 'color':self.bg_hex.text()}
                cr = {'shape':self.cb_cs.currentText(), 'trim_enabled':self.ck_tm.isChecked()}
                res = logic.process_single_image_fill(img, op, tr, se, bg, cr)
                if res.mode != 'RGBA': res = res.convert('RGBA')
                data = res.tobytes("raw", "RGBA")
                qim = QImage(data, res.width, res.height, QImage.Format_RGBA8888)
                self.pv.setPixmap(QPixmap.fromImage(qim))
            except Exception as e: self.log(str(e))

    def run_fill(self):
        op = self.rop.get_settings(); tr = self.rtr.get_settings(); se = self.rse.get_settings()
        bg = {'enabled':self.ck_bg.isChecked(), 'type':['color','gradient','image'][self.cb_bgt.currentIndex()], 'color':self.bg_hex.text()}
        cr = {'shape':self.cb_cs.currentText(), 'trim_enabled':self.ck_tm.isChecked()}
        self.run_worker(logic.task_image_fill, self.fill_pb, self.fill_pb, input_path=self.fi.text(), output_path=self.fo.text(), recursive=self.ck_fr.isChecked(), settings_opaque=op, settings_trans=tr, settings_semi=se, bg_settings=bg, crop_settings=cr, delete_original=self.ck_fd.isChecked(), output_format=self.cb_ff.currentText())

    def page_video_ui(self):
        p, l, self.btn_vd, self.vd_pb = self._create_scroll()
        gp, self.vi, self.vo = self.create_path_group(); l.addWidget(gp)
        gs = QGroupBox("參數"); ls = QFormLayout(gs)
        self.vd_ls = WhiteComboBox(); self.vd_ls.addItems(["3","5","7","9","11"]); self.vd_ls.setCurrentText("7")
        self.vd_la = QLineEdit("1.0")
        ls.addRow(SelectableLabel("Luma Size:"), self.vd_ls); ls.addRow(SelectableLabel("Luma Amount:"), self.vd_la); l.addWidget(gs)
        gr = QGroupBox("輸出"); lr = QFormLayout(gr)
        self.vd_sm = WhiteComboBox(); self.vd_sm.addItems(["None","1080p","720p","Ratio"])
        self.vd_sv = QLineEdit("1.0"); self.vd_pre = QLineEdit(); self.vd_post = QLineEdit(); self.vd_au = QLineEdit(); self.vd_de = QLineEdit()
        lr.addRow(SelectableLabel("縮放:"), self.vd_sm); lr.addRow(SelectableLabel("比例:"), self.vd_sv); lr.addRow(SelectableLabel("前綴:"), self.vd_pre); lr.addRow(SelectableLabel("後綴:"), self.vd_post); l.addWidget(gr)
        gc = QGroupBox("選項"); lc = QGridLayout(gc)
        self.vd_rec = QCheckBox("含子資料夾"); self.vd_rec.setChecked(True); self.vd_mp4 = QCheckBox("轉MP4"); self.vd_mp4.setChecked(True); self.vd_low = QCheckBox("小寫"); self.vd_low.setChecked(True)
        self.vd_del = QCheckBox("刪原始"); self.vd_meta = QCheckBox("除Meta")
        lc.addWidget(self.vd_rec,0,0); lc.addWidget(self.vd_mp4,0,1); lc.addWidget(self.vd_low,0,2); lc.addWidget(self.vd_del,1,0); lc.addWidget(self.vd_meta,1,1); l.addWidget(gc)
        self.btn_vd.clicked.connect(self.run_video)
        return p

    def run_video(self):
        s_idx = self.vd_sm.currentIndex(); mode = 'none'
        if s_idx==1: mode='hd1080'
        elif s_idx==2: mode='hd720'
        elif s_idx==3: mode='ratio'
        self.run_worker(logic.task_video_sharpen, self.vd_pb, self.vd_pb, input_path=self.vi.text(), output_path=self.vo.text(), recursive=self.vd_rec.isChecked(), lower_ext=self.vd_low.isChecked(), delete_original=self.vd_del.isChecked(), prefix=self.vd_pre.text(), postfix=self.vd_post.text(), luma_m_size=int(self.vd_ls.currentText()), luma_amount=float(self.vd_la.text()), scale_mode=mode, scale_value=float(self.vd_sv.text()), convert_h264=self.vd_mp4.isChecked(), remove_metadata=self.vd_meta.isChecked(), author=self.vd_au.text(), description=self.vd_de.text())

    def page_rename_ui(self):
        p, l, self.btn_rn, self.rn_pb = self._create_scroll()
        gp, self.ri, _ = self.create_path_group(); l.addWidget(gp)
        gr = QGroupBox("規則"); lr = QFormLayout(gr)
        self.ck_rp = QCheckBox("改前綴"); self.p1 = QLineEdit(); self.p2 = QLineEdit(); rp = QHBoxLayout(); rp.addWidget(self.p1); rp.addWidget(SelectableLabel("->")); rp.addWidget(self.p2)
        self.ck_rs = QCheckBox("改後綴"); self.s1 = QLineEdit(); self.s2 = QLineEdit(); rs = QHBoxLayout(); rs.addWidget(self.s1); rs.addWidget(SelectableLabel("->")); rs.addWidget(self.s2)
        lr.addRow(self.ck_rp, rp); lr.addRow(self.ck_rs, rs); l.addWidget(gr)
        self.rn_rec = QCheckBox("含子資料夾"); self.rn_rec.setChecked(True); l.addWidget(self.rn_rec)
        self.btn_rn.clicked.connect(self.run_rename)
        return p

    def run_rename(self):
        self.run_worker(logic.task_rename_replace, self.rn_pb, self.rn_pb, input_path=self.ri.text(), recursive=self.rn_rec.isChecked(), do_prefix=self.ck_rp.isChecked(), old_prefix=self.p1.text(), new_prefix=self.p2.text(), do_suffix=self.ck_rs.isChecked(), old_suffix=self.s1.text(), new_suffix=self.s2.text())

    def page_multi_ui(self):
        p, l, self.btn_mt, self.mt_pb = self._create_scroll()
        gp, self.mi, self.mo = self.create_path_group(); l.addWidget(gp)
        self.cb_ori = WhiteComboBox(); self.cb_ori.addItems(["水平","垂直"]); l.addWidget(SelectableLabel("基準:")); l.addWidget(self.cb_ori)
        self.mt_rec = QCheckBox("含子資料夾"); self.mt_rec.setChecked(True); l.addWidget(self.mt_rec)
        self.btn_mt.clicked.connect(self.run_multi)
        return p

    def run_multi(self):
        self.run_worker(logic.task_multi_res, self.mt_pb, self.mt_pb, input_path=self.mi.text(), output_path=self.mo.text(), recursive=self.mt_rec.isChecked(), lower_ext=True, orientation='h' if self.cb_ori.currentIndex()==0 else 'v')

    def sf(self, e): f,_=QFileDialog.getOpenFileName(self,"選檔"); (e.setText(f) if f else None)
    def sd(self, e): d=QFileDialog.getExistingDirectory(self,"選夾"); (e.setText(d) if d else None)
    def log(self, m): self.log_area.append(m)
    def run_worker(self, func, pb, pl, **kwargs):
        if not kwargs.get('input_path'): self.log("❌ 請選擇路徑"); return
        self.active_pbar = pb; self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(lambda v: self.active_pbar.setValue(v))
        self.worker.current_file_signal.connect(lambda s: self.lbl_curr.setText(f"處理中: {s}"))
        self.worker.finished_signal.connect(lambda: self.log("✅ 完成")); self.worker.start()