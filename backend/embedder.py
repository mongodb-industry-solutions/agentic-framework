import os
import pandas as pd
import logging

from db.mdb import MongoDBConnector
from embeddings.bedrock.cohere_embeddings import BedrockCohereEnglishEmbeddings

from dotenv import load_dotenv
import os
from tqdm import tqdm

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class Embedder(MongoDBConnector):
    def __init__(self, collection_name: str, uri=None, database_name: str = None, appname: str = None):
        """
        Embedder class to generate embeddings for text data stored in MongoDB.

        Args:
            collection_name (str, optional): Collection name.
            uri (str, optional): MongoDB URI. Default parent class value.
            database_name (str, optional): Database name. Default parent class value.
            appname (str, optional): Application name. Default parent class value.
        """
        super().__init__(uri, database_name, appname)
        self.collection_name = collection_name
        logger.info("Embedder initialized")

    @staticmethod
    def get_embedding(text: str) -> BedrockCohereEnglishEmbeddings:
        """Generate an embedding for the given text using Bedrock Cohere English Embeddings.
        
        Args:
            text (str): Text to generate an embedding for.
            
        Returns:
            BedrockCohereEnglishEmbeddings: Embedding for the given text.
        """
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
            print(f"Error in get_embedding: {e}")
            return None
        
    


# ==================
# Example usage
# ==================

if __name__ == "__main__":

    # Example usage
    embedder = Embedder(collection_name="vectors")
    text = "This is a test sentence."
    embedding = embedder.get_embedding(text)
    print(embedding)