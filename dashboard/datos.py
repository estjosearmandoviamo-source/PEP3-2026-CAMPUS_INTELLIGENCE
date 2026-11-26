
import os
import sys

import pandas as pd
import streamlit as st


from src.CAMPUS_INTELLIGENCE.Base_Datos.Conexion_DB import conectar

def consultar(sql, params=None):
    """Ejecuta un SELECT y devuelve el resultado como DataFrame."""
   
    conn = conectar()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def cargar_aulas():
    return consultar("SELECT id, aula, capacidad FROM aulas ORDER BY id")


def rango_de_fechas(aula_id):
    """Primera y última fecha con datos de ese aula."""
    df = consultar(
        "SELECT MIN(hora)::date AS desde, MAX(hora)::date AS hasta "
        "FROM ocupacion_historico WHERE aula_id = %s",
        (aula_id,),
    )
    return df.loc[0, "desde"], df.loc[0, "hasta"]

def cargar_ocupacion(aula_id, inicio, fin):
    """Mediciones de ocupación del aula dentro del periodo."""
    df = consultar(
        "SELECT hora, cantidad_personas, porcetaje_ocupacion, estado "
        "FROM ocupacion_historico WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora",
        (aula_id, inicio, fin),
    )
    df["porcentaje"] = df["porcetaje_ocupacion"].astype(float)
   
    return df

def cargar_eventos(aula_id, inicio, fin):
    """Los 5 últimos eventos (para la tabla de entradas y salidas recientes)."""
    return consultar(
        "SELECT hora, tipo, permanecia FROM eventos "
        "WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora DESC LIMIT 5",
        (aula_id, inicio, fin),
    )

def cargar_todos_eventos(aula_id, inicio, fin):
    """Todos los eventos del periodo (no solo 5). Sirve para las probabilidades."""
    df = consultar(
        "SELECT hora, tipo, permanecia FROM eventos "
        "WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora",
        (aula_id, inicio, fin),
    )

    return df
