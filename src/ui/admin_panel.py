# src/ui/admin_panel.py
import streamlit as st
from src.infrastructure.admin_repository import AdminRepository

# ----------------------------------------------------------------------
# Helper – carga de datos y selectboxes
# ----------------------------------------------------------------------
def _load_repo():
    """Instancia única del repositorio (se guarda en session_state)."""
    if "admin_repo" not in st.session_state:
        st.session_state.admin_repo = AdminRepository()
    return st.session_state.admin_repo

# ----------------------------------------------------------------------
# Renderizado del Dashboard
# ----------------------------------------------------------------------
def render_admin_dashboard(user):
    """
    Renderiza el panel de super‑administrador.
    Requiere que user.role.name sea 'ADMIN'.
    """
    repo = _load_repo()

    st.title("⚙️ Panel de Super‑Administrador")
    
    # Definimos las pestañas de gestión
    tabs = st.tabs([
        "📊 Auditoría",
        "👥 Usuarios",
        "🛡️ Roles",
        "🏢 Edificios",
        "🛗 Pisos",
        "🏥 Unidades",
        "📒 Directorio",
    ])

    # ------------------------------------------------------------------
    # 1️⃣ Auditoría
    # ------------------------------------------------------------------
    with tabs[0]:
        st.subheader("📊 Historial de consultas")
        logs = repo.get_logs()
        if logs:
            st.dataframe(logs, hide_index=True, use_container_width=True)
        else:
            st.info("No hay registros de auditoría todavía.")

    # ------------------------------------------------------------------
    # 2️⃣ Usuarios (CRUD COMPLETO)
    # ------------------------------------------------------------------
    with tabs[1]:
        st.subheader("👥 Gestión de usuarios")
        users = repo.get_users()
        
        if users:
            st.markdown("✏️ *Edita directamente en la tabla (Nombre, Email, RUT, Rol)*")
            
            # CORRECCIÓN: Usamos TextColumn(disabled=True) en lugar de HiddenColumn
            # Esto evita el error de versión de Streamlit.
            edited = st.data_editor(
                users,
                column_config={
                    "id": st.column_config.TextColumn(label="ID Sistema", disabled=True),
                    "password_hash": st.column_config.TextColumn(label="Hash Clave", disabled=True),
                    "rol_id": st.column_config.NumberColumn(label="ID Rol", help="1=Admin, 2=Medico..."),
                    "rut": st.column_config.TextColumn(label="RUT", required=True),
                    "nombre_completo": st.column_config.TextColumn(label="Nombre", required=True),
                    "email": st.column_config.TextColumn(label="Email", required=True),
                },
                num_rows="dynamic",
                use_container_width=True,
                key="users_editor",
            )
            
            # Guardar cambios detectados en la tabla
            if edited != users:
                for row in edited:
                    try:
                        # IMPORTANTE: password=None para NO resetear la contraseña
                        repo.save_user(
                            rut=row["rut"],
                            nombre_completo=row["nombre_completo"],
                            email=row["email"],
                            password=None,
                            rol_id=row["rol_id"],
                        )
                    except Exception as e:
                        st.error(f"Error al guardar usuario {row.get('email', 'desconocido')}: {e}")

        else:
            st.info("No hay usuarios registrados aparte de ti.")

        st.divider()

        # ---- Formulario de creación (NUEVO USUARIO) ----
        with st.expander("➕ Crear nuevo usuario"):
            with st.form("new_user"):
                col_a, col_b = st.columns(2)
                with col_a:
                    rut = st.text_input("RUT", placeholder="12.345.678-9")
                    nombre = st.text_input("Nombre completo")
                with col_b:
                    email = st.text_input("Email")
                    pwd = st.text_input("Contraseña", type="password")
                
                # Selección de rol dinámica
                roles_list = repo.get_roles()
                role_options = {r["nombre_rol"]: r["id"] for r in roles_list}
                
                # Protección por si no hay roles
                if role_options:
                    rol_sel = st.selectbox("Asignar Rol", options=list(role_options.keys()))
                else:
                    rol_sel = None
                    st.warning("No hay roles definidos. Crea uno en la pestaña Roles primero.")
                
                submitted = st.form_submit_button("Crear Usuario")
                
                if submitted:
                    if not rut or not nombre or not email or not pwd:
                        st.error("Todos los campos son obligatorios.")
                    elif rol_sel is None:
                        st.error("Debes seleccionar un rol.")
                    else:
                        try:
                            repo.save_user(
                                rut=rut,
                                nombre_completo=nombre,
                                email=email,
                                password=pwd,
                                rol_id=role_options[rol_sel],
                            )
                            st.success(f"✅ Usuario {nombre} creado exitosamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error creando usuario: {e}")

        # ---- Borrar usuario ----
        if users:
            with st.expander("🗑️ Zona de Peligro (Eliminar Usuario)"):
                del_user = st.selectbox(
                    "Selecciona usuario a eliminar",
                    options=[u["email"] for u in users],
                    key="del_user_select",
                )
                if st.button("Eliminar Usuario Seleccionado", type="primary"):
                    try:
                        uid = next(u["id"] for u in users if u["email"] == del_user)
                        repo.delete_user(uid)
                        st.success("✅ Usuario eliminado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error eliminando: {e}")

    # ------------------------------------------------------------------
    # 3️⃣ Roles
    # ------------------------------------------------------------------
    with tabs[2]:
        st.subheader("🛡️ Gestión de roles")
        roles = repo.get_roles()
        st.dataframe(roles, hide_index=True, use_container_width=True)

        with st.expander("➕ Crear nuevo rol"):
            with st.form("new_role"):
                nombre = st.text_input("Nombre del rol (Ej: ENFERMERIA)")
                desc = st.text_area("Descripción")
                submitted = st.form_submit_button("Crear Rol")
                if submitted:
                    try:
                        repo.create_role(nombre.upper(), desc)
                        st.success("✅ Rol creado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ------------------------------------------------------------------
    # 4️⃣ Edificios
    # ------------------------------------------------------------------
    with tabs[3]:
        st.subheader("🏢 Edificios")
        edificios = repo.get_edificios()
        st.dataframe(edificios, hide_index=True, use_container_width=True)

        with st.expander("➕ Añadir edificio"):
            with st.form("new_edificio"):
                nombre = st.text_input("Nombre del edificio")
                codigo = st.text_input("Código interno (ÚNICO)")
                submitted = st.form_submit_button("Guardar Edificio")
                if submitted:
                    try:
                        repo.save_edificio(nombre, codigo)
                        st.success("✅ Edificio guardado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ------------------------------------------------------------------
    # 5️⃣ Pisos
    # ------------------------------------------------------------------
    with tabs[4]:
        st.subheader("🛗 Pisos")
        pisos = repo.get_pisos()
        st.dataframe(pisos, hide_index=True, use_container_width=True)

        with st.expander("➕ Añadir piso"):
            with st.form("new_piso"):
                # Dropdown para elegir edificio por nombre
                ed_list = repo.get_edificios()
                if ed_list:
                    edificio_opts = {e["nombre_edificio"]: e["id"] for e in ed_list}
                    edificio_nom = st.selectbox("Edificio", options=list(edificio_opts.keys()))
                else:
                    st.warning("Crea edificios primero.")
                    edificio_nom = None

                nivel = st.number_input("Nivel (Ej: -1 para Zócalo, 1 para Piso 1)", step=1)
                nombre = st.text_input("Nombre del piso (Ej: Zócalo, Piso 1)")
                
                submitted = st.form_submit_button("Guardar Piso")
                if submitted:
                    if edificio_nom:
                        try:
                            repo.save_piso(nombre, int(nivel), edificio_opts[edificio_nom])
                            st.success("✅ Piso guardado.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Falta seleccionar edificio.")

    # ------------------------------------------------------------------
    # 6️⃣ Unidades
    # ------------------------------------------------------------------
    with tabs[5]:
        st.subheader("🏥 Unidades Hospitalarias")
        unidades = repo.get_unidades()
        st.dataframe(unidades, hide_index=True, use_container_width=True)

        with st.expander("➕ Añadir unidad"):
            with st.form("new_unidad"):
                # Dropdown complejo: "Edificio - Nivel - Nombre Piso"
                pisos_list = repo.get_pisos()
                if pisos_list:
                    pisos_opts = {
                        f"{p['nombre_edificio']} (Nivel {p['nivel_numero']}: {p['nombre_piso']})": p["id"]
                        for p in pisos_list
                    }
                    piso_sel = st.selectbox("Ubicación (Piso)", options=list(pisos_opts.keys()))
                else:
                    st.warning("Crea pisos primero.")
                    piso_sel = None
                    
                nombre = st.text_input("Nombre de la unidad (Ej: Farmacia)")
                tipo = st.text_input("Tipo de servicio (Ej: Apoyo, Clínico)")
                
                submitted = st.form_submit_button("Guardar Unidad")
                if submitted:
                    if piso_sel:
                        try:
                            repo.save_unidad(nombre, tipo, pisos_opts[piso_sel])
                            st.success("✅ Unidad guardada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.error("Falta seleccionar piso.")

    # ------------------------------------------------------------------
    # 7️⃣ Directorio Telefónico
    # ------------------------------------------------------------------
    with tabs[6]:
        st.subheader("📒 Directorio Telefónico")
        contactos = repo.get_directorio()
        st.dataframe(contactos, hide_index=True, use_container_width=True)

        with st.expander("➕ Añadir contacto"):
            with st.form("new_contact"):
                nombre = st.text_input("Nombre de referencia / Cargo")
                anexo = st.number_input("Número de anexo", step=1, format="%d")
                submitted = st.form_submit_button("Guardar Contacto")
                if submitted:
                    try:
                        repo.save_contacto(nombre, int(anexo))
                        st.success("✅ Contacto guardado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")