# -*- coding: utf-8 -*-
"""El asistente: traduce el resultado del modelo a lenguaje corriente.

Toda la lógica de Gemini vive en `app/asistente.py`, compartida con la
aplicación de Streamlit. Aquí solo se expone por HTTP.

Lo que se le manda al modelo de lenguaje es el resultado y las limitaciones
medidas del modelo, nunca datos que identifiquen a un paciente. En esta
aplicación no existen, pero la regla queda escrita para cuando alguien conecte
datos reales.

La clave no se lee aquí ni se escribe en ningún archivo: la toma `app/asistente.py`
de la variable de entorno GEMINI_API_KEY o de los secretos, y no aparece en
ninguna respuesta, ni siquiera dentro de un mensaje de error.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import asistente as motor  # noqa: E402

from api import autenticacion as auth  # noqa: E402

# Una pregunta cada cuatro segundos por sesión. No es para castigar a nadie:
# cada pregunta es una llamada a un servicio externo con cuota, y un dedo
# nervioso sobre el botón puede agotarla en una tarde.
ESPERA_MINIMA = 4.0
_ultima: dict[str, float] = {}


class Efecto(BaseModel):
    nombre: str
    valor: str
    tipico: str
    efecto: float
    riesgo_sin_el: float


class Consulta(BaseModel):
    pregunta: str = Field(min_length=2, max_length=600)
    riesgo: float = Field(ge=0, le=1)
    umbral: float = Field(ge=0, le=1)
    efectos: list[Efecto] = Field(default_factory=list, max_length=15)


def estado(_=Depends(auth.exige("Asistente"))):
    """Si el asistente puede responder, y qué sugerir mientras tanto."""
    return {
        "disponible": motor.disponible(),
        "sugerencias": motor.SUGERENCIAS,
    }


def preguntar(consulta: Consulta, peticion: Request, sesion=Depends(auth.exige("Asistente"))):
    usuario = str(sesion.get("usuario", "anonimo"))
    ahora = time.monotonic()
    desde = ahora - _ultima.get(usuario, 0.0)
    if desde < ESPERA_MINIMA:
        raise HTTPException(
            429,
            f"Espere {ESPERA_MINIMA - desde:.0f} segundos antes de volver a preguntar.",
        )
    _ultima[usuario] = ahora

    if not motor.disponible():
        raise HTTPException(
            503,
            "El asistente no está configurado en este servidor. El resto de la "
            "aplicación funciona igual.",
        )

    estimacion = {
        "riesgo": consulta.riesgo,
        "umbral": consulta.umbral,
        "efectos": [e.model_dump() for e in consulta.efectos],
    }
    hubo, texto = motor.responder(estimacion, consulta.pregunta)
    if not hubo:
        # `texto` viene de app/asistente.py y solo trae el código del error,
        # nunca el cuerpo de la respuesta de Gemini, que a veces repite la clave.
        raise HTTPException(502, texto)
    return {"respuesta": texto}


def registrar(app: FastAPI) -> None:
    app.get("/api/asistente")(estado)
    app.post("/api/asistente")(preguntar)
