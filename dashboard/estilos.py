"""Sistema visual del tablero de monitoreo.

Reúne la paleta, la hoja de estilos y los componentes de presentación que el
tablero usa en todas sus secciones. Separar esto de `app.py` mantiene la
lógica de datos legible y permite cambiar la apariencia en un solo lugar.

Las animaciones son de entrada y de respuesta al puntero: nada se mueve de
forma permanente salvo el resplandor del encabezado y el punto que señala una
alerta alta sin revisar, porque en un tablero de operación el movimiento debe
significar algo.
"""

from html import escape

import streamlit as st

# --------------------------------------------------------------------------
# Paleta
# --------------------------------------------------------------------------
PALETA = {
    "fondo": "#0A0F1C",
    "superficie": "#111A2E",
    "superficie_alta": "#16213A",
    "borde": "#22324F",
    "borde_suave": "#1A2840",
    "texto": "#E8EEF9",
    "texto_suave": "#93A4C0",
    "texto_tenue": "#64748B",
    "acento": "#4C8DFF",
    "acento_claro": "#7FB0FF",
    "verde": "#2FBF8F",
    "ambar": "#F2B544",
    "rojo": "#F26A6A",
    "violeta": "#9B7BFF",
}

TONOS = {
    "neutro": PALETA["acento"],
    "exito": PALETA["verde"],
    "aviso": PALETA["ambar"],
    "peligro": PALETA["rojo"],
    "violeta": PALETA["violeta"],
}


# --------------------------------------------------------------------------
# Hoja de estilos
# --------------------------------------------------------------------------
def _hoja():
    p = PALETA
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {{
    --fondo: {p['fondo']};
    --superficie: {p['superficie']};
    --superficie-alta: {p['superficie_alta']};
    --borde: {p['borde']};
    --borde-suave: {p['borde_suave']};
    --texto: {p['texto']};
    --texto-suave: {p['texto_suave']};
    --texto-tenue: {p['texto_tenue']};
    --acento: {p['acento']};
    --acento-claro: {p['acento_claro']};
    --verde: {p['verde']};
    --ambar: {p['ambar']};
    --rojo: {p['rojo']};
    --violeta: {p['violeta']};
    --radio: 14px;
    --sombra: 0 1px 2px rgba(0,0,0,.30), 0 8px 24px -12px rgba(0,0,0,.55);
}}

html, body, .stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, sans-serif;
}}
.stApp button, .stApp input, .stApp select, .stApp textarea,
.stApp p, .stApp span, .stApp div, .stApp label,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {{
    font-family: inherit;
}}

/* Los iconos de Streamlit son ligaduras tipográficas: si se les impone otra
   fuente se dibujan como texto. Hay que devolverles la suya. */
[data-testid="stIconMaterial"],
[data-testid="stAlertDynamicIcon"],
[data-testid*="Icon"],
span.material-symbols-rounded,
.stApp [class*="material-symbols"] {{
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal !important;
    font-style: normal !important;
    letter-spacing: normal !important;
    text-transform: none !important;
}}

code, pre, [data-testid="stCode"] {{
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
}}

/* Fondo con dos halos muy tenues que dan profundidad sin distraer */
.stApp {{
    background:
        radial-gradient(900px 480px at 12% -8%, rgba(76,141,255,.10), transparent 60%),
        radial-gradient(760px 420px at 92% 4%, rgba(155,123,255,.08), transparent 60%),
        var(--fondo);
    background-attachment: fixed;
}}

[data-testid="stHeader"] {{
    background: transparent;
    backdrop-filter: blur(6px);
}}

[data-testid="stMain"] .block-container {{
    padding-top: 2.2rem;
    padding-bottom: 4rem;
    max-width: 1500px;
}}

h1, h2, h3, h4 {{ letter-spacing: -.02em; }}

