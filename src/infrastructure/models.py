"""
SQLAlchemy ORM models mapping to the existing hospital database schema.
"""
from sqlalchemy import Column, Integer, String
from .database import Base

class PatientModel(Base):
    """
    ORM model for the 'pacientes' table.
    
    Maps Spanish column names to Python attributes.
    """
    __tablename__ = "pacientes"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    ubicacion_actual = Column(String, nullable=False)
    diagnostico_breve = Column(String, nullable=False)
    medico_a_cargo = Column(String, nullable=False)
    
    def __repr__(self) -> str:
        return f"<PatientModel(id={self.id}, nombre={self.nombre_completo})>"

class HospitalAreaModel(Base):
    """
    ORM model for the 'areas' table.
    
    Maps Spanish column names to Python attributes.
    """
    __tablename__ = "areas"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    ubicacion = Column(String, nullable=False)
    tiempo_espera_minutos = Column(Integer, nullable=False)
    
    def __repr__(self) -> str:
        return f"<HospitalAreaModel(id={self.id}, nombre={self.nombre})>"
