from sqlalchemy import text
from src.infrastructure.database import engine
from src.infrastructure.security import hash_password

def seed_default_user():
    print("🌱 Creando usuario de prueba...")
    
    password = "nexa123"
    hashed = hash_password(password)
    
    with engine.connect() as conn:
        # Primero nos aseguramos de que existan los roles
        conn.execute(text("INSERT INTO roles (nombre_rol, descripcion) VALUES ('ADMIN', 'Administrador') ON CONFLICT DO NOTHING"))
        conn.commit()
        
        # Obtenemos el ID del rol ADMIN
        result = conn.execute(text("SELECT id FROM roles WHERE nombre_rol = 'ADMIN'"))
        rol_id = result.scalar()
        
        # Insertamos el usuario
        sql_user = """
        INSERT INTO usuarios (rut, nombre_completo, email, password_hash, rol_id, activo)
        VALUES ('11.111.111-1', 'Admin Nexa', 'admin@nexa.ai', :password_hash, :rol_id, true)
        ON CONFLICT (email) DO UPDATE SET password_hash = :password_hash
        """
        conn.execute(text(sql_user), {"password_hash": hashed, "rol_id": rol_id})
        conn.commit()
        print(f"✅ Usuario creado: admin@nexa.ai / {password}")

if __name__ == "__main__":
    seed_default_user()