/* ---------------- Encabezado ---------------- */
.mlops-hero {{
    position: relative;
    overflow: hidden;
    border: 1px solid var(--borde);
    border-radius: 20px;
    padding: 1.6rem 1.9rem 1.5rem;
    margin-bottom: 1.4rem;
    background:
        linear-gradient(135deg, rgba(76,141,255,.14), rgba(155,123,255,.06) 45%,
                        rgba(17,26,46,.0) 75%),
        var(--superficie);
    box-shadow: var(--sombra);
    animation: aparecer .55s cubic-bezier(.22,.9,.3,1) both;
}}
.mlops-hero::before {{
    content: "";
    position: absolute;
    inset: -1px -1px auto -1px;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--acento),
                                var(--violeta), var(--acento), transparent);
    background-size: 220% 100%;
    animation: barrido 9s ease-in-out infinite;
}}
.mlops-hero h1 {{
    font-size: 1.72rem;
    font-weight: 700;
    margin: 0 0 .25rem;
    color: var(--texto);
}}
.mlops-hero p {{
    margin: 0;
    color: var(--texto-suave);
    font-size: .93rem;
}}
.mlops-chips {{
    display: flex;
    flex-wrap: wrap;
    gap: .45rem;
    margin-top: 1rem;
}}

/* ---------------- Insignias ---------------- */
.mlops-chip {{
    display: inline-flex;
    align-items: center;
    gap: .42rem;
    padding: .3rem .72rem;
    border-radius: 999px;
    font-size: .78rem;
    font-weight: 500;
    letter-spacing: .01em;
    border: 1px solid color-mix(in srgb, var(--tono) 35%, transparent);
    background: color-mix(in srgb, var(--tono) 13%, transparent);
    color: color-mix(in srgb, var(--tono) 72%, white);
    transition: transform .18s ease, background .18s ease;
}}
.mlops-chip:hover {{ transform: translateY(-1px); }}
.mlops-chip .punto {{
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--tono);
    box-shadow: 0 0 0 0 color-mix(in srgb, var(--tono) 60%, transparent);
}}
.mlops-chip.vivo .punto {{ animation: latido 2s ease-out infinite; }}

/* ---------------- Tarjetas de indicador ---------------- */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: .85rem;
    margin-bottom: 1.6rem;
}}
.kpi {{
    position: relative;
    overflow: hidden;
    border: 1px solid var(--borde-suave);
    border-radius: var(--radio);
    background: linear-gradient(180deg, var(--superficie-alta), var(--superficie));
    padding: 1rem 1.1rem 1.05rem;
    box-shadow: var(--sombra);
    animation: subir .5s cubic-bezier(.22,.9,.3,1) both;
    animation-delay: calc(var(--i) * 70ms);
    transition: transform .22s cubic-bezier(.22,.9,.3,1),
                border-color .22s ease, box-shadow .22s ease;
}}
.kpi::after {{
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: var(--tono);
    opacity: .85;
}}
.kpi:hover {{
    transform: translateY(-3px);
    border-color: color-mix(in srgb, var(--tono) 45%, var(--borde));
    box-shadow: 0 1px 2px rgba(0,0,0,.3),
                0 18px 36px -18px color-mix(in srgb, var(--tono) 55%, transparent);
}}
.kpi .rotulo {{
    font-size: .74rem;
    font-weight: 600;
    letter-spacing: .07em;
    text-transform: uppercase;
    color: var(--texto-tenue);
    margin-bottom: .45rem;
}}
.kpi .valor {{
    font-size: 1.62rem;
    font-weight: 700;
    line-height: 1.12;
    color: var(--texto);
    font-variant-numeric: tabular-nums;
    word-break: break-word;
}}
.kpi .pie {{
    margin-top: .3rem;
    font-size: .78rem;
    color: var(--texto-suave);
}}

/* ---------------- Encabezado de sección ---------------- */
.seccion {{
    display: flex;
    align-items: flex-start;
    gap: .8rem;
    margin: .4rem 0 .9rem;
    animation: subir .45s cubic-bezier(.22,.9,.3,1) both;
}}
.seccion .indice {{
    flex: 0 0 auto;
    width: 30px; height: 30px;
    display: grid; place-items: center;
    border-radius: 9px;
    font-size: .82rem; font-weight: 700;
    color: var(--acento-claro);
    background: rgba(76,141,255,.12);
    border: 1px solid rgba(76,141,255,.28);
}}
.seccion .titulo {{
    font-size: 1.07rem; font-weight: 650;
    color: var(--texto); margin: .18rem 0 .12rem;
}}
.seccion .descripcion {{
    font-size: .855rem; color: var(--texto-suave);
    margin: 0; max-width: 92ch; line-height: 1.5;
}}

