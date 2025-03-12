from langchain_mongodb import MongoDBAtlasVectorSearch

from langchain_aws import BedrockEmbeddings
from embeddings.bedrock.getters import get_embedding_model

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


def create_vector_store(
    cluster_uri: str,
    database_name: str,
    collection_name: str,
    text_key: str,
    embedding_key: str,
    index_name: str,
    embedding_model: BedrockEmbeddings,
) -> MongoDBAtlasVectorSearch:
    """
    Creates a vector store using MongoDB Atlas.

    :param cluster_uri: MongoDB connection URI.
    :param database_name: Name of the database.
    :param collection_name: Name of the collection.
    :param text_key: The field containing text data.
    :param embedding_key: Field that will contain the embedding for each document
    :param index_name: Name of the Atlas Vector Search index
    :param embedding_model: The embedding model to use.
    """

    if index_name is None:
        index_name = f"{collection_name}_VS_IDX"

    logging.info(f"Creating vector store...")

    # Vector Store Creation
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=cluster_uri,
        namespace=database_name + "." + collection_name,
        embedding=embedding_model,
        embedding_key=embedding_key,
        index_name=index_name,
        text_key=text_key
    )

    return vector_store


def lookup_collection(vector_store: MongoDBAtlasVectorSearch, query: str, n=10) -> str:
    result = vector_store.similarity_search_with_score(query=query, k=n)
    return str(result)


# Example usage
if __name__ == "__main__":

    embedding_model = get_embedding_model(model_id="cohere.embed-english-v3")

    INDEX_NAME = "policy_VS_IDX"

    vector_store = create_vector_store(
        cluster_uri=os.getenv("MONGODB_URI"),
        database_name=os.getenv("DATABASE_NAME"),
        collection_name=os.getenv("COLLECTION_NAME"),
        text_key="description",
        embedding_key="descriptionEmbedding",
        index_name=INDEX_NAME,
        embedding_model=embedding_model
    )

    query = "collisions"

    result = lookup_collection(vector_store, query=query, n=5)
    print(result)
