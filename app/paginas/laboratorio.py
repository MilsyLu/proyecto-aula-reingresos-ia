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
from src.interpretacion_ml import resumen_comprensible, informe_texto

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
            serie = (pd.to_numeric(crudos[campo], errors="coerce")
                     .replace([np.inf, -np.inf], np.nan).dropna())
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
    st.subheader("Dos modelos, dos resultados")
    tabla = resultado["comparacion"].copy()
    elegido = resultado["elegido"]
    st.success("Modelo recomendado por validación: " + elegido)
    st.write(resultado["justificacion"])
    st.caption(
        "La selección depende de AP de validación, no del conjunto de prueba. "
        "Después de decidir, se evalúan ambos modelos sobre los mismos casos reservados."
    )
    uno, dos = st.columns(2)
    for panel, nombre in zip((uno, dos), ("Gradient Boosting", "Red neuronal MLP")):
        fila = tabla.set_index("modelo").loc[nombre]
        with panel:
            st.markdown("### " + nombre)
            st.caption("Ganador de validación" if nombre == elegido else "Modelo alternativo")
            a, b = st.columns(2)
            a.metric("AP validación", f'{fila["AP_validacion"]:.4f}')
            b.metric("AP prueba", f'{fila["AP_prueba"]:.4f}')
            c, d = st.columns(2)
            c.metric("ROC-AUC prueba", f'{fila["ROC_AUC_prueba"]:.4f}')
            d.metric("Recall prueba", f'{fila["recall_prueba"]:.4f}')
            st.caption(
                f'Precision: {fila["precision_prueba"]:.4f} · '
                f'Umbral (validación): {fila["umbral"]:.4f}'
            )
            matriz = pd.DataFrame(
                [[int(fila["VP"]), int(fila["FN"])],
                 [int(fila["FP"]), int(fila["VN"])]],
                index=["Reingreso real", "No reingreso"],
                columns=["Alerta", "Sin alerta"],
            )
            st.dataframe(matriz, width="stretch")
    st.markdown("#### Comparación en igualdad de condiciones")
    st.dataframe(tabla.round(4), width="stretch", hide_index=True)
    st.bar_chart(
        tabla.set_index("modelo")[["AP_entrenamiento", "AP_validacion", "AP_prueba"]].T
    )
    st.caption(
        "Los dos modelos usan los mismos pacientes, los mismos objetivos y las "
        "mismas particiones. La diferencia está en sus algoritmos y preparación."
    )
    with st.expander("Particiones y preparación de datos"):
        st.dataframe(resultado["particiones"].round(4), width="stretch", hide_index=True)
        st.markdown(
            "**Gradient Boosting:** valores numéricos sin escalar y categorías "
            "ordinales, siguiendo el enfoque del notebook 03. "
            "**MLP:** imputación, estandarización y codificación one-hot. "
            "Los transformadores se ajustan solo con entrenamiento."
        )
    with st.expander("Hiperparámetros, aprendizaje y sobreajuste", expanded=True):
        st.markdown(
            "Se probaron configuraciones distintas para cada algoritmo. "
            "La mejor de cada familia se eligió por AP de validación."
        )
        st.dataframe(resultado["busqueda"].round(4),
                     width="stretch", hide_index=True)
        st.markdown("**Brecha entre entrenamiento y validación**")
        st.bar_chart(
            tabla.set_index("modelo")[["AP_entrenamiento", "AP_validacion"]]
        )
        st.caption(
            "Una diferencia grande entre AP de entrenamiento y validación "
            "puede revelar sobreajuste, pero no demuestra generalización externa."
        )
        curva = resultado["curvas"].get("Red neuronal MLP")
        if curva is not None and not curva.empty:
            st.markdown("**Curva de pérdida durante el entrenamiento de la MLP**")
            st.line_chart(curva.set_index("iteracion"))
            st.caption(
                "Esta curva es pérdida de entrenamiento, no una curva de "
                "validación. La generalización se analiza en las métricas anteriores."
            )
    with st.expander("Justificación del modelo para el cliente", expanded=True):
        st.markdown(
            "Se prefiere el algoritmo con mayor **Average Precision en validación** "
            "porque el reingreso es poco frecuente y la exactitud sola engaña. "
            "Se comunican también sensibilidad, precisión, falsos positivos y negativos."
        )
        st.info(
            "La recomendación del laboratorio NO reemplaza el modelo del cliente. "
            "Las pantallas de predicción continúan usando el Gradient Boosting "
            "histórico guardado en models/gradient_boosting_ajustado.joblib. "
            "Un cambio operativo requiere validación independiente y aprobación."
        )
        st.caption(
            "Estos datos provienen de hospitales estadounidenses de 1999 a 2008. "
            "No se ha demostrado generalización clínica a Colombia."
        )
    st.download_button(
        "Descargar comparativa de ambos modelos",
        tabla.to_csv(index=False).encode("utf-8-sig"),
        "comparacion_gb_mlp.csv", mime="text/csv", key="lab_comp",
    )
    st.download_button(
        "Descargar búsqueda de hiperparámetros",
        resultado["busqueda"].to_csv(index=False).encode("utf-8-sig"),
        "busqueda_gb_mlp.csv", mime="text/csv", key="lab_tuning",
    )
    for nombre, archivo in (("Gradient Boosting", "prueba_gradient_boosting.csv"),
                            ("Red neuronal MLP", "prueba_mlp.csv")):
        st.download_button(
            "Descargar predicciones de prueba: " + nombre,
            resultado["predicciones_prueba"][nombre].to_csv(
                index=False).encode("utf-8-sig"),
            archivo, mime="text/csv", key="lab_pred_" + nombre,
        )



