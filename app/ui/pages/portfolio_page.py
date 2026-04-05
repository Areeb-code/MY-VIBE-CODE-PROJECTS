import os
import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QTableWidget, 
                             QHeaderView, QAbstractItemView, QFrame, QTableWidgetItem, QDialog, 
                             QFormLayout, QLineEdit, QCompleter, QFileDialog, QCheckBox, 
                             QMessageBox, QMenu, QWidgetAction, QComboBox)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize
from PyQt6.QtGui import QColor, QCursor, QIcon, QAction

from ...core.managers import PortfolioManager
from ...core.auth import ROLE_OWNER, ROLE_BROKER, ROLE_CLIENT, get_clients_for_broker, get_all_brokers, get_all_clients

# ─── Styled 3-Dot Menu ────────────────────────────────────────────────────────
MENU_STYLE = """
QMenu {
    background-color: #1e293b;
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 12px;
    padding: 8px 0px;
    min-width: 200px;
}
QMenu::item {
    color: rgba(255,255,255,0.85);
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 500;
    border-radius: 0px;
}
QMenu::item:selected {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
}
QMenu::separator {
    height: 1px;
    background: rgba(255,255,255,0.08);
    margin: 6px 16px;
}
QMenu::icon {
    padding-left: 16px;
}
"""

COMBO_STYLE = """
QComboBox {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 5px 30px 5px 15px;
    font-size: 13px;
    font-weight: bold;
}
QComboBox:hover {
    border: 1px solid rgba(16, 185, 129, 0.5);
    background-color: rgba(16, 185, 129, 0.05);
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left-width: 0px;
}
QComboBox QAbstractItemView {
    background-color: #1e293b;
    color: white;
    selection-background-color: rgba(16, 185, 129, 0.2);
    selection-color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    outline: none;
}
"""

