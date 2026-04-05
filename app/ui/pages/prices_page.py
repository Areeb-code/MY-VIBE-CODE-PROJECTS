from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView, 
                             QAbstractItemView, QTableWidgetItem)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class PricesPage(QWidget):
    """Shows a simple list of all fetched market prices."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Symbol", "Name", "Price", "Change"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.table.setStyleSheet("QTableWidget { background: transparent; border: none; outline: none; } QTableWidget::item:focus { outline: none; border: none; } QHeaderView::section { background: rgba(255,255,255,0.05); color: #10b981; border:none; padding:10px; } QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }")
        layout.addWidget(self.table)
        
    def update_data(self, data):
        self.table.setRowCount(len(data))
        for row, s in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(s['symbol']))
            self.table.setItem(row, 1, QTableWidgetItem(s['name']))
            
            p_item = QTableWidgetItem(f"{s['price']:.2f}")
            p_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 2, p_item)
            
            chg = s.get('change', 0.0)
            c_item = QTableWidgetItem(f"{chg:+.2f}")
            c_item.setForeground(QColor("#10b981") if chg >= 0 else QColor("#ef4444"))
            c_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, c_item)
