"""
RAG Agent implementation using LangChain for SQL database querying.
"""
from typing import Optional
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_community.llms import Ollama
from src.infrastructure.llm_client import OllamaClient
from src.infrastructure.exceptions import LLMConnectionError
from .prompts import SYSTEM_PROMPT, DATABASE_SCHEMA_CONTEXT, RESPONSE_FORMAT_GUIDELINES

class RAGAgent:
    """
    Retrieval-Augmented Generation agent for hospital database queries.
    
    Uses LangChain to translate natural language questions into SQL queries
    and format responses appropriately.
    """
    
    def __init__(
        self,
        database_uri: str = "sqlite:///hospital.db",
        model_name: str = "qwen2.5-coder:latest"
    ):
        """
        Initialize the RAG agent.
        
        Args:
            database_uri: SQLAlchemy database connection string.
            model_name: Ollama model name to use.
        """
        self.ollama_client = OllamaClient(model_name=model_name)
        self.model_name = model_name
        self.database_uri = database_uri
        
        # Initialize LangChain components
        try:
            self.db = SQLDatabase.from_uri(database_uri)
            self.llm = Ollama(model=model_name, temperature=0.3)
        except Exception as e:
            raise LLMConnectionError(f"Failed to initialize RAG agent: {e}")
    
    def _build_context_prompt(self, question: str) -> str:
        """
        Build a context-aware prompt for the LLM.
        
        Args:
            question: User's natural language question.
            
        Returns:
            Formatted prompt with context.
        """
        return f"""{SYSTEM_PROMPT}

{DATABASE_SCHEMA_CONTEXT}

{RESPONSE_FORMAT_GUIDELINES}

Pregunta del usuario: {question}

Genera una consulta SQL para responder esta pregunta. La consulta debe ser válida para SQLite.
"""
    
    def query(self, question: str) -> str:
        """
        Process a natural language question and return an answer.
        
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
                "Ollama service is not available. Please ensure it's running."
            )
        
        try:
            # Create SQL query chain
            chain = create_sql_query_chain(self.llm, self.db)
            
            # Generate SQL query from natural language
            sql_query = chain.invoke({"question": question})
            
            # Execute the query
            result = self.db.run(sql_query)
            
            # Format the response using the LLM
            response_prompt = f"""Basándote en estos resultados de la base de datos:
{result}

Responde a la pregunta del usuario de forma clara y concisa en español:
{question}

Respuesta:"""
            
            formatted_response = self.ollama_client.generate(
                response_prompt,
                temperature=0.5
            )
            
            return formatted_response
            
        except Exception as e:
            # Fallback: try direct LLM query without SQL
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
        fallback_prompt = f"""No pude generar una consulta SQL válida para: "{question}"

Error: {error}

Por favor, reformula tu pregunta o proporciona más detalles.
Puedo ayudarte con:
- Ubicación de pacientes
- Estado de pacientes
- Ubicación de áreas del hospital
- Tiempos de espera en diferentes áreas
"""
        return fallback_prompt
