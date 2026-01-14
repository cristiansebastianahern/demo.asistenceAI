from src.infrastructure.database import engine
from sqlalchemy import text

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT count(*) FROM directorio_telefonico;"))
        count = result.scalar()
        print(f"✅ ¡Conexión Exitosa! Se encontraron {count} registros en el directorio.")
except Exception as e:
    print(f"❌ Error de conexión: {e}")