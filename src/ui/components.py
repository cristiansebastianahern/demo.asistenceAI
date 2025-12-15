"""
Reusable UI components for the Streamlit interface.
"""
import streamlit as st

def display_chat_message(role: str, content: str):
    """
    Display a chat message with appropriate styling.
    
    Args:
        role: Either 'user' or 'assistant'
        content: Message content to display
    """
    with st.chat_message(role):
        st.markdown(content)

def display_example_questions():
    """
    Display example questions in the sidebar.
    
    Returns:
        Selected example question or None
    """
    st.sidebar.header("📋 Preguntas de Ejemplo")
    
    examples = [
        "¿Dónde está la cafetería?",
        "¿Cuál es el tiempo de espera en Urgencias?",
        "¿Dónde puedo encontrar Rayos X?",
        "Muestra todos los pacientes en estado crítico",
        "¿Qué áreas del hospital hay disponibles?"
    ]
    
    selected = None
    for example in examples:
        if st.sidebar.button(example, key=f"example_{example}"):
            selected = example
    
    return selected

def display_system_status(llm_available: bool, db_connected: bool):
    """
    Display system status indicators in the sidebar.
    
    Args:
        llm_available: Whether LLM service is available
        db_connected: Whether database is connected
    """
    st.sidebar.header("🔧 Estado del Sistema")
    
    llm_status = "🟢 Conectado" if llm_available else "🔴 Desconectado"
    db_status = "🟢 Conectado" if db_connected else "🔴 Desconectado"
    
    st.sidebar.text(f"LLM (Ollama): {llm_status}")
    st.sidebar.text(f"Base de Datos: {db_status}")
