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
        self.ollama_client = OllamaClient(model_name=model_name)
        self.model_name = model_name
        self.database_uri = database_uri

        try:
            self.db = SQLDatabase.from_uri(database_uri, view_support=True)
            self.llm = OllamaLLM(model=model_name, temperature=0)
            self.prompt_sql = SQL_GENERATION_TEMPLATE
            self.prompt_response = RESPONSE_FORMATTING_TEMPLATE
        except Exception as e:
            raise LLMConnectionError(
                f"Error CRÍTICO al conectar Agente con PostgreSQL: {e}"
            )

    # ------------------------------------------------------------------
    #  LIMPIADOR DE SQL
    # ------------------------------------------------------------------
    def clean_sql(self, text: str) -> str:
        text = re.sub(r"</?SQL>", "", text, flags=re.I)
        md = re.search(r"```(?:sql)?(.*?)(?:```|$)", text, re.S | re.I)
        if md:
            text = md.group(1)
        sel = re.search(r"(SELECT.*?)(?:;|$)", text, re.S | re.I)
        if sel:
            text = sel.group(1)
        # whitelist columnas
        text = re.sub(
            r"SELECT\s+.*?\s+FROM\s+directorio_telefonico",
            "SELECT nombre_referencia, numero_anexo FROM directorio_telefonico",
            text, flags=re.I
        )
        text = re.sub(
            r"SELECT\s+.*?\s+FROM\s+vista_ubicaciones_maestra",
            "SELECT nombre_unidad, nombre_piso, nombre_edificio FROM vista_ubicaciones_maestra",
            text, flags=re.I
        )
        return text.strip()

    # ------------------------------------------------------------------
    #  FLUJO PRINCIPAL
    # ------------------------------------------------------------------
    def get_answer(self, question: str) -> Dict[str, Any]:
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
            schema_info = self.db.get_table_info()
            filled_prompt_sql = self.prompt_sql.format(
                question=question,
                schema=schema_info
            )

            raw_generated = self.llm.invoke(filled_prompt_sql)
            clean_query = self.clean_sql(raw_generated)
            result_package["sql"] = clean_query

            if not clean_query or "SELECT" not in clean_query.upper():
                result_package["raw_data"] = "[]"
                result_package["answer"] = "No pude generar una consulta válida para tu pregunta."
                return result_package

            # ---- EJECUCIÓN ----
            try:
                db_result = self.db.run(clean_query)
            except Exception as db_err:
                result_package["raw_data"] = f"Error ejecutando SQL: {str(db_err)}"
                result_package["error"] = str(db_err)
                result_package["answer"] = "Hubo un error técnico al consultar la base de datos."
                return result_package

            # ---- DETECCIÓN DE LISTA VACÍA ----
            try:
                data = ast.literal_eval(db_result) if db_result else []
            except Exception:
                data = []

            if not data:                       # <-- aquí la prueba correcta
                result_package["raw_data"] = "[]"
                result_package["answer"] = "No encontré información exacta."
                return result_package

            # ---- CONVERSIÓN A TEXTO BONITO ----
            if len(data[0]) == 2:          # directorio_telefonico
                result_text = "\n".join(f"• {name} - anexo {ext}" for name, ext in data)
            else:                          # vista_ubicaciones_maestra
                result_text = "\n".join(
                    f"• {unit} está en {building}, {floor}"
                    for unit, floor, building in data
                )

            result_package["raw_data"] = result_text

            # ---- FORMATO FINAL ----
            filled_prompt_response = self.prompt_response.format(
                question=question,
                result=result_text
            )
            final_answer = self.llm.invoke(filled_prompt_response)
            result_package["answer"] = final_answer
            return result_package

        except Exception as e:
            result_package["error"] = str(e)
            result_package["answer"] = "Lo siento, ocurrió un error inesperado al procesar tu solicitud."
            return result_package

    # ------------------------------------------------------------------
    #  COMPATIBILIDAD
    # ------------------------------------------------------------------
    def query(self, question: str) -> str:
        return self.get_answer(question)["answer"]

    def query_with_debug(self, question: str) -> tuple:
        result = self.get_answer(question)
        debug_info = {
            "sql": result.get("sql"),
            "raw_data": result.get("raw_data"),
            "final_answer": result.get("answer"),
            "error": result.get("error")
        }
        return result["answer"], debug_info