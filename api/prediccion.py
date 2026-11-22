# -*- coding: utf-8 -*-
"""Rutas de estimación: el formulario, la predicción y el cálculo paso a paso.

Toda la lógica vive en `app/modelo.py`, que es la misma que usa la aplicación
de Streamlit. Aquí solo se expone por HTTP y se valida lo que entra.
"""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import datos  # noqa: E402
import modelo  # noqa: E402

from api import autenticacion as auth  # noqa: E402
from api import trazado as trazado_modulo  # noqa: E402

# Aqui no se usa APIRouter, y es a proposito.
#
# Con esta version de FastAPI (0.142) include_router envuelve el router en un
# _IncludedRouter y las rutas terminan servidas sin su prefijo: /opciones en
# vez de /api/opciones, aunque al listarlas aparezcan bien. Costo un rato
# encontrarlo porque la ruta se veia correcta y respondia 404.
#
# Registrarlas una por una sobre la app, como ya se hace con las de sesion en
# principal.py, no depende de como se comporte include_router en cada version.


class Entradas(BaseModel):
    """Los quince campos del formulario.

    Los rangos no son decorativos. `dias` no puede ser cero porque el modelo
    divide entre él para calcular medicamentos por día; los topes superiores
    vienen de lo que se vio en la cohorte, y pasarse de ahí significa pedirle
    al modelo que extrapole, que es justo donde se equivoca sin avisar.
    """

    edad: float = Field(ge=0, le=100)
    genero: str = Field(pattern="^(Female|Male)$")
    ingresos: int = Field(ge=0, le=25)
    urgencias: int = Field(ge=0, le=80)
    consultas: int = Field(ge=0, le=45)
    dias: int = Field(ge=1, le=14)
    labs: int = Field(ge=0, le=140)
    meds: int = Field(ge=0, le=85)
    diagnosticos: int = Field(ge=1, le=16)
    procedimientos: int = Field(ge=0, le=7)
    diag1: str
    a1c: str
    insulina: str
    cambio: str
    egreso: str


def _valida(entradas: Entradas) -> dict:
    """Comprueba que las categorías existan antes de llegar al modelo.

    Pydantic ya revisó los números. Esto revisa que las opciones de los
    desplegables sean de las que el modelo conoce: una categoría inventada se
    codificaría como -1 en silencio y devolvería una predicción degradada sin
    que nadie se entere.
    """
    datos_entrada = entradas.model_dump()
    catalogos = {
        "diag1": modelo.DIAGNOSTICOS,
        "a1c": modelo.A1C,
        "insulina": modelo.INSULINA,
        "cambio": modelo.CAMBIO_MED,
        "egreso": modelo.EGRESOS,
    }
    for campo, catalogo in catalogos.items():
        if datos_entrada[campo] not in catalogo:
            from fastapi import HTTPException

            raise HTTPException(
                422,
                f"El valor de «{modelo.NOMBRE_CAMPO[campo]}» no es uno de los que "
                "el modelo conoce.",
            )
    return datos_entrada


def opciones(_=Depends(auth.exige("Estimar riesgo"))):
    """Todo lo que el formulario necesita para dibujarse.

    Las opciones salen del modelo, no están escritas en el front: si algún día
    se reentrena con otras categorías, el formulario se actualiza solo.
    """
    tipicos = modelo.valores_tipicos()
    return {
        "campos": [
            {
                "campo": campo,
                "nombre": modelo.NOMBRE_CAMPO[campo],
                "tipico": tipicos.get(campo),
                "tipico_mostrado": modelo.mostrar(campo, tipicos.get(campo)),
                "opciones": (
                    [{"valor": v, "etiqueta": e} for v, e in modelo.ETIQUETAS[campo].items()]
                    if campo in modelo.ETIQUETAS
                    else None
                ),
            }
            for campo in modelo.EQUIVALENCIA
        ],
        "umbral": round(float(datos.umbral_oficial()), 6),
        "tasa_base": 0.1139,
    }


def estimar(entradas: Entradas, _=Depends(auth.exige("Estimar riesgo"))):
    """La probabilidad de reingreso y qué la empujó."""
    valores = _valida(entradas)
    probabilidad, efectos = modelo.explicar(valores)
    umbral = float(datos.umbral_oficial())
    tasa_base = 0.1139

    return {
        "probabilidad": round(probabilidad, 6),
        "umbral": round(umbral, 6),
        "supera": probabilidad >= umbral,
        "tasa_base": tasa_base,
        "veces_la_base": round(probabilidad / tasa_base, 2),
        "efectos": [
            {
                "campo": e["campo"],
                "nombre": e["nombre"],
                "valor": e["valor"],
                "tipico": e["tipico"],
                "sin_el": round(e["riesgo_sin_el"], 6),
                "efecto": round(e["efecto"], 6),
            }
            for e in efectos
        ],
    }


def trazar(entradas: Entradas, _=Depends(auth.exige("Paso a paso"))):
    """Los ocho pasos del cálculo, con los 135 árboles abiertos."""
    return trazado_modulo.trazar(_valida(entradas))


def registrar(app: FastAPI) -> None:
    """Cuelga las tres rutas de la aplicación."""
    app.get("/api/opciones")(opciones)
    app.post("/api/estimar")(estimar)
    app.post("/api/trazado")(trazar)
