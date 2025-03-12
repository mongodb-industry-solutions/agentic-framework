import pandas as pd
from embeddings.bedrock.cohere_embeddings import BedrockCohereEnglishEmbeddings

from dotenv import load_dotenv
import os

import logging
from tqdm import tqdm

# Enable tqdm for pandas
tqdm.pandas()


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Load environment variables from .env file
load_dotenv()

# Function to create a string representation of an article
def create_article_string(article: pd.DataFrame) -> str:
    """Generate a string representation of an article from the given DataFrame."""
    return f"Article headline: {article['headlines']} /n Article description: {article['description']}"


def get_article_embedding(text: str) -> BedrockCohereEnglishEmbeddings:
    """Generate an embedding for the given text using Bedrock Cohere English Embeddings."""

    # Check for valid input
    if not text or not isinstance(text, str):
        logging.error("Invalid input. Please provide a valid text input.")
        return None

    # Example usage of the BedrockCohereEnglishEmbeddings class.
    embeddings = BedrockCohereEnglishEmbeddings(
        region_name=os.getenv("AWS_REGION"),
        aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

    try:
        # Call the predict method to generate embeddings
        embedding = embeddings.predict(text)
        return embedding
    except Exception as e:
        print(f"Error in get_article_embedding: {e}")
        return None


def all_articles_embedding(df_articles: pd.DataFrame) -> pd.DataFrame:
    """Generate embeddings for all articles in the given DataFrame."""

    try:
        df_articles["embedding"] = df_articles["article_string"].progress_apply(get_article_embedding)
        logging.info("Embeddings generated for all articles.")
        return df_articles
    except Exception as e:
        logging.error(f"Error applying embedding function to DataFrame: {e}")
