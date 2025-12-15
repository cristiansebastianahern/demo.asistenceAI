"""
Application layer use cases for the Hospital Assistant.
"""
from typing import Optional
from src.infrastructure.database import DatabaseManager
from src.infrastructure.repositories import SQLPatientRepository, SQLHospitalAreaRepository
from src.infrastructure.llm_client import OllamaClient
from src.infrastructure.exceptions import LLMConnectionError, DatabaseConnectionError
from .rag_agent import RAGAgent

class HospitalAssistantUseCase:
    """
    Main use case orchestrating hospital assistant functionality.
    
    Coordinates between repositories, LLM client, and RAG agent
    to answer user questions about hospital data.
    """
    
    def __init__(
        self,
        database_uri: str = "sqlite:///hospital.db",
        model_name: str = "qwen2.5-coder:latest"
    ):
        """
        Initialize the use case with dependencies.
        
        Args:
            database_uri: Database connection string.
            model_name: Ollama model name.
        """
        self.db_manager = DatabaseManager(database_uri)
        self.patient_repo = SQLPatientRepository(self.db_manager)
        self.area_repo = SQLHospitalAreaRepository(self.db_manager)
        self.rag_agent = RAGAgent(database_uri, model_name)
        self.llm_client = OllamaClient(model_name)
    
    def ask_question(self, question: str) -> str:
        """
        Main entry point for user questions.
        
        Processes natural language questions and returns answers
        based on hospital database information.
        
        Args:
            question: User's question in natural language.
            
        Returns:
            Answer to the question.
            
        Raises:
            LLMConnectionError: If LLM service is unavailable.
            DatabaseConnectionError: If database connection fails.
            
        Example:
            >>> use_case = HospitalAssistantUseCase()
            >>> answer = use_case.ask_question("¿Dónde está la cafetería?")
            >>> print(answer)
        """
        # Check LLM availability
        if not self.llm_client.is_available():
            raise LLMConnectionError(
                "El servicio de IA no está disponible. "
                "Por favor, asegúrate de que Ollama esté ejecutándose."
            )
        
        try:
            # Use RAG agent for complex queries
            answer = self.rag_agent.query(question)
            return answer
            
        except Exception as e:
            raise DatabaseConnectionError(
                f"Error al procesar la pregunta: {str(e)}"
            )
    
    def get_patient_info(self, patient_id: int) -> str:
        """
        Get formatted information about a specific patient.
        
        Args:
            patient_id: Patient ID.
            
        Returns:
            Formatted patient information.
        """
        patient = self.patient_repo.get_patient_by_id(patient_id)
        
        if not patient:
            return f"No se encontró información del paciente con ID {patient_id}."
        
        return f"""Información del Paciente:
- Nombre: {patient.full_name}
- Estado: {patient.status}
- Ubicación: {patient.location}
- Diagnóstico: {patient.diagnosis}
- Médico a cargo: {patient.doctor_in_charge}
"""
    
    def get_area_info(self, area_name: str) -> str:
        """
        Get formatted information about a hospital area.
        
        Args:
            area_name: Name of the hospital area.
            
        Returns:
            Formatted area information.
        """
        area = self.area_repo.get_area_by_name(area_name)
        
        if not area:
            return f"No se encontró información del área '{area_name}'."
        
        return f"""Información del Área:
- Nombre: {area.name}
- Ubicación: {area.location}
- Tiempo de espera: {area.wait_time_minutes} minutos
"""
    
    def list_all_areas(self) -> str:
        """
        List all hospital areas with their information.
        
        Returns:
            Formatted list of all areas.
        """
        areas = self.area_repo.get_all_areas()
        
        if not areas:
            return "No hay áreas registradas en el sistema."
        
        result = "Áreas del Hospital:\n\n"
        for area in areas:
            result += f"{area.name}\n"
            result += f"  - Ubicación: {area.location}\n"
            result += f"  - Tiempo de espera: {area.wait_time_minutes} min\n\n"
        
        return result
