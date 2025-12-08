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
print(f"🔵 Iniciando Sistema RAG Logic-First con {MODELO}...")

db = SQLDatabase.from_uri("sqlite:///hospital.db")
llm = OllamaLLM(model=MODELO, temperature=0.1)

# --- 2. HERRAMIENTAS DE LIMPIEZA ---
def limpiar_sql(texto_bruto):
    # Extraer solo el comando SQL usando Regex
    patron_bloque = r"```sql\s*(.*?)\s*```"
    match_bloque = re.search(patron_bloque, texto_bruto, re.DOTALL)
    if match_bloque: return match_bloque.group(1).strip()
    
    patron_select = r"(SELECT.*?(?:;|$))"
    match_select = re.search(patron_select, texto_bruto, re.IGNORECASE | re.DOTALL)
    if match_select: return match_select.group(1).strip()
    
    return texto_bruto.strip()

# --- 3. FASE A: GENERACIÓN SQL ---
template_sql = """Role: SQL Expert.
Task: Generate a SQLite query for the user question.

Schema:
- areas (nombre, ubicacion, tiempo_espera_minutos)
- pacientes (nombre_completo, estado, ubicacion_actual, diagnostico_breve)

Examples:
Q: Where is Rayos? -> SELECT ubicacion, tiempo_espera_minutos FROM areas WHERE nombre LIKE '%Rayos%';
Q: Status of Juan? -> SELECT estado, ubicacion_actual, diagnostico_breve FROM pacientes WHERE nombre_completo LIKE '%Juan%';

Question: {question}
SQL:"""

prompt_sql = PromptTemplate.from_template(template_sql)
sql_chain = prompt_sql | llm | StrOutputParser()

# --- 4. FASE B: REDACCIÓN HUMANA (Solo si hay datos) ---
template_respuesta = """Role: Hospital Receptionist.
Task: Turn raw data into a polite Spanish sentence.
User asked: {question}
Raw Data: {result}

Instructions:
- Summarize the data clearly.
- Do NOT say "Here is the information". Just give the answer.
- Answer in Spanish.

Respuesta:"""

prompt_respuesta = PromptTemplate.from_template(template_respuesta)
respuesta_chain = prompt_respuesta | llm | StrOutputParser()

# --- 5. ORQUESTADOR LÓGICO ---
def consultar(pregunta):
    print(f"\n👤 Usuario: {pregunta}")
    
    try:
        # 1. Generar SQL
        sql_bruto = sql_chain.invoke({"question": pregunta})
        sql_limpio = limpiar_sql(sql_bruto)
        print(f"   ⚙️ SQL: {sql_limpio}") 
        
        # 2. Ejecutar SQL
        runner = QuerySQLDataBaseTool(db=db)
        resultado_str = runner.invoke(sql_limpio)
        print(f"   💾 Raw: {resultado_str}")
        
        # 3. EVALUACIÓN LÓGICA (Python decide, no la IA)
        # Convertimos el string "[('A', 1)]" a lista real de Python para verificar si está vacía
        try:
            resultado_lista = ast.literal_eval(resultado_str)
        except:
            resultado_lista = [] # Si falla el parseo, asumimos vacío

        if not resultado_lista:
            # Si la lista está vacía, Python responde directamente (sin gastar tokens)
            print("🤖 Asistente: No encontré registros en el sistema que coincidan con tu búsqueda.")
        else:
            # Si HAY datos, dejamos que la IA los redacte bonito
            respuesta = respuesta_chain.invoke({"question": pregunta, "result": resultado_str})
            print(f"🤖 Asistente: {respuesta}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# --- 6. PRUEBAS ---
if __name__ == "__main__":
    consultar("¿Dónde queda Rayos X y cuánto demora?")
    consultar("¿Cuál es el estado de Juan?")
    consultar("¿Dónde está el paciente Batman?") # Prueba negativa