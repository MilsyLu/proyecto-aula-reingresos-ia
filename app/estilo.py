# -*- coding: utf-8 -*-
"""Hoja de estilos de la aplicación.

Dos temas: la portada es oscura y cinematográfica, el interior es claro y legible.
La razón no es capricho. En la portada no hay controles que leer, así que puede
permitirse el efecto; adentro se trabaja con cifras y el contraste alto gana.

Advertencia para quien mantenga esto: Streamlit no ofrece una API de estilos, de
modo que el CSS se apoya en atributos `data-testid`. Son más estables que los
nombres de clase, pero siguen siendo internos y pueden cambiar al actualizar
Streamlit. Si un día la aplicación se ve rara, el sospechoso es este archivo.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).resolve().parent / "assets"

AZUL = "#1F3B63"
TERRACOTA = "#C25A3C"
TINTA = "#15202B"
GRIS = "#5A6472"
PAPEL = "#F4F6F9"
BORDE = "#E3E8EF"

NOCHE = "#04061c"
NOCHE_CARTA = "#0c0a2b"
NOCHE_BORDE = "#292a4d"
NOCHE_TEXTO = "#b4b4bb"
BRASA = "linear-gradient(135deg, #ff8a76 0%, #ff3a63 100%)"


@lru_cache(maxsize=4)
def _incrustar(nombre: str) -> str:
    """Devuelve el archivo en base64 para meterlo dentro del HTML.

    Streamlit no sirve archivos estáticos sin configuración extra, y un `<video
    src="...">` apuntando a disco no cargaría. Incrustarlo evita todo eso: el
    vídeo pesa 578 KB, un tamaño razonable para una portada.
    """
    ruta = ASSETS / nombre
    if not ruta.exists():
        return ""
    return base64.b64encode(ruta.read_bytes()).decode("ascii")


OCULTAR_CROMO = """
<style>
  [data-testid="stHeader"] { background: transparent; height: 0; }
  [data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer { display: none; }
  [data-testid="stMain"] { padding-top: 0; }
</style>
"""


def _tema_claro() -> str:
    return f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
      background: {PAPEL};
      color: {TINTA};
      font-feature-settings: "tnum" on;
  }}
  [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {{ padding-top: 2.2rem; max-width: 1180px; }}

  h1 {{ color: {AZUL}; font-weight: 700; letter-spacing: -0.015em; font-size: 2.0rem; }}
  h2 {{ color: {AZUL}; font-weight: 600; font-size: 1.35rem; margin-top: 1.6rem; }}
  h3, h4 {{ color: {AZUL}; font-weight: 600; }}

  /* tarjetas: borde fino, sin sombras pesadas */
  [data-testid="stMetric"], [data-testid="stForm"], [data-testid="stExpander"] {{
      background: #FFFFFF;
      border: 1px solid {BORDE};
      border-radius: 12px;
      padding: 1rem 1.15rem;
  }}
  [data-testid="stMetricValue"] {{ color: {AZUL}; font-weight: 600; }}
  [data-testid="stMetricLabel"] {{ color: {GRIS}; font-size: 0.82rem; }}

  [data-testid="stSidebar"] {{
      background: #FFFFFF;
      border-right: 1px solid {BORDE};
  }}
  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{ font-size: 1.05rem; }}

  .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {{
      border-radius: 10px;
      border: 1px solid {AZUL};
      font-weight: 600;
  }}
  [data-testid="stFormSubmitButton"] > button {{
      background: {AZUL};
      color: #FFFFFF;
  }}

  [data-testid="stDataFrame"], [data-testid="stTable"] {{
      border: 1px solid {BORDE};
      border-radius: 10px;
      overflow: hidden;
  }}

  /* el aviso de prototipo: visible pero sin gritar */
  .aviso-prototipo {{
      background: #FFF8F2;
      border-left: 3px solid {TERRACOTA};
      border-radius: 8px;
      padding: 0.7rem 0.9rem;
      font-size: 0.86rem;
      color: #6B3A24;
      margin-bottom: 1rem;
  }}

  .tarjeta {{
      background: #FFFFFF;
      border: 1px solid {BORDE};
      border-radius: 12px;
      padding: 1.1rem 1.25rem;
      margin-bottom: 0.9rem;
  }}
  .etiqueta {{
      color: {GRIS};
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600;
  }}
</style>
"""


def _tema_portada() -> str:
    video = _incrustar("portada.mp4")
    poster = _incrustar("portada.jpg")
    fuente = (f'<source src="data:video/mp4;base64,{video}" type="video/mp4">'
              if video else "")
    cartel = f'poster="data:image/jpeg;base64,{poster}"' if poster else ""
    return f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
      background: {NOCHE};
      color: #FFFFFF;
  }}
  [data-testid="stSidebar"] {{ display: none; }}
  /* Streamlit pone sus propias reglas con mas peso: hay que insistir */
  [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {{
      max-width: 430px !important;
      margin-left: max(6vw, 1.5rem) !important;
      margin-right: auto !important;
      padding-top: 8vh !important;
      padding-bottom: 4vh !important;
      position: relative;
      z-index: 2;
  }}

  /* z-index negativo: Streamlit mete este bloque DENTRO del contenedor del
     contenido, y un elemento posicionado con z-index >= 0 se pintaria encima
     del formulario. En negativo queda detras, que es donde debe estar. */
  #fondo-video {{
      position: fixed; inset: 0; z-index: -2; overflow: hidden;
  }}
  #fondo-video video {{
      width: 100%; height: 100%; object-fit: cover;
      filter: saturate(0.92) contrast(1.05) brightness(1.02);
  }}
  /* oscuro donde va el texto, casi limpio donde se ve el video */
  #velo {{
      position: fixed; inset: 0; z-index: -1;
      background:
        linear-gradient(90deg,
          rgba(4,6,28,0.985) 0%,
          rgba(4,6,28,0.955) 24%,
          rgba(4,6,28,0.78) 40%,
          rgba(4,6,28,0.34) 64%,
          rgba(4,6,28,0.18) 100%),
        linear-gradient(180deg,
          rgba(4,6,28,0.45) 0%,
          rgba(4,6,28,0.00) 42%,
          rgba(4,6,28,0.45) 100%);
  }}
  @media (max-width: 860px) {{
      #velo {{ background: rgba(4,6,28,0.95); }}
      [data-testid="stMainBlockContainer"], [data-testid="stMainBlockContainer"] {{ margin-left: auto !important; max-width: 430px !important; }}
  }}

  .marca {{
      color: #FFFFFF; font-size: 2.4rem; font-weight: 700;
      line-height: 1.1; letter-spacing: -0.025em; margin-bottom: 0.35rem;
      text-shadow: 0 2px 24px rgba(0,0,0,0.85);
  }}
  .marca small {{
      display: block; color: #d3d4e2; font-size: 0.92rem;
      font-weight: 400; letter-spacing: 0.01em; margin-top: 0.6rem;
  }}
  .insignia {{
      display: inline-block; border: 1px solid {NOCHE_BORDE};
      background: rgba(12,10,43,0.55); border-radius: 30px;
      padding: 4px 13px; font-size: 0.74rem; color: {NOCHE_TEXTO};
      letter-spacing: 0.04em; margin-bottom: 1.1rem;
  }}

  [data-testid="stForm"] {{
      background: rgba(23,21,60,0.95);
      border: 1px solid #3b3a6b;
      border-radius: 20px;
      padding: 1.5rem 1.4rem 1.2rem;
      box-shadow: 0 18px 50px rgba(0,0,0,0.55);
  }}
  [data-testid="stForm"] label, [data-testid="stForm"] p {{ color: {NOCHE_TEXTO} !important; }}
  [data-testid="stForm"] label, [data-testid="stForm"] label p {{
      color: #cdcee0 !important; font-weight: 500;
  }}
  [data-testid="stForm"] input {{
      background: #0e0d24 !important;
      color: #FFFFFF !important;
      border: 1px solid #4a4878 !important;
      border-radius: 9px !important;
  }}
  [data-testid="stTextInputRootElement"] {{
      background: #0e0d24 !important;
      border: 1px solid #4a4878 !important;
      border-radius: 9px !important;
  }}
  [data-testid="stFormSubmitButton"] > button {{
      background: {BRASA};
      border: none; color: #FFFFFF; font-weight: 600;
      border-radius: 30px; padding: 0.55rem 1.3rem; width: 100%;
  }}
  .pie-portada {{
      color: #6f7183; font-size: 0.76rem; margin-top: 1.4rem; line-height: 1.6;
  }}
  .pie-portada b {{ color: {NOCHE_TEXTO}; font-weight: 500; }}
</style>
<div id="fondo-video">
  <video autoplay muted loop playsinline {cartel}>{fuente}</video>
</div>
<div id="velo"></div>
"""


def aplicar(tema: str):
    """`tema` es 'portada' o 'claro'."""
    st.markdown(OCULTAR_CROMO, unsafe_allow_html=True)
    st.markdown(_tema_portada() if tema == "portada" else _tema_claro(),
                unsafe_allow_html=True)


def aviso_prototipo(texto: str):
    st.markdown(f'<div class="aviso-prototipo">{texto}</div>', unsafe_allow_html=True)
