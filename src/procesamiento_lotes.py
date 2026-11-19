"""Procesamiento de lotes para inferencia; reproduce las transformaciones del notebook 01.

No reentrena ni altera el modelo. Los archivos cargados se procesan en memoria.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

EXCLUIR_EGRESOS = {11, 13, 14, 19, 20, 21}
MEDICAMENTOS = [
    "metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
    "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
    "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide",
    "examide", "citoglipton", "insulin", "glyburide-metformin",
    "glipizide-metformin", "glimepiride-pioglitazone",
    "metformin-rosiglitazone", "metformin-pioglitazone",
]
EDADES = {f"[{a}-{a+10})": a + 5 for a in range(0, 100, 10)}
NUEVAS_NUMERICAS = {
    "edad_num", "servicios_previos", "tuvo_ingreso_previo", "meds_por_dia",
    "labs_por_dia", "num_meds_activos", "hubo_cambio_med", "a1c_medida",
    "glu_medida",
}
NUEVAS_CATEGORICAS = {"grupo_diag_1", "grupo_diag_2", "grupo_diag_3"}


class ArchivoIncompatible(ValueError):
    """El archivo no contiene los campos necesarios para inferencia."""


def agrupar_diagnostico(codigo):
    """Agrupación ICD-9 idéntica a la usada en el entrenamiento."""
    if pd.isna(codigo):
        return "Desconocido"
    texto = str(codigo)
    if texto.startswith(("V", "E")):
        return "Otros"
    try:
        valor = float(texto)
    except ValueError:
        return "Otros"
    entero = int(valor)
    if 390 <= valor <= 459 or entero == 785:
        return "Circulatorio"
    if 460 <= valor <= 519 or entero == 786:
        return "Respiratorio"
    if 520 <= valor <= 579 or entero == 787:
        return "Digestivo"
    if entero == 250:
        return "Diabetes"
    if 800 <= valor <= 999:
        return "Lesiones"
    if 710 <= valor <= 739:
        return "Musculoesqueletico"
    if 580 <= valor <= 629 or entero == 788:
        return "Genitourinario"
    if 140 <= valor <= 239:
        return "Neoplasias"
    return "Otros"


def detectar_formato(df, numericas, categoricas):
    """Admite archivos originales de UCI o las 50 columnas ya preparadas."""
    preparadas = list(numericas) + list(categoricas)
    if set(preparadas).issubset(df.columns):
        return "preparado"
    crudas = ((set(preparadas) - NUEVAS_NUMERICAS - NUEVAS_CATEGORICAS)
              | {"age", "diag_1", "diag_2", "diag_3", "examide", "citoglipton"})
    faltantes = sorted(crudas - set(df.columns))
    if faltantes:
        raise ArchivoIncompatible(
            "El CSV no tiene el esquema original de UCI ni las 50 variables del modelo. "
            "Columnas necesarias ausentes: " + ", ".join(faltantes)
        )
    return "uci"


def preparar_lote(df, numericas, categoricas):
    """Devuelve (X_validas, descartes, diagnóstico). Sin alterar el CSV de origen.

    Las filas excluidas por tipo de egreso o inválidas no se predicen.
    Valores faltantes restantes se dejan al pipeline entrenado: nunca se imputan
    usando estadísticas del CSV nuevo.
    """
    if df.empty:
        raise ArchivoIncompatible("El archivo CSV no contiene hospitalizaciones.")
    if df.columns.duplicated().any():
        raise ArchivoIncompatible("El CSV contiene nombres de columnas duplicados.")
    formato = detectar_formato(df, numericas, categoricas)
    trabajo = df.copy().replace("?", np.nan)
    trabajo.index = pd.RangeIndex(start=0, stop=len(trabajo), name="fila_original")
    motivo = pd.Series("", index=trabajo.index, dtype="object")

    for columna in ["time_in_hospital", "num_medications", "num_lab_procedures",
                    "number_inpatient", "number_emergency", "number_outpatient",
                    "num_procedures", "number_diagnoses"]:
        if columna in trabajo:
            trabajo[columna] = pd.to_numeric(trabajo[columna], errors="coerce")

    estancia = trabajo["time_in_hospital"]
    invalida = estancia.isna() | (estancia <= 0)
    motivo.loc[invalida] = "Estancia hospitalaria ausente o no positiva"
    if "discharge_disposition_id" in trabajo:
        egreso = pd.to_numeric(trabajo["discharge_disposition_id"], errors="coerce")
        excluidas = egreso.isin(EXCLUIR_EGRESOS)
        motivo.loc[excluidas] = "Egreso excluido de la cohorte (fallecimiento/paliativos)"

    if formato == "uci":
        trabajo["edad_num"] = trabajo["age"].map(EDADES)
        motivo.loc[trabajo["edad_num"].isna() & motivo.eq("")] = "Edad no reconocida"
        for columna in ["number_inpatient", "number_emergency", "number_outpatient"]:
            neg = trabajo[columna].notna() & (trabajo[columna] < 0)
            motivo.loc[neg & motivo.eq("")] = f"Valor negativo en {columna}"
        trabajo["servicios_previos"] = (trabajo["number_outpatient"]
                                        + trabajo["number_emergency"]
                                        + trabajo["number_inpatient"])
        trabajo["tuvo_ingreso_previo"] = (trabajo["number_inpatient"] > 0).astype(int)
        trabajo["meds_por_dia"] = trabajo["num_medications"] / estancia
        trabajo["labs_por_dia"] = trabajo["num_lab_procedures"] / estancia
        trabajo["num_meds_activos"] = (trabajo[MEDICAMENTOS].fillna("nan") != "No").sum(axis=1)
        trabajo["hubo_cambio_med"] = (trabajo["change"] == "Ch").astype(int)
        trabajo["a1c_medida"] = (trabajo["A1Cresult"].notna()
                                 & (trabajo["A1Cresult"] != "None")).astype(int)
        trabajo["glu_medida"] = (trabajo["max_glu_serum"].notna()
                                 & (trabajo["max_glu_serum"] != "None")).astype(int)
        for i in (1, 2, 3):
            trabajo[f"grupo_diag_{i}"] = trabajo[f"diag_{i}"].map(agrupar_diagnostico)

    for col in numericas:
        trabajo[col] = pd.to_numeric(trabajo[col], errors="coerce")
    for col in ["num_medications", "num_lab_procedures", "num_procedures", "number_diagnoses"]:
        if col in trabajo:
            invalida = trabajo[col].notna() & (trabajo[col] < 0)
            motivo.loc[invalida & motivo.eq("")] = f"Valor negativo en {col}"
    for col in categoricas:
        trabajo[col] = trabajo[col].astype(str)

    validas = motivo.eq("")
    columnas = list(numericas) + list(categoricas)
    X = trabajo.loc[validas, columnas].copy()
    descartes = pd.DataFrame({"fila_original": trabajo.index[~validas] + 2,
                               "motivo": motivo.loc[~validas].values})
    diagnostico = {
        "formato": formato,
        "recibidas": len(df),
        "validas": int(validas.sum()),
        "excluidas": int((~validas).sum()),
        "faltantes_por_columna": df.replace("?", np.nan).isna().sum().to_dict(),
    }
    return X, descartes, diagnostico


def predecir_lote(modelo, X, umbral):
    """Predicciones en el orden original, con línea CSV (incluye cabecera)."""
    if X.empty:
        return pd.DataFrame(columns=["fila_csv", "probabilidad", "alerta"])
    probabilidades = modelo.predict_proba(X)[:, 1]
    return pd.DataFrame({
        "fila_csv": X.index.to_numpy() + 2,
        "probabilidad": probabilidades,
        "alerta": np.where(probabilidades >= umbral, "Seguimiento", "Sin alerta"),
    })
