from typing import Optional
from pydantic import BaseModel, Field

class Patient(BaseModel):
    """
    Entidad de dominio que representa a un paciente del hospital.
    """
    id: int = Field(..., description="Unique identifier of the patient")
    full_name: str = Field(..., description="Full name of the patient")
    status: str = Field(..., description="Current medical status (e.g., 'Estable', 'Crítico')")
    location: str = Field(..., description="Physical location in the hospital")
    diagnosis: str = Field(..., description="Brief diagnosis")
    doctor_in_charge: str = Field(..., description="Name of the doctor in charge")

class HospitalArea(BaseModel):
    """
    Entidad de dominio que representa un área física del hospital.
    """
    id: int = Field(..., description="Unique identifier of the area")
    name: str = Field(..., description="Name of the area (e.g., 'Urgencias')")
    location: str = Field(..., description="Description of the location")
    wait_time_minutes: int = Field(..., description="Estimated wait time in minutes")

class UserRole(BaseModel):
    """
    Entidad que representa un rol de usuario (ADMIN, MEDICO, PACIENTE).
    """
    id: int
    name: str
    description: Optional[str] = None

class User(BaseModel):
    """
    Entidad de dominio que representa a un usuario del sistema Nexa.
    """
    id: str # UUID
    rut: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool = True
