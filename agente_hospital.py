import time
import re
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- 1. CONFIGURACIÓN ---
MODELO = "qwen2.5-coder:1.5b"
print(f"🔵 Iniciando Sistema RAG Blindado con {MODELO}...")

db = SQLDatabase.from_uri("sqlite:///hospital.db")
llm = OllamaLLM(model=MODELO, temperature=0) # Temp 0 es vital para SQL

# --- 2. FUNCIÓN DE LIMPIEZA QUIRÚRGICA ---
def limpiar_sql(texto_bruto):
    """
    Busca patrones SQL dentro del texto que escupe el modelo.
    Ignora explicaciones como 'Here is the code:'.
    """
    # 1. Intentar extraer contenido entre bloques de código ```sql ... ```
    patron_bloque = r"```sql\s*(.*?)\s*```"
    match_bloque = re.search(patron_bloque, texto_bruto, re.DOTALL)
    if match_bloque:
        return match_bloque.group(1).strip()
    
    # 2. Si no hay bloques, buscar la primera sentencia SELECT pura
    # Busca desde 'SELECT' hasta el primer ';' o fin de línea
    patron_select = r"(SELECT.*?(?:;|$))"
    match_select = re.search(patron_select, texto_bruto, re.IGNORECASE | re.DOTALL)
    if match_select:
        return match_select.group(1).strip()
        
    # 3. Si todo falla, devolver el texto original (probablemente fallará pero lo intentamos)
    return texto_bruto.strip()

# --- 3. FASE A: GENERACIÓN SQL (FEW-SHOT PROMPT) ---
# Le damos ejemplos explícitos para corregir sus alucinaciones previas
template_sql = """You are a SQLite query generator. Respond ONLY with SQL.

SCHEMA:
1. Table 'areas':
   - Columns: nombre, ubicacion, tiempo_espera_minutos
   - Keywords: Rayos X, Cafeteria, UCI, Urgencias, Laboratorio.

2. Table 'pacientes':
   - Columns: nombre_completo, estado, ubicacion_actual, diagnostico_breve
   - Keywords: Juan, Maria, Patient, Sick, Diagnosis.

EXAMPLES:
Q: Where is Rayos X?
SQL: SELECT ubicacion, tiempo_espera_minutos FROM areas WHERE nombre LIKE '%Rayos%';

Q: Where is patient Juan?
SQL: SELECT estado, ubicacion_actual FROM pacientes WHERE nombre_completo LIKE '%Juan%';

Q: {question}
SQL:"""

prompt_sql = PromptTemplate.from_template(template_sql)
sql_chain = prompt_sql | llm | StrOutputParser()

# --- 4. FASE B: RESPUESTA HUMANA ---
template_respuesta = """You are a helpful hospital assistant.
User Question: {question}
Data found: {result}

Task: Answer the user question in Spanish using the Data found.
- If Data is empty, say "No encontré información en el sistema."
- Be concise.

Answer:"""

prompt_respuesta = PromptTemplate.from_template(template_respuesta)
respuesta_chain = prompt_respuesta | llm | StrOutputParser()

# --- 5. ORQUESTADOR ---
def consultar(pregunta):
    print(f"\n👤 Usuario: {pregunta}")
    
    try:
        # 1. Obtener respuesta cruda del modelo
        sql_bruto = sql_chain.invoke({"question": pregunta})
        
        # 2. Limpiar la respuesta (Aquí ocurre la magia)
        sql_limpio = limpiar_sql(sql_bruto)
        print(f"   ⚙️ SQL Generado: {sql_limpio}") 
        
        # 3. Ejecutar SQL
        runner = QuerySQLDataBaseTool(db=db)
        resultado = runner.invoke(sql_limpio)
        print(f"   💾 Datos DB: {resultado}")
        
        # 4. Responder
        respuesta = respuesta_chain.invoke({"question": pregunta, "result": resultado})
        print(f"🤖 Asistente: {respuesta}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# --- 6. EJECUCIÓN ---
if __name__ == "__main__":
    consultar("¿Dónde queda Rayos X y cuánto demora?")
    consultar("¿Cuál es el estado y ubicación de Juan?")