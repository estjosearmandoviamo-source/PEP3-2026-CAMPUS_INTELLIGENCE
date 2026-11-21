"""
Dashboard de estadísticas de ocupación de VisionCampus (Streamlit).
Solo lee datos (SELECT) y muestra únicamente AULA-SIM (datos simulados). No usa la tabla de rostros.

Ejecutar desde la carpeta dashboard/:
    streamlit run app.py
"""
from datetime import datetime, time, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from conexion import conectar
from demo import base_disponible, consulta_demo

AULA_SIMULADA = "AULA-SIM"
REGLAS = {
    "VACIA": "0 %",
    "DISPONIBLE": "menos de 50 %",
    "OCUPACION MEDIA": "50 % a 79 %",
    "ALTA OCUPACION": "80 % a 99 %",
    "LLENA": "100 %",
    "SATURACION": "más de 100 %",
}
VERDE = "#3dff54"
AZUL = "#2f80ed"
AZUL_CLARO = "#60a5fa"
ROJO = "#ff5c5c"
TEXTO = "#e6edf7"
TEXTO_SUAVE = "#8fa6c7"

st.set_page_config(page_title="VisionCampus · Estadísticas", layout="wide")

CSS = """
<style>
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display: none; }
header[data-testid="stHeader"] { background: transparent; }

.stApp {
    background: radial-gradient(1200px 600px at 85% -10%, rgba(47,128,237,0.18), transparent 60%),
                linear-gradient(180deg, #0a1426 0%, #070f1e 100%);
    color: #e6edf7;
}
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1420px; }

/* Tarjetas: contenedores con borde luminoso */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(180deg, #0f1d36 0%, #0b1629 100%);
    border: 1px solid rgba(47,128,237,0.55) !important;
    border-radius: 16px !important;
    box-shadow: 0 0 22px rgba(47,128,237,0.14), inset 0 1px 0 rgba(255,255,255,0.03);
    padding: 6px 8px;
}

/* Cabecera */
.cabecera { display: flex; align-items: center; gap: 22px; margin-bottom: 14px; }
.logo { font-size: 2.1rem; font-weight: 800; color: #ffffff; letter-spacing: -0.5px; }
.logo span { color: #4ade50; }
.sep { width: 2px; height: 56px; background: rgba(96,165,250,0.45); }
.titulo-principal { font-size: 2.2rem; font-weight: 800; color: #ffffff; line-height: 1.1; }
.subtitulo { font-size: 1.05rem; color: #9fb3cf; margin-top: 4px; }

/* Etiquetas y controles */
[data-testid="stWidgetLabel"] p, label p { color: #9fb3cf !important; font-size: 0.9rem; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background: #0c1a31 !important;
    border: 1px solid rgba(47,128,237,0.7) !important;
    border-radius: 12px !important;
    color: #e6edf7 !important;
}
div[data-baseweb="select"] span, div[data-baseweb="select"] div, input { color: #e6edf7 !important; }
button[kind="primary"] {
    background: linear-gradient(180deg, #4ade50, #22c55e) !important;
    color: #04130a !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    height: 2.6rem;
    box-shadow: 0 0 16px rgba(61,255,84,0.35);
}

/* Tarjetas KPI */
.kpi { padding: 4px 6px; }
.kpi-titulo { color: #9fb3cf; font-size: 0.95rem; font-weight: 600; margin-bottom: 6px; }
.kpi-valor { color: #ffffff; font-size: 2.6rem; font-weight: 800; line-height: 1.05; }
.kpi-valor.verde { color: #3dff54; text-shadow: 0 0 14px rgba(61,255,84,0.35); }
.kpi-pie { color: #9fb3cf; font-size: 0.95rem; margin-top: 6px; }
.badge {
    display: inline-block; background: linear-gradient(180deg, #4ade50, #22c55e);
    color: #04130a; border-radius: 999px; padding: 8px 20px; font-weight: 800;
    font-size: 1.05rem; box-shadow: 0 0 16px rgba(61,255,84,0.35);
}
.barra { height: 8px; background: #1b2d4a; border-radius: 999px; margin-top: 10px; overflow: hidden; }
.barra div { height: 100%; background: linear-gradient(90deg, #22c55e, #3dff54); border-radius: 999px; }

/* Títulos de sección */
.seccion { font-size: 1.15rem; font-weight: 700; color: #ffffff; margin: 2px 0 10px 2px; }

/* Filas de resumen con píldoras */
.fila { display: flex; justify-content: space-between; align-items: center;
        padding: 9px 4px; border-bottom: 1px solid rgba(96,165,250,0.15); }
.fila:last-child { border-bottom: none; }
.fila .nombre { color: #cfe0f5; font-size: 0.98rem; }
.pill {
    background: linear-gradient(180deg, #4ade50, #22c55e); color: #04130a;
    font-weight: 800; border-radius: 10px; padding: 4px 14px; min-width: 70px; text-align: center;
    box-shadow: 0 0 10px rgba(61,255,84,0.25);
}

/* Tabla de eventos */
.tabla { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
.tabla th { color: #9fb3cf; text-align: left; padding: 8px 6px; font-weight: 600;
            border-bottom: 1px solid rgba(96,165,250,0.35); }
.tabla td { color: #e6edf7; padding: 9px 6px; border-bottom: 1px solid rgba(96,165,250,0.12); }
.ent { color: #3dff54; font-weight: 700; }
.sal { color: #ff5c5c; font-weight: 700; }

/* Pills de IC y Próximamente */
.ic {
    background: rgba(61,255,84,0.08); border: 1px solid rgba(61,255,84,0.55);
    color: #3dff54; border-radius: 12px; padding: 10px 14px; text-align: center;
    font-weight: 700; margin-top: 10px;
}
.proximo { display: flex; flex-direction: column; gap: 6px; padding: 4px 4px; }
.proximo .cabeza { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.proximo b { color: #ffffff; font-size: 1.02rem; }
.chip {
    background: rgba(47,128,237,0.25); color: #bfdbfe; border-radius: 999px;
    padding: 3px 10px; font-size: 0.72rem; font-weight: 700; white-space: nowrap;
    border: 1px solid rgba(96,165,250,0.5);
}
.proximo small { color: #9fb3cf; font-size: 0.9rem; }

.pie-pagina { text-align: center; color: #6b82a6; font-size: 0.85rem; margin-top: 18px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def estilo_grafico(fig, titulo, altura):
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=15, color=TEXTO)),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXTO_SUAVE),
        margin=dict(l=10, r=10, t=55, b=10),
        xaxis=dict(gridcolor="#1b2d4a", zerolinecolor="#1b2d4a", linecolor="#1b2d4a"),
        yaxis=dict(gridcolor="#1b2d4a", zerolinecolor="#1b2d4a", linecolor="#1b2d4a"),
    )
    return fig


@st.cache_data(ttl=30)
def modo_demostracion():
    return not base_disponible()


MODO_DEMO = modo_demostracion()


def consultar(sql, params=None):
    if MODO_DEMO:
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
    df = consultar(
        "SELECT MIN(hora)::date AS desde, MAX(hora)::date AS hasta "
        "FROM ocupacion_historico WHERE aula_id = %s",
        (aula_id,),
    )
    return df.loc[0, "desde"], df.loc[0, "hasta"]


@st.cache_data(ttl=60)
def cargar_ocupacion(aula_id, inicio, fin):
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
    return consultar(
        "SELECT hora, tipo, permanecia FROM eventos "
        "WHERE aula_id = %s AND hora >= %s AND hora < %s ORDER BY hora DESC LIMIT 5",
        (aula_id, inicio, fin),
    )


def formato_permanencia(segundos):
    if pd.isna(segundos):
        return "–"
    minutos_totales = int(float(segundos)) // 60
    horas, minutos = divmod(minutos_totales, 60)
    return f"{horas} h {minutos} min" if horas else f"{minutos} min"


# ---------------- Cabecera ----------------
st.markdown(
    """
    <div class="cabecera">
        <div class="logo">Vision<span>Campus</span></div>
        <div class="sep"></div>
        <div>
            <div class="titulo-principal">Estadísticas de Ocupación</div>
            <div class="subtitulo">Uso real de las aulas a partir de datos medidos</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if MODO_DEMO:
    st.warning("Modo demostración: no hay base de datos conectada. Se muestran datos simulados (AULA-SIM) generados en memoria.")

