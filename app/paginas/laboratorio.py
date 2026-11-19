"""Laboratorio de datos, entrenamiento y evaluación del proyecto.

Separa el modelo oficial (inferencia) de los experimentos nuevos. La colección
histórica y el problema se documentaron antes: esta pantalla comienza al subir
un CSV etiquetado y deja visible la evidencia técnica de cada operación.
"""
from __future__ import annotations

import hashlib
import io

import numpy as np
import pandas as pd
import streamlit as st

import datos
from src.analisis_calidad import resumen_calidad, resumen_numericas, distribucion_objetivo
from src.laboratorio_ml import (
    DatosEntrenamientoInvalidos, entrenar_experimento, obtener_etiquetas,
)
from src.procesamiento_lotes import ArchivoIncompatible, preparar_lote

LIMITE_FILAS = 12000
LIMITE_MB = 30


def _contexto():
    st.markdown(
        "El proyecto ya definió el problema y recopiló datos históricos de "
        "**Diabetes 130-US Hospitals (1999–2008)**. A partir de un archivo "
        "etiquetado, aquí puede reproducir una versión controlada del proceso "
        "de preparación, entrenamiento y evaluación."
    )
    with st.expander("Objetivo y procedencia de los datos"):
        st.markdown(
            "**Objetivo:** detectar reingresos antes de 30 días (clasificación binaria). "
            "El valor positivo corresponde a `readmitted = <30`. "
            "**Fuente histórica:** UCI Machine Learning Repository, dataset 296. "
            "**Unidad de análisis:** hospitalización; un paciente puede tener varias. "
            "La métrica principal es **Average Precision**, porque la clase "
            "positiva es minoritaria."
        )
        st.caption(
            "Evidencia: README.md; notebooks/00_EDA_fase1.ipynb; "
            "reports/Fase_1_Proyecto_IA_Grupo04_Reingresos.pdf"
        )


def _exploracion(crudos, X, descartes, resumen):
    st.subheader("Explorar y preparar")
    a, b, c, d = st.columns(4)
    a.metric("Hospitalizaciones recibidas", f'{resumen["recibidas"]:,}')
    b.metric("Registros utilizables", f'{resumen["validas"]:,}')
    c.metric("Excluidos", f'{resumen["excluidas"]:,}')
    calidad = resumen_calidad(crudos)
    d.metric("Celdas sin dato", f'{calidad["celdas_faltantes"]:,}')
    st.caption(
        f'Esquema detectado: {resumen["formato"]}. Los descartes responden a '
        "criterios documentados de la cohorte; los faltantes restantes los "
        "gestiona el preprocesamiento del experimento."
    )
    t_calidad, t_estadisticas, t_objetivo = st.tabs([
        "Calidad", "Variables", "Variable objetivo"
    ])
    with t_calidad:
        st.dataframe(calidad["tabla"], hide_index=True, width="stretch")
        st.caption(
            f'{calidad["duplicados"]:,} duplicados exactos detectados. '
            "No se eliminan automáticamente: dos hospitalizaciones pueden "
            "pertenecer a una misma persona."
        )
        st.download_button(
            "Descargar reporte de calidad",
            calidad["tabla"].to_csv(index=False).encode("utf-8-sig"),
            "calidad_laboratorio.csv", mime="text/csv",
        )
        if not descartes.empty:
            with st.expander("Registros excluidos"):
                st.dataframe(descartes.head(200), hide_index=True, width="stretch")
                st.download_button(
                    "Descargar exclusiones", descartes.to_csv(index=False).encode("utf-8-sig"),
                    "exclusiones_laboratorio.csv", mime="text/csv",
                )
    with t_estadisticas:
        tabla, extremos = resumen_numericas(crudos)
        if tabla.empty:
            st.info("No hay variables numéricas del esquema exploratorio.")
        else:
            st.dataframe(tabla.round(2), hide_index=True, width="stretch")
            campo = st.selectbox("Explorar distribución", tabla["variable"].tolist(),
                                  key="lab_variable")
            serie = pd.to_numeric(crudos[campo], errors="coerce").dropna()
            if not serie.empty:
                conteos, bordes = np.histogram(serie.to_numpy(), bins=20)
                histograma = pd.DataFrame({
                    "Intervalo": [
                        f"{bordes[i]:.1f} – {bordes[i + 1]:.1f}"
                        for i in range(len(conteos))
                    ],
                    "Registros": conteos,
                })
                st.bar_chart(histograma.set_index("Intervalo"))
            else:
                st.info("No hay observaciones numéricas válidas para graficar.")
            st.markdown("**Valores atípicos potenciales (método IQR)**")
            st.dataframe(extremos, hide_index=True, width="stretch")
            st.caption("Es una alerta exploratoria, no una orden para eliminar casos.")
    with t_objetivo:
        etiquetas = distribucion_objetivo(crudos)
        if etiquetas.empty:
            st.warning("Este archivo no contiene el resultado real del reingreso.")
        else:
            st.dataframe(etiquetas, hide_index=True, width="stretch")
            st.bar_chart(etiquetas.set_index("categoria")["registros"])


