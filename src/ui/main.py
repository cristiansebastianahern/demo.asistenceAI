import streamlit as st
import os
from src.application.use_cases import HospitalAssistantUseCase, AuthUseCase
from src.infrastructure.exceptions import LLMConnectionError, DatabaseConnectionError
from src.ui.components import (
    display_chat_message, 
    display_example_questions, 
    display_system_status, 
    login_form, 
    load_css,
    render_header
)

# --- Configuración de Página ---
st.set_page_config(
    page_title="Nexa - Hospital Assistant AI",
    page_icon="🏥",
    layout="wide"
)

# --- Cargar Estilos ---
load_css()

# --- Helpers ---
def get_logo_path():
    path = "src/ui/assets/images/logo-Hospital-hori-xl.svg"
    return path if os.path.exists(path) else None

# --- Inicialización de Estado ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
# NUEVA VARIABLE DE ESTADO PARA CONTROLAR LA VISTA
if "show_admin_panel" not in st.session_state:
    st.session_state.show_admin_panel = False

# Inicializar Use Cases
if "auth_use_case" not in st.session_state:
    try:
        st.session_state.auth_use_case = AuthUseCase()
    except Exception as e:
        st.error(f"Error cargando auth: {e}")

if "hospital_use_case" not in st.session_state:
    try:
        st.session_state.hospital_use_case = HospitalAssistantUseCase()
    except Exception as e:
        st.error(f"Error cargando IA: {e}")

# --- Login Logic ---
def handle_login(email, password):
    try:
        user = st.session_state.auth_use_case.login(email, password)
        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.toast(f"✅ Bienvenida, {user.full_name}")
            st.rerun()
        else:
            st.error("Credenciales inválidas.")
    except Exception as e:
        st.error(f"Error: {e}")

# ==============================================================================
# 🔐 LOGIN (Bloqueante)
# ==============================================================================
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        logo = get_logo_path()
        if logo:
            st.image(logo, width=250)
        else:
            st.markdown("## 🏥 NEXA")
        username, password, submit = login_form()
        if submit:
            handle_login(username, password)
    st.stop()