/* ---------------- Contenedores con borde ---------------- */
[data-testid="stVerticalBlockBorderWrapper"] {{
    border-radius: var(--radio) !important;
    border-color: var(--borde-suave) !important;
    background: linear-gradient(180deg,
                rgba(22,33,58,.55), rgba(17,26,46,.35)) !important;
}}

/* ---------------- Indicadores nativos ---------------- */
[data-testid="stMetric"] {{
    background: linear-gradient(180deg, var(--superficie-alta), var(--superficie));
    border: 1px solid var(--borde-suave);
    border-radius: var(--radio);
    padding: .85rem 1rem;
    transition: transform .2s ease, border-color .2s ease;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    border-color: rgba(76,141,255,.4);
}}
[data-testid="stMetricLabel"] p {{
    font-size: .76rem !important;
    font-weight: 600;
    letter-spacing: .05em;
    text-transform: uppercase;
    color: var(--texto-tenue) !important;
}}
[data-testid="stMetricValue"] {{
    font-variant-numeric: tabular-nums;
    font-weight: 700;
}}

/* ---------------- Pestañas ---------------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: .25rem;
    border-bottom: 1px solid var(--borde-suave);
    padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
    height: 44px;
    padding: 0 1.05rem;
    border-radius: 10px 10px 0 0;
    color: var(--texto-suave);
    font-weight: 550;
    font-size: .93rem;
    transition: color .18s ease, background .18s ease;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: var(--texto);
    background: rgba(76,141,255,.07);
}}
.stTabs [aria-selected="true"] {{ color: var(--acento-claro) !important; }}
.stTabs [data-baseweb="tab-highlight"] {{
    background: linear-gradient(90deg, var(--acento), var(--violeta));
    height: 2px;
}}
.stTabs [data-baseweb="tab-panel"] {{
    padding-top: 1.3rem;
    animation: aparecer .4s ease both;
}}

/* ---------------- Barra lateral ---------------- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0D1526, #0A0F1C);
    border-right: 1px solid var(--borde-suave);
}}
[data-testid="stSidebar"] .block-container {{ padding-top: 1.5rem; }}
.marca {{
    display: flex; align-items: center; gap: .68rem;
    padding-bottom: 1rem; margin-bottom: 1rem;
    border-bottom: 1px solid var(--borde-suave);
}}
.marca .glifo {{
    width: 38px; height: 38px; flex: 0 0 auto;
    display: grid; place-items: center;
    border-radius: 11px;
    background: linear-gradient(135deg, var(--acento), var(--violeta));
    color: white; font-weight: 700; font-size: .95rem;
    box-shadow: 0 6px 18px -8px rgba(76,141,255,.9);
}}
.marca .nombre {{ font-weight: 650; font-size: .98rem; line-height: 1.2; }}
.marca .sub {{ font-size: .74rem; color: var(--texto-tenue); }}

.lateral-dato {{
    display: flex; justify-content: space-between; align-items: baseline;
    gap: .6rem; padding: .4rem 0;
    border-bottom: 1px dashed var(--borde-suave);
    font-size: .83rem;
}}
.lateral-dato .clave {{ color: var(--texto-tenue); }}
.lateral-dato .valor {{ color: var(--texto); font-weight: 600; }}
.lateral-pie {{
    margin-top: 1.4rem; padding-top: .9rem;
    border-top: 1px solid var(--borde-suave);
    font-size: .74rem; color: var(--texto-tenue); line-height: 1.5;
}}

/* ---------------- Avisos ---------------- */
[data-testid="stAlert"] {{
    border-radius: 12px;
    border-left-width: 3px;
    animation: subir .4s ease both;
}}

/* ---------------- Tablas ---------------- */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--borde-suave);
}}

/* ---------------- Botones y campos ---------------- */
.stButton > button {{
    border-radius: 10px;
    border: 1px solid var(--borde);
    font-weight: 550;
    transition: transform .16s ease, border-color .16s ease, background .16s ease;
}}
.stButton > button:hover {{
    transform: translateY(-1px);
    border-color: var(--acento);
}}
[data-baseweb="select"] > div {{
    border-radius: 10px !important;
    border-color: var(--borde) !important;
}}

