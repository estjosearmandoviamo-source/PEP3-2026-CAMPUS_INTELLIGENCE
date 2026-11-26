"""
  app.py ............ ESTE ARCHIVO: la pantalla. Qué va y en qué posición. (ESTUDIAR)
  streamlit run app.py
"""
from datetime import datetime, time, timedelta

import streamlit as st

import diseno as d
import estadistica as est
from datos import (
    cargar_aulas, cargar_eventos, cargar_ocupacion, cargar_todos_eventos,
     rango_de_fechas,
)

st.set_page_config(page_title="VisionCampus · Estadísticas", layout="wide")
d.cargar_estilo()

# =====================================================================
# CABECERA
# =====================================================================
d.cabecera(False)

# =====================================================================
# FILTROS: aula y periodo
# =====================================================================
aulas = cargar_aulas()                                        # datos.py
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 3, 1])
    with c1:
        nombre_aula = st.selectbox("Aula", aulas["aula"].tolist(), index=0)
    aula = aulas[aulas["aula"] == nombre_aula].iloc[0]
    aula_id, capacidad = int(aula["id"]), int(aula["capacidad"])
    es_simulada = nombre_aula == "AULA-SIM"
    with c1:
        d.etiqueta_datos(es_simulada)

    # [TU LÓGICA] Aquí se decide qué aulas puede mostrar el tablero.
    # Ahora muestra todas las aulas de la tabla "aulas": AULA-P6 (datos reales) y AULA-SIM (simulados).
    # Si algún día quieres limitar el tablero a una sola aula, aquí pones la condición.

    desde, hasta = rango_de_fechas(aula_id)                   # datos.py
    if desde is None:
        st.info("Todavía no hay datos para esta aula. Si es AULA-SIM, ejecuta generar_datos_simulados.py.")
        st.stop()

    with c2:
        rango = st.date_input("Periodo", value=(desde, hasta), min_value=desde, max_value=hasta)
    with c3:
        st.write("")
        if st.button("Actualizar", type="primary", width="stretch"):
            st.cache_data.clear()

if not isinstance(rango, tuple) or len(rango) != 2:
    st.stop()
inicio = datetime.combine(rango[0], time())
fin = datetime.combine(rango[1] + timedelta(days=1), time())

# =====================================================================
# DATOS DEL PERIODO ELEGIDO (se piden una sola vez y se usan en toda la pantalla)
# =====================================================================
ocup = cargar_ocupacion(aula_id, inicio, fin)                 # datos.py
if ocup.empty:
    st.warning("No hay registros de ocupación en este periodo.")
    st.stop()
todos_ev = cargar_todos_eventos(aula_id, inicio, fin)         # datos.py
x = ocup["porcentaje"]                                        # la columna que más se analiza

# =====================================================================
# TARJETAS DE ARRIBA
# =====================================================================
ind = est.indicadores(ocup)                                   # estadistica.py
por_hora = est.promedio_por_hora(ocup)
hora_pico, promedio_pico = est.hora_pico(por_hora)
ultimo = ind["ultimo"]
color_estado = d.COLOR_ESTADO.get(ultimo["estado"], d.VERDE)

k1, k2, k3, k4 = st.columns(4)
with k1:
    with st.container(border=True):
        d.tarjeta_ocupacion(ultimo["porcentaje"], int(ultimo["cantidad_personas"]), capacidad, color_estado)
with k2:
    with st.container(border=True):
        d.tarjeta_estado(ultimo["estado"], color_estado)
with k3:
    with st.container(border=True):
        d.tarjeta_kpi("Hora pico del periodo", f"{hora_pico}:00",
                      f"Promedio de {promedio_pico:.0f} % en esa hora", d.VERDE)
with k4:
    with st.container(border=True):
        d.tarjeta_kpi("Promedio del último día", f"{ind['promedio_dia']:.0f} %",
                      f"{ind['dia_final'].strftime('%d/%m/%Y')} · {d.texto_diferencia(ind['diferencia'])}",
                      d.AZUL_CLARO)

