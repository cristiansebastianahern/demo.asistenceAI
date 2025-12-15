"""
Concrete implementations of repository interfaces using SQLAlchemy.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from src.domain.entities import Patient, HospitalArea
from src.domain.interfaces import PatientRepository, HospitalAreaRepository
from .models import PatientModel, HospitalAreaModel
from .database import DatabaseManager
from .exceptions import PatientNotFoundError, AreaNotFoundError

class SQLPatientRepository:
    """
    SQLAlchemy implementation of PatientRepository.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the repository with a database manager.
        
        Args:
            db_manager: DatabaseManager instance for session handling.
        """
        self.db_manager = db_manager
    
    def _model_to_entity(self, model: PatientModel) -> Patient:
        """
        Convert ORM model to domain entity.
        
        Args:
            model: PatientModel instance.
            
        Returns:
            Patient domain entity.
        """
        return Patient(
            id=model.id,
            full_name=model.nombre_completo,
            status=model.estado,
            location=model.ubicacion_actual,
            diagnosis=model.diagnostico_breve,
            doctor_in_charge=model.medico_a_cargo
        )
    
    def get_patient_by_id(self, id: int) -> Optional[Patient]:
        """
        Retrieve a patient by their unique ID.
        
        Args:
            id: Patient ID.
            
        Returns:
            Patient entity if found, None otherwise.
        """
        with self.db_manager.get_session() as session:
            model = session.query(PatientModel).filter(PatientModel.id == id).first()
            return self._model_to_entity(model) if model else None
    
    def search_patients_by_name(self, name: str) -> List[Patient]:
        """
        Search for patients by name (partial match, case-insensitive).
        
        Args:
            name: Name or partial name to search for.
            
        Returns:
            List of matching Patient entities.
        """
        with self.db_manager.get_session() as session:
            models = session.query(PatientModel).filter(
                PatientModel.nombre_completo.ilike(f"%{name}%")
            ).all()
            return [self._model_to_entity(model) for model in models]
    
    def get_patients_by_status(self, status: str) -> List[Patient]:
        """
        Retrieve all patients with a specific status.
        
        Args:
            status: Patient status (e.g., 'Crítico', 'Estable').
            
        Returns:
            List of Patient entities with the specified status.
        """
        with self.db_manager.get_session() as session:
            models = session.query(PatientModel).filter(
                PatientModel.estado == status
            ).all()
            return [self._model_to_entity(model) for model in models]

class SQLHospitalAreaRepository:
    """
    SQLAlchemy implementation of HospitalAreaRepository.
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the repository with a database manager.
        
        Args:
            db_manager: DatabaseManager instance for session handling.
        """
        self.db_manager = db_manager
    
    def _model_to_entity(self, model: HospitalAreaModel) -> HospitalArea:
        """
        Convert ORM model to domain entity.
        
        Args:
            model: HospitalAreaModel instance.
            
        Returns:
            HospitalArea domain entity.
        """
        return HospitalArea(
            id=model.id,
            name=model.nombre,
            location=model.ubicacion,
            wait_time_minutes=model.tiempo_espera_minutos
        )
    
    def get_all_areas(self) -> List[HospitalArea]:
        """
        Retrieve all hospital areas.
        
        Returns:
            List of all HospitalArea entities.
        """
        with self.db_manager.get_session() as session:
            models = session.query(HospitalAreaModel).all()
            return [self._model_to_entity(model) for model in models]
    
    def get_area_by_name(self, name: str) -> Optional[HospitalArea]:
        """
        Retrieve a specific area by its name (case-insensitive).
        
        Args:
            name: Name of the hospital area.
            
        Returns:
            HospitalArea entity if found, None otherwise.
        """
        with self.db_manager.get_session() as session:
            model = session.query(HospitalAreaModel).filter(
                HospitalAreaModel.nombre.ilike(name)
            ).first()
            return self._model_to_entity(model) if model else None
