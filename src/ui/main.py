"""
Main Streamlit application for Hospital Assistant AI.
"""
import streamlit as st
from src.application.use_cases import HospitalAssistantUseCase
from src.infrastructure.exceptions import LLMConnectionError, DatabaseConnectionError
from .components import display_chat_message, display_example_questions, display_system_status

# Page configuration
st.set_page_config(
    page_title="Hospital Assistant AI",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "use_case" not in st.session_state:
    st.session_state.use_case = HospitalAssistantUseCase()

# Main title
st.title("🏥 Asistente Virtual - Hospital Clínico Magallanes")
st.markdown("Pregunta sobre ubicaciones, pacientes, áreas del hospital y más.")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/150x150.png?text=Hospital+Logo", width=150)
    st.markdown("---")
    
    # System status
    try:
        llm_available = st.session_state.use_case.llm_client.is_available()
    except:
        llm_available = False
    
    display_system_status(llm_available, True)
    
    st.markdown("---")
    
    # Example questions
    selected_example = display_example_questions()
    
    st.markdown("---")
    st.markdown("### ℹ️ Información")
    st.markdown("""
    Este asistente puede ayudarte con:
    - 📍 Ubicaciones de áreas
    - ⏱️ Tiempos de espera
    - 👤 Información de pacientes
    - 🏥 Servicios del hospital
    """)

# Display chat history
for message in st.session_state.messages:
    display_chat_message(message["role"], message["content"])

# Handle example question selection
if selected_example:
    st.session_state.messages.append({"role": "user", "content": selected_example})
    display_chat_message("user", selected_example)
    
    # Generate response
    with st.spinner("Procesando..."):
        try:
            response = st.session_state.use_case.ask_question(selected_example)
            st.session_state.messages.append({"role": "assistant", "content": response})
            display_chat_message("assistant", response)
        except LLMConnectionError as e:
            error_msg = f"❌ Error de conexión con el servicio de IA: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except DatabaseConnectionError as e:
            error_msg = f"❌ Error de base de datos: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"❌ Error inesperado: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    st.rerun()

# Chat input
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    display_chat_message("user", prompt)
    
    # Generate response
    with st.spinner("Procesando..."):
        try:
            response = st.session_state.use_case.ask_question(prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            display_chat_message("assistant", response)
        except LLMConnectionError as e:
            error_msg = f"❌ Error de conexión con el servicio de IA: {str(e)}\n\nAsegúrate de que Ollama esté ejecutándose."
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except DatabaseConnectionError as e:
            error_msg = f"❌ Error de base de datos: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
        except Exception as e:
            error_msg = f"❌ Error inesperado: {str(e)}"
            st.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear chat button
if st.sidebar.button("🗑️ Limpiar Conversación"):
    st.session_state.messages = []
    st.rerun()
