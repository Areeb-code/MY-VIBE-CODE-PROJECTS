"""
PSX Platform — Login Window & Setup Wizard
Professional dark-themed login screen with broker registration.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QGraphicsDropShadowEffect,
                             QMessageBox, QStackedWidget, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QColor, QFont, QIcon
from ..core.auth import authenticate, create_owner, register_broker, Session
from ..core.db import has_owner, init_db
from ..core.utils import get_asset_path


# ─── Styled Input Field ───────────────────────────────────────────────────────

class StyledInput(QLineEdit):
    """Dark themed input with optional password visibility toggle."""
    def __init__(self, placeholder="", is_password=False, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(50)
        self._is_password = is_password
        
        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            # Toggle Button (Eye icon)
            self.toggle_btn = QPushButton(self)
            self.toggle_btn.setFixedSize(30, 30)
            self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toggle_btn.setText("👁️")
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    color: rgba(255, 255, 255, 0.4);
                    font-size: 16px;
                }
                QPushButton:hover { color: #10b981; }
            """)
            self.toggle_btn.clicked.connect(self.toggle_visibility)
            
            # Position the button inside the QLineEdit
            self.setTextMargins(0, 0, 35, 0) # Right margin for button
        
        self.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                color: white;
                font-size: 15px;
                padding: 0 20px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid #10b981;
                background: rgba(16, 185, 129, 0.05);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.3);
            }
        """)

    def resizeEvent(self, e):
        if hasattr(self, 'toggle_btn'):
            self.toggle_btn.move(self.width() - 35, (self.height() - 30) // 2)
        super().resizeEvent(e)

    def toggle_visibility(self):
        if self.echoMode() == QLineEdit.EchoMode.Password:
            self.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("🙈")
        else:
            self.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("👁️")


# ─── Styled Button ────────────────────────────────────────────────────────────

class PrimaryButton(QPushButton):
    """Emerald green primary action button."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: 700;
                font-family: 'Segoe UI', sans-serif;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #047857);
            }
            QPushButton:pressed {
                background: #047857;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }
        """)


class LinkButton(QPushButton):
    """Subtle text-only link button."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #10b981;
                border: none;
                font-size: 13px;
                font-weight: 600;
                font-family: 'Segoe UI', sans-serif;
                padding: 5px;
            }
            QPushButton:hover {
                color: #34d399;
                text-decoration: underline;
            }
        """)


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP WIZARD (First Run — Owner account creation)
# ═══════════════════════════════════════════════════════════════════════════════

class SetupWizardPage(QWidget):
    """First-run wizard to create the system owner account."""
    setup_complete = pyqtSignal(object)  # Emits Session

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Card container
        card = QFrame()
        card.setFixedSize(420, 520)
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(40, 40, 40, 40)
        card_lay.setSpacing(15)

        # Icon
        icon_lbl = QLabel("🏗️")
        icon_lbl.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(icon_lbl)

        # Title
        title = QLabel("Initial Setup")
        title.setStyleSheet("""
            font-size: 24px; font-weight: 800; color: white; 
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(title)

        subtitle = QLabel("Create your system account to get started")
        subtitle.setStyleSheet("""
            font-size: 13px; color: rgba(255, 255, 255, 0.4);
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(subtitle)

        card_lay.addSpacing(10)

        self.name_input = StyledInput("Full Name")
        self.email_input = StyledInput("Email Address")
        self.password_input = StyledInput("Password", is_password=True)
        self.confirm_input = StyledInput("Confirm Password", is_password=True)

        card_lay.addWidget(self.name_input)
        card_lay.addWidget(self.email_input)
        card_lay.addWidget(self.password_input)
        card_lay.addWidget(self.confirm_input)

        card_lay.addSpacing(5)

        self.setup_btn = PrimaryButton("Create Account")
        self.setup_btn.clicked.connect(self._do_setup)
        card_lay.addWidget(self.setup_btn)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            color: #ef4444; font-size: 12px; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        card_lay.addWidget(self.error_label)

        card_lay.addStretch()
        layout.addWidget(card)

    def _do_setup(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not name or not email or not password:
            self.error_label.setText("All fields are required.")
            return

        if len(password) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        if '@' not in email or '.' not in email:
            self.error_label.setText("Please enter a valid email address.")
            return

        self.setup_btn.setEnabled(False)
        self.setup_btn.setText("Setting up...")

        session = create_owner(name, email, password)
        if session:
            self.setup_complete.emit(session)
        else:
            self.error_label.setText("Setup failed. Account may already exist.")
            self.setup_btn.setEnabled(True)
            self.setup_btn.setText("Create Account")


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN PAGE
# ═══════════════════════════════════════════════════════════════════════════════

class LoginPage(QWidget):
    """Login form with fields for username/email and password."""
    login_success = pyqtSignal(object)  # Emits Session
    switch_to_register = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        # Card container
        card = QFrame()
        card.setFixedSize(420, 450)
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(40, 40, 40, 40)
        card_lay.setSpacing(15)

        # Logo / Brand
        brand_lbl = QLabel("📊")
        brand_lbl.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        brand_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(brand_lbl)

        title = QLabel("PSX Market Tracker")
        title.setStyleSheet("""
            font-size: 22px; font-weight: 800; color: white;
            font-family: 'Georgia', serif; font-style: italic;
            background: transparent; border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(title)

        subtitle = QLabel("Sign in to continue")
        subtitle.setStyleSheet("""
            font-size: 13px; color: rgba(255, 255, 255, 0.4);
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(subtitle)

        card_lay.addSpacing(10)

        self.identifier_input = StyledInput("Username or Email")
        self.password_input = StyledInput("Password", is_password=True)
        self.password_input.returnPressed.connect(self._do_login)

        card_lay.addWidget(self.identifier_input)
        card_lay.addWidget(self.password_input)

        card_lay.addSpacing(5)

        self.login_btn = PrimaryButton("Sign In")
        self.login_btn.clicked.connect(self._do_login)
        card_lay.addWidget(self.login_btn)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            color: #ef4444; font-size: 12px; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        card_lay.addWidget(self.error_label)

        card_lay.addStretch()

        # Register link
        reg_link = LinkButton("New Broker? Register here →")
        reg_link.clicked.connect(self.switch_to_register.emit)
        card_lay.addWidget(reg_link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)

    def _do_login(self):
        identifier = self.identifier_input.text().strip()
        password = self.password_input.text()

        if not identifier or not password:
            self.error_label.setText("Please enter your credentials.")
            return

        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")

        session = authenticate(identifier, password)
        if session:
            self.error_label.setText("")
            self.login_success.emit(session)
        else:
            self.error_label.setText("Invalid credentials or account deactivated.")

        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")

    def clear_fields(self):
        """Reset the form for next login."""
        self.identifier_input.clear()
        self.password_input.clear()
        self.error_label.setText("")


# ═══════════════════════════════════════════════════════════════════════════════
#  BROKER REGISTRATION PAGE
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterPage(QWidget):
    """Broker self-registration form."""
    register_success = pyqtSignal(object)  # Emits Session
    switch_to_login = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setFixedSize(420, 560)
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 24px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 80))
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(40, 40, 40, 40)
        card_lay.setSpacing(15)

        icon_lbl = QLabel("📈")
        icon_lbl.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(icon_lbl)

        title = QLabel("Register as Broker")
        title.setStyleSheet("""
            font-size: 22px; font-weight: 800; color: white;
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(title)

        subtitle = QLabel("Create your broker account to manage clients")
        subtitle.setStyleSheet("""
            font-size: 13px; color: rgba(255, 255, 255, 0.4);
            font-family: 'Segoe UI', sans-serif; background: transparent; border: none;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_lay.addWidget(subtitle)

        card_lay.addSpacing(5)

        self.name_input = StyledInput("Full Name / Username")
        self.email_input = StyledInput("Email Address")
        self.password_input = StyledInput("Password", is_password=True)
        self.confirm_input = StyledInput("Confirm Password", is_password=True)

        card_lay.addWidget(self.name_input)
        card_lay.addWidget(self.email_input)
        card_lay.addWidget(self.password_input)
        card_lay.addWidget(self.confirm_input)

        card_lay.addSpacing(5)

        self.register_btn = PrimaryButton("Create Broker Account")
        self.register_btn.clicked.connect(self._do_register)
        card_lay.addWidget(self.register_btn)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("""
            color: #ef4444; font-size: 12px; background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        card_lay.addWidget(self.error_label)

        card_lay.addStretch()

        back_link = LinkButton("← Back to Sign In")
        back_link.clicked.connect(self.switch_to_login.emit)
        card_lay.addWidget(back_link, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(card)

    def _do_register(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()

        if not name or not email or not password:
            self.error_label.setText("All fields are required.")
            return

        if len(password) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return

        if password != confirm:
            self.error_label.setText("Passwords do not match.")
            return

        if '@' not in email or '.' not in email:
            self.error_label.setText("Please enter a valid email address.")
            return

        self.register_btn.setEnabled(False)
        self.register_btn.setText("Creating account...")

        result = register_broker(name, email, password)
        if result['success']:
            self.error_label.setText("")
            self.register_success.emit(result['session'])
        else:
            self.error_label.setText(result['error'])

        self.register_btn.setEnabled(True)
        self.register_btn.setText("Create Broker Account")


# ═══════════════════════════════════════════════════════════════════════════════
#  LOGIN WINDOW (Container for all auth pages)
# ═══════════════════════════════════════════════════════════════════════════════

class LoginWindow(QWidget):
    """
    Main authentication window containing:
    - Setup wizard (first run only)
    - Login page
    - Broker registration page
    """
    auth_success = pyqtSignal(object)  # Emits Session to main app

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PSX Market Tracker — Sign In")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))

        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #09090b, stop:0.5 #0c1220, stop:1 #09090b);
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Page 0: Setup Wizard (only if no owner)
        self.setup_page = SetupWizardPage()
        self.setup_page.setup_complete.connect(self._on_setup_complete)

        # Page 1: Login
        self.login_page = LoginPage()
        self.login_page.login_success.connect(self._on_login)
        self.login_page.switch_to_register.connect(self._show_register)

        # Page 2: Register
        self.register_page = RegisterPage()
        self.register_page.register_success.connect(self._on_login)
        self.register_page.switch_to_login.connect(self._show_login)

        self.stack.addWidget(self.setup_page)   # 0
        self.stack.addWidget(self.login_page)    # 1
        self.stack.addWidget(self.register_page) # 2

        # Decide which page to show first
        if has_owner():
            self.stack.setCurrentIndex(1)  # Login
        else:
            self.stack.setCurrentIndex(0)  # Setup wizard

    def _on_setup_complete(self, session):
        """Owner account created. Go to main app directly."""
        self.auth_success.emit(session)

    def _on_login(self, session):
        """Authentication successful. Transition to main app."""
        self.auth_success.emit(session)

    def _show_register(self):
        self.stack.setCurrentIndex(2)

    def _show_login(self):
        self.stack.setCurrentIndex(1)

    def reset_for_logout(self):
        """Reset to login page on logout."""
        self.login_page.clear_fields()
        self.stack.setCurrentIndex(1)
        self.show()
