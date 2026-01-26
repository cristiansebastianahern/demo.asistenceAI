# src/infrastructure/admin_repository.py
import bcrypt
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from src.infrastructure.database import engine, DatabaseManager

def _hash_password(plain: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")

class AdminRepository:
    """
    Repositorio unificado para gestionar todas las entidades del sistema.
    CORRECCIÓN: Uso de row._mapping para compatibilidad con SQLAlchemy 2.0+
    """

    def __init__(self, db_manager: DatabaseManager | None = None):
        self.db_manager = db_manager or DatabaseManager()
        self.engine = engine

    # ------------------------------------------------------------------
    # 1️⃣ Usuarios
    # ------------------------------------------------------------------
    def get_users(self):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT u.id, u.rut, u.nombre_completo, u.email,
                           r.id AS rol_id, r.nombre_rol, r.descripcion
                    FROM usuarios u
                    LEFT JOIN roles r ON u.rol_id = r.id
                    ORDER BY u.nombre_completo;
                    """
                )
            ).fetchall()
            # CORRECCIÓN AQUÍ: ._mapping
            return [dict(row._mapping) for row in rows]

    def save_user(self, id: int | None = None, rut: str = None, nombre_completo: str = None, email: str = None,
                  password: str | None = None, rol_id: int = None):
        """Guardar o actualizar usuario con validación de duplicados y soporte para ID."""
        hashed = _hash_password(password) if password else None
        
        try:
            with self.engine.begin() as conn:
                if id is not None:
                    # UPDATE existente por ID
                    if hashed:
                        sql = """
                            UPDATE usuarios
                            SET rut = :rut, nombre_completo = :nombre, email = :email,
                                password_hash = :pwd, rol_id = :rol, activo = true
                            WHERE id = :id;
                        """
                        params = {"id": id, "rut": rut, "nombre": nombre_completo, "email": email, "pwd": hashed, "rol": rol_id}
                    else:
                        sql = """
                            UPDATE usuarios
                            SET rut = :rut, nombre_completo = :nombre, email = :email,
                                rol_id = :rol, activo = true
                            WHERE id = :id;
                        """
                        params = {"id": id, "rut": rut, "nombre": nombre_completo, "email": email, "rol": rol_id}
                    conn.execute(text(sql), params)
                else:
                    # INSERT nuevo usuario
                    if not hashed:
                        raise ValueError("La contraseña es obligatoria para usuarios nuevos.")
                    conn.execute(
                        text(
                            """
                            INSERT INTO usuarios (rut, nombre_completo, email,
                                                 password_hash, rol_id, activo)
                            VALUES (:rut, :nombre, :email, :pwd, :rol, true);
                            """
                        ),
                        {"rut": rut, "nombre": nombre_completo, "email": email, "pwd": hashed, "rol": rol_id},
                    )
        except IntegrityError as e:
            error_msg = str(e.orig).lower()
            if 'rut' in error_msg and 'unique' in error_msg:
                raise ValueError(f"❌ Error: El RUT '{rut}' ya está registrado en el sistema.")
            elif 'email' in error_msg and 'unique' in error_msg:
                raise ValueError(f"❌ Error: El email '{email}' ya está en uso.")
            else:
                raise ValueError(f"❌ Error de integridad: {str(e)}")

    def delete_user(self, user_id: str):
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM usuarios WHERE id = :uid;"), {"uid": user_id})

    # ------------------------------------------------------------------
    # 2️⃣ Roles
    # ------------------------------------------------------------------
    def get_roles(self):
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM roles ORDER BY nombre_rol;")).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def save_role(self, id: int = None, nombre_rol: str = None, descripcion: str = None):
        """Guardar o actualizar rol usando ID como clave primaria."""
        try:
            with self.engine.begin() as conn:
                if id is not None:
                    # UPDATE por ID
                    conn.execute(
                        text("UPDATE roles SET nombre_rol = :nombre, descripcion = :desc WHERE id = :id;"),
                        {"id": id, "nombre": nombre_rol, "desc": descripcion}
                    )
                else:
                    # INSERT nuevo
                    conn.execute(
                        text("INSERT INTO roles (nombre_rol, descripcion) VALUES (:nombre, :desc);"),
                        {"nombre": nombre_rol, "desc": descripcion}
                    )
        except IntegrityError as e:
            if 'nombre_rol' in str(e.orig).lower():
                raise ValueError(f"❌ Error: El rol '{nombre_rol}' ya existe.")
            raise ValueError(f"❌ Error de integridad: {str(e)}")
    
    # Alias for backward compatibility
    def create_role(self, nombre_rol: str, descripcion: str | None = None):
        """Alias para save_role (sin ID = INSERT)."""
        return self.save_role(id=None, nombre_rol=nombre_rol, descripcion=descripcion)
    
    def delete_role(self, role_id: int):
        """Eliminar un rol. Verificar que no tenga usuarios asignados."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM roles WHERE id = :rid;"), {"rid": role_id})
        except IntegrityError:
            raise ValueError("❌ No se puede eliminar: hay usuarios asignados a este rol.")

    # ------------------------------------------------------------------
    # 3️⃣ Topología
    # ------------------------------------------------------------------
    def get_edificios(self):
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM edificios ORDER BY nombre_edificio;")).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def get_all_edificios(self):
        """Obtener todos los edificios para dropdowns (sin JOIN)."""
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT id, nombre_edificio FROM edificios ORDER BY nombre_edificio;")
            ).fetchall()
            return [dict(row._mapping) for row in rows]

    def save_edificio(self, id: int = None, nombre_edificio: str = None, codigo_interno: str = None):
        """
        Guardar o actualizar edificio usando ID como clave primaria.
        
        Args:
            id: Si se proporciona, actualiza el registro existente. Si es None, crea uno nuevo.
            nombre_edificio: Nombre del edificio
            codigo_interno: Código único
        """
        try:
            with self.engine.begin() as conn:
                if id is not None:
                    # UPDATE: Usar ID como clave primaria
                    conn.execute(
                        text("UPDATE edificios SET nombre_edificio = :nombre, codigo_interno = :codigo WHERE id = :id;"),
                        {"id": id, "nombre": nombre_edificio, "codigo": codigo_interno}
                    )
                else:
                    # INSERT: Crear nuevo registro
                    conn.execute(
                        text("INSERT INTO edificios (nombre_edificio, codigo_interno) VALUES (:nombre, :codigo);"),
                        {"nombre": nombre_edificio, "codigo": codigo_interno}
                    )
        except IntegrityError as e:
            if 'codigo_interno' in str(e.orig).lower():
                raise ValueError(f"❌ Error: El código '{codigo_interno}' ya está en uso.")
            raise ValueError(f"❌ Error de integridad: {str(e)}")
    
    def delete_edificio(self, edificio_id: int):
        """
        Eliminar un edificio. Verificar que no tenga pisos asociados.
        
        NOTA: engine.begin() maneja automáticamente el commit/rollback.
        """
        try:
            with self.engine.begin() as conn:
                # This will raise IntegrityError if there are related pisos
                conn.execute(text("DELETE FROM edificios WHERE id = :eid;"), {"eid": edificio_id})
                # Commit is automatic on successful exit from context manager
        except IntegrityError:
            raise ValueError("❌ No se puede eliminar: hay pisos asociados a este edificio.")

    def get_pisos(self):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT p.id, p.nivel_numero, p.nombre_piso,
                           e.id AS edificio_id, e.nombre_edificio
                    FROM pisos p
                    JOIN edificios e ON p.edificio_id = e.id
                    ORDER BY e.nombre_edificio, p.nivel_numero;
                """)
            ).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def save_piso(self, id: int = None, nombre_piso: str = None, nivel_numero: int = None, edificio_id: int = None):
        """Guardar o actualizar piso usando ID como clave primaria."""
        try:
            with self.engine.begin() as conn:
                if id is not None:
                    # UPDATE por ID
                    conn.execute(
                        text("UPDATE pisos SET nombre_piso = :nombre, nivel_numero = :nivel, edificio_id = :ed_id WHERE id = :id;"),
                        {"id": id, "nombre": nombre_piso, "nivel": nivel_numero, "ed_id": edificio_id}
                    )
                else:
                    # INSERT nuevo
                    conn.execute(
                        text("INSERT INTO pisos (edificio_id, nivel_numero, nombre_piso) VALUES (:ed_id, :nivel, :nombre);"),
                        {"ed_id": edificio_id, "nivel": nivel_numero, "nombre": nombre_piso}
                    )
        except IntegrityError as e:
            raise ValueError(f"❌ Error: Ya existe un piso con nivel {nivel_numero} en este edificio.")
    
    def delete_piso(self, piso_id: int):
        """Eliminar un piso. Verificar que no tenga unidades asociadas."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM pisos WHERE id = :pid;"), {"pid": piso_id})
        except IntegrityError:
            raise ValueError("❌ No se puede eliminar: hay unidades hospitalarias en este piso.")

    def get_unidades(self):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT u.id, u.nombre_unidad, u.tipo_servicio,
                           p.id AS piso_id, p.nivel_numero, e.id AS edificio_id,
                           e.nombre_edificio
                    FROM unidades_hospitalarias u
                    JOIN pisos p ON u.piso_id = p.id
                    JOIN edificios e ON p.edificio_id = e.id
                    ORDER BY e.nombre_edificio, p.nivel_numero, u.nombre_unidad;
                """)
            ).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def save_unidad(self, id: int = None, nombre_unidad: str = None, tipo_servicio: str = None, piso_id: int = None):
        """Guardar o actualizar unidad usando ID como clave primaria."""
        try:
            with self.engine.begin() as conn:
                if id is not None:
                    # UPDATE por ID
                    conn.execute(
                        text("UPDATE unidades_hospitalarias SET nombre_unidad = :nombre, tipo_servicio = :tipo, piso_id = :piso WHERE id = :id;"),
                        {"id": id, "nombre": nombre_unidad, "tipo": tipo_servicio, "piso": piso_id}
                    )
                else:
                    # INSERT nuevo
                    conn.execute(
                        text("INSERT INTO unidades_hospitalarias (piso_id, nombre_unidad, tipo_servicio) VALUES (:piso, :nombre, :tipo);"),
                        {"piso": piso_id, "nombre": nombre_unidad, "tipo": tipo_servicio}
                    )
        except IntegrityError as e:
            raise ValueError(f"❌ Error: La unidad '{nombre_unidad}' ya existe en este piso.")
    
    def delete_unidad(self, unidad_id: int):
        """Eliminar una unidad hospitalaria."""
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM unidades_hospitalarias WHERE id = :uid;"), {"uid": unidad_id})

    # ------------------------------------------------------------------
    # 4️⃣ Directorio
    # ------------------------------------------------------------------
    def get_directorio(self):
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT id, numero_anexo, nombre_referencia FROM directorio_telefonico ORDER BY numero_anexo;")).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def save_contacto(self, id: int = None, nombre_referencia: str = None, numero_anexo: int = None):
        """Guardar o actualizar contacto usando ID como clave primaria."""
        try:
            with self.engine.begin() as conn:
                if id is not None:
                    # UPDATE por ID
                    conn.execute(
                        text("UPDATE directorio_telefonico SET nombre_referencia = :nombre, numero_anexo = :anexo WHERE id = :id;"),
                        {"id": id, "nombre": nombre_referencia, "anexo": numero_anexo}
                    )
                else:
                    # INSERT nuevo
                    conn.execute(
                        text("INSERT INTO directorio_telefonico (numero_anexo, nombre_referencia) VALUES (:anexo, :nombre);"),
                        {"anexo": numero_anexo, "nombre": nombre_referencia}
                    )
        except IntegrityError as e:
            if 'numero_anexo' in str(e.orig).lower():
                raise ValueError(f"❌ Error: El anexo {numero_anexo} ya está asignado.")
            raise ValueError(f"❌ Error de integridad: {str(e)}")
    
    def delete_contacto(self, contacto_id: int):
        """Eliminar un contacto del directorio telefónico."""
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM directorio_telefonico WHERE id = :cid;"), {"cid": contacto_id})

    # ------------------------------------------------------------------
    # 5️⃣ Auditoría
    # ------------------------------------------------------------------
    def log_interaction(self, usuario_id: str, pregunta: str, respuesta: str):
        """
        Registrar interacción del chatbot en historial.
        
        Args:
            usuario_id: UUID del usuario (puede ser None para invitados)
            pregunta: Pregunta del usuario (se truncará a 2000 chars)
            respuesta: Respuesta del AI (se truncará a 10000 chars)
        """
        import uuid
        from datetime import datetime
        
        try:
            # Generate new UUID for this interaction
            new_id = str(uuid.uuid4())
            
            # Truncate for safety (prevent abuse)
            safe_pregunta = (pregunta or "")[:2000]
            safe_respuesta = (respuesta or "")[:10000]
            
            # Handle None usuario_id (guest users)
            if not usuario_id:
                print("⚠️ No se guardó historial: usuario_id es None (invitado)")
                return
            
            with self.engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO historial_consultas (id, usuario_id, pregunta, respuesta, fecha)
                        VALUES (:id, :uid, :preg, :resp, :fecha);
                    """),
                    {
                        "id": new_id,
                        "uid": usuario_id,
                        "preg": safe_pregunta,
                        "resp": safe_respuesta,
                        "fecha": datetime.now()
                    },
                )
        except Exception as e:
            # No fallar el chatbot si falla el logging
            print(f"⚠️ Error al guardar historial: {e}")


    def get_logs(self, limit: int = 100):
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("""
                    SELECT h.id, h.fecha, u.nombre_completo AS usuario,
                           h.pregunta, h.respuesta
                    FROM historial_consultas h
                    LEFT JOIN usuarios u ON h.usuario_id = u.id
                    ORDER BY h.fecha DESC
                    LIMIT :lim;
                """),
                {"lim": limit},
            ).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN