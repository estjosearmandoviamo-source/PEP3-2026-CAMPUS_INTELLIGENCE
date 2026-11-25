"""
DISEÑO del dashboard  ·  DECORACIÓN (no hace falta estudiarlo)
==============================================================
Todo lo que tiene que ver con CÓMO SE VE: colores, HTML de las tarjetas y estilo de los gráficos.
No calcula nada ni toca la base de datos: recibe números ya calculados y los dibuja.

  - Colores y textos fijos ............ arriba
  - Piezas de HTML (tarjetas, tablas) .. sección 1
  - Gráficos de plotly ................. sección 2
  - Los colores de las tarjetas y bordes están en estilo.css (como el .qss de la app de escritorio)
"""
import os

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------
# Colores y textos fijos
# ---------------------------------------------------------------------
VERDE = "#3dff54"
AZUL = "#2f80ed"
AZUL_CLARO = "#60a5fa"
AMARILLO = "#ffd24d"
NARANJA = "#ff9f43"
TEXTO = "#e6edf7"
TEXTO_SUAVE = "#8fa6c7"

# Color de cada estado del aula (de tranquilo a crítico)
COLOR_ESTADO = {
    "VACIA": "#8fa6c7",
    "DISPONIBLE": "#3dff54",
    "OCUPACION MEDIA": "#ffd24d",
    "ALTA OCUPACION": "#ff9f43",
    "LLENA": "#ff5c5c",
    "SATURACION": "#ff3b3b",
}
# Texto que explica cuándo se da cada estado
REGLAS = {
    "VACIA": "0 %",
    "DISPONIBLE": "menos de 50 %",
    "OCUPACION MEDIA": "50 % a 79 %",
    "ALTA OCUPACION": "80 % a 99 %",
    "LLENA": "100 %",
    "SATURACION": "más de 100 %",
}


