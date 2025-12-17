"""
RAG Agent implementation using LangChain for SQL database querying.
Based on the working prototype agente_hospital_v5.py.
"""
import re
import ast
from typing import Optional
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.infrastructure.llm_client import OllamaClient
from src.infrastructure.exceptions import LLMConnectionError
from .prompts import SQL_GENERATION_TEMPLATE, RESPONSE_FORMATTING_TEMPLATE


class RAGAgent:
    """
    Agente de Recuperación Aumentada (RAG) para consultas a la base de datos del hospital.

    Utiliza LangChain para traducir preguntas en lenguaje natural a consultas SQL
    y formatea las respuestas adecuadamente. Basado en el prototipo funcional con
    aplicación de comodines y enfoque de dos fases.
    """
    
    def __init__(
        self,
        database_uri: str = "sqlite:///data/hospital.db",
        model_name: str = "qwen2.5-coder:1.5b"
    ):
        """
        Inicializa el agente RAG.

        Parámetros:
            database_uri: Cadena de conexión SQLAlchemy a la base de datos.
            model_name: Nombre del modelo Ollama a usar.
        """
        self.ollama_client = OllamaClient(model_name=model_name)
        self.model_name = model_name
        self.database_uri = database_uri
        
        # Initialize LangChain components
        try:
            self.db = SQLDatabase.from_uri(database_uri)
            # Lower temperature for SQL generation (more deterministic)
            self.llm = OllamaLLM(model=model_name, temperature=0.1)
            
            # Setup SQL generation chain
            self.sql_prompt = PromptTemplate.from_template(SQL_GENERATION_TEMPLATE)
            self.sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            
            # Setup response formatting chain
            self.response_prompt = PromptTemplate.from_template(RESPONSE_FORMATTING_TEMPLATE)
            self.response_chain = self.response_prompt | self.llm | StrOutputParser()
            
            # Setup query execution tool
            self.query_tool = QuerySQLDataBaseTool(db=self.db)
            
        except Exception as e:
            raise LLMConnectionError(f"Error al inicializar el agente RAG: {e}")
    
    def _clean_sql(self, raw_sql: str) -> str:
        """
        Clean SQL query from LLM output.
        
        Extracts SQL from markdown code blocks or finds SELECT statements.
        
        Args:
            raw_sql: Raw output from LLM that may contain SQL.
            
        Returns:
            Cleaned SQL query string.
        """
        # Try to extract from markdown code block
        code_block_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(code_block_pattern, raw_sql, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Try to find SELECT statement
        select_pattern = r"(SELECT.*?(?:;|$))"
        match = re.search(select_pattern, raw_sql, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Return as-is if no pattern matched
        return raw_sql.strip()
    
    def query(self, question: str) -> str:
        """
        Process a natural language question and return an answer.
        
        Uses a two-phase approach:
        1. Generate SQL query from question
        2. Execute query and format results into natural language
        
        Args:
            question: User's question in natural language.
            
        Returns:
            Formatted answer based on database query results.
            
        Raises:
            LLMConnectionError: If LLM service is unavailable.
            
        Example:
            >>> agent = RAGAgent()
            >>> answer = agent.query("¿Dónde está el paciente Juan Pérez?")
            >>> print(answer)
        """
        if not self.ollama_client.is_available():
            raise LLMConnectionError(
                "El servicio Ollama no está disponible. Por favor, asegúrate de que esté ejecutándose."
            )
        
        try:
            # Phase 1: Generate SQL query
            raw_sql = self.sql_chain.invoke({"question": question})
            clean_sql = self._clean_sql(raw_sql)
            
            # Phase 2: Execute query
            result_str = self.query_tool.invoke(clean_sql)
            
            # Phase 3: Parse and check results
            try:
                result_list = ast.literal_eval(result_str)
            except:
                result_list = []
            
            # Phase 4: Format response
            if not result_list:
                return "No encontré registros en el sistema que coincidan con tu búsqueda."
            else:
                formatted_response = self.response_chain.invoke({
                    "question": question,
                    "result": result_str
                })
                return formatted_response
                
        except Exception as e:
            # Fallback error handling
            return self._fallback_query(question, str(e))
    
    def _fallback_query(self, question: str, error: str) -> str:
        """
        Fallback method when SQL query generation fails.
        
        Args:
            question: Original user question.
            error: Error message from failed query.
            
        Returns:
            Informative error message or alternative response.
        """
        return f"""No pude generar una consulta SQL válida para: "{question}"

Error: {error}

Por favor, reformula tu pregunta o proporciona más detalles.
Puedo ayudarte con:
- Ubicación de pacientes
- Estado de pacientes
- Ubicación de áreas del hospital
- Tiempos de espera en diferentes áreas
"""
