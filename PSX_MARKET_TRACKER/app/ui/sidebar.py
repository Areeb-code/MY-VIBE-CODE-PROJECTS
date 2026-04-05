from PyQt6.QtWidgets import QPushButton, QFrame, QVBoxLayout, QLabel, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, pyqtProperty, QSize
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QImage, QColor, QFont, QIcon
import os

class SidebarButton(QPushButton):
    def __init__(self, icon, label, parent=None):
        super().__init__(parent); self.it, self.lbl = icon, label
        self.setFixedHeight(50); self.setCursor(Qt.CursorShape.PointingHandCursor); self.upd(False)
    def upd(self, ex):
        if ex:
            self.setText(f"  {self.it}    {self.lbl}")
            self.setStyleSheet("QPushButton { background:transparent; color:white; text-align:left; padding-left:15px; border:none; font-size:14px; } QPushButton:hover { background:rgba(16,185,129,0.15); color:#10b981; }")
        else:
            self.setText(self.it)
            self.setStyleSheet("QPushButton { background:transparent; color:white; text-align:center; border:none; font-size:18px; } QPushButton:hover { background:rgba(16,185,129,0.15); color:#10b981; }")

class Sidebar(QFrame):
    # Signal emiting (Index, Title)
    page_selected = pyqtSignal(int, str)

    def __init__(self, parent=None, session=None):
        super().__init__(parent); self.setObjectName("sidebar"); self.setFixedWidth(60); self._w = 60; self.is_ex = False
        self.session = session
        self.settings_manager = parent.settings_manager if parent and hasattr(parent, "settings_manager") else None
        self.setStyleSheet("#sidebar { background:#0f1419; border-right:1px solid #222; }")
        
        self.main_lay = QVBoxLayout(self)
        self.main_lay.setContentsMargins(0, 20, 0, 10)
        self.main_lay.setSpacing(5)
        
        # Profile Section
        self.profile_container = QWidget()
        self.profile_lay = QVBoxLayout(self.profile_container)
        self.profile_lay.setContentsMargins(0, 0, 0, 20)
        self.profile_lay.setSpacing(10)
        self.profile_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.profile_pic = QLabel()
        self.profile_pic.setFixedSize(40, 40)
        self.profile_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_lay.addWidget(self.profile_pic, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.profile_name = QLabel()
        self.profile_name.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        self.profile_name.setVisible(False)
        self.profile_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_lay.addWidget(self.profile_name, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Role badge (only for broker/client — never shows "Owner")
        self.role_badge = QLabel()
        self.role_badge.setVisible(False)
        self.role_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.role_badge.setStyleSheet("""
            color: #10b981; font-size: 10px; font-weight: bold;
            background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);
            border-radius: 4px; padding: 2px 8px;
        """)
        if session and session.role in ('broker', 'client'):
            self.role_badge.setText(session.role.upper())
        self.profile_lay.addWidget(self.role_badge, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.main_lay.addWidget(self.profile_container)
        self.update_profile()
        
        self.btns = []
        
        # Build menu based on role
        menu_items = self._get_menu_items()

        for icon, label, idx in menu_items:
            b = SidebarButton(icon, label, self)
            b.clicked.connect(lambda ch, i=idx, l=label: self.page_selected.emit(i, l))
            self.btns.append(b); self.main_lay.addWidget(b)
            
        self.main_lay.addStretch()

    def _get_menu_items(self):
        """Return menu items based on session role."""
        # Base items visible to all roles
        items = [
            ("📊", "Dashboard", 0),
            ("💰", "Prices", 1),
            ("🔍", "Search", 2),
            ("📁", "Portfolio", 3),
            ("📰", "News", 4),
            ("⚙️", "Settings", 5)
        ]
        # All roles see the same menu structure
        return items

    def update_profile(self):
        # Use session name if available, fall back to settings
        if self.session:
            name = self.session.user_name
        elif self.settings_manager:
            name = self.settings_manager.get("user_name") or "User"
        else:
            name = "User"
        
        path = ""
        if self.settings_manager:
            path = self.settings_manager.get("user_logo_path") or ""
        
        size = 40
        img = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(img)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw base circle
        painter.setBrush(QBrush(QColor("#1a1a2e")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, size, size)
        
        if path and os.path.exists(path):
            src = QImage(path).scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            mask = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
            mask.fill(Qt.GlobalColor.transparent)
            mp = QPainter(mask)
            mp.setRenderHint(QPainter.RenderHint.Antialiasing)
            mp.setBrush(QBrush(Qt.GlobalColor.white))
            mp.drawEllipse(0, 0, size, size)
            mp.end()
            
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawImage(0, 0, mask)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.drawImage(0, 0, src)
        else:
            painter.setPen(QColor("#10b981"))
            font = QFont("Segoe UI", 12, QFont.Weight.Bold)
            painter.setFont(font)
            initial = name[0].upper() if name else "U"
            painter.drawText(img.rect(), Qt.AlignmentFlag.AlignCenter, initial)
            
        painter.end()
        self.profile_pic.setPixmap(QPixmap.fromImage(img))
        self.profile_name.setText(name)

    def get_w(self): return self._w
    def set_w(self, v): self._w = v; self.setFixedWidth(int(v))
    anim_width = pyqtProperty(float, get_w, set_w)
    def toggle(self):
        self.is_ex = not self.is_ex; self.a = QPropertyAnimation(self, b"anim_width"); self.a.setDuration(200); self.a.setEndValue(200 if self.is_ex else 60); self.a.start()
        for b in self.btns: b.upd(self.is_ex)
        
        if self.is_ex:
            self.profile_pic.setFixedSize(80, 80)
            self.profile_name.setVisible(True)
            if self.session and self.session.role in ('broker', 'client'):
                self.role_badge.setVisible(True)
        else:
            self.profile_pic.setFixedSize(40, 40)
            self.profile_name.setVisible(False)
            self.role_badge.setVisible(False)
        self.update_profile()
