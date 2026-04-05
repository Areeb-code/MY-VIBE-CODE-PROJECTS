# ═══════════════════════════════════════════════════════════════════════════════
# HANDS: THE SCRAPER LOGIC - Grabs real data from PSX website
# ═══════════════════════════════════════════════════════════════════════════════

# Import requests for downloading web pages
import requests

# Import BeautifulSoup for parsing the HTML
from bs4 import BeautifulSoup

class PSXScraper:
    """The 'Hands' of the app - reaches out to the internet for data."""
    
    # URL of the PSX Market Watch page
    URL = "https://dps.psx.com.pk/market-watch"
    
    # This method fetches and parses the data
    def fetch_all_stocks(self):
        
        # List to store all our stock data
        stock_list = []
        
        # Try to download the page
        try:
            
            # Send GET request to PSX
            response = requests.get(self.URL, timeout=10)
            
            # Check if request was successful
            if response.status_code != 200:
                return []
            
            # Create the 'translator' (soup)
            soup = BeautifulSoup(response.text, "lxml")
            
            # Find all table rows
            rows = soup.find_all("tr")
            
            # Loop through rows (skip the first header row)
            for row in rows[1:]:
                
                # Get all cells in this row
                cells = row.find_all("td")
                
                # Check if we have enough cells (PSX usually has ~13 columns)
                if len(cells) >= 10:
                    
                    # Extract data from columns (Indices based on PSX Data Portal)
                    # 0: Symbol, 1: Name, 6: Current Price, 7: Change, 8: % Change
                    symbol = cells[0].text.strip()
                    name = cells[1].text.strip()
                    
                    # Clean up price (remove commas)
                    price_str = cells[6].text.strip().replace(",", "")
                    change_str = cells[7].text.strip().replace(",", "")
                    percent_str = cells[8].text.strip().replace("%", "")
                    
                    # Convert to numbers if possible
                    try:
                        price = float(price_str)
                        change = float(change_str)
                        percent = float(percent_str)
                    except ValueError:
                        price = 0.0
                        change = 0.0
                        percent = 0.0
                    
                    # Create a dictionary for this stock
                    stock_data = {
                        "symbol": symbol,
                        "name": name,
                        "price": price,
                        "change": change,
                        "percent": percent
                    }
                    
                    # Add to our list
                    stock_list.append(stock_data)
                    
            # Return the full list of stock data
            return stock_list
            
        # If internet is down or error occurs, return empty list
        except requests.exceptions.RequestException as e:
            print(f"Scraper Network Error: {e}")
            return []
        except Exception as e:
            print(f"Scraper Gen Error: {e}")
            return []

    # This method fetches latest news from Google News RSS
    def fetch_market_news(self):
        
        # Google News RSS URL for "Pakistan Stock Exchange"
        news_url = "https://news.google.com/rss/search?q=Pakistan+Stock+Exchange+PSX&hl=en-PK&gl=PK&ceid=PK:en"
        
        try:
            # Fetch the XML feed
            response = requests.get(news_url, timeout=10)
            
            # Check success
            if response.status_code != 200:
                return []
            
            # Use BeautifulSoup to parse XML (features='xml')
            # If lxml-xml is not installed, it might fall back, but 'xml' is safer for RSS
            soup = BeautifulSoup(response.content, features="xml")
            
            # Find all <item> tags
            items = soup.find_all("item")
            
            news_list = []
            
            # Loop through first 10 items
            for item in items[:10]:
                
                title = item.title.text if item.title else "No Title"
                link = item.link.text if item.link else "#"
                pub_date = item.pubDate.text if item.pubDate else "Just now"
                
                # Clean up date (Example: "Mon, 27 Jan 2026 05:00:00 GMT" -> "27 Jan 2026")
                # Simple split logic to shorten it
                try:
                    parts = pub_date.split(" ")
                    short_date = f"{parts[0]} {parts[1]} {parts[2]} {parts[3]}"
                except:
                    short_date = pub_date
                
                news_list.append({
                    "title": title,
                    "date": short_date,
                    "link": link,
                    "source": "Google News"
                })
                
            return news_list
            
        except requests.exceptions.RequestException as e:
            print(f"News Network Error: {e}")
            return [
                {"title": "Offline: Check Internet Connection", "date": "Now", "source": "System"},
                {"title": "Could not fetch latest news", "date": "Today", "source": "System"}
            ]
        except Exception as e:
            print(f"News Scraper Error: {e}")
            # Fallback sample news if internet fails
            return [
                {"title": "PSX Hits New Highs Amid Positive Sentiment", "date": "Today", "source": "Sample News"},
                {"title": "Market Watch: KSE-100 Index Analysis", "date": "Yesterday", "source": "Sample News"}
            ]

# Simple test code
if __name__ == "__main__":
    scraper = PSXScraper()
    data = scraper.fetch_all_stocks()
    print(f"Fetched {len(data)} stocks!")
    if data:
        print(f"Example: {data[0]}")