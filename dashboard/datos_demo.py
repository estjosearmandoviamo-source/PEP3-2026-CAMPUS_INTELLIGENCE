"""
Modo demostración: si no hay base de datos disponible, el dashboard usa los mismos datos
simulados (AULA-SIM) generados en memoria, sin conectarse a PostgreSQL.
"""
import random
from datetime import timedelta
from functools import lru_cache

import pandas as pd

from generar_datos_simulados import DIAS, FECHA_INICIO, SEMILLA, generar_dia


def base_disponible():
    try:
        import os, sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "CAMPUS_INTELLIGENCE", "Base_Datos"))
        from Conexion_DB import conectar
        conectar().close()
        return True
    except Exception:
        return False


@lru_cache(maxsize=1)
def datos_simulados():
    rng = random.Random(SEMILLA)
    sid = 1
    ocupacion, eventos = [], []
    for d in range(DIAS):
        o, e, sid = generar_dia(rng, FECHA_INICIO + timedelta(days=d), sid)
        ocupacion += o
        eventos += e
    return pd.DataFrame(ocupacion), pd.DataFrame(eventos)


def consulta_demo(sql, params=None):
    """Responde las mismas consultas que app.py hace a la base, usando datos en memoria."""
    ocup, ev = datos_simulados()

    if "FROM aulas" in sql:
        return pd.DataFrame({"id": [2], "aula": ["AULA-SIM"], "capacidad": [30]})

    if "MIN(hora)" in sql:
        return pd.DataFrame({"desde": [ocup["hora"].min().date()],
                             "hasta": [ocup["hora"].max().date()]})

    inicio, fin = params[1], params[2]

    if "FROM ocupacion_historico" in sql:
        df = ocup[(ocup["hora"] >= inicio) & (ocup["hora"] < fin)]
        return df[["hora", "cantidad_personas", "porcetaje_ocupacion", "estado"]].reset_index(drop=True)

    if "FROM eventos" in sql:
        df = ev[(ev["hora"] >= inicio) & (ev["hora"] < fin)]
        if "LIMIT" in sql:  # los últimos eventos para la tabla
            df = df.sort_values("hora", ascending=False).head(5)
        else:               # todos los eventos del periodo (para las probabilidades)
            df = df.sort_values("hora")
        return df[["hora", "tipo", "permanecia"]].reset_index(drop=True)

    raise ValueError("Consulta no contemplada en modo demostración")
