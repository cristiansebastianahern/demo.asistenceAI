"""
RAG Agent implementation using LangChain for SQL database querying.
Refactored for PostgreSQL and View Support.
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
from src.infrastructure.database import DATABASE_URL # <--- LA CLAVE: Importamos la config real
from .prompts import SQL_GENERATION_TEMPLATE, RESPONSE_FORMATTING_TEMPLATE

class RAGAgent:
    """
    Agente de Recuperación Aumentada (RAG) para consultas a PostgreSQL.
    Conectado a la infraestructura Dockerizada de Nexa.
    """
    
    def __init__(
        self,
        # AHORA usa por defecto la conexión de PostgreSQL, no SQLite
        database_uri: str = DATABASE_URL, 
        model_name: str = "qwen2.5-coder:1.5b"
    ):
        """
        Inicializa el agente RAG conectado a PostgreSQL.
        """
        self.ollama_client = OllamaClient(model_name=model_name)
        self.model_name = model_name
        self.database_uri = database_uri
        
        try:
            # Inicializamos la conexión a DB
            # include_tables es opcional, pero ayuda a que el LLM no se distraiga con tablas de sistema
            self.db = SQLDatabase.from_uri(
                database_uri,
                view_support=True, # Permitir ver la vista_ubicaciones_maestra
            )
            
            # Temperatura baja para SQL preciso
            self.llm = OllamaLLM(model=model_name, temperature=0)
            
            # Cadena de Generación SQL
            self.sql_prompt = PromptTemplate.from_template(SQL_GENERATION_TEMPLATE)
            self.sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            
            # Cadena de Formateo de Respuesta Natural
            self.response_prompt = PromptTemplate.from_template(RESPONSE_FORMATTING_TEMPLATE)
            self.response_chain = self.response_prompt | self.llm | StrOutputParser()
            
            # Herramienta de ejecución
            self.query_tool = QuerySQLDataBaseTool(db=self.db)
            
        except Exception as e:
            raise LLMConnectionError(f"Error CRÍTICO al conectar Agente con PostgreSQL: {e}")
    
    def _clean_sql(self, raw_sql: str) -> str:
        """Limpia el SQL generado por el LLM (elimina markdown y explicaciones)."""
        # 1. Buscar bloques de código ```sql ... ```
        code_block_pattern = r"```sql\s*(.*?)\s*```"
        match = re.search(code_block_pattern, raw_sql, re.DOTALL)
        if match:
            return match.group(1).strip()
            
        # 2. Buscar bloques ``` ... ``` genéricos
        code_block_generic = r"```\s*(.*?)\s*```"
        match_gen = re.search(code_block_generic, raw_sql, re.DOTALL)
        if match_gen:
            return match_gen.group(1).strip()
        
        # 3. Buscar sentencia SELECT pura si no hay markdown
        select_pattern = r"(SELECT\s+.*?(?:;|$))"
        match_select = re.search(select_pattern, raw_sql, re.IGNORECASE | re.DOTALL)
        if match_select:
            return match_select.group(1).strip()
        
        return raw_sql.strip()
    
    def query(self, question: str) -> str:
        """
        Procesa la pregunta, genera SQL, consulta Postgres y responde.
        """
        if not self.ollama_client.is_available():
            return "⚠️ Error: El servicio de IA (Ollama) no está respondiendo."
        
        try:
            # FASE 1: Generar SQL
            # Inyectamos el esquema dinámicamente para que el prompt siempre esté fresco
            raw_sql = self.sql_chain.invoke({
                "question": question,
                # LangChain puede obtener info de las tablas automáticamente si se lo pedimos,
                # pero aquí usamos el contexto definido en prompts.py
            })
            clean_sql = self._clean_sql(raw_sql)
            
            # Debug: Imprimir en consola para ver qué está pensando la IA (Útil para desarrollo)
            print(f"🧠 [RAG] SQL Generado: {clean_sql}")
            
            # FASE 2: Ejecutar en PostgreSQL
            result_str = self.query_tool.invoke(clean_sql)
            print(f"💾 [DB] Resultado: {result_str}")
            
            # FASE 3: Verificar resultados vacíos
            # A veces la base de datos devuelve "", "[]", o "None"
            if not result_str or result_str.strip() == "" or result_str == "[]":
                return "No encontré información exacta en la base de datos para esa consulta. Intenta reformularla."
            
            # FASE 4: Respuesta Humana
            formatted_response = self.response_chain.invoke({
                "question": question,
                "result": result_str
            })
            return formatted_response
                
        except Exception as e:
            return self._fallback_query(question, str(e))
    
    def _fallback_query(self, question: str, error: str) -> str:
        return f"""Disculpa, tuve un error técnico al consultar la base de datos.
        
Detalle: {error}

Por favor intenta preguntar de otra forma, por ejemplo:
- "¿Cuál es el anexo de Farmacia?"
- "¿Dónde queda el Auditorio?"
"""




#################################################################################
# """
# RAG Agent implementation using LangChain for SQL database querying.
# Based on the working prototype agente_hospital_v5.py.
# """
# import re
# import ast
# from typing import Optional
# from langchain_community.utilities import SQLDatabase
# from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
# from langchain_ollama import OllamaLLM
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser
# from src.infrastructure.llm_client import OllamaClient
# from src.infrastructure.exceptions import LLMConnectionError
# from .prompts import SQL_GENERATION_TEMPLATE, RESPONSE_FORMATTING_TEMPLATE


