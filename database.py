import os
import psycopg2

conn = psycopg2.connect(
    host=os.getenv("PGHOST"),
    database=os.getenv("PGDATABASE"),
    user=os.getenv("PGUSER"),
    password=os.getenv("PGPASSWORD"),
    port=os.getenv("PGPORT")
)

cursor = conn.cursor()


def setup():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS keys(
        id SERIAL PRIMARY KEY,
        key TEXT UNIQUE,
        used BOOLEAN,
        discord_id TEXT,
        hwid TEXT,
        validation TEXT
    )
    """)

    conn.commit()