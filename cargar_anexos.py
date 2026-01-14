import pandas as pd
from sqlalchemy import text
from src.infrastructure.database import engine

def cargar_datos():
    archivo_csv = "ANEXOS HCM.csv"
    
    print(f"📂 Leyendo archivo: {archivo_csv}...")
    try:
        # 1. Leer el CSV
        df = pd.read_csv(archivo_csv)
        
        # 2. Limpieza básica
        df = df.dropna(subset=['DISPLAY'])  # Borrar filas vacías
        df['DISPLAY'] = df['DISPLAY'].astype(str).str.strip() # Quitar espacios extra
        
        # 3. Mapear columnas del CSV a la Base de Datos
        # CSV: ANEXO, DISPLAY  ->  DB: numero_anexo, nombre_referencia
        df_final = df[['ANEXO', 'DISPLAY']].copy()
        df_final.columns = ['numero_anexo', 'nombre_referencia']
        
        print(f"🔄 Preparando {len(df_final)} registros...")

        # 4. Conectar y Cargar
        with engine.connect() as connection:
            # Opcional: Limpiar la tabla primero para evitar duplicados de pruebas anteriores
            print("🧹 Limpiando tabla antigua...")
            connection.execute(text("TRUNCATE TABLE directorio_telefonico RESTART IDENTITY;"))
            connection.commit()
            
            # Inserción masiva usando Pandas
            print("🚀 Insertando datos en PostgreSQL...")
            df_final.to_sql('directorio_telefonico', con=connection, if_exists='append', index=False)
            connection.commit()
            
        print("✅ ¡Carga Completa! Verifica en BeeKeeper Studio.")
        
    except FileNotFoundError:
        print("❌ Error: No encuentro el archivo .csv en esta carpeta.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    cargar_datos()