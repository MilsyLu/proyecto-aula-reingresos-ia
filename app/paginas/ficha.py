# -*- coding: utf-8 -*-
"""Ficha técnica del modelo y recorrido por las 12 fases del ciclo de ML.

Dos lecturas de lo mismo. La pestaña «Ficha del modelo» responde qué es y cuánto
rinde; la pestaña «Cómo se construyó» responde cómo se llegó hasta ahí.

Las cifras no están escritas a mano: se leen de `reports/`, de modo que si un
experimento se repite, la ficha cambia sola. Lo único literal son los intervalos
de confianza, que se calcularon una sola vez por remuestreo.
"""
from __future__ import annotations

import streamlit as st

import datos
from datos import formato

REPOSITORIO = "https://github.com/MilsyLu/proyecto-aula-reingresos-ia"

# El original venía sin tildes. Las cadenas que llegan desde el CSV se corrigen
# aquí para que la tabla se lea igual que el resto de la página.
ACENTOS = {
    "Precision": "Precisión",
    ">=": "≥",
    " x ": " × ",
}

FASES = [
    ("01", "Definir el problema",
     "Clasificación binaria: reingreso antes de 30 días (<30). "
     "La métrica principal es Average Precision por el desbalance de clases.",
     "README.md y reports/Fase_1_Proyecto_IA_Grupo04_Reingresos.pdf",
     "Documentada"),
    ("02", "Recolección de datos",
     "Dataset UCI Diabetes 130-US Hospitals (1999-2008). "
     "Puede cargarse un nuevo CSV en Procesamiento CSV.",
     "data/raw/IDs_mapping.csv; notebooks/01_preprocesamiento_particion.ipynb",
     "Carga interactiva"),
    ("03", "Exploración y análisis (EDA)",
     "Resumen, faltantes, duplicados, distribuciones y valores extremos "
     "en archivos nuevos; EDA original en el notebook 00.",
     "notebooks/00_EDA_fase1.ipynb; src/analisis_calidad.py",
     "EDA interactivo"),
    ("04", "Limpieza y preparación",
     "Se validan esquemas y registros; se mantiene la imputación "
     "del pipeline entrenado y se registran las exclusiones.",
     "notebooks/01_preprocesamiento_particion.ipynb; src/procesamiento_lotes.py",
     "Procesamiento interactivo"),
    ("05", "Ingeniería de características",
     "12 características derivadas, incluyendo uso previo, "
     "medicamentos por día y grupos diagnósticos ICD-9.",
     "notebooks/01_preprocesamiento_particion.ipynb; src/procesamiento_lotes.py",
     "Procesamiento interactivo"),
    ("06", "Dividir los datos",
     "Partición 60/20/20 agrupada por paciente para evitar fugas "
     "entre entrenamiento, validación y prueba.",
     "notebooks/01_preprocesamiento_particion.ipynb",
     "Experimento documentado"),
    ("07", "Seleccionar el algoritmo",
     "Se compararon clasificador mayoritario, regresión logística "
     "y Gradient Boosting; se eligió el último.",
     "notebooks/02_modelos_baseline.ipynb; reports/metricas_03_comparacion.csv",
     "Experimento documentado"),
    ("08", "Entrenar el modelo",
     "HistGradientBoostingClassifier entrenado y guardado como "
     "pipeline para inferencia.",
     "notebooks/03_hiperparametros.ipynb; models/gradient_boosting_ajustado.joblib",
     "Modelo disponible"),
    ("09", "Ajustar hiperparámetros",
     "30 configuraciones con RandomizedSearchCV y "
     "validación cruzada agrupada por paciente.",
     "notebooks/03_hiperparametros.ipynb; reports/mejores_hiperparametros.json",
     "Experimento documentado"),
    ("10", "Evaluar el modelo",
     "Se reportan AP, ROC-AUC, sensibilidad, precisión, "
     "matriz de confusión y Brier en datos de prueba.",
     "notebooks/04_evaluacion_comparada.ipynb; reports/metricas_04_final.csv",
     "Resultados visibles"),
    ("11", "Validar generalización",
     "Separación por paciente, validación cruzada y "
     "auditoría de equidad y sensibilidad. No constituye validación "
     "clínica externa en datos actuales.",
     "notebooks/05_equidad_sensibilidad.ipynb; reports/metricas_05_sensibilidad.csv",
     "Validación interna"),
    ("12", "Desplegar el modelo",
     "Aplicación Streamlit con predicción manual, "
     "predicción masiva y consulta de métricas.",
     "app/app.py; README.md",
     "Prototipo integrado"),
]

# Calculados una sola vez por remuestreo; por eso se quedan escritos.
INTERVALOS = {
    "AP": "[0,2047 ; 0,2467]",
    "ROC_AUC": "[0,6527 ; 0,6786]",
    "recall": "[0,5766 ; 0,6202]",
}


def _tildes(texto: str) -> str:
    for malo, bueno in ACENTOS.items():
        texto = texto.replace(malo, bueno)
    return texto