/* ---------------- Pie ---------------- */
.mlops-pie {{
    margin-top: 2.4rem; padding-top: 1rem;
    border-top: 1px solid var(--borde-suave);
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: .6rem;
    font-size: .76rem; color: var(--texto-tenue);
}}

/* ---------------- Animaciones ---------------- */
@keyframes subir {{
    from {{ opacity: 0; transform: translateY(12px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes aparecer {{
    from {{ opacity: 0; }}
    to   {{ opacity: 1; }}
}}
@keyframes barrido {{
    0%, 100% {{ background-position: 0% 50%; }}
    50%      {{ background-position: 100% 50%; }}
}}
@keyframes latido {{
    0%   {{ box-shadow: 0 0 0 0 color-mix(in srgb, var(--tono) 65%, transparent); }}
    70%  {{ box-shadow: 0 0 0 7px transparent; }}
    100% {{ box-shadow: 0 0 0 0 transparent; }}
}}

/* Quien pidió menos movimiento, menos movimiento recibe */
@media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: .01ms !important;
    }}
}}

/* Oculta el menú y la marca de agua para la vista de operación */
#MainMenu, footer {{ visibility: hidden; }}
"""


def inyectar_estilos():
    """Aplica la hoja de estilos. Debe llamarse una sola vez, al inicio."""
    st.markdown(f"<style>{_hoja()}</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Componentes
# --------------------------------------------------------------------------
def insignia(texto, tono="neutro", vivo=False):
    """Devuelve el HTML de una insignia con punto de color."""
    color = TONOS.get(tono, TONOS["neutro"])
    clase = "mlops-chip vivo" if vivo else "mlops-chip"
    return (f'<span class="{clase}" style="--tono:{color}">'
            f'<span class="punto"></span>{escape(str(texto))}</span>')


def encabezado(titulo, subtitulo, chips=()):
    """Bloque superior con el título del tablero y su estado resumido."""
    marcas = "".join(chips)
    st.markdown(
        f"""
        <div class="mlops-hero">
            <h1>{escape(titulo)}</h1>
            <p>{escape(subtitulo)}</p>
            <div class="mlops-chips">{marcas}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def fila_kpis(tarjetas):
    """Franja de indicadores. Cada tarjeta: rotulo, valor, pie y tono."""
    bloques = []
    for indice, tarjeta in enumerate(tarjetas):
        color = TONOS.get(tarjeta.get("tono", "neutro"), TONOS["neutro"])
        bloques.append(
            f'<div class="kpi" style="--i:{indice}; --tono:{color}">'
            f'<div class="rotulo">{escape(tarjeta["rotulo"])}</div>'
            f'<div class="valor">{escape(str(tarjeta["valor"]))}</div>'
            f'<div class="pie">{escape(str(tarjeta.get("pie", "")))}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="kpi-grid">{"".join(bloques)}</div>',
                unsafe_allow_html=True)


def titulo_seccion(indice, titulo, descripcion):
    """Encabezado numerado de sección, con su explicación de una línea."""
    st.markdown(
        f"""
        <div class="seccion">
            <div class="indice">{escape(str(indice))}</div>
            <div>
                <div class="titulo">{escape(titulo)}</div>
                <p class="descripcion">{escape(descripcion)}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dato_lateral(clave, valor):
    """Par clave-valor de la barra lateral."""
    st.markdown(
        f'<div class="lateral-dato"><span class="clave">{escape(clave)}</span>'
        f'<span class="valor">{escape(str(valor))}</span></div>',
        unsafe_allow_html=True,
    )


def marca_lateral(nombre, sub):
    """Identificador de la plataforma en la barra lateral."""
    st.markdown(
        f"""
        <div class="marca">
            <div class="glifo">ML</div>
            <div>
                <div class="nombre">{escape(nombre)}</div>
                <div class="sub">{escape(sub)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pie_pagina(izquierda, derecha):
    """Cierre del tablero con la procedencia de los datos."""
    st.markdown(
        f'<div class="mlops-pie"><span>{escape(izquierda)}</span>'
        f'<span>{escape(derecha)}</span></div>',
        unsafe_allow_html=True,
    )
