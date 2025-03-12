import re
import requests
from time import sleep
from bs4 import BeautifulSoup
from db.mongo_db import MongoDBConnector
from scrapers.generic_scraper import GenericScraper
from datetime import datetime, timedelta, timezone

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class NewsScraper(GenericScraper):
    def __init__(self, collection_name, scrape_num_articles=1):
        """
        Initialize the NewsScraper with necessary parameters.
        """
        self.headers = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://www.google.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.44'
        }

        self.collection_name = collection_name
        self.scrape_num_articles = scrape_num_articles
        self.mongo_client = MongoDBConnector()

    @staticmethod
    def extract_article(card, ticker):
        """
        Extract article information from the raw HTML.
        """
        extraction_timestamp = datetime.now(timezone.utc)

        headline = card.find('h4', 's-title').text
        source = card.find("span", 's-source').text
        posted = card.find('span', 's-time').text.replace('·', '').strip()
        description = card.find('p', 's-desc').text.strip()
        raw_link = card.find('a').get('href')
        unquoted_link = requests.utils.unquote(raw_link)
        pattern = re.compile(r'RU=(.+)\/RK')
        clean_link = re.search(pattern, unquoted_link).group(1)

        # Extract hours from "posted" (e.g., "5 hours ago")
        hours_ago_match = re.search(r'(\d+) hour', posted)
        hours_ago = int(hours_ago_match.group(1)) if hours_ago_match else 0

        # Calculate published timestamp
        published_timestamp = extraction_timestamp - timedelta(hours=hours_ago)

        return {
            'headline': headline,
            'source': source,
            'posted': posted,
            'description': description,
            'link': clean_link,
            'synced': False,
            'extraction_timestamp': extraction_timestamp.isoformat(),
            'published_timestamp': published_timestamp.isoformat(),
            'ticker': ticker  # Add the ticker field
        }

    def scrape_articles(self, search_query):
        """
        Scrape news articles for a specific search query.
        """
        template = 'https://news.search.yahoo.com/search?p={}'
        url = template.format(search_query)
        articles = []
        links = set()
        num_search = self.scrape_num_articles

        while num_search:
            num_search -= 1
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('div', 'NewsArticle')

            # Extract articles from the page
            for card in cards:
                article = self.extract_article(card, search_query)
                link = article['link']
                if link not in links:
                    links.add(link)
                    articles.append(article)

            # Find the next page
            try:
                url = soup.find('a', 'next').get('href')
                sleep(1)
            except AttributeError:
                break

        # Insert articles into MongoDB
        if articles:
            self.mongo_client.insert_many(self.collection_name, articles)
            logging.info(f"Inserted {len(articles)} articles into MongoDB.")

        return articles

    def scrape_all_tickers(self, tickers):
        """
        Scrape news articles for a list of tickers.
        """
        for ticker in tickers:
            logging.info(f"Scraping news for ticker: {ticker}")
            try:
                self.scrape_articles(ticker)
            except Exception as e:
                logging.error(f"Error while scraping news for {ticker}: {e}")
