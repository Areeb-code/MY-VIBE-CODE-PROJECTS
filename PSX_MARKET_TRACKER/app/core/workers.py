from PyQt6.QtCore import QThread, pyqtSignal
# Import from the sibling scraper module
from .scraper import PSXScraper

class ScraperThread(QThread):
    """Background worker that asks the scraper for real data."""
    data_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def run(self):
        try:
            scraper = PSXScraper()
            data = scraper.fetch_all_stocks()
            if data:
                self.data_received.emit(data)
            else:
                self.error_occurred.emit("Could not fetch data.")
        except Exception as e:
            self.error_occurred.emit(str(e))

class NewsLoaderThread(QThread):
    """Background worker that fetches Google News RSS."""
    news_received = pyqtSignal(list)
    
    def run(self):
        try:
            scraper = PSXScraper()
            news = scraper.fetch_market_news()
            self.news_received.emit(news)
        except:
            self.news_received.emit([])
