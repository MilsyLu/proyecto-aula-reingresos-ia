# -*- coding: utf-8 -*-
"""Portada e inicio de sesión."""
from __future__ import annotations

import tomllib
from pathlib import Path

import streamlit as st

from auth import ARCHIVO_DEMO, iniciar, verificar


def _cuentas_demo():
    try:
        datos = tomllib.loads(Path(ARCHIVO_DEMO).read_text(encoding="utf-8"))["usuarios"]
    except Exception:
        return []
    return [(u, c.get("clave_demo"), c.get("rol")) for u, c in datos.items()
            if c.get("clave_demo")]


def render():
    st.markdown(
        '<div class="insignia">Universidad Popular del Cesar · Grupo 04</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div class="marca">Riesgo de reingreso<br>a 30 días'
        '<small>Priorización del seguimiento al alta en pacientes diabéticos</small></div>',
        unsafe_allow_html=True)

    with st.form("entrar"):
        usuario = st.text_input("Usuario", placeholder="su usuario")
        clave = st.text_input("Contraseña", type="password", placeholder="••••••••")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        datos = verificar(usuario, clave)
        if datos:
            iniciar(datos)
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

    demo = _cuentas_demo()
    if demo:
        filas = "<br>".join(
            f"<b>{u}</b> / {c} &nbsp;·&nbsp; {'coordinación' if r == 'coordinador' else 'asistencial'}"
            for u, c, r in demo)
        st.markdown(
            f'<div class="pie-portada">Cuentas de demostración<br>{filas}'
            '<br><br>Prototipo académico. No es una herramienta de decisión clínica '
            'y no contiene datos de pacientes reales.</div>',
            unsafe_allow_html=True)
