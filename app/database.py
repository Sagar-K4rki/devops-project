import psycopg2
import os

def get_connection():
    """
    Creates and returns a PostgreSQL connection.
    Reads credentials from environment variables so we never
    hardcode passwords in code.
    """
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "weatherapp"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

def init_db():
    """
    Creates the cities table if it doesn't exist.
    This runs once when the app starts up.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id        SERIAL PRIMARY KEY,
            name      VARCHAR(100) NOT NULL,
            country   VARCHAR(100) NOT NULL,
            added_at  TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()