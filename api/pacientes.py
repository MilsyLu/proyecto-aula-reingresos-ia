# -*- coding: utf-8 -*-
"""La lista priorizada: las 19.870 hospitalizaciones de prueba, por riesgo.

No son pacientes inventados para que la pantalla se vea llena. Son las mismas
hospitalizaciones del conjunto de prueba —las que el modelo nunca vio mientras
se entrenaba—, con la probabilidad que les dio y con el desenlace real al lado.
Que esté el desenlace real es lo que hace útil la pantalla: se puede mirar un
paciente de riesgo 40 % y ver si reingresó o no.

Los tres tramos de riesgo no son decorativos. El reingreso observado en cada
uno es 17,8 %, 8,2 % y 5,0 %: la escala ordena de verdad, y eso se puede
comprobar con el CSV en la mano.

Pagina en el servidor. Veinte mil filas en una sola respuesta son unos cuatro
megas de JSON y un navegador que se arrastra al dibujar la tabla.
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from api import autenticacion as auth  # noqa: E402

PREDICCIONES = BASE / "reports/predicciones_prueba.csv"
UMBRAL_JSON = BASE / "reports/umbral_elegido.json"

EGRESOS = {
    1: "A casa",
    2: "Traslado a otro hospital",
    3: "Centro de enfermería",
    4: "Cuidado intermedio",
    5: "Otra institución",
    6: "A casa con atención domiciliaria",
    22: "Rehabilitación",
}

GENERO = {"Female": "Mujer", "Male": "Hombre"}
EDAD = {"80 o mas": "80 o más"}

POR_PAGINA = 40


@lru_cache(maxsize=1)
def _cohorte() -> tuple[pd.DataFrame, float]:
    """El CSV preparado una sola vez, con los nombres que ve la persona.

    Se cachea porque son veinte mil filas y leerlas en cada petición de una
    tabla paginada sería absurdo. El archivo no cambia mientras corre el
    servidor: lo escribe el entrenamiento, no la aplicación.
    """
    d = pd.read_csv(PREDICCIONES)
    umbral = float(json.loads(UMBRAL_JSON.read_text(encoding="utf-8"))["umbral"])

    d = d.assign(
        egreso_nombre=d.egreso.map(EGRESOS).fillna("Otro egreso"),
        genero_es=d.genero.map(GENERO).fillna(d.genero),
        edad_es=d.grupo_edad.map(EDAD).fillna(d.grupo_edad),
        nivel=pd.cut(
            d.probabilidad,
            bins=[-1.0, umbral / 2, umbral, 2.0],
            labels=["bajo", "medio", "alto"],
        ).astype(str),
    ).sort_values("probabilidad", ascending=False, ignore_index=True)

    d["puesto"] = d.index + 1
    return d, umbral


def _ficha(r) -> dict:
    return {
        "puesto": int(r.puesto),
        "paciente": int(r.paciente),
        "probabilidad": round(float(r.probabilidad), 6),
        "nivel": r.nivel,
        "alerta": bool(r.alerta),
        "reingreso_real": bool(r.reingreso_real),
        "resultado": r.resultado,
        "edad": int(r.edad),
        "grupo_edad": r.edad_es,
        "genero": r.genero_es,
        "dias_estancia": int(r.dias_estancia),
        "ingresos_previos": int(r.ingresos_previos),
        "medicamentos": int(r.medicamentos),
        "diagnosticos": int(r.diagnosticos),
        "diagnostico_principal": r.diagnostico_principal,
        "egreso": r.egreso_nombre,
    }


def listar(
    pagina: int = 1,
    nivel: str = "",
    q: str = "",
    desenlace: str = "",
    _=Depends(auth.exige("Lista priorizada")),
):
    """Una página de la lista, filtrada."""
    d, umbral = _cohorte()

    if nivel in ("alto", "medio", "bajo"):
        d = d[d.nivel == nivel]
    if desenlace == "reingresaron":
        d = d[d.reingreso_real == 1]
    elif desenlace == "no-reingresaron":
        d = d[d.reingreso_real == 0]
    if q.strip():
        # Se busca por numero de paciente, que es lo unico que identifica una
        # fila: no hay nombres, y es a proposito, son datos anonimizados.
        texto = q.strip()
        d = d[d.paciente.astype(str).str.contains(texto, regex=False)]

    total = len(d)
    pagina = max(1, pagina)
    desde = (pagina - 1) * POR_PAGINA
    trozo = d.iloc[desde : desde + POR_PAGINA]

    return {
        "pacientes": [_ficha(r) for r in trozo.itertuples(index=False)],
        "total": total,
        "pagina": pagina,
        "paginas": max(1, -(-total // POR_PAGINA)),
        "por_pagina": POR_PAGINA,
        "umbral": round(umbral, 6),
    }


def resumen(_=Depends(auth.exige("Lista priorizada"))):
    """Cuántos hay en cada tramo y cuántos reingresaron de verdad en cada uno.

    Esta es la cifra que justifica que los tramos existan: si el reingreso real
    no bajara de un tramo al siguiente, la escala sería un adorno.
    """
    d, umbral = _cohorte()
    return {
        "total": int(len(d)),
        "umbral": round(umbral, 6),
        "tramos": [
            {
                "nivel": n,
                "pacientes": int((d.nivel == n).sum()),
                "reingreso_real": round(float(d[d.nivel == n].reingreso_real.mean()), 4),
            }
            for n in ("alto", "medio", "bajo")
        ],
    }


def registrar(app: FastAPI) -> None:
    app.get("/api/pacientes")(listar)
    app.get("/api/pacientes/resumen")(resumen)