# =====================================================================
# GRÁFICOS: ocupación en el tiempo y promedio por hora
# =====================================================================
g1, g2 = st.columns(2)
with g1:
    with st.container(border=True):
        d.titulo_seccion("Ocupación en el tiempo")
        d.explicacion("Cada punto es una medición. La franja verde marca la zona de hora pico (80 % o más).")
        d.dibujar(d.grafico_ocupacion_en_el_tiempo(ocup, ind["media_periodo"]))
with g2:
    with st.container(border=True):
        d.titulo_seccion("Ocupación promedio por hora")
        d.explicacion("Verde = hora pico (80 % o más). La línea punteada marca ese límite.")
        d.dibujar(d.grafico_promedio_por_hora(por_hora))

# =====================================================================
# RESUMEN ESTADÍSTICO, DISTRIBUCIÓN Y ÚLTIMOS EVENTOS
# =====================================================================
resumen = est.resumen_ocupacion(x)                            # estadistica.py

e1, e2, e3 = st.columns(3)
with e1:
    with st.container(border=True):
        d.titulo_seccion("Resumen estadístico del periodo")
        d.lista_de_datos([
            ("Media (μ)", f"{resumen['media']:.1f} %"),
            ("Desviación estándar (σ)", f"{resumen['desviacion']:.1f} %"),
            ("Máximo", f"{resumen['maximo']:.0f} %"),
            ("Mínimo", f"{resumen['minimo']:.0f} %"),
            ("n (registros)", f"{resumen['n']:,}"),
        ])
with e2:
    with st.container(border=True):
        d.titulo_seccion("Distribución de la ocupación")
        limites, conteos = est.histograma(x)
        d.dibujar(d.grafico_histograma(limites, conteos, resumen["media"]))
        d.intervalo_de_confianza(resumen["ic_inf"], resumen["ic_sup"], resumen["n"], resumen["desviacion"])
with e3:
    with st.container(border=True):
        d.titulo_seccion("Entradas y salidas recientes")
        eventos = cargar_eventos(aula_id, inicio, fin)        # datos.py
        if eventos.empty:
            st.info("No hay eventos en este periodo.")
        else:
            filas = []
            for _, ev in eventos.iterrows():
                # La permanencia solo tiene sentido en las salidas
                permanencia = est.formato_permanencia(ev["permanecia"]) if ev["tipo"] == "SALIDA" else "–"
                filas.append((f"{ev['hora']:%H:%M}", ev["tipo"], permanencia))
            d.tabla_eventos(filas)

# =====================================================================
# PROBABILIDADES OBSERVADAS
# =====================================================================
d.titulo_seccion("Probabilidades observadas en el periodo", separado=True)
d.explicacion("Son frecuencias reales del periodo elegido: cuántas veces ocurrió algo "
              "entre todas las mediciones. No son predicciones.")

pr = est.probabilidades(ocup, todos_ev)                       # estadistica.py
n = pr["n"]

q1, q2, q3, q4 = st.columns(4)
with q1:
    with st.container(border=True):
        d.tarjeta_kpi("Aula con personas", f"{100 * pr['k_ocupada'] / n:.1f} %",
                      f"{pr['k_ocupada']:,} de {n:,} mediciones · "
                      f"IC 95 %: {100 * pr['w_inf']:.1f} – {100 * pr['w_sup']:.1f} %",
                      d.AZUL_CLARO, d.AZUL_CLARO)
with q2:
    with st.container(border=True):
        d.tarjeta_kpi("Ocupación ≥ 50 %", f"{100 * pr['k_50'] / n:.1f} %",
                      f"{pr['k_50']:,} de {n:,} mediciones", d.AMARILLO, d.AMARILLO)
with q3:
    with st.container(border=True):
        d.tarjeta_kpi("Ocupación ≥ 80 %", f"{100 * pr['k_80'] / n:.1f} %",
                      f"{pr['k_80']:,} de {n:,} mediciones", d.NARANJA, d.NARANJA)
