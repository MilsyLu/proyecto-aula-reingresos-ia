# -*- coding: utf-8 -*-
"""ReingresaIA: experiencia de predicción y laboratorio de IA.

Solo existen dos áreas principales. Los componentes de entrenamiento y
predicción se mantienen separados y protegidos por los roles existentes.
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

import auth  # noqa: E402
import estilo  # noqa: E402
from paginas import portada  # noqa: E402

# La barra lateral siempre nace expandida. Plegarla en la portada con
# `initial_sidebar_state="collapsed"` no funciona: Streamlit solo aplica ese
# estado en la primera carga, así que al iniciar sesión se quedaba plegada en
# un píxel y sin botón para abrirla. En la portada la tapa una regla de CSS
# condicionada a que el vídeo esté en la página (ver estilo.py).
st.set_page_config(
    page_title="ReingresaIA | Riesgo de reingreso a 30 días",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

sesion = auth.sesion()

if not sesion:
    estilo.aplicar("portada")
    portada.render()
    st.stop()

estilo.aplicar("claro")

CLIENTE = "Predicción de riesgo"
ADMIN = "Laboratorio de IA"
areas = [CLIENTE] + ([ADMIN] if auth.es_coordinador() else [])

with st.sidebar:
    st.markdown("## 🏥 ReingresaIA")
    st.caption("Predicción de reingresos a 30 días")
    st.divider()
    st.caption("SESIÓN ACTIVA")
    st.markdown("**" + sesion.get("nombre", "Usuario") + "**")
    st.caption(auth.NOMBRE_ROL.get(sesion["rol"], sesion["rol"]))
    st.divider()
    st.caption("La navegación principal permanece arriba aunque cierre este panel.")
    if st.button("Cerrar sesión", width="stretch", key="cerrar_sesion"):
        auth.cerrar()
        st.rerun()

st.markdown(
    '<div class="reia-encabezado">'
    '<div class="reia-marca">REINGRESAIA · GRUPO 04</div>'
    '<div class="reia-subtitulo">Análisis inteligente de reingresos hospitalarios a 30 días</div>'
    '</div>',
    unsafe_allow_html=True,
)
if len(areas) == 1:
    area = CLIENTE
else:
    area = st.segmented_control(
        "Área de trabajo", options=areas, default=CLIENTE,
        key="area_principal",
    ) or CLIENTE
    if area not in areas:
        area = CLIENTE

if area == CLIENTE:
    auth.exige("Estimar riesgo")
    st.markdown("### Predicción de riesgo")
    st.caption(
        "Consulte una hospitalización y obtenga una estimación comprensible. "
        "Se utiliza el modelo oficial previamente entrenado."
    )
    opciones = ["Consultar paciente"]
    if auth.es_coordinador():
        opciones.append("Analizar archivo CSV")
    opciones.append("Sobre el modelo")
    seleccion = st.segmented_control(
        "¿Qué necesita hacer?", options=opciones, default=opciones[0],
        key="cliente_seccion",
    ) or opciones[0]

    if seleccion == "Analizar archivo CSV":
        auth.exige("Cargar archivo")
        from paginas import lote
        lote.render()
    elif seleccion == "Sobre el modelo":
        auth.exige("Ficha del modelo")
        from paginas import ayuda_cliente
        ayuda_cliente.render()
    else:
        from paginas import estimar
        estimar.render()
else:
    auth.exige("Laboratorio de modelos")
    st.markdown("### Laboratorio de IA")
    st.caption(
        "Explore los datos, entrene Gradient Boosting y una red neuronal, "
        "compare sus resultados y comprenda cuál se recomienda."
    )
    opciones = ["Experimento guiado", "Evidencia del proyecto"]
    seleccion = st.segmented_control(
        "Contenido del laboratorio", options=opciones,
        default=opciones[0], key="admin_seccion",
    ) or opciones[0]

    if seleccion == "Experimento guiado":
        from paginas import laboratorio
        laboratorio.render()
    else:
        t0, t1, t2, t3 = st.tabs([
            "Los datos", "Modelo oficial", "Equidad y límites", "Metodología"
        ])
        with t0:
            auth.exige("Conocer los datos")
            from paginas import exploracion
            exploracion.render()
        with t1:
            auth.exige("Desempeño del modelo")
            from paginas import desempeno
            desempeno.render()
        with t2:
            auth.exige("Equidad y límites")
            from paginas import equidad
            equidad.render()
        with t3:
            auth.exige("Ficha del modelo")
            from paginas import ficha
            ficha.render()

st.caption(
    "Universidad Popular del Cesar · Proyecto académico. "
    "Prototipo no validado para decisiones clínicas."
)
