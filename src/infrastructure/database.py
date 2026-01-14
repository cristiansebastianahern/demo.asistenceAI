from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# 1. Cargar variables de entorno
load_dotenv()

# 2. Configuración de Conexión (PostgreSQL/Docker)
DB_USER = os.getenv("POSTGRES_USER", "nexa_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "D3x31(Kd.oB1")
#DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nexa_secure_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "nexa_db")

# Cadena de conexión (Explícitamente usando psycopg2)
DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 3. Crear Motor y Fábrica de Sesiones
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. Dependencia para FastAPI/Streamlit
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. CLASE DE COMPATIBILIDAD (DatabaseManager)
class DatabaseManager:
    """
    Wrapper para mantener compatibilidad con use_cases antiguos.
    """
    def __init__(self, db_name=None):
        self.db = SessionLocal()

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()
        
    def get_session(self):
        return self.db







#############################################
# """ from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# import os
# from dotenv import load_dotenv
# from typing import Generator

# # Load environment variables from .env if present
# load_dotenv()

# # Database connection configuration (defaults for local development)
# DB_USER = os.getenv("POSTGRES_USER", "nexa_admin")
# DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "D3x31(Kd.oB1")
# DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
# DB_PORT = os.getenv("POSTGRES_PORT", "5432")
# DB_NAME = os.getenv("POSTGRES_DB", "nexa_db")

# # Construct the SQLAlchemy database URL
# DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# # Global SQLAlchemy components for compatibility with models.py
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# class DatabaseManager:
#     """Encapsulates SQLAlchemy engine and session handling for the application.

#     Provides a ``get_session`` generator yielding a session that is automatically
#     closed after use.
#     """

#     def __init__(self, database_uri: str = DATABASE_URL):
#         self.engine = create_engine(database_uri)
#         self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
#         self.Base = Base  # Reuse the global Base if needed, or instantiate new if preferred

#     def get_session(self) -> Generator:
#         """Yield a database session and ensure it is closed after use."""
#         db = self.SessionLocal()
#         try:
#             yield db
#         finally:
#             db.close()

# # Optional helper for FastAPI or other frameworks
# def get_db():
#     """Yield a database session (legacy helper)."""
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close() """