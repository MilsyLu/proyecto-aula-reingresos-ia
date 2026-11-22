# -*- coding: utf-8 -*-
"""El cálculo paso a paso, de la entrada a la probabilidad final.

Esta es la pantalla que responde a «¿y usted cómo sabe?». No es una
aproximación ni una ilustración: es el cálculo real del modelo, abierto en sus
ocho pasos, y la suma de los 135 árboles reconstruye `predict_proba` hasta el
sexto decimal.

Los pasos:

  1. Lo que escribió el usuario, 15 campos
  2. Las 50 columnas que espera el modelo, y con qué se rellenaron las otras 35
  3. Qué vacíos se llenaron y con qué
  4. Cómo se convirtió cada categoría en un número
  5. El punto de partida: la tasa base de la cohorte, en log-odds
  6. Los 135 árboles, uno por uno
  7. De log-odds a probabilidad
  8. La comparación contra el umbral del programa

El paso 6 sale de `staged_decision_function`, que devuelve el acumulado tras
cada árbol. La diferencia entre un paso y el anterior es lo que aportó ese
árbol, y la suma de todos más el punto de partida da el resultado exacto.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import datos  # noqa: E402
import modelo  # noqa: E402


def _sigmoide(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _clasificador():
    return datos.cargar_modelo().named_steps["modelo"]


def _preprocesador():
    return datos.cargar_modelo().named_steps["prep"]


def _codificador():
    """El OrdinalEncoder, que sabe qué número le toca a cada categoría."""
    return _preprocesador().named_transformers_["categoricas"].named_steps["ordinal"]


def trazar(entradas: dict) -> dict:
    """Devuelve los ocho pasos del cálculo para una hospitalización."""
    numericas, categoricas, por_defecto = datos.cargar_columnas()
    tipicos = modelo.valores_tipicos()
    fila = modelo.construir_fila(entradas)
    pipeline = datos.cargar_modelo()
    clf = _clasificador()

    # --- paso 1: lo que escribió el usuario --------------------------------
    escrito = [
        {
            "campo": campo,
            "nombre": modelo.NOMBRE_CAMPO[campo],
            "valor": modelo.mostrar(campo, entradas[campo]),
            "es_tipico": str(entradas[campo]) == str(tipicos.get(campo)),
        }
        for campo in modelo.EQUIVALENCIA
        if campo in entradas
    ]

    # --- paso 2: las 50 columnas -------------------------------------------
    # Las que el formulario no pregunta toman el valor típico del
    # entrenamiento. Decirlo importa: el modelo no "adivina" esas 35, se le
    # está dando el valor más frecuente de la cohorte.
    del_formulario = {modelo.EQUIVALENCIA[c] for c in entradas if c in modelo.EQUIVALENCIA}
    derivadas = {
        "servicios_previos", "tuvo_ingreso_previo", "meds_por_dia",
        "labs_por_dia", "a1c_medida",
    }
    columnas = []
    for columna in numericas + categoricas:
        if columna in del_formulario:
            origen = "del formulario"
        elif columna in derivadas:
            origen = "calculada"
        else:
            origen = "valor típico"
        columnas.append({
            "columna": columna,
            "valor": str(fila.iloc[0][columna]),
            "origen": origen,
        })
    resumen_columnas = {
        "total": len(columnas),
        "del_formulario": sum(1 for c in columnas if c["origen"] == "del formulario"),
        "calculadas": sum(1 for c in columnas if c["origen"] == "calculada"),
        "tipicas": sum(1 for c in columnas if c["origen"] == "valor típico"),
    }

    # --- paso 3: imputación -------------------------------------------------
    # Lo que llega vacío se rellena con 'Ausente', que es una categoría que el
    # modelo aprendió durante el entrenamiento, no un parche.
    vacios = [
        {"columna": c, "relleno": "Ausente"}
        for c in categoricas
        if fila.iloc[0][c] in ("", "nan", "None") or fila.iloc[0][c] is None
    ]

    # --- paso 4: codificación ----------------------------------------------
    codificador = _codificador()
    codificadas = []
    for i, columna in enumerate(categoricas):
        valor = str(fila.iloc[0][columna])
        posibles = list(codificador.categories_[i])
        try:
            codigo = posibles.index(valor)
            conocida = True
        except ValueError:
            # -1 es lo que el modelo recibe cuando la categoría no estaba en el
            # entrenamiento. Mostrarlo evita que una predicción degradada pase
            # por buena.
            codigo = -1
            conocida = False
        codificadas.append({
            "columna": columna,
            "valor": valor,
            "codigo": codigo,
            "conocida": conocida,
            "posibles": len(posibles),
        })
    no_vistas = [c for c in codificadas if not c["conocida"]]

    # --- pasos 5 y 6: el punto de partida y los árboles ---------------------
    X = _preprocesador().transform(fila)
    partida = float(np.ravel(clf._baseline_prediction)[0])
    acumulado = np.array([float(np.ravel(p)[0]) for p in clf.staged_decision_function(X)])
    aportes = np.diff(np.concatenate([[partida], acumulado]))

    arboles = [
        {
            "n": i + 1,
            "aporte": round(float(a), 6),
            "acumulado": round(float(acumulado[i]), 6),
            "probabilidad": round(_sigmoide(float(acumulado[i])), 6),
        }
        for i, a in enumerate(aportes)
    ]
    orden = np.argsort(-np.abs(aportes))[:10]
    mas_fuertes = [arboles[int(i)] for i in orden]

    # Cuánto del recorrido hacen los primeros quince.
    final = float(acumulado[-1])
    prob_partida = _sigmoide(partida)
    prob_final = _sigmoide(final)
    corte = min(15, len(acumulado))
    recorrido = prob_final - prob_partida
    primeros = (
        (_sigmoide(float(acumulado[corte - 1])) - prob_partida) / recorrido
        if abs(recorrido) > 1e-9
        else 0.0
    )

    # --- paso 7: comprobación ----------------------------------------------
    # Si esto no coincide, algo se rompió en el preprocesamiento y más vale
    # enterarse aquí que en la sustentación.
    del_modelo = float(pipeline.predict_proba(fila)[0, 1])
    coincide = abs(del_modelo - prob_final) < 1e-9

    # --- paso 8: el umbral --------------------------------------------------
    umbral = datos.umbral_oficial()
    tasa_base = prob_partida

    return {
        "escrito": escrito,
        "columnas": {"resumen": resumen_columnas, "detalle": columnas},
        "vacios": vacios,
        "codificadas": {"detalle": codificadas, "no_vistas": no_vistas},
        "partida": {
            "log_odds": round(partida, 6),
            "probabilidad": round(prob_partida, 6),
        },
        "arboles": {
            "total": len(arboles),
            "pasos": arboles,
            "mas_fuertes": mas_fuertes,
            "fraccion_primeros_quince": round(float(primeros), 4),
        },
        "final": {
            "log_odds": round(final, 6),
            "probabilidad": round(prob_final, 6),
            "del_modelo": round(del_modelo, 6),
            "coincide": coincide,
        },
        "umbral": {
            "valor": round(float(umbral), 6),
            "supera": prob_final >= umbral,
            "tasa_base": round(tasa_base, 6),
            "veces_la_base": round(prob_final / tasa_base, 2) if tasa_base else None,
        },
    }