def _resultado(resultado, firma):
    st.subheader("Resultados de la experimentación")
    st.success(f'Modelo seleccionado en validación: **{resultado["elegido"]}**.')
    st.caption(
        "Estos modelos se entrenaron únicamente con el archivo cargado en esta sesión. "
        "No sustituyen al Gradient Boosting oficial ni actualizan sus métricas."
    )
    st.markdown("**Partición por paciente**")
    st.dataframe(resultado["particiones"].round(4), hide_index=True, width="stretch")
    st.caption(
        "Las proporciones son aproximadas, con grupos mutuamente excluyentes. "
        "No se comparten pacientes entre entrenamiento, validación y prueba."
    )
    st.markdown("**Comparación de algoritmos (validación)**")
    st.dataframe(resultado["comparacion"].round(4), hide_index=True, width="stretch")
    st.bar_chart(resultado["comparacion"].set_index("modelo")["AP_validacion"])
    metricas = resultado["prueba"]
    st.markdown("**Evaluación final del modelo elegido (prueba independiente)**")
    c = st.columns(4)
    c[0].metric("Average Precision", f'{metricas["AP"]:.4f}')
    c[1].metric("ROC-AUC", f'{metricas["ROC_AUC"]:.4f}')
    c[2].metric("Sensibilidad", f'{metricas["recall"]:.4f}')
    c[3].metric("Precisión", f'{metricas["precision"]:.4f}')
    st.caption(
        f'Umbral = {resultado["umbral"]:.4f}, elegido en validación para '
        "buscar sensibilidad ≥ 0,60. La prueba se utilizó una sola vez."
    )
    matriz = pd.DataFrame(
        [[metricas["VP"], metricas["FN"]], [metricas["FP"], metricas["VN"]]],
        index=["Reingreso real", "No reingreso"],
        columns=["Con alerta", "Sin alerta"],
    )
    st.dataframe(matriz, width="stretch")
    with st.expander("Interpretar errores y generalización"):
        st.write(
            "Una diferencia pequeña entre las métricas de validación y prueba "
            "es una señal favorable, pero no demuestra desempeño en otros "
            "hospitales o años. Una alerta incorrecta consume capacidad; un "
            "reingreso no detectado representa un falso negativo."
        )
        st.markdown(
            "**Control de generalización:** separación por `patient_nbr`, "
            "transformaciones aprendidas solo del conjunto de entrenamiento, "
            "selección del modelo y umbral en validación, evaluación final en prueba."
        )
    st.download_button(
        "Exportar comparación de modelos",
        resultado["comparacion"].to_csv(index=False).encode("utf-8-sig"),
        "comparacion_laboratorio.csv", mime="text/csv",
        key="lab_descarga_comparacion",
    )
    st.download_button(
        "Exportar predicciones de prueba",
        resultado["predicciones_prueba"].to_csv(index=False).encode("utf-8-sig"),
        "evaluacion_laboratorio.csv", mime="text/csv",
        key="lab_descarga_prueba",
    )


