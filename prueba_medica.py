# prueba_medica.py
import time
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# 1. Configuración Visual (Vibe Coding)
print("🔵 Inicializando Sistema de Tesis Hospitalario...")
start_time = time.time()

# 2. Conexión con el Modelo Local
# Usamos el modelo 1B que descargamos para máxima velocidad en CPU
llm = OllamaLLM(model="llama3.2:1b")

# 3. Definir la personalidad del Asistente
prompt = ChatPromptTemplate.from_template("""
Eres un asistente virtual empático y eficiente del Hospital Clinico Magallanes.
Tu objetivo es informar a los familiares sobre el estado de los pacientes de forma clara y tranquila.

Consulta del usuario: {question}

Respuesta breve y profesional:
""")

# 4. Crear la cadena de pensamiento (Chain)
chain = prompt | llm

# 5. Simular una consulta
pregunta = "¿En que año fue fundado en magallanes, el Hospital Clinico Magallanes?"
print(f"👤 Usuario: {pregunta}")
print("... Pensando (Ejecutando en CPU local) ...")

respuesta = chain.invoke({"question": pregunta})

# 6. Mostrar resultado
end_time = time.time()
print(f"\n🤖 Asistente IA:\n{respuesta}")
print(f"\n⚡ Tiempo de respuesta: {end_time - start_time:.2f} segundos")