def _explicacion_sencilla(resultado):
    """Interpreta los dos modelos sin datos inventados."""
    info = resumen_comprensible(resultado)
    st.divider()
    st.header("¿Cómo entender estos resultados?")
    st.markdown(
        "Esta sección traduce los resultados del entrenamiento a lenguaje "
        "sencillo. Las cifras vienen del experimento ejecutado."
    )
    st.subheader("¿Cuál se eligió y por qué?")
    st.write(info["seleccion"])
    st.subheader("¿Qué mostraron los datos que no se usaron para elegir?")
    st.write(info["prueba"])
    st.caption(
        f'Los dos modelos evaluaron {info["filas_prueba"]:,} registros '
        "de prueba. Esos datos no se utilizaron para elegir el ganador."
    )
    st.subheader("¿Qué pasó con las alertas?")
    st.markdown(
        "Una alerta es una señal de riesgo, no una certeza de reingreso. "
        "Mire tanto los casos detectados como las falsas alertas."
    )
    columnas = st.columns(2)
    for panel, fila in zip(columnas, info["decisiones"]):
        with panel:
            st.markdown("**" + fila["nombre"] + "**")
            st.write(fila["texto"])
            a, b = st.columns(2)
            a.metric("Reingresos detectados", fila["recall"])
            b.metric("Alertas correctas", fila["precision"])
    st.subheader("Diccionario: qué significa cada indicador")
    for titulo, significado in info["glosario"]:
        with st.expander(titulo):
            st.write(significado)
    st.subheader("Qué conclusión comunicar")
    st.info(info["advertencia"])
    st.download_button(
        "Descargar explicación completa",
        informe_texto(resultado).encode("utf-8-sig"),
        "explicacion_resultados_modelos.txt", mime="text/plain",
        key="lab_explicacion_texto",
    )

def render():
    st.title("Laboratorio de modelos")
    _contexto()
    st.info(
        "El sistema operativo de predicciones sigue usando Gradient Boosting. "
        "En este laboratorio se entrenan **Gradient Boosting y una red neuronal MLP**, "
        "cada uno con su preparación y parámetros, sin reemplazar al modelo oficial."
    )
    st.warning("Use únicamente datos públicos o anonimizados. No cargue archivos con información identificable de pacientes.")
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
        busqueda = st.select_slider(
            "Configuraciones por algoritmo", options=[1, 2, 3], value=2,
        )
        st.caption(
            "Se compara Gradient Boosting con una red MLP. Cada modelo utiliza "
            "su preprocesamiento y se ajusta con AP de validación."
        )
        ejecutar = st.form_submit_button(
            "Entrenar y evaluar experimento", type="primary"
        )
    firma = hashlib.sha256(contenido).hexdigest() + f":{neuronas}:{iteraciones}:{busqueda}"
    if ejecutar:
        try:
            with st.spinner("Entrenando modelos del laboratorio..."):
                resultado = entrenar_experimento(
                    X, y, pacientes, numericas, categoricas,
                    neuronas=neuronas, iteraciones=iteraciones,
                    busqueda=busqueda,
                )
            st.session_state["lab_resultado"] = {
                "firma": firma, "resultado": resultado,
            }
        except (DatosEntrenamientoInvalidos, ValueError) as error:
            st.error(f"No se completó el entrenamiento: {error}")
    guardado = st.session_state.get("lab_resultado")
    if guardado and guardado["firma"] == firma:
        _resultado(guardado["resultado"], firma)
        _explicacion_sencilla(guardado["resultado"])

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
