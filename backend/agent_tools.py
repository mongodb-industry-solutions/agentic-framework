from langchain.agents import tool
from db.mdb import MongoDBConnector
import logging
from dotenv import load_dotenv
from config.config_loader import ConfigLoader
from loader import CSVLoader
import csv

from embedder import Embedder

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
config = ConfigLoader()
# Get the
CSV_DATA = config.get("CSV_DATA")
MDB_DATA_COLLECTION = config.get("MDB_DATA_COLLECTION")
CSV_TO_VECTORIZE = config.get("CSV_TO_VECTORIZE")
MDB_VECTORS_COLLECTION = config.get("MDB_VECTORS_COLLECTION")
MDB_VECTOR_SEARCH_INDEX = config.get("MDB_VECTOR_SEARCH_INDEX")

class AgentTools(MongoDBConnector):
    def __init__(self, collection_name: str=None, uri=None, database_name: str = None, appname: str = None):
        """
        Embedder class to generate embeddings for text data stored in MongoDB.

        Args:
            collection_name (str, optional): Collection name.
            uri (str, optional): MongoDB URI. Default parent class value.
            database_name (str, optional): Database name. Default parent class value.
            appname (str, optional): Application name. Default parent class value.
        """
        super().__init__(uri, database_name, appname)
        if collection_name:
            self.collection_name = collection_name
            self.collection = self.get_collection(self.collection_name)
            logger.info(f"AgentTools initialized for collection: {self.collection_name}")
        logger.info("AgentTools initialized")

    def get_data_from_csv(self, state: dict) -> dict:
        "Reads data from a CSV file."
        message = "[Tool] Retrieved data from CSV file."
        logger.info(message)

        # Load CSV data
        # TODO: Probably not the best way to do this
        csv_loader = CSVLoader(filepath=CSV_DATA, collection_name=MDB_DATA_COLLECTION)
        csv_filepath = csv_loader.filepath

        data_records = []
        with open(csv_filepath, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_records.append(row)

        for record in data_records:
            logger.info(record)

        state.setdefault("updates", []).append(message)
        return {"data": data_records, "thread_id": state.get("thread_id", "")}

    def get_data_from_mdb(self, state: dict) -> dict:
        "Reads data from a MongoDB collection."
        message = "[Tool] Retrieved data from MongoDB collection."
        logger.info(message)

        data_records = []
        for record in self.collection.find():
            data_records.append(record)

        state.setdefault("updates", []).append(message)
        return {"data": data_records, "thread_id": state.get("thread_id", "")}
    
    def vector_search(self, state: dict) -> dict:
        """Performs a vector search in a MongoDB collection."""
        message = "[Tool] Performing MongoDB Atlas Vector Search"
        logger.info(message)

        # Set default update message
        state.setdefault("updates", []).append(message)
        # Get embedding key
        if state.get("embedding_key"):
            embedding_key = state["embedding_key"]
        elif self.collection_name:
            embedding_key = self.collection_name + "_embedding"
        else:
            # Default embedding key
            embedding_key = "embedding"
        # Get the embedding vector from the state
        embedding = state.get("embedding_vector", [])
        # Similar data records
        similar_issues = [
            {"issue": "Engine knocking when turning", "recommendation": "Inspect spark plugs and engine oil."},
            {"issue": "Suspension noise under load", "recommendation": "Check suspension components for wear."}
        ]

        try:
            # Perform vector search
            if self.collection is not None:
                pipeline = [
                {
                    "$vectorSearch": {
                        "index": MDB_VECTOR_SEARCH_INDEX,
                        "path": embedding_key,
                        "queryVector": embedding,
                        "numCandidates": 5,
                        "limit": 2
                    }
                }
            ]
            # Execute the aggregation pipeline
            results = list(self.collection.aggregate(pipeline))
            # Format the results
            for result in results:
                if "_id" in result:
                    result["_id"] = str(result["_id"])
            if results:
                logger.info(f"[MongoDB] Retrieved similar data from vector search.")
                state.setdefault("updates", []).append("[MongoDB] Retrieved similar data.")
                similar_issues = results
            else:
                logger.info(f"[MongoDB] No similar data found. Returning default message.")
                state.setdefault("updates", []).append("[MongoDB] No similar data found.")
                similar_issues = [{"issue": "No similar issues found", "recommendation": "No immediate action based on past data."}]
        except Exception as e:
            logger.error(f"Error during MongoDB Vector Search operation: {e}")
            state.setdefault("updates", []).append("[MongoDB] Error during Vector Search operation.")
            similar_issues = [{"issue": "MongoDB Vector Search operation error", "recommendation": "Please try again later."}]
        
        return {"similar_issues": similar_issues}

# Define tools
@tool
def get_data_from_csv_tool(state: dict) -> dict:
    "Reads data from a CSV file."
    csv_data = AgentTools()
    return csv_data.get_data_from_csv(state)

@tool
def get_data_from_mdb_tool(state: dict) -> dict:
    "Reads data from a MongoDB collection."
    mdb_data = AgentTools(collection_name=MDB_DATA_COLLECTION)
    return mdb_data.get_data_from_mdb(state)

@tool
def vector_search_tool(state: dict) -> dict:
    """Performs a vector search in a MongoDB collection."""
    mdb_vector = AgentTools(collection_name=MDB_VECTORS_COLLECTION)
    return mdb_vector.vector_search(state)


tools = [get_data_from_csv_tool, get_data_from_mdb_tool, vector_search_tool]

if __name__ == "__main__":

    # Example usage
    state = {"thread_id": "123"}
    
    # # Get data from CSV
    # csv_data = AgentTools()
    # r = csv_data.get_data_from_csv(state)
    # print(r)


    # # Get data from MongoDB
    # mdb_data = AgentTools(collection_name=MDB_DATA_COLLECTION)
    # r = mdb_data.get_data_from_mdb(state)
    # print(r)

    # Perform vector search
    state["embedding_key"] = "issue_embedding"

    query_txt = "My vehicle's fuel consumption has increased significantly over the past week. What might be wrong with the engine or fuel system?"
     # Instantiate the Embedder
    embedder = Embedder()
    query_embedded = embedder.get_embedding(query_txt)
    state["embedding_vector"] = query_embedded
    mdb_vector = AgentTools(collection_name=MDB_VECTORS_COLLECTION)
    r = mdb_vector.vector_search(state)

    for issue in r["similar_issues"]:
        print("Similar Issue:")
        print(issue["issue"])
        print("Recommendation:")
        print(issue["recommendation"])