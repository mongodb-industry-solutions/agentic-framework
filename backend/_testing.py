from loader import CSVLoader
from config.config_loader import ConfigLoader
from mdb_timeseries_coll_creator import TimeSeriesCollectionCreator
from mdb_vector_search_idx_creator import VectorSearchIDXCreator
from embedder import Embedder
from agent_tools import AgentTools


# ==================
# Example usage
# ==================

if __name__ == "__main__":

    # Example usage
    state = {}
    state["issue_report"] = "My vehicle's fuel consumption has increased significantly over the past week. What might be wrong with the engine or fuel system?"
    state["embedding_key"] = "issue_embedding"
    state["thread_id"] = "123"

    # Load configuration
    config_loader = ConfigLoader()
    filepath_csv_data = config_loader.get("CSV_DATA")
    filepath_csv_to_vectorize = config_loader.get("CSV_TO_VECTORIZE")
    mdb_timeseries_collection = config_loader.get("MDB_TIMESERIES_COLLECTION")
    mdb_embeddings_collection = config_loader.get("MDB_EMBEDDINGS_COLLECTION")

    # Get data from CSV
    csv_data = AgentTools()
    r = csv_data.get_data_from_csv(state)
    print("Reading data from CSV...")
    print(r)

    # Generate chain of thought
    print("Generating chain of thought...")
    agent_tools = AgentTools()
    state = agent_tools.generate_chain_of_thought(state=state)

    # Create Time Series Collection
    print("Creating Time Series Collection...")
    r = TimeSeriesCollectionCreator().create_timeseries_collection(
        collection_name=mdb_timeseries_collection,
        time_field="timestamp",
        granularity="minutes"
    )
    print(r)

    # Load data in Pandas DataFrame
    print("Loading data in Pandas DataFrame...")
    data = CSVLoader(filepath=filepath_csv_data, collection_name=mdb_timeseries_collection)
    data_df = data.load()
    print(data_df.head())
    
    # Store data in MongoDB
    print("Storing timeseries data in MongoDB...")
    r = data.store(data_df)
    print(r)
    
    # Load Data for Vectorization
    print("Loading data for Vectorization...")
    vector = CSVLoader(filepath=filepath_csv_to_vectorize, collection_name=mdb_embeddings_collection)
    vector_df = vector.load()
    print("Printing data for Vectorization...")
    print(vector_df.head())

    print("Storing issues in MongoDB...")

    print("Skipping the storage of vector data for now...")
    # r = vector.store(vector_df)
    # print(r)

    print("Data stored successfully.")

    print("Creating Embeddings over Issues data...")
    embedder = Embedder(collection_name=mdb_embeddings_collection)
    embedder.embed(attribute_name="issue", overwrite=False)
    print("Embeddings created successfully.")
    
    # Perform vector search
    print("Performing vector search...")

    # Create vector search index
    print("Creating vector search index...")
    # Using default values for the index creation
    r = VectorSearchIDXCreator().create_index()
    print(r)

    # Query text
    print("Complaint:")
    print(state["issue_report"])

    # Instantiate the Embedder
    embedder = Embedder()
    query_embedded = embedder.get_embedding(state["issue_report"])
    state["embedding_vector"] = query_embedded
    mdb_vector = AgentTools(collection_name=mdb_embeddings_collection)
    r = mdb_vector.vector_search(state)

    # Print the results
    print("Results:")
    for issue in r["similar_issues"]:
        print("Similar issue No. " + str(r["similar_issues"].index(issue) + 1))
        print("Similar Issue:")
        print(issue["issue"])
        print("Recommendation:")
        print(issue["recommendation"])