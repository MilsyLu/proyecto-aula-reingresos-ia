# -*- coding: utf-8 -*-
"""Inicio de sesión y control de acceso por rol.

Los dos roles no son decorativos: reproducen la tesis del proyecto. El umbral de
alerta es una decisión de política sanitaria, no un cálculo clínico, así que quien
lo fija (el coordinador) no es quien lo consume (el personal asistencial).

Las contraseñas se guardan con hash SHA-256 y sal por usuario; nunca en claro.
Para un prototipo académico esto es suficiente. Un sistema real usaría el
directorio de la institución y un segundo factor.
"""
from __future__ import annotations

import hashlib
import hmac
import tomllib
from pathlib import Path

import streamlit as st

ARCHIVO_DEMO = Path(__file__).resolve().parent / "usuarios_demo.toml"

PERMISOS = {
    "clinico": {
        "Estimar riesgo", "Ficha del modelo",
    },
    "coordinador": {
        "Estimar riesgo", "Cargar archivo", "Conocer los datos",
        "Desempeño del modelo", "Equidad y límites", "Ficha del modelo",
        "Laboratorio de modelos",
    },
}

NOMBRE_ROL = {"clinico": "Personal asistencial", "coordinador": "Coordinación del programa"}


def _hash(contrasena: str, sal: str) -> str:
    return hashlib.sha256((sal + contrasena).encode("utf-8")).hexdigest()


@st.cache_data(show_spinner=False)
def _usuarios():
    """Usuarios de `st.secrets` si existen; si no, los de demostración.

    En Streamlit Cloud basta con pegar una sección [usuarios] en los secretos de
    la aplicación para reemplazar las cuentas de demostración por las reales.
    """
    try:
        if "usuarios" in st.secrets:
            return {clave: dict(valor) for clave, valor in st.secrets["usuarios"].items()}
    except Exception:
        pass
    return tomllib.loads(ARCHIVO_DEMO.read_text(encoding="utf-8"))["usuarios"]


def verificar(usuario: str, contrasena: str):
    """Devuelve los datos del usuario si las credenciales son correctas."""
    cuenta = _usuarios().get(usuario.strip().lower())
    if not cuenta:
        return None
    esperado = cuenta.get("hash", "")
    calculado = _hash(contrasena, cuenta.get("sal", ""))
    # comparación en tiempo constante: no revela cuánto coincide
    if not hmac.compare_digest(esperado, calculado):
        return None
    return {"usuario": usuario.strip().lower(),
            "nombre": cuenta.get("nombre", usuario),
            "rol": cuenta.get("rol", "clinico")}


def sesion():
    return st.session_state.get("sesion")


def iniciar(datos):
    st.session_state["sesion"] = datos


def cerrar():
    for clave in ("sesion", "lote_resultado", "lab_resultado", "lab_datos", "lab_etapa", "lab_firma_archivo", "ultima_estimacion", "conversacion"):
        st.session_state.pop(clave, None)


def paginas_permitidas():
    """Páginas que el rol de la sesión actual puede abrir."""
    activa = sesion()
    if not activa:
        return set()
    return PERMISOS.get(activa["rol"], set())


def exige(pagina: str) -> bool:
    """Puerta de entrada de cada página. Devuelve False si el rol no alcanza."""
    if pagina not in paginas_permitidas():
        st.error("Su perfil no tiene acceso a esta sección.")
        st.caption("Si necesita entrar, pídale acceso a la coordinación del programa.")
        st.stop()
    return True


def es_coordinador() -> bool:
    activa = sesion()
    return bool(activa) and activa["rol"] == "coordinador"
