import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.ui.splash_screen import SplashScreen
from app.ui.main_window import MainApp
from app.ui.login_window import LoginWindow
from app.ui.dialogs import get_asset_path
from app.core.managers import SettingsManager
from app.core.db import init_db

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PSX Market Tracker")
    app.setApplicationDisplayName("PSX Market Tracker")
    app.setWindowIcon(QIcon(get_asset_path("icon.png")))
    
    # Initialize the database (creates tables if first run)
    init_db()
    
    # Keep references to prevent garbage collection
    win = None
    login_win = None
    
    sm = SettingsManager()
    
    def show_main(session):
        nonlocal win, login_win
        if login_win:
            login_win.hide()
        win = MainApp(session=session)
        win.logout_requested.connect(handle_logout)
        win.show()
    
    def handle_logout():
        nonlocal win, login_win
        if win:
            win.close()
            win = None
        if login_win:
            login_win.reset_for_logout()
        else:
            login_win = LoginWindow()
            login_win.auth_success.connect(show_main)
            login_win.show()
    
    def show_login():
        nonlocal login_win
        login_win = LoginWindow()
        login_win.auth_success.connect(show_main)
        login_win.show()
    
    def handle_splash_done():
        from app.ui.onboarding import OnboardingWindow
        from app.core.db import has_owner
        
        # Decide if we need onboarding:
        # 1. No owner account in DB
        # 2. Settings says first_run is True
        if not has_owner() or sm.get("first_run"):
            onboarding = OnboardingWindow(sm)
            onboarding.finished.connect(show_login)
            onboarding.show()
            # To prevent GC
            app._onboarding = onboarding
        else:
            show_login()
    
    sp = SplashScreen(handle_splash_done)
    sp.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
