"""
Excepciones personalizadas para la capa de infraestructura.
"""

class DatabaseConnectionError(Exception):
    """
Se lanza cuando falla la conexión a la base de datos.
"""
    pass

class LLMConnectionError(Exception):
    """
Se lanza cuando el servicio LLM no está disponible.
"""
    pass

class PatientNotFoundError(Exception):
    """
Se lanza cuando no se encuentra un paciente en la base de datos.
"""
    pass

class AreaNotFoundError(Exception):
    """
Se lanza cuando no se encuentra un área del hospital en la base de datos.
"""
    pass
