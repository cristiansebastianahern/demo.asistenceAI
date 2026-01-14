from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from .database import Base

class RoleModel(Base):
    """
    ORM model for the 'roles' table.
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
    users = relationship("UserModel", back_populates="role")

class UserModel(Base):
    """
    ORM model for the 'usuarios' table.
    """
    __tablename__ = "usuarios"
    
    id = Column(String(36), primary_key=True, server_default=func.uuid_generate_v4())
    rut = Column(String(12), unique=True, nullable=False)
    nombre_completo = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    
    role = relationship("RoleModel", back_populates="users")

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