with q4:
    with st.container(border=True):
        d.tarjeta_kpi("Entra alguien en 1 hora", f"{100 * pr['p_entrada']:.0f} %",
                      f"Poisson: λ = {pr['lam']:.2f} entradas/hora "
                      f"({pr['n_entradas']} entradas en {pr['horas_observadas']} h)",
                      d.VERDE, d.VERDE)

# =====================================================================
# CUÁNDO SE USA EL AULA
# =====================================================================
h1, h2 = st.columns([3, 2])
with h1:
    with st.container(border=True):
        d.titulo_seccion("¿Cuándo se usa el aula?")
        d.explicacion("Ocupación media (%) por día de la semana y hora. Las celdas vacías no tienen mediciones.")
        d.dibujar(d.grafico_mapa_de_calor(est.tabla_dia_hora(ocup)))
with h2:
    with st.container(border=True):
        d.titulo_seccion("Tiempo en cada estado")
        d.explicacion("Porcentaje de las mediciones en cada estado del aula.")
        estados = list(d.COLOR_ESTADO.keys())
        d.dibujar(d.grafico_estados(estados, est.porcentaje_por_estado(ocup, estados)))

# =====================================================================
# PERCENTILES, ENTRADAS POR HORA Y PERMANENCIA
# =====================================================================
r1, r2, r3 = st.columns([1, 1.3, 1])
with r1:
    with st.container(border=True):
        d.titulo_seccion("Percentiles de la ocupación")
        d.explicacion("P90 = el 90 % de las mediciones estuvo en ese valor o menos.")
        mediana, p90, p95 = est.percentiles(x)
        d.lista_de_datos([
            ("Mediana (P50)", f"{mediana:.1f} %"),
            ("P90", f"{p90:.1f} %"),
            ("P95", f"{p95:.1f} %"),
            ("Máximo", f"{resumen['maximo']:.1f} %"),
            ("Personas (máx.)", f"{int(ocup['cantidad_personas'].max())} de {capacidad}"),
        ])
with r2:
    with st.container(border=True):
        d.titulo_seccion("Entradas por hora del día")
        d.explicacion("Cuántas entradas se registraron en cada hora (suma del periodo).")
        entradas_hora = est.entradas_por_hora(todos_ev)       # estadistica.py
        if entradas_hora.empty:
            st.info("No hay entradas en este periodo.")
        else:
            d.dibujar(d.grafico_entradas_por_hora(entradas_hora))
with r3:
    with st.container(border=True):
        d.titulo_seccion("Permanencia en el aula")
        d.explicacion("Tiempo que estuvo cada persona antes de salir.")
        permanencias = est.permanencias_de_salidas(todos_ev)  # estadistica.py
        if permanencias.empty:
            st.info("Todavía no hay salidas con tiempo de permanencia registrado.")
        else:
            d.lista_de_datos([
                ("Salidas con tiempo", f"{len(permanencias):,}"),
                ("Promedio", est.formato_permanencia(permanencias.mean())),
                ("Mediana", est.formato_permanencia(permanencias.median())),
                ("Máxima", est.formato_permanencia(permanencias.max())),
            ])

# =====================================================================
# PRÓXIMAMENTE Y PIE DE PÁGINA
# =====================================================================
d.titulo_seccion("Próximamente", separado=True)
paneles = [
    ("Anomalías", "Patrones inusuales de ocupación"),
    ("Predicción", "Pronóstico con intervalo de confianza"),
    ("Validación", "Conteo manual vs. sistema"),
    ("Real vs. programado", "Cumplimiento del horario"),
]
for columna, (titulo, texto) in zip(st.columns(4), paneles):
    with columna:
        with st.container(border=True):
            d.tarjeta_proximamente(titulo, texto)

d.pie_de_pagina(es_simulada, nombre_aula)
