from langchain.agents import tool
from embeddings.bedrock.getters import get_embedding_model
from agent_vector_store import create_vector_store

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

INDEX_NAME = "financial_news_VS_IDX"

embedding_model = get_embedding_model(model_id="cohere.embed-english-v3")

vector_store = create_vector_store(
        cluster_uri=os.getenv("MONGODB_URI"),
        database_name=os.getenv("DATABASE_NAME"),
        collection_name=os.getenv("NEWS_COLLECTION"),
        text_key="article_string",
        index_name=INDEX_NAME,
        embedding_model=embedding_model
    )

@tool
def lookup_articles(query: str, n=10) -> str:
    "Gathers the top n articles from the database that are most similar to the query."
    result = vector_store.similarity_search_with_score(query=query, k=n)
    return str(result)


tools = [lookup_articles]