# -*- coding: utf-8 -*-
"""Inicio de sesión y control de acceso por rol, sin Streamlit.

Reproduce la lógica de `app/auth.py`, que ya funciona y está probada, pero
desacoplada de Streamlit para que la pueda usar FastAPI. Se mantiene el mismo
archivo de usuarios y el mismo esquema de contraseñas: SHA-256 con sal por
usuario y comparación en tiempo constante.

El reparto de permisos cambió respecto a Streamlit, y el cambio es deliberado.
Antes el clínico veía menos. Ahora **ve todo el conocimiento**: los datos, las
métricas, la equidad, el techo, cómo se entrenó. Lo que queda reservado para la
coordinación son las tres palancas de operación: cargar archivos, fijar el
umbral y disparar un entrenamiento.

Esa división es la tesis del proyecto hecha software. El umbral es una decisión
de política sanitaria —cuánta gente alcanza a llamar el programa—, no un
cálculo clínico. Quien lo fija no es quien lo consume. Pero esconderle el
conocimiento al personal asistencial no tendría ninguna justificación.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import tomllib
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException, Request, status

BASE = Path(__file__).resolve().parent.parent
ARCHIVO_USUARIOS = BASE / "app" / "usuarios_demo.toml"

# Todo lo que sirve para entender: abierto a los dos roles.
CONOCIMIENTO = frozenset({
    "Guía",
    "Las 12 fases",
    "Estimar riesgo",
    "Paso a paso",
    "Asistente",
    "Conocer los datos",
    "Estadística descriptiva",
    "Mapa de calor",
    "Comparar modelos",
    "Desempeño",
    "Importancia",
    "Equidad",
    "Techo de los datos",
    "Ficha del modelo",
    "Recorrido grabado",
})

# El trabajo del dia a dia con pacientes concretos: tambien para los dos roles.
#
# Registrar a alguien para seguimiento y llamarlo es trabajo asistencial, no
# una decision de politica; y los reportes son conocimiento, que es lo que este
# proyecto decidio no esconderle a nadie. La division sigue intacta: lo
# reservado a coordinacion son las tres palancas de abajo.
ASISTENCIAL = frozenset({
    "Seguimiento",
    "Reportes",
    "Lista priorizada",
})

# Las palancas que mueven el programa: solo coordinación.
OPERACION = frozenset({
    "Cargar archivo",
    "Fijar umbral",
    "Entrenar en vivo",
})

PERMISOS: dict[str, frozenset[str]] = {
    "clinico": CONOCIMIENTO | ASISTENCIAL,
    "coordinador": CONOCIMIENTO | ASISTENCIAL | OPERACION,
}

NOMBRE_ROL = {
    "clinico": "Personal asistencial",
    "coordinador": "Coordinación del programa",
}


def _hash(contrasena: str, sal: str) -> str:
    return hashlib.sha256((sal + contrasena).encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _usuarios() -> dict[str, dict]:
    """Las cuentas del archivo de demostración.

    En producción se reemplazan con la variable de entorno REINGRESAIA_USUARIOS,
    que contiene el mismo TOML. Así no hay credenciales reales en el repositorio.
    """
    desde_entorno = os.environ.get("REINGRESAIA_USUARIOS")
    if desde_entorno:
        return tomllib.loads(desde_entorno)["usuarios"]
    return tomllib.loads(ARCHIVO_USUARIOS.read_text(encoding="utf-8"))["usuarios"]


def verificar(usuario: str, contrasena: str) -> dict | None:
    """Devuelve los datos de la cuenta si las credenciales son correctas."""
    cuenta = _usuarios().get(usuario.strip().lower())
    if not cuenta:
        # Se calcula un hash de todas formas: si no, el tiempo de respuesta
        # delata que el usuario no existe.
        _hash(contrasena, "sal_inexistente")
        return None
    if not hmac.compare_digest(cuenta.get("hash", ""), _hash(contrasena, cuenta.get("sal", ""))):
        return None
    rol = cuenta.get("rol", "clinico")
    return {
        "usuario": usuario.strip().lower(),
        "nombre": cuenta.get("nombre", usuario),
        "rol": rol,
        "permisos": sorted(PERMISOS.get(rol, frozenset())),
    }


def cuentas_demo() -> list[dict]:
    """Las credenciales de demostración, para mostrarlas en la pantalla de entrada.

    Solo aparecen las que traen `clave_demo`. Una cuenta real nunca la trae, así
    que en producción esta lista queda vacía sola.
    """
    return [
        {
            "usuario": nombre_usuario,
            "clave": cuenta["clave_demo"],
            "rol": NOMBRE_ROL.get(cuenta.get("rol", ""), cuenta.get("rol", "")),
        }
        for nombre_usuario, cuenta in _usuarios().items()
        if cuenta.get("clave_demo")
    ]


def sesion_de(peticion: Request) -> dict | None:
    datos = peticion.session.get("sesion")
    return datos if isinstance(datos, dict) else None


def exige_sesion(peticion: Request) -> dict:
    sesion = sesion_de(peticion)
    if not sesion:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Su sesión expiró. Vuelva a entrar.")
    return sesion


def exige(permiso: str):
    """Dependencia de FastAPI que cierra la puerta de una ruta.

    El front esconde los enlaces que el rol no puede abrir, pero eso es comodidad
    visual. La verificación de verdad ocurre aquí, en cada petición.
    """

    def verificador(peticion: Request) -> dict:
        sesion = exige_sesion(peticion)
        if permiso not in set(sesion.get("permisos", [])):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Su perfil no tiene acceso a esta sección. "
                "Si necesita entrar, pídale acceso a la coordinación del programa.",
            )
        return sesion

    return verificador
