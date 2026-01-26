# src/ui/admin_panel.py
import streamlit as st
import pandas as pd
from typing import Callable, List, Dict, Any, Optional
from src.infrastructure.admin_repository import AdminRepository

# ----------------------------------------------------------------------
# Helper – Repository Loading
# ----------------------------------------------------------------------
def _load_repo():
    """Instancia única del repositorio (se guarda en session_state)."""
    if "admin_repo" not in st.session_state:
        st.session_state.admin_repo = AdminRepository()
    return st.session_state.admin_repo

# ----------------------------------------------------------------------
# GOLDEN SAMPLE: Buildings (Edificios) Tab
# ----------------------------------------------------------------------
def render_edificios_tab():
    """
    REFERENCE IMPLEMENTATION: Buildings CRUD with proper refresh logic.
    
    This is the "golden sample" that demonstrates proper st.rerun() usage
    to ensure the UI reflects database changes immediately.
    """
    repo = _load_repo()
    
    st.subheader("🏢 Gestión de Edificios")
    st.info("📝 **Instrucciones:** Edita los valores directamente en la tabla. Marca las casillas para seleccionar y eliminar edificios.")
    
    # ============================================================
    # CREATE SECTION: Form for adding new buildings
    # ============================================================
    with st.expander("➕ Crear Nuevo Edificio"):
        with st.form("form_create_edificio", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Edificio *", placeholder="Edificio A")
            with col2:
                codigo = st.text_input("Código Interno *", placeholder="A1", max_chars=10)
            
            submitted = st.form_submit_button("Crear Edificio", type="primary", use_container_width=True)
            
            if submitted:
                if not all([nombre, codigo]):
                    st.error("❌ Todos los campos son obligatorios.")
                else:
                    try:
                        repo.save_edificio(
                            id=None,  # ⭐ No ID = INSERT
                            nombre_edificio=nombre,
                            codigo_interno=codigo
                        )
                        st.success(f"✅ Edificio '{nombre}' creado exitosamente.")
                        st.rerun()  # CRITICAL: Force refresh to show new record
                    except Exception as e:
                        st.error(f"❌ {str(e)}")
    
    st.divider()
    
    # ============================================================
    # READ SECTION: Load and display existing buildings
    # ============================================================
    edificios = repo.get_edificios()
    
    if not edificios or len(edificios) == 0:
        st.warning("⚠️ No hay edificios registrados. Crea uno usando el formulario de arriba.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(edificios)
    
    # Add selection column (checkbox) as the first column
    df.insert(0, "Seleccionar", False)
    
    # Column configuration
    column_config = {
        "Seleccionar": st.column_config.CheckboxColumn(
            "Seleccionar",
            help="Marca para eliminar este edificio",
            default=False,
        ),
        "id": st.column_config.NumberColumn(
            "ID",
            disabled=True,
            width="small",
        ),
        "nombre_edificio": st.column_config.TextColumn(
            "Nombre",
            required=True,
            help="Nombre del edificio",
        ),
        "codigo_interno": st.column_config.TextColumn(
            "Código",
            required=True,
            help="Código único del edificio",
        ),
    }
    
    # Data editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="edificios_data_editor",
        num_rows="fixed"  # Prevent adding/deleting rows from editor
    )
    
    # ============================================================
    # UPDATE SECTION: Save changes button
    # ============================================================
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        save_clicked = st.button("💾 Guardar Cambios", key="save_edificios", type="primary", use_container_width=True)
    with col2:
        delete_clicked = st.button(
            "🗑️ Eliminar Seleccionados",
            key="delete_edificios",
            type="secondary",
            use_container_width=True
        )
    
    # ============================================================
    # SAVE LOGIC: Detect and persist changes
    # ============================================================
    if save_clicked:
        try:
            # Remove selection column for comparison
            original_df = df.drop(columns=["Seleccionar"])
            edited_data_df = edited_df.drop(columns=["Seleccionar"])
            
            changes_made = False
            errors = []
            
            # Compare row by row
            for idx in range(len(edited_data_df)):
                original_row = original_df.iloc[idx].to_dict()
                edited_row = edited_data_df.iloc[idx].to_dict()
                
                # If data changed, save it
                if original_row != edited_row:
                    try:
                        repo.save_edificio(
                            id=edited_row["id"],  # ⭐ CRITICAL: Pass ID for UPDATE
                            nombre_edificio=edited_row["nombre_edificio"],
                            codigo_interno=edited_row["codigo_interno"]
                        )
                        changes_made = True
                    except Exception as e:
                        errors.append(f"Fila {idx + 1}: {str(e)}")
            
            # Feedback
            if changes_made and not errors:
                st.success("✅ Cambios guardados exitosamente.")
                st.rerun()  # CRITICAL: Refresh to show updated data
            elif errors:
                st.error("❌ Se encontraron errores:")
                for error in errors:
                    st.error(error)
            else:
                st.info("ℹ️ No se detectaron cambios en los datos.")
                
        except Exception as e:
            st.error(f"❌ Error inesperado al guardar: {str(e)}")
    
    # ============================================================
    # DELETE LOGIC: Remove selected buildings
    # ============================================================
    if delete_clicked:
        # Find rows where checkbox is True
        selected_rows = edited_df[edited_df["Seleccionar"] == True]
        
        if len(selected_rows) == 0:
            st.warning("⚠️ No has seleccionado ningún edificio para eliminar.")
        else:
            # Store in session state for confirmation
            st.session_state["edificios_to_delete"] = selected_rows["id"].tolist()
            st.session_state["confirm_delete_edificios"] = True
    
    # ============================================================
    # DELETE CONFIRMATION: Two-step delete process
    # ============================================================
    if st.session_state.get("confirm_delete_edificios", False):
        ids_to_delete = st.session_state.get("edificios_to_delete", [])
        
        st.warning(f"⚠️ **¿Estás seguro de eliminar {len(ids_to_delete)} edificio(s)?**")
        st.caption("Esta acción no se puede deshacer. Los edificios con pisos asociados no se podrán eliminar.")
        
        col_yes, col_no, col_spacer = st.columns([1, 1, 3])
        
        with col_yes:
            if st.button("✅ Sí, Eliminar", key="confirm_delete_yes", type="primary", use_container_width=True):
                deleted_count = 0
                errors = []
                
                for edificio_id in ids_to_delete:
                    try:
                        repo.delete_edificio(edificio_id)
                        deleted_count += 1
                    except Exception as e:
                        errors.append(f"ID {edificio_id}: {str(e)}")
                
                # Clear confirmation state
                st.session_state["confirm_delete_edificios"] = False
                if "edificios_to_delete" in st.session_state:
                    del st.session_state["edificios_to_delete"]
                
                # Show results
                if deleted_count > 0:
                    st.success(f"✅ {deleted_count} edificio(s) eliminado(s) exitosamente.")
                
                if errors:
                    st.error("❌ Algunos edificios no pudieron eliminarse:")
                    for error in errors:
                        st.error(error)
                
                # CRITICAL: Force UI refresh to show deleted records are gone
                st.rerun()
        
        with col_no:
            if st.button("❌ Cancelar", key="confirm_delete_no", use_container_width=True):
                st.session_state["confirm_delete_edificios"] = False
                if "edificios_to_delete" in st.session_state:
                    del st.session_state["edificios_to_delete"]
                st.rerun()

# ----------------------------------------------------------------------
# Phone Directory (Directorio Telefónico) Tab - Refactored Pattern
# ----------------------------------------------------------------------
def render_directorio_tab():
    """
    REFACTORED IMPLEMENTATION: Phone Directory CRUD with Grid + New/Edit Form pattern.
    
    Follows the same standardized pattern as render_edificios_tab() for consistency.
    """
    repo = _load_repo()
    
    st.subheader("📒 Gestión de Directorio Telefónico")
    st.info("📝 **Instrucciones:** Edita los valores directamente en la tabla. Marca las casillas para seleccionar y eliminar contactos.")
    
    # ============================================================
    # CREATE SECTION: Form for adding new contacts
    # ============================================================
    with st.expander("➕ Crear Nuevo Contacto"):
        with st.form("form_create_contacto_directorio", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre_referencia = st.text_input(
                    "Nombre/Referencia *", 
                    max_chars=100,
                    placeholder="Ej: Dr. Juan Pérez / Urgencias"
                )
            
            with col2:
                numero_anexo = st.number_input(
                    "Número de Anexo *", 
                    min_value=1000, 
                    max_value=999999,
                    value=1000,
                    step=1,
                    help="Extensión telefónica (mínimo 1000)"
                )
            
            submitted = st.form_submit_button("💾 Crear Contacto", type="primary", use_container_width=True)
            
            if submitted:
                if not nombre_referencia:
                    st.error("❌ El nombre/referencia es obligatorio.")
                else:
                    try:
                        repo.save_contacto(
                            id=None,  # ⭐ No ID = INSERT
                            nombre_referencia=nombre_referencia,
                            numero_anexo=int(numero_anexo)
                        )
                        st.success(f"✅ Contacto '{nombre_referencia}' (Anexo: {numero_anexo}) creado exitosamente.")
                        st.rerun()  # CRITICAL: Force refresh to show new record
                    except Exception as e:
                        st.error(f"❌ {str(e)}")
    
    st.divider()
    
    # ============================================================
    # READ SECTION: Load and display existing contacts
    # ============================================================
    contactos = repo.get_directorio()
    
    if not contactos or len(contactos) == 0:
        st.warning("⚠️ No hay contactos registrados. Crea uno usando el formulario de arriba.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(contactos)
    
    # Add selection column (checkbox) as the first column
    df.insert(0, "Seleccionar", False)
    
    # Column configuration
    column_config = {
        "Seleccionar": st.column_config.CheckboxColumn(
            "Seleccionar",
            help="Marca para eliminar este contacto",
            default=False,
        ),
        "id": st.column_config.NumberColumn(
            "ID",
            disabled=True,
            width="small",
        ),
        "numero_anexo": st.column_config.NumberColumn(
            "Anexo",
            required=True,
            help="Extensión telefónica (mínimo 1000)",
            min_value=1000,
            max_value=999999,
            step=1,
        ),
        "nombre_referencia": st.column_config.TextColumn(
            "Nombre/Referencia",
            required=True,
            max_chars=100,
            help="Nombre de la persona o unidad",
        ),
    }
    
    # Data editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="directorio_data_editor",
        num_rows="fixed"  # Prevent adding/deleting rows from editor
    )
    
    # ============================================================
    # UPDATE SECTION: Save changes button
    # ============================================================
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        save_clicked = st.button("💾 Guardar Cambios", key="save_directorio", type="primary", use_container_width=True)
    with col2:
        delete_clicked = st.button(
            "🗑️ Eliminar Seleccionados",
            key="delete_directorio",
            type="secondary",
            use_container_width=True
        )
    
    # ============================================================
    # SAVE LOGIC: Detect and persist changes
    # ============================================================
    if save_clicked:
        try:
            # Remove selection column for comparison
            original_df = df.drop(columns=["Seleccionar"])
            edited_data_df = edited_df.drop(columns=["Seleccionar"])
            
            changes_made = False
            errors = []
            
            # Compare row by row
            for idx in range(len(edited_data_df)):
                original_row = original_df.iloc[idx].to_dict()
                edited_row = edited_data_df.iloc[idx].to_dict()
                
                # If data changed, save it
                if original_row != edited_row:
                    # Validate nombre_referencia
                    if not edited_row["nombre_referencia"] or edited_row["nombre_referencia"].strip() == "":
                        errors.append(f"Fila {idx + 1}: El nombre/referencia no puede estar vacío.")
                        continue
                    
                    try:
                        repo.save_contacto(
                            id=edited_row["id"],  # ⭐ CRITICAL: Pass ID for UPDATE
                            nombre_referencia=edited_row["nombre_referencia"],
                            numero_anexo=int(edited_row["numero_anexo"])
                        )
                        changes_made = True
                    except Exception as e:
                        errors.append(f"Fila {idx + 1}: {str(e)}")
            
            # Feedback
            if changes_made and not errors:
                st.success("✅ Cambios guardados exitosamente.")
                st.rerun()  # CRITICAL: Refresh to show updated data
            elif errors:
                st.error("❌ Se encontraron errores:")
                for error in errors:
                    st.error(error)
            else:
                st.info("ℹ️ No se detectaron cambios en los datos.")
                
        except Exception as e:
            st.error(f"❌ Error inesperado al guardar: {str(e)}")
    
    # ============================================================
    # DELETE LOGIC: Remove selected contacts
    # ============================================================
    if delete_clicked:
        # Find rows where checkbox is True
        selected_rows = edited_df[edited_df["Seleccionar"] == True]
        
        if len(selected_rows) == 0:
            st.warning("⚠️ No has seleccionado ningún contacto para eliminar.")
        else:
            # Store in session state for confirmation
            st.session_state["directorio_to_delete"] = selected_rows["id"].tolist()
            st.session_state["confirm_delete_directorio"] = True
    
    # ============================================================
    # DELETE CONFIRMATION: Two-step delete process
    # ============================================================
    if st.session_state.get("confirm_delete_directorio", False):
        ids_to_delete = st.session_state.get("directorio_to_delete", [])
        
        st.warning(f"⚠️ **¿Estás seguro de eliminar {len(ids_to_delete)} contacto(s)?**")
        st.caption("Esta acción no se puede deshacer.")
        
        col_yes, col_no, col_spacer = st.columns([1, 1, 3])
        
        with col_yes:
            if st.button("✅ Sí, Eliminar", key="confirm_delete_directorio_yes", type="primary", use_container_width=True):
                deleted_count = 0
                errors = []
                
                for contacto_id in ids_to_delete:
                    try:
                        repo.delete_contacto(contacto_id)
                        deleted_count += 1
                    except Exception as e:
                        errors.append(f"ID {contacto_id}: {str(e)}")
                
                # Clear confirmation state
                st.session_state["confirm_delete_directorio"] = False
                if "directorio_to_delete" in st.session_state:
                    del st.session_state["directorio_to_delete"]
                
                # Show results
                if deleted_count > 0:
                    st.success(f"✅ {deleted_count} contacto(s) eliminado(s) exitosamente.")
                
                if errors:
                    st.error("❌ Algunos contactos no pudieron eliminarse:")
                    for error in errors:
                        st.error(error)
                
                # CRITICAL: Force UI refresh to show deleted records are gone
                st.rerun()
        
        with col_no:
            if st.button("❌ Cancelar", key="confirm_delete_directorio_no", use_container_width=True):
                st.session_state["confirm_delete_directorio"] = False
                if "directorio_to_delete" in st.session_state:
                    del st.session_state["directorio_to_delete"]
                st.rerun()

# ----------------------------------------------------------------------
# Hospital Units (Unidades Hospitalarias) Tab - Refactored Pattern
# ----------------------------------------------------------------------
def render_unidades_tab():
    """
    REFACTORED IMPLEMENTATION: Hospital Units CRUD with Grid + New/Edit Form pattern.
    
    Features smart cascading dropdown: Building → Floor → Unit hierarchy.
    """
    repo = _load_repo()
    
    st.subheader("🏥 Gestión de Unidades Hospitalarias")
    st.info("📝 **Instrucciones:** Edita los valores directamente en la tabla. Marca las casillas para seleccionar y eliminar unidades.")
    
    # ============================================================
    # CREATE SECTION: Form for adding new units
    # ============================================================
    with st.expander("➕ Crear Nueva Unidad"):
        with st.form("form_create_unidad_hospitalaria", clear_on_submit=True):
            # Smart Cascading Dropdown for Floor Selection
            st.markdown("**Ubicación (Edificio y Piso) ***")
            pisos = repo.get_pisos()
            
            if not pisos:
                st.warning("⚠️ No hay pisos registrados. Debes crear edificios y pisos primero.")
            else:
                # Format dropdown options: "Edificio A - Nivel 2 (Piso 1)"
                piso_options = {}
                for p in pisos:
                    display_text = f"{p['nombre_edificio']} - Nivel {p['nivel_numero']} ({p['nombre_piso']})"
                    piso_options[display_text] = p['id']
                
                piso_sel = st.selectbox(
                    "Selecciona el piso donde se ubicará la unidad",
                    options=list(piso_options.keys()),
                    help="Formato: Edificio - Nivel (Nombre del Piso)"
                )
                
                # Unit details
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre_unidad = st.text_input(
                        "Nombre de la Unidad *", 
                        max_chars=100,
                        placeholder="Ej: Urgencias / Pediatría"
                    )
                
                with col2:
                    tipo_servicio = st.text_input(
                        "Tipo de Servicio",
                        max_chars=50,
                        placeholder="Ej: Clínico / Apoyo / Admin"
                    )
                
                submitted = st.form_submit_button("💾 Crear Unidad", type="primary", use_container_width=True)
                
                if submitted:
                    if not nombre_unidad:
                        st.error("❌ El nombre de la unidad es obligatorio.")
                    else:
                        try:
                            repo.save_unidad(
                                id=None,  # ⭐ No ID = INSERT
                                nombre_unidad=nombre_unidad,
                                tipo_servicio=tipo_servicio if tipo_servicio else None,
                                piso_id=piso_options[piso_sel]
                            )
                            st.success(f"✅ Unidad '{nombre_unidad}' creada exitosamente en {piso_sel}.")
                            st.rerun()  # CRITICAL: Force refresh to show new record
                        except Exception as e:
                            st.error(f"❌ {str(e)}")
    
    st.divider()
    
    # ============================================================
    # READ SECTION: Load and display existing units
    # ============================================================
    unidades = repo.get_unidades()
    
    if not unidades or len(unidades) == 0:
        st.warning("⚠️ No hay unidades registradas. Crea una usando el formulario de arriba.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(unidades)
    
    # Add selection column (checkbox) as the first column
    df.insert(0, "Seleccionar", False)
    
    # Column configuration
    column_config = {
        "Seleccionar": st.column_config.CheckboxColumn(
            "Seleccionar",
            help="Marca para eliminar esta unidad",
            default=False,
        ),
        "id": st.column_config.NumberColumn(
            "ID",
            disabled=True,
            width="small",
        ),
        "nombre_unidad": st.column_config.TextColumn(
            "Nombre Unidad",
            required=True,
            max_chars=100,
            help="Nombre de la unidad hospitalaria",
        ),
        "tipo_servicio": st.column_config.TextColumn(
            "Tipo Servicio",
            max_chars=50,
            help="Tipo de servicio que presta la unidad",
        ),
        "nombre_edificio": st.column_config.TextColumn(
            "Edificio",
            disabled=True,
            help="Edificio donde se ubica (solo lectura)",
        ),
        "nivel_numero": st.column_config.NumberColumn(
            "Nivel",
            disabled=True,
            width="small",
            help="Nivel del piso (solo lectura)",
        ),
        "piso_id": st.column_config.NumberColumn(
            "ID Piso",
            disabled=True,
            width="small",
            help="ID del piso (necesario para guardar cambios)",
        ),
        "edificio_id": None,  # Hide this column completely
    }
    
    # Data editor
    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="unidades_data_editor",
        num_rows="fixed",  # Prevent adding/deleting rows from editor
        disabled=["id", "nombre_edificio", "nivel_numero", "piso_id", "edificio_id"]
    )
    
    # ============================================================
    # UPDATE SECTION: Save changes button
    # ============================================================
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        save_clicked = st.button("💾 Guardar Cambios", key="save_unidades", type="primary", use_container_width=True)
    with col2:
        delete_clicked = st.button(
            "🗑️ Eliminar Seleccionados",
            key="delete_unidades",
            type="secondary",
            use_container_width=True
        )
    
    # ============================================================
    # SAVE LOGIC: Detect and persist changes
    # ============================================================
    if save_clicked:
        try:
            # Remove selection column for comparison
            original_df = df.drop(columns=["Seleccionar"])
            edited_data_df = edited_df.drop(columns=["Seleccionar"])
            
            changes_made = False
            errors = []
            
            # Compare row by row
            for idx in range(len(edited_data_df)):
                original_row = original_df.iloc[idx].to_dict()
                edited_row = edited_data_df.iloc[idx].to_dict()
                
                # If data changed, save it
                if original_row != edited_row:
                    # Validate nombre_unidad
                    if not edited_row["nombre_unidad"] or edited_row["nombre_unidad"].strip() == "":
                        errors.append(f"Fila {idx + 1}: El nombre de la unidad no puede estar vacío.")
                        continue
                    
                    try:
                        repo.save_unidad(
                            id=edited_row["id"],  # ⭐ CRITICAL: Pass ID for UPDATE
                            nombre_unidad=edited_row["nombre_unidad"],
                            tipo_servicio=edited_row.get("tipo_servicio"),
                            piso_id=edited_row["piso_id"]
                        )
                        changes_made = True
                    except Exception as e:
                        errors.append(f"Fila {idx + 1}: {str(e)}")
            
            # Feedback
            if changes_made and not errors:
                st.success("✅ Cambios guardados exitosamente.")
                st.rerun()  # CRITICAL: Refresh to show updated data
            elif errors:
                st.error("❌ Se encontraron errores:")
                for error in errors:
                    st.error(error)
            else:
                st.info("ℹ️ No se detectaron cambios en los datos.")
                
        except Exception as e:
            st.error(f"❌ Error inesperado al guardar: {str(e)}")
    
    # ============================================================
    # DELETE LOGIC: Remove selected units
    # ============================================================
    if delete_clicked:
        # Find rows where checkbox is True
        selected_rows = edited_df[edited_df["Seleccionar"] == True]
        
        if len(selected_rows) == 0:
            st.warning("⚠️ No has seleccionado ninguna unidad para eliminar.")
        else:
            # Store in session state for confirmation
            st.session_state["unidades_to_delete"] = selected_rows["id"].tolist()
            st.session_state["confirm_delete_unidades"] = True
    
    # ============================================================
    # DELETE CONFIRMATION: Two-step delete process
    # ============================================================
    if st.session_state.get("confirm_delete_unidades", False):
        ids_to_delete = st.session_state.get("unidades_to_delete", [])
        
        st.warning(f"⚠️ **¿Estás seguro de eliminar {len(ids_to_delete)} unidad(es)?**")
        st.caption("Esta acción no se puede deshacer.")
        
        col_yes, col_no, col_spacer = st.columns([1, 1, 3])
        
        with col_yes:
            if st.button("✅ Sí, Eliminar", key="confirm_delete_unidades_yes", type="primary", use_container_width=True):
                deleted_count = 0
                errors = []
                
                for unidad_id in ids_to_delete:
                    try:
                        repo.delete_unidad(unidad_id)
                        deleted_count += 1
                    except Exception as e:
                        errors.append(f"ID {unidad_id}: {str(e)}")
                
                # Clear confirmation state
                st.session_state["confirm_delete_unidades"] = False
                if "unidades_to_delete" in st.session_state:
                    del st.session_state["unidades_to_delete"]
                
                # Show results
                if deleted_count > 0:
                    st.success(f"✅ {deleted_count} unidad(es) eliminada(s) exitosamente.")
                
                if errors:
                    st.error("❌ Algunas unidades no pudieron eliminarse:")
                    for error in errors:
                        st.error(error)
                
                # CRITICAL: Force UI refresh to show deleted records are gone
                st.rerun()
        
        with col_no:
            if st.button("❌ Cancelar", key="confirm_delete_unidades_no", use_container_width=True):
                st.session_state["confirm_delete_unidades"] = False
                if "unidades_to_delete" in st.session_state:
                    del st.session_state["unidades_to_delete"]
                st.rerun()

# ----------------------------------------------------------------------
# Generic CRUD Interface (Keep for other tabs - will be refactored later)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# Create Forms (Abbreviated - only showing what's needed)
# ----------------------------------------------------------------------
def create_user_form(tab_key: str):
    """Formulario para crear nuevo usuario."""
    repo = _load_repo()
    
    with st.form(f"form_create_user_{tab_key}"):
        col1, col2 = st.columns(2)
        
        with col1:
            rut = st.text_input("RUT *", placeholder="12.345.678-9")
            nombre = st.text_input("Nombre Completo *")
        
        with col2:
            email = st.text_input("Email *", placeholder="usuario@hospital.cl")
            password = st.text_input("Contraseña *", type="password")
        
        roles = repo.get_roles()
        role_options = {r["nombre_rol"]: r["id"] for r in roles}
        rol_sel = st.selectbox("Rol *", options=list(role_options.keys())) if role_options else None
        
        submitted = st.form_submit_button("Crear Usuario", type="primary")
        
        if submitted:
            if not all([rut, nombre, email, password, rol_sel]):
                st.error("❌ Todos los campos son obligatorios.")
            else:
                try:
                    repo.save_user(
                        rut=rut,
                        nombre_completo=nombre,
                        email=email,
                        password=password,
                        rol_id=role_options[rol_sel]
                    )
                    st.success(f"✅ Usuario '{nombre}' creado exitosamente.")
                    st.session_state[f"show_create_form_{tab_key}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

def create_role_form(tab_key: str):
    """Formulario para crear nuevo rol."""
    repo = _load_repo()
    
    with st.form(f"form_create_role_{tab_key}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_rol = st.text_input("Nombre del Rol *", placeholder="ENFERMERO")
        
        with col2:
            descripcion = st.text_area("Descripción", placeholder="Descripción del rol (opcional)", height=100)
        
        submitted = st.form_submit_button("Crear Rol", type="primary")
        
        if submitted:
            if not nombre_rol:
                st.error("❌ El nombre del rol es obligatorio.")
            else:
                try:
                    repo.save_role(
                        id=None,  # ⭐ No ID = INSERT
                        nombre_rol=nombre_rol,
                        descripcion=descripcion
                    )
                    st.success(f"✅ Rol '{nombre_rol}' creado exitosamente.")
                    st.session_state[f"show_create_form_{tab_key}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

def create_piso_form(tab_key: str):
    """Formulario para crear nuevo piso."""
    repo = _load_repo()
    
    with st.form(f"form_create_piso_{tab_key}"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Dropdown for edificio (foreign key)
            edificios = repo.get_all_edificios()
            edificio_options = {e["nombre_edificio"]: e["id"] for e in edificios}
            edificio_sel = st.selectbox(
                "Edificio *", 
                options=list(edificio_options.keys())
            ) if edificio_options else None
            
            nivel_numero = st.number_input(
                "Nivel/Número *", 
                min_value=-10, 
                max_value=50, 
                value=1, 
                step=1,
                help="Número del piso (ej: -1 para sótano, 1 para primer piso)"
            )
        
        with col2:
            nombre_piso = st.text_input(
                "Nombre del Piso *", 
                max_chars=50,
                placeholder="Piso 1"
            )
        
        submitted = st.form_submit_button("Crear Piso", type="primary")
        
        if submitted:
            if not all([edificio_sel, nombre_piso]):
                st.error("❌ Todos los campos son obligatorios.")
            else:
                try:
                    repo.save_piso(
                        id=None,  # ⭐ No ID = INSERT
                        edificio_id=edificio_options[edificio_sel],
                        nivel_numero=nivel_numero,
                        nombre_piso=nombre_piso
                    )
                    st.success(f"✅ Piso '{nombre_piso}' creado exitosamente.")
                    st.session_state[f"show_create_form_{tab_key}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

def create_contacto_form(tab_key: str):
    """Formulario para crear nuevo contacto en el directorio telefónico."""
    repo = _load_repo()
    
    with st.form(f"form_create_contacto_{tab_key}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nombre_referencia = st.text_input(
                "Nombre/Referencia *", 
                max_chars=100,
                placeholder="Ej: Dr. Juan Pérez / Urgencias"
            )
        
        with col2:
            numero_anexo = st.number_input(
                "Número de Anexo *", 
                min_value=1000, 
                max_value=999999,
                value=1000,
                step=1,
                help="Extensión telefónica (mínimo 1000)"
            )
        
        submitted = st.form_submit_button("💾 Crear Contacto", type="primary", use_container_width=True)
        
        if submitted:
            if not nombre_referencia:
                st.error("❌ El nombre/referencia es obligatorio.")
            else:
                try:
                    repo.save_contacto(
                        id=None,  # ⭐ No ID = INSERT
                        nombre_referencia=nombre_referencia,
                        numero_anexo=int(numero_anexo)
                    )
                    st.success(f"✅ Contacto '{nombre_referencia}' (Anexo: {numero_anexo}) creado exitosamente.")
                    st.session_state[f"show_create_form_{tab_key}"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

# ... (other create forms omitted for brevity - keep existing ones)

def render_crud_interface(
    title: str,
    data: List[Dict[str, Any]],
    primary_key: str,
    save_callback: Callable,
    delete_callback: Callable,
    create_form_callback: Optional[Callable] = None,
    column_config: Optional[Dict] = None,
    hidden_columns: Optional[List[str]] = None,
    read_only_columns: Optional[List[str]] = None,
    tab_key: str = "crud"
):
    """Generic CRUD interface for tabs.
    Parameters:
        title: Section title.
        data: List of records.
        primary_key: Field name of the primary key.
        save_callback: Function to call for saving a row (receives dict).
        delete_callback: Function to call for deleting a row by id.
        create_form_callback: Optional function to render a creation form.
        column_config: Optional Streamlit column config dict.
        hidden_columns: Columns to hide from the editor.
        read_only_columns: Columns that should be read‑only.
        tab_key: Unique key for Streamlit widgets.
    """
    st.subheader(title)
    st.info("📝 **Instrucciones:** Edita los valores directamente en la tabla. Marca las casillas para seleccionar filas y borrarlas.")

    if create_form_callback:
        if st.button(f"➕ Nuevo Registro", key=f"new_{tab_key}", type="primary"):
            st.session_state[f"show_create_form_{tab_key}"] = True
        if st.session_state.get(f"show_create_form_{tab_key}", False):
            with st.expander("📝 Crear Nuevo Registro", expanded=True):
                create_form_callback(tab_key)

    st.divider()

    if not data:
        st.warning("No hay registros para mostrar.")
        return

    df = pd.DataFrame(data)
    df.insert(0, "Seleccionar", False)

    if not column_config:
        column_config = {}

    # Checkbox column for selection
    column_config["Seleccionar"] = st.column_config.CheckboxColumn(
        "Seleccionar",
        help="Marca para borrar",
        default=False,
    )

    if read_only_columns:
        for col in read_only_columns:
            if col in df.columns:
                column_config[col] = st.column_config.TextColumn(col, disabled=True)

    if primary_key not in column_config:
        column_config[primary_key] = st.column_config.TextColumn(primary_key, disabled=True)

    if hidden_columns:
        for col in hidden_columns:
            if col in df.columns:
                column_config[col] = st.column_config.TextColumn(col, disabled=True, width="small")

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=f"data_editor_{tab_key}",
        num_rows="fixed",
    )

    col_save, col_del, _ = st.columns([1, 1, 3])
    with col_save:
        save_clicked = st.button("💾 Guardar Cambios", key=f"save_{tab_key}", type="primary", use_container_width=True)
    with col_del:
        delete_clicked = st.button("🗑️ Borrar Seleccionados", key=f"delete_{tab_key}", type="secondary", use_container_width=True)

    if save_clicked:
        try:
            original_df = df.drop(columns=["Seleccionar"])
            edited_data_df = edited_df.drop(columns=["Seleccionar"])
            changes_made = False
            errors = []
            for idx in range(len(edited_data_df)):
                original_row = original_df.iloc[idx].to_dict()
                edited_row = edited_data_df.iloc[idx].to_dict()
                if original_row != edited_row:
                    try:
                        save_callback(edited_row)
                        changes_made = True
                    except Exception as e:
                        errors.append(f"Fila {idx + 1}: {str(e)}")
            if changes_made and not errors:
                st.success("✅ Cambios guardados exitosamente.")
                st.rerun()
            elif errors:
                st.error("❌ Errores al guardar:")
                for err in errors:
                    st.error(err)
            else:
                st.info("ℹ️ No se detectaron cambios.")
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")

    if delete_clicked:
        selected_rows = edited_df[edited_df["Seleccionar"] == True]
        if len(selected_rows) == 0:
            st.warning("⚠️ No has seleccionado ninguna fila para borrar.")
        else:
            st.session_state[f"confirm_delete_{tab_key}"] = True
            st.session_state[f"rows_to_delete_{tab_key}"] = selected_rows[primary_key].tolist()

    if st.session_state.get(f"confirm_delete_{tab_key}", False):
        st.warning(f"⚠️ **¿Confirmas eliminar {len(st.session_state[f'rows_to_delete_{tab_key}'])} registro(s)?**")
        col_yes, col_no, _ = st.columns([1, 1, 3])
        with col_yes:
            if st.button("✅ Sí, Borrar", key=f"confirm_yes_{tab_key}", type="primary"):
                try:
                    deleted_count = 0
                    errors = []
                    for record_id in st.session_state[f"rows_to_delete_{tab_key}"]:
                        try:
                            delete_callback(record_id)
                            deleted_count += 1
                        except Exception as e:
                            errors.append(f"ID {record_id}: {str(e)}")
                    st.session_state[f"confirm_delete_{tab_key}"] = False
                    del st.session_state[f"rows_to_delete_{tab_key}"]
                    if deleted_count > 0 and not errors:
                        st.success(f"✅ {deleted_count} registro(s) eliminado(s) exitosamente.")
                        st.rerun()
                    elif errors:
                        st.error("❌ Errores al eliminar:")
                        for err in errors:
                            st.error(err)
                except Exception as e:
                    st.error(f"❌ Error al eliminar: {str(e)}")
        with col_no:
            if st.button("❌ Cancelar", key=f"confirm_no_{tab_key}"):
                st.session_state[f"confirm_delete_{tab_key}"] = False
                if f"rows_to_delete_{tab_key}" in st.session_state:
                    del st.session_state[f"rows_to_delete_{tab_key}"]
                st.rerun()


# ----------------------------------------------------------------------
# Main Admin Dashboard
# ----------------------------------------------------------------------
def render_admin_dashboard(user):
    """
    Renderiza el panel de super-administrador.
    
    NOTA: El tab de Edificios usa el nuevo patrón "golden sample".
    Los demás tabs seguirán usando render_crud_interface hasta que los migremos.
    """
    repo = _load_repo()
    
    st.title("⚙️ Panel de Super-Administrador")
    
    tabs = st.tabs([
        "📊 Auditoría",
        "👥 Usuarios",
        "🛡️ Roles",
        "🏢 Edificios",
        "🛗 Pisos",
        "🏥 Unidades",
        "📒 Directorio",
    ])
    
    # ----------------------------------------------------------------------
    # 1️⃣ Auditoría
    # ----------------------------------------------------------------------
    with tabs[0]:
        st.subheader("📊 Historial de Consultas")
        logs = repo.get_logs()
        if logs:
            st.dataframe(logs, hide_index=True, use_container_width=True)
        else:
            st.info("No hay registros de auditoría todavía.")
    
    # ----------------------------------------------------------------------
    # 2️⃣ Usuarios (usando render_crud_interface por ahora)
    # ----------------------------------------------------------------------
    with tabs[1]:
        users = repo.get_users()
        
        render_crud_interface(
            title="👥 Gestión de Usuarios",
            data=users,
            primary_key="id",
            save_callback=lambda row: repo.save_user(
                rut=row["rut"],
                nombre_completo=row["nombre_completo"],
                email=row["email"],
                password=None,
                rol_id=row["rol_id"]
            ),
            delete_callback=lambda user_id: repo.delete_user(user_id),
            create_form_callback=create_user_form,
            column_config={
                "id": st.column_config.TextColumn("ID", disabled=True, width="small"),
                "rut": st.column_config.TextColumn("RUT", required=True),
                "nombre_completo": st.column_config.TextColumn("Nombre Completo", required=True),
                "email": st.column_config.TextColumn("Email", required=True),
                "rol_id": st.column_config.NumberColumn("ID Rol", help="1=ADMIN, 2=USER"),
                "nombre_rol": st.column_config.TextColumn("Rol", disabled=True),
            },
            hidden_columns=["password_hash", "descripcion"],
            read_only_columns=["id", "nombre_rol"],
            tab_key="usuarios"
        )
    
    # ----------------------------------------------------------------------
    # 3️⃣ Roles (usando render_crud_interface con create_role_form)
    # ----------------------------------------------------------------------
    with tabs[2]:
        roles = repo.get_roles()
        
        render_crud_interface(
            title="🛡️ Gestión de Roles",
            data=roles,
            primary_key="id",
            save_callback=lambda row: repo.save_role(
                id=row.get("id"),  # ⭐ Pass ID
                nombre_rol=row["nombre_rol"],
                descripcion=row.get("descripcion", "")
            ),
            delete_callback=lambda role_id: repo.delete_role(role_id) if hasattr(repo, 'delete_role') else None,
            create_form_callback=create_role_form,  # ⭐ ENABLED: Form for creating new roles
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "nombre_rol": st.column_config.TextColumn("Nombre del Rol", required=True),
                "descripcion": st.column_config.TextColumn("Descripción"),
            },
            read_only_columns=["id"],
            tab_key="roles"
        )
    
    # ----------------------------------------------------------------------
    # 4️⃣ Edificios - GOLDEN SAMPLE IMPLEMENTATION ⭐
    # ----------------------------------------------------------------------
    with tabs[3]:
        render_edificios_tab()  # ⭐ USING NEW PATTERN
    
    # ----------------------------------------------------------------------
    # 5️⃣ Pisos (usando render_crud_interface con create_piso_form)
    # ----------------------------------------------------------------------
    with tabs[4]:
        pisos = repo.get_pisos()
        
        render_crud_interface(
            title="🛗 Gestión de Pisos",
            data=pisos,
            primary_key="id",
            save_callback=lambda row: repo.save_piso(
                id=row.get("id"),  # ⭐ Pass ID
                nombre_piso=row["nombre_piso"],
                nivel_numero=row["nivel_numero"],
                edificio_id=row["edificio_id"]
            ),
            delete_callback=lambda piso_id: repo.delete_piso(piso_id) if hasattr(repo, 'delete_piso') else None,
            create_form_callback=create_piso_form,  # ⭐ ENABLED: Form for creating new pisos
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "nombre_piso": st.column_config.TextColumn("Nombre Piso", required=True),
                "nivel_numero": st.column_config.NumberColumn("Nivel", required=True),
                "edificio_id": st.column_config.NumberColumn("ID Edificio", disabled=True),
                "nombre_edificio": st.column_config.TextColumn("Edificio", disabled=True),
            },
            read_only_columns=["id", "edificio_id", "nombre_edificio"],
            tab_key="pisos"
        )
    
    # ----------------------------------------------------------------------
    # 6️⃣ Unidades - REFACTORED IMPLEMENTATION ⭐
    # ----------------------------------------------------------------------
    with tabs[5]:
        render_unidades_tab()  # ⭐ USING NEW PATTERN WITH CASCADING DROPDOWN
    
    # ----------------------------------------------------------------------
    # 7️⃣ Directorio Telefónico - REFACTORED IMPLEMENTATION ⭐
    # ----------------------------------------------------------------------
    with tabs[6]:
        render_directorio_tab()  # ⭐ USING NEW PATTERN