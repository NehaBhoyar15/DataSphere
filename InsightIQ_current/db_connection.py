

import os
import sys
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Locate .env beside the project file or packaged executable
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))


def get_connection():
    try:
        connection = mysql.connector.connect(
            use_pure=True,
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME", "ai assistance"),
            connection_timeout=5,
        )

        if connection.is_connected():
            return connection

        connection.close()

    except Error as e:
        print(f"MySQL connection error: {e}")

    return None


if __name__ == "__main__":
    conn = get_connection()

    if conn:
        print("MySQL connected successfully!")
        print("Database:", conn.database)
        conn.close()
    else:
        print("MySQL connection failed.")
