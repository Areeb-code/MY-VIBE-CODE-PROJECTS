import os
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
                             QSpinBox, QComboBox, QCheckBox, QPushButton, QLabel, 
                             QDialogButtonBox, QGraphicsDropShadowEffect, QTextBrowser, QMessageBox)
from PyQt6.QtCore import Qt, QEvent, QTimer, QRect, QSize, QRectF
from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QBrush, QImage, QIcon, QPen

from ..core.utils import get_resource_path, get_asset_path, get_legal_path
from ..core.auth import ROLE_OWNER, ROLE_BROKER, ROLE_CLIENT, change_password
from .login_window import StyledInput
from PyQt6.QtWidgets import QFileDialog

class ProfilePicButton(QPushButton):
    """Circular profile picture button with hover camera icon."""
    def __init__(self, size=120, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hover = False
        self.img_path = ""
        self.user_name = ""

    def set_data(self, path, name):
        self.img_path = path
        self.user_name = name
        self.update()

    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        size = self.width()
        rect = QRect(0, 0, size, size)
        
        # Draw base circle
        painter.setBrush(QBrush(QColor("#1a1a2e")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)
        
        # Draw image or initial
        if self.img_path and os.path.exists(self.img_path):
            img = QImage(self.img_path)
            img = img.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            
            mask = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
            mask.fill(Qt.GlobalColor.transparent)
            mp = QPainter(mask)
            mp.setRenderHint(QPainter.RenderHint.Antialiasing)
            mp.setBrush(QBrush(Qt.GlobalColor.white))
            mp.drawEllipse(0, 0, size, size)
            mp.end()
            
            output = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
            output.fill(Qt.GlobalColor.transparent)
            op = QPainter(output)
            op.setRenderHint(QPainter.RenderHint.Antialiasing)
            op.drawImage(0, 0, mask)
            op.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            op.drawImage(0, 0, img)
            op.end()
            painter.drawImage(0, 0, output)
        else:
            painter.setPen(QColor("#10b981"))
            font = QFont("Segoe UI", size // 3, QFont.Weight.Bold)
            painter.setFont(font)
            initial = self.user_name[0].upper() if self.user_name else "A"
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, initial)
            
        # Draw bold greenish border (#10b981, 5px)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.setPen(QPen(QColor("#10b981"), 5))
        painter.drawEllipse(QRectF(2.5, 2.5, size-5, size-5))
        
        # Draw camera overlay on hover
        if self._hover:
            overlay_color = QColor(0, 0, 0, 150)
            painter.setBrush(QBrush(overlay_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Segoe UI", size // 6))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "📷")
        painter.end()

class SettingsDialog(QDialog):
    """A professional WhatsApp-style dialog window for editing user settings."""
    def __init__(self, parent, settings_manager, session=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.session = session
        self.parent_app = parent
        
        if self.session and self.session.role == ROLE_OWNER:
            self.setWindowTitle("System Settings")
        else:
            self.setWindowTitle("Settings")
            
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))
        self.setFixedSize(500, 750)
        
        self.setStyleSheet("""
            QDialog { background-color: #0c0d14; color: white; }
            QLabel { color: rgba(255, 255, 255, 0.7); font-size: 13px; }
            QLineEdit { 
                background: transparent; border: none; border-bottom: 2px solid #333; 
                color: white; font-size: 18px; padding: 5px 0; font-weight: bold;
            }
            QLineEdit:focus { border-bottom: 2px solid #10b981; }
            QCheckBox { color: rgba(255, 255, 255, 0.8); font-size: 13px; spacing: 10px; }
            QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #333; border-radius: 4px; }
            QCheckBox::indicator:checked { background: #10b981; border: 2px solid #10b981; }
            QSpinBox, QComboBox {
                background-color: #1a1a2e; color: white; border-radius: 5px; padding: 5px 10px;
            }
        """)
        
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(40, 40, 40, 40)
        main_lay.setSpacing(15)
        
        # Profile Section
        profile_lay = QVBoxLayout()
        profile_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile_lay.setSpacing(10)
        
        self.profile_btn = ProfilePicButton(120)
        self.profile_btn.set_data(self.settings_manager.get("user_logo_path"), self.session.user_name if self.session else self.settings_manager.get("user_name"))
        self.profile_btn.clicked.connect(self.change_photo)
        profile_lay.addWidget(self.profile_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Name editing section
        name_container = QHBoxLayout()
        name_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_container.setSpacing(10)
        
        display_name = self.session.user_name if self.session else self.settings_manager.get("user_name")
        self.name_edit = QLineEdit(display_name)
        self.name_edit.setFixedWidth(200)
        self.name_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_edit.setReadOnly(True) 
        self.name_edit.setStyleSheet("QLineEdit { background: transparent; border: none; border-bottom: 2px solid rgba(255,255,255,0.1); color: white; font-size: 18px; font-weight: bold; font-family: Georgia, serif; font-style: italic; } QLineEdit:focus { border-bottom: 2px solid #10b981; }")
        
        # Only allow changing name locally in settings if not using auth purely,
        # but with the new DB, name is in DB. For now, editing name here updates the DB for that user natively?
        # Let's keep it simple: Name changes in DB are complex (need DB write), so we'll just allow display name change in settings.json 
        # or disable name editing if logged in.
        if self.session:
            self.name_edit.setToolTip("Account name cannot be changed here.")
            self.name_edit.setStyleSheet("QLineEdit { background: transparent; border: none; border-bottom: none; color: white; font-size: 18px; font-weight: bold; font-family: Georgia, serif; font-style: italic; }")
            name_container.addWidget(self.name_edit)
        else:
            self.edit_btn = QPushButton("✏️")
            self.edit_btn.setFixedSize(30, 30)
            self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.edit_btn.setStyleSheet("QPushButton { font-size: 16px; border: none; background: transparent; color: rgba(255,255,255,0.4); } QPushButton:hover { color: #10b981; }")
            self.edit_btn.clicked.connect(self.enable_rename)
            name_container.addWidget(self.name_edit)
            name_container.addWidget(self.edit_btn)
            
        profile_lay.addLayout(name_container)
        
        role_label = QLabel()
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.session:
            if self.session.role == ROLE_OWNER:
                role_label.setText("System Administrator")
                role_label.setStyleSheet("color: #8b5cf6; font-weight: bold;")
            elif self.session.role == ROLE_BROKER:
                role_label.setText("Broker Account")
                role_label.setStyleSheet("color: #3b82f6; font-weight: bold;")
            else:
                role_label.setText("Client Account")
                role_label.setStyleSheet("color: #10b981; font-weight: bold;")
        profile_lay.addWidget(role_label)
        
        main_lay.addLayout(profile_lay)
        main_lay.addSpacing(10)
        
        # Security Section (Change Password)
        if self.session:
            sec_lay = QHBoxLayout()
            self.pwd_btn = QPushButton("🔑 Change Password")
            self.pwd_btn.setFixedHeight(35)
            self.pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.pwd_btn.setStyleSheet("""
                QPushButton { background-color: rgba(255,255,255,0.05); color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; font-weight: bold; padding: 0 15px; }
                QPushButton:hover { background-color: rgba(255,255,255,0.1); border: 1px solid white; }
            """)
            self.pwd_btn.clicked.connect(self.prompt_change_password)
            sec_lay.addWidget(self.pwd_btn)
            sec_lay.addStretch()
            main_lay.addLayout(sec_lay)
            main_lay.addSpacing(10)
            
        # Role-Specific Management Buttons
        if self.session and self.session.role in (ROLE_BROKER, ROLE_OWNER):
            mgmt_lay = QHBoxLayout()
            
            if self.session.role == ROLE_BROKER:
                self.manage_btn = QPushButton("👥 Manage Clients")
                self.manage_btn.clicked.connect(self.open_client_manager)
            else:
                self.manage_btn = QPushButton("🏢 Manage Brokers")
                self.manage_btn.clicked.connect(self.open_broker_manager)
                
            self.manage_btn.setFixedHeight(40)
            self.manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.manage_btn.setStyleSheet("""
                QPushButton { background-color: #3b82f6; color: white; border: none; border-radius: 8px; font-weight: 800; padding: 0 20px;}
                QPushButton:hover { background-color: #2563eb; }
            """)
            mgmt_lay.addWidget(self.manage_btn)
            main_lay.addLayout(mgmt_lay)
            main_lay.addSpacing(10)
        
        # Global Settings
        opts_lay = QVBoxLayout()
        opts_lay.setSpacing(12)
        
        self.bg_check = QCheckBox("Run in background when closed")
        self.bg_check.setChecked(self.settings_manager.get("run_in_background"))
        
        self.notif_check = QCheckBox("Enable price alerts & notifications")
        self.notif_check.setChecked(self.settings_manager.get("notifications_enabled"))
        
        self.auto_check = QCheckBox("Auto-save platform data")
        self.auto_check.setChecked(self.settings_manager.get("auto_save_portfolio"))
        
        cb_style = f"""
            QCheckBox {{ color: white; font-size: 14px; spacing: 12px; padding: 2px; font-weight: 500;}}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid #10b981; border-radius: 4px; background: #1a1a2e; }}
            QCheckBox::indicator:checked {{ 
                background: #10b981; 
                image: url("{get_resource_path('assets/check.png').replace('\\', '/')}");
            }}
        """
        self.bg_check.setStyleSheet(cb_style)
        self.notif_check.setStyleSheet(cb_style)
        self.auto_check.setStyleSheet(cb_style)
        
        opts_lay.addWidget(self.bg_check)
        opts_lay.addWidget(self.notif_check)
        opts_lay.addWidget(self.auto_check)
        
        main_lay.addLayout(opts_lay)
        
        # Display/Behavior Properties
        form = QFormLayout()
        form.setVerticalSpacing(15)
        
        self.refresh_sp = QSpinBox()
        self.refresh_sp.setRange(10, 3600); self.refresh_sp.setValue(self.settings_manager.get("refresh_interval"))
        self.refresh_sp.setSuffix("s")
        self.refresh_sp.setStyleSheet("QSpinBox { font-size: 14px; }")
        form.addRow("Data Sync Interval:", self.refresh_sp)
        
        self.theme_cb = QComboBox()
        self.theme_cb.addItems(["Dark (Default)", "Light"])
        self.theme_cb.setCurrentText(self.settings_manager.get("theme"))
        self.theme_cb.setStyleSheet("""
            QComboBox { 
                background: #1a1a2e; 
                border: 1px solid rgba(255,255,255,0.1); 
                padding: 5px 10px; 
                border-radius: 5px;
                color: white;
                font-size: 14px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: white;
                selection-background-color: #10b981;
                border: 1px solid #10b981;
                outline: none;
            }
        """)
        form.addRow("Application Theme:", self.theme_cb)
        
        main_lay.addLayout(form)
        
        main_lay.addStretch()
        
        # Footer buttons
        btn_lay = QHBoxLayout()
        
        self.about_btn = QPushButton("ℹ️ About")
        self.about_btn.setFixedSize(100, 40)
        self.about_btn.clicked.connect(self.show_about_dialog)
        self.about_btn.setStyleSheet("background: rgba(255,255,255,0.05); color: white; border: 1px solid #333; border-radius: 8px;")
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setFixedHeight(40)
        self.save_btn.clicked.connect(self.save_and_close)
        self.save_btn.setStyleSheet("background: #10b981; color: white; border-radius: 8px; font-weight: bold; padding: 0 20px;")
        
        btn_lay.addWidget(self.about_btn)
        btn_lay.addStretch()
        btn_lay.addWidget(self.save_btn)
        
        main_lay.addLayout(btn_lay)

    def enable_rename(self):
        self.name_edit.setReadOnly(False)
        self.name_edit.setFocus()
        self.name_edit.setStyleSheet("QLineEdit { background: transparent; border: none; border-bottom: 2px solid #10b981; color: white; font-size: 18px; font-weight: bold; }")

    def change_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Change Profile Photo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.settings_manager.set("user_logo_path", path)
            self.profile_btn.set_data(path, self.name_edit.text())

    def prompt_change_password(self):
        # Professional custom password change dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Change Password")
        dialog.setFixedWidth(400)
        dialog.setStyleSheet("QDialog { background-color: #0c0d14; color: white; }")
        
        lay = QVBoxLayout(dialog)
        lay.setContentsMargins(30, 30, 30, 30); lay.setSpacing(15)
        
        title = QLabel("Update Security Credentials")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        lay.addWidget(title)
        
        old_pwd = StyledInput("Current Password", is_password=True)
        new_pwd = StyledInput("New Password", is_password=True)
        conf_pwd = StyledInput("Confirm New Password", is_password=True)
        
        for inp in [old_pwd, new_pwd, conf_pwd]:
            lay.addWidget(inp)
            
        err_lbl = QLabel("")
        err_lbl.setStyleSheet("color: #ef4444; font-size: 11px;")
        lay.addWidget(err_lbl)
        
        btn_lay = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet("background: transparent; color: rgba(255,255,255,0.4); border: none;")
        
        save_btn = QPushButton("Update Password")
        save_btn.setStyleSheet("background: #10b981; color: white; border-radius: 8px; font-weight: bold; padding: 10px 20px;")
        
        def do_update():
            if not old_pwd.text() or not new_pwd.text():
                err_lbl.setText("Fields cannot be empty.")
                return
            if new_pwd.text() != conf_pwd.text():
                err_lbl.setText("New passwords do not match.")
                return
            
            success, msg = change_password(self.session.user_id, old_pwd.text(), new_pwd.text())
            if success:
                QMessageBox.information(self, "Success", "Password updated successfully.")
                dialog.accept()
            else:
                err_lbl.setText(msg)
        
        save_btn.clicked.connect(do_update)
        
        btn_lay.addStretch()
        btn_lay.addWidget(cancel_btn)
        btn_lay.addWidget(save_btn)
        lay.addLayout(btn_lay)
        
        dialog.exec()

    def open_client_manager(self):
        from .client_manager_dialog import ClientManagerDialog
        dialog = ClientManagerDialog(self.session, self)
        dialog.exec()

    def open_broker_manager(self):
        from .client_manager_dialog import BrokerManagerDialog
        dialog = BrokerManagerDialog(self.session, self)
        dialog.exec()

    def save_and_close(self):
        if not self.session:
            self.settings_manager.set("user_name", self.name_edit.text())
            
        self.settings_manager.set("refresh_interval", self.refresh_sp.value())
        self.settings_manager.set("theme", self.theme_cb.currentText())
        self.settings_manager.set("run_in_background", self.bg_check.isChecked())
        self.settings_manager.set("notifications_enabled", self.notif_check.isChecked())
        self.settings_manager.set("auto_save_portfolio", self.auto_check.isChecked())
        self.settings_manager.save_settings()
        self.accept()

    def show_about_dialog(self):
        AboutLegalDialog(self).exec()

class AboutLegalDialog(QDialog):
    """A professional modal dialog for software information and licensing."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Software Information & License")
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #0f1419; color: white; }
            QLabel { color: white; background: transparent; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        header_lay = QHBoxLayout()
        app_info = QVBoxLayout()
        app_title = QLabel("PSX Tracker Pro")
        app_title.setStyleSheet("font-size: 28px; font-weight: 800; color: #10b981;")
        version = QLabel("Version 1.0.4 - Professional Edition")
        version.setStyleSheet("font-size: 14px; color: rgba(255,255,255,0.6);")
        app_info.addWidget(app_title)
        app_info.addWidget(version)
        
        logo_lbl = QLabel("📊")
        logo_lbl.setStyleSheet("font-size: 48px; padding-right: 10px;")
        
        header_lay.addWidget(logo_lbl)
        header_lay.addLayout(app_info)
        header_lay.addStretch()
        main_layout.addLayout(header_lay)
        
        owner = QLabel("© 2026 Areeb Siddiqui. All Rights Reserved.")
        owner.setStyleSheet("font-size: 13px; font-weight: 600; color: #10b981;")
        main_layout.addWidget(owner)
        
        self.legal_browser = QTextBrowser()
        self.legal_browser.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 10px;
                color: rgba(255,255,255,0.8);
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 15px;
            }
        """)
        
        legal_text = "Legal terms file not found."
        try:
            legal_path = get_legal_path("legal_terms.txt")
            if os.path.exists(legal_path):
                with open(legal_path, "r", encoding="utf-8") as f:
                    legal_text = f.read()
            else:
                legal_text = f"Legal file not found at: {legal_path}"
        except Exception as e:
            legal_text = f"Error loading legal terms: {str(e)}"
            
        self.legal_browser.setText(legal_text)
        main_layout.addWidget(self.legal_browser)
        
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.setFixedSize(120, 40)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.accept)
        
        self.close_btn.setStyleSheet("""
            QPushButton { background-color: #1a1a2e; color: white; border: 1px solid #333; border-radius: 8px; font-size: 13px; font-weight: bold; }
            QPushButton:hover { background-color: #222; border: 1px solid #10b981; }
        """)
        self.close_shadow = QGraphicsDropShadowEffect(self.close_btn)
        self.close_shadow.setBlurRadius(0); self.close_shadow.setOffset(0, 0); self.close_shadow.setColor(QColor(16, 185, 129, 0))
        self.close_btn.setGraphicsEffect(self.close_shadow)
        self.close_btn.installEventFilter(self)
        
        btn_lay.addWidget(self.close_btn)
        main_layout.addLayout(btn_lay)

    def eventFilter(self, obj, event):
        if obj == self.close_btn:
            if event.type() == QEvent.Type.Enter:
                self.close_shadow.setBlurRadius(15); self.close_shadow.setOffset(0, 3); self.close_shadow.setColor(QColor(16, 185, 129, 100))
            elif event.type() == QEvent.Type.Leave:
                self.close_shadow.setBlurRadius(0); self.close_shadow.setOffset(0, 0); self.close_shadow.setColor(QColor(16, 185, 129, 0))
        return super().eventFilter(obj, event)
