from sqlalchemy import text
from src.infrastructure.database import engine

def reparar_base_datos():
    print("🔧 Iniciando diagnóstico y reparación de NEXA DB...")
    
    with engine.connect() as conn:
        # 1. Instalar extensión para ignorar tildes (Crucial en español)
        print("abc Instalando extensión 'unaccent'...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent;"))
            conn.commit()
            print("✅ Extensión unaccent activa.")
        except Exception as e:
            print(f"⚠️ No se pudo instalar unaccent (quizás falta permisos de superusuario): {e}")

        # 2. Recrear la Vista Maestra (Force)
        print("👁️ Recreando vista_ubicaciones_maestra...")
        sql_vista = """
        DROP VIEW IF EXISTS vista_ubicaciones_maestra;
        CREATE VIEW vista_ubicaciones_maestra AS
        SELECT 
            u.nombre_unidad,
            u.tipo_servicio,
            p.nombre_piso,
            p.nivel_numero,
            e.nombre_edificio,
            e.codigo_interno
        FROM unidades_hospitalarias u
        JOIN pisos p ON u.piso_id = p.id
        JOIN edificios e ON p.edificio_id = e.id;
        """
        conn.execute(text(sql_vista))
        conn.commit()
        print("✅ Vista creada exitosamente.")

        # 3. Verificar Datos
        print("🔍 Verificando datos existentes...")
        result = conn.execute(text("SELECT count(*) FROM unidades_hospitalarias"))
        count = result.scalar()
        print(f"📊 Unidades encontradas: {count}")

        if count == 0:
            print("⚠️ ¡ALERTA! No hay unidades en la base de datos.")
            print("   -> Ejecuta el script 'init_nexa_full.sql' en BeeKeeper para poblar los edificios.")
        else:
            # Prueba de lectura
            sample = conn.execute(text("SELECT * FROM vista_ubicaciones_maestra LIMIT 3")).fetchall()
            print("📝 Ejemplo de datos en la vista:")
            for row in sample:
                print(f"   - {row}")

if __name__ == "__main__":
    reparar_base_datos()