# -*- coding: utf-8 -*-
"""Calcula la estadística descriptiva de la cohorte y la deja en reports/.

Se precalcula en vez de hacerlo en la aplicación porque `data/processed/` no se
versiona: en el servidor no existe. Lo que sí viaja al servidor son estas tablas,
que pesan unos pocos kilobytes.

Genera:
  reports/descriptiva_numericas.csv    media, mediana, moda, desviación, cuartiles
  reports/descriptiva_categoricas.csv  valores distintos, moda y su frecuencia
  reports/descriptiva_resumen.json     conteos de la cohorte y de la partición
  reports/descriptiva_histogramas.csv  distribución por tramos de las numéricas
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent
REP = BASE / "reports"

# nombre en español de cada variable, para que la tabla se lea sin diccionario
NOMBRES = {
    "edad_num": "Edad",
    "time_in_hospital": "Días de estancia",
    "num_lab_procedures": "Pruebas de laboratorio",
    "num_procedures": "Procedimientos",
    "num_medications": "Medicamentos administrados",
    "number_outpatient": "Consultas externas (año previo)",
    "number_emergency": "Visitas a urgencias (año previo)",
    "number_inpatient": "Hospitalizaciones previas (año previo)",
    "number_diagnoses": "Diagnósticos registrados",
    "servicios_previos": "Servicios previos (derivada)",
    "tuvo_ingreso_previo": "Tuvo ingreso previo (0/1)",
    "meds_por_dia": "Medicamentos por día (derivada)",
    "labs_por_dia": "Pruebas por día (derivada)",
    "num_meds_activos": "Medicamentos activos (derivada)",
    "hubo_cambio_med": "Hubo cambio de medicación (0/1)",
    "a1c_medida": "Se midió HbA1c (0/1)",
    "glu_medida": "Se midió glucosa (0/1)",
    "gender": "Género",
    "admission_type_id": "Tipo de ingreso",
    "discharge_disposition_id": "Tipo de egreso",
    "admission_source_id": "Origen del ingreso",
    "medical_specialty": "Especialidad que atiende",
    "max_glu_serum": "Glucosa en suero",
    "A1Cresult": "Hemoglobina glicosilada",
    "insulin": "Insulina",
    "change": "Cambio de medicación",
    "diabetesMed": "Toma medicación para diabetes",
    "grupo_diag_1": "Diagnóstico principal (grupo)",
    "grupo_diag_2": "Diagnóstico secundario (grupo)",
    "grupo_diag_3": "Diagnóstico adicional (grupo)",
}


def main():
    proc = pd.read_csv(BASE / "data/processed/cohorte_procesada.csv", low_memory=False)
    cols = json.loads((BASE / "data/processed/columnas.json").read_text(encoding="utf-8"))
    NUM, CAT = cols["numericas"], cols["categoricas"]

    crudo = pd.read_csv(BASE / "data/raw/diabetic_data.csv", low_memory=False)

    # ---------------------------------------------------------- resumen general
    particion = {}
    for nombre, grupo in proc.groupby("conjunto"):
        particion[nombre] = {
            "filas": int(len(grupo)),
            "pacientes": int(grupo.patient_nbr.nunique()),
            "positivos": int(grupo.y.sum()),
            "prevalencia": float(grupo.y.mean()),
        }
    repeticiones = proc.patient_nbr.value_counts()
    resumen = {
        "patrones_originales": int(len(crudo)),
        "pacientes_originales": int(crudo.patient_nbr.nunique()),
        "columnas_originales": int(crudo.shape[1]),
        "excluidos": int(len(crudo) - len(proc)),
        "patrones": int(len(proc)),
        "pacientes": int(proc.patient_nbr.nunique()),
        "positivos": int(proc.y.sum()),
        "prevalencia": float(proc.y.mean()),
        "predictores": len(NUM) + len(CAT),
        "numericas": len(NUM),
        "categoricas": len(CAT),
        "pacientes_con_una": int((repeticiones == 1).sum()),
        "pacientes_con_varias": int((repeticiones > 1).sum()),
        "max_hospitalizaciones": int(repeticiones.max()),
        "particion": particion,
    }
    (REP / "descriptiva_resumen.json").write_text(
        json.dumps(resumen, indent=1, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------- numéricas
    filas = []
    for columna in NUM:
        serie = pd.to_numeric(proc[columna], errors="coerce")
        modas = serie.mode()
        filas.append({
            "variable": NOMBRES.get(columna, columna),
            "clave": columna,
            "n": int(serie.notna().sum()),
            "faltantes": int(serie.isna().sum()),
            "media": float(serie.mean()),
            "mediana": float(serie.median()),
            "moda": float(modas.iloc[0]) if len(modas) else np.nan,
            "desviacion": float(serie.std()),
            "minimo": float(serie.min()),
            "q1": float(serie.quantile(0.25)),
            "q3": float(serie.quantile(0.75)),
            "maximo": float(serie.max()),
            "asimetria": float(serie.skew()),
        })
    pd.DataFrame(filas).to_csv(REP / "descriptiva_numericas.csv", index=False)

    # ----------------------------------------------------------- categóricas
    filas = []
    for columna in CAT:
        serie = proc[columna].astype(str).replace("nan", np.nan)
        conteo = serie.value_counts()
        filas.append({
            "variable": NOMBRES.get(columna, columna),
            "clave": columna,
            "n": int(serie.notna().sum()),
            "faltantes": int(serie.isna().sum()),
            "distintos": int(serie.nunique()),
            "moda": str(conteo.index[0]) if len(conteo) else "",
            "frecuencia_moda": int(conteo.iloc[0]) if len(conteo) else 0,
            "porcentaje_moda": float(conteo.iloc[0] / len(serie) * 100) if len(conteo) else 0.0,
        })
    pd.DataFrame(filas).to_csv(REP / "descriptiva_categoricas.csv", index=False)

    # --------------------------------------------------------- histogramas
    # 20 tramos por variable, con la tasa de reingreso de cada tramo: deja ver
    # de un golpe la distribución y su relación con el desenlace
    trozos = []
    for columna in NUM:
        serie = pd.to_numeric(proc[columna], errors="coerce")
        if serie.nunique() <= 1:
            continue
        tramos = pd.cut(serie, bins=min(20, max(serie.nunique(), 2)), duplicates="drop")
        agrupado = proc.groupby(tramos, observed=True).agg(
            casos=("y", "size"), reingresos=("y", "sum"))
        for intervalo, fila in agrupado.iterrows():
            trozos.append({
                "variable": NOMBRES.get(columna, columna),
                "clave": columna,
                "centro": float((intervalo.left + intervalo.right) / 2),
                "desde": float(intervalo.left),
                "hasta": float(intervalo.right),
                "casos": int(fila.casos),
                "reingresos": int(fila.reingresos),
                "tasa": float(fila.reingresos / fila.casos) if fila.casos else 0.0,
            })
    pd.DataFrame(trozos).to_csv(REP / "descriptiva_histogramas.csv", index=False)

    print(f"patrones {resumen['patrones']:,}".replace(",", ".") +
          f"  pacientes {resumen['pacientes']:,}".replace(",", ".") +
          f"  positivos {resumen['positivos']:,}".replace(",", "."))
    print(f"numericas {len(NUM)}  categoricas {len(CAT)}  "
          f"tramos de histograma {len(trozos)}")
    for nombre in ("descriptiva_resumen.json", "descriptiva_numericas.csv",
                   "descriptiva_categoricas.csv", "descriptiva_histogramas.csv"):
        print(f"  {nombre}: {(REP / nombre).stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
