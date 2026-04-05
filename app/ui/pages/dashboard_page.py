from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFrame, QScrollArea, QLabel, 
                             QGridLayout, QGraphicsOpacityEffect, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from ..dashboard_card import DashboardCard
from ...core.managers import PortfolioManager
from ...core.auth import ROLE_OWNER, ROLE_BROKER, ROLE_CLIENT, get_system_stats, get_clients_for_broker

class SummaryTile(QFrame):
    def __init__(self, title, value, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 100)
        self.clr = QColor(color)
        self._shine_pos = -1.0
        self._opacity = 1.0
        
        self.setStyleSheet("QFrame { border: none; background: transparent; }")
        
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(5)
        
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 11px; font-weight: bold; text-transform: uppercase;")
        lay.addWidget(t_lbl)
        
        self.v_lbl = QLabel(value)
        self.v_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 800;")
        lay.addWidget(self.v_lbl)
        
        # Animations
        self.anim = QPropertyAnimation(self, b"shine_pos")
        self.anim.setDuration(800)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def set_value(self, val, color=None):
        self.v_lbl.setText(str(val))
        if color:
            self.v_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: 800;")

    def get_shine(self): return self._shine_pos
    def set_shine(self, v): self._shine_pos = v; self.update()
    shine_pos = pyqtProperty(float, get_shine, set_shine)
    
    def get_op(self): return self._opacity
    def set_op(self, v): self._opacity = v; self.update()
    opacity_val = pyqtProperty(float, get_op, set_op)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setOpacity(self._opacity)
        r = self.rect().adjusted(2,2,-2,-2)
        
        # 1. Shadow / Outer Glow
        p.setBrush(QColor(0, 0, 0, 30))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r.adjusted(3,5,3,5), 18, 18)

        # 2. Glass Background
        p.setBrush(QColor(30, 35, 40, 200))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(r, 16, 16)
        
        # 3. "Sunshine" Shine Effect
        if self._shine_pos > -1.0 and self.underMouse():
            shine_grad = QLinearGradient(r.width() * (self._shine_pos - 0.2), 0, r.width() * (self._shine_pos + 0.3), r.height())
            shine_grad.setColorAt(0, QColor(0, 0, 0, 0))
            shine_grad.setColorAt(0.5, QColor(16, 185, 129, 50))
            shine_grad.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(shine_grad); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r, 16, 16)
        p.end()

    def enterEvent(self, e): 
        self.anim.stop(); self.anim.setStartValue(-1.0); self.anim.setEndValue(1.5); self.anim.start()
        super().enterEvent(e)
        
    def leaveEvent(self, e): 
        self.anim.stop(); self.anim.setStartValue(self._shine_pos); self.anim.setEndValue(-1.0); self.anim.start()
        super().leaveEvent(e)

