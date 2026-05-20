import psycopg2
import os

conn = None
cursor = None


def connect_database():

    global conn, cursor

    db = os.getenv("DATABASE_URL")

    if not db:
        print("DATABASE_URL NOT FOUND")
        return None, None

    try:

        conn = psycopg2.connect(db)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys(
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            used BOOLEAN DEFAULT FALSE,
            discord_id TEXT,
            roblox_id BIGINT,
            hwid TEXT,
            validation TEXT,
            created_at TIMESTAMP,
            expires_at TIMESTAMP,
            expired TEXT,
            blacklisted TEXT
        )
        """)

        conn.commit()

        # Add missing columns if they don't exist yet
        for col, coltype in [
            ("created_at", "TIMESTAMP"),
            ("expires_at", "TIMESTAMP"),
            ("expired", "TEXT"),
            ("roblox_id", "BIGINT"),
            ("blacklisted", "TEXT"),
        ]:
            cursor.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='keys' AND column_name=%s
                """,
                (col,),
            )
            if not cursor.fetchone():
                cursor.execute(f"ALTER TABLE keys ADD COLUMN {col} {coltype}")
                print(f"Added column: {col}")

        conn.commit()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trial_keys(
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            discord_id TEXT,
            roblox_id BIGINT,
            created_at TIMESTAMP
        )
        """)

        conn.commit()

        print("DATABASE CONNECTED")
        return conn, cursor

    except Exception as e:
        print(f"Database error: {e}")
        return None, None
