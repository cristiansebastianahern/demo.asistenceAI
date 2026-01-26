import bcrypt
from sqlalchemy import text
from src.infrastructure.database import engine

def create_super_user():
    print("🔐 Iniciando creación de Superusuario (Con RUT)...")
    
    # --- DATOS DEL USUARIO ---
    EMAIL = "admin@nexa.ai"
    PASSWORD_RAW = "nexa123"
    FULL_NAME = "Administrador Nexa"
    RUT_ADMIN = "13.970.885-7"  # RUT solicitado
    
    with engine.connect() as conn:
        try:
            # 1. Gestionar ROLES (Tabla: roles -> nombre_rol)
            print("🔍 Verificando roles del sistema...")
            
            # Crear rol ADMIN (debe ser id=1)
            result = conn.execute(text("SELECT id FROM roles WHERE nombre_rol = 'ADMIN'"))
            admin_role_row = result.fetchone()
            
            if not admin_role_row:
                print("⚠️ Rol ADMIN no existe. Creándolo...")
                conn.execute(text("INSERT INTO roles (nombre_rol, descripcion) VALUES ('ADMIN', 'Acceso Total del Sistema')"))
                conn.commit()
                admin_role_row = conn.execute(text("SELECT id FROM roles WHERE nombre_rol = 'ADMIN'")).fetchone()
            
            role_id = admin_role_row[0]
            print(f"✅ Rol ADMIN asignado ID: {role_id}")
            
            # Crear rol USER (para usuarios regulares, debe ser id=2)
            result = conn.execute(text("SELECT id FROM roles WHERE nombre_rol = 'USER'"))
            user_role_row = result.fetchone()
            
            if not user_role_row:
                print("⚠️ Rol USER no existe. Creándolo...")
                conn.execute(text("INSERT INTO roles (nombre_rol, descripcion) VALUES ('USER', 'Acceso Solo a Chat e Historial Personal')"))
                conn.commit()
                print("✅ Rol USER creado exitosamente")
            else:
                print(f"✅ Rol USER ya existe con ID: {user_role_row[0]}")

            # 2. Encriptar Contraseña
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(PASSWORD_RAW.encode('utf-8'), salt).decode('utf-8')

            # 3. Crear o Actualizar Usuario (Tabla: usuarios -> rut, password_hash, rol_id)
            print(f"👤 Procesando usuario {EMAIL}...")
            
            # Verificamos si existe por email
            user_check = conn.execute(text("SELECT id FROM usuarios WHERE email = :email"), {"email": EMAIL}).fetchone()
            
            if user_check:
                print("⚠️ El usuario ya existe. Actualizando credenciales y RUT...")
                update_sql = """
                    UPDATE usuarios 
                    SET password_hash = :pwd, 
                        rut = :rut,
                        activo = true,
                        rol_id = :role
                    WHERE email = :email
                """
                conn.execute(text(update_sql), {
                    "pwd": hashed_password, 
                    "rut": RUT_ADMIN,
                    "role": role_id,
                    "email": EMAIL
                })
            else:
                print("✨ Creando nuevo registro...")
                # Insertamos usando las columnas exactas de tu captura
                insert_sql = """
                    INSERT INTO usuarios (rut, nombre_completo, email, password_hash, rol_id, activo)
                    VALUES (:rut, :name, :email, :pwd, :role, true)
                """
                conn.execute(text(insert_sql), {
                    "rut": RUT_ADMIN,
                    "name": FULL_NAME,
                    "email": EMAIL,
                    "pwd": hashed_password, 
                    "role": role_id
                })
            
            conn.commit()
            print("🎉 ¡ÉXITO TOTAL!")
            print(f"👉 RUT: {RUT_ADMIN}")
            print(f"👉 Email: {EMAIL}")
            print(f"👉 Pass: {PASSWORD_RAW}")
            
        except Exception as e:
            print(f"❌ Error creando usuario: {e}")
            conn.rollback()

if __name__ == "__main__":
    create_super_user()