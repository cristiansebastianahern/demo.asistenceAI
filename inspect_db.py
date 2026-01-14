import sqlite3
import os

def inspect_db(db_path):
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Tables in {db_path}: {[t[0] for t in tables]}")
        
        # List all views
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
        views = cursor.fetchall()
        print(f"Views in {db_path}: {[v[0] for v in views]}")
        
        # Check specific tables content/schema
        for table in [t[0] for t in tables]:
            cursor.execute(f"PRAGMA table_info({table});")
            info = cursor.fetchall()
            print(f"Schema for {table}: {[i[1] for i in info]}")
            
            cursor.execute(f"SELECT COUNT(*) FROM {table};")
            count = cursor.fetchone()[0]
            print(f"Count for {table}: {count}")
            
        conn.close()
    except Exception as e:
        print(f"Error inspecting {db_path}: {e}")

if __name__ == "__main__":
    inspect_db('data/hospital.db')
