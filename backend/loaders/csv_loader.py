import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CSVLoader:
    """
    Class to handle loading CSV files into Pandas DataFrames with error handling.
    """
    def __init__(self, filepath: str, delimiter: str = ',', encoding: str = 'utf-8'):
        """
        Initialize the CSVLoader with a relative file path and optional delimiter and encoding.
        The filepath will be resolved relative to the script's directory.
        """
        logging.info(f"Provided relative filepath: {filepath}")
        
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logging.info(f"Script directory: {script_dir}")
        
        # Always treat the provided filepath as relative and join with the script's directory
        self.filepath = os.path.join(script_dir, filepath)
        logging.info(f"Resolved absolute filepath: {self.filepath}")
        
        # Check if the file exists at the resolved path
        if not os.path.exists(self.filepath):
            logging.error(f"File does not exist at: {self.filepath}")
            raise FileNotFoundError(f"File not found: {self.filepath}")
        
        self.delimiter = delimiter
        self.encoding = encoding

    def load(self) -> pd.DataFrame:
        """
        Load the CSV file into a Pandas DataFrame.
        :return: Pandas DataFrame
        """
        try:
            df = pd.read_csv(self.filepath, delimiter=self.delimiter, encoding=self.encoding)
            logging.info(f"Successfully loaded CSV file: {self.filepath}")
            return df
        except FileNotFoundError:
            logging.error(f"File not found: {self.filepath}")
            raise
        except pd.errors.ParserError:
            logging.error(f"Parsing error occurred while reading file: {self.filepath}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error while loading file: {self.filepath} - {e}")
            raise



# ==================
# Example usage
# ==================

if __name__ == "__main__":
    # Example usage:
    # Provide a relative path to the CSV file
    # https://www.kaggle.com/datasets/notlucasp/financial-news-headlines?resource=download
    loader = CSVLoader(filepath="data/fsi/financial_news_headlines.csv")
    df = loader.load()
    print(df.head())
