-- ==================================================================================
-- PROYECTO NEXA - Refinamiento RAG
-- Script de Creación de Vistas para Awareness Espacial
-- ==================================================================================

-- TAREA 1: CREACIÓN DE VISTA ESPACIAL
-- Esta vista une Unidades -> Pisos -> Edificios para facilitar consultas de ubicación.

CREATE OR REPLACE VIEW vista_ubicaciones_maestra AS
SELECT 
    u.id AS unidad_id,
    u.nombre_unidad,
    u.tipo_servicio,
    p.nombre_piso,
    p.nivel_numero,
    e.nombre_edificio,
    e.codigo_interno
FROM unidades_hospitalarias u
JOIN pisos p ON u.piso_id = p.id
JOIN edificios e ON p.edificio_id = e.id;

-- Comentario: Esta vista permitirá que el agente RAG responda "¿Dónde queda X?" 
-- sin tener que adivinar los JOINS complejos en tiempo de ejecución.