# ---------------- Filtros ----------------
aulas = cargar_aulas()
with st.container(border=True):
    c1, c2, c3 = st.columns([2, 3, 1])
    with c1:
        nombre_aula = st.selectbox("Aula", aulas["aula"].tolist(), index=0)
    aula = aulas[aulas["aula"] == nombre_aula].iloc[0]
    aula_id, capacidad = int(aula["id"]), int(aula["capacidad"])

    if nombre_aula != AULA_SIMULADA:
        st.error("Este panel solo muestra datos simulados (AULA-SIM). Selecciona AULA-SIM.")
        st.stop()

    desde, hasta = rango_de_fechas(aula_id)
    if desde is None:
        st.info("Todavía no hay datos para esta aula. Ejecuta generar_datos_simulados.py.")
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

ocup = cargar_ocupacion(aula_id, inicio, fin)
if ocup.empty:
    st.warning("No hay registros de ocupación en este periodo.")
    st.stop()

# ---------------- Indicadores ----------------
ultimo = ocup.iloc[-1]
dia_final = ocup["hora"].dt.date.max()
promedio_dia = ocup.loc[ocup["hora"].dt.date == dia_final, "porcentaje"].mean()
ancho_barra = min(max(float(ultimo["porcentaje"]), 0), 100)

k1, k2, k3, k4 = st.columns(4)
with k1:
    with st.container(border=True):
        st.markdown(
            f"""<div class="kpi">
                <div class="kpi-titulo">Ocupación actual</div>
                <div class="kpi-valor verde">{ultimo['porcentaje']:.0f} %</div>
                <div class="barra"><div style="width:{ancho_barra:.0f}%"></div></div>
                <div class="kpi-pie">{int(ultimo['cantidad_personas'])} / {capacidad} personas</div>
            </div>""",
            unsafe_allow_html=True,
        )