class SmartPortfolioPage(QWidget):
    """The main table showing holdings (Portfolio) or transactions (Log)."""
    def __init__(self, notify_callback, parent=None, session=None):
        super().__init__(parent)
        self.notify_callback = notify_callback
        self.session = session
        self.manager = PortfolioManager(session=self.session)
        self.all_symbols = [] 
        
        # State
        self.view_mode = "portfolio"  # or "log"
        self.selection_mode = False
        self._header_animating = False
        self.current_client_filter = None # None means "All" for current context
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ═══════════════════════════════════════════════════════════════════
        #  HEADER BAR  (wraps two states: Normal vs Selection)
        # ═══════════════════════════════════════════════════════════════════
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(70)
        self.header_frame.setStyleSheet("""
            QFrame { background: transparent; border: none; }
            QLabel { background: transparent; border: none; }
        """)
        header_lay = QHBoxLayout(self.header_frame)
        header_lay.setContentsMargins(20, 10, 20, 10)
        header_lay.setSpacing(10)
        
        self.parent_app = parent
        self.last_live_data = {}
        
        # ── Title ──
        if self.session and self.session.role == ROLE_OWNER:
            title_text = "Platform Portfolios"
        elif self.session and self.session.role == ROLE_BROKER:
            title_text = "Client Portfolios"
        else:
            title_text = "My Smart Portfolio"
            
        self.title = QLabel(title_text)
        self.title.setStyleSheet(
            "font-size: 24px; font-weight: bold; font-family: Georgia, serif; "
            "font-style: italic; color: white;"
        )
        
        # ═══════════════════════════════════════════════════════════════════
        #  NORMAL-STATE BUTTONS  (right side of header in normal mode)
        # ═══════════════════════════════════════════════════════════════════
        self.normal_buttons = QWidget()
        nb_lay = QHBoxLayout(self.normal_buttons)
        nb_lay.setContentsMargins(0, 0, 0, 0)
        nb_lay.setSpacing(8)
        
        # Add filtering options if Broker or Owner
        if self.session and self.session.role in (ROLE_BROKER, ROLE_OWNER):
            self.client_filter = QComboBox()
            self.client_filter.setFixedSize(200, 38)
            self.client_filter.setStyleSheet(COMBO_STYLE)
            self._populate_client_filter()
            self.client_filter.currentIndexChanged.connect(self._on_client_filter_changed)
            nb_lay.addWidget(self.client_filter)
        
        # Export
        self.export_btn = QPushButton("📄 Export")
        self.export_btn.setObjectName("export_btn")
        self.export_btn.setFixedSize(110, 38)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.clicked.connect(self.export_report)
        
        # Add Stock
        self.add_btn = QPushButton("+ Add Stock")
        self.add_btn.setObjectName("add_btn")
        self.add_btn.setFixedSize(120, 38)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(lambda: self.show_add_dialog())
        
        # Three-dot menu button
        self.dots_btn = QPushButton("⋮")
        self.dots_btn.setFixedSize(42, 38)
        self.dots_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dots_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06);
                color: rgba(255,255,255,0.8);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 10px;
                font-size: 22px;
                font-weight: 900;
                letter-spacing: 2px;
            }
            QPushButton:hover {
                background: rgba(16, 185, 129, 0.15);
                color: #10b981;
                border: 1px solid rgba(16, 185, 129, 0.35);
            }
            QPushButton:pressed {
                background: rgba(16, 185, 129, 0.25);
            }
        """)
        self.dots_btn.clicked.connect(self._show_three_dot_menu)
        
        # Style normal buttons
        self._apply_btn_style(self.export_btn, False)
        self._apply_btn_style(self.add_btn, False)
        self.export_btn.installEventFilter(self)
        self.add_btn.installEventFilter(self)
        
        nb_lay.addWidget(self.export_btn)
        nb_lay.addWidget(self.add_btn)
        nb_lay.addWidget(self.dots_btn)
        
        # ═══════════════════════════════════════════════════════════════════
        #  SELECTION-STATE BUTTONS  (right side of header in selection mode)
        # ═══════════════════════════════════════════════════════════════════
        self.selection_buttons = QWidget()
        sb_lay = QHBoxLayout(self.selection_buttons)
        sb_lay.setContentsMargins(0, 0, 0, 0)
        sb_lay.setSpacing(10)
        
        # Cancel / Back Arrow
        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setFixedSize(42, 38)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                color: rgba(255,255,255,0.7);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.15);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
        """)
        self.cancel_btn.clicked.connect(self._exit_selection_mode)
        
        # Delete (Red Trash)
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setFixedSize(46, 38)
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.15);
                color: #ef4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 10px;
                font-size: 18px;
            }
            QPushButton:hover {
                background: #ef4444;
                color: white;
                border: 1px solid #ef4444;
            }
        """)
        self.delete_btn.clicked.connect(self.bulk_delete)
        self.delete_btn.hide()  # Hidden until ≥1 item checked
        
        sb_lay.addWidget(self.cancel_btn)
        sb_lay.addWidget(self.delete_btn)

        # Initially hide selection buttons
        self.selection_buttons.hide()
        
        # ── Assemble Header ──
        header_lay.addWidget(self.title)
        header_lay.addStretch()
        header_lay.addWidget(self.normal_buttons)
        header_lay.addWidget(self.selection_buttons)
        
        layout.addWidget(self.header_frame)

        # ═══════════════════════════════════════════════════════════════════
        #  TABLE
        # ═══════════════════════════════════════════════════════════════════
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(52) # Ensure enough space for buttons
        
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; outline: none; border: none; }
            QTableWidget::item:focus { outline: none; border: none; }
            QHeaderView::section { background-color: rgba(255,255,255,0.05); color: #10b981; padding: 12px; border: none; font-weight: bold; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }
        """)
        
        layout.addWidget(self.table)
        
        # ═══════════════════════════════════════════════════════════════════
        #  SUMMARY FOOTER
        # ═══════════════════════════════════════════════════════════════════
        self.summary_frame = QFrame()
        self.summary_frame.setFixedHeight(80)
        self.summary_frame.setStyleSheet("""
            QFrame { 
                background: rgba(255, 255, 255, 0.05); 
                border-top: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 0px; 
            }
            QLabel { background: transparent; border: none; }
        """)
        
        sum_lay = QHBoxLayout(self.summary_frame)
        sum_lay.setContentsMargins(30, 0, 30, 0)
        
        def create_sum_box(label_text):
            box = QVBoxLayout()
            box.setSpacing(2)
            title_lbl = QLabel(label_text)
            title_lbl.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 11px; font-weight: bold; text-transform: uppercase;")
            val_lbl = QLabel("Rs. 0.00")
            val_lbl.setStyleSheet("color: white; font-size: 18px; font-weight: 800;")
            box.addWidget(title_lbl)
            box.addWidget(val_lbl)
            return box, val_lbl

        self.box_inv, self.lbl_inv = create_sum_box("Total Invested")
        self.box_val, self.lbl_val = create_sum_box("Current Value")
        self.box_pl, self.lbl_pl = create_sum_box("Net Profit/Loss")
        
        sum_lay.addLayout(self.box_inv)
        sum_lay.addStretch()
        sum_lay.addLayout(self.box_val)
        sum_lay.addStretch()
        sum_lay.addLayout(self.box_pl)
        
        layout.addWidget(self.summary_frame)
        
        self.refresh_table()

    # ═══════════════════════════════════════════════════════════════════════
    #  ROLE-AWARE FILTERING
    # ═══════════════════════════════════════════════════════════════════════
    def _populate_client_filter(self):
        """Populate the dropdown based on the user's role and available clients."""
        self.client_filter.clear()
        self.client_filter.addItem("Aggregate (All Data)", userData=None)
        
        if self.session.role == ROLE_BROKER:
            clients = get_clients_for_broker(self.session.user_id)
            for c in clients:
                self.client_filter.addItem(f"Client: {c['name']}", userData=c['id'])
        elif self.session.role == ROLE_OWNER:
            clients = get_all_clients()
            for c in clients:
                self.client_filter.addItem(f"Client: {c['name']} (ID:{c['id']})", userData=c['id'])

    def _on_client_filter_changed(self, index):
        """Handle when the user selects a different client filter."""
        self.current_client_filter = self.client_filter.itemData(index)
        self.refresh_table()

    # ═══════════════════════════════════════════════════════════════════════
    #  THREE-DOT MENU
    # ═══════════════════════════════════════════════════════════════════════
    def _show_three_dot_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(MENU_STYLE)
        
        # View Options sub-section
        if self.view_mode == "portfolio":
            view_action = menu.addAction("📜  Switch to Log View")
        else:
            view_action = menu.addAction("📊  Switch to Portfolio View")
        view_action.triggered.connect(self.toggle_view_mode)
        
        menu.addSeparator()
        
        select_action = menu.addAction("☑️  Select Multiple")
        select_action.triggered.connect(self._enter_selection_mode)
        
        menu.addSeparator()
        
        delete_all_action = menu.addAction("🗑️  Delete All Data")
        delete_all_action.triggered.connect(self._delete_all_data)
        
        # Position below the dots button
        btn_pos = self.dots_btn.mapToGlobal(QPoint(0, self.dots_btn.height() + 4))
        # Align right edge of menu with right edge of button
        menu.exec(btn_pos)

    def toggle_view_mode(self):
        if self.view_mode == "portfolio":
            self.view_mode = "log"
            self._set_base_title("Transaction Log")
        else:
            self.view_mode = "portfolio"
            
            if self.session and self.session.role == ROLE_OWNER:
                self._set_base_title("Platform Portfolios")
            elif self.session and self.session.role == ROLE_BROKER:
                self._set_base_title("Client Portfolios")
            else:
                self._set_base_title("My Smart Portfolio")
            
        # Exit selection mode when switching views
        if self.selection_mode:
            self._exit_selection_mode()
        # Refresh
        self.refresh_table()

    def _set_base_title(self, text):
        self.title.setText(text)
        self.title.setStyleSheet(
            "font-size: 24px; font-weight: bold; font-family: Georgia, serif; "
            "font-style: italic; color: white;"
        )

    def _delete_all_data(self):
        filter_str = ""
        if self.current_client_filter:
            filter_str = " for the selected client"
            
        confirm = QMessageBox.critical(self, "⚠️ CRITICAL: Delete All Data",
            f"This will PERMANENTLY delete all transactions and alerts{filter_str}.\n\n"
            "Are you absolutely sure you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
            
        if confirm == QMessageBox.StandardButton.Yes:
            # Second confirmation for such a destructive action
            second_confirm = QMessageBox.warning(self, "Final Confirmation",
                "Are you REALLY sure? This cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
                
            if second_confirm == QMessageBox.StandardButton.Yes:
                self.manager.delete_all_data(specific_client_id=self.current_client_filter)
                self.refresh_table()
                self.notify_callback("🗑️ Data Reset", f"Portfolio data cleared{filter_str}.")

    # ═══════════════════════════════════════════════════════════════════
    #  SELECTION MODE: ENTER / EXIT  (WhatsApp-style contextual shift)
    # ═══════════════════════════════════════════════════════════════════
    def _enter_selection_mode(self):
        if self.selection_mode:
            return
        self.selection_mode = True
        
        # ── Transform header ──
        # 1. Tint the header background
        self.header_frame.setStyleSheet("""
            QFrame { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(16, 185, 129, 0.08), stop:1 rgba(30, 41, 59, 0.95));
                border: none;
                border-bottom: 1px solid rgba(16, 185, 129, 0.2);
            }
            QLabel { background: transparent; border: none; }
        """)
        
        # 2. Swap button groups
        self.normal_buttons.hide()
        self.selection_buttons.show()
        self.delete_btn.hide()  # Only show once ≥1 checked
        
        # 3. Title changes to count
        self.title.setText("0 Selected")
        self.title.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #10b981; "
            "font-family: 'Segoe UI', sans-serif; font-style: normal;"
        )
        
        # 4. Show checkboxes
        self.table.setColumnHidden(0, False)
        
        # Refresh to re-draw checkboxes
        self.refresh_table()

    def _exit_selection_mode(self):
        if not self.selection_mode:
            return
        self.selection_mode = False
        
        # ── Restore header ──
        self.header_frame.setStyleSheet("""
            QFrame { background: transparent; border: none; }
            QLabel { background: transparent; border: none; }
        """)
        
        # Swap button groups back
        self.selection_buttons.hide()
        self.normal_buttons.show()
        self.delete_btn.hide()
        
        # Restore title
        if self.view_mode == "portfolio":
            if self.session and self.session.role == ROLE_OWNER:
                self._set_base_title("Platform Portfolios")
            elif self.session and self.session.role == ROLE_BROKER:
                self._set_base_title("Client Portfolios")
            else:
                self._set_base_title("My Smart Portfolio")
        else:
            self._set_base_title("Transaction Log")
            
        # Hide checkboxes
        self.table.setColumnHidden(0, True)

    def refresh_table(self):
        self.table.setRowCount(0)
        self.table.clearContents()
        
        if self.view_mode == "portfolio":
            self.setup_portfolio_view()
        else:
            self.setup_log_view()
            
        self.table.setColumnHidden(0, not self.selection_mode)
        
        # Trigger price update if we have data
        if self.last_live_data:
            self.update_prices(self.last_live_data)
        else:
             # Calculate static totals if we don't have live data yet
             self.calculate_static_totals()

    def setup_portfolio_view(self):
        # Columns: [Select, Symbol, Qty, Avg Price, Current, P/L, Alerts, Action]
        columns = ["", "Symbol", "Qty", "Avg Price", "Current", "P/L", "Alerts", "Action"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        
        data = self.manager.get_aggregated_portfolio(specific_client_id=self.current_client_filter)
        self.table.setRowCount(len(data))
        
        for row, (sym, info) in enumerate(data.items()):
            # col 0: Checkbox
            self._add_checkbox(row)
            
            # col 1-7
            self.table.setItem(row, 1, QTableWidgetItem(sym))
            self.table.setItem(row, 2, QTableWidgetItem(str(info['quantity'])))
            self.table.setItem(row, 3, QTableWidgetItem(f"{info['buy_price']:.2f}"))
            
            curr_item = QTableWidgetItem("---")
            curr_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, curr_item)
            
            pl_item = QTableWidgetItem("---")
            pl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, pl_item)
            
            alerts = []
            if info['limit_upper'] > 0: alerts.append(f"↑ {info['limit_upper']}")
            if info['limit_lower'] > 0: alerts.append(f"↓ {info['limit_lower']}")
            status = " | ".join(alerts) if alerts else "None"
            self.table.setItem(row, 6, QTableWidgetItem(status))
            
            # Action: Remove Stock (Clear Position)
            action_container = QWidget()
            action_lay = QHBoxLayout(action_container)
            action_lay.setContentsMargins(0, 0, 0, 0)
            action_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn = QPushButton("Clear")
            self._style_remove_btn(btn)
            btn.clicked.connect(lambda ch, s=sym: self.remove_stock(s))
            action_lay.addWidget(btn)
            self.table.setCellWidget(row, 7, action_container)

    def setup_log_view(self):
        # Columns: [Select, Date, Type, Symbol, Qty, Price, Total, ID (Hidden)]
        columns = ["", "Date", "Type", "Symbol", "Qty", "Price", "Total", "ID"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        
        # Hide ID column
        self.table.setColumnHidden(7, True)
        
        transactions = self.manager.get_transactions(specific_client_id=self.current_client_filter)
        # sort by date desc is already handled by SQL, but we reverse it for UI order just in case
        transactions = sorted(transactions, key=lambda x: x['date'], reverse=True)
        
        self.table.setRowCount(len(transactions))
        
        for row, t in enumerate(transactions):
            self._add_checkbox(row)
            
            self.table.setItem(row, 1, QTableWidgetItem(t['date']))
            
            type_item = QTableWidgetItem(t['type'])
            if t['type'] == "BUY":
                type_item.setForeground(QColor("#10b981"))
            else: # SELL
                type_item.setForeground(QColor("#ef4444"))
            self.table.setItem(row, 2, type_item)
            
            self.table.setItem(row, 3, QTableWidgetItem(t['symbol']))
            self.table.setItem(row, 4, QTableWidgetItem(str(t['quantity'])))
            self.table.setItem(row, 5, QTableWidgetItem(f"{t['price']:.2f}"))
            
            total = t['quantity'] * t['price']
            self.table.setItem(row, 6, QTableWidgetItem(f"{total:,.2f}"))
            
            self.table.setItem(row, 7, QTableWidgetItem(str(t['id']))) # String since ID is Int from DB

    def _add_checkbox(self, row):
        container = QWidget()
        lay = QHBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        ck = QCheckBox()
        ck.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #555;
                border-radius: 4px;
                background: #1e1e2e;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #10b981;
            }
            QCheckBox::indicator:checked {
                background-color: #10b981;
                border: 2px solid #10b981;
            }
        """)
        ck.setCursor(Qt.CursorShape.PointingHandCursor)
        lay.addWidget(ck)
        self.table.setCellWidget(row, 0, container)
        
        # Connect clicked to highlight
        ck.stateChanged.connect(lambda state, r=row: self._highlight_row(r, state))
        ck.stateChanged.connect(self.update_header_selection_count)
        
    def _highlight_row(self, row, state):
        # User requested: "Highlight selected rows with a distinct background color (e.g., light blue)"
        # Since we use dark theme mainly, we use a subtle blue tint.
        is_selected = (state == 2) # Qt.CheckState.Checked
        color = QColor(37, 99, 235, 40) if is_selected else QColor(0,0,0,0)
        
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(color)
        
        self.update_header_selection_count()

    def update_header_selection_count(self):
        count = 0
        for row in range(self.table.rowCount()):
            cell = self.table.cellWidget(row, 0)
            if cell:
                ck = cell.findChild(QCheckBox)
                if ck and ck.isChecked():
                    count += 1
        
        if self.selection_mode:
            self.title.setText(f"{count} Selected")
            # Show/hide delete based on selection count
            if count > 0:
                self.delete_btn.show()
            else:
                self.delete_btn.hide()

    def bulk_delete(self):
        if self.view_mode == "log":
            ids_to_delete = []
            for row in range(self.table.rowCount()):
                cell = self.table.cellWidget(row, 0)
                if cell:
                    ck = cell.findChild(QCheckBox)
                    if ck and ck.isChecked():
                        t_id_item = self.table.item(row, 7) # ID col
                        if t_id_item:
                             ids_to_delete.append(int(t_id_item.text()))
            
            if not ids_to_delete: return
            
            confirm = QMessageBox.question(self, "Confirm Delete", 
                f"Are you sure you want to delete {len(ids_to_delete)} transactions?\nThis cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
            if confirm == QMessageBox.StandardButton.Yes:
                self.manager.delete_transactions(ids_to_delete)
                self.refresh_table()
                self.notify_callback("🗑️ Deleted", f"Removed {len(ids_to_delete)} transactions.")
                self._exit_selection_mode() # Exit selection mode
                
        else: # Portfolio mode
            # Deleting stocks means clearing position 
            symbols_to_remove = []
            for row in range(self.table.rowCount()):
                cell = self.table.cellWidget(row, 0)
                if cell:
                    ck = cell.findChild(QCheckBox)
                    if ck and ck.isChecked():
                        sym = self.table.item(row, 1).text()
                        symbols_to_remove.append(sym)

            if not symbols_to_remove: return

            confirm = QMessageBox.question(self, "Confirm Delete", 
                f"Are you sure you want to remove {len(symbols_to_remove)} stocks?\nThis will delete ALL history for these stocks.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if confirm == QMessageBox.StandardButton.Yes:
                for s in symbols_to_remove:
                    self.manager.remove_stock(s, specific_client_id=self.current_client_filter) 
                self.refresh_table()
                self.notify_callback("🗑️ Deleted", f"Removed {len(symbols_to_remove)} stocks.")
                self._exit_selection_mode()

    def remove_stock(self, sym):
        confirm = QMessageBox.question(self, "Confirm Remove", 
            f"Remove {sym} and all its history?", 
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.manager.remove_stock(sym, specific_client_id=self.current_client_filter)
            self.refresh_table()

    def _style_remove_btn(self, btn):
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(30)
        btn.setMinimumWidth(80)
        btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.08);
                color: rgba(239, 68, 68, 0.95);
                font-size: 11px;
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.25);
                color: #ffffff;
                border: 1px solid #ef4444;
            }
        """)

    def show_add_dialog(self, symbol_prefill=""):
        d = QDialog(self)
        d.setWindowTitle("Add Transaction")
        d.setFixedSize(350, 450) if self.session and self.session.role in (ROLE_BROKER, ROLE_OWNER) else d.setFixedSize(350, 400)
        d.setStyleSheet("QDialog { background: #1a1a2e; color: white; } QLabel { color: #ccc; } QLineEdit, QComboBox { background: #0f0f1a; color: white; border: 1px solid #333; padding: 8px; } QPushButton { background: #10b981; color: white; border-radius: 5px; padding: 10px; }")
        
        lay = QFormLayout(d)
        
        # Target client selector if Broker/Owner
        target_client_id = None
        if self.session and self.session.role in (ROLE_BROKER, ROLE_OWNER):
            c_select = QComboBox()
            c_select.addItem("My Internal Portfolio (Self)", userData=self.session.user_id)
            
            if self.session.role == ROLE_BROKER:
                for c in get_clients_for_broker(self.session.user_id):
                    c_select.addItem(f"Client: {c['name']}", userData=c['id'])
            elif self.session.role == ROLE_OWNER:
                for c in get_all_clients():
                    c_select.addItem(f"Client: {c['name']} (ID:{c['id']})", userData=c['id'])
                    
            # Auto-select the currently filtered client
            if self.current_client_filter:
                index = c_select.findData(self.current_client_filter)
                if index >= 0:
                    c_select.setCurrentIndex(index)
                    
            lay.addRow("Add To:", c_select)
        
        i_sym = QLineEdit(symbol_prefill)
        if self.all_symbols:
            completer = QCompleter(self.all_symbols)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            i_sym.setCompleter(completer)
            
        lay.addRow("Symbol:", i_sym)
        i_qty = QLineEdit("0"); lay.addRow("Quantity:", i_qty)
        i_buy = QLineEdit("0.0"); lay.addRow("Price:", i_buy)
        
        i_hi = QLineEdit("0.0"); lay.addRow("Take Profit (Upper):", i_hi)
        i_lo = QLineEdit("0.0"); lay.addRow("Stop Loss (Lower):", i_lo)
        
        def save_stock():
            nonlocal target_client_id
            if self.session and self.session.role in (ROLE_BROKER, ROLE_OWNER):
                target_client_id = c_select.currentData()
            else:
                target_client_id = self.session.user_id if self.session else None
                
            try:
                sym = i_sym.text().strip().upper()
                if not sym:
                    QMessageBox.warning(d, "Input Error", "Please enter a valid stock symbol.")
                    return
                
                try:
                    qty = int(i_qty.text().strip())
                    buy = float(i_buy.text().strip())
                    hi = float(i_hi.text().strip())
                    lo = float(i_lo.text().strip())
                except ValueError:
                    QMessageBox.warning(d, "Input Error", "Invalid numbers.")
                    return

                self.manager.add_or_update_stock(sym, qty, buy, hi, lo, client_id=target_client_id)
                d.accept()
                self.refresh_table()
                
            except Exception as e:
               QMessageBox.critical(d, "Error", f"Error: {str(e)}")

        btn = QPushButton("Save Transaction")
        btn.clicked.connect(save_stock)
        lay.addRow(btn)
        
        d.exec()

    def update_prices(self, live_data_map):
        self.last_live_data = live_data_map
        
        if self.view_mode == "portfolio":
            for row in range(self.table.rowCount()):
                sym = self.table.item(row, 1).text() # col 1 is symbol
                if sym in live_data_map:
                    curr = live_data_map[sym]
                    # col 3 is Avg Price, col 4 is Current
                    self.table.item(row, 4).setText(f"{curr:.2f}")
                    
                    # Calculate P/L
                    qty_item = self.table.item(row, 2)
                    avg_item = self.table.item(row, 3)
                    
                    if qty_item and avg_item:
                         qty = int(qty_item.text())
                         avg = float(avg_item.text())
                         pl = (curr - avg) * qty
                         
                         pl_item = self.table.item(row, 5)
                         pl_item.setText(f"{pl:+.2f}")
                         pl_item.setForeground(QColor("#10b981") if pl >= 0 else QColor("#ef4444"))
                    
                    # Check alerts
                    alerts = self.manager.alerts.get(sym, {})
                    up = alerts.get("limit_upper", 0)
                    lo = alerts.get("limit_lower", 0)
                    
                    if up > 0 and curr >= up:
                        self.notify_callback("🚀 Take Profit!", f"{sym} @ {curr}")
                    if lo > 0 and curr <= lo:
                        self.notify_callback("📉 Stop Loss!", f"{sym} @ {curr}")

        # Update Totals (Always)
        total_inv = 0
        total_curr = 0
        
        # Re-calculate totals from ALL aggregated data, not just table rows
        agg_data = self.manager.get_aggregated_portfolio(specific_client_id=self.current_client_filter)
        
        for sym, info in agg_data.items():
            qty = info['quantity']
            buy = info['buy_price'] # Avg
            
            total_inv += (qty * buy)
            
            c_price = live_data_map.get(sym, buy)
            total_curr += (qty * c_price)
            
        total_pl = total_curr - total_inv
        
        self.lbl_inv.setText(f"Rs. {total_inv:,.2f}")
        self.lbl_val.setText(f"Rs. {total_curr:,.2f}")
        self.lbl_pl.setText(f"Rs. {total_pl:+,.2f}")
        
        if total_pl > 0: self.lbl_pl.setStyleSheet("color: #10b981; font-size: 18px; font-weight: 800;")
        elif total_pl < 0: self.lbl_pl.setStyleSheet("color: #ef4444; font-size: 18px; font-weight: 800;")
        else: self.lbl_pl.setStyleSheet("color: white; font-size: 18px; font-weight: 800;")

    def calculate_static_totals(self):
         # Just calc invested from aggregated
         agg_data = self.manager.get_aggregated_portfolio(specific_client_id=self.current_client_filter)
         total_inv = 0
         for sym, info in agg_data.items():
             total_inv += (info['quantity'] * info['buy_price'])
         
         self.lbl_inv.setText(f"Rs. {total_inv:,.2f}")
         # Current Value = Invested (initially)
         self.lbl_val.setText(f"Rs. {total_inv:,.2f}")
         self.lbl_pl.setText("Rs. +0.00")

    def update_all_symbols(self, symbols):
        self.all_symbols = symbols
    
    def _apply_btn_style(self, btn, is_hovered):
        # Simplified stpler
        is_dark = True
        border_col = "#10b981"
        bg_col = "#10b981"
        
        if hasattr(self, 'delete_btn') and btn == self.delete_btn: return
        if hasattr(self, 'cancel_btn') and btn == self.cancel_btn: return

        if is_hovered:
            btn.setStyleSheet(f"QPushButton {{ background-color: {bg_col}; color: white; border: 1px solid {border_col}; border-radius: 10px; font-size: 13px; font-weight: bold; }}")
        else:
            btn.setStyleSheet("QPushButton { background-color: rgba(255, 255, 255, 0.08); color: rgba(255, 255, 255, 0.7); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 10px; font-size: 13px; font-weight: bold; }")
    
    def eventFilter(self, obj, event):
        if event.type() in [QEvent.Type.Enter, QEvent.Type.Leave]:
            is_hovered = (event.type() == QEvent.Type.Enter)
            if obj in [self.export_btn, self.add_btn]:
                self._apply_btn_style(obj, is_hovered)
        return super().eventFilter(obj, event)

    
    def export_report(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Export Portfolio Report", "portfolio_report", "Excel Files (*.xlsx);;PDF Files (*.pdf)"
        )
        if not file_path: return
        
        if "xlsx" in selected_filter: self.export_excel(file_path)
        elif "pdf" in selected_filter: self.export_pdf(file_path)
    
    def export_excel(self, file_path):
        try:
            from ...core.reports import ExcelReportGenerator
            reporter = ExcelReportGenerator(
                self.parent_app.settings_manager if self.parent_app else None
            )
            reporter.generate_report(
                file_path,
                self.manager.get_transactions(specific_client_id=self.current_client_filter),
                self.manager.get_aggregated_portfolio(specific_client_id=self.current_client_filter),
                live_data=self.last_live_data
            )
            self.notify_callback("✅ Export Complete", "Professional Excel report saved.")
        except ImportError as e:
            self.notify_callback("❌ Missing Library", str(e))
        except Exception as e:
            self.notify_callback("❌ Excel Export Failed", str(e))
    
    def export_pdf(self, file_path):
        try:
            from ...core.reports import PDFReportGenerator
            reporter = PDFReportGenerator(
                self.parent_app.settings_manager if self.parent_app else None
            )
            reporter.generate_report(
                file_path,
                self.manager.get_transactions(specific_client_id=self.current_client_filter),
                self.manager.get_aggregated_portfolio(specific_client_id=self.current_client_filter),
                live_data=self.last_live_data
            )
            self.notify_callback("✅ Export Complete", "Professional PDF report saved.")
        except ImportError as e:
            self.notify_callback("❌ Missing Library", str(e))
        except Exception as e:
            self.notify_callback("❌ PDF Export Failed", str(e))