def cargar_estilo():
    """Lee estilo.css y se lo pasa a Streamlit."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "estilo.css")
    with open(ruta, encoding="utf-8") as archivo:
        st.markdown(f"<style>{archivo.read()}</style>", unsafe_allow_html=True)


def mostrar_html(codigo):
    """Dibuja un trozo de HTML en la página."""
    st.markdown(codigo, unsafe_allow_html=True)


def dibujar(fig):
    """Dibuja un gráfico de plotly sin la barra de herramientas."""
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# =====================================================================
# 1. PIEZAS DE HTML
# =====================================================================
def cabecera(modo_demo):
    """Logo, título y etiqueta de conexión."""
    if modo_demo:
        chip = '<span class="chip-estado ambar">● Modo demostración · sin base de datos</span>'
    else:
        chip = '<span class="chip-estado verde">● Conectado a PostgreSQL</span>'
    mostrar_html(f"""
    <div class="cabecera">
        <div class="logo">Vision<span>Campus</span></div>
        <div class="sep"></div>
        <div>
            <div class="titulo-principal">Estadísticas de Ocupación</div>
            <div class="subtitulo">Ocupación de aulas medida con visión por computadora</div>
        </div>
        <div class="lado-derecho">{chip}</div>
    </div>
    """)


def etiqueta_datos(es_simulada):
    """Etiqueta DATOS SIMULADOS (amarilla) o DATOS REALES (verde)."""
    if es_simulada:
        mostrar_html('<span class="chip-datos sim">DATOS SIMULADOS</span>')
    else:
        mostrar_html('<span class="chip-datos real">DATOS REALES</span>')


def titulo_seccion(texto, separado=False):
    margen = ' style="margin-top:14px"' if separado else ""
    mostrar_html(f'<div class="seccion"{margen}>{texto}</div>')


def explicacion(texto):
    mostrar_html(f'<div class="explica">{texto}</div>')


def tarjeta_kpi(titulo, valor, pie, color_acento, color_valor=None):
    """Tarjeta con franja de color, un número grande y una línea de detalle."""
    estilo_valor = f' style="color:{color_valor}"' if color_valor else ""
    mostrar_html(f"""<div class="kpi">
        <div class="acento" style="background:{color_acento}"></div>
        <div class="kpi-titulo">{titulo}</div>
        <div class="kpi-valor"{estilo_valor}>{valor}</div>
        <div class="kpi-pie">{pie}</div>
    </div>""")


def tarjeta_ocupacion(porcentaje, personas, capacidad, color):
    """Tarjeta 'Ocupación actual' con su barra de progreso."""
    ancho = min(max(float(porcentaje), 0), 100)
    mostrar_html(f"""<div class="kpi">
        <div class="acento" style="background:{color}"></div>
        <div class="kpi-titulo">Ocupación actual</div>
        <div class="kpi-valor" style="color:{color}">{porcentaje:.0f} %</div>
        <div class="barra"><div style="width:{ancho:.0f}%; background:{color}"></div></div>
        <div class="kpi-pie">{personas} / {capacidad} personas</div>
    </div>""")


def tarjeta_estado(estado, color):
    """Tarjeta 'Estado del aula' con la etiqueta de color."""
    mostrar_html(f"""<div class="kpi">
        <div class="acento" style="background:{color}"></div>
        <div class="kpi-titulo">Estado del aula</div>
        <span class="badge" style="background:{color}">{estado}</span>
        <div class="kpi-pie">Regla: {REGLAS.get(estado, '')}</div>
    </div>""")


def texto_diferencia(diferencia):
    """'▲ +3 puntos frente al periodo' (naranja si sube, verde si baja)."""
    if diferencia >= 0:
        return f'<span class="delta-sube">▲ {diferencia:+.0f} puntos</span> frente al periodo'
    return f'<span class="delta-baja">▼ {diferencia:+.0f} puntos</span> frente al periodo'


def lista_de_datos(filas):
    """Lista de pares (nombre, valor) con el valor dentro de una etiqueta verde."""
    mostrar_html("".join(
        f'<div class="fila"><span class="nombre">{nombre}</span><span class="pill">{valor}</span></div>'
        for nombre, valor in filas
    ))


def intervalo_de_confianza(ic_inf, ic_sup, n, desviacion):
    mostrar_html(
        f'<div class="ic">IC 95 % de la media: {ic_inf:.1f} % – {ic_sup:.1f} %</div>'
        f'<div class="explica" style="text-align:center; margin-top:6px">'
        f'Con 95 % de confianza, la media real está en ese rango (n = {n:,}, σ = {desviacion:.1f} %).</div>'
    )


def tabla_eventos(filas):
    """Tabla de entradas y salidas. filas = lista de (hora, tipo, permanencia_en_texto)."""
    cuerpo = ""
    for hora, tipo, permanencia in filas:
        if tipo == "ENTRADA":
            etiqueta = '<span class="ent">→ Entrada</span>'
        else:
            etiqueta = '<span class="sal">← Salida</span>'
        cuerpo += f"<tr><td>{hora}</td><td>{etiqueta}</td><td>{permanencia}</td></tr>"
    mostrar_html(
        "<table class='tabla'><thead><tr><th>Hora</th><th>Tipo</th><th>Permanencia</th></tr></thead>"
        f"<tbody>{cuerpo}</tbody></table>"
    )


def tarjeta_proximamente(titulo, texto):
    mostrar_html(f"""<div class="proximo">
        <div class="cabeza"><b>{titulo}</b><span class="chip">Próximamente</span></div>
        <small>{texto}</small>
    </div>""")


def pie_de_pagina(es_simulada, nombre_aula):
    datos = "Datos simulados (AULA-SIM)" if es_simulada else "Datos reales de " + nombre_aula
    mostrar_html(f'<div class="pie-pagina">VisionCampus v1.5 · {datos} · Sistema anónimo: no identifica personas</div>')


# =====================================================================
# 2. GRÁFICOS (plotly). Cada función recibe datos ya calculados y devuelve la figura.
# =====================================================================
def _estilo_base(fig, altura):
    """Fondo transparente, letras y rejilla del tema oscuro."""
    fig.update_layout(
        title=dict(text="", font=dict(size=15, color=TEXTO)),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXTO_SUAVE),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor="#1b2d4a", zerolinecolor="#1b2d4a", linecolor="#1b2d4a"),
        yaxis=dict(gridcolor="#1b2d4a", zerolinecolor="#1b2d4a", linecolor="#1b2d4a"),
    )
    return fig


def grafico_ocupacion_en_el_tiempo(ocup, media_periodo):
    fig = go.Figure()
    # Un trazo por día: la línea nunca une el final de un día con el inicio del siguiente
    for dia, datos_dia in ocup.groupby(ocup["hora"].dt.date):
        fig.add_trace(go.Scatter(
            x=datos_dia["hora"], y=datos_dia["porcentaje"], mode="lines",
            line=dict(color=AZUL_CLARO, width=2), fill="tozeroy",
            fillcolor="rgba(47,128,237,0.28)", name=str(dia), showlegend=False,
            hovertemplate="%{x|%d/%m %H:%M}<br><b>%{y:.0f} %</b><extra></extra>",
        ))
    fig.add_hrect(y0=80, y1=105, fillcolor="rgba(61,255,84,0.07)", line_width=0)
    fig.add_hline(y=100, line_dash="dash", line_color=VERDE,
                  annotation_text="Capacidad (100 %)", annotation_font_color=VERDE)
    fig.add_hline(y=media_periodo, line_dash="dot", line_color=AMARILLO,
                  annotation_text=f"Media {media_periodo:.0f} %",
                  annotation_position="bottom right", annotation_font_color=AMARILLO)
    fig.update_yaxes(range=[0, 105], ticksuffix=" %")
    _estilo_base(fig, 340)
    fig.update_layout(showlegend=False)
    return fig


def grafico_promedio_por_hora(por_hora):
    colores = [VERDE if valor >= 80 else AZUL for valor in por_hora["porcentaje"]]
    fig = go.Figure(go.Bar(
        x=por_hora["hora_dia"].astype(str) + ":00", y=por_hora["porcentaje"],
        marker=dict(color=colores, line=dict(width=0)),
        text=[f"{valor:.0f} %" for valor in por_hora["porcentaje"]],
        textposition="outside", textfont=dict(color=TEXTO),
        hovertemplate="%{x}<br><b>%{y:.1f} %</b> en promedio<extra></extra>",
    ))
    fig.add_hline(y=80, line_dash="dot", line_color=VERDE, opacity=0.6)
    fig.update_yaxes(range=[0, 110], ticksuffix=" %")
    return _estilo_base(fig, 340)


def grafico_histograma(limites, conteos, media):
    centros = [a + 5 for a in limites[:-1]]                       # centro de cada intervalo
    etiquetas = [f"{a}–{b}" for a, b in zip(limites[:-1], limites[1:])]
    colores = [VERDE if a >= 80 else AZUL for a in limites[:-1]]
    fig = go.Figure(go.Bar(
        x=centros, y=conteos, width=9,
        marker=dict(color=colores, line=dict(color=AZUL_CLARO, width=1)),
        hovertemplate="Ocupación %{text}<br><b>%{y}</b> registros<extra></extra>",
        text=etiquetas, textposition="none",
    ))
    fig.add_vline(x=media, line_dash="dash", line_color=AMARILLO,
                  annotation_text=f"μ = {media:.1f} %", annotation_font_color=AMARILLO)
    _estilo_base(fig, 280)
    fig.update_layout(xaxis_title="Ocupación (%)", yaxis_title="Registros")
    fig.update_xaxes(tickvals=centros, ticktext=etiquetas, range=[0, 100])
    return fig


def grafico_mapa_de_calor(tabla):
    nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    valor_max = max(float(np.nanmax(tabla.values)), 10.0)
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=[f"{h}:00" for h in tabla.columns], y=nombres_dias,
        zmin=0, zmax=valor_max, xgap=3, ygap=3,
        colorscale=[[0, "#0f2342"], [0.5, AZUL], [1, VERDE]],
        colorbar=dict(ticksuffix=" %", thickness=10, tickfont=dict(color=TEXTO_SUAVE)),
        hovertemplate="%{y} %{x}<br><b>%{z:.1f} %</b> de ocupación media<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    return _estilo_base(fig, 300)


def grafico_estados(estados, porcentajes):
    fig = go.Figure(go.Bar(
        y=estados, x=porcentajes, orientation="h",
        marker=dict(color=[COLOR_ESTADO[e] for e in estados]),
        text=[f"{valor:.1f} %" for valor in porcentajes], textposition="outside",
        textfont=dict(color=TEXTO),
        hovertemplate="%{y}<br><b>%{x:.1f} %</b> del tiempo<extra></extra>",
    ))
    fig.update_xaxes(range=[0, 118], ticksuffix=" %")
    fig.update_yaxes(autorange="reversed")
    return _estilo_base(fig, 300)


def grafico_entradas_por_hora(por_hora_ent):
    fig = go.Figure(go.Bar(
        x=[f"{h}:00" for h in por_hora_ent.index], y=por_hora_ent.values,
        marker=dict(color=VERDE), text=por_hora_ent.values, textposition="outside",
        textfont=dict(color=TEXTO),
        hovertemplate="%{x}<br><b>%{y}</b> entradas<extra></extra>",
    ))
    fig.update_yaxes(range=[0, float(por_hora_ent.max()) * 1.25])
    return _estilo_base(fig, 250)
