import streamlit as st
import base64
import os

def load_css():
    """Carga el archivo style.css"""
    css_path = "src/ui/assets/style.css"
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def render_header():
    """
    Renderiza el encabezado oficial con soporte para logos SVG.
    """
    # Rutas a tus logos nuevos
    logo_path = "src/ui/assets/images/logo-Hospital-light-hori-xl.svg" # Texto Blanco (Para fondo oscuro/header)
    
    logo_html = ""
    if os.path.exists(logo_path):
        with open(logo_path, "r") as f:
            svg_content = f.read()
            # Ajustar tamaño si el SVG es muy grande
            svg_content = svg_content.replace('<svg ', '<svg style="height: 60px; width: auto;" ')
            b64_logo = base64.b64encode(svg_content.encode('utf-8')).decode("utf-8")
        logo_html = f'<img src="data:image/svg+xml;base64,{b64_logo}" class="nexa-logo">'
    else:
        logo_html = "<h2>NEXA</h2>" # Fallback

    # Renderizar HTML del Header
    st.markdown(f"""
        <div class="nexa-header">
            <div style="display: flex; align-items: center; gap: 15px;">
                {logo_html}
                <div style="color: white;">
                    <h3 style="margin:0; color:white !important; font-weight:700;">HOSPITAL CLÍNICO MAGALLANES</h3>
                    <p style="margin:0; color:rgba(255,255,255,0.9) !important; font-size: 0.9rem;">Asistente de IA Generativa</p>
                </div>
            </div>
            <div>
                <span style="background:rgba(255,255,255,0.2); padding:5px 10px; border-radius:15px; font-size:0.8rem; color:white;">
                    v2.0 Stable
                </span>
            </div>
        </div>
    """, unsafe_allow_html=True)

def login_form():
    """
    Muestra un formulario de inicio de sesión.
    Retorna: (email, password, submit_button_state) para que main.py maneje la lógica.
    """
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown("### 🔐 Acceso al Sistema Nexa")
    st.markdown("Ingrese sus credenciales corporativas.")
    
    with st.form("login_form"):
        email = st.text_input("Correo Electrónico", placeholder="admin@nexa.ai")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión", use_container_width=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    return email, password, submit

def display_chat_message(role: str, content: str):
    """
    Muestra un mensaje en el chat con el estilo correcto.
    """
    # Mapeo de iconos/avatares
    avatar = "🧑‍⚕️" if role == "user" else "🤖"
    
    # Si quisieras usar tus SVGs como avatar, podrías cargar la ruta aquí
    # Por ahora usamos emojis para simplificar
    
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)

def display_example_questions():
    """
    Muestra botones con preguntas sugeridas para guiar al usuario.
    Retorna el texto de la pregunta si se hace clic, o None.
    """
    st.markdown("#### 💡 Sugerencias rápidas:")
    
    col1, col2 = st.columns(2)
    selected_question = None
    
    with col1:
        if st.button("¿Dónde queda la Cafetería?", use_container_width=True):
            selected_question = "¿Dónde queda la Cafetería?"
        if st.button("Anexo de Farmacia", use_container_width=True):
            selected_question = "¿Cuál es el anexo de Farmacia?"
            
    with col2:
        if st.button("¿Cómo llego a Rayos X?", use_container_width=True):
            selected_question = "¿Dónde está la unidad de Rayos X?"
        if st.button("Datos de Karen Antiquera", use_container_width=True):
            selected_question = "Dame el anexo de Karen Antiquera"
            
    return selected_question

def display_system_status(llm_available: bool, db_available: bool):
    """
    Muestra indicadores de estado en el sidebar.
    """
    st.sidebar.markdown("### 📡 Estado del Sistema")
    
    if db_available:
        st.sidebar.success("Base de Datos: ONLINE")
    else:
        st.sidebar.error("Base de Datos: OFFLINE")
        
    if llm_available:
        st.sidebar.success("Motor IA: ONLINE")
    else:
        st.sidebar.warning("Motor IA: DESCONECTADO")