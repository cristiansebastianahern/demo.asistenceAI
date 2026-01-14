import os
import sqlite3
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

LOG_FILE = 'migration.log'

def log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')
    print(msg)

def apply_sql():
    load_dotenv()
    
    # Try PostgreSQL first if environment variables are set
    DB_USER = os.getenv("POSTGRES_USER", "nexa_admin")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "D3x31(Kd.oB1")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "nexa_db")
    
    pg_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    sqlite_path = 'data/hospital.db'
    sql_filename = 'database/04_create_views.sql'
    
    if not os.path.exists(sql_filename):
        log(f"SQL file {sql_filename} not found.")
        return

    with open(sql_filename, 'r') as f:
        sql_content = f.read()

    # Apply to SQLite
    if os.path.exists(sqlite_path):
        log(f"Applying to SQLite: {sqlite_path}")
        try:
            conn = sqlite3.connect(sqlite_path)
            cursor = conn.cursor()
            # SQLite workaround for CREATE OR REPLACE VIEW
            # We transform "CREATE OR REPLACE VIEW" to "DROP VIEW IF EXISTS" + "CREATE VIEW"
            modified_sql = sql_content.replace("CREATE OR REPLACE VIEW", "DROP VIEW IF EXISTS vista_ubicaciones_maestra; CREATE VIEW")
            cursor.executescript(modified_sql)
            conn.commit()
            conn.close()
            log("Successfully applied to SQLite.")
        except Exception as e:
            log(f"Error applying to SQLite: {e}")
    else:
        log(f"SQLite database {sqlite_path} not found.")

    # Apply to PostgreSQL (if reachable)
    log(f"Attempting to apply to PostgreSQL: {DB_HOST}")
    try:
        engine = create_engine(pg_url, connect_args={'connect_timeout': 2})
        with engine.connect() as conn:
            conn.execute(text(sql_content))
            conn.commit()
        log("Successfully applied to PostgreSQL.")
    except Exception as e:
        log(f"PostgreSQL connection failed (expected if not running): {e}")

if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    apply_sql()
