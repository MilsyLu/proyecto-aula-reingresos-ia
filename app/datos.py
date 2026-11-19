# -*- coding: utf-8 -*-
"""Carga del modelo y de los resultados del proyecto, con caché.

Un único lugar para leer de disco, de modo que las páginas no repitan rutas ni
vuelvan a abrir los mismos archivos en cada interacción.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent.parent
MODELO_RUTA = BASE / "models" / "gradient_boosting_ajustado.joblib"
REPORTES = BASE / "reports"
ASSETS = Path(__file__).resolve().parent / "assets"

# --- identidad visual, la misma del informe final -------------------------
AZUL = "#1F3B63"
TERRACOTA = "#C25A3C"
VERDE = "#2E8B74"
GRIS = "#5A6472"
TINTA = "#15202B"


@st.cache_resource(show_spinner=False)
def cargar_modelo():
    return joblib.load(MODELO_RUTA)


@st.cache_data(show_spinner=False)
def cargar_columnas():
    """Las 50 variables que espera el modelo, más el valor típico de cada una."""
    cfg = json.loads((Path(__file__).resolve().parent / "valores_por_defecto.json")
                     .read_text(encoding="utf-8"))
    return cfg["numericas"], cfg["categoricas"], cfg["por_defecto"]


@st.cache_data(show_spinner=False)
def umbral_oficial():
    return json.loads((REPORTES / "umbral_elegido.json")
                      .read_text(encoding="utf-8"))["umbral"]


@st.cache_data(show_spinner=False)
def cargar_tabla(nombre):
    return pd.read_csv(REPORTES / nombre)


@st.cache_data(show_spinner=False)
def predicciones_prueba():
    """Las 19.870 hospitalizaciones del conjunto de prueba, ya puntuadas."""
    return pd.read_csv(REPORTES / "predicciones_prueba.csv")


@st.cache_data(show_spinner=False)
def metricas_finales():
    """Las cifras oficiales del informe, leídas del CSV en vez de escritas a mano."""
    df = cargar_tabla("metricas_04_final.csv").set_index("conjunto")
    return df.loc["PRUEBA"].to_dict()


def formato(valor, decimales=1):
    """Número al estilo colombiano: coma decimal y punto de miles."""
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def entero(valor):
    return f"{int(valor):,}".replace(",", ".")


def metricas_en(df, umbral):
    """Recalcula la matriz de confusión para cualquier umbral."""
    alerta = df.probabilidad >= umbral
    real = df.reingreso_real == 1
    vp = int((real & alerta).sum())
    fn = int((real & ~alerta).sum())
    fp = int((~real & alerta).sum())
    vn = int((~real & ~alerta).sum())
    return {
        "VP": vp, "FN": fn, "FP": fp, "VN": vn,
        "recall": vp / (vp + fn) if vp + fn else 0.0,
        "precision": vp / (vp + fp) if vp + fp else 0.0,
        "tasa_alerta": (vp + fp) / len(df) if len(df) else 0.0,
        "exactitud": (vp + vn) / len(df) if len(df) else 0.0,
    }


@st.cache_data(show_spinner=False)
def ganancia_por_tramo():
    """Cuánto concentra el riesgo el modelo según a cuánta gente se llame.

    Responde la pregunta que la precisión sola no responde. "Precisión 0,178" no
    es una propiedad fija del modelo: es el valor que toma cuando se alerta sobre
    el 38 % de la población. Si el programa solo alcanza para el 2 %, entre esos
    pacientes reingresa el 43 %.

    Devuelve, para varios tamaños de lista: la tasa real de reingreso de los
    elegidos, cuántas veces es la tasa general, y qué porción de todos los
    reingresos queda dentro de la lista.
    """
    d = predicciones_prueba().sort_values("probabilidad", ascending=False)
    base = d.reingreso_real.mean()
    total = d.reingreso_real.sum()
    filas = []
    for fraccion in (0.02, 0.05, 0.10, 0.20, 0.30, 0.384, 0.50):
        n = max(int(len(d) * fraccion), 1)
        elegidos = d.head(n)
        tasa = elegidos.reingreso_real.mean()
        filas.append({
            "fraccion": fraccion,
            "pacientes": n,
            "tasa": tasa,
            "veces": tasa / base if base else 0.0,
            "cobertura": elegidos.reingreso_real.sum() / total if total else 0.0,
        })
    return pd.DataFrame(filas), base
