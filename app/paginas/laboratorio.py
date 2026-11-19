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
    """Primero la decisión, después los detalles técnicos bajo demanda."""
    st.markdown("#### ¿Cuál modelo funcionó mejor?")
    tabla = resultado["comparacion"].set_index("modelo")
    ganador = resultado["elegido"]
    st.success(f"Recomendación experimental: **{ganador}**")
    st.markdown(resultado["justificacion"])
    st.caption(
        "La decisión se toma con validación. Ambos modelos se evaluaron "
        "después en el mismo conjunto de prueba; estos números no "
        "sustituyen los del modelo oficial."
    )
    cols = st.columns(2)
    for panel, nombre in zip(cols, ("Gradient Boosting", "Red neuronal MLP")):
        fila = tabla.loc[nombre]
        with panel:
            st.markdown(f"##### {nombre}")
            st.caption("Seleccionado" if nombre == ganador else "Alternativa")
            a, b = st.columns(2)
            a.metric("AP validación", f'{fila["AP_validacion"]:.3f}')
            b.metric("AP prueba", f'{fila["AP_prueba"]:.3f}')
            st.caption(
                f'Reingresos detectados: {100 * fila["recall_prueba"]:.1f} % · '
                f'Alertas acertadas: {100 * fila["precision_prueba"]:.1f} %'
            )
    st.markdown("##### Comparación visual")
    st.bar_chart(
        tabla[["AP_entrenamiento", "AP_validacion", "AP_prueba"]]
        .rename(columns={
            "AP_entrenamiento": "Entrenamiento",
            "AP_validacion": "Validación",
            "AP_prueba": "Prueba",
        })
    )
    st.caption(
        "Valores mayores de Average Precision son preferibles; "
        "si entrenamiento supera mucho a validación puede existir sobreajuste."
    )

    with st.expander("Ver matrices de confusión y todas las métricas"):
        for nombre in ("Gradient Boosting", "Red neuronal MLP"):
            fila = tabla.loc[nombre]
            st.markdown(f"**{nombre}**")
            a, b, c = st.columns(3)
            a.metric("ROC-AUC prueba", f'{fila["ROC_AUC_prueba"]:.3f}')
            b.metric("Recall prueba", f'{fila["recall_prueba"]:.3f}')
            c.metric("Precisión prueba", f'{fila["precision_prueba"]:.3f}')
            st.dataframe(
                pd.DataFrame(
                    [[int(fila["VP"]), int(fila["FN"])],
                     [int(fila["FP"]), int(fila["VN"])]],
                    index=["Reingreso real", "No reingreso"],
                    columns=["Alerta", "Sin alerta"],
                ),
                width="stretch",
            )
            st.caption(f'Umbral seleccionado en validación: {fila["umbral"]:.4f}')

    with st.expander("Examinar configuraciones y aprendizaje"):
        st.markdown(
            "Las configuraciones se seleccionan por AP de validación. "
            "Los transformadores de cada algoritmo se ajustan "
            "únicamente con entrenamiento."
        )
        st.dataframe(
            resultado["busqueda"].round(4), width="stretch", hide_index=True
        )
        curva = resultado["curvas"].get("Red neuronal MLP")
        if curva is not None and not curva.empty:
            st.markdown("**Pérdida durante el entrenamiento de la red neuronal**")
            st.line_chart(curva.set_index("iteracion"))
            st.caption(
                "Esta curva describe la optimización de la red, "
                "no su generalización a nuevos hospitales."
            )

    with st.expander("Trazabilidad: particiones y características"):
        st.dataframe(
            resultado["particiones"].round(4),
            hide_index=True, width="stretch",
        )
        st.write(
            "Gradient Boosting codifica las categorías ordinalmente, mientras "
            "que la MLP utiliza codificación one-hot y estandarización. "
            "Ambos comparten datos, etiquetas y particiones por paciente."
        )

    with st.expander("Descargar evidencia técnica"):
        st.download_button(
            "Comparación de los dos modelos (.csv)",
            resultado["comparacion"].to_csv(index=False).encode("utf-8-sig"),
            "comparacion_gb_mlp.csv", mime="text/csv", key="lab_comp",
        )
        st.download_button(
            "Búsqueda de hiperparámetros (.csv)",
            resultado["busqueda"].to_csv(index=False).encode("utf-8-sig"),
            "busqueda_gb_mlp.csv", mime="text/csv", key="lab_tuning",
        )
        for nombre, archivo in (
            ("Gradient Boosting", "prueba_gradient_boosting.csv"),
            ("Red neuronal MLP", "prueba_mlp.csv"),
        ):
            st.download_button(
                "Predicciones de prueba: " + nombre,
                resultado["predicciones_prueba"][nombre].to_csv(
                    index=False).encode("utf-8-sig"),
                archivo, mime="text/csv", key="lab_pred_" + nombre,
            )
    st.info(
        "El modelo recomendado aquí es experimental. El área Predicción "
        "de riesgo continúa usando el Gradient Boosting oficial; "
        "no se cambia automáticamente para el cliente."
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


ETAPAS = (
    "1 · Datos", "2 · Preparación", "3 · Entrenamiento",
    "4 · Comparación", "5 · Interpretación",
)


def _ir_a(etapa):
    """La navegación se modifica mediante callbacks para evitar conflictos
    con el estado de widgets ya creados en la misma ejecución de Streamlit."""
    st.session_state["lab_etapa"] = etapa


def _datos_disponibles():
    return st.session_state.get("lab_datos")


def _paso_datos():
    st.markdown("#### Conozca el origen de los datos")
    _contexto()
    st.info(
        "El problema y la recolección histórica se documentaron previamente. "
        "Este laboratorio empieza al cargar registros con el resultado real "
        "del reingreso, para reproducir su entrenamiento."
    )
    st.warning(
        "Use solo información pública o anonimizada. No cargue datos personales "
        "identificables de pacientes."
    )
    archivo = st.file_uploader(
        "Cargar un CSV etiquetado", type=["csv"], key="lab_csv",
        help="Se requieren readmitted o y (etiqueta real) y patient_nbr (identificador de grupo).",
    )
    st.caption(
        "Admite archivos UCI o archivos preparados con las 50 variables; "
        "máximo 30 MB. Un CSV sin resultado real debe procesarse "
        "en Predicción de riesgo, no aquí."
    )
    if archivo is not None:
        if archivo.size > LIMITE_MB * 1024 * 1024:
            st.error(f"El archivo supera el límite de {LIMITE_MB} MB.")
        else:
            contenido = archivo.getvalue()
            identidad = hashlib.sha256(contenido).hexdigest()
            if st.session_state.get("lab_firma_archivo") != identidad:
                try:
                    crudos = pd.read_csv(
                        io.BytesIO(contenido), na_values=["?"], low_memory=False
                    )
                    numericas, categoricas, _ = datos.cargar_columnas()
                    etiquetas = obtener_etiquetas(crudos)
                    if "patient_nbr" not in crudos:
                        raise DatosEntrenamientoInvalidos(
                            "Falta patient_nbr. No se puede evitar la mezcla de pacientes."
                        )
                    X, descartes, diagnostico = preparar_lote(
                        crudos, numericas, categoricas
                    )
                    y = etiquetas.loc[X.index]
                    pacientes = crudos.loc[X.index, "patient_nbr"]
                    if pacientes.isna().any():
                        raise DatosEntrenamientoInvalidos(
                            "Hay identificadores de paciente sin valor."
                        )
                    if len(X) < 120:
                        raise DatosEntrenamientoInvalidos(
                            "Se requieren al menos 120 hospitalizaciones válidas."
                        )
                    # La muestra es reproducible y se utiliza para ambos modelos.
                    total_validas = len(X)
                    if total_validas > LIMITE_FILAS:
                        X = X.sample(n=LIMITE_FILAS, random_state=42)
                        y = y.loc[X.index]
                        pacientes = pacientes.loc[X.index]
                    st.session_state["lab_datos"] = {
                        "crudos": crudos, "X": X, "descartes": descartes,
                        "diagnostico": diagnostico, "y": y,
                        "pacientes": pacientes, "numericas": numericas,
                        "categoricas": categoricas, "identidad": identidad,
                        "validas_originales": total_validas,
                    }
                    st.session_state["lab_firma_archivo"] = identidad
                    st.session_state.pop("lab_resultado", None)
                except (ArchivoIncompatible, DatosEntrenamientoInvalidos,
                        KeyError, ValueError, UnicodeDecodeError,
                        pd.errors.ParserError) as error:
                    st.error(f"No se pudo preparar el archivo: {error}")
                    return

    paquete = _datos_disponibles()
    if paquete:
        d = paquete["diagnostico"]
        a, b, c = st.columns(3)
        a.metric("Registros recibidos", f'{d["recibidas"]:,}')
        b.metric("Registros válidos", f'{d["validas"]:,}')
        c.metric("Excluidos", f'{d["excluidas"]:,}')
        if paquete["validas_originales"] > LIMITE_FILAS:
            st.info(
                f"Se seleccionó una muestra reproducible de {LIMITE_FILAS:,} "
                "registros válidos para mantener viable la demostración. "
                "Los resultados describen esta muestra."
            )
        st.success("Datos disponibles para explorar, preparar y entrenar.")
        st.button(
            "Continuar: revisar y preparar datos", type="primary",
            on_click=_ir_a, args=(ETAPAS[1],),
        )


def _paso_preparacion(paquete):
    st.markdown("#### Qué datos entran al entrenamiento")
    st.markdown(
        "Aquí se resumen faltantes, distribuciones, registros excluidos y "
        "características que aprende cada algoritmo. "
        "No se eliminan registros simplemente por parecer atípicos."
    )
    _exploracion(
        paquete["crudos"], paquete["X"], paquete["descartes"],
        paquete["diagnostico"],
    )
    with st.expander("Qué sucede después con las 50 características"):
        st.markdown(
            "Se utilizan las variables originales y las derivadas, como "
            "servicios previos, medicación diaria y grupos diagnósticos. "
            "**Gradient Boosting** conserva numéricas sin escalar y "
            "codifica categorías ordinalmente. "
            "La **MLP** imputa, estandariza y aplica one-hot. "
            "Cada transformación se ajusta exclusivamente con entrenamiento."
        )
    st.button(
        "Continuar: configurar modelos", type="primary",
        on_click=_ir_a, args=(ETAPAS[2],),
    )


def _paso_entrenamiento(paquete):
    st.markdown("#### Entrenar dos modelos sobre los mismos pacientes")
    st.markdown(
        "El programa divide el archivo en entrenamiento, validación y prueba "
        "sin compartir pacientes. Se prueba más de una configuración "
        "y elige el modelo mediante Average Precision en validación."
    )
    with st.form("lab_entrenamiento"):
        a, b = st.columns(2)
        neuronas = a.slider(
            "Neuronas de la red MLP", 8, 64, 24, 8,
            help="Número de neuronas de la primera capa oculta.",
        )
        iteraciones = b.slider(
            "Máximo de iteraciones de MLP", 30, 120, 65, 5,
        )
        busqueda = st.select_slider(
            "Configuraciones por algoritmo",
            options=[1, 2, 3], value=2,
            help="Búsqueda acotada para la demostración, no exhaustiva.",
        )
        ejecutar = st.form_submit_button(
            "Entrenar y comparar los dos modelos", type="primary",
        )

    firma = paquete["identidad"] + f":{neuronas}:{iteraciones}:{busqueda}"
    guardado = st.session_state.get("lab_resultado")
    if ejecutar:
        try:
            with st.spinner("Preparando características y entrenando ambos modelos…"):
                resultado = entrenar_experimento(
                    paquete["X"], paquete["y"], paquete["pacientes"],
                    paquete["numericas"], paquete["categoricas"],
                    neuronas=neuronas, iteraciones=iteraciones, busqueda=busqueda,
                )
            st.session_state["lab_resultado"] = {
                "firma": firma, "identidad": paquete["identidad"],
                "resultado": resultado,
            }
            guardado = st.session_state["lab_resultado"]
        except (DatosEntrenamientoInvalidos, ValueError) as error:
            st.error(f"El entrenamiento no se completó: {error}")
    if guardado and guardado["firma"] == firma:
        st.success(
            "Los dos modelos se entrenaron. El ganador experimental se "
            "seleccionó sin utilizar los datos de prueba."
        )
        tabla = guardado["resultado"]["comparacion"].set_index("modelo")
        st.dataframe(
            tabla[["AP_validacion", "AP_prueba"]].round(4), width="stretch",
        )
        st.button(
            "Continuar: comparar resultados", type="primary",
            on_click=_ir_a, args=(ETAPAS[3],),
        )
    elif guardado:
        st.info(
            "La configuración ha cambiado. Ejecute un nuevo entrenamiento "
            "para actualizar los resultados."
        )


def render():
    st.title("Experimento guiado")
    st.caption(
        "Cinco etapas para recorrer el proyecto: de los datos originales "
        "a una comparación justificada de Gradient Boosting y una red neuronal."
    )
    etapa = st.segmented_control(
        "Etapas del experimento", ETAPAS, default=ETAPAS[0],
        key="lab_etapa",
    ) or ETAPAS[0]
    indice = ETAPAS.index(etapa)
    st.progress((indice + 1) / len(ETAPAS))
    st.caption(f"Etapa {indice + 1} de {len(ETAPAS)}")
    paquete = _datos_disponibles()
    guardado = st.session_state.get("lab_resultado")
    if indice > 0 and not paquete:
        st.info("Comience por la etapa Datos y cargue un CSV etiquetado.")
        st.button("Ir a Datos", on_click=_ir_a, args=(ETAPAS[0],))
        return
    if indice >= 3 and (
        not guardado or guardado["identidad"] != paquete["identidad"]
    ):
        st.info(
            "Primero debe entrenar ambos modelos para obtener resultados "
            "comparables. Abra la etapa Entrenamiento."
        )
        st.button("Ir a Entrenamiento", on_click=_ir_a, args=(ETAPAS[2],))
        return

    if indice == 0:
        _paso_datos()
    elif indice == 1:
        _paso_preparacion(paquete)
    elif indice == 2:
        _paso_entrenamiento(paquete)
    elif indice == 3:
        _resultado(guardado["resultado"], guardado["firma"])
        st.button(
            "Continuar: entender los resultados", type="primary",
            on_click=_ir_a, args=(ETAPAS[4],),
        )
    else:
        _explicacion_sencilla(guardado["resultado"])
        st.button(
            "Volver a la comparación", on_click=_ir_a, args=(ETAPAS[3],),
        )