with k2:
    with st.container(border=True):
        st.markdown(
            f"""<div class="kpi">
                <div class="kpi-titulo">Estado del aula</div>
                <span class="badge">{ultimo['estado']}</span>
                <div class="kpi-pie">Regla: {REGLAS.get(ultimo['estado'], '')}</div>
            </div>""",
            unsafe_allow_html=True,
        )
with k3:
    with st.container(border=True):
        st.markdown(
            f"""<div class="kpi">
                <div class="kpi-titulo">Personas ahora</div>
                <div class="kpi-valor">{int(ultimo['cantidad_personas'])} de {capacidad}</div>
            </div>""",
            unsafe_allow_html=True,
        )
with k4:
    with st.container(border=True):
        st.markdown(
            f"""<div class="kpi">
                <div class="kpi-titulo">Promedio del último día</div>
                <div class="kpi-valor">{promedio_dia:.0f} %</div>
                <div class="kpi-pie">{dia_final.strftime('%d/%m/%Y')}</div>
            </div>""",
            unsafe_allow_html=True,
        )

# ---------------- Gráficos de tiempo y por hora ----------------
g1, g2 = st.columns(2)
with g1:
    with st.container(border=True):
        fig = go.Figure(go.Scatter(
            x=ocup["hora"], y=ocup["porcentaje"], mode="lines",
            line=dict(color=AZUL_CLARO, width=2), fill="tozeroy",
            fillcolor="rgba(47,128,237,0.28)", name="Ocupación",
        ))
        fig.add_hline(y=100, line_dash="dash", line_color=VERDE,
                      annotation_text="Capacidad (100 %)",
                      annotation_font_color=VERDE)
        fig.update_yaxes(range=[0, 105], ticksuffix=" %")
        estilo_grafico(fig, "Ocupación en el tiempo", 360)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with g2:
    with st.container(border=True):
        por_hora = (ocup.assign(hora_dia=ocup["hora"].dt.hour)
                    .groupby("hora_dia")["porcentaje"].mean().reset_index())
        colores = [VERDE if p >= 80 else AZUL for p in por_hora["porcentaje"]]
        fig = go.Figure(go.Bar(
            x=por_hora["hora_dia"].astype(str) + ":00", y=por_hora["porcentaje"],
            marker=dict(color=colores, line=dict(width=0)),
            text=[f"{p:.0f} %" for p in por_hora["porcentaje"]],
            textposition="outside", textfont=dict(color=TEXTO),
        ))
        fig.update_yaxes(range=[0, 110], ticksuffix=" %")
        estilo_grafico(fig, "Ocupación promedio por hora  ·  verde = hora pico (≥ 80 %)", 360)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ---------------- Estadística del periodo ----------------
