from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QLabel, QTextEdit, QFileDialog, 
                               QStackedWidget, QLineEdit, QCheckBox, QGroupBox, 
                               QFormLayout, QComboBox, QSplitter, QScrollArea, QFrame, 
                               QProgressBar, QColorDialog, QDialog, QSpinBox, QGridLayout, QSlider)
from PySide6.QtCore import Qt, QSettings, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from app.workers import Worker
import app.logic as logic

class SelectableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setCursor(Qt.IBeamCursor)

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
    def __init__(self, parent=None): super().__init__(parent)

class SidebarButton(QFrame):
    clicked = Signal(int)
    def __init__(self, text, icon_char, index, parent=None):
        super().__init__(parent)
        self.index = index; self.setCursor(Qt.PointingHandCursor); self.setMinimumHeight(60); self.setObjectName("SidebarBtn")
        l = QHBoxLayout(self); l.setContentsMargins(20,0,20,0); l.setSpacing(15)
        self.ind = QWidget(); self.ind.setFixedSize(4,24); self.ind.setStyleSheet("background:transparent;border-radius:2px;")
        self.ic = QLabel(icon_char); self.ic.setStyleSheet("color:#94a3b8;font-size:20px;background:transparent;")
        self.txt = QLabel(text); self.txt.setObjectName("SidebarBtnText"); self.txt.setStyleSheet("font-size:16px;background:transparent;")
        l.addWidget(self.ind); l.addWidget(self.ic); l.addWidget(self.txt); l.addStretch()
    def set_selected(self, s):
        self.ind.setStyleSheet("background:#38bdf8;" if s else "background:transparent;")
        self.ic.setStyleSheet(f"color:{'#38bdf8' if s else '#94a3b8'};font-size:20px;background:transparent;")
        self.txt.setStyleSheet(f"color:{'white' if s else '#cbd5e1'};font-weight:{'bold' if s else 'normal'};font-size:16px;background:transparent;")
        self.setStyleSheet("background:#334155;border-radius:8px;" if s else "background:transparent;")
    def mousePressEvent(self, e): (self.clicked.emit(self.index) if e.button() == Qt.LeftButton else None)

class ImageTransformDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("圖片變形設定"); self.resize(400, 300)
        l = QFormLayout(self); self.path = ""; self.btn_p = QPushButton("選擇圖片"); self.btn_p.clicked.connect(self.bp)
        self.sl_s = QSlider(Qt.Horizontal); self.sl_s.setRange(10, 200); self.sl_s.setValue(100)
        self.sl_r = QSlider(Qt.Horizontal); self.sl_r.setRange(0, 360); self.sl_r.setValue(0)
        self.sb_x = QSpinBox(); self.sb_x.setRange(-999,999); self.sb_y = QSpinBox(); self.sb_y.setRange(-999,999)
        l.addRow("圖片:", self.btn_p); l.addRow("縮放 %:", self.sl_s); l.addRow("旋轉:", self.sl_r)
        l.addRow("X 偏移:", self.sb_x); l.addRow("Y 偏移:", self.sb_y)
        btn = QPushButton("確定"); btn.clicked.connect(self.accept); l.addRow(btn)
    def bp(self): f,_=QFileDialog.getOpenFileName(self,"選圖"); (setattr(self,'path',f) or self.btn_p.setText(f)) if f else None
    def get_data(self): return {'image_path':self.path, 'transform':{'scale':self.sl_s.value(), 'angle':self.sl_r.value(), 'x':self.sb_x.value(), 'y':self.sb_y.value()}}

