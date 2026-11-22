# -*- coding: utf-8 -*-
"""Entrenar un modelo en vivo y transmitir el proceso fase por fase.

Idea de Iván: que al subir un archivo el modelo se entrene delante de quien lo
subió. Lo valioso no es que entrene —eso ya lo hacía el laboratorio de
Streamlit— sino que **la espera se convierta en la clase**.

Por eso no es una petición normal. Una petición normal se queda esperando
cuarenta segundos y el navegador la corta; aquí el servidor va mandando una
línea por fase a medida que ocurre, y el front revela una lámina con cada una.

Cuatro momentos enseñan algo en vez de solo informar:

  1. La partición mal hecha. Si se elige repartir al azar, se entrena de las
     dos formas y se muestran los dos números juntos. El azar puntúa mejor
     porque el mismo paciente queda a ambos lados. Es el error más común en
     trabajos de aula y aquí se comete y se ve.
  2. La trampa de la exactitud. El modelo que siempre dice «no reingresa»
     acierta nueve de cada diez veces y no sirve para nada.
  3. El sobreajuste. Se muestran la puntuación en entrenamiento y en
     validación lado a lado, y la brecha entre las dos.
  4. El umbral. Mover el corte cambia a cuánta gente se llama y cuántos
     reingresos se escapan. No hay un valor correcto.

Límites, porque el servidor tiene un núcleo y lo comparte con RustDesk: un
entrenamiento a la vez en todo el servidor, tope de archivo y de filas, y el
modelo que salga de aquí **nunca** reemplaza al oficial: vive en memoria y
muere con la petición.
"""
from __future__ import annotations

import io
import json
import sys
import threading
import time
from pathlib import Path
from typing import Iterator

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import datos  # noqa: E402

from api import autenticacion as auth  # noqa: E402
from api.lotes import leer_tabla  # noqa: E402
from src import cargue_flexible  # noqa: E402
from src import procesamiento_lotes  # noqa: E402

TOPE_BYTES = 20 * 1024 * 1024
TOPE_FILAS = 60_000
MUESTRA_RAPIDA = 20_000
SEMILLA = 42

# Un entrenamiento a la vez en todo el servidor. No es tacanearia: con un
# nucleo compartido, dos a la vez dejan la aplicacion entera sin responder.
_ocupado = threading.Lock()


def _linea(tipo: str, **campos) -> bytes:
    """Una fase, en una línea de JSON. El front lee línea por línea."""
    return (json.dumps({"tipo": tipo, **campos}, ensure_ascii=False) + "\n").encode("utf-8")


