from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QStackedWidget
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, pyqtSignal, QThread
from PyQt6.QtGui import QPainter, QFont, QLinearGradient, QColor, QPen, QBrush, QIcon
from ..core.utils import get_asset_path

class MetallicLetter(QWidget):
    def __init__(self, l, parent=None):
        super().__init__(parent); self.lt = l; self.sh = -0.3; self.fl = 0.0; self.setFixedSize(140, 160)
    def get_s(self): return self.sh
    def set_s(self, v): self.sh = v; self.update()
    def get_f(self): return self.fl
    def set_f(self, v): self.fl = v; self.update()
    shine_position = pyqtProperty(float, get_s, set_s)
    fill_amount = pyqtProperty(float, get_f, set_f)
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); f = QFont("Segoe UI Black", 100); f.setWeight(QFont.Weight.Black); p.setFont(f)
        g = QLinearGradient(0,0,self.width(),0)
        if self.fl >= 1.0: 
            g.setColorAt(0,QColor(16,185,129)); g.setColorAt(1,QColor(16,185,129))
        else: 
            # 5-Stop Brushed Metal Gradient
            base = QColor(30,45,40)
            mid = QColor(150,255,200)
            g.setColorAt(0, base)
            sp = self.sh
            g.setColorAt(max(0, min(1, sp - 0.15)), base)
            g.setColorAt(max(0, min(1, sp)), mid)
            g.setColorAt(max(0, min(1, sp + 0.15)), base)
            g.setColorAt(1, base)
            
        p.setPen(QPen(QBrush(g), 5))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.lt)
        if 0 < self.fl < 1: 
            p.setPen(QPen(QColor(16,185,129,int(255*self.fl)), 5))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.lt)
        p.end()

class ModernProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 4)
        self._progress = 0.0
        self._shine = -0.5
        
        # Internal shine animation
        self.a_shine = QPropertyAnimation(self, b"shine_pos")
        self.a_shine.setDuration(1500); self.a_shine.setStartValue(-0.5); self.a_shine.setEndValue(1.5)
        self.a_shine.setLoopCount(-1); self.a_shine.start()
        
    def get_p(self): return self._progress
    def set_p(self, v): self._progress = v; self.update()
    def get_s(self): return self._shine
    def set_s(self, v): self._shine = v; self.update()
    
    progress = pyqtProperty(float, get_p, set_p)
    shine_pos = pyqtProperty(float, get_s, set_s)
    
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # BG
        p.setBrush(QColor(30,40,35)); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), 2, 2)
        
        # Progress Fill
        fill_w = int(self.width() * self._progress)
        if fill_w > 0:
            g = QLinearGradient(0, 0, fill_w, 0)
            g.setColorAt(0, QColor(16,185,129))
            
            # Shine sweep inside the fill
            sp = self._shine
            g.setColorAt(max(0, min(1, sp - 0.2)), QColor(16,185,129))
            g.setColorAt(max(0, min(1, sp)), QColor(150,255,200))
            g.setColorAt(max(0, min(1, sp + 0.2)), QColor(16,185,129))
            g.setColorAt(1, QColor(16,185,129))
            
            p.setBrush(QBrush(g))
            p.drawRoundedRect(0, 0, fill_w, self.height(), 2, 2)
        p.end()

class SplashWorker(QThread):
    progress = pyqtSignal(float)
    finished = pyqtSignal()
    
    def run(self):
        import time
        # Simulate loading process (0 to 100)
        for i in range(101):
            time.sleep(0.02) 
            self.progress.emit(i / 100.0)
        self.finished.emit()

class SplashScreen(QWidget):
    def __init__(self, cb):
        super().__init__()
        self.cb = cb
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(1000, 750)
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))
        self.setStyleSheet("background:#050608;")
        
        self.lp = MetallicLetter("P", self)
        self.ls = MetallicLetter("S", self)
        self.lx = MetallicLetter("X", self)
        
        l_lay = QHBoxLayout(); l_lay.setSpacing(10); l_lay.addStretch()
        l_lay.addWidget(self.lp); l_lay.addWidget(self.ls); l_lay.addWidget(self.lx); l_lay.addStretch()
        self.lw = QWidget(); self.lw.setLayout(l_lay)
        
        sub = QLabel("MARKET TRACKER"); sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:rgba(255,255,255,0.3); font-size:20px; letter-spacing:12px; font-weight: bold;")
        
        self.status = QLabel("Initializing..."); self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color:#10b981; font-size:14px; font-family: 'Segoe UI Semibold';")
        
        self.bar = ModernProgressBar()
        
        m_lay = QVBoxLayout(self)
        m_lay.addStretch(3)
        m_lay.addWidget(self.lw, alignment=Qt.AlignmentFlag.AlignCenter)
        m_lay.addWidget(sub, alignment=Qt.AlignmentFlag.AlignCenter)
        m_lay.addSpacing(90)
        m_lay.addWidget(self.bar, alignment=Qt.AlignmentFlag.AlignCenter)
        m_lay.addWidget(self.status, alignment=Qt.AlignmentFlag.AlignCenter)
        m_lay.addStretch(3)
        
        self.setup()

    def setup(self):
        self._as = []
        for i, l in enumerate([self.lp,self.ls,self.lx]):
            a = QPropertyAnimation(l, b"shine_position")
            a.setDuration(2200); a.setStartValue(-0.3); a.setEndValue(1.3); a.setLoopCount(-1)
            self._as.append(a)
            QTimer.singleShot(i*350, a.start)
            
        # Smooth progress transition
        self.bar_anim = QPropertyAnimation(self.bar, b"progress")
        self.bar_anim.setDuration(300)
            
        self.worker = SplashWorker()
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, val):
        self.bar_anim.stop()
        self.bar_anim.setEndValue(val)
        self.bar_anim.start()
        
        if val >= 0.99:
            self.lp.set_f(1.0); self.ls.set_f(1.0); self.lx.set_f(1.0)
            self.status.setText("✅ System Ready.")
        else:
            if val < 0.3: self.status.setText("Connecting to PSX...")
            elif val < 0.6: self.status.setText("Loading Professional Assets...")
            elif val < 0.9: self.status.setText("Preparing Market Insights...")
            else: self.status.setText("Finalizing...")

    def on_finished(self):
        QTimer.singleShot(1000, self.real_close)

    def real_close(self):
        try:
            self.worker.progress.disconnect(self.update_progress)
            self.worker.quit()
        except: pass
        for a in self._as: a.stop()
        self.bar.a_shine.stop()
        self.close()
        self.cb()
