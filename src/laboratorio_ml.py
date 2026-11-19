"""Comparación reproducible de dos procesos de entrenamiento: GB y MLP.

Cada candidato tiene su propio preprocesamiento e hiperparámetros. La selección
se hace exclusivamente con validación; ambos resultados de prueba se calculan
DESPUÉS de congelar el ganador, sin usarlos para escogerlo. El modelo oficial
versionado nunca se sobrescribe.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.metrics import (average_precision_score, confusion_matrix,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


class DatosEntrenamientoInvalidos(ValueError):
    """Datos insuficientes o incompatibles para comparar modelos."""


NOMBRES_MODELOS = ("Gradient Boosting", "Red neuronal MLP")


def obtener_etiquetas(datos: pd.DataFrame) -> pd.Series:
    """Etiquetas verificadas, no probabilidades del modelo anterior."""
    if "readmitted" in datos:
        origen = datos["readmitted"].astype("string")
        if not origen.isin(["<30", ">30", "NO"]).all():
            raise DatosEntrenamientoInvalidos(
                "La columna readmitted solo puede contener <30, >30 o NO."
            )
        return origen.eq("<30").astype(int)
    if "y" in datos:
        y = pd.to_numeric(datos["y"], errors="coerce")
        if y.isna().any() or not y.isin([0, 1]).all():
            raise DatosEntrenamientoInvalidos("La columna y debe tener solo 0 y 1.")
        return y.astype(int)
    raise DatosEntrenamientoInvalidos(
        "El archivo necesita la etiqueta real readmitted o y para entrenar."
    )


def particionar(X, y, pacientes, semilla=42):
    """División 60/20/20 aproximada sin pacientes repetidos entre conjuntos."""
    if len(X) < 120 or pd.Series(pacientes).nunique() < 30 or pd.Series(y).nunique() != 2:
        raise DatosEntrenamientoInvalidos(
            "Se necesitan al menos 120 registros, 30 pacientes y ambas clases."
        )
    try:
        cv1 = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=semilla)
        tv, te = next(cv1.split(X, y, groups=pacientes))
        cv2 = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=semilla + 1)
        tr_rel, va_rel = next(cv2.split(X.iloc[tv], y.iloc[tv],
                                        groups=pacientes.iloc[tv]))
    except ValueError as error:
        raise DatosEntrenamientoInvalidos(
            f"No se pudieron repartir los grupos en tres conjuntos: {error}"
        ) from error
    indices = {
        "entrenamiento": np.asarray(tv)[tr_rel],
        "validacion": np.asarray(tv)[va_rel],
        "prueba": np.asarray(te),
    }
    conjuntos = [set(pacientes.iloc[i]) for i in indices.values()]
    if any(conjuntos[i] & conjuntos[j] for i, j in ((0, 1), (0, 2), (1, 2))):
        raise DatosEntrenamientoInvalidos("Fuga: pacientes en varias particiones.")
    if any(y.iloc[i].nunique() != 2 for i in indices.values()):
        raise DatosEntrenamientoInvalidos(
            "Alguna partición tiene una sola clase; use un CSV más equilibrado."
        )
    return indices


def elegir_umbral(y_val, prob, recall_minimo=0.60):
    """Fija el umbral por validación, priorizando precisión con recall mínimo."""
    y = np.asarray(y_val)
    prob = np.asarray(prob, dtype=float)
    if len(y) != len(prob) or not np.isfinite(prob).all():
        raise DatosEntrenamientoInvalidos("Probabilidades de validación inválidas.")
    candidatos = np.unique(np.r_[0.0, prob, 1.0])
    # Procesamiento vectorial y lotes pequeños; evita llamar recall_score por
    # cada observación (en datos reales serían miles de llamadas Python).
    mejor = (float(candidatos[0]), -1.0)
    positivos = max(int((y == 1).sum()), 1)
    for umbral in candidatos:
        alertas = prob >= umbral
        vp = int(((y == 1) & alertas).sum())
        recall = vp / positivos
        if recall < recall_minimo - 1e-12:
            continue
        precision = vp / max(int(alertas.sum()), 1)
        if (precision, float(umbral)) > (mejor[1], mejor[0]):
            mejor = (float(umbral), precision)
    return mejor[0]


def metricas(y, prob, umbral):
    y = np.asarray(y, dtype=int)
    prob = np.asarray(prob, dtype=float)
    alerta = prob >= umbral
    vn, fp, fn, vp = confusion_matrix(y, alerta, labels=[0, 1]).ravel()
    return {
        "AP": float(average_precision_score(y, prob)),
        "ROC_AUC": float(roc_auc_score(y, prob)),
        "recall": float(recall_score(y, alerta, zero_division=0)),
        "precision": float(precision_score(y, alerta, zero_division=0)),
        "VP": int(vp), "FN": int(fn), "FP": int(fp), "VN": int(vn),
    }


def _procesador_gb(numericas, categoricas):
    """Mismo enfoque del notebook 03: valores numéricos sin escalar y ordinales."""
    return ColumnTransformer([
        ("numericas", "passthrough", numericas),
        ("categoricas", Pipeline([
            ("imputar", SimpleImputer(strategy="constant", fill_value="Ausente")),
            ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value",
                                       unknown_value=-1)),
        ]), categoricas),
    ])


def _procesador_mlp(numericas, categoricas):
    """La MLP sí requiere estandarización y one-hot, ajustados solo en train."""
    return ColumnTransformer([
        ("numericas", Pipeline([
            ("imputar", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("escalar", StandardScaler()),
        ]), numericas),
        ("categoricas", Pipeline([
            ("imputar", SimpleImputer(strategy="constant", fill_value="Ausente")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), categoricas),
    ])


def _candidatos(numericas, categoricas, neuronas, iteraciones, busqueda, semilla):
    mascara = [False] * len(numericas) + [True] * len(categoricas)
    # HistGradientBoosting tolera NaN en columnas numéricas.
    gb_config = [
        {"learning_rate": 0.05, "max_leaf_nodes": 15,
         "min_samples_leaf": 100, "l2_regularization": 0.5},
        {"learning_rate": 0.08, "max_leaf_nodes": 31,
         "min_samples_leaf": 50, "l2_regularization": 1.0},
        {"learning_rate": 0.03, "max_leaf_nodes": 15,
         "min_samples_leaf": 50, "l2_regularization": 0.5},
    ]
    mlp_config = [
        {"hidden_layer_sizes": (int(neuronas),), "alpha": 0.0001},
        {"hidden_layer_sizes": (int(neuronas),), "alpha": 0.01},
        {"hidden_layer_sizes": (int(neuronas), int(max(4, neuronas // 2))),
         "alpha": 0.001},
    ]
    cantidad = int(busqueda)
    for modelo, configuraciones in ((NOMBRES_MODELOS[0], gb_config[:cantidad]),
                                     (NOMBRES_MODELOS[1], mlp_config[:cantidad])):
        for numero, conf in enumerate(configuraciones, 1):
            if modelo == NOMBRES_MODELOS[0]:
                estimador = HistGradientBoostingClassifier(
                    categorical_features=mascara, max_iter=120,
                    early_stopping=False, random_state=semilla, **conf
                )
                procesador = _procesador_gb(numericas, categoricas)
            else:
                estimador = MLPClassifier(
                    max_iter=int(iteraciones), early_stopping=False,
                    random_state=semilla, n_iter_no_change=10, **conf
                )
                procesador = _procesador_mlp(numericas, categoricas)
            yield modelo, numero, conf, Pipeline([
                ("preprocesamiento", procesador), ("modelo", estimador)
            ])


def entrenar_experimento(X, y, pacientes, numericas, categoricas,
                         neuronas=24, iteraciones=65, semilla=42, busqueda=2):
    """Dos modelos, dos resultados de prueba, una selección por validación.

    Ajusta 1-3 configuraciones por modelo usando el mismo train/valid/test.
    La búsqueda es deliberadamente acotada para Streamlit, no un HPO exhaustivo.
    """
    if not 8 <= neuronas <= 64 or not 30 <= iteraciones <= 120:
        raise DatosEntrenamientoInvalidos("Parámetros de la MLP fuera de rango.")
    if busqueda not in (1, 2, 3):
        raise DatosEntrenamientoInvalidos("La búsqueda admite 1, 2 o 3 configuraciones.")
    if not set(numericas + categoricas).issubset(X.columns):
        raise DatosEntrenamientoInvalidos("El archivo no contiene todos los predictores.")
    if len(X) != len(y) or len(X) != len(pacientes):
        raise DatosEntrenamientoInvalidos("Longitudes incompatibles.")
    X = X.copy().reset_index(drop=True)
    y = pd.Series(y).reset_index(drop=True)
    pacientes = pd.Series(pacientes).reset_index(drop=True)
    if y.isna().any() or not y.isin([0, 1]).all() or pacientes.isna().any():
        raise DatosEntrenamientoInvalidos("Etiquetas o pacientes inválidos.")
    y = y.astype(int)
    for columna in categoricas:
        X[columna] = X[columna].astype(object).where(X[columna].notna(), np.nan)
        X[columna] = X[columna].map(
            lambda v: str(v) if pd.notna(v) else np.nan
        )
    for columna in numericas:
        X[columna] = pd.to_numeric(X[columna], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
    indices = particionar(X, y, pacientes, semilla)
    tr, va, te = [indices[k] for k in ("entrenamiento", "validacion", "prueba")]
    historial = []
    finales = {}
    for nombre, numero, params, pipeline in _candidatos(
        numericas, categoricas, neuronas, iteraciones, busqueda, semilla
    ):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            pipeline.fit(X.iloc[tr], y.iloc[tr])
        prob_tr = pipeline.predict_proba(X.iloc[tr])[:, 1]
        prob_va = pipeline.predict_proba(X.iloc[va])[:, 1]
        ap_tr = float(average_precision_score(y.iloc[tr], prob_tr))
        ap_va = float(average_precision_score(y.iloc[va], prob_va))
        registro = {
            "modelo": nombre, "configuracion": numero,
            "parametros": str(params), "AP_entrenamiento": ap_tr,
            "AP_validacion": ap_va,
            "ROC_AUC_validacion": float(roc_auc_score(y.iloc[va], prob_va)),
            "brecha_AP": ap_tr - ap_va,
        }
        historial.append(registro)
        if nombre not in finales or ap_va > finales[nombre]["ap_val"]:
            finales[nombre] = {
                "pipeline": pipeline, "ap_val": ap_va, "prob_val": prob_va,
                "registro": registro, "parametros": params,
            }

    # Política explícita: se decide por AP en validación; nunca por prueba.
    ganador = max(NOMBRES_MODELOS, key=lambda n: finales[n]["ap_val"])
    comparacion = []
    predicciones = {}
    curvas = {}
    for nombre in NOMBRES_MODELOS:
        elegido = finales[nombre]
        umbral = elegir_umbral(y.iloc[va], elegido["prob_val"])
        prob_test = elegido["pipeline"].predict_proba(X.iloc[te])[:, 1]
        met_test = metricas(y.iloc[te], prob_test, umbral)
        registro = elegido["registro"]
        comparacion.append({
            "modelo": nombre, "AP_entrenamiento": registro["AP_entrenamiento"],
            "AP_validacion": registro["AP_validacion"],
            "AP_prueba": met_test["AP"],
            "ROC_AUC_validacion": registro["ROC_AUC_validacion"],
            "ROC_AUC_prueba": met_test["ROC_AUC"],
            "recall_prueba": met_test["recall"],
            "precision_prueba": met_test["precision"],
            "brecha_AP": registro["brecha_AP"], "umbral": umbral,
            "VP": met_test["VP"], "FN": met_test["FN"],
            "FP": met_test["FP"], "VN": met_test["VN"],
            "seleccionado": nombre == ganador,
        })
        predicciones[nombre] = pd.DataFrame({
            "probabilidad": prob_test, "reingreso_real": y.iloc[te].to_numpy(),
        })
        if nombre == "Red neuronal MLP":
            # Curva auténtica de pérdida durante el entrenamiento.
            perdidas = elegido["pipeline"].named_steps["modelo"].loss_curve_
            curvas[nombre] = pd.DataFrame({
                "iteracion": range(1, len(perdidas) + 1),
                "perdida_entrenamiento": perdidas,
            })
    particiones = pd.DataFrame([
        {"conjunto": k, "registros": len(i),
         "pacientes": int(pacientes.iloc[i].nunique()),
         "prevalencia": float(y.iloc[i].mean())}
        for k, i in indices.items()
    ])
    return {
        "comparacion": pd.DataFrame(comparacion),
        "busqueda": pd.DataFrame(historial),
        "elegido": ganador,
        "justificacion": (
            f"{ganador} obtuvo la mejor Average Precision de validación "
            f"({finales[ganador]['ap_val']:.4f}). Ambos modelos se evaluaron "
            "en los mismos pacientes y particiones; las métricas de prueba "
            "solo se muestran después de decidir el ganador."
        ),
        "particiones": particiones, "curvas": curvas,
        "modelos": {n: finales[n]["pipeline"] for n in NOMBRES_MODELOS},
        "predicciones_prueba": predicciones,
        "parametros": {n: finales[n]["parametros"] for n in NOMBRES_MODELOS},
    }
