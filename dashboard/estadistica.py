"""
ESTADÍSTICA del dashboard  ·  PARA ESTUDIAR
===========================================
Aquí están solo los CÁLCULOS. No dibuja nada: recibe tablas y devuelve números.
Las fórmulas explicadas con palabras están en EXPLICACION_MATEMATICA.md

Nombres que se repiten en todo el archivo:
  porcentajes ... una columna con los % de ocupación            (ej: 3.3, 6.6, 10.0 ...)
  mediciones .... la tabla de ocupación                         (columnas: hora, cantidad_personas, porcentaje, estado)
  eventos ....... la tabla de entradas y salidas                (columnas: hora, tipo, permanecia)
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# 1. Resumen de la ocupación: media, desviación e intervalo de confianza
# ---------------------------------------------------------------------
def resumen_ocupacion(porcentajes):
    """
    Calcula el resumen de la ocupación.

    Recibe:   porcentajes = la columna 'porcentaje' de la tabla de mediciones.
    Devuelve: un diccionario con n, media, desviacion, maximo, minimo, ic_inf, ic_sup.
    """
    cantidad_datos = len(porcentajes)
    media = porcentajes.mean()
    desviacion = porcentajes.std(ddof=1)                      # desviación estándar muestral (divide entre n-1)
    margen = 1.96 * desviacion / np.sqrt(cantidad_datos)      # 1.96 es el valor z para 95 % de confianza
    return {
        "n": cantidad_datos,
        "media": media,
        "desviacion": desviacion,
        "maximo": porcentajes.max(),
        "minimo": porcentajes.min(),
        "ic_inf": media - margen,                             # IC 95 % de la media: media ± margen
        "ic_sup": media + margen,
    }


def percentiles(porcentajes):
    """
    Mediana (P50), P90 y P95. P90 = el 90 % de las mediciones es igual o menor.

    Recibe:   porcentajes = la columna 'porcentaje' de la tabla de mediciones.
    Devuelve: tres números (mediana, p90, p95).
    """
    cuantiles = porcentajes.quantile([0.5, 0.9, 0.95])
    return cuantiles[0.5], cuantiles[0.9], cuantiles[0.95]


def histograma(porcentajes):
    """
    Cuenta cuántas mediciones caen en cada intervalo de 10 puntos (0-10, 10-20, ... 90-100).

    Recibe:   porcentajes = la columna 'porcentaje' de la tabla de mediciones.
    Devuelve: (limites, conteos). Los límites son 0, 10, 20 ... 100 y los conteos
              dicen cuántas mediciones hay en cada intervalo.
    """
    limites = list(range(0, 101, 10))
    conteos, _ = np.histogram(porcentajes, bins=limites)
    return limites, conteos


# ---------------------------------------------------------------------
# 2. Indicadores de las tarjetas de arriba
# ---------------------------------------------------------------------
def indicadores(mediciones):
    """
    Último registro, promedio del último día y media de todo el periodo.

    Recibe:   mediciones = la tabla de ocupación completa del periodo.
    Devuelve: un diccionario con ultimo, dia_final, promedio_dia, media_periodo y diferencia.
    """
    dia_final = mediciones["hora"].dt.date.max()
    promedio_dia = mediciones.loc[mediciones["hora"].dt.date == dia_final, "porcentaje"].mean()
    media_periodo = mediciones["porcentaje"].mean()
    return {
        "ultimo": mediciones.iloc[-1],                # la medición más reciente
        "dia_final": dia_final,
        "promedio_dia": promedio_dia,
        "media_periodo": media_periodo,
        "diferencia": promedio_dia - media_periodo,   # puntos por encima o debajo del periodo
    }


def promedio_por_hora(mediciones):
    """
    Ocupación promedio para cada hora del día (7:00, 8:00, ...).

    Recibe:   mediciones = la tabla de ocupación.
    Devuelve: una tabla con dos columnas: hora_dia y porcentaje (el promedio de esa hora).
    """
    return (mediciones.assign(hora_dia=mediciones["hora"].dt.hour)
            .groupby("hora_dia")["porcentaje"].mean().reset_index())


def hora_pico(por_hora):
    """
    Busca la hora con mayor ocupación promedio.

    Recibe:   por_hora = la tabla que devuelve promedio_por_hora().
    Devuelve: (hora, promedio). Ejemplo: (16, 4.1).
    """
    fila = por_hora.loc[por_hora["porcentaje"].idxmax()]
    return int(fila["hora_dia"]), float(fila["porcentaje"])


def tabla_dia_hora(mediciones):
    """
    Ocupación media por día de la semana (filas 0=Lun ... 6=Dom) y hora (columnas).

    Recibe:   mediciones = la tabla de ocupación.
    Devuelve: una tabla de 7 filas (días) por N columnas (horas). Sirve para el mapa de calor.
    """
    tabla = (mediciones.assign(dia=mediciones["hora"].dt.dayofweek, h=mediciones["hora"].dt.hour)
             .pivot_table(index="dia", columns="h", values="porcentaje", aggfunc="mean"))
    return tabla.reindex(range(7))   # asegura que aparezcan los 7 días aunque falte alguno


def porcentaje_por_estado(mediciones, estados):
    """
    De todas las mediciones, qué % estuvo en cada estado (VACIA, DISPONIBLE, ...).

    Recibe:   mediciones = la tabla de ocupación.
              estados    = lista con los nombres de los estados a contar.
    Devuelve: una lista de porcentajes, uno por cada estado, en el mismo orden.
    """
    total = len(mediciones)
    return [100 * (mediciones["estado"] == estado).sum() / total for estado in estados]


# ---------------------------------------------------------------------
# 3. Probabilidades observadas
# ---------------------------------------------------------------------
def intervalo_wilson(veces, total, z=1.96):
    """
    Intervalo de confianza del 95 % de una proporción veces/total (método de Wilson).
    Funciona bien aunque 'veces' sea 0.

    Recibe:   veces = cuántas veces ocurrió el evento.
              total = cuántas mediciones hubo en total.
              z     = 1.96 para 95 % de confianza.
    Devuelve: (límite inferior, límite superior), ambos entre 0 y 1.
    """
    if total == 0:
        return 0.0, 0.0
    proporcion = veces / total
    denominador = 1 + z ** 2 / total
    centro = (proporcion + z ** 2 / (2 * total)) / denominador
    margen = z * np.sqrt(proporcion * (1 - proporcion) / total + z ** 2 / (4 * total ** 2)) / denominador
    return max(0.0, centro - margen), min(1.0, centro + margen)


def probabilidades(mediciones, eventos):
    """
    Probabilidad observada = veces que ocurrió / mediciones totales.
    Además, la probabilidad de que entre alguien en una hora (modelo de Poisson).

    Recibe:   mediciones = la tabla de ocupación del periodo.
              eventos    = la tabla con todas las entradas y salidas del periodo.
    Devuelve: un diccionario con n, k_ocupada, k_50, k_80, w_inf, w_sup,
              horas_observadas, n_entradas, lam y p_entrada.
    """
    total_mediciones = len(mediciones)
    porcentajes = mediciones["porcentaje"]
    k_ocupada = int((mediciones["cantidad_personas"] > 0).sum())   # mediciones con al menos 1 persona
    k_50 = int((porcentajes >= 50).sum())                          # mediciones con 50 % o más
    k_80 = int((porcentajes >= 80).sum())                          # mediciones con 80 % o más
    w_inf, w_sup = intervalo_wilson(k_ocupada, total_mediciones)

    # Poisson: lambda = entradas por hora; P(al menos 1 entrada) = 1 - e^(-lambda)
    horas_observadas = int(mediciones["hora"].dt.floor("h").nunique())
    n_entradas = int((eventos["tipo"] == "ENTRADA").sum())
    lam = n_entradas / horas_observadas if horas_observadas else 0.0
    return {
        "n": total_mediciones, "k_ocupada": k_ocupada, "k_50": k_50, "k_80": k_80,
        "w_inf": w_inf, "w_sup": w_sup,
        "horas_observadas": horas_observadas, "n_entradas": n_entradas,
        "lam": lam, "p_entrada": 1 - np.exp(-lam),
    }


# ---------------------------------------------------------------------
# 4. Entradas y permanencia
# ---------------------------------------------------------------------
def entradas_por_hora(eventos):
    """
    Cuántas ENTRADAS hubo en cada hora del día.

    Recibe:   eventos = la tabla con todas las entradas y salidas del periodo.
    Devuelve: una serie (hora del día -> cantidad de entradas). Vacía si no hay entradas.
    """
    entradas = eventos[eventos["tipo"] == "ENTRADA"]
    return entradas.groupby(entradas["hora"].dt.hour).size()


def permanencias_de_salidas(eventos):
    """
    Tiempos de permanencia (en segundos) de las SALIDAS que sí tienen tiempo registrado.

    Recibe:   eventos = la tabla con todas las entradas y salidas del periodo.
    Devuelve: una columna con los segundos de permanencia de cada salida.
    """
    return eventos.loc[(eventos["tipo"] == "SALIDA") & (eventos["permanecia"] > 0), "permanecia"]


def formato_permanencia(segundos):
    """
    Convierte segundos a texto: 125 -> '2 min', 4000 -> '1 h 6 min'.

    Recibe:   segundos = un número (o vacío).
    Devuelve: un texto. Si el valor está vacío devuelve '–'.
    """
    if pd.isna(segundos):
        return "–"
    minutos_totales = int(float(segundos)) // 60
    horas, minutos = divmod(minutos_totales, 60)
    return f"{horas} h {minutos} min" if horas else f"{minutos} min"
