# -*- coding: utf-8 -*-
"""Información para la persona que consulta un riesgo, sin métricas de laboratorio."""
from __future__ import annotations

import streamlit as st


def render():
    st.subheader("Entender la predicción")
    st.markdown(
        "ReingresaIA estima el **riesgo de reingreso hospitalario antes "
        "de 30 días** después de una hospitalización, utilizando "
        "los datos registrados durante la atención."
    )
    st.markdown("#### ¿Cómo interpretar el resultado?")
    a, b = st.columns(2)
    with a:
        st.markdown("**Probabilidad estimada**")
        st.write(
            "Es una puntuación de riesgo calculada por el modelo a partir "
            "de los datos ingresados. No es una certeza ni un diagnóstico."
        )
    with b:
        st.markdown("**Alerta de seguimiento**")
        st.write(
            "Se genera cuando la estimación alcanza el umbral elegido por "
            "el proyecto. Sirve para organizar prioridades, no para "
            "decidir automáticamente una intervención."
        )

    st.markdown("#### ¿Qué puede hacer aquí?")
    st.markdown(
        "En **Consultar paciente** puede completar el formulario y "
        "consultar la estimación. La coordinación también dispone de "
        "**Analizar archivo CSV** para priorizar varios registros."
    )
    with st.expander("Preguntas frecuentes"):
        st.markdown(
            "**¿Una alerta significa que el paciente regresará?** No. "
            "Solo indica un riesgo estimado elevado según el umbral.\n\n"
            "**¿De dónde viene el modelo?** De un proyecto académico "
            "entrenado con hospitalizaciones históricas de pacientes "
            "con diabetes en Estados Unidos (1999–2008).\n\n"
            "**¿Se entrena nuevamente al consultar un paciente?** No. "
            "La consulta utiliza el Gradient Boosting oficial previamente "
            "entrenado y guardado.\n\n"
            "**¿Por qué no veo todas las métricas del algoritmo?** "
            "Esos detalles se explican en el Laboratorio de IA, "
            "disponible para el perfil coordinador."
        )
    st.warning(
        "Prototipo académico no validado para uso clínico. "
        "No sustituye el criterio de profesionales de salud."
    )
