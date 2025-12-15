"""
Database connection management using SQLAlchemy.
"""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from .exceptions import DatabaseConnectionError

# Base class for ORM models
Base = declarative_base()

class DatabaseManager:
    """
    Manages database connections and sessions.
    
    Supports both SQLite (development) and PostgreSQL (production).
    """
    
    def __init__(self, connection_string: str = "sqlite:///hospital.db"):
        """
        Initialize the database manager.
        
        Args:
            connection_string: SQLAlchemy connection string.
                              Default: "sqlite:///hospital.db"
                              PostgreSQL example: "postgresql://user:pass@localhost/dbname"
        """
        try:
            self.engine = create_engine(
                connection_string,
                echo=False,  # Set to True for SQL query logging
                pool_pre_ping=True  # Verify connections before using
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to database: {e}")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Yields:
            SQLAlchemy Session object.
            
        Example:
            >>> db_manager = DatabaseManager()
            >>> with db_manager.get_session() as session:
            ...     patients = session.query(PatientModel).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseConnectionError(f"Database operation failed: {e}")
        finally:
            session.close()
