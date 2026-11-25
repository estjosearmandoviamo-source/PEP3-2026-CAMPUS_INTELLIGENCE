
import os
import sys

import pandas as pd
import streamlit as st

# Conexión: usamos el método conectar() de José (src/.../Base_Datos/Conexion_DB.py)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "CAMPUS_INTELLIGENCE", "Base_Datos"))
from Conexion_DB import conectar
from datos_demo import base_disponible, consulta_demo


@st.cache_data(ttl=30)
def modo_demostracion():
    """True si no hay base de datos y se usan datos de demostración."""
    return not base_disponible()


def consultar(sql, params=None):
    """Ejecuta un SELECT y devuelve el resultado como DataFrame."""
    if modo_demostracion():
        return consulta_demo(sql, params)
    conn = conectar()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=300)
def cargar_aulas():
    return consultar("SELECT id, aula, capacidad FROM aulas ORDER BY id")


@st.cache_data(ttl=60)
def rango_de_fechas(aula_id):
    """Primera y última fecha con datos de ese aula."""
    df = consultar(
        "SELECT MIN(hora)::date AS desde, MAX(hora)::date AS hasta "
        "FROM ocupacion_historico WHERE aula_id = %s",
        (aula_id,),
    )
    return df.loc[0, "desde"], df.loc[0, "hasta"]


@st.cache_data(ttl=60)
def cargar_ocupacion(aula_id, inicio, fin):
    """Mediciones de ocupación del aula dentro del periodo."""
    df = consultar(
        "SELECT hora, cantidad_personas, porcetaje_ocupacion, estado "
        "FROM ocupacion_historico WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora",
        (aula_id, inicio, fin),
    )
    # psycopg2 devuelve NUMERIC como Decimal; se convierte a float para poder calcular
    df["porcentaje"] = df["porcetaje_ocupacion"].astype(float)
    df["cantidad_personas"] = df["cantidad_personas"].astype(int)
    return df


@st.cache_data(ttl=60)
def cargar_eventos(aula_id, inicio, fin):
    """Los 5 últimos eventos (para la tabla de entradas y salidas recientes)."""
    return consultar(
        "SELECT hora, tipo, permanecia FROM eventos "
        "WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora DESC LIMIT 5",
        (aula_id, inicio, fin),
    )


@st.cache_data(ttl=60)
def cargar_todos_eventos(aula_id, inicio, fin):
    """Todos los eventos del periodo (no solo 5). Sirve para las probabilidades."""
    df = consultar(
        "SELECT hora, tipo, permanecia FROM eventos "
        "WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora",
        (aula_id, inicio, fin),
    )
    df["permanecia"] = pd.to_numeric(df["permanecia"], errors="coerce")
    return df
