-- ==================================================================================
-- PROYECTO NEXA - HOSPITAL CLÍNICO MAGALLANES
-- Script Maestro de Inicialización (Schema + Seed Data + Anexos)
-- ==================================================================================

-- 1. CONFIGURACIÓN INICIAL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. DEFINICIÓN DE ESQUEMA (DDL)

-- Tabla de Roles
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    nombre_rol VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rut VARCHAR(12) UNIQUE NOT NULL,
    nombre_completo VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol_id INTEGER REFERENCES roles(id),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Edificios
CREATE TABLE IF NOT EXISTS edificios (
    id SERIAL PRIMARY KEY,
    nombre_edificio VARCHAR(50) NOT NULL,
    codigo_interno VARCHAR(10) UNIQUE NOT NULL,
    descripcion TEXT
);

-- Tabla de Pisos
CREATE TABLE IF NOT EXISTS pisos (
    id SERIAL PRIMARY KEY,
    edificio_id INTEGER REFERENCES edificios(id) ON DELETE CASCADE,
    nivel_numero INTEGER NOT NULL,
    nombre_piso VARCHAR(50),
    UNIQUE(edificio_id, nivel_numero)
);

-- Tabla de Unidades Hospitalarias
CREATE TABLE IF NOT EXISTS unidades_hospitalarias (
    id SERIAL PRIMARY KEY,
    piso_id INTEGER REFERENCES pisos(id) ON DELETE CASCADE,
    nombre_unidad VARCHAR(100) NOT NULL,
    tipo_servicio VARCHAR(50),
    horario_atencion VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Directorio Telefónico (NUEVA)
CREATE TABLE IF NOT EXISTS directorio_telefonico (
    id SERIAL PRIMARY KEY,
    numero_anexo INTEGER NOT NULL,
    nombre_referencia VARCHAR(150) NOT NULL,
    unidad_id INTEGER REFERENCES unidades_hospitalarias(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX idx_directorio_nombre ON directorio_telefonico(nombre_referencia);
CREATE INDEX idx_directorio_anexo ON directorio_telefonico(numero_anexo);
CREATE INDEX idx_unidades_nombre ON unidades_hospitalarias(nombre_unidad);

-- ==================================================================================
-- 3. CARGA DE DATOS SEMILLA (DML)
-- ==================================================================================

-- A. ROLES
INSERT INTO roles (nombre_rol, descripcion) VALUES 
('ADMIN', 'Administrador del Sistema'),
('MEDICO', 'Personal Clínico'),
('PACIENTE', 'Usuario Externo')
ON CONFLICT DO NOTHING;

-- B. EDIFICIOS (Torres A, B, C, D)
INSERT INTO edificios (nombre_edificio, codigo_interno) VALUES 
('Edificio A (Alfa)', 'TORRE_A'),
('Edificio B (Beta)', 'TORRE_B'),
('Edificio C (Charlie)', 'TORRE_C'),
('Edificio D (Delta)', 'TORRE_D')
ON CONFLICT DO NOTHING;

-- C. TOPOLOGÍA (Pisos y Unidades - Resumen)
-- Insertar pisos clave para Torre B (Ejemplo crítico)
WITH ed_b AS (SELECT id FROM edificios WHERE codigo_interno = 'TORRE_B')
INSERT INTO pisos (edificio_id, nivel_numero, nombre_piso) VALUES 
((SELECT id FROM ed_b), -1, 'Zócalo'),
((SELECT id FROM ed_b), 1, 'Piso 1'),
((SELECT id FROM ed_b), 2, 'Piso 2'),
((SELECT id FROM ed_b), 3, 'Piso 3'),
((SELECT id FROM ed_b), 5, 'Piso 5')
ON CONFLICT DO NOTHING;

-- Insertar Unidades clave (Mapeo de Planos)
WITH p_zocalo AS (SELECT p.id FROM pisos p JOIN edificios e ON p.edificio_id = e.id WHERE e.codigo_interno = 'TORRE_B' AND p.nivel_numero = -1)
INSERT INTO unidades_hospitalarias (piso_id, nombre_unidad, tipo_servicio) VALUES
((SELECT id FROM p_zocalo), 'Anatomía Patológica', 'Apoyo'),
((SELECT id FROM p_zocalo), 'Auditorio', 'Admin'),
((SELECT id FROM p_zocalo), 'Cafetería', 'Servicios'),
((SELECT id FROM p_zocalo), 'Radioterapia', 'Clínico');

WITH p_uno AS (SELECT p.id FROM pisos p JOIN edificios e ON p.edificio_id = e.id WHERE e.codigo_interno = 'TORRE_B' AND p.nivel_numero = 1)
INSERT INTO unidades_hospitalarias (piso_id, nombre_unidad, tipo_servicio) VALUES
((SELECT id FROM p_uno), 'Imagenología', 'Apoyo'),
((SELECT id FROM p_uno), 'Banco de Sangre', 'Apoyo');

-- D. DIRECTORIO TELEFÓNICO (Carga Masiva desde CSV)
INSERT INTO directorio_telefonico (numero_anexo, nombre_referencia) VALUES
(611511, 'OF. ADM. CAPACITACION'),
(613000, 'CENTRAL'),
(613002, 'Director HCM'),
(613003, 'BETTY BART'),
(613004, 'Luisa Sotomayor'),
(613005, 'D. Maria Isabel Iduya.'),
(613006, 'LUIS VARGAS C.'),
(613014, 'Archivo SOME'),
(613019, 'Central Esterilizacion'),
(613020, 'URGENCIA LABORATORIO'),
(613028, 'FARMACIA CENTRAL'),
(613038, 'Pabellon Central'),
(613042, 'UCI ENFERMERA'),
(613088, 'INFORMATICA JEFATURA'),
(613089, 'INFORMATICA SOPORTE'),
(613200, 'ADMISION URGENCIA'),
(613155, 'O.I.R.S.')
-- (Nota: He incluido los más críticos aquí. Para los 500+ restantes, el agente usará el CSV o script Python si lo prefieres, pero esto inicializa lo vital para la demo).
;