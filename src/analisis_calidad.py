"""Exploración descriptiva de CSV para inferencia (sin aprender parámetros del lote).

No elimina registros, no interpreta los outliers como errores y nunca usa
readmitted para generar características. Las estadísticas son descriptivas.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


COLUMNAS_NUMERICAS = (
    "time_in_hospital", "num_lab_procedures", "num_procedures",
    "num_medications", "number_outpatient", "number_emergency",
    "number_inpatient", "number_diagnoses", "edad_num", "servicios_previos",
)


def resumen_calidad(df: pd.DataFrame) -> dict:
    """Resumen de calidad reproducible y apto para comparar antes/después."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Se espera un DataFrame de pandas.")
    faltantes = df.replace("?", np.nan).isna().sum()
    duplicados = int(df.duplicated().sum())  # Se informan, no se eliminan.
    datos = pd.DataFrame({
        "columna": df.columns,
        "tipo": [str(t) for t in df.dtypes],
        "faltantes": faltantes.to_numpy(dtype=int),
        "porcentaje_faltante": (100 * faltantes / len(df)).fillna(0).round(2).to_numpy(),
        "valores_distintos": df.nunique(dropna=True).to_numpy(dtype=int),
    })
    return {
        "filas": len(df),
        "columnas": len(df.columns),
        "duplicados": duplicados,
        "celdas_faltantes": int(faltantes.sum()),
        "tabla": datos.sort_values(["faltantes", "columna"], ascending=[False, True]),
    }


def resumen_numericas(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estadísticas y alertas IQR (señal descriptiva, nunca eliminación)."""
    resultados = []
    atipicos = []
    for nombre in COLUMNAS_NUMERICAS:
        if nombre not in df:
            continue
        s = pd.to_numeric(df[nombre].replace("?", np.nan), errors="coerce")
        validos = s.dropna()
        if validos.empty:
            continue
        q1, q3 = validos.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr > 0:
            extremos = ((validos < q1 - 1.5 * iqr) |
                        (validos > q3 + 1.5 * iqr))
            n_extremos = int(extremos.sum())
        else:
            n_extremos = 0  # IQR nulo: evitar falsas conclusiones
        resultados.append({
            "variable": nombre, "n": len(validos), "media": float(validos.mean()),
            "mediana": float(validos.median()), "min": float(validos.min()),
            "max": float(validos.max()), "q1": float(q1), "q3": float(q3),
        })
        atipicos.append({"variable": nombre, "posibles_atipicos_IQR": n_extremos})
    return pd.DataFrame(resultados), pd.DataFrame(atipicos)


def distribucion_objetivo(df: pd.DataFrame) -> pd.DataFrame:
    """La etiqueta solo se describe si existe, nunca se usa al predecir."""
    if "readmitted" in df:
        etiquetas = df["readmitted"].fillna("Sin registro").astype(str)
    elif "y" in df:
        etiquetas = df["y"].map({1: "<30", 0: "NO o >30"}).fillna("Sin registro")
    else:
        return pd.DataFrame(columns=["categoria", "registros", "porcentaje"])
    cuentas = etiquetas.value_counts(dropna=False)
    return pd.DataFrame({
        "categoria": cuentas.index.astype(str),
        "registros": cuentas.to_numpy(),
        "porcentaje": (100 * cuentas / len(df)).round(2).to_numpy(),
    })