class RegionControl(QGroupBox):
    settings_changed = Signal()
    def __init__(self, title, has_target_select=False, parent=None):
        super().__init__(title, parent)
        self.has_target = has_target_select; self.sets = {'target_color':'#FFFFFF', 'fill_color':'#FFFFFF', 'fill_gradient':{}, 'fill_image_path':''}
        self.init_ui()
    def init_ui(self):
        l = QVBoxLayout(self); l.setSpacing(10)
        if self.has_target:
            l.addWidget(SelectableLabel("目標區塊:"))
            self.cb_t = WhiteComboBox(); self.cb_t.addItems([f"全部{self.title().replace('區塊','')}", "指定色值", "非指定色值"])
            self.cb_t.currentIndexChanged.connect(lambda i: (self.w_tc.setVisible(i>0), self.settings_changed.emit()))
            l.addWidget(self.cb_t)
            self.w_tc = QWidget(); lt = QHBoxLayout(self.w_tc); lt.setContentsMargins(0,0,0,0)
            self.edt_tc = QLineEdit("#FFFFFF"); self.btn_tc = QPushButton(); self.btn_tc.setFixedSize(24,24); self.btn_tc.clicked.connect(self.pick_tc)
            lt.addWidget(SelectableLabel("色值:")); lt.addWidget(self.edt_tc); lt.addWidget(self.btn_tc); l.addWidget(self.w_tc); self.w_tc.hide()

        l.addWidget(SelectableLabel("透明度:"))
        self.cb_tr = WhiteComboBox(); self.cb_tr.addItems(["維持", "改變"])
        self.cb_tr.currentIndexChanged.connect(lambda i: (self.w_tr.setVisible(i==1), self.settings_changed.emit()))
        l.addWidget(self.cb_tr)
        self.w_tr = QWidget(); lr = QHBoxLayout(self.w_tr); lr.setContentsMargins(0,0,0,0)
        lr.addWidget(QLabel("不透明")); self.sl_tr = QSlider(Qt.Horizontal); self.sl_tr.setRange(0,100); self.sl_tr.valueChanged.connect(self.settings_changed.emit)
        lr.addWidget(self.sl_tr); lr.addWidget(QLabel("透明")); l.addWidget(self.w_tr); self.w_tr.hide()

        l.addWidget(SelectableLabel("填充內容:"))
        self.cb_c = WhiteComboBox(); self.cb_c.addItems(["維持", "填充顏色", "填充漸層", "填充圖片"])
        self.cb_c.currentIndexChanged.connect(lambda i: (self.st_c.setCurrentIndex(i), self.settings_changed.emit()))
        l.addWidget(self.cb_c); self.st_c = QStackedWidget(); self.st_c.addWidget(QWidget())
        
        pc = QWidget(); lc = QHBoxLayout(pc); lc.setContentsMargins(0,0,0,0)
        self.edt_fc = QLineEdit("#FFFFFF"); bfc = QPushButton(); bfc.setFixedSize(24,24); bfc.clicked.connect(self.pick_fc)
        lc.addWidget(SelectableLabel("色值:")); lc.addWidget(self.edt_fc); lc.addWidget(bfc); self.st_c.addWidget(pc)

        pg = QWidget(); lg = QVBoxLayout(pg); lg.setContentsMargins(0,0,0,0)
        self.sl_ga = QSlider(Qt.Horizontal); self.sl_ga.setRange(0,360); lg.addWidget(QLabel("角度 (0-360):")); lg.addWidget(self.sl_ga)
        lgs = QHBoxLayout(); self.btn_gs = QPushButton("起"); self.btn_ge = QPushButton("結")
        self.btn_gs.clicked.connect(lambda: self.pk_g(True)); self.btn_ge.clicked.connect(lambda: self.pk_g(False))
        lgs.addWidget(self.btn_gs); lgs.addWidget(self.btn_ge); lg.addLayout(lgs); self.st_c.addWidget(pg)
        
        pi = QWidget(); li = QVBoxLayout(pi); btn_img = QPushButton("選擇圖片"); btn_img.clicked.connect(self.pk_img)
        li.addWidget(btn_img); self.st_c.addWidget(pi)
        l.addWidget(self.st_c); l.addStretch()

    def pick_tc(self): (c:=QColorDialog.getColor()) and c.isValid() and (self.edt_tc.setText(c.name().upper()), self.settings_changed.emit())
    def pick_fc(self): (c:=QColorDialog.getColor()) and c.isValid() and (self.edt_fc.setText(c.name().upper()), self.settings_changed.emit())
    def pk_g(self, is_start): (c:=QColorDialog.getColor()) and c.isValid() and (self.sets.setdefault('fill_gradient',{})).__setitem__('start' if is_start else 'end', c.name()) or self.settings_changed.emit()
    def pk_img(self): (f:=QFileDialog.getOpenFileName(self,"選圖")[0]) and (self.sets.__setitem__('fill_image_path',f) or self.settings_changed.emit())
    def get_settings(self):
        return {'target_mode': ['all','specific','non_specific'][self.cb_t.currentIndex()] if self.has_target else 'all',
                'target_color': self.edt_tc.text(), 'trans_mode': 'change' if self.cb_tr.currentIndex()==1 else 'maintain',
                'trans_val': self.sl_tr.value(), 'fill_mode': ['maintain','color','gradient','image'][self.cb_c.currentIndex()],
                'fill_color': self.edt_fc.text(), 'fill_gradient': {'angle':self.sl_ga.value(), **self.sets.get('fill_gradient',{})},
                'fill_image_path': self.sets['fill_image_path']}

