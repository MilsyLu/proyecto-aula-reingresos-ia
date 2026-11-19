# -*- coding: utf-8 -*-
"""Aplicación Streamlit: dos áreas simples, permisos por rol y módulos reutilizables.

La navegación principal funciona incluso con el panel lateral plegado.
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

# Usamos el estado de la sesión, no CSS display:none, para iniciar sin
# navegación en portada y permitir reabrir el panel dentro de la app.
sesion = auth.sesion()
st.set_page_config(
    page_title="Reingresos a 30 días | Grupo 04",
    page_icon="🏥", layout="wide",
    initial_sidebar_state="expanded" if sesion else "collapsed",
)

if not sesion:
    estilo.aplicar("portada")
    portada.render()
    st.stop()

estilo.aplicar("claro")

# Solo dos áreas principales. Las opciones especializadas viven dentro
# del área correspondiente, evitando una barra con seis pantallas sueltas.
CLIENTE = "Resultados para el cliente"
ADMIN = "Laboratorio y evaluación"
areas = [CLIENTE] + ([ADMIN] if auth.es_coordinador() else [])

with st.sidebar:
    st.markdown("### Proyecto Reingresos")
    st.caption("Inteligencia Artificial · Grupo 04")
    st.markdown(
        "**" + sesion.get("nombre", "Usuario") + "**"
    )
    st.caption(auth.NOMBRE_ROL.get(sesion["rol"], sesion["rol"]))
    st.divider()
    st.caption(
        "Puede cerrar este panel sin perder la navegación: "
        "las dos áreas están disponibles en la parte superior."
    )
    if st.button("Cerrar sesión", width="stretch", key="cerrar_sesion"):
        auth.cerrar()
        st.rerun()

st.caption("Predicción académica de reingresos hospitalarios a 30 días")
if len(areas) == 1:
    area = CLIENTE
else:
    area = st.segmented_control(
        "¿Qué desea consultar?",
        options=areas,
        default=CLIENTE,
        key="area_principal",
    )
    if area not in areas:
        area = CLIENTE

if area == CLIENTE:
    auth.exige("Estimar riesgo")
    st.markdown(
        "Consulte el riesgo estimado de una hospitalización. "
        "Los resultados se producen con el modelo oficial ya publicado."
    )
    cliente_opciones = ["Consultar un paciente"]
    if auth.es_coordinador():
        cliente_opciones.append("Procesar varios pacientes")
    if len(cliente_opciones) == 1:
        seleccion = cliente_opciones[0]
    else:
        seleccion = st.segmented_control(
            "Tipo de consulta", options=cliente_opciones,
            default=cliente_opciones[0], key="cliente_seccion",
        )
    if seleccion == "Procesar varios pacientes":
        auth.exige("Cargar archivo")
        from paginas import lote
        lote.render()
    else:
        from paginas import estimar
        estimar.render()
else:
    auth.exige("Laboratorio de modelos")
    st.markdown(
        "Esta área muestra cómo se procesan los datos, cómo se entrenan y "
        "comparan dos modelos, y qué evidencia respalda los resultados."
    )
    admin_opciones = [
        "Entrenar y comparar",
        "Resultados del modelo oficial",
        "Equidad y límites",
        "Cómo se construyó",
    ]
    seleccion = st.segmented_control(
        "Explorar el proceso", options=admin_opciones,
        default=admin_opciones[0], key="admin_seccion",
    )
    if seleccion == "Entrenar y comparar":
        from paginas import laboratorio
        laboratorio.render()
    elif seleccion == "Resultados del modelo oficial":
        auth.exige("Desempeño del modelo")
        from paginas import desempeno
        desempeno.render()
    elif seleccion == "Equidad y límites":
        auth.exige("Equidad y límites")
        from paginas import equidad
        equidad.render()
    else:
        auth.exige("Ficha del modelo")
        from paginas import ficha
        ficha.render()

st.divider()
st.caption(
    "Universidad Popular del Cesar · Grupo 04 · "
    "Prototipo académico: no validado para tomar decisiones clínicas."
)
