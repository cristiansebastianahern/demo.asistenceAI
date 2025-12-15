"""
Unit tests for Infrastructure layer repositories.
"""
import pytest
from src.infrastructure.repositories import SQLPatientRepository, SQLHospitalAreaRepository
from src.domain.entities import Patient, HospitalArea

def test_get_patient_by_id(sample_patients):
    """Test retrieving a patient by ID."""
    repo = SQLPatientRepository(sample_patients)
    
    patient = repo.get_patient_by_id(1)
    
    assert patient is not None
    assert patient.id == 1
    assert patient.full_name == "Juan Pérez"
    assert patient.status == "Estable"

def test_get_patient_by_id_not_found(sample_patients):
    """Test retrieving a non-existent patient."""
    repo = SQLPatientRepository(sample_patients)
    
    patient = repo.get_patient_by_id(999)
    
    assert patient is None

def test_search_patients_by_name(sample_patients):
    """Test searching patients by name."""
    repo = SQLPatientRepository(sample_patients)
    
    patients = repo.search_patients_by_name("María")
    
    assert len(patients) == 1
    assert patients[0].full_name == "María González"

def test_get_patients_by_status(sample_patients):
    """Test retrieving patients by status."""
    repo = SQLPatientRepository(sample_patients)
    
    critical_patients = repo.get_patients_by_status("Crítico")
    
    assert len(critical_patients) == 1
    assert critical_patients[0].status == "Crítico"

def test_get_all_areas(sample_areas):
    """Test retrieving all hospital areas."""
    repo = SQLHospitalAreaRepository(sample_areas)
    
    areas = repo.get_all_areas()
    
    assert len(areas) == 2
    assert isinstance(areas[0], HospitalArea)

def test_get_area_by_name(sample_areas):
    """Test retrieving an area by name."""
    repo = SQLHospitalAreaRepository(sample_areas)
    
    area = repo.get_area_by_name("Urgencias")
    
    assert area is not None
    assert area.name == "Urgencias"
    assert area.wait_time_minutes == 20