class MainWindow(QMainWindow):
    def __init__(self): super().__init__(); self.setWindowTitle("Python Media Batch Processor"); self.resize(1400, 950); self.init_ui()
    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central); ml = QHBoxLayout(central); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)
        self.sb = QWidget(); self.sb.setFixedWidth(260); self.sb.setObjectName("SidebarFrame"); sl = QVBoxLayout(self.sb); sl.setContentsMargins(0,30,0,20); sl.setSpacing(8)
        sl.addWidget(QLabel("Media Batcher", styleSheet="color:#38bdf8;font-size:24px;font-weight:bold;margin-left:20px;"))
        self.btns = []; items = [("圖片處理","🖼️",0), ("智慧填色","🎨",1), ("影片銳利化","🎥",2), ("更名工具","📝",3), ("Icon 生成","📦",4)]
        for t, i, idx in items: b = SidebarButton(t, i, idx, self.sb); b.clicked.connect(self.switch_page); sl.addWidget(b); self.btns.append(b)
        sl.addStretch(); ml.addWidget(self.sb)
        
        right = QWidget(); right.setObjectName("RightFrame"); rl = QVBoxLayout(right); rl.setContentsMargins(0,0,0,0)
        self.header = QLabel("功能", styleSheet="background:white;padding-left:30px;font-size:24px;font-weight:bold;min-height:60px;")
        rl.addWidget(self.header); self.stack = QStackedWidget()
        self.stack.addWidget(self.page_scaling_ui()); self.stack.addWidget(self.page_fill_ui()); self.stack.addWidget(self.page_video_ui())
        self.stack.addWidget(self.page_rename_ui()); self.stack.addWidget(self.page_multi_ui())
        
        # Log Panel 改進: Console 與 按鈕平行
        self.log_con = QWidget(); self.log_con.setStyleSheet("background-color:#2b2b2b;color:white;"); ll = QHBoxLayout(self.log_con); ll.setContentsMargins(10,10,10,10); ll.setSpacing(10)
        self.log_area = QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setStyleSheet("background:#1e1e1e;color:#eee;border:1px solid #444;font-family:Consolas;padding:5px;")
        
        # 右側控制區 (清除按鈕)
        right_ctrl = QVBoxLayout(); right_ctrl.setContentsMargins(0,0,0,0); right_ctrl.setAlignment(Qt.AlignTop)
        btn_c = QPushButton("清除 Log"); btn_c.setObjectName("ClearLogBtn"); btn_c.setFixedSize(80, 28)
        btn_c.clicked.connect(lambda: self.log_area.clear())
        right_ctrl.addWidget(btn_c)
        
        ll.addWidget(self.log_area, 1) # Console 佔據主要空間
        ll.addLayout(right_ctrl)       # 按鈕在右側

        sp = QSplitter(Qt.Vertical); sp.addWidget(self.stack); sp.addWidget(self.log_con); sp.setStretchFactor(0, 3); sp.setStretchFactor(1, 1); rl.addWidget(sp); ml.addWidget(right); self.switch_page(0)

    def switch_page(self, idx): self.stack.setCurrentIndex(idx); [b.set_selected(b.index==idx) for b in self.btns]; self.header.setText(["圖片處理","智慧填色","影片銳利化","更名工具","Icon 生成"][idx])
    
    def _create_scroll(self):
        page = QWidget(); pl = QVBoxLayout(page); pl.setContentsMargins(0,0,0,0)
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        ct = QWidget(); ct.setObjectName("ScrollContent"); self.cl = QVBoxLayout(ct); self.cl.setContentsMargins(40,30,40,30); self.cl.setSpacing(20)
        sc.setWidget(ct); pl.addWidget(sc)
        
        ba = QWidget(); ba.setStyleSheet("background:rgba(223,212,186,0.95);border-top:none;")
        bl = QVBoxLayout(ba); bl.setContentsMargins(40,15,40,15)
        
        v_file = QVBoxLayout(); v_file.setSpacing(4)
        r_info = QHBoxLayout(); self.lbl_file = SelectableLabel(""); r_info.addWidget(self.lbl_file); r_info.addStretch(); self.lbl_file_pct = QLabel("0%"); r_info.addWidget(self.lbl_file_pct)
        v_file.addLayout(r_info)
        self.pb_file = QProgressBar(); self.pb_file.setObjectName("FileProgress"); self.pb_file.setRange(0,100); self.pb_file.setTextVisible(False); v_file.addWidget(self.pb_file); bl.addLayout(v_file); bl.addSpacing(10)

        r2 = QHBoxLayout(); btn = QPushButton("開始執行"); btn.setObjectName("ExecBtn"); btn.setCursor(Qt.PointingHandCursor)
        self.lbl_status = SelectableLabel(""); pb = QProgressBar(); pb.setObjectName("TotalProgress"); pb.setRange(0, 100); pb.setFormat("%p%")
        v_btn = QVBoxLayout(); v_btn.addWidget(self.lbl_status); v_btn.addWidget(btn); r2.addLayout(v_btn); r2.addStretch(); 
        r_total = QHBoxLayout(); r_total.addWidget(SelectableLabel("總進度:")); r_total.addWidget(pb); r2.addLayout(r_total); bl.addLayout(r2)
        pl.addWidget(ba); return page, self.cl, btn, pb

    def create_path_group(self):
        g = QGroupBox("路徑"); l = QFormLayout()
        ri = QHBoxLayout(); ei = QLineEdit(); bd = QPushButton("資料夾"); bf = QPushButton("檔案"); dd = DragDropArea()
        bd.clicked.connect(lambda: (d:=QFileDialog.getExistingDirectory(self)) and ei.setText(d)); bf.clicked.connect(lambda: (f:=QFileDialog.getOpenFileName(self)[0]) and ei.setText(f)); dd.fileDropped.connect(ei.setText)
        ri.addWidget(ei); ri.addWidget(bd); ri.addWidget(bf); ri.addWidget(dd)
        ro = QHBoxLayout(); eo = QLineEdit(); bo = QPushButton("資料夾"); do = DragDropArea()
        bo.clicked.connect(lambda: (d:=QFileDialog.getExistingDirectory(self)) and eo.setText(d)); do.fileDropped.connect(eo.setText)
        ro.addWidget(eo); ro.addWidget(bo); ro.addWidget(do); l.addRow(SelectableLabel("輸入:"), ri); l.addRow(SelectableLabel("輸出:"), ro)
        g.setLayout(l); return g, ei, eo

    def page_scaling_ui(self):
        p,l,b,pb = self._create_scroll(); self.sc_pb = pb; self.btn_sc = b
        gp, self.sc_i, self.sc_o = self.create_path_group(); l.addWidget(gp)
        go = QGroupBox("參數"); lo = QFormLayout(go)
        self.sc_mode = WhiteComboBox(); self.sc_mode.setMinimumWidth(250)
        self.sc_mode.addItems(["維持現狀，不縮放", "比例 (Ratio)", "固定寬度 (Fixed Width)", "固定高度 (Fixed Height)"])
        self.sc_v1 = QLineEdit("1.0"); self.lbl_hint = QLabel("")
        self.sc_mode.currentIndexChanged.connect(lambda i: self.lbl_hint.setText("0.1-5.0" if i==1 else "像素" if i>1 else ""))
        h_row = QHBoxLayout(); h_row.addWidget(self.sc_v1); h_row.addWidget(self.lbl_hint); lo.addRow("模式:", self.sc_mode); lo.addRow("數值:", h_row)
        self.sc_sh = QLineEdit("1.0"); lo.addRow("銳利度 (0.0-2.0):", self.sc_sh)
        self.sc_br = QLineEdit("1.0"); lo.addRow("亮度 (0.0-2.0):", self.sc_br)
        l.addWidget(go)
        gc = QGroupBox("選項"); lc = QGridLayout(gc)
        self.sc_rec = QCheckBox("含子資料夾"); self.sc_rec.setChecked(True); self.sc_jpg = QCheckBox("轉JPG"); self.sc_jpg.setChecked(True)
        self.sc_low = QCheckBox("小寫副檔名"); self.sc_low.setChecked(True); self.sc_del = QCheckBox("刪原始檔")
        self.sc_crop = QCheckBox("豆包裁切"); self.sc_meta = QCheckBox("除Meta")
        lc.addWidget(self.sc_rec,0,0); lc.addWidget(self.sc_jpg,0,1); lc.addWidget(self.sc_low,0,2); lc.addWidget(self.sc_del,1,0); lc.addWidget(self.sc_crop,1,1); lc.addWidget(self.sc_meta,1,2); l.addWidget(gc)
        self.btn_sc.clicked.connect(lambda: self.run_worker(logic.task_scaling, self.sc_pb, input_path=self.sc_i.text(), output_path=self.sc_o.text(), mode=['none','ratio','width','height'][self.sc_mode.currentIndex()], mode_value_1=float(self.sc_v1.text() or 0), recursive=self.sc_rec.isChecked(), convert_jpg=self.sc_jpg.isChecked(), lower_ext=self.sc_low.isChecked(), delete_original=self.sc_del.isChecked(), prefix="", postfix="", crop_doubao=self.sc_crop.isChecked(), sharpen_factor=float(self.sc_sh.text()), brightness_factor=float(self.sc_br.text()), remove_metadata=self.sc_meta.isChecked(), author="", description=""))
        return p

    def page_fill_ui(self):
        p,l,b,pb = self._create_scroll(); self.fill_pb = pb; self.btn_fill = b
        gp, self.fi, self.fo = self.create_path_group(); l.addWidget(gp)
        rr = QHBoxLayout(); self.rop = RegionControl("不透明", True); self.rtr = RegionControl("透明"); self.rse = RegionControl("半透明", True)
        rr.addWidget(self.rop); rr.addWidget(self.rtr); rr.addWidget(self.rse); l.insertLayout(1, rr)
        
        # 修正: 背景設定與裁切設定 50/50 分配
        adv = QHBoxLayout()
        
        # 左側：背景設定 (Stretch=1)
        gb = QGroupBox("背景設定"); lb = QFormLayout(gb)
        self.bg_mode = WhiteComboBox(); self.bg_mode.addItems(["疊加", "鏤空背景"])
        self.bg_mat = WhiteComboBox(); self.bg_mat.addItems(["色塊", "漸層", "圖片"]); self.bg_mat.currentIndexChanged.connect(lambda i: self.st_bg.setCurrentIndex(i))
        self.st_bg = QStackedWidget(); p1 = QWidget(); l1 = QHBoxLayout(p1); self.bg_c = QLineEdit("#FFFFFF"); b_bgc = QPushButton("選色"); b_bgc.clicked.connect(lambda: (c:=QColorDialog.getColor()) and self.bg_c.setText(c.name()))
        l1.addWidget(self.bg_c); l1.addWidget(b_bgc); self.st_bg.addWidget(p1)
        p2 = QWidget(); l2 = QVBoxLayout(p2); self.bg_ga = QSlider(Qt.Horizontal); self.bg_ga.setRange(0,360); l2.addWidget(QLabel("角度")); l2.addWidget(self.bg_ga); self.st_bg.addWidget(p2)
        p3 = QWidget(); l3 = QVBoxLayout(p3); b_img = QPushButton("設定圖片"); b_img.clicked.connect(lambda: ImageTransformDialog(self).exec()); l3.addWidget(b_img); self.st_bg.addWidget(p3)
        self.bg_cut = WhiteComboBox(); self.bg_cut.addItems(["原始圖片不透明像素", "原始圖片透明像素", "原始圖片色值"])
        lb.addRow("模式:", self.bg_mode); lb.addRow("素材:", self.bg_mat); lb.addRow("設定:", self.st_bg); lb.addRow("鏤空目標:", self.bg_cut)
        adv.addWidget(gb, 1) # Stretch 1

        # 右側：裁切設定 (Stretch=1)
        gc = QGroupBox("裁切設定"); lc = QVBoxLayout(gc)
        self.ck_shp = QCheckBox("形狀裁切"); self.cb_shp = WhiteComboBox(); self.cb_shp.hide()
        self.ck_shp.toggled.connect(self.cb_shp.setVisible)
        self.cb_shp.addItems(["圓形","正方形","正三角形","正五邊形","正六邊形","四角星形(圓角)","四角星形(尖角)","五角星形(圓角)","五角星形(尖角)","隨機雲狀(正圓內)","隨機雲狀"])
        self.ck_trim = QCheckBox("貼合尺寸裁切"); self.ck_trim.setObjectName("PinkCheck")
        lc.addWidget(self.ck_shp); lc.addWidget(self.cb_shp); lc.addWidget(self.ck_trim); lc.addStretch()
        adv.addWidget(gc, 1) # Stretch 1
        
        l.insertLayout(2, adv)

        out_layout = QHBoxLayout(); gout = QGroupBox("輸出設定"); lout = QVBoxLayout(gout)
        lout.addWidget(QLabel("格式:")); cb_fmt = WhiteComboBox(); cb_fmt.addItems(["png","jpg"]); lout.addWidget(cb_fmt)
        out_layout.addWidget(gout); out_layout.addWidget(QLabel("預覽區塊(佔位)", alignment=Qt.AlignCenter, styleSheet="border:2px dashed #999;background:#eee;min-height:100px;"))
        l.insertLayout(3, out_layout)
        self.btn_fill.clicked.connect(lambda: self.run_worker(logic.task_image_fill, self.fill_pb, input_path=self.fi.text(), output_path=self.fo.text(), recursive=True, settings_opaque=self.rop.get_settings(), settings_trans=self.rtr.get_settings(), settings_semi=self.rse.get_settings(), bg_settings={'enabled':True, 'mode':['overlay','cutout'][self.bg_mode.currentIndex()], 'material_type':['color','gradient','image'][self.bg_mat.currentIndex()]}, crop_settings={'shape':self.cb_shp.currentText() if self.ck_shp.isChecked() else '無', 'trim':self.ck_trim.isChecked()}, delete_original=False, output_format=cb_fmt.currentText()))
        return p

    def page_video_ui(self):
        p, l, self.btn_vd, self.vd_pb = self._create_scroll()
        gp, self.vi, self.vo = self.create_path_group(); l.addWidget(gp)
        gs = QGroupBox("參數"); ls = QFormLayout(gs)
        self.vd_ls = WhiteComboBox(); self.vd_ls.addItems(["3","5","7","9","11"]); self.vd_ls.setCurrentText("7")
        self.vd_la = QLineEdit("1.0"); ls.addRow(SelectableLabel("Luma Size:"), self.vd_ls); ls.addRow(SelectableLabel("Luma Amount:"), self.vd_la); l.addWidget(gs)
        gr = QGroupBox("輸出"); lr = QFormLayout(gr)
        self.vd_sm = WhiteComboBox(); self.vd_sm.addItems(["None","1080p","720p","Ratio"])
        self.vd_sv = QLineEdit("1.0"); self.vd_pre = QLineEdit(); self.vd_post = QLineEdit(); self.vd_au = QLineEdit(); self.vd_de = QLineEdit()
        lr.addRow(SelectableLabel("縮放:"), self.vd_sm); lr.addRow(SelectableLabel("比例:"), self.vd_sv); lr.addRow(SelectableLabel("前綴:"), self.vd_pre); lr.addRow(SelectableLabel("後綴:"), self.vd_post); l.addWidget(gr)
        gc = QGroupBox("選項"); lc = QGridLayout(gc)
        self.vd_rec = QCheckBox("含子資料夾"); self.vd_rec.setChecked(True); self.vd_mp4 = QCheckBox("轉MP4"); self.vd_mp4.setChecked(True); self.vd_low = QCheckBox("小寫"); self.vd_low.setChecked(True)
        self.vd_del = QCheckBox("刪原始"); self.vd_meta = QCheckBox("除Meta")
        lc.addWidget(self.vd_rec,0,0); lc.addWidget(self.vd_mp4,0,1); lc.addWidget(self.vd_low,0,2); lc.addWidget(self.vd_del,1,0); lc.addWidget(self.vd_meta,1,1); l.addWidget(gc)
        self.btn_vd.clicked.connect(lambda: self.run_worker(logic.task_video_sharpen, self.vd_pb, input_path=self.vi.text(), output_path=self.vo.text(), recursive=True, lower_ext=True, delete_original=False, prefix="", postfix="", luma_m_size=7, luma_amount=1.0, scale_mode='none', scale_value=1.0, convert_h264=True, remove_metadata=False, author="", description="")); return p

    def page_rename_ui(self):
        p, l, self.btn_rn, self.rn_pb = self._create_scroll()
        gp, self.ri, _ = self.create_path_group(); l.addWidget(gp)
        gr = QGroupBox("規則"); lr = QFormLayout(gr)
        self.ck_rp = QCheckBox("改前綴"); self.p1 = QLineEdit(); self.p2 = QLineEdit(); rp = QHBoxLayout(); rp.addWidget(self.p1); rp.addWidget(SelectableLabel("->")); rp.addWidget(self.p2)
        self.ck_rs = QCheckBox("改後綴"); self.s1 = QLineEdit(); self.s2 = QLineEdit(); rs = QHBoxLayout(); rs.addWidget(self.s1); rs.addWidget(SelectableLabel("->")); rs.addWidget(self.s2)
        lr.addRow(self.ck_rp, rp); lr.addRow(self.ck_rs, rs); l.addWidget(gr)
        self.rn_rec = QCheckBox("含子資料夾"); self.rn_rec.setChecked(True); l.addWidget(self.rn_rec)
        self.btn_rn.clicked.connect(lambda: self.run_worker(logic.task_rename_replace, self.rn_pb, input_path=self.ri.text(), recursive=True, do_prefix=self.ck_rp.isChecked(), old_prefix=self.p1.text(), new_prefix=self.p2.text(), do_suffix=self.ck_rs.isChecked(), old_suffix=self.s1.text(), new_suffix=self.s2.text())); return p

    def page_multi_ui(self):
        p, l, self.btn_mt, self.mt_pb = self._create_scroll()
        gp, self.mi, self.mo = self.create_path_group(); l.addWidget(gp)
        r_ori = QHBoxLayout(); r_ori.addWidget(SelectableLabel("基準:")); self.cb_ori = WhiteComboBox(); self.cb_ori.addItems(["水平","垂直"]); r_ori.addWidget(self.cb_ori); r_ori.addStretch(); l.addLayout(r_ori)
        self.mt_rec = QCheckBox("含子資料夾"); self.mt_rec.setChecked(True); l.addWidget(self.mt_rec)
        self.btn_mt.clicked.connect(lambda: self.run_worker(logic.task_multi_res, self.mt_pb, input_path=self.mi.text(), output_path=self.mo.text(), recursive=True, lower_ext=True, orientation='h')); return p

    def run_worker(self, func, pb, **kwargs):
        if not kwargs.get('input_path'): self.log_area.append("❌ 路徑未設定"); return
        self.active_pbar = pb; self.lbl_status.setText("準備中..."); self.worker = Worker(func, **kwargs)
        self.worker.log_signal.connect(self.log_area.append); self.worker.progress_signal.connect(pb.setValue)
        self.worker.current_file_signal.connect(lambda s: (self.lbl_status.setText("執行中..."), self.lbl_file.setText(f"{s}"))); 
        self.worker.file_progress_signal.connect(lambda v: (self.pb_file.setValue(v), self.lbl_file_pct.setText(f"{v}%")))
        self.worker.finished_signal.connect(lambda: (self.log_area.append("✅ 完成"), self.lbl_status.setText("完成"))); self.worker.start()