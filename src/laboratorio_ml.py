"""Laboratorio de entrenamiento independiente del modelo oficial.

Solo admite ejemplos etiquetados y grupos de pacientes; evita fugas entre
particiones y selecciona el algoritmo/umbral sin mirar el conjunto de prueba.
No persiste modelos ni modifica los resultados académicos existentes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score, confusion_matrix, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class DatosEntrenamientoInvalidos(ValueError):
    """Datos insuficientes o incompatibles para un experimento reproducible."""


def obtener_etiquetas(datos: pd.DataFrame) -> pd.Series:
    """Acepta etiqueta histórica UCI o la columna binaria y."""
    if "readmitted" in datos.columns:
        original = datos["readmitted"].astype("string")
        if not original.isin(["<30", ">30", "NO"]).all():
            raise DatosEntrenamientoInvalidos(
                "readmitted contiene etiquetas desconocidas o vacías."
            )
        return original.eq("<30").astype(int)
    if "y" in datos.columns:
        etiquetas = pd.to_numeric(datos["y"], errors="coerce")
        if etiquetas.isna().any() or not etiquetas.isin([0, 1]).all():
            raise DatosEntrenamientoInvalidos("y debe contener solo 0 y 1.")
        return etiquetas.astype(int)
    raise DatosEntrenamientoInvalidos(
        "Para entrenar se requiere una etiqueta real: readmitted o y."
    )


def particionar(X: pd.DataFrame, y: pd.Series, pacientes: pd.Series, semilla=42):
    """Separación aproximada 60/20/20 sin pacientes compartidos."""
    if len(X) < 120 or pacientes.nunique() < 30 or y.nunique() != 2:
        raise DatosEntrenamientoInvalidos(
            "Se requieren al menos 120 hospitalizaciones, 30 pacientes y ambas clases."
        )
    cv_prueba = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=semilla)
    idx_trainval, idx_test = next(cv_prueba.split(X, y, groups=pacientes))
    X_tv, y_tv, p_tv = X.iloc[idx_trainval], y.iloc[idx_trainval], pacientes.iloc[idx_trainval]
    cv_val = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=semilla + 1)
    idx_train_rel, idx_val_rel = next(cv_val.split(X_tv, y_tv, groups=p_tv))
    ids = {
        "entrenamiento": np.asarray(idx_trainval)[idx_train_rel],
        "validacion": np.asarray(idx_trainval)[idx_val_rel],
        "prueba": np.asarray(idx_test),
    }
    grupos = [set(pacientes.iloc[indices]) for indices in ids.values()]
    if (grupos[0] & grupos[1] or grupos[0] & grupos[2] or grupos[1] & grupos[2]):
        raise DatosEntrenamientoInvalidos("Se detectó un paciente compartido entre conjuntos.")
    if any(y.iloc[indices].nunique() != 2 for indices in ids.values()):
        raise DatosEntrenamientoInvalidos(
            "Alguna partición no contiene ambas clases; pruebe otro conjunto de datos."
        )
    return ids


def elegir_umbral(y_validacion, probabilidades, recall_minimo=0.60):
    """Umbral que maximiza precisión, sujeto a la sensibilidad de validación."""
    candidatos = np.unique(np.r_[0.0, probabilidades, 1.0])
    mejor = (0.0, -1.0)
    for umbral in candidatos:
        pred = probabilidades >= umbral
        sensibilidad = recall_score(y_validacion, pred, zero_division=0)
        if sensibilidad + 1e-12 < recall_minimo:
            continue
        precision = precision_score(y_validacion, pred, zero_division=0)
        if (precision, umbral) > (mejor[1], mejor[0]):
            mejor = (float(umbral), float(precision))
    return mejor[0]


def metricas(y, probabilidades, umbral):
    pred = np.asarray(probabilidades) >= umbral
    vn, fp, fn, vp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "AP": float(average_precision_score(y, probabilidades)),
        "ROC_AUC": float(roc_auc_score(y, probabilidades)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "VP": int(vp), "FN": int(fn), "FP": int(fp), "VN": int(vn),
    }


def entrenar_experimento(X, y, pacientes, numericas, categoricas,
                         neuronas=24, iteraciones=65, semilla=42):
    """Entrena mayoritario, regresión logística y red neuronal MLP.

    Selecciona por AP en validación; prueba solo una vez al final. Todos los
    imputadores, escaladores y codificadores se ajustan exclusivamente en train.
    """
    if not set(numericas + categoricas).issubset(X.columns):
        raise DatosEntrenamientoInvalidos("Faltan variables del modelo.")
    if not 8 <= neuronas <= 64 or not 30 <= iteraciones <= 120:
        raise DatosEntrenamientoInvalidos("Configuración de red fuera de rango.")
    if y.isna().any() or pacientes.isna().any():
        raise DatosEntrenamientoInvalidos("Hay etiquetas o identificadores de paciente vacíos.")
    if len(X) != len(y) or len(X) != len(pacientes):
        raise DatosEntrenamientoInvalidos("Tamaños diferentes de datos, etiquetas y pacientes.")
    # Evitar conversion de categorias como códigos administrativos a flotantes.
    X = X.copy().reset_index(drop=True)
    y = pd.Series(y).reset_index(drop=True).astype(int)
    pacientes = pd.Series(pacientes).reset_index(drop=True)
    for columna in categoricas:
        X[columna] = X[columna].fillna("Ausente").astype(str)
    for columna in numericas:
        X[columna] = pd.to_numeric(X[columna], errors="coerce").replace(
            [np.inf, -np.inf], np.nan
        )
    indices = particionar(X, y, pacientes, semilla)
    tr, va, te = (indices[k] for k in ("entrenamiento", "validacion", "prueba"))
    prep = ColumnTransformer([
        ("numericas", Pipeline([
            ("imputar", SimpleImputer(strategy="median", keep_empty_features=True)),
            ("escalar", StandardScaler()),
        ]), numericas),
        ("categoricas", OneHotEncoder(handle_unknown="ignore",
                                     sparse_output=False), categoricas),
    ])
    modelos = {
        "Mayoritario": DummyClassifier(strategy="prior"),
        "Regresion logistica": LogisticRegression(
            max_iter=350, class_weight="balanced", random_state=semilla
        ),
        "Red neuronal MLP": MLPClassifier(
            hidden_layer_sizes=(int(neuronas),),
            max_iter=int(iteraciones), early_stopping=True,
            n_iter_no_change=10, random_state=semilla,
        ),
    }
    filas, ajustados, probabilidades_val = [], {}, {}
    for nombre, algoritmo in modelos.items():
        pipeline = Pipeline([("preprocesamiento", prep), ("modelo", algoritmo)])
        pipeline.fit(X.iloc[tr], y.iloc[tr])
        prob = pipeline.predict_proba(X.iloc[va])[:, 1]
        registro = metricas(y.iloc[va], prob, umbral=0.5)
        filas.append({"modelo": nombre, "AP_validacion": registro["AP"],
                      "ROC_AUC_validacion": registro["ROC_AUC"]})
        ajustados[nombre] = pipeline
        probabilidades_val[nombre] = prob
    comparacion = pd.DataFrame(filas).sort_values(
        "AP_validacion", ascending=False
    ).reset_index(drop=True)
    elegido = str(comparacion.iloc[0]["modelo"])
    umbral = elegir_umbral(y.iloc[va], probabilidades_val[elegido])
    prob_test = ajustados[elegido].predict_proba(X.iloc[te])[:, 1]
    final = metricas(y.iloc[te], prob_test, umbral)
    distribucion = pd.DataFrame([
        {"conjunto": nombre, "registros": len(ind),
         "pacientes": int(pacientes.iloc[ind].nunique()),
         "prevalencia": float(y.iloc[ind].mean())}
        for nombre, ind in indices.items()
    ])
    return {
        "comparacion": comparacion,
        "elegido": elegido,
        "umbral": umbral,
        "prueba": final,
        "particiones": distribucion,
        "modelo_experimental": ajustados[elegido],
        "predicciones_prueba": pd.DataFrame({
            "probabilidad": prob_test,
            "reingreso_real": y.iloc[te].to_numpy(),
        }),
    }
