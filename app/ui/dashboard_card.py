from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QLinearGradient

class DashboardCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, icon, title, desc, color, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setFixedHeight(180); self.clr = QColor(color)
        self._shine_pos = -1.0 # Animation property
        self._opacity = 1.0 # Internal opacity for hover or fade
        
        # Remove any default QFrame border completely
        self.setStyleSheet("QFrame { border: none; background: transparent; }")
        
        lay = QVBoxLayout(self); lay.setContentsMargins(30,30,30,30); lay.setSpacing(10)
        
        top = QHBoxLayout()
        il = QLabel(icon); il.setStyleSheet(f"color:{color}; font-size:32px; border:none; background:transparent;")
        tl = QLabel(title); tl.setProperty("class", "title-text"); tl.setStyleSheet("font-size:20px; font-weight:800; border:none; background:transparent; color:white;")
        top.addWidget(il); top.addWidget(tl); top.addStretch(); lay.addLayout(top)
        
        dl = QLabel(desc); dl.setProperty("class", "desc-text"); dl.setStyleSheet("font-size:14px; font-weight:400; border:none; background:transparent; color:rgba(255,255,255,0.6);"); dl.setWordWrap(True)
        lay.addWidget(dl)
        
        # Animations
        self.anim = QPropertyAnimation(self, b"shine_pos")
        self.anim.setDuration(800); self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def get_shine(self): return self._shine_pos
    def set_shine(self, v): self._shine_pos = v; self.update()
    shine_pos = pyqtProperty(float, get_shine, set_shine)
    
    def get_op(self): return self._opacity
    def set_op(self, v): self._opacity = v; self.update()
    opacity_val = pyqtProperty(float, get_op, set_op)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self._opacity) # Support fade-in from DashboardPage
        r = self.rect().adjusted(2,2,-2,-2)
        
        # 1. Shadow / Outer Glow (Drawn manually for stability)
        p.setBrush(QColor(0, 0, 0, 30))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r.adjusted(3,5,3,5), 22, 22)

        # 2. Glass Background (Clean dark glass, no visible border)
        p.setBrush(QColor(30, 35, 40, 200)) # Darker, more opaque glass
        p.setPen(Qt.PenStyle.NoPen) # No border
        p.drawRoundedRect(r, 20, 20)
        
        # 3. "Sunshine" Shine Effect (Moving Gradient)
        if self._shine_pos > -1.0 and self.underMouse():
            shine_grad = QLinearGradient(r.width() * (self._shine_pos - 0.2), 0, r.width() * (self._shine_pos + 0.3), r.height())
            shine_grad.setColorAt(0, QColor(0, 0, 0, 0))
            shine_grad.setColorAt(0.5, QColor(16, 185, 129, 50))
            shine_grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(shine_grad); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r, 20, 20)
        p.end()

    def enterEvent(self, e): 
        # Start the Shine Sweep
        self.anim.stop(); self.anim.setStartValue(-1.0); self.anim.setEndValue(1.5); self.anim.start()
        super().enterEvent(e)
        
    def leaveEvent(self, e): 
        self.anim.stop(); self.anim.setStartValue(self._shine_pos); self.anim.setEndValue(-1.0); self.anim.start()
        super().leaveEvent(e)
        
    def mousePressEvent(self, e): 
        if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit()
        super().mousePressEvent(e)
