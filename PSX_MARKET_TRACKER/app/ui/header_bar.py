from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QPushButton, QLabel, 
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QRectF, QPointF
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, QPolygonF

class RefreshButton(QPushButton):
    def __init__(self, callback, parent=None):
        super().__init__("Refresh", parent) 
        self.setFixedSize(35, 35)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.animate_click)
        self.callback = callback
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #10b981;
                border: none;
                font-size: 20px;
                font-weight: bold;
                border-radius: 17px;
            }
            QPushButton:hover {
                background: rgba(16, 185, 129, 0.1);
            }
        """)
        
        # Rotation Animation
        self._angle = 0
        self.anim = QPropertyAnimation(self, b"rotation_angle")
        self.anim.setDuration(800)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(0)
        self.anim.setEndValue(360)
    
    # Property for animation
    @pyqtProperty(float)
    def rotation_angle(self): return self._angle
    
    @rotation_angle.setter
    def rotation_angle(self, a):
        self._angle = a
        self.update() # Trigger repaint
        
    def paintEvent(self, event):
        # Custom paint to handle rotation
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Translate to center, rotate, translate back
        w, h = self.width(), self.height()
        p.translate(w/2, h/2)
        p.rotate(self._angle)
        p.translate(-w/2, -h/2)
        
        # Draw background if hovered
        if self.underMouse():
            p.setBrush(QColor(16, 185, 129, 25))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(0, 0, w, h)
            
        p.setPen(QPen(QColor("#10b981"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        
        # Draw a professional circular arrow (refresh icon)
        center = self.rect().center()
        radius = min(w, h) / 2 - 8
        rect = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
        
        # Draw the arc (3/4 circle)
        p.drawArc(rect, 45 * 16, 270 * 16)
        
        # Draw the arrow head
        arrow_size = 5
        p.setBrush(QColor("#10b981"))
        p.translate(center.x(), center.y())
        p.rotate(45) # Match the arc start
        p.translate(radius, 0)
        
        from PyQt6.QtGui import QPolygonF
        from PyQt6.QtCore import QPointF
        arrow_head = QPolygonF([
            QPointF(0, -arrow_size),
            QPointF(arrow_size * 1.5, 0),
            QPointF(0, arrow_size)
        ])
        p.drawPolygon(arrow_head)
        p.end()

    def animate_click(self):
        self.anim.stop()
        self.anim.setStartValue(0)
        self.anim.setEndValue(360)
        self.anim.start()
        self.callback() # Call the actual refresh function

class HeaderBar(QFrame):
    def __init__(self, on_menu_click, on_refresh_click, parent=None, session=None, logout_callback=None):
        super().__init__(parent)
        self.session = session
        self.setObjectName("header")
        self.setFixedHeight(60)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(15, 0, 20, 0); lay.setSpacing(15)
        
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(40, 40); self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.clicked.connect(on_menu_click)
        self.menu_btn.setStyleSheet("background:transparent; color:#10b981; border:none; font-size:24px; font-weight:bold;")
        
        self.logo = QLabel("PSX")
        self.logo.setStyleSheet("color:#10b981; font-size:28px; font-weight:900; background:transparent;")
        
        self.title = QLabel("Market Tracker")
        self.title.setProperty("class", "title-text")
        self.title.setStyleSheet("font-size:22px; font-weight:600; font-style:italic; font-family:'Times New Roman', serif; color:white; background:transparent;")
        
        # Add a soft white "Glow" effect to the title
        self.title_glow = QGraphicsDropShadowEffect(self.title)
        self.title_glow.setBlurRadius(25)
        self.title_glow.setOffset(0, 0)
        self.title_glow.setColor(QColor(255, 255, 255, 200))
        self.title.setGraphicsEffect(self.title_glow)
        
        self.refresh_btn = RefreshButton(on_refresh_click, self)
        
        self.status = QLabel("Live")
        self.status.setStyleSheet("color:#10b981; font-size:11px; font-weight:bold; background:transparent;")
        
        # User info label
        self.user_info = QLabel("")
        self.user_info.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 12px; background: transparent;")
        if session:
            role_label = "Broker" if session.role == 'broker' else ("Client" if session.role == 'client' else "")
            display = session.user_name
            if role_label:
                display = f"{session.user_name} · {role_label}"
            self.user_info.setText(display)
        
        # Logout button
        self.logout_btn = QPushButton("🚪")
        self.logout_btn.setFixedSize(35, 35)
        self.logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_btn.setToolTip("Sign Out")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 0.4);
                border: none;
                font-size: 20px;
                border-radius: 17px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.15);
                color: #ef4444;
            }
        """)
        if logout_callback:
            self.logout_btn.clicked.connect(logout_callback)
        
        lay.addWidget(self.menu_btn)
        lay.addWidget(self.logo)
        lay.addWidget(self.title)
        lay.addStretch()
        lay.addWidget(self.user_info)
        lay.addWidget(self.refresh_btn)
        lay.addWidget(self.status)
        lay.addWidget(self.logout_btn)
        
    def set_title(self, text):
        # Updates the header title dynamically
        self.title.setText(text)
