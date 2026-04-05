from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QSystemTrayIcon)
from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon

# Import core components
from ..core.managers import SettingsManager, SystemTrayManager
from ..core.workers import ScraperThread
from ..core.theme import get_theme_stylesheet
from ..core.utils import get_resource_path
from ..core.auth import Session, ROLE_OWNER, ROLE_BROKER, ROLE_CLIENT

# Import UI components
from .header_bar import HeaderBar
from .sidebar import Sidebar
from .dialogs import SettingsDialog, get_asset_path

# Import Pages
from .pages.dashboard_page import DashboardPage
from .pages.prices_page import PricesPage
from .pages.search_page import SearchPage
from .pages.portfolio_page import SmartPortfolioPage
from .pages.news_page import NewsPage

class MainApp(QMainWindow):
    logout_requested = pyqtSignal()
    
    def __init__(self, session=None):
        super().__init__()
        self.session = session
        self.setWindowTitle("PSX Market Tracker")
        self.setMinimumSize(1100, 800)
        self.setWindowIcon(QIcon(get_resource_path("assets/icon.png")))
                              
        self.settings_manager = SettingsManager()
        # Ensure icon is found
        icon_path = get_resource_path("assets/icon.png")
        self.tray_manager = SystemTrayManager(self, icon_path)
        
        self.scraper_thread = ScraperThread()
        self.scraper_thread.data_received.connect(self.on_data)
        self.scraper_thread.error_occurred.connect(self.on_error)
        
        c = QWidget(); self.setCentralWidget(c); win_l = QVBoxLayout(c); win_l.setContentsMargins(0,0,0,0); win_l.setSpacing(0)
        self.header = HeaderBar(self.tog_s, self.ref, self, session=self.session, logout_callback=self._do_logout)
        win_l.addWidget(self.header)
        b = QWidget(); b_lay = QHBoxLayout(b); b_lay.setContentsMargins(0,0,0,0); win_l.addWidget(b)
        
        self.sidebar = Sidebar(self, session=self.session); b_lay.addWidget(self.sidebar)
        self.sidebar.page_selected.connect(self.switch_page)
        
        self.stack = QStackedWidget(); b_lay.addWidget(self.stack)
        
        # Initialize Pages (pass session for role-based rendering)
        self.d_p = DashboardPage(self, session=self.session)
        self.prices_p = PricesPage(self)
        self.s_p = SearchPage(self.add_to_portfolio_from_search, self)
        self.portfolio_p = SmartPortfolioPage(self.notify, self, session=self.session)
        self.n_p = NewsPage(self)
        
        self.stack.addWidget(self.d_p)      # 0
        self.stack.addWidget(self.prices_p)     # 1
        self.stack.addWidget(self.s_p)      # 2
        self.stack.addWidget(self.portfolio_p) # 3
        self.stack.addWidget(self.n_p)      # 4
        
        self.apply_theme(self.settings_manager.get("theme")); self.ref()
        self.tmr = QTimer(self); self.tmr.timeout.connect(self.ref); self.tmr.start(self.settings_manager.get("refresh_interval")*1000)

    def _do_logout(self):
        """Handle logout — stop timers and emit signal."""
        self.tmr.stop()
        if self.scraper_thread.isRunning():
            self.scraper_thread.quit()
            self.scraper_thread.wait(2000)
        self.logout_requested.emit()

    def switch_page(self, index, title):
        if index == 5:
            self.open_settings()
        else:
            self.stack.setCurrentIndex(index)
            if index == 0:
                self.header.set_title("Market Tracker")
            else:
                self.header.set_title(title)

    def apply_theme(self, n):
        self.setStyleSheet(get_theme_stylesheet(n)); self.settings_manager.set("theme", n)
        
        if n == "light":
            self.header.title.setStyleSheet("font-size:22px; font-weight:600; font-style:italic; font-family:'Times New Roman', serif; color:#065f46; background:transparent;")
            self.header.title_glow.setColor(QColor(16, 185, 129, 200))
        else:
            self.header.title.setStyleSheet("font-size:22px; font-weight:600; font-style:italic; font-family:'Times New Roman', serif; color:white; background:transparent;")
            self.header.title_glow.setColor(QColor(255, 255, 255, 220))

    def ref(self):
        if self.scraper_thread.isRunning(): return
        self.header.status.setText("● Updating..."); self.scraper_thread.start()
    
    
    def on_data(self, d):
        self.portfolio_p.update_prices({s["symbol"]:s["price"] for s in d})
        self.portfolio_p.update_all_symbols([s["symbol"] for s in d])
        # Pass the fresh portfolio data to the dashboard
        self.d_p.update_summary({s["symbol"]:s["price"] for s in d}, self.portfolio_p.manager.get_aggregated_portfolio())
        self.prices_p.update_data(d)
        self.s_p.update_symbols(d)
        self.header.status.setText("● Live")
        
    def on_error(self, msg):
        self.header.status.setText("● Offline")
    
    def tog_s(self): self.sidebar.toggle()
    
    def add_to_portfolio_from_search(self, s):
        self.switch_page(3, "Portfolio")
        self.portfolio_p.show_add_dialog(s)
        
    def open_settings(self):
        if SettingsDialog(self, self.settings_manager, session=self.session).exec(): 
            self.apply_theme(self.settings_manager.get("theme"))
            self.sidebar.update_profile()
    
    def notify(self, t, m): self.tray_manager.tray_icon.showMessage(t, m, QSystemTrayIcon.MessageIcon.Information, 3000)
    
    def closeEvent(self, e):
        if self.settings_manager.get("run_in_background"): e.ignore(); self.tray_manager.minimize_to_tray()
        else: e.accept()
