"""
Custom exceptions for the Infrastructure layer.
"""

class DatabaseConnectionError(Exception):
    """Raised when database connection fails."""
    pass

class LLMConnectionError(Exception):
    """Raised when LLM service is unavailable."""
    pass

class PatientNotFoundError(Exception):
    """Raised when a patient is not found in the database."""
    pass

class AreaNotFoundError(Exception):
    """Raised when a hospital area is not found in the database."""
    pass
