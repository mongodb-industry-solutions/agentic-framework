import os
from scrapers.news_scraper import NewsScraper

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Example usage
if __name__ == "__main__":

    # Initialize the scraper
    scraper = NewsScraper(
        collection_name=os.getenv("NEWS_SCRAPED_COLLECTION"),
        scrape_num_articles=int(3)
    )

    # List of tickers to scrape
    tickers = [
        "SPY", "QQQ", "EEM", "XLE", "TLT", "LQD", "HYG", "HYG", "GLD", "USO", "VIX"
    ]

    # Scrape all tickers
    scraper.scrape_all_tickers(tickers)
   