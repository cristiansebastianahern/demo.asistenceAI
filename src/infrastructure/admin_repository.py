# src/infrastructure/admin_repository.py
import bcrypt
from sqlalchemy import text
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

    def save_user(self, rut: str, nombre_completo: str, email: str,
                  password: str | None, rol_id: int):
        hashed = _hash_password(password) if password else None
        
        with self.engine.begin() as conn:
            existing = conn.execute(
                text("SELECT id FROM usuarios WHERE email = :email"),
                {"email": email},
            ).fetchone()
            
            if existing:
                if hashed:
                    sql = """
                        UPDATE usuarios
                        SET rut = :rut, nombre_completo = :nombre,
                            password_hash = :pwd, rol_id = :rol, activo = true
                        WHERE email = :email;
                    """
                    params = {"rut": rut, "nombre": nombre_completo, "pwd": hashed, "rol": rol_id, "email": email}
                else:
                    sql = """
                        UPDATE usuarios
                        SET rut = :rut, nombre_completo = :nombre,
                            rol_id = :rol, activo = true
                        WHERE email = :email;
                    """
                    params = {"rut": rut, "nombre": nombre_completo, "rol": rol_id, "email": email}
                conn.execute(text(sql), params)
            else:
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

    def create_role(self, nombre_rol: str, descripcion: str | None = None):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO roles (nombre_rol, descripcion) VALUES (:nombre, :desc) ON CONFLICT (nombre_rol) DO NOTHING;"),
                {"nombre": nombre_rol, "desc": descripcion},
            )

    # ------------------------------------------------------------------
    # 3️⃣ Topología
    # ------------------------------------------------------------------
    def get_edificios(self):
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT * FROM edificios ORDER BY nombre_edificio;")).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def save_edificio(self, nombre_edificio: str, codigo_interno: str):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO edificios (nombre_edificio, codigo_interno) VALUES (:nombre, :codigo) ON CONFLICT (codigo_interno) DO UPDATE SET nombre_edificio = EXCLUDED.nombre_edificio;"),
                {"nombre": nombre_edificio, "codigo": codigo_interno},
            )

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

    def save_piso(self, nombre_piso: str, nivel_numero: int, edificio_id: int):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO pisos (edificio_id, nivel_numero, nombre_piso) VALUES (:ed_id, :nivel, :nombre) ON CONFLICT (edificio_id, nivel_numero) DO UPDATE SET nombre_piso = EXCLUDED.nombre_piso;"),
                {"ed_id": edificio_id, "nivel": nivel_numero, "nombre": nombre_piso},
            )

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

    def save_unidad(self, nombre_unidad: str, tipo_servicio: str, piso_id: int):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO unidades_hospitalarias (piso_id, nombre_unidad, tipo_servicio) VALUES (:piso, :nombre, :tipo) ON CONFLICT (piso_id, nombre_unidad) DO UPDATE SET tipo_servicio = EXCLUDED.tipo_servicio;"),
                {"piso": piso_id, "nombre": nombre_unidad, "tipo": tipo_servicio},
            )

    # ------------------------------------------------------------------
    # 4️⃣ Directorio
    # ------------------------------------------------------------------
    def get_directorio(self):
        with self.engine.connect() as conn:
            rows = conn.execute(text("SELECT id, numero_anexo, nombre_referencia FROM directorio_telefonico ORDER BY numero_anexo;")).fetchall()
            return [dict(row._mapping) for row in rows] # CORRECCIÓN

    def save_contacto(self, nombre_referencia: str, numero_anexo: int):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO directorio_telefonico (numero_anexo, nombre_referencia) VALUES (:anexo, :nombre) ON CONFLICT (numero_anexo) DO UPDATE SET nombre_referencia = EXCLUDED.nombre_referencia;"),
                {"anexo": numero_anexo, "nombre": nombre_referencia},
            )

    # ------------------------------------------------------------------
    # 5️⃣ Auditoría
    # ------------------------------------------------------------------
    def log_interaction(self, usuario_id: str, pregunta: str, respuesta: str):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO historial_consultas (usuario_id, pregunta, respuesta) VALUES (:uid, :preg, :resp);"),
                {"uid": usuario_id, "preg": pregunta, "resp": respuesta},
            )

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