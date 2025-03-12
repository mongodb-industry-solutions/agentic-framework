from loader import CSVLoader
from config.config_loader import ConfigLoader


# ==================
# Example usage
# ==================

if __name__ == "__main__":

    # Example usage
    config_loader = ConfigLoader()
    csv_data = config_loader.get("CSV_DATA")
    csv_to_vectorize = config_loader.get("CSV_TO_VECTORIZE")
    mdb_data_collection = config_loader.get("MDB_DATA_COLLECTION")
    mdb_vectors_collection = config_loader.get("MDB_VECTORS_COLLECTION")

    data = CSVLoader(filepath=csv_data, collection_name=mdb_data_collection)
    data_df = data.load()
    print(data_df.head())
    
    print("Storing data...")
    result = data.store(data_df)
    print(result)
    
    vector = CSVLoader(filepath=csv_to_vectorize, collection_name=mdb_vectors_collection)
    vector_df = vector.load()
    print(vector_df.head())

    print("Storing vector data...")
    result = vector.store(vector_df)
    print(result)

    print("Data and vector data stored successfully.")
    