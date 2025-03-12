from db.mongo_db import MongoDBConnector
from loaders.csv_loader import CSVLoader
from embeddings.financial_news_embeddings import create_article_string, all_articles_embedding
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def timestring_to_utc(time_str):
    """
    Convert a given time string in the format '7:51  PM ET Fri, 17 July 2020' to UTC timestamp.
    """
    from datetime import datetime
    import pytz

    # Normalize spaces (remove multiple spaces)
    time_str = " ".join(time_str.split())

    # Define the Eastern Time Zone
    eastern = pytz.timezone('US/Eastern')

    # Define possible date formats
    date_formats = [
        "%I:%M %p ET %a, %d %B %Y",  # Full month name
        "%I:%M %p ET %a, %d %b %Y"   # Abbreviated month name
    ]

    # Try parsing with both formats
    for date_format in date_formats:
        try:
            local_time = datetime.strptime(time_str, date_format)
            break  # Exit loop if parsing is successful
        except ValueError:
            continue
    else:
        raise ValueError(
            f"Time format does not match expected formats: {time_str}")

    # Localize to Eastern Time
    local_time = eastern.localize(local_time)

    # Convert to UTC
    utc_time = local_time.astimezone(pytz.utc)

    return utc_time.isoformat()

# ==================
# Example usage
# ==================


if __name__ == "__main__":
    # Provide a relative path to the CSV file
    # https://www.kaggle.com/datasets/notlucasp/financial-news-headlines?resource=download
    loader = CSVLoader(filepath="data/fsi/financial_news_headlines.csv")
    df_articles = loader.load()

    # Convert "Time" column to UTC timestamp
    df_articles["published_timestamp_utc"] = df_articles["Time"].apply(timestring_to_utc)

    # Rename columns and reorder: headlines, description, time, published_timestamp_utc
    df_articles = df_articles.rename(columns={
        "Headlines": "headlines",
        "Time": "time",
        "Description": "description"
    })
    df_articles = df_articles[["headlines", "description", "time", "published_timestamp_utc"]]

    # Apply the function to all articles
    df_articles["article_string"] = df_articles.apply(create_article_string, axis=1)

    # Generate embeddings for all articles
    df_articles = all_articles_embedding(df_articles)
    logging.info(f"Generated embeddings for {len(df_articles)} articles.")

    # Check the first few rows
    df_articles.head()

    logging.info(f"Converting DataFrame to a list of dictionaries.")
    news_articles_dict = df_articles.to_dict("records")

    # Connect to MongoDB
    mongo_client = MongoDBConnector()

    # Delete all existing records in the collection
    deleted_count = mongo_client.delete_many(os.getenv("NEWS_COLLECTION"), {})

    # Insert the news records into MongoDB
    result = mongo_client.insert_many(os.getenv("NEWS_COLLECTION"), news_articles_dict)
    
    logging.info(f"Inserted {len(result)} news records into MongoDB.")