class DashboardPage(QWidget):
    def __init__(self, parent=None, session=None):
        super().__init__(parent)
        self.p_app = parent
        self.session = session
        self.manager = PortfolioManager(session=self.session)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        
        content_widget = QWidget()
        content_widget.setObjectName("dashboard_content")
        content_widget.setStyleSheet("#dashboard_content { background: transparent; }")
        self.lay = QVBoxLayout(content_widget)
        self.lay.setContentsMargins(40, 40, 40, 40)
        self.lay.setSpacing(30)
        
        un = self.session.user_name.split(" ")[0] if self.session else "Investor"
        
        self.wl = QLabel("")
        self.wl.setProperty("class", "title-text")
        # Base style: Sans-serif. We will apply the serif/italic style to the username via HTML in tc()
        self.wl.setStyleSheet("font-size:36px; font-weight:800; border:none; background:transparent;")
        self.lay.addWidget(self.wl)
        
        # dynamic subtitle based on role
        subtitle_text = "Here's your market overview for today."
        if self.session:
            if self.session.role == ROLE_OWNER:
                subtitle_text = "System-wide activity and statistics."
            elif self.session.role == ROLE_BROKER:
                subtitle_text = "Overview of your clients' active portfolios."
                
        self.sub = QLabel(subtitle_text)
        self.sub.setProperty("class", "desc-text")
        self.sub.setStyleSheet("font-size:16px; border:none; background:transparent;")
        op = QGraphicsOpacityEffect()
        self.sub.setGraphicsEffect(op)
        op.setOpacity(0)
        self.lay.addWidget(self.sub)
        
        # --- Summary Tiles Section ---
        self.sum_lay = QHBoxLayout()
        self.sum_lay.setSpacing(20)
        
        self.tiles = []
        
        if not self.session or self.session.role == ROLE_CLIENT:
            # Standard single portfolio view
            self.t_inv = SummaryTile("TOTAL INVESTED", "Rs. 0.00", "#ffffff", self)
            self.t_val = SummaryTile("CURRENT VALUE", "Rs. 0.00", "#ffffff", self)
            self.t_pl = SummaryTile("NET PROFIT/LOSS", "Rs. 0.00", "#10b981", self)
            self.sum_lay.addWidget(self.t_inv)
            self.sum_lay.addWidget(self.t_val)
            self.sum_lay.addWidget(self.t_pl)
            self.tiles = [self.t_inv, self.t_val, self.t_pl]
            
        elif self.session.role == ROLE_BROKER:
            # Broker aggregate view
            self.t_clients = SummaryTile("TOTAL CLIENTS", "0", "#3b82f6", self)
            self.t_val = SummaryTile("AUM (CLIENT VALUE)", "Rs. 0.00", "#ffffff", self)
            self.t_pl = SummaryTile("CLIENTS NET RETURN", "Rs. 0.00", "#10b981", self)
            self.sum_lay.addWidget(self.t_clients)
            self.sum_lay.addWidget(self.t_val)
            self.sum_lay.addWidget(self.t_pl)
            self.tiles = [self.t_clients, self.t_val, self.t_pl]
            
            # Fetch broker static data now
            clients = get_clients_for_broker(self.session.user_id)
            self.t_clients.set_value(str(len(clients)))
            
        elif self.session.role == ROLE_OWNER:
            # Owner system view
            self.t_brokers = SummaryTile("ACTIVE BROKERS", "0", "#8b5cf6", self)
            self.t_clients = SummaryTile("TOTAL CLIENTS", "0", "#3b82f6", self)
            self.t_tx = SummaryTile("TOTAL TRANSACTIONS", "0", "#f59e0b", self)
            self.sum_lay.addWidget(self.t_brokers)
            self.sum_lay.addWidget(self.t_clients)
            self.sum_lay.addWidget(self.t_tx)
            self.tiles = [self.t_brokers, self.t_clients, self.t_tx]
            
            # Fetch owner static data now
            stats = get_system_stats()
            self.t_brokers.set_value(str(stats['broker_count']))
            self.t_clients.set_value(str(stats['client_count']))
            self.t_tx.set_value(str(stats['total_transactions']))
            
        self.sum_lay.addStretch()
        self.lay.addLayout(self.sum_lay)
        # -----------------------------
        
        self.lay.addSpacing(10)
        
        gc = QWidget()
        self.gl = QGridLayout(gc)
        self.gl.setSpacing(25)
        self.lay.addWidget(gc)
        
        opts = [
            ("📈", "Live Prices", "View real-time stock quotes from PSX.", "#10b981", 1),
            ("🔍", "Search", "Find specific stocks and check their data.", "#3b82f6", 2),
            ("💼", "Portfolio", "Manage holdings and track performance.", "#f59e0b", 3),
            ("📰", "Latest News", "Read what's happening in the market.", "#ec4899", 4),
            ("⚙️", "Settings", "Customize your app experience.", "#8b5cf6", 5)
        ]
        
        if self.session and self.session.role == ROLE_OWNER:
            opts[2] = ("💼", "Global Portfolios", "View all trades in the platform.", "#f59e0b", 3)
            opts[4] = ("⚙️", "System Settings", "Manage brokers and platform settings.", "#8b5cf6", 5)
        elif self.session and self.session.role == ROLE_BROKER:
            opts[2] = ("💼", "Client Portfolios", "Manage your clients' trades.", "#f59e0b", 3)
            opts[4] = ("⚙️", "Settings", "Manage your clients and preferences.", "#8b5cf6", 5)
        
        self.cards = []
        for i, (ic, tit, ds, c, t) in enumerate(opts):
            cd = DashboardCard(ic, tit, ds, c, self)
            cd.set_op(0) 
            if t == 5: 
                cd.clicked.connect(lambda: self.p_app.open_settings() if self.p_app else None)
            else: 
                cd.clicked.connect(lambda target=t, title=tit: self.p_app.switch_page(target, title) if self.p_app else None)
            
            self.gl.addWidget(cd, i // 2, i % 2)
            self.cards.append(cd)
            
        self.lay.addStretch(1)
        
        ft_lay = QHBoxLayout()
        ft_lay.addStretch()
        ft = QLabel("© 2026 Slade Tech. All rights reserved.")
        ft.setStyleSheet("color:rgba(120,120,120,0.4); font-size:11px; border:none; background:transparent;")
        ft_lay.addWidget(ft)
        ft_lay.addStretch()
        self.lay.addLayout(ft_lay)
        
        self.scroll.setWidget(content_widget)
        main_layout.addWidget(self.scroll)
        
        # Initial Summary Load
        self.update_summary({})
        
        # Start Blur Animation for Welcome Label
        self.start_welcome_animation(un)

    def start_welcome_animation(self, username):
        try:
            # Set final HTML text immediately
            final_html = f"<font face='Segoe UI' color='#ffffff'>Welcome, </font><font face='Georgia, serif' color='#10b981'><i>{username}</i></font>!"
            self.wl.setText(final_html)
            
            # Apply Blur Entry
            from PyQt6.QtWidgets import QGraphicsBlurEffect
            blur = QGraphicsBlurEffect()
            self.wl.setGraphicsEffect(blur)
            
            self.wl_anim = QPropertyAnimation(blur, b"blurRadius")
            self.wl_anim.setDuration(800)
            self.wl_anim.setStartValue(20.0)
            self.wl_anim.setEndValue(0.0)
            self.wl_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            
            self.wl_anim.finished.connect(lambda: (self.fbs(), self.an_c()))
            self.wl_anim.start()
        except:
            self.fbs(); self.an_c()

    def fbs(self):
        try:
            if not self.sub.graphicsEffect(): return
            a = QPropertyAnimation(self.sub.graphicsEffect(), b"opacity"); a.setDuration(800); a.setStartValue(0.0); a.setEndValue(1.0); a.start(); self._s_ref = a
        except: pass
    def an_c(self):
        try:
            # Animate summary tiles too
            self._ans = []
            for item in self.tiles + self.cards:
                a = QPropertyAnimation(item, b"opacity_val"); a.setDuration(500); a.setStartValue(0.0); a.setEndValue(1.0)
                QTimer.singleShot(len(self._ans)*50, lambda anim=a: anim.start() if anim else None); self._ans.append(a)
        except: pass

    def update_summary(self, live_data_map, portfolio_data=None):
        if self.session and self.session.role == ROLE_OWNER:
            # Subtitle static tiles are already set, we just need to update TX count
            stats = get_system_stats()
            self.t_tx.set_value(str(stats['total_transactions']))
            return
            
        # Allow passing fresh portfolio data
        if portfolio_data is None:
            portfolio_data = self.manager.get_aggregated_portfolio()
            
        # Calculate totals
        total_inv = 0
        total_curr = 0
        
        for sym, info in portfolio_data.items():
            qty = info['quantity']
            buy = info['buy_price']
            total_inv += (qty * buy)
            
            c_price = live_data_map.get(sym, buy) 
            total_curr += (qty * c_price)
            
        total_pl = total_curr - total_inv
        
        pl_color = "#ffffff"
        if total_pl > 0: pl_color = "#10b981"
        elif total_pl < 0: pl_color = "#ef4444"
        
        if not self.session or self.session.role == ROLE_CLIENT:
            self.t_inv.set_value(f"Rs. {total_inv:,.2f}")
            self.t_val.set_value(f"Rs. {total_curr:,.2f}")
            self.t_pl.set_value(f"Rs. {total_pl:+,.2f}", pl_color)
        elif self.session.role == ROLE_BROKER:
            # We already set the client count, update AUM and Return
            self.t_val.set_value(f"Rs. {total_curr:,.2f}")
            self.t_pl.set_value(f"Rs. {total_pl:+,.2f}", pl_color)
