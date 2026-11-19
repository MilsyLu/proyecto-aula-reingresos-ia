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
from datos import AZUL, GRIS, formato

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

    a, b = st.columns(2)
    with a:
        st.markdown(f"""
#### Qué hace
Estima la probabilidad de que una hospitalización de un paciente con diabetes
termine en un **reingreso antes de 30 días**.

#### Datos
- **Fuente:** Diabetes 130-US Hospitals 1999-2008, UCI (dataset 296)
- **Cohorte:** 99.343 hospitalizaciones, 69.990 pacientes
- **Prevalencia:** 11,39 %
- **Partición:** 60/20/20 **por paciente**, con `StratifiedGroupKFold`

#### Modelo
- `HistGradientBoostingClassifier`
- 50 predictores: 17 numéricos, 33 categóricos
- Elegido entre **30 combinaciones** de hiperparámetros
- Umbral de decisión: **{formato(umbral, 4)}**, fijado en validación
        """)
    with b:
        st.markdown(f"""
#### Desempeño en prueba
| Métrica | Valor | IC 95 % |
|---|---|---|
| Average precision | {formato(m["AP"], 4)} | {INTERVALOS["AP"]} |
| ROC-AUC | {formato(m["ROC_AUC"], 4)} | {INTERVALOS["ROC_AUC"]} |
| Sensibilidad | {formato(m["recall"], 4)} | {INTERVALOS["recall"]} |
| Precisión | {formato(m["precision"], 4)} | |
| Brier | {formato(m["Brier"], 4)} | |

#### Matriz de confusión
Sobre {datos.entero(m["VP"] + m["FN"] + m["FP"] + m["VN"])} hospitalizaciones que el
modelo nunca vio: **{datos.entero(m["VP"])}** reingresos detectados,
**{datos.entero(m["FN"])}** que se le escaparon, **{datos.entero(m["FP"])}** alertas
sin reingreso y **{datos.entero(m["VN"])}** altas correctamente tranquilas.
        """)

    st.markdown("#### Metas de la Fase 1")
    st.dataframe(_tabla_metas(), hide_index=True, width="stretch")
    st.caption(
        "Ningún umbral cumple las dos últimas metas a la vez: subir la precisión "
        "obliga a bajar la sensibilidad. Se documenta tal cual, sin alterar el "
        "conjunto de prueba para que el resultado luzca mejor.")

    # --------------------------------------------------------- qué no hace
    st.markdown("---")
    st.markdown("#### Qué no hace")
    st.markdown(
        "- **No alerta igual a todo el mundo.** La sensibilidad global de 0,60 cae "
        "a 0,48 en los pacientes dados de alta a casa, que son el 79 % de los casos. "
        "Donde más se usaría, peor funciona.\n"
        "- **No descansa sobre la clínica.** Dos variables administrativas concentran "
        "el 43,5 % del desempeño. El modelo aprendió del circuito hospitalario tanto "
        "como del paciente.\n"
        "- **No trata igual a todas las edades.** La razón de paridad por edad es de "
        "0,569: alerta más sobre los mayores sin que su riesgo real sea mayor.\n"
        "- **No conoce el presente.** Los datos son de hospitales de Estados Unidos "
        "entre 1999 y 2008. Otro país, otra época, otra práctica clínica.\n"
        "- **No decide nada.** La salida solo puede **añadir** seguimiento a un "
        "paciente, nunca restringirle atención.")

    st.markdown("---")
    st.markdown(
        "**Equipo:** Michel Custodes · Iván Güette · Maira Torres "
        "&nbsp;&nbsp;|&nbsp;&nbsp; Universidad Popular del Cesar, "
        "Ingeniería de Sistemas, 2026\n\n"
        f"**Repositorio:** {REPOSITORIO}")


# ---------------------------------------------------------------- 12 fases
def _como_se_construyo():
    st.markdown(
        "Esta sección conecta el programa entregado con las doce fases de "
        "desarrollo del modelo explicadas en clase. Una parte se ejecutó "
        "durante la investigación (notebooks) y otra funciona en vivo "
        "mediante el formulario y el procesamiento CSV.")
    st.info(
        "Consultar una fase no vuelve a entrenar el modelo. Para reproducir "
        "un experimento, ejecute los notebooks en orden con el dataset UCI.")

    for numero, nombre, explicacion, archivos, evidencia in FASES:
        with st.expander(f"{numero} · {nombre} — {evidencia}"):
            st.write(explicacion)
            st.caption("Evidencia en el repositorio: " + archivos)

    st.caption(
        "Los CSV nuevos sin etiquetas conocidas sirven para inferencia, no "
        "para medir precisión ni para reentrenar. Las doce etapas no se "
        "ejecutan todas en cada predicción.")


# ---------------------------------------------------------------- contrato
def render():
    st.title("Ficha del modelo")
    st.markdown(
        f'<p style="color:{GRIS};margin-top:-0.6rem">'
        f'Qué es el modelo, cuánto rinde y <span style="color:{AZUL}">cómo se '
        'llegó hasta aquí</span>.</p>',
        unsafe_allow_html=True)

    ficha, construccion = st.tabs(["Ficha del modelo", "Cómo se construyó"])
    with ficha:
        _ficha()
    with construccion:
        _como_se_construyo()
