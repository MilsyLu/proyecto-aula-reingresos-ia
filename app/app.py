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

COORDINADOR = auth.es_coordinador()
INICIO = "Archivo y lista de llamadas" if COORDINADOR else "Estimar un paciente"

grupos = {
    "EMPEZAR AQUÍ": ["Qué es esto"],
    "TRABAJAR": ["Estimar un paciente"] + (["Archivo y lista de llamadas"] if COORDINADOR else []),
}
if COORDINADOR:
    grupos["CONOCER LOS DATOS"] = ["De dónde salen los datos"]
    grupos["CONOCER EL MODELO"] = [
        "Desempeño y métricas", "Equidad y límites", "Ficha del modelo"
    ]
    grupos["APRENDER HACIENDO"] = ["Entrene usted el modelo"]

paginas = [pagina for grupo in grupos.values() for pagina in grupo]
if st.session_state.get("reia_pagina") not in paginas:
    st.session_state["reia_pagina"] = INICIO


def mostrar_navegacion(prefijo):
    for titulo, opciones in grupos.items():
        st.markdown(f'<div class="reia-nav-titulo">{titulo}</div>', unsafe_allow_html=True)
        for opcion in opciones:
            if st.button(
                opcion,
                key=f"nav_{prefijo}_{opcion}",
                width="stretch",
                type="primary" if st.session_state["reia_pagina"] == opcion else "secondary",
            ):
                st.session_state["reia_pagina"] = opcion
                st.session_state["reia_menu_abierto"] = False
                st.rerun()


with st.sidebar:
    st.markdown("## ReingresaIA")
    st.caption("Riesgo de reingreso a 30 días")
    st.divider()
    mostrar_navegacion("escritorio")

nombre_rol = auth.NOMBRE_ROL.get(sesion["rol"], sesion["rol"])
with st.container(key="reia-mobile-topbar"):
    menu, encabezado = st.columns([1, 4], vertical_alignment="center")
    with menu:
        if st.button(
            "Cerrar" if st.session_state.get("reia_menu_abierto") else "Menú",
            key="alternar_menu_movil",
        ):
            st.session_state["reia_menu_abierto"] = not st.session_state.get(
                "reia_menu_abierto", False
            )
            st.rerun()
    with encabezado:
        st.markdown(
            '<div class="reia-topbar-marca">ReingresaIA</div>'
            '<div class="reia-topbar-subtitulo">Universidad Popular del Cesar · Grupo 04</div>',
            unsafe_allow_html=True,
        )

if st.session_state.get("reia_menu_abierto"):
    with st.container(key="reia-mobile-menu"):
        st.markdown(f"**{sesion.get('nombre', 'Usuario')}** · {nombre_rol}")
        if st.button("Cerrar sesión", key="cerrar_sesion_movil"):
            auth.cerrar()
            st.rerun()
        st.divider()
        mostrar_navegacion("movil")

with st.container(key="reia-desktop-topbar"):
    encabezado, usuario, salir = st.columns([6, 3, 1], vertical_alignment="center")
    with encabezado:
        st.markdown(
            '<div class="reia-topbar-marca">ReingresaIA</div>'
            '<div class="reia-topbar-subtitulo">Universidad Popular del Cesar · Grupo 04</div>',
            unsafe_allow_html=True,
        )
    with usuario:
        st.markdown(
            f'<div class="reia-usuario"><strong>{sesion.get("nombre", "Usuario")}</strong>'
            f'<span>{nombre_rol}</span></div>',
            unsafe_allow_html=True,
        )
    with salir:
        if st.button("Salir", key="cerrar_sesion"):
            auth.cerrar()
            st.rerun()

seleccion = st.session_state["reia_pagina"]

if seleccion == "Qué es esto":
    st.markdown("### Qué es esto y qué puede hacer")
    from paginas import ayuda_cliente
    ayuda_cliente.render()
elif seleccion == "Estimar un paciente":
    auth.exige("Estimar riesgo")
    from paginas import estimar
    estimar.render()
elif seleccion == "Archivo y lista de llamadas":
    auth.exige("Cargar archivo")
    st.markdown("### Del archivo a la lista de llamadas")
    st.caption("Cargue un corte de pacientes y ordénelos según la prioridad de seguimiento.")
    from paginas import lote
    lote.render()
elif seleccion == "De dónde salen los datos":
    auth.exige("Conocer los datos")
    st.markdown("### De dónde salen los datos")
    from paginas import exploracion
    exploracion.render()
elif seleccion == "Desempeño y métricas":
    auth.exige("Desempeño del modelo")
    st.markdown("### Desempeño y métricas")
    from paginas import desempeno
    desempeno.render()
elif seleccion == "Equidad y límites":
    auth.exige("Equidad y límites")
    st.markdown("### Equidad y límites")
    from paginas import equidad
    equidad.render()
elif seleccion == "Ficha del modelo":
    auth.exige("Ficha del modelo")
    st.markdown("### Ficha del modelo")
    from paginas import ficha
    ficha.render()
elif seleccion == "Entrene usted el modelo":
    auth.exige("Laboratorio de modelos")
    st.markdown("### Entrene usted el modelo")
    from paginas import laboratorio
    laboratorio.render()

st.caption(
    "Prototipo académico no validado para decisiones clínicas · "
    "No sustituye el criterio de profesionales de salud."
)
