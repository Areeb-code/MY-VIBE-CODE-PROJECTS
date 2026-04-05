"""
PSX Platform — Client Manager Dialog
Broker panel to manage client accounts (create, edit, deactivate).
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                             QLineEdit, QMessageBox, QFrame, QFormLayout, QWidget)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QIcon
from ..core.auth import (create_client, get_clients_for_broker, toggle_user_active,
                         update_user, Session, ROLE_BROKER, ROLE_OWNER, get_all_brokers)
from ..core.utils import get_asset_path


class AddClientDialog(QDialog):
    """Dialog for creating a new client account."""
    def __init__(self, broker_session, parent=None):
        super().__init__(parent)
        self.broker_session = broker_session
        self.created_credentials = None
        
        self.setWindowTitle("Add Client")
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))
        self.setFixedSize(400, 380)
        self.setStyleSheet("""
            QDialog { background-color: #0c0d14; color: white; }
            QLabel { color: rgba(255, 255, 255, 0.7); font-size: 13px; background: transparent; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title = QLabel("Create Client Account")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: white;")
        layout.addWidget(title)
        
        subtitle = QLabel("The client will use these credentials to log in")
        subtitle.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.4);")
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        input_style = """
            QLineEdit {
                background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; color: white; font-size: 14px; padding: 8px 12px;
            }
            QLineEdit:focus { border: 1px solid #10b981; }
        """
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Client's full name")
        self.name_input.setStyleSheet(input_style)
        form.addRow("Name:", self.name_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("client@example.com")
        self.email_input.setStyleSheet(input_style)
        form.addRow("Email:", self.email_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Minimum 6 characters")
        self.password_input.setStyleSheet(input_style)
        form.addRow("Password:", self.password_input)
        
        layout.addLayout(form)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
        btn_lay = QHBoxLayout()
        btn_lay.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 40)
        cancel_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.05); color: white; border: 1px solid #333; border-radius: 8px; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_lay.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Client")
        create_btn.setFixedSize(140, 40)
        create_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        create_btn.setStyleSheet("""
            QPushButton { background: #10b981; color: white; border: none; border-radius: 8px; font-weight: bold; }
            QPushButton:hover { background: #059669; }
        """)
        create_btn.clicked.connect(self._create)
        btn_lay.addWidget(create_btn)
        
        layout.addLayout(btn_lay)
    
    def _create(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not name or not email or not password:
            self.error_label.setText("All fields are required.")
            return
        if len(password) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return
        if '@' not in email or '.' not in email:
            self.error_label.setText("Please enter a valid email.")
            return
        
        result = create_client(self.broker_session, name, email, password)
        if result['success']:
            self.created_credentials = {'name': name, 'email': email, 'password': password}
            self.accept()
        else:
            self.error_label.setText(result['error'])


class ClientManagerDialog(QDialog):
    """Broker's client management dialog — view, add, deactivate clients."""
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        
        self.setWindowTitle("Manage Clients")
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #0c0d14; color: white; }
            QLabel { color: white; background: transparent; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Header
        header_lay = QHBoxLayout()
        
        title = QLabel("👥 Client Accounts")
        title.setStyleSheet("font-size: 22px; font-weight: 800;")
        header_lay.addWidget(title)
        
        header_lay.addStretch()
        
        add_btn = QPushButton("+ Add Client")
        add_btn.setFixedSize(130, 40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton { background: #10b981; color: white; border: none; border-radius: 10px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #059669; }
        """)
        add_btn.clicked.connect(self._add_client)
        header_lay.addWidget(add_btn)
        
        layout.addLayout(header_lay)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Email", "Status", "Created", "Actions"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; outline: none; border: none; }
            QHeaderView::section { background-color: rgba(255,255,255,0.05); color: #10b981; padding: 10px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); color: white; }
        """)
        layout.addWidget(self.table)
        
        # Footer
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 40)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.05); color: white; border: 1px solid #333; border-radius: 8px; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
        """)
        close_btn.clicked.connect(self.accept)
        
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(close_btn)
        layout.addLayout(footer)
        
        self._refresh_table()
    
    def _refresh_table(self):
        if self.session.role == ROLE_OWNER:
            # Owner sees all clients
            from ..core.db import get_connection
            conn = get_connection()
            rows = conn.execute(
                "SELECT id, name, email, is_active, created_at FROM users WHERE role = 'client' ORDER BY name"
            ).fetchall()
            conn.close()
            clients = [dict(r) for r in rows]
        else:
            clients = get_clients_for_broker(self.session.user_id)
        
        self.table.setRowCount(len(clients))
        
        for row, client in enumerate(clients):
            self.table.setItem(row, 0, QTableWidgetItem(client['name']))
            self.table.setItem(row, 1, QTableWidgetItem(client['email']))
            
            status = "Active" if client['is_active'] else "Inactive"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor("#10b981") if client['is_active'] else QColor("#ef4444"))
            self.table.setItem(row, 2, status_item)
            
            created = client.get('created_at', '')
            if created:
                created = created[:10]  # date only
            self.table.setItem(row, 3, QTableWidgetItem(created))
            
            # Action button
            action_container = QWidget()
            action_lay = QHBoxLayout(action_container)
            action_lay.setContentsMargins(4, 4, 4, 4)
            action_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if client['is_active']:
                btn = QPushButton("Deactivate")
                btn.setStyleSheet("""
                    QPushButton { background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; }
                    QPushButton:hover { background: #ef4444; color: white; }
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda ch, cid=client['id']: self._toggle_active(cid, False))
            else:
                btn = QPushButton("Activate")
                btn.setStyleSheet("""
                    QPushButton { background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.3); border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; }
                    QPushButton:hover { background: #10b981; color: white; }
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda ch, cid=client['id']: self._toggle_active(cid, True))
            
            action_lay.addWidget(btn)
            self.table.setCellWidget(row, 4, action_container)
    
    def _add_client(self):
        dlg = AddClientDialog(self.session, self)
        if dlg.exec():
            creds = dlg.created_credentials
            QMessageBox.information(self, "Client Created",
                f"Client account created successfully!\n\n"
                f"Name: {creds['name']}\n"
                f"Email: {creds['email']}\n"
                f"Password: {creds['password']}\n\n"
                f"Share these credentials with your client.")
            self._refresh_table()
    
    def _toggle_active(self, user_id, activate):
        action = "activate" if activate else "deactivate"
        confirm = QMessageBox.question(self, "Confirm",
            f"Are you sure you want to {action} this client?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            toggle_user_active(user_id, activate)
            self._refresh_table()


class BrokerManagerDialog(QDialog):
    """Owner's broker management dialog — view all brokers."""
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        
        self.setWindowTitle("Manage Brokers")
        self.setWindowIcon(QIcon(get_asset_path("icon.png")))
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #0c0d14; color: white; }
            QLabel { color: white; background: transparent; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        title = QLabel("🏢 All Brokers")
        title.setStyleSheet("font-size: 22px; font-weight: 800;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "Email", "Clients", "Status", "Actions"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(4, 120)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; outline: none; border: none; }
            QHeaderView::section { background-color: rgba(255,255,255,0.05); color: #10b981; padding: 10px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); color: white; }
        """)
        layout.addWidget(self.table)
        
        close_btn = QPushButton("Close")
        close_btn.setFixedSize(100, 40)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255,255,255,0.05); color: white; border: 1px solid #333; border-radius: 8px; }
            QPushButton:hover { background: rgba(255,255,255,0.1); }
        """)
        close_btn.clicked.connect(self.accept)
        
        footer = QHBoxLayout()
        footer.addStretch()
        footer.addWidget(close_btn)
        layout.addLayout(footer)
        
        self._refresh_table()
    
    def _refresh_table(self):
        from ..core.db import get_connection
        
        brokers = get_all_brokers()
        self.table.setRowCount(len(brokers))
        
        conn = get_connection()
        
        for row, broker in enumerate(brokers):
            self.table.setItem(row, 0, QTableWidgetItem(broker['name']))
            self.table.setItem(row, 1, QTableWidgetItem(broker['email']))
            
            # Client count
            client_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM users WHERE role = 'client' AND broker_id = ?",
                (broker['id'],)
            ).fetchone()['cnt']
            self.table.setItem(row, 2, QTableWidgetItem(str(client_count)))
            
            status = "Active" if broker['is_active'] else "Inactive"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(QColor("#10b981") if broker['is_active'] else QColor("#ef4444"))
            self.table.setItem(row, 3, status_item)
            
            # Action button
            action_container = QWidget()
            action_lay = QHBoxLayout(action_container)
            action_lay.setContentsMargins(4, 4, 4, 4)
            action_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if broker['is_active']:
                btn = QPushButton("Deactivate")
                btn.setStyleSheet("""
                    QPushButton { background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; }
                    QPushButton:hover { background: #ef4444; color: white; }
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda ch, bid=broker['id']: self._toggle_active(bid, False))
            else:
                btn = QPushButton("Activate")
                btn.setStyleSheet("""
                    QPushButton { background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.3); border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; }
                    QPushButton:hover { background: #10b981; color: white; }
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda ch, bid=broker['id']: self._toggle_active(bid, True))
            
            action_lay.addWidget(btn)
            self.table.setCellWidget(row, 4, action_container)
        
        conn.close()
    
    def _toggle_active(self, broker_id, activate):
        action = "activate" if activate else "deactivate"
        confirm = QMessageBox.question(self, "Confirm",
            f"Are you sure you want to {action} this broker?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if confirm == QMessageBox.StandardButton.Yes:
            toggle_user_active(broker_id, activate)
            self._refresh_table()