x = ocup["porcentaje"]
n = len(x)
media = x.mean()
s = x.std(ddof=1)  # desviación estándar muestral
ic_margen = 1.96 * s / np.sqrt(n)
ic_inf, ic_sup = media - ic_margen, media + ic_margen

e1, e2, e3 = st.columns([1, 1, 1])
with e1:
    with st.container(border=True):
        st.markdown('<div class="seccion">Resumen estadístico del periodo</div>', unsafe_allow_html=True)
        filas = [
            ("Media (μ)", f"{media:.1f} %"),
            ("Desviación estándar (σ)", f"{s:.1f} %"),
            ("Máximo", f"{x.max():.0f} %"),
            ("Mínimo", f"{x.min():.0f} %"),
            ("n (registros)", f"{n:,}"),
        ]
        html = "".join(f'<div class="fila"><span class="nombre">{k}</span><span class="pill">{v}</span></div>'
                       for k, v in filas)
        st.markdown(html, unsafe_allow_html=True)

with e2:
    with st.container(border=True):
        st.markdown('<div class="seccion">Distribución de la ocupación</div>', unsafe_allow_html=True)
        limites = list(range(0, 101, 10))
        conteos, _ = np.histogram(x, bins=limites)
        etiquetas = [f"{a}–{b}" for a, b in zip(limites[:-1], limites[1:])]
        fig = go.Figure(go.Bar(x=etiquetas, y=conteos,
                               marker=dict(color=AZUL, line=dict(color=AZUL_CLARO, width=1))))
        estilo_grafico(fig, "", 280)
        fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), xaxis_title="Ocupación (%)",
                          yaxis_title="Registros")
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.markdown(
            f'<div class="ic">IC 95 % de la media: {ic_inf:.1f} % – {ic_sup:.1f} %</div>',
            unsafe_allow_html=True,
        )

with e3:
    with st.container(border=True):
        st.markdown('<div class="seccion">Entradas y salidas recientes</div>', unsafe_allow_html=True)
        eventos = cargar_eventos(aula_id, inicio, fin)
        if eventos.empty:
            st.info("No hay eventos en este periodo.")
        else:
            filas_ev = []
            for _, ev in eventos.iterrows():
                if ev["tipo"] == "ENTRADA":
                    tipo = '<span class="ent">→ Entrada</span>'
                else:
                    tipo = '<span class="sal">← Salida</span>'
                filas_ev.append(
                    f"<tr><td>{ev['hora']:%H:%M}</td><td>{tipo}</td>"
                    f"<td>{formato_permanencia(ev['permanecia'])}</td></tr>"
                )
            st.markdown(
                "<table class='tabla'><thead><tr><th>Hora</th><th>Tipo</th><th>Permanencia</th></tr></thead>"
                f"<tbody>{''.join(filas_ev)}</tbody></table>",
                unsafe_allow_html=True,
            )

# ---------------- Paneles futuros ----------------
st.markdown('<div class="seccion" style="margin-top:14px">Próximamente</div>', unsafe_allow_html=True)
p1, p2, p3, p4 = st.columns(4)
paneles = [
    (p1, "Anomalías", "Patrones inusuales de ocupación"),
    (p2, "Predicción", "Pronóstico con intervalo de confianza"),
    (p3, "Validación", "Conteo manual vs. sistema"),
    (p4, "Real vs. programado", "Cumplimiento del horario"),
]
for col, titulo, texto in paneles:
    with col:
        with st.container(border=True):
            st.markdown(
                f"""<div class="proximo">
                    <div class="cabeza"><b>{titulo}</b><span class="chip">Próximamente</span></div>
                    <small>{texto}</small>
                </div>""",
                unsafe_allow_html=True,
            )

st.markdown(
    '<div class="pie-pagina">VisionCampus v1.5 · Datos simulados (AULA-SIM) · Sistema anónimo: no identifica personas</div>',
    unsafe_allow_html=True,
)
