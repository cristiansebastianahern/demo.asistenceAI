import sqlite3
import random

# --- CONFIGURACIÓN DE DATOS SINTÉTICOS ---

NOMBRES = ["Juan", "María", "Carlos", "Ana", "Luis", "Elena", "Pedro", "Sofía", "Miguel", "Lucía", "Diego", "Valentina", "Javier", "Isabella", "Andrés", "Camila", "Fernando", "Gabriela", "Ricardo", "Paula"]
APELLIDOS = ["Pérez", "González", "Rodríguez", "López", "Martínez", "Sánchez", "Fernández", "Gómez", "Díaz", "Torres", "Ruiz", "Vargas", "Castro", "Morales", "Herrera", "Medina", "Aguilar", "Rojas", "Silva", "Mendoza"]

DIAGNOSTICOS = [
    ("Fractura de tibia", "Traumatología"),
    ("Apendicitis aguda", "Cirugía General"),
    ("Migraña severa", "Neurología"),
    ("Neumonía bacteriana", "Medicina Interna"),
    ("Gastroenteritis viral", "Urgencias"),
    ("Control post-operatorio", "Consultas Externas"),
    ("Insuficiencia cardíaca", "Cardiología"),
    ("Reacción alérgica leve", "Dermatología"),
    ("Cálculos renales", "Urología"),
    ("Esguince de tobillo grado 2", "Traumatología"),
    ("Hipertensión descontrolada", "Medicina Interna"),
    ("Observación por traumatismo craneal", "Neurología")
]

DOCTORES = ["Dr. Gregory House", "Dra. Meredith Grey", "Dr. Shaun Murphy", "Dra. Lisa Cuddy", "Dr. Stephen Strange", "Dra. Dana Scully", "Dr. John Watson", "Dra. Michaela Quinn", "Dr. Leonard McCoy", "Dra. Beverly Crusher"]

ESTADOS = ["Estable", "Observación", "Crítico", "En recuperación", "Esperando alta", "Pre-operatorio"]

AREAS_HOSPITAL = [
    (1, "Rayos X", "Piso 1, Ala Norte (Línea Azul)", 45),
    (2, "Urgencias", "Planta Baja, Entrada Principal", 20),
    (3, "Cafetería", "Piso 2, Frente a ascensores", 5),
    (4, "UCI (Cuidados Intensivos)", "Piso 3, Ala Sur (Acceso Restringido)", 0),
    (5, "Traumatología", "Piso 1, Pasillo B", 30),
    (6, "Laboratorio Clínico", "Sótano 1, Ala Este", 60),
    (7, "Farmacia", "Planta Baja, Salida Lateral", 15),
    (8, "Maternidad", "Piso 4, Ala Oeste", 0),
    (9, "Pediatría", "Piso 4, Decoración Infantil", 10),
    (10, "Oncología", "Piso 5, Ala Norte", 0),
    (11, "Cardiología", "Piso 2, Pasillo A", 40),
    (12, "Admisión Central", "Planta Baja, Hall Central", 25)
]

# --- GENERADOR DE PACIENTES ---

def generar_pacientes(n=50):
    pacientes = []
    for i in range(1, n + 1):
        nombre = f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)}"
        diag, area_tematica = random.choice(DIAGNOSTICOS)
        medico = random.choice(DOCTORES)
        estado = random.choice(ESTADOS)
        
        # Asignar ubicación lógica según estado
        if estado == "Crítico":
            ubicacion = "UCI Cama " + str(random.randint(1, 20))
        elif estado == "Esperando alta":
            ubicacion = "Habitación " + str(random.randint(300, 599))
        elif estado == "Observación":
            ubicacion = "Urgencias Box " + str(random.randint(1, 15))
        else:
            ubicacion = f"Habitación {random.randint(100, 299)} ({area_tematica})"

        pacientes.append((i, nombre, estado, ubicacion, diag, medico))
    return pacientes

# --- EJECUCIÓN ---

conn = sqlite3.connect("hospital.db")
cursor = conn.cursor()

print("🏥 Regenerando Data Center del Hospital con 50+ registros...")

# Limpiar tablas anteriores para no duplicar si corres el script varias veces
cursor.execute("DROP TABLE IF EXISTS areas")
cursor.execute("DROP TABLE IF EXISTS pacientes")

# Crear tablas
cursor.execute('''
CREATE TABLE areas (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    ubicacion TEXT,
    tiempo_espera_minutos INTEGER
)
''')

cursor.execute('''
CREATE TABLE pacientes (
    id INTEGER PRIMARY KEY,
    nombre_completo TEXT,
    estado TEXT,
    ubicacion_actual TEXT,
    diagnostico_breve TEXT,
    medico_a_cargo TEXT
)
''')

# Insertar Áreas
cursor.executemany('INSERT INTO areas VALUES (?,?,?,?)', AREAS_HOSPITAL)

# Generar e Insertar Pacientes
lista_pacientes = generar_pacientes(55) # Generamos 55 para tener de sobra
cursor.executemany('INSERT INTO pacientes VALUES (?,?,?,?,?,?)', lista_pacientes)

conn.commit()
count_pacientes = cursor.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
count_areas = cursor.execute("SELECT COUNT(*) FROM areas").fetchone()[0]
conn.close()

print(f"✅ Base de datos actualizada exitosamente.")
print(f"   - 📂 {count_areas} Áreas operativas registradas.")
print(f"   - 👤 {count_pacientes} Pacientes ingresados al sistema.")
print("   - 💾 Archivo: 'hospital.db' listo para RAG.")