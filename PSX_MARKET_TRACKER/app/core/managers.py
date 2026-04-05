import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import QObject

from .db import get_connection, tenant_where, migrate_from_json, import_json_for_user
from .auth import Session, ROLE_OWNER, ROLE_BROKER, ROLE_CLIENT

class SystemTrayManager(QObject):
    """Handles system tray icon and its menu for background running."""
    
    def __init__(self, main_window, icon_path):
        super().__init__()
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon(main_window)
        icon = QIcon(icon_path)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("PSX Market Tracker - Running in background")
        
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: #1a1a2e;
                color: white;
                border: 1px solid #333;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
            }
            QMenu::item:selected {
                background-color: #10b981;
            }
        """)
        
        self.open_action = QAction("📊 Open PSX Tracker", main_window)
        self.open_action.triggered.connect(self.show_main_window)
        self.tray_menu.addAction(self.open_action)
        self.tray_menu.addSeparator()
        self.quit_action = QAction("❌ Quit Completely", main_window)
        self.quit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(self.quit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        # Direct comparison is safer in most PyQt6 environments
        # Fallback to integer check if direct enum comparison fails
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick or str(reason) == '2':
            self.show_main_window()
    
    def show_main_window(self):
        self.main_window.show()
        self.main_window.showNormal()
        self.main_window.activateWindow()
        self.main_window.raise_()
    
    def minimize_to_tray(self):
        self.main_window.hide()
        self.tray_icon.showMessage(
            "PSX Tracker", 
            "App is running in background. Double-click to open.", 
            QSystemTrayIcon.MessageIcon.Information, 
            2000 
        )
    
    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()

class SettingsManager:
    """Handles loading and saving user settings to a JSON file."""
    
    def __init__(self):
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(os.path.abspath(sys.executable))
        else:
            # Go up two levels from app/core/managers.py to root
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
        self.settings_file = os.path.join(base_dir, "data", "settings.json")
        
        self.default_settings = {
            "user_name": "Investor",
            "refresh_interval": 60,
            "notifications_enabled": True,
            "theme": "dark",
            "auto_save_portfolio": True,
            "run_in_background": True,
            "first_run": True,
            "user_logo_path": ""
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    merged = self.default_settings.copy()
                    merged.update(loaded)
                    return merged
            except (json.JSONDecodeError, IOError):
                return self.default_settings.copy()
        return self.default_settings.copy()
    
    def save_settings(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
                return True
        except IOError:
            return False
    
    def get(self, key):
        return self.settings.get(key)
    
    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

class PortfolioManager:
    """Manages the portfolio data (transactions and alerts) in SQLite with Tenant Filtering."""
    def __init__(self, session=None):
        self.session = session
        
        # If no session is provided (e.g. initial boot testing), create a dummy owner session
        if not self.session:
            self.session = Session(user_id=1, user_name="System", email="sys", role=ROLE_OWNER, broker_id=None)
            
        self._check_for_migration()

    def _check_for_migration(self):
        """Check if we need to migrate from JSON on first use for this specific tenant."""
        # We only migrate to the very first owner or broker that logs in
        # (Usually the owner since they are forced to create an account first)
        migration_data = migrate_from_json()
        if migration_data and self.session.role in (ROLE_OWNER, ROLE_BROKER):
            # Check if this user has any data yet
            conn = get_connection()
            cnt = conn.execute("SELECT COUNT(*) as cnt FROM portfolio").fetchone()['cnt']
            conn.close()
            
            if cnt == 0:
                print("Migrating legacy JSON data to SQLite for current user...")
                # If owner, assume broker_id is their own ID for now to satisfy the FK
                # though Owner doesn't strictly have a broker_id. Oh wait, owner broker_id is NULL.
                # Portfolio table REQUIRES broker_id. 
                # Instead of crashing, let's assign broker_id to 1 (which might be the owner's ID).
                broker_id_to_use = self.session.broker_id if self.session.broker_id else self.session.user_id
                import_json_for_user(self.session.user_id, broker_id_to_use, migration_data)
                
                # Delete or rename the JSON to prevent double migration
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                portfolio_json = os.path.join(base_dir, "data", "portfolio.json")
                if os.path.exists(portfolio_json):
                    os.rename(portfolio_json, portfolio_json + ".backup")

    @property
    def alerts(self):
        """Return all active alerts for the current tenant context."""
        conn = get_connection()
        where, params = tenant_where(self.session)
        rows = conn.execute(f"SELECT symbol, limit_upper, limit_lower FROM alerts WHERE {where}", params).fetchall()
        conn.close()
        
        alert_dict = {}
        for r in rows:
            alert_dict[r['symbol']] = {
                "limit_upper": r['limit_upper'],
                "limit_lower": r['limit_lower']
            }
        return alert_dict

    @property
    def transactions(self):
        """Return all transactions for the current tenant context."""
        return self.get_transactions()

    def get_transactions(self, specific_client_id=None):
        """Get transactions, optionally filtered by a specific client."""
        conn = get_connection()
        where, params = tenant_where(self.session)
        
        query = f"SELECT id, symbol, quantity, price, type, date, note FROM portfolio WHERE {where}"
        
        # If broker/owner wants to see a specific client
        if specific_client_id and self.session.role != ROLE_CLIENT:
            query += " AND client_id = ?"
            params = params + (specific_client_id,)
            
        query += " ORDER BY date ASC"
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(r) for r in rows]

    def delete_all_data(self, specific_client_id=None):
        """Clears all transactions and alerts for the tenant."""
        conn = get_connection()
        where, params = tenant_where(self.session)
        
        if specific_client_id and self.session.role != ROLE_CLIENT:
            port_query = f"DELETE FROM portfolio WHERE {where} AND client_id = ?"
            alert_query = f"DELETE FROM alerts WHERE {where} AND client_id = ?"
            ext_params = params + (specific_client_id,)
            conn.execute(port_query, ext_params)
            conn.execute(alert_query, ext_params)
        else:
            conn.execute(f"DELETE FROM portfolio WHERE {where}", params)
            conn.execute(f"DELETE FROM alerts WHERE {where}", params)
            
        conn.commit()
        conn.close()

    def add_transaction(self, symbol, quantity, price, type_="BUY", date=None, note="", client_id=None):
        """Add a transaction. For brokers/owners, client_id must be provided to add for a client. 
           If client_id is None, it falls back to the logged in user."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        target_client = client_id if client_id else self.session.user_id
        
        # Determine the broker ID to associate
        if self.session.role == ROLE_CLIENT:
            broker_id = self.session.broker_id
        elif self.session.role == ROLE_BROKER:
            broker_id = self.session.user_id
        else: # Owner adding directly
            broker_id = self.session.user_id
            
        conn = get_connection()
        cursor = conn.execute("""
            INSERT INTO portfolio (broker_id, client_id, symbol, quantity, price, type, date, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (broker_id, target_client, symbol.upper(), int(quantity), float(price), type_.upper(), date, note))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {"id": new_id, "symbol": symbol.upper(), "quantity": int(quantity), "price": float(price), "type": type_.upper(), "date": date}

    def update_alerts(self, symbol, high, low, client_id=None):
        target_client = client_id if client_id else self.session.user_id
        
        if self.session.role == ROLE_CLIENT:
            broker_id = self.session.broker_id
        elif self.session.role == ROLE_BROKER:
            broker_id = self.session.user_id
        else:
            broker_id = self.session.user_id
            
        conn = get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO alerts (broker_id, client_id, symbol, limit_upper, limit_lower)
            VALUES (?, ?, ?, ?, ?)
        """, (broker_id, target_client, symbol.upper(), float(high), float(low)))
        conn.commit()
        conn.close()

    def add_or_update_stock(self, symbol, qty, buy_price, high_limit, low_limit, client_id=None):
        """Legacy adapter: Adds a BUY transaction and updates alerts."""
        self.add_transaction(symbol, qty, buy_price, "BUY", client_id=client_id)
        self.update_alerts(symbol, high_limit, low_limit, client_id=client_id)

    def delete_transactions(self, transaction_ids):
        """Batch delete transactions by ID."""
        if not transaction_ids: return
        
        conn = get_connection()
        where, params = tenant_where(self.session)
        
        placeholders = ','.join('?' for _ in transaction_ids)
        query = f"DELETE FROM portfolio WHERE {where} AND id IN ({placeholders})"
        
        # Extend params with the IDs (ensure they are strictly flat)
        final_params = list(params) + list(transaction_ids)
        
        conn.execute(query, tuple(final_params))
        conn.commit()
        conn.close()

    def remove_stock(self, symbol, specific_client_id=None):
        """Remove all transactions for a symbol (Clear position)."""
        symbol = symbol.upper()
        conn = get_connection()
        where, params = tenant_where(self.session)
        
        port_query = f"DELETE FROM portfolio WHERE {where} AND symbol = ?"
        alert_query = f"DELETE FROM alerts WHERE {where} AND symbol = ?"
        
        ext_params = list(params) + [symbol]
        
        if specific_client_id and self.session.role != ROLE_CLIENT:
            port_query += " AND client_id = ?"
            alert_query += " AND client_id = ?"
            ext_params.append(specific_client_id)
            
        ext_params = tuple(ext_params)
        
        conn.execute(port_query, ext_params)
        conn.execute(alert_query, ext_params)
        conn.commit()
        conn.close()

    def get_stock(self, symbol, specific_client_id=None):
        """Returns aggregated info for a symbol."""
        agg = self.get_aggregated_portfolio(specific_client_id)
        return agg.get(symbol.upper())

    @property
    def portfolio(self):
        """Property to access aggregated portfolio."""
        return self.get_aggregated_portfolio()

    def get_aggregated_portfolio(self, specific_client_id=None):
        """Calculates current holdings based on transaction history."""
        agg = {}
        
        txs = self.get_transactions(specific_client_id)
        
        for t in txs:
            sym = t['symbol']
            qty = int(t.get('quantity', 0))
            price = float(t.get('price', 0.0))
            t_type = str(t.get('type', 'BUY')).upper()
            
            if sym not in agg:
                agg[sym] = {"quantity": 0, "buy_price": 0.0, "total_cost": 0.0}
            
            p = agg[sym]
            
            if t_type == "BUY":
                new_cost = float(qty * price)
                total_qty = p['quantity'] + qty
                total_cost = (p['quantity'] * p['buy_price']) + new_cost
                
                if total_qty > 0:
                    p['buy_price'] = total_cost / total_qty
                else:
                    p['buy_price'] = 0.0
                    
                p['quantity'] = total_qty
                
            elif t_type == "SELL":
                if p['quantity'] >= qty:
                    p['quantity'] -= qty
                else:
                    p['quantity'] = 0
        
        # Merge with alerts
        alerts_map = self.alerts
        final_portfolio = {}
        for sym, data in agg.items():
            if data['quantity'] > 0:
                alm = alerts_map.get(sym, {"limit_upper": 0.0, "limit_lower": 0.0})
                final_portfolio[sym] = {
                    "quantity": data['quantity'],
                    "buy_price": data['buy_price'],
                    "limit_upper": alm['limit_upper'],
                    "limit_lower": alm['limit_lower']
                }
        
        return final_portfolio
