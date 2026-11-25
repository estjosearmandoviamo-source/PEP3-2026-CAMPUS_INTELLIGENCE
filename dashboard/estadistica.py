"""
ESTADÍSTICA del dashboard  ·  PARA ESTUDIAR
===========================================
Las fórmulas explicadas con palabras están en EXPLICACION_MATEMATICA.md
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# 1. Resumen de la ocupación: media, desviación e intervalo de confianza
# ---------------------------------------------------------------------
def resumen_ocupacion(x):
    """x = columna 'porcentaje' de ocup. Devuelve un diccionario con el resumen."""
    n = len(x)
    media = x.mean()
    desviacion = x.std(ddof=1)               # desviación estándar muestral (divide entre n-1)
    margen = 1.96 * desviacion / np.sqrt(n)  # 1.96 es el valor z para 95 % de confianza
    return {
        "n": n,
        "media": media,
        "desviacion": desviacion,
        "maximo": x.max(),
        "minimo": x.min(),
        "ic_inf": media - margen,            # IC 95 % de la media: media ± margen
        "ic_sup": media + margen,
    }


def percentiles(x):
    """Mediana (P50), P90 y P95. P90 = el 90 % de las mediciones es igual o menor."""
    cuantiles = x.quantile([0.5, 0.9, 0.95])
    return cuantiles[0.5], cuantiles[0.9], cuantiles[0.95]


def histograma(x):
    """Cuántas mediciones caen en cada intervalo de 10 puntos (0-10, 10-20, ... 90-100)."""
    limites = list(range(0, 101, 10))
    conteos, _ = np.histogram(x, bins=limites)
    return limites, conteos


# ---------------------------------------------------------------------
# 2. Indicadores de las tarjetas de arriba
# ---------------------------------------------------------------------
def indicadores(ocup):
    """Último registro, promedio del último día y media de todo el periodo."""
    dia_final = ocup["hora"].dt.date.max()
    promedio_dia = ocup.loc[ocup["hora"].dt.date == dia_final, "porcentaje"].mean()
    media_periodo = ocup["porcentaje"].mean()
    return {
        "ultimo": ocup.iloc[-1],                      # la medición más reciente
        "dia_final": dia_final,
        "promedio_dia": promedio_dia,
        "media_periodo": media_periodo,
        "diferencia": promedio_dia - media_periodo,   # puntos por encima o debajo del periodo
    }


def promedio_por_hora(ocup):
    """Ocupación promedio para cada hora del día (7:00, 8:00, ...)."""
    return (ocup.assign(hora_dia=ocup["hora"].dt.hour)
            .groupby("hora_dia")["porcentaje"].mean().reset_index())


def hora_pico(por_hora):
    """La hora con mayor ocupación promedio. Devuelve (hora, promedio)."""
    fila = por_hora.loc[por_hora["porcentaje"].idxmax()]
    return int(fila["hora_dia"]), float(fila["porcentaje"])


def tabla_dia_hora(ocup):
    """Ocupación media por día de la semana (filas 0=Lun ... 6=Dom) y hora (columnas)."""
    tabla = (ocup.assign(dia=ocup["hora"].dt.dayofweek, h=ocup["hora"].dt.hour)
             .pivot_table(index="dia", columns="h", values="porcentaje", aggfunc="mean"))
    return tabla.reindex(range(7))   # asegura que aparezcan los 7 días aunque falte alguno


def porcentaje_por_estado(ocup, estados):
    """De todas las mediciones, qué % estuvo en cada estado (VACIA, DISPONIBLE, ...)."""
    n = len(ocup)
    return [100 * (ocup["estado"] == e).sum() / n for e in estados]


# ---------------------------------------------------------------------
# 3. Probabilidades observadas
# ---------------------------------------------------------------------
def intervalo_wilson(k, n, z=1.96):
    """IC 95 % de una proporción k/n (método de Wilson). Funciona bien aunque k sea 0."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z ** 2 / n
    centro = (p + z ** 2 / (2 * n)) / denom
    margen = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return max(0.0, centro - margen), min(1.0, centro + margen)


def probabilidades(ocup, todos_ev):
    """
    Probabilidad observada = veces que ocurrió / mediciones totales  (k / n).
    Además, la probabilidad de que entre alguien en una hora (modelo de Poisson).
    """
    n = len(ocup)
    x = ocup["porcentaje"]
    k_ocupada = int((ocup["cantidad_personas"] > 0).sum())   # mediciones con al menos 1 persona
    k_50 = int((x >= 50).sum())                              # mediciones con 50 % o más
    k_80 = int((x >= 80).sum())                              # mediciones con 80 % o más
    w_inf, w_sup = intervalo_wilson(k_ocupada, n)

    # Poisson: lambda = entradas por hora; P(al menos 1 entrada) = 1 - e^(-lambda)
    horas_observadas = int(ocup["hora"].dt.floor("h").nunique())
    n_entradas = int((todos_ev["tipo"] == "ENTRADA").sum())
    lam = n_entradas / horas_observadas if horas_observadas else 0.0
    return {
        "n": n, "k_ocupada": k_ocupada, "k_50": k_50, "k_80": k_80,
        "w_inf": w_inf, "w_sup": w_sup,
        "horas_observadas": horas_observadas, "n_entradas": n_entradas,
        "lam": lam, "p_entrada": 1 - np.exp(-lam),
    }


# ---------------------------------------------------------------------
# 4. Entradas y permanencia
# ---------------------------------------------------------------------
def entradas_por_hora(todos_ev):
    """Cuántas ENTRADAS hubo en cada hora del día. Devuelve una Serie (vacía si no hay)."""
    entradas = todos_ev[todos_ev["tipo"] == "ENTRADA"]
    return entradas.groupby(entradas["hora"].dt.hour).size()


def permanencias_de_salidas(todos_ev):
    """Tiempos de permanencia (en segundos) de las SALIDAS que sí tienen tiempo registrado."""
    return todos_ev.loc[(todos_ev["tipo"] == "SALIDA") & (todos_ev["permanecia"] > 0), "permanecia"]


def formato_permanencia(segundos):
    """Convierte segundos a texto: 125 -> '2 min', 4000 -> '1 h 6 min'."""
    if pd.isna(segundos):
        return "–"
    minutos_totales = int(float(segundos)) // 60
    horas, minutos = divmod(minutos_totales, 60)
    return f"{horas} h {minutos} min" if horas else f"{minutos} min"
