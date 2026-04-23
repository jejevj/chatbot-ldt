"""
Script untuk menjalankan SQL migration files
Usage: python run_migration.py migrations/001_create_chat_tables.sql
"""
import sys
import psycopg2
from urllib.parse import quote_plus
import os

def run_migration(sql_file_path: str):
    """Run SQL migration file"""
    # Database connection
    password = quote_plus("qwert12345!")
    conn = psycopg2.connect(
        host="127.0.0.1",
        port=5433,
        database="satu_data_db",
        user="postgres",
        password="qwert12345!"
    )
    
    try:
        cursor = conn.cursor()
        
        # Read SQL file
        print(f"Reading migration file: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute SQL
        print("Executing migration...")
        cursor.execute(sql_content)
        conn.commit()
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error running migration: {str(e)}")
        conn.rollback()
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <sql_file_path>")
        sys.exit(1)
    
    sql_file = sys.argv[1]
    run_migration(sql_file)
