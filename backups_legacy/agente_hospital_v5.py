import time
import re
import ast
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 1. CONFIGURACIÓN ---
MODELO = "qwen2.5-coder:1.5b"
print(f"🔵 Iniciando Sistema RAG V5 (Wildcards + Formatter) con {MODELO}...")

db = SQLDatabase.from_uri("sqlite:///hospital.db")
# Temperature 0.1 da un poco de flexibilidad para redacción, pero mantiene lógica
llm = OllamaLLM(model=MODELO, temperature=0.1)

# --- 2. HERRAMIENTAS ---
def limpiar_sql(texto_bruto):
    patron_bloque = r"```sql\s*(.*?)\s*```"
    match = re.search(patron_bloque, texto_bruto, re.DOTALL)
    if match: return match.group(1).strip()
    
    patron_select = r"(SELECT.*?(?:;|$))"
    match = re.search(patron_select, texto_bruto, re.IGNORECASE | re.DOTALL)
    if match: return match.group(1).strip()
    
    return texto_bruto.strip()

# --- 3. FASE SQL (ENFORCING WILDCARDS) ---
template_sql = """Role: SQL Expert.
Task: Generate SQL query for SQLite.

Tables:
- areas (nombre, ubicacion, tiempo_espera_minutos)
- pacientes (nombre_completo, estado, ubicacion_actual, diagnostico_breve)

CRITICAL RULES:
1. ALWAYS use wildcard % for text searches. Example: LIKE '%Name%'
2. Return ONLY the SQL code.

Examples:
Q: Rayos X? -> SELECT ubicacion, tiempo_espera_minutos FROM areas WHERE nombre LIKE '%Rayos%';
Q: Juan? -> SELECT estado, ubicacion_actual, diagnostico_breve FROM pacientes WHERE nombre_completo LIKE '%Juan%';

Question: {question}
SQL:"""

prompt_sql = PromptTemplate.from_template(template_sql)
sql_chain = prompt_sql | llm | StrOutputParser()

# --- 4. FASE RESPUESTA (DATA FORMATTER) ---
template_respuesta = """Task: Format the database result into a clean Spanish sentence.
User Question: {question}
Data: {result}

Instructions:
- Do NOT repeat the question.
- Construct a direct answer based on the Data.
- Example: "El paciente está en X con estado Y."

Respuesta:"""

prompt_respuesta = PromptTemplate.from_template(template_respuesta)
respuesta_chain = prompt_respuesta | llm | StrOutputParser()

# --- 5. ORQUESTADOR ---
def consultar(pregunta):
    print(f"\n👤 Usuario: {pregunta}")
    
    try:
        # 1. SQL
        sql_bruto = sql_chain.invoke({"question": pregunta})
        sql_limpio = limpiar_sql(sql_bruto)
        print(f"   ⚙️ SQL: {sql_limpio}") 
        
        # 2. Ejecutar
        runner = QuerySQLDataBaseTool(db=db)
        resultado_str = runner.invoke(sql_limpio)
        print(f"   💾 Data: {resultado_str}")
        
        # 3. Lógica Python
        try:
            resultado_lista = ast.literal_eval(resultado_str)
        except:
            resultado_lista = []

        if not resultado_lista:
            print("🤖 Asistente: No encontré registros en el sistema que coincidan con tu búsqueda.")
        else:
            respuesta = respuesta_chain.invoke({"question": pregunta, "result": resultado_str})
            print(f"🤖 Asistente: {respuesta}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# --- 6. PRUEBAS ---
if __name__ == "__main__":
    # Prueba 1: Wildcards (Ahora debería encontrar a Juan aunque no sea nombre exacto)
    consultar("¿Qué se sabe de Juan?")
    
    # Prueba 2: Formato correcto (No debería repetir pregunta)
    consultar("¿Dónde queda Rayos X y cuánto demora?")