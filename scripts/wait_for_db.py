import os
import time
import psycopg2
from urllib.parse import urlparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_db():
    """Wait for database to be available"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    logger.info("Found DATABASE_URL environment variable")
    
    url = urlparse(db_url)
    dbname = url.path[1:]
    user = url.username
    # password = "****"  # Masked for security
    host = url.hostname
    port = url.port

    logger.info(f"Parsed database connection info:")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Database: {dbname}")
    logger.info(f"User: {user}")

    max_retries = 30
    retry_interval = 2

    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})...")
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=5  # Add timeout
            )
            conn.close()
            logger.info("Successfully connected to database!")
            return
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database not ready yet: {e}")
                time.sleep(retry_interval)
            else:
                logger.error("Max retries reached. Could not connect to database.")
                logger.error(f"Final error: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error: {type(e).__name__}: {e}")
            raise

if __name__ == "__main__":
    try:
        wait_for_db()
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise 