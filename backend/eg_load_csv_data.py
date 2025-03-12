from config.config_loader import ConfigLoader
from loaders.csv_loader import CSVLoader
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ==================
# Example usage
# ==================

if __name__ == "__main__":

    config_loader = ConfigLoader()

    # Load configurations
    EXAMPLE_CSV_PATH = config_loader.get("EXAMPLE_CSV_PATH")
    EXAMPLE_CSV_FILES = config_loader.get("EXAMPLE_CSV_FILES")

    # Load CSV file
    logging.info("Loading CSV files...")
    logging.info(f"CSV Path: {EXAMPLE_CSV_PATH}")
    logging.info(f"CSV Files: {EXAMPLE_CSV_FILES}")
    csv_files = list(EXAMPLE_CSV_FILES)

    for file in csv_files:
        logging.info(f"Loading CSV file: {file}")
        loader = CSVLoader(filepath=f"{EXAMPLE_CSV_PATH}{file}")
        df = loader.load()
        print(df.head())