def _tabla_metas():
    """La tabla de cumplimiento, leída del CSV y no escrita a mano."""
    tabla = datos.cargar_tabla("cumplimiento_metas.csv").copy()
    tabla.columns = ["Meta de la Fase 1", "Objetivo", "Obtenido en prueba", "¿Cumple?"]
    tabla["Meta de la Fase 1"] = tabla["Meta de la Fase 1"].map(_tildes)
    tabla["Objetivo"] = tabla["Objetivo"].map(lambda v: formato(v, 4))
    tabla["Obtenido en prueba"] = tabla["Obtenido en prueba"].map(lambda v: formato(v, 4))
    tabla["¿Cumple?"] = tabla["¿Cumple?"].map(
        lambda v: "Sí" if str(v).strip().upper() == "SI" else "No")
    return tabla


# ---------------------------------------------------------------- ficha
def _ficha():
    m = datos.metricas_finales()
    umbral = datos.umbral_oficial()
    total = datos.entero(m["VP"] + m["FN"] + m["FP"] + m["VN"])

    a, b, c = st.columns([1, 1, 1.15], gap="medium")
    with a:
        st.markdown(
            "**Qué hace**\n\n"
            "Estima la probabilidad de que una hospitalización de un paciente con "
            "diabetes termine en un **reingreso antes de 30 días**.\n\n"
            "**Datos**\n"
            "- Diabetes 130-US Hospitals 1999-2008, UCI (dataset 296)\n"
            "- 99.343 hospitalizaciones · 69.990 pacientes\n"
            "- Prevalencia: 11,39 %\n"
            "- Partición 60/20/20 **por paciente** (`StratifiedGroupKFold`)")
    with b:
        st.markdown(
            "**Modelo**\n"
            "- `HistGradientBoostingClassifier`\n"
            "- 50 predictores: 17 numéricos, 33 categóricos\n"
            "- Elegido entre **30 combinaciones** de hiperparámetros\n"
            f"- Umbral de decisión **{formato(umbral, 4)}**, fijado en validación\n\n"
            "**Matriz de confusión**")
        st.caption(
            f"Sobre {total} hospitalizaciones nunca vistas: "
            f"**{datos.entero(m['VP'])}** reingresos detectados · "
            f"**{datos.entero(m['FN'])}** escapados · "
            f"**{datos.entero(m['FP'])}** alertas sin reingreso · "
            f"**{datos.entero(m['VN'])}** altas tranquilas.")
    with c:
        st.markdown(f"""**Desempeño en prueba**

| Métrica | Valor | IC 95 % |
|---|---|---|
| Average precision | {formato(m["AP"], 4)} | {INTERVALOS["AP"]} |
| ROC-AUC | {formato(m["ROC_AUC"], 4)} | {INTERVALOS["ROC_AUC"]} |
| Sensibilidad | {formato(m["recall"], 4)} | {INTERVALOS["recall"]} |
| Precisión | {formato(m["precision"], 4)} | |
| Brier | {formato(m["Brier"], 4)} | |
""")

    izq, der = st.columns([1.15, 1], gap="medium")
    with izq:
        st.markdown("**Metas de la Fase 1**")
        st.dataframe(_tabla_metas(), hide_index=True, width="stretch")
        st.caption(
            "Ningún umbral cumple las dos últimas metas a la vez: subir la precisión "
            "obliga a bajar la sensibilidad. Se documenta tal cual.")
    with der:
        st.markdown(
            "**Qué no hace**\n"
            "- **No alerta igual a todo el mundo.** La sensibilidad de 0,60 cae a "
            "0,48 en las altas a casa, el 79 % de los casos.\n"
            "- **No descansa sobre la clínica.** Dos variables administrativas "
            "concentran el 43,5 % del desempeño.\n"
            "- **No trata igual a todas las edades.** Razón de paridad 0,569: "
            "alerta más sobre los mayores.\n"
            "- **No conoce el presente.** Estados Unidos, 1999-2008.\n"
            "- **No decide nada.** Solo puede **añadir** seguimiento, nunca "
            "restringir atención.")

    st.caption(
        "Equipo: Michel Custodes · Iván Güette · Maira Torres  |  Universidad "
        "Popular del Cesar, Ingeniería de Sistemas, 2026  |  "
        f"Repositorio: {REPOSITORIO}")


# ---------------------------------------------------------------- 12 fases
def _como_se_construyo():
    st.caption(
        "Las doce fases del desarrollo del modelo, con su evidencia. Una parte se "
        "ejecutó en los notebooks y otra funciona en vivo en el formulario y el "
        "procesamiento CSV. Consultar una fase no vuelve a entrenar nada: para "
        "reproducir un experimento, ejecute los notebooks en orden con el dataset UCI.")

    columnas = st.columns(3, gap="medium")
    for indice, (numero, nombre, explicacion, archivos, evidencia) in enumerate(FASES):
        with columnas[indice // 4]:
            with st.expander(f"{numero} · {nombre}"):
                st.write(explicacion)
                st.caption(f"Estado: {evidencia}")
                st.caption("Evidencia en el repositorio: " + archivos)

    st.caption(
        "Los CSV nuevos sin etiquetas sirven para inferencia, no para medir "
        "precisión ni reentrenar. Las doce etapas no se ejecutan en cada predicción.")


# ---------------------------------------------------------------- contrato
def render():
    st.subheader("Ficha del modelo")
    st.caption("Qué es el modelo, cuánto rinde y cómo se llegó hasta aquí.")

    ficha, construccion = st.tabs(["Ficha del modelo", "Cómo se construyó"])
    with ficha:
        _ficha()
    with construccion:
        _como_se_construyo()
