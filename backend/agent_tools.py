from db.mdb import MongoDBConnector

import datetime
import logging

from langchain.agents import tool

from config.config_loader import ConfigLoader
from config.prompts import get_chain_of_thoughts_prompt, get_llm_recommendation_prompt
from utils import convert_objectids
from bedrock.anthropic_chat_completions import BedrockAnthropicChatCompletions

from loader import CSVLoader
import csv

from agent_state import AgentState
from embedder import Embedder
from profiler import AgentProfiler
from mdb_timeseries_coll_creator import TimeSeriesCollectionCreator

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class AgentTools(MongoDBConnector):
    def __init__(self, collection_name: str=None, uri=None, database_name: str=None, appname: str=None):
        """
        AgentTools class to perform various actions for the agent.

        Args:
            collection_name (str): Collection name. Default is None.
            uri (str, optional): MongoDB URI. Default parent class value.
            database_name (str, optional): Database name. Default parent class value.
            appname (str, optional): Application name. Default parent class value.
        """
        super().__init__(uri, database_name, appname)

        # Load configuration
        config = ConfigLoader()
        self.config = config

        # Get configuration values
        self.csv_data = self.config.get("CSV_DATA")
        self.mdb_timeseries_collection = self.config.get("MDB_TIMESERIES_COLLECTION")
        self.mdb_timeseries_timefield = self.config.get("MDB_TIMESERIES_TIMEFIELD")
        self.mdb_timeseries_granularity = self.config.get("MDB_TIMESERIES_GRANULARITY")
        self.csv_to_vectorize = self.config.get("CSV_TO_VECTORIZE")
        self.mdb_embeddings_collection = self.config.get("MDB_EMBEDDINGS_COLLECTION")
        self.mdb_embeddings_collection_vs_field = self.config.get("MDB_EMBEDDINGS_COLLECTION_VS_FIELD")
        self.mdb_vs_index = self.config.get("MDB_VS_INDEX")
        self.mdb_agent_profiles_collection = self.config.get("MDB_AGENT_PROFILES_COLLECTION")
        self.agent_profile_chosen_id = self.config.get("AGENT_PROFILE_CHOSEN_ID")
        self.embeddings_model_id = self.config.get("EMBEDDINGS_MODEL_ID")
        self.embeddings_model_name = self.config.get("EMBEDDINGS_MODEL_NAME")
        self.chatcompletions_model_id = self.config.get("CHATCOMPLETIONS_MODEL_ID")
        self.chatcompletions_model_name = self.config.get("CHATCOMPLETIONS_MODEL_NAME")
        self.agent_motive = self.config.get("AGENT_MOTIVE")
        self.agent_data_consumed = self.config.get("AGENT_DATA_CONSUMED")
        self.llm_recommendation_role = self.config.get("LLM_RECOMMENDATION_ROLE")
        self.mdb_historical_recommendations_collection = self.config.get("MDB_HISTORICAL_RECOMMENDATIONS_COLLECTION")

        if collection_name:
            # Set the collection name
            self.collection_name = collection_name
            self.collection = self.get_collection(self.collection_name)

    def get_data_from_csv(self, state: dict) -> dict:
        "Reads data from a CSV file."
        message = "[Tool] Retrieved data from CSV file."
        logger.info(message)

        # Load CSV data
        # TODO: Probably not the best way to do this
        csv_loader = CSVLoader(filepath=self.csv_data, collection_name=self.mdb_timeseries_collection)
        csv_filepath = csv_loader.filepath

        data_records = []
        with open(csv_filepath, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                data_records.append(row)

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
            embedding_key = self.mdb_embeddings_collection_vs_field
        else:
            # Default embedding key
            embedding_key = "embedding"
        # Get the embedding vector from the state
        embedding = state.get("embedding_vector", [])
        # Similar data records
        similar_issues = [
            {"issue": "Engine knocking when turning",
                "recommendation": "Inspect spark plugs and engine oil."},
            {"issue": "Suspension noise under load",
                "recommendation": "Check suspension components for wear."}
        ]

        try:
            # Perform vector search
            if self.collection is not None:
                pipeline = [
                    {
                        "$vectorSearch": {
                            "index": self.mdb_vs_index,
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
                logger.info(
                    f"[MongoDB] Retrieved similar data from vector search.")
                state.setdefault("updates", []).append(
                    "[MongoDB] Retrieved similar data.")
                similar_issues = results
            else:
                logger.info(
                    f"[MongoDB] No similar data found. Returning default message.")
                state.setdefault("updates", []).append(
                    "[MongoDB] No similar data found.")
                similar_issues = [{"issue": "No similar issues found",
                                   "recommendation": "No immediate action based on past data."}]
        except Exception as e:
            logger.error(f"Error during MongoDB Vector Search operation: {e}")
            state.setdefault("updates", []).append(
                "[MongoDB] Error during Vector Search operation.")
            similar_issues = [{"issue": "MongoDB Vector Search operation error",
                               "recommendation": "Please try again later."}]

        return {"similar_issues": similar_issues}

    def generate_chain_of_thought(self, state: AgentState) -> AgentState:
        """Generates the chain of thought for the agent."""
        logger.info("[LLM Chain-of-Thought Reasoning]")
        # Example usage
        profiler = AgentProfiler(collection_name=self.mdb_agent_profiles_collection)
        # Get the agent profile
        p = profiler.get_agent_profile(agent_id=self.agent_profile_chosen_id)
        # Get the Issue Report from the state
        issue_report = state["issue_report"]

        CHAIN_OF_THOUGHTS_PROMPT = get_chain_of_thoughts_prompt(
            profile=p["profile"],
            rules=p["rules"],
            goals=p["goals"],
            issue_report=issue_report,
            agent_motive=self.agent_motive,
            agent_data_consumed=self.agent_data_consumed,
            embedding_model_name=self.embeddings_model_name,
            chat_completion_model_name=self.chatcompletions_model_name
        )
        logger.info("Chain-of-Thought Reasoning Prompt:")
        logger.info(CHAIN_OF_THOUGHTS_PROMPT)

        try:
            # Instantiate the chat completion model
            chat_completions = BedrockAnthropicChatCompletions(model_id=self.chatcompletions_model_id)
            # Generate a chain of thought based on the prompt
            chain_of_thought = chat_completions.predict(CHAIN_OF_THOUGHTS_PROMPT)
        except Exception as e:
            logger.error(f"Error generating chain of thought: {e}")
            chain_of_thought = (
                "1. Consume data.\n"
                "2. Generate an embedding for the complaint.\n"
                "3. Perform a vector search on past issues.\n"
                "4. Persist data into MongoDB.\n"
                "5. Generate a final summary and recommendation."
            )

        logger.info("Chain-of-Thought Reasoning:")
        logger.info(chain_of_thought)
        state.setdefault("updates", []).append("Chain-of-thought generated.")
        return {**state, "chain_of_thought": chain_of_thought, "next_step": "get_data_from_csv_tool"}
    
    @staticmethod
    def process_data(state: AgentState) -> AgentState:
        """Processes the data."""
        state.setdefault("updates", []).append("Data processed.")
        state["next_step"] = "embedding_node"
        return state

    def get_query_embedding(self, state: AgentState) -> AgentState:
        """Generates the query embedding."""
        logger.info("[Action] Generating Query Embedding...")
        state.setdefault("updates", []).append("Generating query embedding...")

        # Get the query text
        text = state["issue_report"]

        try: 
            # Instantiate the Embedder
            embedder = Embedder(collection_name=self.mdb_embeddings_collection)
            embedding = embedder.get_embedding(text)
            state.setdefault("updates", []).append("Query embedding generated!")
            logger.info("Query embedding generated!")
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            state.setdefault("updates", []).append("Error generating query embedding; using dummy vector.")
            embedding = [0.0] * 1024
        return {**state, "embedding_vector": embedding, "next_step": "vector_search_tool"}
    
    @staticmethod
    def process_vector_search(state: AgentState) -> AgentState:
        """Processes the vector search results."""
        state.setdefault("updates", []).append("Vector search results processed.")
        state["next_step"] = "persistence_node"
        return state
    
    def persist_data(self, state: AgentState) -> AgentState:
        """Persists the data into MongoDB."""
        state.setdefault("updates", []).append("Persisting data to MongoDB...")
        logger.info("[Action] Persisting data to MongoDB...")

        # Check if a collection is set
        if self.collection is not None:
            # Combined data to persist
            combined_data = {
                    "issue_report": state["issue_report"],
                    "telemetry": state["telemetry_data"],
                    "similar_issues": state["similar_issues_list"],
                    "thread_id": state.get("thread_id", "")
                }
            try:
                logger.info("Checking Time Series Collection...")
                ts_coll_result = TimeSeriesCollectionCreator().create_timeseries_collection(
                    collection_name=self.mdb_timeseries_collection,
                    time_field=self.mdb_timeseries_timefield,
                    granularity=self.mdb_timeseries_granularity
                )
                logger.info(ts_coll_result)

                # Looping through data to persist
                for record in combined_data["telemetry"]:
                    try:
                        record["timestamp"] = datetime.datetime.strptime(record["timestamp"], "%Y-%m-%dT%H:%M:%SZ")
                    except Exception as e:
                        logger.error("Error parsing timestamp:", e)
                    record["thread_id"] = state.get("thread_id", "")
                    # Convert ObjectIds to strings
                    record = convert_objectids(record)
                    # Insert the record
                    self.collection.insert_one(record)
                logger.info(f"[MongoDB] Data persisted in {self.collection_name} collection.")

                logger.info("Getting logs collection...")
                coll_logs = self.db["logs"]
                logger.info("Generating log entry...")
                log_entry = {
                    "thread_id": state.get("thread_id", ""),
                    "issue_report": combined_data["issue_report"],
                    "similar_issues": combined_data["similar_issues"],
                    "created_at": datetime.datetime.now(datetime.timezone.utc)
                }
                # Convert ObjectIds to strings
                log_entry = convert_objectids(log_entry)
                # Insert the record
                coll_logs.insert_one(log_entry)
                state.setdefault("updates", []).append("Data persisted to MongoDB.")
            except Exception as e:
                logger.error("Error persisting data to MongoDB:", e)
                state.setdefault("updates", []).append("Error persisting data to MongoDB.")
        else:
            state.setdefault("updates", []).append("No MongoDB collection set for persistence.")
            logger.info("No MongoDB collection set for persistence.")
            return {**state, "next_step": "recommendation_node"}
        
    def get_llm_recommendation(self, state: AgentState) -> AgentState:
        state.setdefault("updates", []).append("Generating final recommendation...")
        logger.info("[Final Answer] Generating final recommendation...")
        
        telemetry_data = state["telemetry_data"]
        similar_issues = state["similar_issues_list"]
        
        if not telemetry_data:
            state.setdefault("updates", []).append("No telemetry data; using default values.")
            logger.warning("[Warning] No telemetry data available. Using default values.")
            telemetry_data = [{
                "timestamp": "2025-02-19T13:15:00Z",
                "engine_temperature": "99",
                "oil_pressure": "33",
                "avg_fuel_consumption": "8.8"
            }]
        critical_conditions = []
        
        for record in telemetry_data:
            try:
                engine_temp = float(record["engine_temperature"])
                oil_pressure = float(record["oil_pressure"])
                if engine_temp > 100:
                    critical_conditions.append(f"Critical engine temperature: {engine_temp}°C")
                if oil_pressure < 30:
                    critical_conditions.append(f"Low oil pressure: {oil_pressure} PSI")
            except (ValueError, KeyError) as e:
                logger.error(f"[Warning] Error parsing telemetry values: {e}")
        critical_info = "CRITICAL ALERT: " + ", ".join(critical_conditions) + "\n\n" if critical_conditions else ""

        # Generate the LLM recommendation prompt
        LLM_RECOMMENDATION_PROMPT = get_llm_recommendation_prompt(
            critical_info=critical_info,
            telemetry_data=telemetry_data,
            similar_issues=similar_issues
        )
        logger.info("LLM Recommendation Prompt:")
        logger.info(LLM_RECOMMENDATION_PROMPT)

        try:
            # Instantiate the chat completion model
            chat_completions = BedrockAnthropicChatCompletions(model_id=self.chatcompletions_model_id)
            # Generate a chain of thought based on the prompt
            llm_recommendation = chat_completions.predict(LLM_RECOMMENDATION_PROMPT)
        except Exception as e:
            logger.error(f"Error generating LLM recommendation: {e}")
            llm_recommendation = "Unable to generate recommendation at this time."

        logger.info("LLM Recommendation:")
        logger.info(llm_recommendation)
        state.setdefault("updates", []).append("Final recommendation generated.")

        try:
            recommendation_record = {
                "thread_id": state.get("thread_id", ""),
                "timestamp": datetime.datetime.now(datetime.timezone.utc),
                "issue_report": state["issue_report"],
                "telemetry_data": state["telemetry_data"],
                "similar_issues": state["similar_issues_list"],
                "recommendation": llm_recommendation
            }
            recommendation_record = convert_objectids(recommendation_record)
            self.collection.insert_one(recommendation_record)
            state.setdefault("updates", []).append("Recommendation stored in MongoDB.")
            logger.info("[MongoDB] Recommendation stored in historical records")
        except Exception as e:
            logger.error(f"Error storing recommendation in MongoDB: {e}")
            state.setdefault("updates", []).append("Error storing recommendation in MongoDB.")

        return {**state, "recommendation_text": llm_recommendation, "next_step": "end"}



# Define tools
def get_data_from_csv_tool(state: dict) -> dict:
    "Reads data from a CSV file."
    agent_tools = AgentTools()
    return agent_tools.get_data_from_csv(state=state)

def get_data_from_mdb_tool(state: dict) -> dict:
    "Reads data from a MongoDB collection."
    # Load configuration
    config = ConfigLoader()
    # Get the MongoDB collection name
    mdb_timeseries_collection = config.get("MDB_TIMESERIES_COLLECTION")
    # Instantiate the AgentTools class
    agent_tools = AgentTools(collection_name=mdb_timeseries_collection)
    return agent_tools.get_data_from_mdb(state)

def vector_search_tool(state: dict) -> dict:
    """Performs a vector search in a MongoDB collection."""
    # Load configuration
    config = ConfigLoader()
    # Get the MongoDB collection name
    mdb_embeddings_collection = config.get("MDB_EMBEDDINGS_COLLECTION")
    # Instantiate the AgentTools class
    agent_tools = AgentTools(collection_name=mdb_embeddings_collection)
    return agent_tools.vector_search(state=state)

def generate_chain_of_thought_tool(state: AgentState) -> AgentState:
    """Generates the chain of thought for the agent."""
    agent_tools = AgentTools()
    return agent_tools.generate_chain_of_thought(state=state)

def process_data_tool(state: AgentState) -> AgentState:
    """Processes the data."""
    agent_tools = AgentTools()
    return agent_tools.process_data(state=state)

def get_query_embedding_tool(state: AgentState) -> AgentState:
    """Generates the query embedding."""
    agent_tools = AgentTools()
    return agent_tools.get_query_embedding(state=state)

def process_vector_search_tool(state: AgentState) -> AgentState:
    """Processes the vector search results."""
    agent_tools = AgentTools()
    return agent_tools.process_vector_search(state=state)

def persist_data_tool(state: AgentState) -> AgentState:
    """Persists the data into MongoDB."""
    # Load configuration
    config = ConfigLoader()
    # Get the MongoDB collection name
    mdb_timeseries_collection = config.get("MDB_TIMESERIES_COLLECTION")
    # Instantiate the AgentTools class
    agent_tools = AgentTools(collection_name=mdb_timeseries_collection)
    return agent_tools.persist_data(state=state)

def get_llm_recommendation_tool(state: AgentState) -> AgentState:
    """Generates the LLM recommendation."""
    # Load configuration
    config = ConfigLoader()
    # Get the MongoDB collection name
    mdb_historical_recommendations_collection = config.get("MDB_HISTORICAL_RECOMMENDATIONS_COLLECTION")
    # Instantiate the AgentTools class
    agent_tools = AgentTools(collection_name=mdb_historical_recommendations_collection)
    return agent_tools.get_llm_recommendation(state=state)
