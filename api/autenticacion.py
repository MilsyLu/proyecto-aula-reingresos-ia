# -*- coding: utf-8 -*-
"""Autenticación y permisos por rol para la plataforma ReingresaIA.

El personal asistencial solo utiliza predicción, gestión de pacientes y agenda.
Coordinación conserva esas funciones y accede además a operación, evaluación
y laboratorio. Todos los permisos se verifican en la API, no solo en el menú.
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

# Solo funciones operativas para el personal asistencial.
ASISTENCIAL = frozenset({
    "Guía", "Estimar riesgo", "Seguimiento", "Asistente",
})

# La coordinación puede cargar archivos, generar reportes, cambiar el umbral y
# acceder a las evidencias de desarrollo y al entrenamiento experimental.
ADMINISTRACION = frozenset({
    "Cargar archivo", "Fijar umbral", "Reportes", "Lista priorizada",
})
LABORATORIO = frozenset({
    "Las 12 fases", "Paso a paso", "Asistente", "Conocer los datos",
    "Estadística descriptiva", "Mapa de calor", "Comparar modelos",
    "Desempeño", "Importancia", "Equidad", "Techo de los datos",
    "Ficha del modelo", "Recorrido grabado", "Entrenar en vivo",
})

PERMISOS: dict[str, frozenset[str]] = {
    "clinico": ASISTENCIAL,
    "coordinador": ASISTENCIAL | ADMINISTRACION | LABORATORIO,
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
