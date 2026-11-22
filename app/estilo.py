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

AZUL = "#252321"
TERRACOTA = "#B85A42"
TINTA = "#292724"
GRIS = "#77736F"
PAPEL = "#FBFAF8"
BORDE = "#E8E5E0"

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
  [data-testid="stHeader"] { background: transparent; pointer-events: none; }
  [data-testid="stSidebarCollapsedControl"] { display: flex !important; visibility: visible !important; }
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
      font-family: Inter, ui-sans-serif, system-ui, sans-serif;
      font-feature-settings: "tnum" on;
  }}
  /* Densidad. El criterio es el mismo de CheCu: que quepa en una pantalla,
     la informacion de un vistazo y el minimo de scroll. Todo lo de abajo
     aprieta el espaciado por defecto de Streamlit, que es muy generoso. */
  [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {{
      padding-top: 1.2rem;
      padding-bottom: 1.5rem;
      max-width: 1320px;
  }}
  [data-testid="stVerticalBlock"] {{ gap: 0.6rem; }}
  [data-testid="stHorizontalBlock"] {{ gap: 0.9rem; align-items: flex-start; }}

  /* Cabecera compacta, sin ocultar los controles de navegación de Streamlit. */
  [data-testid="stHeader"] {{ min-height: 3rem !important; }}
  /* Controles de las dos áreas principales y su subnavegación. */
  [data-testid="stSegmentedControl"] {{
      background: #FFFFFF; border: 1px solid {BORDE};
      border-radius: 13px; padding: 0.35rem; margin-bottom: 0.7rem;
  }}

  h1, h2, h3, [data-testid="stHeading"] h1,
  [data-testid="stHeading"] h2, [data-testid="stHeading"] h3 {{
      color: {AZUL}; font-family: Georgia, 'Times New Roman', serif !important;
      font-weight: 500; letter-spacing: -0.025em;
  }}
  h1 {{ font-size: 1.8rem; margin: 0 0 0.35rem; padding: 0; }}
  h2 {{ font-size: 1.35rem; margin: 0.7rem 0 0.25rem; padding: 0; }}
  h3 {{ font-size: 1.12rem; margin: 0.55rem 0 0.2rem; padding: 0; }}
  h4 {{ color: {AZUL}; font-family: Georgia, 'Times New Roman', serif !important;
       font-weight: 500; font-size: 1rem; letter-spacing: -0.01em;
       margin: 0.45rem 0 0.1rem; padding: 0; }}
  p {{ margin-bottom: 0.4rem; line-height: 1.45; }}
  hr {{ margin: 0.6rem 0; }}
  [data-testid="stCaptionContainer"] p {{ margin-bottom: 0.2rem; line-height: 1.35; }}

  /* tarjetas: borde fino, sin sombras pesadas */
  [data-testid="stMetric"], [data-testid="stForm"], [data-testid="stExpander"] {{
      background: #FFFFFF;
      border: 1px solid {BORDE};
      border-radius: 10px;
  }}
  [data-testid="stMetric"] {{ padding: 0.55rem 0.75rem; }}
  [data-testid="stForm"] {{ padding: 0.8rem 0.9rem; }}
  [data-testid="stExpander"] details > summary {{ padding: 0.4rem 0.75rem; font-size: 0.86rem; }}
  [data-testid="stMetricValue"] {{ color: {AZUL}; font-weight: 600; font-size: 1.5rem; }}
  [data-testid="stMetricLabel"] {{ color: {GRIS}; font-size: 0.74rem; }}
  [data-testid="stMetricDelta"] {{ font-size: 0.72rem; }}

  /* controles mas bajos: en un formulario de 15 campos esto solo ahorra pantalla */
  [data-testid="stNumberInput"] input, [data-testid="stSelectbox"] div[role="combobox"] {{
      padding-top: 0.25rem !important; padding-bottom: 0.25rem !important;
      font-size: 0.86rem !important;
  }}
  [data-testid="stWidgetLabel"] p {{ font-size: 0.78rem; margin-bottom: 0.1rem; }}
  [data-testid="stTabs"] button {{ padding: 0.3rem 0.7rem; font-size: 0.88rem; }}

  /* Las dos reglas de la barra lateral (esta y la de la portada) estan
     condicionadas a si el vídeo de la portada esta o no en la pagina. Asi da
     igual que Streamlit deje un bloque de estilos viejo pegado: la regla que
     manda es siempre la que corresponde a lo que hay en pantalla. */
  body:not(:has(#fondo-video)) [data-testid="stSidebar"] {{
      display: flex !important;
      visibility: visible !important;
      min-width: 272px !important;
      transform: none !important;
  }}
  [data-testid="stSidebar"] {{
      background: #FFFFFF;
      border-right: 1px solid {BORDE};
  }}
  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {{
      font-family: Georgia, 'Times New Roman', serif;
      font-size: 1.3rem; font-weight: 500; letter-spacing: -0.02em;
  }}
  [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 0.3rem; }}
  [data-testid="stSidebar"] [data-testid="stButton"] button {{
      border: 0; border-radius: 7px; justify-content: flex-start;
      min-height: 2.15rem; padding: 0.35rem 0.55rem;
      color: {GRIS}; background: transparent; font-size: 0.88rem;
      font-weight: 450; text-align: left;
  }}
  [data-testid="stSidebar"] [data-testid="stButton"] button:hover {{
      background: #F4F2EF; color: {TINTA}; border: 0;
  }}
  [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
      background: #F1EFEC; color: {TINTA}; font-weight: 650;
  }}
  .reia-nav-titulo {{
      color: #96918A; font-size: 0.65rem; letter-spacing: 0.15em;
      font-weight: 650; margin: 0.8rem 0 0.2rem;
  }}

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

  /* Encabezado ReingresaIA sin saturar las pantallas interiores. */
  .reia-topbar-marca {{
      color: {AZUL}; font-family: Georgia, 'Times New Roman', serif;
      font-size: 1.35rem; font-weight: 500; letter-spacing: -0.025em;
  }}
  .reia-topbar-subtitulo {{ color: {GRIS}; font-size: 0.72rem; margin-top: 0.1rem; }}
  .reia-usuario {{ text-align: right; line-height: 1.35; font-size: 0.78rem; }}
  .reia-usuario strong, .reia-usuario span {{ display: block; }}
  .reia-usuario span {{ color: {GRIS}; font-size: 0.7rem; }}
  .st-key-reia-mobile-topbar, .st-key-reia-mobile-menu {{ display: none; }}
  .st-key-reia-desktop-topbar [data-testid="stHorizontalBlock"] {{
      padding: 0.2rem 0 0.75rem; border-bottom: 1px solid {BORDE};
      margin-bottom: 1.1rem; align-items: center;
  }}
  @media (max-width: 767px) {{
      body:not(:has(#fondo-video)) [data-testid="stSidebar"] {{ display: none !important; }}
      .st-key-reia-desktop-topbar {{ display: none !important; }}
      .st-key-reia-mobile-topbar {{
          display: block !important; padding: 0.15rem 0 0.7rem;
          border-bottom: 1px solid {BORDE}; margin-bottom: 1rem;
      }}
      .st-key-reia-mobile-menu {{
          display: block !important; max-height: 62vh; overflow-y: auto;
          background: #FFFFFF; border: 1px solid {BORDE};
          border-radius: 12px; padding: 0.8rem; margin-bottom: 1rem;
      }}
      .st-key-reia-mobile-menu [data-testid="stButton"] button {{
          justify-content: flex-start; text-align: left; border: 0 !important;
          border-radius: 7px; background: transparent; color: {GRIS};
          font-weight: 450;
      }}
      .st-key-reia-mobile-menu [data-testid="stButton"] button p {{ text-align: left; }}
      .st-key-reia-mobile-menu [data-testid="stBaseButton-primary"] {{
          background: #F1EFEC !important; color: {TINTA} !important; font-weight: 650;
      }}
      [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {{
          padding: 0.65rem 0.85rem 1rem !important;
      }}
      .reia-topbar-subtitulo {{ font-size: 0.62rem; }}
  }}
  /* Los paneles y los bloques de preguntas deben ser legibles en móvil. */
  [data-testid="stSegmentedControl"] button {{ border-radius: 9px; }}
  [data-testid="stTabs"] button {{ font-size: 0.9rem; }}
  [data-testid="stSidebarCollapsedControl"] {{
      visibility: visible !important; display: flex !important;
  }}

  /* el aviso de prototipo: visible pero sin gritar */
  .aviso-prototipo {{
      background: #FFF8F2;
      border-left: 3px solid {TERRACOTA};
      border-radius: 8px;
      padding: 0.5rem 0.75rem;
      font-size: 0.82rem;
      line-height: 1.4;
      color: #6B3A24;
      margin-bottom: 0.5rem;
  }}

  .tarjeta {{
      background: #FFFFFF;
      border: 1px solid {BORDE};
      border-radius: 10px;
      padding: 0.7rem 0.85rem;
      margin-bottom: 0.5rem;
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
  /* La barra lateral se tapa con una regla condicionada a la portada,
     nunca con un display:none suelto que luego no se puede revertir. */
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
  body:has(#fondo-video) [data-testid="stSidebar"],
  body:has(#fondo-video) [data-testid="stSidebarCollapsedControl"] {{
      display: none !important;
  }}

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
  /* el boton de mostrar la contrasena quedaba gris oscuro sobre fondo oscuro */
  [data-testid="stForm"] [data-testid="stIconMaterial"],
  [data-testid="stTextInputRootElement"] button,
  [data-testid="stTextInputRootElement"] svg {{
      color: #c7c8da !important;
      fill: #c7c8da !important;
      opacity: 1 !important;
  }}
  [data-testid="stTextInputRootElement"] button {{
      background: transparent !important;
      border: none !important;
  }}
  [data-testid="stTextInputRootElement"] button:hover [data-testid="stIconMaterial"] {{
      color: #FFFFFF !important;
  }}

  .pie-portada {{
      color: #8a8ca0; font-size: 0.78rem; margin-top: 1.5rem; line-height: 1.6;
  }}
  .pie-portada b {{ color: #d3d4e2; font-weight: 600;
      display: block; margin-bottom: 0.55rem; letter-spacing: 0.01em; }}
  .cuenta-demo {{
      border: 1px solid #2f2e56; border-radius: 12px;
      padding: 0.55rem 0.75rem; margin-bottom: 0.5rem;
      background: rgba(12,10,43,0.55);
  }}
  .cuenta-rol {{
      color: #9b9ba4; font-size: 0.68rem; text-transform: uppercase;
      letter-spacing: 0.09em; font-weight: 600; margin-bottom: 0.3rem;
  }}
  .cuenta-demo span {{ display: inline-block; min-width: 78px; color: #8a8ca0; }}
  .cuenta-demo code {{
      color: #FFFFFF; background: rgba(255,255,255,0.08);
      border-radius: 5px; padding: 1px 7px; font-size: 0.78rem;
  }}
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
