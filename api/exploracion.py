# -*- coding: utf-8 -*-
"""Rutas de «conocer los datos»: la cohorte, la estadística y el mapa de calor.

Todo sale de archivos ya calculados en `reports/`. Ninguna de estas rutas abre
el conjunto de datos ni ejecuta el modelo: son tablas de unos pocos kilobytes
que se leen una vez y quedan en memoria.

Esa decisión no es por rendimiento sino por honestidad: las cifras que ve
alguien en pantalla son exactamente las que quedaron guardadas al correr los
cuadernos, no un recálculo que podría dar distinto.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import datos  # noqa: E402

from api import autenticacion as auth  # noqa: E402

REPORTES = BASE / "reports"


def _tabla(nombre: str) -> list[dict]:
    """Lee un CSV de reports/ y lo devuelve como lista de registros."""
    ruta = REPORTES / nombre
    if not ruta.is_file():
        raise HTTPException(
            503,
            f"Falta el archivo {nombre}. Hay que generarlo corriendo el script "
            "que lo produce antes de desplegar.",
        )
    marco = pd.read_csv(ruta)
    # NaN no es JSON válido; se convierte a null para que el front decida qué
    # mostrar en vez de recibir un literal roto.
    return json.loads(marco.to_json(orient="records"))


def cohorte(_=Depends(auth.exige("Conocer los datos"))):
    """De dónde salen los datos y qué se excluyó."""
    ruta = REPORTES / "descriptiva_resumen.json"
    if not ruta.is_file():
        raise HTTPException(503, "Falta reports/descriptiva_resumen.json.")
    return json.loads(ruta.read_text(encoding="utf-8"))


def descriptiva(_=Depends(auth.exige("Estadística descriptiva"))):
    """Media, mediana, moda, desviación, cuartiles y distribuciones."""
    return {
        "numericas": _tabla("descriptiva_numericas.csv"),
        "categoricas": _tabla("descriptiva_categoricas.csv"),
        "histogramas": _tabla("descriptiva_histogramas.csv"),
    }


def mapa_calor(_=Depends(auth.exige("Mapa de calor"))):
    """Tipo de egreso cruzado con hospitalizaciones previas."""
    celdas = _tabla("mapa_calor.csv")
    if not celdas:
        raise HTTPException(503, "El mapa de calor está vacío.")
    tasas = [c["tasa"] for c in celdas]
    return {
        "celdas": celdas,
        "minimo": min(tasas),
        "maximo": max(tasas),
        "tasa_base": 0.1139,
        "umbral": round(float(datos.umbral_oficial()), 6),
        "total_casos": sum(c["casos"] for c in celdas),
    }


def registrar(app: FastAPI) -> None:
    app.get("/api/cohorte")(cohorte)
    app.get("/api/descriptiva")(descriptiva)
    app.get("/api/mapa-calor")(mapa_calor)
