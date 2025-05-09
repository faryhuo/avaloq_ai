import pyodbc
import sys
import logging
from typing import Optional, Tuple, List
from dotenv import load_dotenv
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_connection_string() -> str:
    """
    Create connection string for Oracle database
    """
    return (
        f"DRIVER={{Oracle}};"
        f"DBQ={os.getenv('ORACLE_HOST')}:{os.getenv('ORACLE_PORT')}/{os.getenv('ORACLE_SERVICE_NAME')};"
        f"UID={os.getenv('ORACLE_USERNAME')};"
        f"PWD={os.getenv('ORACLE_PASSWORD')}"
    )

@contextmanager
def get_connection():
    """
    Context manager for getting a database connection
    """
    connection = None
    try:
        connection = pyodbc.connect(get_connection_string())
        yield connection
    except pyodbc.Error as error:
        logger.error(f"Error connecting to database: {error}")
        raise
    finally:
        if connection:
            connection.close()

def fetch_data() -> Optional[Tuple[str, str]]:
    """
    Execute the SQL query and fetch the result
    """
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            sql_query = """
            SELECT s.name, h.text
            FROM src#1 s 
            JOIN src_hist h ON s.id = h.src_id
            ORDER BY h.seq_nr DESC
            FETCH FIRST 1 ROW ONLY
            """
            cursor.execute(sql_query)
            result = cursor.fetchone()
            cursor.close()
            return result
    except pyodbc.Error as error:
        logger.error(f"Error executing query: {error}")
        return None

def main():
    # Check if all required environment variables are set
    required_vars = ["ORACLE_USERNAME", "ORACLE_PASSWORD", "ORACLE_HOST", 
                    "ORACLE_PORT", "ORACLE_SERVICE_NAME"]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"- {var}")
        sys.exit(1)

    try:
        # Fetch data
        result = fetch_data()
        if result:
            name, text = result
            logger.info(f"Name: {name}")
            logger.info(f"Text: {text}")
        else:
            logger.info("No data found")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 