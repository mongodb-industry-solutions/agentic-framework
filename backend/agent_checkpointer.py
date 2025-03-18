import logging

from langgraph.checkpoint.mongodb import MongoDBSaver
from db.mdb import MongoDBConnector
from config.config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Load configuration
config = ConfigLoader()
# Get the MongoDB checkpointer collection name from the config
MDB_CHECKPOINTER_COLLECTION = config.get("MDB_CHECKPOINTER_COLLECTION")

class AgentCheckpointer(MongoDBConnector):
    def __init__(self, collection_name: str = MDB_CHECKPOINTER_COLLECTION, uri=None, database_name: str = None, appname: str = None):
        """
        AgentCheckpointer class to save agent states to MongoDB.

        Args:
            collection_name (str, optional): Collection name. Default is MDB_CHECKPOINTER_COLLECTION.
            uri (str, optional): MongoDB URI. Default parent class value.
            database_name (str, optional): Database name. Default parent class value.
            appname (str, optional): Application name. Default parent class value.
        """
        super().__init__(uri, database_name, appname)
        self.database_name = database_name
        self.checkpoint_collection_name = collection_name
        self.writes_collection_name = collection_name + "_writes"
        
        logger.info("AgentCheckpointer initialized")

    # --- Create MongoDB Saver ---
    def create_mongodb_saver(self):
        """
        Create a MongoDBSaver instance to save agent states to MongoDB."

        Uses:
            - MongoDBSaver.from_conn_string()

        Params:
            conn_string (str): MongoDB connection string. Takes the value from parent class.
            db_name (str): Database name. Takes the value from parent class.
            checkpoint_collection_name (str): Checkpointer collection name. Default is MDB_CHECKPOINTER_COLLECTION.
            writes_collection_name (str): Writes collection name. Default is MDB_CHECKPOINTER_COLLECTION + "_writes".

        Returns:
            MongoDBSaver: MongoDBSaver instance to save agent states to MongoDB.
        """
        mongo_uri = self.uri
        if not mongo_uri:
            logger.warning("[MongoDB] MONGO_URI not set. State saving will be disabled.")
            return None
        try:
            logger.info(f"[MongoDB] Initializing MongoDBSaver!")
            return MongoDBSaver.from_conn_string(conn_string=mongo_uri, 
                                                 db_name=self.database_name,
                                                 checkpoint_collection_name=self.checkpoint_collection_name, 
                                                 writes_collection_name=self.writes_collection_name)
        except Exception as e:
            logger.error(f"[MongoDB] Error initializing MongoDB saver: {e}")
            return None