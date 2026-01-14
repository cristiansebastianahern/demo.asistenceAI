from .entities import Patient, HospitalArea, User
from typing import Protocol, List, Optional

class UserRepository(Protocol):
    """
    Interface for accessing User data.
    """
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their email address."""
        ...

    def get_user_by_rut(self, rut: str) -> Optional[User]:
        """Retrieve a user by their RUT."""
        ...

    def get_password_hash(self, user_id: str) -> Optional[str]:
        """Retrieve the hashed password for a specific user."""
        ...

class PatientRepository(Protocol):
    """
    Interface for accessing Patient data.
    """
    def get_patient_by_id(self, id: int) -> Optional[Patient]:
        """Retrieve a patient by their unique ID."""
        ...

    def search_patients_by_name(self, name: str) -> List[Patient]:
        """Search for patients by name (partial match)."""
        ...

    def get_patients_by_status(self, status: str) -> List[Patient]:
        """Retrieve all patients with a specific status."""
        ...

class HospitalAreaRepository(Protocol):
    """
    Interface for accessing Hospital Area data.
    """
    def get_all_areas(self) -> List[HospitalArea]:
        """Retrieve all hospital areas."""
        ...

    def get_area_by_name(self, name: str) -> Optional[HospitalArea]:
        """Retrieve a specific area by its name."""
        ...
