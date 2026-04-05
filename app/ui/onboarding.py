import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFileDialog, QGraphicsDropShadowEffect, 
                             QGraphicsBlurEffect, QCheckBox, QFrame)
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QRect, QTimer, pyqtSignal, QEasingCurve, QSize, QRectF
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QBrush, QImage, QIcon, QPainterPath, QPen
from ..core.utils import get_resource_path
from .login_window import StyledInput
from ..core.db import has_owner
from ..core.auth import create_owner


class NeuroLabel(QLabel):
    """A premium label with internal entrance blur and breathing neon glow."""
    def __init__(self, text="", font_size=28, is_serif=True, color="#ffffff", glow_color=None, entrance_delay=0, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Force strict transparency and no border to prevent "boxy" glows
        font_family = "'Times New Roman', serif" if is_serif else "'Segoe UI', sans-serif"
        font_style = "italic" if is_serif else "normal"
        self.setStyleSheet(f"""
            QLabel {{
                font-size: {font_size}px; 
                font-weight: bold; 
                font-family: {font_family}; 
                font-style: {font_style};
                color: {color}; 
                border: none; 
                background: transparent; 
                letter-spacing: 1px;
            }}
        """)
        
        self._glow_color = glow_color or QColor(16, 185, 129, 200) # Soft Cyan/Green Neon
        
        # 1. Start with Entrance Blur
        self._eff = QGraphicsBlurEffect()
        self.setGraphicsEffect(self._eff)
        
        self.blur_anim = QPropertyAnimation(self._eff, b"blurRadius")
        self.blur_anim.setDuration(800)
        self.blur_anim.setStartValue(20.0) # Soft start for better partial visibility
        self.blur_anim.setEndValue(0.0)
        self.blur_anim.setEasingCurve(QEasingCurve.Type.OutQuart)
        
        self.blur_anim.finished.connect(self.start_breathing)
        QTimer.singleShot(entrance_delay, self.blur_anim.start)

    def start_breathing(self):
        # Switch to Glow Effect
        self._glow = QGraphicsDropShadowEffect()
        self._glow.setBlurRadius(20)
        self._glow.setOffset(0, 0)
        self._glow.setColor(self._glow_color)
        self.setGraphicsEffect(self._glow)
        
        # Pulse the glow (breathing)
        self.pulse = QPropertyAnimation(self._glow, b"blurRadius")
        self.pulse.setDuration(1500)
        self.pulse.setStartValue(12.0)
        self.pulse.setEndValue(30.0)
        self.pulse.setEasingCurve(QEasingCurve.Type.InOutSine)
        self.pulse.setLoopCount(-1)
        self.pulse.start()
class GlowButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background: #1a1a2e; color: white; border: 2px solid #10b981; border-radius: 12px; font-weight: bold; font-size: 16px;
            }
            QPushButton:hover { background: #21213a; border-color: #0d9668; }
        """)
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(16, 185, 129, 0))
        self.setGraphicsEffect(self.shadow)

    def enterEvent(self, e):
        self.shadow.setBlurRadius(25)
        self.shadow.setOffset(0, 4) # Glow Below
        self.shadow.setColor(QColor(16, 185, 129, 200)) # Grounded neon
        super().enterEvent(e)
        
    def leaveEvent(self, e):
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(16, 185, 129, 0))
        super().leaveEvent(e)

class OnboardingWindow(QWidget):
    finished = pyqtSignal()

    def __init__(self, settings_manager):
        super().__init__()
        self.settings_manager = settings_manager
        self.setWindowTitle("Welcome to PSX Market Tracker")
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.step = 1
        self.user_name = settings_manager.get("user_name")
        self.logo_path = ""
        
        self.init_ui()
        
    def init_ui(self):
        self.bg = QFrame(self)
        self.bg.setGeometry(0, 0, 800, 600)
        self.bg.setStyleSheet("""
            QFrame { 
                background-color: #0f0f1a; 
                border-radius: 20px; 
            }
        """)
        
        self.layout = QVBoxLayout(self.bg)
        self.layout.setContentsMargins(50, 50, 50, 50)
        
        self.content_stack = QWidget()
        self.content_layout = QVBoxLayout(self.content_stack)
        self.layout.addWidget(self.content_stack)
        
        self.show_step_1()

    def clear_layout(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.name_edit = None # Nullify stale references

    def show_step_1(self):
        self.clear_layout()
        self.content_layout.addStretch()
        
        # Neurophoric Header: [Welcome to] [PSX] [Market Tracker]
        header_container = QWidget()
        header_lay = QHBoxLayout(header_container)
        header_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_lay.setSpacing(12)
        
        # Static Parts
        w1 = QLabel("Welcome to")
        w1.setStyleSheet("font-size: 38px; font-weight: bold; font-family: 'Times New Roman', serif; font-style: italic; color: white;")
        w2 = QLabel("Market Tracker")
        w2.setStyleSheet("font-size: 38px; font-weight: bold; font-family: 'Times New Roman', serif; font-style: italic; color: white;")
        
        # The NEUROPHORIC trademark (Localized Glow)
        self.psx_lbl = NeuroLabel("PSX", font_size=42, is_serif=True, color="#10b981")
        
        header_lay.addWidget(w1); header_lay.addWidget(self.psx_lbl); header_lay.addWidget(w2)
        
        self.content_layout.addWidget(header_container)
        self.content_layout.addStretch()
        
        self.journey_btn = GlowButton("Begin Journey")
        self.journey_btn.setFixedSize(200, 50); self.journey_btn.clicked.connect(self.transition_to_step_2)
        self.content_layout.addWidget(self.journey_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Entrance animations for individual pieces to avoid QGraphicsEffect collisions
        self.animate_label_blur(w1); self.animate_label_blur(w2)
        # Note: NeuroLabel handles its own entrance/breathing safely.
        
    def animate_label_blur(self, label):
        blur = QGraphicsBlurEffect()
        label.setGraphicsEffect(blur)
        anim = QPropertyAnimation(blur, b"blurRadius")
        anim.setDuration(800); anim.setStartValue(30.0); anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutQuart)
        anim.start()
        # Keep reference to avoid GC
        if not hasattr(self, '_anims'): self._anims = []
        self._anims.append((anim, blur))

    def animate_welcome_entry(self):
        # Fade in the whole window once on startup
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(500); self.fade_anim.setStartValue(0.0); self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()
        self.raise_(); self.activateWindow()

    def animate_step_entry(self, widget):
        # Apply Gaussian Blur Entry for any widget (especially titles)
        blur = QGraphicsBlurEffect()
        widget.setGraphicsEffect(blur)
        
        anim = QPropertyAnimation(blur, b"blurRadius")
        anim.setDuration(400)
        anim.setStartValue(20.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        # Keep reference
        widget._blur_anim = anim

    def transition_to_step_2(self):
        self.blur_out(self.show_step_2)

    def transition_back_to_step_1(self):
        # Save current state before clearing
        if self.name_edit:
            try: self.user_name = self.name_edit.text()
            except: pass
        self.blur_out(self.show_step_1)

    def transition_back_to_step_2(self):
        self.blur_out(self.show_step_2)

    def transition_to_step_3(self):
        if self.name_edit:
            try: self.user_name = self.name_edit.text()
            except: pass
        self.blur_out(self.show_step_3)

    def blur_out(self, callback):
        # Remove screen-wide blur, just switch steps immediately or use a lighter fade
        self.opacity_anim_out = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim_out.setDuration(300)
        self.opacity_anim_out.setStartValue(1.0)
        self.opacity_anim_out.setEndValue(0.0)
        self.opacity_anim_out.finished.connect(lambda: self.finish_fade_out(callback))
        self.opacity_anim_out.start()

    def finish_fade_out(self, callback):
        callback()
        self.opacity_anim_in = QPropertyAnimation(self, b"windowOpacity")
        self.opacity_anim_in.setDuration(300)
        self.opacity_anim_in.setStartValue(0.0)
        self.opacity_anim_in.setEndValue(1.0)
        self.opacity_anim_in.start()

    def finish_blur_out(self, callback, effect):
        # Kept for compatibility if called elsewhere, but we prefer fade
        callback()

    def show_step_2(self):
        self.clear_layout()
        
        # Header with Back button and Title
        header_lay = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(80, 40)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("QPushButton { color: rgba(255,255,255,0.4); border: none; background: transparent; font-size: 14px; text-align: left; } QPushButton:hover { color: #10b981; }")
        back_btn.clicked.connect(self.transition_back_to_step_1)
        header_lay.addWidget(back_btn)
        header_lay.addStretch()
        self.content_layout.addLayout(header_lay)
        
        title = NeuroLabel("Who are we tracking for?", color="#ffffff")
        self.content_layout.addWidget(title)
        # NeuroLabel handles its own entrance blur-in. No external group needed.
        
        self.profile_btn = QPushButton()
        self.profile_btn.setFixedSize(120, 120)
        self.profile_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_profile_preview()
        self.profile_btn.clicked.connect(self.pick_logo)
        
        self.content_layout.addSpacing(20)
        self.content_layout.addWidget(self.profile_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        note = QLabel("Click the circle to upload your professional logo/photo")
        note.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.4);")
        self.content_layout.addWidget(note, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.name_edit = QLineEdit(self.user_name)
        self.name_edit.setPlaceholderText("Enter your name...")
        self.name_edit.setFixedSize(300, 45)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background: #1a1a2e; color: white; border: 1px solid #333; 
                border-radius: 8px; padding: 0 15px; font-size: 16px;
            }
            QLineEdit:focus { border: 1px solid #10b981; }
        """)
        self.content_layout.addSpacing(30)
        self.content_layout.addWidget(self.name_edit, alignment=Qt.AlignmentFlag.AlignCenter)

        # Admin Setup Fields (if needed)
        if self.step == 2 and not has_owner():
            self.email_edit = StyledInput("Admin Email")
            self.email_edit.setFixedWidth(300)
            self.pwd_edit = StyledInput("Admin Password", is_password=True)
            self.pwd_edit.setFixedWidth(300)
            self.content_layout.addWidget(self.email_edit, alignment=Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(self.pwd_edit, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.content_layout.addStretch()
        
        next_btn = GlowButton("Continue")
        next_btn.setFixedSize(200, 45)
        next_btn.setStyleSheet("/* Styles handled by GlowButton */")
        next_btn.clicked.connect(self.transition_to_step_3)
        self.content_layout.addWidget(next_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def update_profile_preview(self):
        size = 120
        # Create final pixmap
        final_px = QPixmap(size, size)
        final_px.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(final_px)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circular mask path
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        
        if self.logo_path and os.path.exists(self.logo_path):
            img = QImage(self.logo_path)
            img = img.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            painter.drawImage(0, 0, img)
        else:
            painter.setBrush(QBrush(QColor("#1a1a2e")))
            painter.drawEllipse(0, 0, size, size)
            painter.setPen(QColor("#10b981"))
            font = QFont("Segoe UI", 48, QFont.Weight.Bold)
            painter.setFont(font)
            # Ensure name_edit exists and is not deleted safely
            name_text = self.user_name
            if self.name_edit:
                try: name_text = self.name_edit.text()
                except: pass
            initial = name_text[0].upper() if name_text else "A"
            painter.drawText(final_px.rect(), Qt.AlignmentFlag.AlignCenter, initial)
        
        # Draw bold greenish border (#10b981, 5px)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#10b981"), 5))
        painter.drawEllipse(QRectF(2.5, 2.5, size-5, size-5))
        
        painter.end()
        
        self.profile_btn.setIcon(QIcon(final_px))
        self.profile_btn.setIconSize(QSize(size, size))
        self.profile_btn.setStyleSheet("border: none; background: transparent;")

    def pick_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.logo_path = path
            self.update_profile_preview()


    def show_step_3(self):
        self.clear_layout()
        
        # Header with Back button and Title
        header_lay = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(80, 40)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("QPushButton { color: rgba(255,255,255,0.4); border: none; background: transparent; font-size: 14px; text-align: left; } QPushButton:hover { color: #10b981; }")
        back_btn.clicked.connect(self.transition_back_to_step_2)
        header_lay.addWidget(back_btn)
        header_lay.addStretch()
        self.content_layout.addLayout(header_lay)

        title = NeuroLabel("Let's tweak your setup", color="#ffffff")
        self.content_layout.addWidget(title)
        # NeuroLabel handles its own entrance blur-in. No external group needed.
        
        self.content_layout.addSpacing(40)
        
        # Settings checkboxes
        self.cb_bg = QCheckBox("Run in Background (Keep tracking when closed)")
        self.cb_notif = QCheckBox("Enable Price Alerts & Notifications")
        self.cb_autosave = QCheckBox("Auto-save Portfolio changes")
        
        def style_cb(cb, checked):
            cb.setChecked(checked)
            cb.setStyleSheet(f"""
                QCheckBox {{ color: white; font-size: 16px; spacing: 15px; padding: 12px; font-weight: 500;}}
                QCheckBox::indicator {{ width: 22px; height: 22px; border: 2px solid #10b981; border-radius: 6px; background: #1a1a2e; }}
                QCheckBox::indicator:checked {{ 
                    background: #10b981; 
                    image: url("{get_resource_path('assets/check.png').replace('\\', '/')}");
                    padding: 5px;
                }}
                QCheckBox::indicator:unchecked:hover {{ border: 2px solid #0d9668; }}
            """)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(0); shadow.setOffset(0,0); shadow.setColor(QColor(16, 185, 129, 200))
            cb.setGraphicsEffect(shadow)
            cb.stateChanged.connect(lambda state: self.animate_check(cb, shadow, state))

        style_cb(self.cb_bg, self.settings_manager.get("run_in_background"))
        style_cb(self.cb_notif, self.settings_manager.get("notifications_enabled"))
        style_cb(self.cb_autosave, self.settings_manager.get("auto_save_portfolio"))
        
        self.content_layout.addWidget(self.cb_bg)
        self.content_layout.addWidget(self.cb_notif)
        self.content_layout.addWidget(self.cb_autosave)
        
        self.content_layout.addStretch()
        
        finish_btn = GlowButton("Finalize & Launch 🚀")
        finish_btn.setFixedSize(250, 50)
        finish_btn.clicked.connect(self.finalize)
        self.content_layout.addWidget(finish_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def animate_check(self, cb, glow, state):
        anim = QPropertyAnimation(glow, b"blurRadius")
        anim.setDuration(300)
        if state == 2: # Checked
            anim.setStartValue(0); anim.setEndValue(15)
        else:
            anim.setStartValue(15); anim.setEndValue(0)
        anim.start()
        # To prevent GC
        cb._anim = anim

    def finalize(self):
        # If no owner exists, create one now using the provided name, email, and password
        if not has_owner():
            email = getattr(self, 'email_edit', None)
            pwd = getattr(self, 'pwd_edit', None)
            if email and pwd:
                e_text = email.text().strip()
                p_text = pwd.text()
                if e_text and p_text:
                    create_owner(self.user_name, e_text, p_text)

        self.settings_manager.set("user_name", self.user_name)
        self.settings_manager.set("user_logo_path", self.logo_path)
        self.settings_manager.set("run_in_background", self.cb_bg.isChecked())
        self.settings_manager.set("notifications_enabled", self.cb_notif.isChecked())
        self.settings_manager.set("auto_save_portfolio", self.cb_autosave.isChecked())
        self.settings_manager.set("first_run", False)
        self.settings_manager.save_settings()
        
        # System Ready Animation - disappear faster
        self.hide()
        self.finished.emit()
