from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, 
                             QScrollArea, QPushButton, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor

class SearchPage(QWidget):
    """A prominent search interface for finding stock symbols."""
    def __init__(self, add_to_watchlist_callback, parent=None):
        super().__init__(parent)
        self.add_to_watchlist = add_to_watchlist_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_container.setStyleSheet("""
            #searchContainer {
                background-color: #1a1a2e;
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 30px;
                padding: 10px 25px;
            }
            #searchContainer:focus-within {
                border: 1px solid #10b981;
            }
        """)
        
        search_layout = QHBoxLayout(search_container)
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("background: transparent; color: white;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search symbols (e.g. KEL, OGDC, HBL)...")
        self.search_input.setStyleSheet("border: none; background: transparent; color: white; font-size: 18px;")
        self.search_input.textChanged.connect(self.update_results)
        search_layout.addWidget(self.search_input)
        
        layout.addWidget(search_container)
        
        self.results_tip = QLabel("Type at least 2 characters to search...")
        self.results_tip.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 14px; padding-left: 20px;")
        layout.addWidget(self.results_tip)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.results_widget)
        
        layout.addWidget(self.scroll)
        
        self.all_symbols = [
            {"symbol": "KEL", "name": "K-Electric Limited"},
            {"symbol": "OGDC", "name": "Oil & Gas Dev. Co."},
            {"symbol": "HBL", "name": "Habib Bank Limited"},
            {"symbol": "PSO", "name": "Pakistan State Oil"},
            {"symbol": "LUCK", "name": "Lucky Cement"},
            {"symbol": "SYS", "name": "Systems Limited"},
            {"symbol": "ENGRO", "name": "Engro Corporation"},
            {"symbol": "MCB", "name": "MCB Bank Limited"},
        ]
    
    def update_symbols(self, live_data):
        self.all_symbols = live_data
        self.results_tip.setText(f"Loaded {len(live_data)} real PSX stocks! Try searching...")
    
    def update_results(self, text):
        while self.results_layout.count():
            child = self.results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if len(text) < 2:
            self.results_tip.show()
            return
        
        self.results_tip.hide()
        matches = [s for s in self.all_symbols if text.upper() in s["symbol"] or text.upper() in s["name"].upper()]
        
        for match in matches:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.03);
                    border: none;
                    border-radius: 10px;
                    margin-bottom: 5px;
                }
                QFrame:hover {
                    background-color: rgba(16, 185, 129, 0.1);
                }
            """)
            
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(20, 15, 20, 15)
            
            sym_lbl = QLabel(match["symbol"])
            sym_lbl.setStyleSheet("color: #10b981; font-weight: bold; font-size: 18px; background: transparent;")
            card_layout.addWidget(sym_lbl)
            
            name_lbl = QLabel(match["name"])
            name_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 13px;")
            card_layout.addWidget(name_lbl)
            
            card_layout.addStretch()
            
            price = match.get("price", 0.0)
            percent = match.get("percent", 0.0)
            
            price_lbl = QLabel(f"Rs. {price:.2f}")
            price_lbl.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
            card_layout.addWidget(price_lbl)
            
            change_text = f"+{percent:.2f}%" if percent >= 0 else f"{percent:.2f}%"
            percent_lbl = QLabel(change_text)
            if percent > 0:
                percent_lbl.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
            elif percent < 0:
                percent_lbl.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
            else:
                percent_lbl.setStyleSheet("color: gray; font-size: 12px;")
            card_layout.addWidget(percent_lbl)
            
            card_layout.addSpacing(20)
            
            add_btn = QPushButton("➕ Portfolio")
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet("""
                QPushButton { background-color: #10b981; color: white; border: none; border-radius: 5px; padding: 5px 15px; font-weight: bold; }
                QPushButton:hover { background-color: #0d9668; }
            """)
            add_btn.clicked.connect(lambda checked, s=match["symbol"]: self.add_to_watchlist(s))
            
            card_layout.addWidget(add_btn)
            self.results_layout.addWidget(card)

        if not matches:
            no_res = QLabel(f"No results found for '{text}'")
            no_res.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_res.setStyleSheet("color: rgba(255, 255, 255, 0.4); padding: 40px;")
            self.results_layout.addWidget(no_res)