def render():
    st.title("Laboratorio de modelos")
    _contexto()
    st.info(
        "El sistema operativo de predicciones sigue usando Gradient Boosting. "
        "En este laboratorio se entrena una **red neuronal MLP** y se compara "
        "con modelos de referencia, sin reemplazar al original."
    )
    st.subheader("Seleccionar datos")
    st.markdown(
        "Cargue un CSV original de UCI o un CSV preparado con las 50 "
        "características del modelo. Para entrenar se requiere una columna "
        "real **readmitted** o **y** y el identificador **patient_nbr**. "
        "Un CSV sin etiquetas solo sirve para predicción y debe usarse en "
        "**Cargar archivo**."
    )
    archivo = st.file_uploader(
        "Archivo etiquetado (.csv)", type=["csv"], key="lab_csv"
    )
    if archivo is None:
        return
    if archivo.size > LIMITE_MB * 1024 * 1024:
        st.error(f"El archivo supera {LIMITE_MB} MB.")
        return
    try:
        contenido = archivo.getvalue()
        crudos = pd.read_csv(io.BytesIO(contenido), na_values=["?"], low_memory=False)
        numericas, categoricas, _ = datos.cargar_columnas()
        etiquetas = obtener_etiquetas(crudos)
        if "patient_nbr" not in crudos.columns:
            raise DatosEntrenamientoInvalidos(
                "No existe patient_nbr: no se puede separar sin fuga entre pacientes."
            )
        X, descartes, diagnostico = preparar_lote(crudos, numericas, categoricas)
        y = etiquetas.loc[X.index]
        pacientes = crudos.loc[X.index, "patient_nbr"]
        if pacientes.isna().any():
            raise DatosEntrenamientoInvalidos(
                "Hay identificadores patient_nbr vacíos."
            )
    except (ArchivoIncompatible, DatosEntrenamientoInvalidos, KeyError,
            ValueError, UnicodeDecodeError, pd.errors.ParserError) as error:
        st.error(f"No se pudo preparar el experimento: {error}")
        return
    st.divider()
    _exploracion(crudos, X, descartes, diagnostico)
    if len(X) < 120:
        st.warning("No hay suficientes registros válidos para entrenamiento.")
        return
    if len(X) > LIMITE_FILAS:
        st.info(
            f"Para proteger los recursos del prototipo se entrenará sobre una "
            f"muestra reproducible de {LIMITE_FILAS:,} registros, tomada "
            "antes de dividir por paciente. Los resultados describen esta muestra."
        )
        X = X.sample(n=LIMITE_FILAS, random_state=42)
        y = y.loc[X.index]
        pacientes = pacientes.loc[X.index]
    st.divider()
    st.subheader("Configurar y entrenar")
    with st.form("lab_entrenamiento"):
        a, b = st.columns(2)
        neuronas = a.slider(
            "Neuronas en la capa oculta de la MLP", 8, 64, 24, 8
        )
        iteraciones = b.slider(
            "Máximo de iteraciones", 30, 120, 65, 5
        )
        st.caption(
            "Se compara clasificador mayoritario, regresión logística "
            "y una red neuronal con una capa oculta. Las variables numéricas "
            "se imputan y estandarizan; las categóricas se codifican."
        )
        ejecutar = st.form_submit_button(
            "Entrenar y evaluar experimento", type="primary"
        )
    firma = hashlib.sha256(contenido).hexdigest() + f":{neuronas}:{iteraciones}"
    if ejecutar:
        try:
            with st.spinner("Entrenando modelos del laboratorio..."):
                resultado = entrenar_experimento(
                    X, y, pacientes, numericas, categoricas,
                    neuronas=neuronas, iteraciones=iteraciones,
                )
            st.session_state["lab_resultado"] = {
                "firma": firma, "resultado": resultado,
            }
        except (DatosEntrenamientoInvalidos, ValueError) as error:
            st.error(f"No se completó el entrenamiento: {error}")
    guardado = st.session_state.get("lab_resultado")
    if guardado and guardado["firma"] == firma:
        _resultado(guardado["resultado"], firma)

    st.divider()
    with st.expander("Del experimento al aplicativo desplegado"):
        st.markdown(
            "El modelo oficial ya se evaluó en el proyecto y se publicó "
            "en la sección **Estimar riesgo** y **Cargar archivo**. "
            "Este laboratorio demuestra el ciclo sin reemplazar el modelo "
            "ni alterar el conjunto de prueba oficial."
        )
        st.caption(
            "Evidencia adicional: notebooks/01_preprocesamiento_particion.ipynb "
            "a 05_equidad_sensibilidad.ipynb; reports/metricas_04_final.csv; "
            "models/gradient_boosting_ajustado.joblib."
        )
