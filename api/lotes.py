# -*- coding: utf-8 -*-
"""Cargar un archivo y convertirlo en una lista de llamadas, y fijar el umbral.

Las dos palancas de operación del programa, reservadas a coordinación.

El reconocimiento de columnas lo hace `src/cargue_flexible.py`, que acepta
nombres en español y en inglés y mide la cobertura pesando cada variable por su
importancia, no contándolas. Eso importa: un archivo con cuarenta columnas
irrelevantes y sin las dos que mandan tiene cobertura baja, que es justo lo que
hay que saber antes de confiar en el resultado.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import datos  # noqa: E402

from api import autenticacion as auth  # noqa: E402
from src import cargue_flexible  # noqa: E402
from src import procesamiento_lotes  # noqa: E402

# El servidor tiene un nucleo. Un archivo de cien megas lo deja ocupado
# minutos y la aplicacion entera deja de responder.
TOPE_BYTES = 20 * 1024 * 1024
TOPE_FILAS = 60_000
# Por debajo de esto el resultado no es de fiar: el modelo estaria rellenando
# casi todo con valores tipicos y devolviendo el riesgo del paciente promedio
# con toda la apariencia de una prediccion.
COBERTURA_MINIMA = 0.25


def leer_tabla(contenido: bytes, nombre: str) -> pd.DataFrame:
    """Lee un CSV o un Excel subido, sin suponer el separador.

    Se prueba primero el motor rápido con coma, que es el caso normal. Si sale
    una sola columna, el archivo usa otro separador: se prueban punto y coma y
    tabulación, que es lo que produce Excel en configuración regional española.

    No se usa `sep=None` con el motor de Python: no admite `low_memory` y, en
    archivos grandes, tarda bastante más en adivinar de lo que cuesta probar
    tres separadores.
    """
    if nombre.lower().endswith((".xlsx", ".xls")):
        try:
            return pd.read_excel(io.BytesIO(contenido))
        except Exception:
            raise HTTPException(422, "No se pudo leer el Excel. Revise que tenga "
                                     "una fila de encabezados y datos debajo.")

    ultimo = None
    for separador in (",", ";", "	", "|"):
        try:
            marco = pd.read_csv(io.BytesIO(contenido), sep=separador, low_memory=False)
        except Exception as error:
            ultimo = error
            continue
        if marco.shape[1] > 1:
            return marco
        ultimo = ValueError("una sola columna")

    raise HTTPException(
        422,
        "No se pudo leer el archivo. Debe ser un CSV o un Excel con una fila de "
        "encabezados y una hospitalización por fila, separado por comas, punto y "
        f"coma o tabulaciones. ({type(ultimo).__name__ if ultimo else 'desconocido'})",
    )


async def analizar(archivo: UploadFile, _=Depends(auth.exige("Cargar archivo"))):
    """Del archivo a la lista de llamadas."""
    contenido = await archivo.read()
    if len(contenido) > TOPE_BYTES:
        raise HTTPException(
            413,
            f"El archivo pesa más de {TOPE_BYTES // (1024 * 1024)} MB. "
            "Divídalo o déjelo en el corte de un día.",
        )
    if not contenido:
        raise HTTPException(422, "El archivo llegó vacío.")

    crudo = leer_tabla(contenido, archivo.filename or "")
    if crudo.empty:
        raise HTTPException(422, "El archivo no tiene filas.")
    if len(crudo) > TOPE_FILAS:
        raise HTTPException(
            413,
            f"El archivo trae {len(crudo):,} filas y el tope es {TOPE_FILAS:,}."
            .replace(",", "."),
        )

    # Si alguien sube por error un archivo que esta misma aplicación produjo,
    # decírselo es más útil que intentar predecir sobre un reporte de calidad.
    propia = cargue_flexible.es_salida_propia(crudo)
    if propia:
        raise HTTPException(
            422,
            f"Ese archivo es «{propia}», uno de los que esta aplicación genera. "
            "Suba el corte de hospitalizaciones, no un reporte de salida.",
        )

    numericas, categoricas, por_defecto = datos.cargar_columnas()
    X, informe = cargue_flexible.preparar_tolerante(crudo, numericas, categoricas, por_defecto)

    if informe["cobertura"] < COBERTURA_MINIMA:
        raise HTTPException(
            422,
            f"El archivo solo cubre el {informe['cobertura'] * 100:.0f} % de lo que el "
            "modelo necesita. Con tan poca información la estimación sería el riesgo "
            "del paciente promedio para todos, que no sirve para priorizar. Faltan "
            "sobre todo: " + ", ".join(informe["faltan_importantes"][:4]) + ".",
        )

    # Fallecimientos y cuidados paliativos salen: esas personas no pueden
    # reingresar, igual que en el entrenamiento.
    descartados = 0
    if "discharge_disposition_id" in crudo.columns:
        codigos = pd.to_numeric(crudo["discharge_disposition_id"], errors="coerce")
        fuera = codigos.isin(procesamiento_lotes.EXCLUIR_EGRESOS)
        descartados = int(fuera.sum())
        if descartados:
            X = X.loc[~fuera.reindex(X.index, fill_value=False)]

    if X.empty:
        raise HTTPException(422, "No quedó ninguna hospitalización después de las exclusiones.")

    modelo = datos.cargar_modelo()
    umbral = float(datos.umbral_oficial())
    no_vistas = procesamiento_lotes.categorias_no_vistas(modelo, X, categoricas)
    probabilidades = modelo.predict_proba(X)[:, 1]

    orden = probabilidades.argsort()[::-1]
    lista = [
        {
            "puesto": i + 1,
            "fila_csv": int(X.index[j]) + 2,
            "probabilidad": round(float(probabilidades[j]), 6),
            "alerta": bool(probabilidades[j] >= umbral),
        }
        for i, j in enumerate(orden)
    ]

    return {
        "filas_archivo": int(len(crudo)),
        "descartados": descartados,
        "analizadas": int(len(X)),
        "cobertura": round(float(informe["cobertura"]), 4),
        "reconocidas": informe["reconocidas"],
        "sin_reconocer": informe["sin_reconocer"][:20],
        "faltan_importantes": informe["faltan_importantes"][:8],
        "rellenadas": len(informe.get("rellenadas", [])),
        "categorias_no_vistas": no_vistas if isinstance(no_vistas, list) else [],
        "umbral": round(umbral, 6),
        "sobre_umbral": int((probabilidades >= umbral).sum()),
        "lista": lista,
    }


class Capacidad(BaseModel):
    """A cuánta gente alcanza a llamar el programa."""

    llamadas: int = Field(ge=1, le=20_000)


def consecuencias(peticion: Capacidad, _=Depends(auth.exige("Fijar umbral"))):
    """Qué pasa si el programa solo alcanza a llamar a N pacientes.

    Se calcula sobre el conjunto de prueba, que es el único donde se sabe
    quién reingresó de verdad. En producción no se podría medir esto: solo se
    sabe después.
    """
    d = datos.predicciones_prueba().sort_values("probabilidad", ascending=False)
    total = len(d)
    reingresos = int(d.reingreso_real.sum())
    n = min(peticion.llamadas, total)
    elegidos = d.head(n)

    aciertan = int(elegidos.reingreso_real.sum())
    base = float(d.reingreso_real.mean())
    tasa = float(elegidos.reingreso_real.mean()) if n else 0.0
    corte = float(elegidos.probabilidad.min()) if n else 1.0

    return {
        "llamadas": n,
        "poblacion": total,
        "fraccion": round(n / total, 4),
        "umbral_resultante": round(corte, 6),
        "umbral_oficial": round(float(datos.umbral_oficial()), 6),
        "aciertan": aciertan,
        "tasa": round(tasa, 4),
        "tasa_base": round(base, 4),
        "veces_la_base": round(tasa / base, 2) if base else 0.0,
        "cobertura": round(aciertan / reingresos, 4) if reingresos else 0.0,
        "se_escapan": reingresos - aciertan,
        "reingresos_totales": reingresos,
        "llamadas_de_mas": n - aciertan,
    }


def registrar(app: FastAPI) -> None:
    app.post("/api/archivo")(analizar)
    app.post("/api/capacidad")(consecuencias)
