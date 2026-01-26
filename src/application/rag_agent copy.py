"""
RAG Agent implementation using explicit 3-step workflow (Generate -> Execute -> Format).
Refactored to fix context loss and improve reliability.
"""
import re
import ast
from typing import Dict, Any, Optional
from langchain_community.utilities import SQLDatabase
from langchain_ollama import OllamaLLM
from src.infrastructure.llm_client import OllamaClient
from src.infrastructure.exceptions import LLMConnectionError
from src.infrastructure.database import DATABASE_URL
from .prompts import SQL_GENERATION_TEMPLATE, RESPONSE_FORMATTING_TEMPLATE

class RAGAgent:
    """
    Agente RAG con flujo explícito: Generar SQL -> Ejecutar -> Formatear Respuesta.
    Implementa la lógica de 'HospitalAssistantUseCase'.
    """
    
    def __init__(
        self,
        database_uri: str = DATABASE_URL, 
        model_name: str = "qwen2.5-coder:1.5b"
    ):
        """
        Inicializa el agente RAG.
        """
        self.ollama_client = OllamaClient(model_name=model_name)
        self.model_name = model_name
        self.database_uri = database_uri
        
        try:
            # Inicializamos la conexión a DB
            self.db = SQLDatabase.from_uri(
                database_uri,
                view_support=True,
            )
            
            # Inicializar LLM
            self.llm = OllamaLLM(model=model_name, temperature=0)
            
            # Definir Prompts
            self.prompt_sql = SQL_GENERATION_TEMPLATE
            self.prompt_response = RESPONSE_FORMATTING_TEMPLATE
            
        except Exception as e:
            raise LLMConnectionError(f"Error CRÍTICO al conectar Agente con PostgreSQL: {e}")
    
    def clean_sql(self, text: str) -> str:
        """
        Limpia el texto generado para extraer solo el SQL válido.
        Elimina markdown, explicaciones y espacios extra.
        """
        # 1. Eliminar bloques de código markdown ```sql ... ``` o ``` ... ```
        pattern = r"```(?:sql)?\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)
        
        # 2. Eliminar explicaciones previas o posteriores (heurística simple: quedarse con SELECT)
        # Buscamos desde el primer SELECT hasta el final o un punto y coma
        select_pattern = r"(SELECT\s+.*)"
        match_select = re.search(select_pattern, text, re.DOTALL | re.IGNORECASE)
        if match_select:
            text = match_select.group(1)
            
        # 3. Limpiar espacios extra y ; final si existe (langchain run a veces prefiere sin ;)
        text = text.strip().rstrip(';')
        
        return text

    def get_answer(self, question: str) -> Dict[str, Any]:
        """
        Flujo explícito de 3 pasos:
        1. Generate: LLM genera SQL.
        2. Execute: Se ejecuta SQL en DB.
        3. Answer: LLM genera respuesta con datos.
        
        Returns:
            Dict con keys: 'answer', 'sql', 'raw_data'
        """
        result_package = {
            "answer": "",
            "sql": "",
            "raw_data": "",
            "error": None
        }

        if not self.ollama_client.is_available():
            result_package["answer"] = "⚠️ Error: El servicio de IA (Ollama) no está disponible."
            result_package["error"] = "Ollama unavailable"
            return result_package

        try:
            # STEP 0: Contexto del esquema (Fresh schema info)
            schema_info = self.db.get_table_info()
            
            # STEP 1: GENERATE SQL
            # Formateamos el prompt nosotros mismos para control total
            filled_prompt_sql = self.prompt_sql.format(
                question=question,
                schema=schema_info
            )
            
            raw_generated_text = self.llm.invoke(filled_prompt_sql)
            clean_sql_query = self.clean_sql(raw_generated_text)
            
            result_package["sql"] = clean_sql_query
            
            # STEP 2: EXECUTE SQL
            # Si el SQL está vacío o es inválido, abortar
            if not clean_sql_query or "SELECT" not in clean_sql_query.upper():
                result_package["raw_data"] = "[]"
                result_package["answer"] = "No pude generar una consulta válida para tu pregunta."
                return result_package
                
            try:
                # Ejecución directa
                db_result = self.db.run(clean_sql_query)
                result_package["raw_data"] = str(db_result)
            except Exception as db_err:
                result_package["raw_data"] = f"Error ejecutando SQL: {str(db_err)}"
                result_package["error"] = str(db_err)
                # Intentamos recuperarnos o informar
                result_package["answer"] = "Hubo un error técnico al consultar la base de datos."
                return result_package

            # Crucial Logic: Validar resultados vacíos
            if not db_result or db_result == "" or db_result == "[]":
                result_package["answer"] = f"No encontré información exacta en la base de datos sobre '{question}'."
                return result_package

            # STEP 3: FORMAT ANSWER
            # Formatear el prompt de respuesta
            filled_prompt_response = self.prompt_response.format(
                question=question,
                result=db_result
            )
            
            final_answer = self.llm.invoke(filled_prompt_response)
            result_package["answer"] = final_answer
            
            return result_package

        except Exception as e:
            result_package["error"] = str(e)
            result_package["answer"] = "Lo siento, ocurrió un error inesperado al procesar tu solicitud."
            return result_package

    # --- Backward Compatibility Methods ---

    def query(self, question: str) -> str:
        """
        Método de compatibilidad para llamadas simples.
        Devuelve solo la respuesta de texto.
        """
        result = self.get_answer(question)
        return result["answer"]

    def query_with_debug(self, question: str) -> tuple:
        """
        Método de compatibilidad para la UI actual.
        Adapta el dict de retorno al formato (answer, debug_info).
        """
        result = self.get_answer(question)
        
        debug_info = {
            "sql": result.get("sql"),
            "raw_data": result.get("raw_data"),
            "final_answer": result.get("answer"),
            "error": result.get("error")
        }
        
        # Mantenemos las claves que la UI espera aunque estén vacías
        # 'schema' no lo estamos devolviendo en get_answer para ser eficientes, 
        # pero podríamos añadirlo si fuera crítico. Por ahora 'sql' y 'raw_data' son lo vital.
        
        return result["answer"], debug_info