def _preparador(numericas, categoricas, para_lineal=False):
    if para_lineal:
        return ColumnTransformer([
            ("num", Pipeline([
                ("imputar", SimpleImputer(strategy="median")),
                ("escalar", StandardScaler()),
            ]), numericas),
            ("cat", Pipeline([
                ("imputar", SimpleImputer(strategy="constant", fill_value="Ausente")),
                ("codificar", OneHotEncoder(handle_unknown="ignore", sparse_output=False,
                                            max_categories=12)),
            ]), categoricas),
        ])
    return ColumnTransformer([
        ("num", "passthrough", numericas),
        ("cat", Pipeline([
            ("imputar", SimpleImputer(strategy="constant", fill_value="Ausente")),
            ("codificar", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
        ]), categoricas),
    ])


def _ap(y, prob) -> float:
    return float(average_precision_score(y, prob))


def _entrenar_gb(X, y, entrena, valida, numericas, categoricas):
    """Gradient Boosting y sus dos puntuaciones, la de entrenamiento y la de validación."""
    mascara = [False] * len(numericas) + [True] * len(categoricas)
    modelo = Pipeline([
        ("prep", _preparador(numericas, categoricas)),
        ("modelo", HistGradientBoostingClassifier(
            categorical_features=mascara, max_iter=120, learning_rate=0.05,
            max_leaf_nodes=15, min_samples_leaf=100, l2_regularization=0.5,
            early_stopping=False, random_state=SEMILLA,
        )),
    ])
    modelo.fit(X.iloc[entrena], y[entrena])
    prob_tr = modelo.predict_proba(X.iloc[entrena])[:, 1]
    prob_va = modelo.predict_proba(X.iloc[valida])[:, 1]
    return modelo, _ap(y[entrena], prob_tr), _ap(y[valida], prob_va), prob_va


def _etiquetas(df: pd.DataFrame) -> np.ndarray | None:
    """Construye el desenlace: 1 si reingresó antes de 30 días."""
    if "y" in df.columns:
        return pd.to_numeric(df["y"], errors="coerce").fillna(0).astype(int).to_numpy()
    if "readmitted" in df.columns:
        return (df["readmitted"].astype(str).str.strip() == "<30").astype(int).to_numpy()
    return None


def _corre(contenido: bytes, nombre: str, particion: str) -> Iterator[bytes]:
    """El entrenamiento, fase por fase. Cada `yield` llega al navegador enseguida."""
    reloj = time.monotonic()

    def desde():
        return round(time.monotonic() - reloj, 1)

    try:
        # ---------------------------------------------- 1. leer el archivo
        yield _linea("fase", n=1, titulo="Leer el archivo", estado="corriendo")
        try:
            crudo = leer_tabla(contenido, nombre)
        except Exception as error:
            mensaje = getattr(error, "detail", "No se pudo leer el archivo.")
            yield _linea("error", mensaje=str(mensaje))
            return

        if len(crudo) > TOPE_FILAS:
            yield _linea("error",
                         mensaje=f"El archivo trae {len(crudo)} filas y el tope es {TOPE_FILAS}.")
            return

        yield _linea("fase", n=1, titulo="Leer el archivo", estado="listo", segundos=desde(),
                     cifra=f"{len(crudo):,}".replace(",", "."),
                     detalle=f"{len(crudo)} filas y {crudo.shape[1]} columnas")

        # ------------------------------------------ 2. reconocer columnas
        yield _linea("fase", n=2, titulo="Reconocer las columnas", estado="corriendo")
        numericas, categoricas, por_defecto = datos.cargar_columnas()
        X, informe = cargue_flexible.preparar_tolerante(crudo, numericas, categoricas, por_defecto)
        yield _linea("fase", n=2, titulo="Reconocer las columnas", estado="listo",
                     segundos=desde(),
                     cifra=f"{informe['cobertura'] * 100:.0f} %",
                     detalle=f"{len(informe['reconocidas'])} columnas reconocidas; la cobertura "
                             "pesa cada una por su importancia, no las cuenta")

        # --------------------------------------- 3. construir la etiqueta
        yield _linea("fase", n=3, titulo="Construir la etiqueta", estado="corriendo")
        y = _etiquetas(crudo)
        if y is None:
            yield _linea("error",
                         mensaje="El archivo no trae la columna 'readmitted' ni 'y'. Sin saber "
                                 "quién reingresó no hay nada que aprender.")
            return
        if y.sum() == 0 or y.sum() == len(y):
            yield _linea("error", mensaje="Todas las filas tienen el mismo desenlace. "
                                          "Un modelo no puede aprender de eso.")
            return
        yield _linea("fase", n=3, titulo="Construir la etiqueta", estado="listo",
                     segundos=desde(), cifra=f"{y.mean() * 100:.2f} %",
                     detalle=f"{int(y.sum())} de {len(y)} reingresaron antes de 30 días")

        # ------------------------------------------------- 4. limpiar
        yield _linea("fase", n=4, titulo="Limpiar", estado="corriendo")
        quitar = np.zeros(len(crudo), dtype=bool)
        if "discharge_disposition_id" in crudo.columns:
            codigos = pd.to_numeric(crudo["discharge_disposition_id"], errors="coerce")
            quitar = codigos.isin(procesamiento_lotes.EXCLUIR_EGRESOS).to_numpy()
        X = X.loc[~quitar[: len(X)]].reset_index(drop=True)
        y = y[: len(quitar)][~quitar][: len(X)]
        yield _linea("fase", n=4, titulo="Limpiar", estado="listo", segundos=desde(),
                     cifra=f"{int(quitar.sum()):,}".replace(",", "."),
                     detalle="fallecimientos y cuidados paliativos fuera: esas personas no "
                             "pueden reingresar, y dejarlas enseña a predecir algo que no existe")

        # ------------------------------------- muestra para el modo rápido
        if len(X) > MUESTRA_RAPIDA:
            indices = np.random.default_rng(SEMILLA).choice(len(X), MUESTRA_RAPIDA, replace=False)
            X = X.iloc[indices].reset_index(drop=True)
            y = y[indices]
            yield _linea("aviso",
                         mensaje=f"Se toma una muestra de {MUESTRA_RAPIDA:,} filas para que esto "
                                 "termine en menos de un minuto en un servidor de un núcleo."
                                 .replace(",", "."))

        pacientes = (
            crudo.loc[~quitar, "patient_nbr"].to_numpy()[: len(X)]
            if "patient_nbr" in crudo.columns
            else np.arange(len(X))
        )
        if len(pacientes) != len(X):
            pacientes = np.arange(len(X))

        # ------------------------------------------------ 5. partir
        yield _linea("fase", n=5, titulo="Partir los datos", estado="corriendo")
        por_paciente = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=SEMILLA)
        ent_p, val_p = next(por_paciente.split(X, y, groups=pacientes))
        ent_a, val_a = train_test_split(np.arange(len(X)), test_size=0.3,
                                        random_state=SEMILLA, stratify=y)
        unicos = len(np.unique(pacientes))
        yield _linea("fase", n=5, titulo="Partir los datos", estado="listo", segundos=desde(),
                     cifra=f"{unicos:,}".replace(",", "."),
                     detalle=f"{unicos} pacientes distintos en {len(X)} hospitalizaciones")

        # --------------------------------- 6. la trampa de la exactitud
        yield _linea("fase", n=6, titulo="La línea base", estado="corriendo")
        mayoritario = np.zeros(len(val_p))
        exactitud = float((y[val_p] == 0).mean())
        yield _linea("leccion", clave="exactitud",
                     titulo="Un modelo que acierta casi siempre y no sirve",
                     cifras=[
                         {"v": f"{exactitud * 100:.1f} %", "n": "de exactitud, respondiendo siempre lo mismo"},
                         {"v": "0,500", "n": "de ROC-AUC: es lanzar una moneda"},
                         {"v": "0", "n": "pacientes detectados"},
                     ],
                     texto="Como solo reingresa uno de cada nueve, un modelo que siempre dice "
                           "que no acierta casi siempre. Por eso este proyecto no se mide con "
                           "exactitud sino con average precision, que sí castiga a quien no "
                           "alerta a nadie.")
        yield _linea("fase", n=6, titulo="La línea base", estado="listo", segundos=desde(),
                     cifra=f"{_ap(y[val_p], mayoritario):.4f}",
                     detalle="average precision del modelo que nunca alerta: es la prevalencia")

        # --------------------------------------- 7. regresión logística
        yield _linea("fase", n=7, titulo="Regresión logística", estado="corriendo")
        lineal = Pipeline([
            ("prep", _preparador(numericas, categoricas, para_lineal=True)),
            ("modelo", LogisticRegression(max_iter=600, class_weight="balanced")),
        ])
        lineal.fit(X.iloc[ent_p], y[ent_p])
        ap_lineal = _ap(y[val_p], lineal.predict_proba(X.iloc[val_p])[:, 1])
        yield _linea("fase", n=7, titulo="Regresión logística", estado="listo",
                     segundos=desde(), cifra=f"{ap_lineal:.4f}",
                     detalle="la referencia honesta: simple y explicable")

        # -------------------------- 8. Gradient Boosting, por paciente
        yield _linea("fase", n=8, titulo="Gradient Boosting", estado="corriendo",
                     detalle="esto es lo que tarda; son 120 árboles")
        _, ap_tr, ap_va, prob_va = _entrenar_gb(X, y, ent_p, val_p, numericas, categoricas)
        brecha = ap_tr - ap_va
        yield _linea("leccion", clave="sobreajuste",
                     titulo="Cuánto se memoriza el modelo",
                     cifras=[
                         {"v": f"{ap_tr:.4f}", "n": "con los datos que ya vio"},
                         {"v": f"{ap_va:.4f}", "n": "con datos nuevos"},
                         {"v": f"{brecha:+.4f}", "n": "la brecha entre los dos"},
                     ],
                     texto=(
                         "La diferencia entre las dos columnas es cuánto se aprendió los datos "
                         "de memoria. Un modelo que brilla en entrenamiento y cae en validación "
                         "va a fallar con pacientes nuevos.

"
                         f"Esta brecha de {brecha:.4f} es bastante mayor que la del modelo "
                         "oficial, que es 0,0538, y la razón vale la pena: aquí se entrena con "
                         "una fracción de los datos y sin parada temprana, que son justamente "
                         "las dos cosas que evitan que un modelo se memorice. Con menos datos, "
                         "cualquier modelo se los aprende más fácil.

"
                         "Por eso en el proyecto oficial se eligió la configuración de menor "
                         "brecha y no la de mejor puntaje."
                     ))
        yield _linea("fase", n=8, titulo="Gradient Boosting", estado="listo", segundos=desde(),
                     cifra=f"{ap_va:.4f}",
                     detalle=f"ROC-AUC {roc_auc_score(y[val_p], prob_va):.4f}")

        # ------------------------- 9. la partición mal hecha, si la pidió
        if particion == "azar":
            yield _linea("fase", n=9, titulo="Y ahora, partiendo al azar", estado="corriendo",
                         detalle="se entrena otra vez, repartiendo hospitalizaciones en vez de personas")
            _, _, ap_azar, _ = _entrenar_gb(X, y, ent_a, val_a, numericas, categoricas)
            compartidos = len(np.intersect1d(pacientes[ent_a], pacientes[val_a]))
            yield _linea("leccion", clave="particion",
                         titulo="Por qué nunca se parte al azar",
                         cifras=[
                             {"v": f"{ap_va:.4f}", "n": "partiendo por paciente, lo correcto"},
                             {"v": f"{ap_azar:.4f}", "n": "partiendo al azar"},
                             {"v": f"{compartidos:,}".replace(",", "."),
                              "n": "pacientes que quedaron a ambos lados"},
                         ],
                         texto=(
                             "Partir al azar puntúa mejor y el modelo no es mejor: es que "
                             f"{compartidos} personas tienen hospitalizaciones en los dos lados, "
                             "y el modelo las reconoce. Ese número de más no existe fuera del "
                             "laboratorio. Es el error más común en trabajos sobre este conjunto "
                             "de datos, y no avisa."
                         ) if ap_azar > ap_va else (
                             "Esta vez el azar no puntuó más alto, que pasa cuando hay pocas "
                             "personas repetidas en la muestra. El riesgo sigue siendo real: con "
                             "la cohorte completa, donde dieciséis mil personas aparecen varias "
                             "veces, la diferencia sí aparece."
                         ))
            yield _linea("fase", n=9, titulo="Y ahora, partiendo al azar", estado="listo",
                         segundos=desde(), cifra=f"{ap_azar:.4f}",
                         detalle=f"{ap_azar - ap_va:+.4f} frente a la partición correcta")

        # ----------------------------------------------- 10. el umbral
        siguiente = 10 if particion == "azar" else 9
        yield _linea("fase", n=siguiente, titulo="Elegir el umbral", estado="corriendo")
        opciones = []
        for objetivo in (0.5, 0.6, 0.7, 0.8):
            corte = float(np.quantile(prob_va, 1 - objetivo * y[val_p].mean() / max(prob_va.mean(), 1e-9)))
            alerta = prob_va >= corte
            detectados = int((alerta & (y[val_p] == 1)).sum())
            opciones.append({
                "umbral": round(corte, 4),
                "alertados": int(alerta.sum()),
                "pct_alertados": round(float(alerta.mean()), 4),
                "detecta": round(detectados / max(int(y[val_p].sum()), 1), 4),
                "acierta": round(detectados / max(int(alerta.sum()), 1), 4),
            })
        yield _linea("leccion", clave="umbral",
                     titulo="Dónde cortar no lo decide el modelo",
                     tabla=opciones,
                     texto="Cada fila es una decisión distinta sobre a cuánta gente llamar. "
                           "Alertar a más gente detecta más reingresos y acierta menos. No hay "
                           "un valor correcto: depende de cuántas llamadas puede hacer el "
                           "programa, y por eso lo fija la coordinación y no el modelo.")
        yield _linea("fase", n=siguiente, titulo="Elegir el umbral", estado="listo", segundos=desde(),
                     cifra=f"{len(opciones)}", detalle="cortes posibles, ninguno correcto por sí mismo")

        # ---------------------------------------- 11. contra el oficial
        oficial = datos.metricas_finales()
        yield _linea("fase", n=siguiente + 1, titulo="Comparar con el modelo oficial", estado="listo",
                     segundos=desde(), cifra=f"{ap_va:.4f}",
                     detalle=f"el oficial da {oficial['AP']:.4f} en su conjunto de prueba")
        yield _linea("cierre",
                     suyo=round(ap_va, 4),
                     oficial=round(float(oficial["AP"]), 4),
                     segundos=desde(),
                     texto="Su modelo y el oficial se entrenaron con particiones distintas, así "
                           "que no tienen que dar idéntico. Que queden cerca es justamente lo "
                           "que se espera, y es lo que hace reproducible el trabajo. "
                           "Este modelo vive en memoria y desaparece al cerrar: no reemplaza "
                           "al oficial ni se guarda en ninguna parte.")

    except Exception as error:  # noqa: BLE001
        # El tipo del error, nunca su texto: puede traer rutas del servidor.
        yield _linea("error", mensaje=f"El entrenamiento falló ({type(error).__name__}).")
    finally:
        if _ocupado.locked():
            _ocupado.release()


async def entrenar(
    archivo: UploadFile,
    particion: str = Form("paciente"),
    _=Depends(auth.exige("Entrenar en vivo")),
):
    contenido = await archivo.read()
    if len(contenido) > TOPE_BYTES:
        raise HTTPException(413, f"El archivo pesa más de {TOPE_BYTES // (1024 * 1024)} MB.")
    if not contenido:
        raise HTTPException(422, "El archivo llegó vacío.")
    if not _ocupado.acquire(blocking=False):
        raise HTTPException(
            429,
            "Ya hay un entrenamiento en curso en el servidor. Espere a que termine: "
            "con un solo núcleo, dos a la vez dejan la aplicación sin responder.",
        )

    return StreamingResponse(
        _corre(contenido, archivo.filename or "", particion),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def registrar(app: FastAPI) -> None:
    app.post("/api/entrenar")(entrenar)
