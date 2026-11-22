# -*- coding: utf-8 -*-
"""Rutas de «conocer el modelo»: qué se probó, qué tan bien rinde y qué límites tiene.

Igual que las de exploración, todo sale de archivos ya calculados en
`reports/`. Las cifras que ve alguien en pantalla son exactamente las que
quedaron guardadas al correr los cuadernos, no un recálculo que podría dar
distinto.
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


def _tabla(nombre: str, obligatoria: bool = True) -> list[dict]:
    ruta = REPORTES / nombre
    if not ruta.is_file():
        if obligatoria:
            raise HTTPException(503, f"Falta el archivo {nombre} en reports/.")
        return []
    return json.loads(pd.read_csv(ruta).to_json(orient="records"))


def _json(nombre: str) -> dict:
    ruta = REPORTES / nombre
    if not ruta.is_file():
        raise HTTPException(503, f"Falta el archivo {nombre} en reports/.")
    return json.loads(ruta.read_text(encoding="utf-8"))


def modelos(_=Depends(auth.exige("Comparar modelos"))):
    """Qué modelos se probaron y por qué ganó el que ganó.

    Las dos tablas no son lo mismo y conviene no mezclarlas. `comparacion`
    viene de la Fase 2 y es la que produjo el modelo oficial. `laboratorio` es
    la reproducción independiente de Iván, con su propia partición y 120
    iteraciones, y por eso da 0,2206 donde el oficial da 0,2238.
    """
    return {
        "baseline": _tabla("metricas_02_baseline.csv"),
        "comparacion": _tabla("metricas_03_comparacion.csv"),
        "laboratorio": _tabla("metricas_06_mlp.csv", obligatoria=False),
        "busqueda_laboratorio": _tabla("busqueda_06_laboratorio.csv", obligatoria=False),
        "busqueda_oficial": _tabla("busqueda_03_hiperparametros.csv", obligatoria=False)[:6],
        "curva_mlp": _tabla("curva_perdida_mlp.csv", obligatoria=False),
        "oficial": datos.metricas_finales(),
    }


def desempeno(_=Depends(auth.exige("Desempeño"))):
    """Las métricas del modelo oficial, y a cuánta gente conviene llamar."""
    ganancia, base = datos.ganancia_por_tramo()
    return {
        "finales": json.loads(datos.cargar_tabla("metricas_04_final.csv").to_json(orient="records")),
        "calibracion": _tabla("calibracion.csv"),
        "metas": _tabla("cumplimiento_metas.csv"),
        "umbrales": _tabla("umbrales_validacion.csv"),
        "ganancia": json.loads(ganancia.to_json(orient="records")),
        "tasa_base": round(float(base), 6),
        "umbral": round(float(datos.umbral_oficial()), 6),
    }


def importancia(_=Depends(auth.exige("Importancia"))):
    """Cuánto pierde el modelo si se le revuelve cada variable."""
    filas = _tabla("importancia_permutacion.csv")
    # Muchas de las 50 aportan cero o menos. Dejarlas en la lista no es un
    # error: enseña que la mayoria de columnas no estaba diciendo nada.
    utiles = [f for f in filas if f["pct_del_AP"] > 0.1]
    return {
        "variables": filas,
        "con_aporte": len(utiles),
        "total": len(filas),
        "suma_primeras_dos": round(sum(f["pct_del_AP"] for f in filas[:2]), 2),
    }


def equidad(_=Depends(auth.exige("Equidad"))):
    """Si el modelo trata igual a todos, y qué no se puede medir."""
    return {
        "resumen": _tabla("metricas_05_equidad.csv"),
        "raza": _tabla("metricas_05_subgrupos_raza.csv", obligatoria=False),
        "genero": _tabla("metricas_05_subgrupos_genero.csv", obligatoria=False),
        "edad": _tabla("metricas_05_subgrupos_edad.csv", obligatoria=False),
        "sensibilidad": _tabla("metricas_05_sensibilidad.csv", obligatoria=False),
    }


def techo(_=Depends(auth.exige("Techo de los datos"))):
    """Hasta dónde se puede llegar con estas columnas."""
    return _json("auditoria_techo.json")


def ficha(_=Depends(auth.exige("Ficha del modelo"))):
    """La ficha técnica: qué es, cómo se entrenó y para qué NO sirve."""
    return {
        "hiperparametros": _json("mejores_hiperparametros.json"),
        "metricas": datos.metricas_finales(),
        "umbral": _json("umbral_elegido.json"),
        "metas": _tabla("cumplimiento_metas.csv"),
    }


def registrar(app: FastAPI) -> None:
    app.get("/api/modelos")(modelos)
    app.get("/api/desempeno")(desempeno)
    app.get("/api/importancia")(importancia)
    app.get("/api/equidad")(equidad)
    app.get("/api/techo")(techo)
    app.get("/api/ficha")(ficha)
