"""
Pytest fixtures for database testing.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database import Base, DatabaseManager
from src.infrastructure.models import PatientModel, HospitalAreaModel

@pytest.fixture
def in_memory_db():
    """
    Create an in-memory SQLite database for testing.
    
    Yields:
        DatabaseManager instance with in-memory database.
    """
    db_manager = DatabaseManager("sqlite:///:memory:")
    
    # Create tables
    Base.metadata.create_all(db_manager.engine)
    
    yield db_manager
    
    # Cleanup
    Base.metadata.drop_all(db_manager.engine)

@pytest.fixture
def sample_patients(in_memory_db):
    """
    Populate the in-memory database with sample patient data.
    
    Args:
        in_memory_db: DatabaseManager fixture.
        
    Returns:
        DatabaseManager with populated data.
    """
    with in_memory_db.get_session() as session:
        patients = [
            PatientModel(
                id=1,
                nombre_completo="Juan Pérez",
                estado="Estable",
                ubicacion_actual="Habitación 101",
                diagnostico_breve="Fractura de tibia",
                medico_a_cargo="Dr. Gregory House"
            ),
            PatientModel(
                id=2,
                nombre_completo="María González",
                estado="Crítico",
                ubicacion_actual="UCI Cama 5",
                diagnostico_breve="Insuficiencia cardíaca",
                medico_a_cargo="Dra. Meredith Grey"
            ),
        ]
        session.add_all(patients)
    
    return in_memory_db

@pytest.fixture
def sample_areas(in_memory_db):
    """
    Populate the in-memory database with sample hospital area data.
    
    Args:
        in_memory_db: DatabaseManager fixture.
        
    Returns:
        DatabaseManager with populated data.
    """
    with in_memory_db.get_session() as session:
        areas = [
            HospitalAreaModel(
                id=1,
                nombre="Urgencias",
                ubicacion="Planta Baja, Entrada Principal",
                tiempo_espera_minutos=20
            ),
            HospitalAreaModel(
                id=2,
                nombre="Cafetería",
                ubicacion="Piso 2, Frente a ascensores",
                tiempo_espera_minutos=5
            ),
        ]
        session.add_all(areas)
    
    return in_memory_db
