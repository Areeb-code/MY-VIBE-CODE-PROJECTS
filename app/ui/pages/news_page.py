from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QScrollArea, QHBoxLayout, 
                             QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QCursor
from ...core.workers import NewsLoaderThread

class ClickableFrame(QFrame):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def mousePressEvent(self, event):
        if self.url:
            QDesktopServices.openUrl(QUrl(self.url))
        super().mousePressEvent(event)

class NewsPage(QWidget):
    """A page showing the latest market news and announcements."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title = QLabel("Market News Feed")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        layout.addWidget(title)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background: transparent;")
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll.setWidget(self.list_widget)
        layout.addWidget(self.scroll)
        
        self.load_news()
    
    def load_news(self):
        # Clear existing
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.list_widget)
        
        loading_lbl = QLabel("Fetching latest market news...")
        loading_lbl.setStyleSheet("color: #10b981; font-size: 16px; margin: 20px;")
        loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.list_layout.addWidget(loading_lbl)
        
        self.news_thread = NewsLoaderThread()
        self.news_thread.news_received.connect(self.display_news)
        self.news_thread.start()
        
    def display_news(self, news_items):
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not news_items:
            error_lbl = QLabel("No news available at the moment.")
            error_lbl.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 16px;")
            self.list_layout.addWidget(error_lbl)
            return

        for item in news_items:
            self.create_news_card(item)
            
    def create_news_card(self, item):
        card = ClickableFrame(item.get("link", ""))
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
                margin-bottom: 20px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(16, 185, 129, 0.3);
            }
        """)
        
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 30))
        card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(25, 25, 25, 25)
        
        header_layout = QHBoxLayout()
        
        source_lbl = QLabel(item.get("source", "News"))
        source_lbl.setStyleSheet("color: #10b981; font-weight: bold; border: none; background: transparent;")
        header_layout.addWidget(source_lbl)
        
        header_layout.addStretch()
        
        date_lbl = QLabel(item.get("date", ""))
        date_lbl.setProperty("class", "desc-text") 
        date_lbl.setStyleSheet("font-size: 12px; border: none; background: transparent;")
        header_layout.addWidget(date_lbl)
        
        card_layout.addLayout(header_layout)
        
        title_lbl = QLabel(item.get("title", ""))
        title_lbl.setProperty("class", "title-text")
        title_lbl.setStyleSheet("font-size: 17px; font-weight: 600; margin-top: 5px; border: none; background: transparent;")
        title_lbl.setWordWrap(True)
        card_layout.addWidget(title_lbl)
        
        link_lbl = QLabel("Read full story ↗")
        link_lbl.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 500; margin-top: 15px; border: none; background: transparent;")
        card_layout.addWidget(link_lbl)
        
        self.list_layout.addWidget(card)
