# -*- coding: utf-8 -*-
"""Cargue de archivos que no traen exactamente las columnas del modelo.

El problema real: quien usa esto no tiene tiempo de revisar que su archivo tenga
las 50 variables con los nombres exactos del entrenamiento. Antes la aplicación
rechazaba el archivo entero y listaba 40 columnas ausentes, que no le sirve a nadie.

Lo que hace este módulo:

1. **Reconoce nombres equivalentes.** `length_of_stay` es `time_in_hospital`,
   `num_previous_admissions` es `number_inpatient`, y así. La comparación ignora
   mayúsculas, acentos, guiones y espacios.
2. **Rellena lo que falte** con el valor típico del entrenamiento, igual que hace
   el formulario individual con las 35 variables que no pregunta.
3. **Dice cuánto del modelo queda cubierto de verdad**, usando la importancia por
   permutación medida sobre el conjunto de prueba.

Ese tercer punto es el importante. Rellenar con el valor típico siempre produce
*un* número, y ahí está el peligro: un archivo que no trae ninguna variable útil
devolvería el riesgo del paciente promedio para todo el mundo, con apariencia de
predicción. Por eso la cobertura se calcula y se muestra siempre.
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent

# nombre alternativo -> nombre que espera el modelo (o que espera el preparador de UCI)
ALIAS = {
    # identificación y demografía
    "age": "age", "edad": "age", "age_years": "age", "patient_age": "age",
    "gender": "gender", "sexo": "gender", "sex": "gender",
    # uso previo de servicios
    "num_previous_admissions": "number_inpatient",
    "previous_admissions": "number_inpatient",
    "prior_admissions": "number_inpatient",
    "hospitalizaciones_previas": "number_inpatient",
    "inpatient_visits": "number_inpatient",
    "emergency_visits": "number_emergency",
    "er_visits": "number_emergency",
    "urgencias": "number_emergency",
    "outpatient_visits": "number_outpatient",
    "consultas_externas": "number_outpatient",
    # esta hospitalización
    "length_of_stay": "time_in_hospital",
    "los": "time_in_hospital",
    "days_in_hospital": "time_in_hospital",
    "estancia": "time_in_hospital",
    "dias_estancia": "time_in_hospital",
    "medications_count": "num_medications",
    "num_meds": "num_medications",
    "medicamentos": "num_medications",
    "procedures_count": "num_procedures",
    "procedimientos": "num_procedures",
    "lab_procedures": "num_lab_procedures",
    "num_labs": "num_lab_procedures",
    "chronic_conditions": "number_diagnoses",
    "diagnoses_count": "number_diagnoses",
    "num_diagnoses": "number_diagnoses",
    "diagnosticos": "number_diagnoses",
    # administrativas
    "admission_type": "admission_type_id",
    "tipo_ingreso": "admission_type_id",
    "discharge_disposition": "discharge_disposition_id",
    "discharge_type": "discharge_disposition_id",
    "tipo_egreso": "discharge_disposition_id",
    "admission_source": "admission_source_id",
    "specialty": "medical_specialty",
    "especialidad": "medical_specialty",
    # laboratorio
    "a1c": "A1Cresult", "hba1c": "A1Cresult", "last_hemoglobin": "A1Cresult",
    "glucose": "max_glu_serum", "last_glucose": "max_glu_serum",
    # medicación
    "insulin_use": "insulin",
    "medication_change": "change",
    "diabetes_med": "diabetesMed",
}

# columnas que claramente no son predictores y nunca deben confundirse con uno
IGNORAR = {"patient_id", "encounter_id", "patient_nbr", "id", "index",
           "readmitted", "readmission", "readmission_risk", "y", "target", "label"}


def normalizar(nombre: str) -> str:
    """'Días de Estancia' y 'dias-estancia' deben ser el mismo nombre."""
    texto = unicodedata.normalize("NFKD", str(nombre))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def mapear_columnas(df: pd.DataFrame, esperadas) -> tuple[pd.DataFrame, dict]:
    """Renombra lo que se reconozca. Devuelve el marco y qué se reconoció."""
    esperadas_norm = {normalizar(c): c for c in esperadas}
    alias_norm = {normalizar(k): v for k, v in ALIAS.items()}

    renombres, reconocidas = {}, {}
    for columna in df.columns:
        clave = normalizar(columna)
        if clave in IGNORAR or columna in IGNORAR:
            continue
        destino = esperadas_norm.get(clave) or alias_norm.get(clave)
        if destino and destino not in renombres.values():
            if destino != columna:
                renombres[columna] = destino
            reconocidas[destino] = columna
    return df.rename(columns=renombres), reconocidas


def _importancias():
    ruta = BASE / "reports" / "importancia_permutacion.csv"
    if not ruta.exists():
        return {}
    tabla = pd.read_csv(ruta)
    positivas = tabla[tabla.caida_AP > 0]
    total = positivas.caida_AP.sum()
    if total <= 0:
        return {}
    return dict(zip(positivas.variable, positivas.caida_AP / total))


def cobertura(presentes) -> tuple[float, list]:
    """Qué fracción del poder predictivo del modelo cubre este archivo.

    No cuenta columnas: pesa cada una por cuánto cae el AP cuando se desordena.
    Traer 40 variables irrelevantes y ninguna de las dos que mandan da una
    cobertura baja, que es justo lo que hay que saber.
    """
    pesos = _importancias()
    if not pesos:
        return 0.0, []
    cubierto = sum(peso for var, peso in pesos.items() if var in presentes)
    faltan = sorted(((var, peso) for var, peso in pesos.items()
                     if var not in presentes and peso >= 0.01),
                    key=lambda par: -par[1])
    return cubierto, faltan


def completar(df: pd.DataFrame, numericas, categoricas, por_defecto):
    """Añade las columnas que falten con el valor típico del entrenamiento."""
    trabajo = df.copy()
    rellenadas = []
    for columna in list(numericas) + list(categoricas):
        if columna not in trabajo.columns:
            trabajo[columna] = por_defecto[columna]
            rellenadas.append(columna)
        elif trabajo[columna].isna().all():
            trabajo[columna] = por_defecto[columna]
            rellenadas.append(columna)
    return trabajo, rellenadas


# variable derivada -> columnas que hacen falta para poder calcularla
DERIVADAS = {
    "edad_num": ["age"],
    "grupo_diag_1": ["diag_1"],
    "grupo_diag_2": ["diag_2"],
    "grupo_diag_3": ["diag_3"],
    "servicios_previos": ["number_inpatient", "number_emergency", "number_outpatient"],
    "tuvo_ingreso_previo": ["number_inpatient"],
    "meds_por_dia": ["num_medications", "time_in_hospital"],
    "labs_por_dia": ["num_lab_procedures", "time_in_hospital"],
    "hubo_cambio_med": ["change"],
    "a1c_medida": ["A1Cresult"],
    "glu_medida": ["max_glu_serum"],
}


def diagnosticar(df: pd.DataFrame):
    """Qué trae el archivo, antes de intentar nada."""
    cols = json.loads((BASE / "data/processed/columnas.json").read_text(encoding="utf-8"))
    esperadas = cols["numericas"] + cols["categoricas"]
    crudas_uci = ["age", "diag_1", "diag_2", "diag_3", "time_in_hospital",
                  "num_medications", "num_lab_procedures", "number_inpatient"]

    mapeado, reconocidas = mapear_columnas(df, esperadas + crudas_uci)

    # las derivadas no vienen en el archivo, se calculan: cuentan como cubiertas
    # siempre que estén sus ingredientes
    disponibles = set(reconocidas)
    for derivada, ingredientes in DERIVADAS.items():
        if derivada not in disponibles and all(i in disponibles for i in ingredientes):
            disponibles.add(derivada)

    cubierto, faltan = cobertura(disponibles)
    diagnostico_extra = disponibles
    return {
        "marco": mapeado,
        "reconocidas": reconocidas,
        "sin_reconocer": [c for c in df.columns
                          if c not in reconocidas.values() and c not in IGNORAR],
        "cobertura": cubierto,
        "faltan_importantes": faltan,
    }


def preparar_tolerante(df, numericas, categoricas, por_defecto):
    """Construye las 50 variables a partir de lo que el archivo alcance a dar.

    Lo que falte toma el valor típico del entrenamiento. Eso siempre produce un
    número, por eso esta función devuelve además la cobertura: sin ella, un
    archivo sin información útil daría el riesgo del paciente promedio para todas
    las filas, con toda la apariencia de ser una predicción.
    """
    from src.procesamiento_lotes import EDADES, a_texto, agrupar_diagnostico

    informe = diagnosticar(df)
    t = informe["marco"].copy()

    # edad: puede venir en los rangos de UCI ("[70-80)") o en años
    if "age" in t.columns and "edad_num" not in t.columns:
        if t["age"].dtype == object:
            convertida = t["age"].map(EDADES)
            if convertida.isna().all():
                convertida = pd.to_numeric(t["age"], errors="coerce")
        else:
            convertida = pd.to_numeric(t["age"], errors="coerce")
        t["edad_num"] = convertida

    for i in (1, 2, 3):
        if f"diag_{i}" in t.columns and f"grupo_diag_{i}" not in t.columns:
            t[f"grupo_diag_{i}"] = t[f"diag_{i}"].map(agrupar_diagnostico)

    previos = [c for c in ("number_inpatient", "number_emergency", "number_outpatient")
               if c in t.columns]
    if previos and "servicios_previos" not in t.columns:
        t["servicios_previos"] = sum(pd.to_numeric(t[c], errors="coerce").fillna(0)
                                     for c in previos)
    if "number_inpatient" in t.columns and "tuvo_ingreso_previo" not in t.columns:
        t["tuvo_ingreso_previo"] = (pd.to_numeric(t["number_inpatient"],
                                                  errors="coerce").fillna(0) > 0).astype(int)

    if "time_in_hospital" in t.columns:
        dias = pd.to_numeric(t["time_in_hospital"], errors="coerce").clip(lower=1)
        for origen, destino in (("num_medications", "meds_por_dia"),
                                ("num_lab_procedures", "labs_por_dia")):
            if origen in t.columns and destino not in t.columns:
                t[destino] = pd.to_numeric(t[origen], errors="coerce") / dias

    for origen, destino in (("A1Cresult", "a1c_medida"), ("max_glu_serum", "glu_medida")):
        if origen in t.columns and destino not in t.columns:
            t[destino] = t[origen].notna().astype(int)
    if "change" in t.columns and "hubo_cambio_med" not in t.columns:
        t["hubo_cambio_med"] = (t["change"].astype(str) == "Ch").astype(int)

    t, rellenadas = completar(t, numericas, categoricas, por_defecto)

    for columna in numericas:
        t[columna] = pd.to_numeric(t[columna], errors="coerce")
        t[columna] = t[columna].replace([float("inf"), float("-inf")], pd.NA)
        if t[columna].isna().all():
            t[columna] = por_defecto[columna]
    for columna in categoricas:
        t[columna] = a_texto(t[columna])

    X = t[list(numericas) + list(categoricas)].copy()
    informe["rellenadas"] = rellenadas
    informe["filas"] = len(X)
    return X, informe