# ==============================================================================
# 🏥 SIDEBAR (Navegación Global)
# ==============================================================================
with st.sidebar:
    logo = get_logo_path()
    if logo:
        st.image(logo, width=150)
    
    st.markdown("---")
    
    # Estado de servicios
    llm_ok = False
    if "hospital_use_case" in st.session_state:
        try:
            llm_ok = st.session_state.hospital_use_case.llm_client.is_available()
        except: pass
    display_system_status(llm_ok, True)
    
    st.markdown("---")
    
    # Usuario
    if st.session_state.user:
        st.write(f"👤 **{st.session_state.user.full_name}**")
        
        # BOTÓN SALIR
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.messages = []
            st.session_state.show_admin_panel = False
            st.rerun()
            
        st.markdown("---")
        
        # BOTÓN LIMPIAR CHAT (Solo visible si NO estamos en admin)
        if not st.session_state.show_admin_panel:
            if st.button("🗑️ Limpiar Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

        # ⚙️ SELECTOR DE VISTAS (Solo Admin)
        if getattr(st.session_state.user, "role", None) and st.session_state.user.role.name.upper() == "ADMIN":
            st.markdown("### 🛠️ Administración")
            
            # Switch entre Chat y Admin
            if st.session_state.show_admin_panel:
                if st.button("💬 Volver al Chat", type="secondary", use_container_width=True):
                    st.session_state.show_admin_panel = False
                    st.rerun()
            else:
                if st.button("⚙️ Panel de Control", type="primary", use_container_width=True):
                    st.session_state.show_admin_panel = True
                    st.rerun()

# ==============================================================================
# 🖥️ ÁREA PRINCIPAL (Renderizado Condicional)
# ==============================================================================

# VISTA 1: PANEL DE ADMINISTRACIÓN
if st.session_state.show_admin_panel:
    # Importamos aquí para evitar ciclos y solo cargar si es necesario
    from src.ui.admin_panel import render_admin_dashboard
    # Renderizamos en el área principal (fuera del sidebar)
    render_admin_dashboard(st.session_state.user)

# VISTA 2: CHATBOT (Vista por defecto)
else:
    # 1. Header
    render_header()
    
    # 2. Historial
    for message in st.session_state.messages:
        display_chat_message(message["role"], message["content"])

    # 3. Sugerencias (si vacío)
    selected_example = None
    if len(st.session_state.messages) == 0:
        selected_example = display_example_questions()

    # 4. Input
    prompt = st.chat_input("Escribe tu pregunta aquí...")
    if selected_example:
        prompt = selected_example

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        display_chat_message("user", prompt)
        
        with st.spinner("🧠 NEXA está pensando..."):
            try:
                response = st.session_state.hospital_use_case.ask_question(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                display_chat_message("assistant", response)
            except Exception as e:
                st.error(f"Error: {e}")
                
        if selected_example:
            st.rerun()


######################################################################################
# import streamlit as st
# from src.application.use_cases import HospitalAssistantUseCase, AuthUseCase
# from src.infrastructure.exceptions import LLMConnectionError, DatabaseConnectionError
# from src.ui.components import display_chat_message, display_example_questions, display_system_status, login_form, load_css
# from src.ui.ui_logo_helper import get_nexa_logo

# # Page configuration
# st.set_page_config(
#     page_title="Nexa - Hospital Assistant AI",
#     page_icon="🏥",
#     layout="wide"
# )

# # Load custom styles
# load_css()

# # Initialize session state
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# if "user" not in st.session_state:
#     st.session_state.user = None

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# if "auth_use_case" not in st.session_state:
#     st.session_state.auth_use_case = AuthUseCase()

# if "hospital_use_case" not in st.session_state:
#     st.session_state.hospital_use_case = HospitalAssistantUseCase()

# # Login Logic
# def handle_login(email, password):
#     user = st.session_state.auth_use_case.login(email, password)
#     if user:
#         st.session_state.authenticated = True
#         st.session_state.user = user
#         st.toast(f"✅ Bienvenida, {user.full_name}")
#         st.rerun()
#     else:
#         st.error("Credenciales inválidas o cuenta inactiva.")

# # -----------------------------------------------------------------------------
# # MAIN APP PROTECTION
# # -----------------------------------------------------------------------------
# if not st.session_state.authenticated:
#     # Centered login form
#     col1, col2, col3 = st.columns([1, 2, 1])
#     with col2:
#         st.image(get_nexa_logo(), width=200)
#         login_form(handle_login)
#     st.stop()

# # Main title
# st.title("🏥 Asistente Virtual - Hospital Clínico Magallanes")
# st.markdown("Pregunta sobre ubicaciones, pacientes, áreas del hospital y más.")

# # Sidebar
# with st.sidebar:
#     st.image(get_nexa_logo(), width=150)
#     st.markdown("---")
    
#     # System status
#     try:
#         llm_available = st.session_state.hospital_use_case.llm_client.is_available()
#     except:
#         llm_available = False
    
#     display_system_status(llm_available, True)
    
#     st.markdown("---")
    
#     # User info and Logout
#     if st.session_state.user:
#         st.write(f"👤 **{st.session_state.user.full_name}**")
#         st.write(f"🔹 {st.session_state.user.role.name}")
#         if st.sidebar.button("🚪 Cerrar Sesión"):
#             st.session_state.authenticated = False
#             st.session_state.user = None
#             st.rerun()

#     st.markdown("---")
    
#     # Example questions
#     selected_example = display_example_questions()
    
#     st.markdown("---")
#     st.markdown("### ℹ️ Información")
#     st.markdown("""
#     Este asistente puede ayudarte con:
#     - 📍 Ubicaciones de áreas
#     - ⏱️ Tiempos de espera
#     - 👤 Información de pacientes
#     - 🏥 Servicios del hospital
#     """)

# # Display chat history
# for message in st.session_state.messages:
#     display_chat_message(message["role"], message["content"])

# # Handle example question selection
# if selected_example:
#     st.session_state.messages.append({"role": "user", "content": selected_example})
#     display_chat_message("user", selected_example)
    
#     # Generate response
#     with st.spinner("Procesando..."):
#         try:
#             response = st.session_state.hospital_use_case.ask_question(selected_example)
#             st.session_state.messages.append({"role": "assistant", "content": response})
#             display_chat_message("assistant", response)
#         except LLMConnectionError as e:
#             error_msg = f"❌ Error de conexión con el servicio de IA: {str(e)}"
#             st.error(error_msg)
#             st.session_state.messages.append({"role": "assistant", "content": error_msg})
#         except DatabaseConnectionError as e:
#             error_msg = f"❌ Error de base de datos: {str(e)}"
#             st.error(error_msg)
#             st.session_state.messages.append({"role": "assistant", "content": error_msg})
#         except Exception as e:
#             error_msg = f"❌ Error inesperado: {str(e)}"
#             st.error(error_msg)
#             st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
#     st.rerun()

# # Chat input
# if prompt := st.chat_input("Escribe tu pregunta aquí..."):
#     # Add user message
#     st.session_state.messages.append({"role": "user", "content": prompt})
#     display_chat_message("user", prompt)
    
#     # Generate response
#     with st.spinner("Procesando..."):
#         try:
#             response = st.session_state.hospital_use_case.ask_question(prompt)
#             st.session_state.messages.append({"role": "assistant", "content": response})
#             display_chat_message("assistant", response)
#         except LLMConnectionError as e:
#             error_msg = f"❌ Error de conexión con el servicio de IA: {str(e)}\n\nAsegúrate de que Ollama esté ejecutándose."
#             st.error(error_msg)
#             st.session_state.messages.append({"role": "assistant", "content": error_msg})
#         except DatabaseConnectionError as e:
#             error_msg = f"❌ Error de base de datos: {str(e)}"
#             st.error(error_msg)
#             st.session_state.messages.append({"role": "assistant", "content": error_msg})
#         except Exception as e:
#             error_msg = f"❌ Error inesperado: {str(e)}"
#             st.error(error_msg)
#             st.session_state.messages.append({"role": "assistant", "content": error_msg})

# # Clear chat button
# if st.sidebar.button("🗑️ Limpiar Conversación"):
#     st.session_state.messages = []
#     st.rerun()
