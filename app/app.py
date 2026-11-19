# -*- coding: utf-8 -*-
"""Riesgo de reingreso hospitalario a 30 días — aplicación del Grupo 04.

Proyecto de aula de Inteligencia Artificial.
Universidad Popular del Cesar · Ingeniería de Sistemas · 2026.

Prototipo académico. No está validado para uso clínico.
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

AQUI = Path(__file__).resolve().parent
BASE = AQUI.parent
for ruta in (str(AQUI), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import auth                     # noqa: E402
import estilo                   # noqa: E402
from paginas import portada     # noqa: E402

st.set_page_config(page_title="Riesgo de reingreso a 30 días",
                   page_icon="🏥", layout="wide",
                   initial_sidebar_state="expanded")

# --------------------------------------------------------------- sin sesión
sesion = auth.sesion()
if not sesion:
    estilo.aplicar("portada")
    portada.render()
    st.stop()

# --------------------------------------------------------------- con sesión
estilo.aplicar("claro")

PAGINAS = [
    ("Estimar riesgo", "estimar"),
    ("Cargar archivo", "lote"),
    ("Laboratorio de modelos", "laboratorio"),
    ("Desempeño del modelo", "desempeno"),
    ("Equidad y límites", "equidad"),
    ("Ficha del modelo", "ficha"),
]
permitidas = auth.paginas_permitidas()
disponibles = [(etiqueta, modulo) for etiqueta, modulo in PAGINAS if etiqueta in permitidas]

with st.sidebar:
    st.markdown("### Reingresos a 30 días")
    st.caption("Proyecto de aula de IA · Grupo 04")
    st.markdown(
        f'<div class="tarjeta" style="padding:0.7rem 0.85rem;margin-top:0.6rem">'
        f'<div class="etiqueta">{auth.NOMBRE_ROL.get(sesion["rol"], sesion["rol"])}</div>'
        f'<div style="font-weight:600;margin-top:3px">{sesion["nombre"]}</div></div>',
        unsafe_allow_html=True)

    eleccion = st.radio("Secciones", [e for e, _ in disponibles],
                        label_visibility="collapsed")

    st.divider()
    if st.button("Cerrar sesión", width="stretch"):
        auth.cerrar()
        st.rerun()
    st.caption("Prototipo académico. No es una herramienta de decisión clínica.")

# la puerta de verdad: aunque alguien fuerce el valor, aquí se comprueba el rol
auth.exige(eleccion)
modulo = dict(disponibles)[eleccion]

if modulo == "estimar":
    from paginas import estimar
    estimar.render()
elif modulo == "lote":
    from paginas import lote
    lote.render()
elif modulo == "laboratorio":
    from paginas import laboratorio
    laboratorio.render()
elif modulo == "desempeno":
    from paginas import desempeno
    desempeno.render()
elif modulo == "equidad":
    from paginas import equidad
    equidad.render()
else:
    from paginas import ficha
    ficha.render()
