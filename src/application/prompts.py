# src/application/prompts.py
# v6.4 – ya sin placeholders numéricos
from langchain_core.prompts import PromptTemplate

# 1. SQL GENERATION (Sin cambios, ya funciona bien)
SQL_GENERATION_TEMPLATE = PromptTemplate.from_template(
"""Role: PostgreSQL expert. Return ONLY the query between <SQL> tags.

EXISTING COLUMNS:
- directorio_telefonico: nombre_referencia, numero_anexo
- vista_ubicaciones_maestra: nombre_unidad, nombre_piso, nombre_edificio

Rules:
1. PEOPLE/PHONES → directorio_telefonico
   SELECT nombre_referencia, numero_anexo
   WHERE unaccent(nombre_referencia) ILIKE unaccent('%term%')
2. PLACES → vista_ubicaciones_maestra
   SELECT nombre_unidad, nombre_piso, nombre_edificio
   WHERE unaccent(nombre_unidad) ILIKE unaccent('%term%')
3. ALWAYS LIMIT 5; ALWAYS use unaccent + ILIKE + %%; NEVER add extra columns.

Question: {question}"""
)

# 2. RESPONSE FORMATTING (EL CAMBIO QUIRÚRGICO)
# Eliminamos el "If []". Asumimos que si llega aquí, HAY datos.
RESPONSE_FORMATTING_TEMPLATE = PromptTemplate.from_template(
"""Role: Hospital Assistant (Nexa).
Task: Present the found data to the user in Spanish.

User Question: {question}
Found Data:
{result}

Instructions:
1. The 'Found Data' contains the correct answer. DO NOT say "not found".
2. Start with a polite phrase like "Encontré la siguiente información:" or "Aquí tienes los datos coincidentes:".
3. Display the 'Found Data' clearly as a list.

Answer:""")


##############################################################################
# from langchain_core.prompts import PromptTemplate

# SQL_GENERATION_TEMPLATE = PromptTemplate.from_template(
# """Role: PostgreSQL expert. Return ONLY the query between <SQL> tags.

# EXISTING COLUMNS:
# - directorio_telefonico: nombre_referencia, numero_anexo
# - vista_ubicaciones_maestra: nombre_unidad, nombre_piso, nombre_edificio

# Rules:
# 1. PEOPLE/PHONES → directorio_telefonico
#    SELECT nombre_referencia, numero_anexo
#    WHERE unaccent(nombre_referencia) ILIKE unaccent('%term%')
# 2. PLACES → vista_ubicaciones_maestra
#    SELECT nombre_unidad, nombre_piso, nombre_edificio
#    WHERE unaccent(nombre_unidad) ILIKE unaccent('%term%')
# 3. ALWAYS LIMIT 5; ALWAYS use unaccent + ILIKE + %%; NEVER add extra columns.

# Question: {question}"""
# )

# RESPONSE_FORMATTING_TEMPLATE = PromptTemplate.from_template(
# """You are Nexa. Answer in Spanish using ONLY the data below.
# Question: {question}
# Data: {result}

# If [] → "No encontré información exacta."
# Else:
# {result}

# Answer:""")