# class RAGAgent:
#     """
#     Agente de Recuperación Aumentada (RAG) para consultas a la base de datos del hospital.

#     Utiliza LangChain para traducir preguntas en lenguaje natural a consultas SQL
#     y formatea las respuestas adecuadamente. Basado en el prototipo funcional con
#     aplicación de comodines y enfoque de dos fases.
#     """
    
#     def __init__(
#         self,
#         database_uri: str = "sqlite:///data/hospital.db",
#         model_name: str = "qwen2.5-coder:1.5b"
#     ):
#         """
#         Inicializa el agente RAG.

#         Parámetros:
#             database_uri: Cadena de conexión SQLAlchemy a la base de datos.
#             model_name: Nombre del modelo Ollama a usar.
#         """
#         self.ollama_client = OllamaClient(model_name=model_name)
#         self.model_name = model_name
#         self.database_uri = database_uri
        
#         # Initialize LangChain components
#         try:
#             self.db = SQLDatabase.from_uri(database_uri)
#             # Lower temperature for SQL generation (more deterministic)
#             self.llm = OllamaLLM(model=model_name, temperature=0.1)
            
#             # Setup SQL generation chain
#             self.sql_prompt = PromptTemplate.from_template(SQL_GENERATION_TEMPLATE)
#             self.sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            
#             # Setup response formatting chain
#             self.response_prompt = PromptTemplate.from_template(RESPONSE_FORMATTING_TEMPLATE)
#             self.response_chain = self.response_prompt | self.llm | StrOutputParser()
            
#             # Setup query execution tool
#             self.query_tool = QuerySQLDataBaseTool(db=self.db)
            
#         except Exception as e:
#             raise LLMConnectionError(f"Error al inicializar el agente RAG: {e}")
    
#     def _clean_sql(self, raw_sql: str) -> str:
#         """
#         Clean SQL query from LLM output.
        
#         Extracts SQL from markdown code blocks or finds SELECT statements.
        
#         Args:
#             raw_sql: Raw output from LLM that may contain SQL.
            
#         Returns:
#             Cleaned SQL query string.
#         """
#         # Try to extract from markdown code block
#         code_block_pattern = r"```sql\s*(.*?)\s*```"
#         match = re.search(code_block_pattern, raw_sql, re.DOTALL)
#         if match:
#             return match.group(1).strip()
        
#         # Try to find SELECT statement
#         select_pattern = r"(SELECT.*?(?:;|$))"
#         match = re.search(select_pattern, raw_sql, re.IGNORECASE | re.DOTALL)
#         if match:
#             return match.group(1).strip()
        
#         # Return as-is if no pattern matched
#         return raw_sql.strip()
    
#     def query(self, question: str) -> str:
#         """
#         Process a natural language question and return an answer.
        
#         Uses a two-phase approach:
#         1. Generate SQL query from question
#         2. Execute query and format results into natural language
        
#         Args:
#             question: User's question in natural language.
            
#         Returns:
#             Formatted answer based on database query results.
            
#         Raises:
#             LLMConnectionError: If LLM service is unavailable.
            
#         Example:
#             >>> agent = RAGAgent()
#             >>> answer = agent.query("¿Dónde está el paciente Juan Pérez?")
#             >>> print(answer)
#         """
#         if not self.ollama_client.is_available():
#             raise LLMConnectionError(
#                 "El servicio Ollama no está disponible. Por favor, asegúrate de que esté ejecutándose."
#             )
        
#         try:
#             # Phase 1: Generate SQL query
#             raw_sql = self.sql_chain.invoke({"question": question})
#             clean_sql = self._clean_sql(raw_sql)
            
#             # Phase 2: Execute query
#             result_str = self.query_tool.invoke(clean_sql)
            
#             # Phase 3: Parse and check results
#             try:
#                 result_list = ast.literal_eval(result_str)
#             except:
#                 result_list = []
            
#             # Phase 4: Format response
#             if not result_list:
#                 return "No encontré registros en el sistema que coincidan con tu búsqueda."
#             else:
#                 formatted_response = self.response_chain.invoke({
#                     "question": question,
#                     "result": result_str
#                 })
#                 return formatted_response
                
#         except Exception as e:
#             # Fallback error handling
#             return self._fallback_query(question, str(e))
    
#     def _fallback_query(self, question: str, error: str) -> str:
#         """
#         Fallback method when SQL query generation fails.
        
#         Args:
#             question: Original user question.
#             error: Error message from failed query.
            
#         Returns:
#             Informative error message or alternative response.
#         """
#         return f"""No pude generar una consulta SQL válida para: "{question}"

# Error: {error}

# Por favor, reformula tu pregunta o proporciona más detalles.
# Puedo ayudarte con:
# - Ubicación de pacientes
# - Estado de pacientes
# - Ubicación de áreas del hospital
# - Tiempos de espera en diferentes áreas
# """
