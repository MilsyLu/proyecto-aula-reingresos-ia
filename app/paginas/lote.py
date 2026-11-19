# -*- coding: utf-8 -*-
"""Cargue de un archivo de pacientes y lista priorizada de seguimiento.

Responde la pregunta con la que arrancó el proyecto: si el programa solo alcanza
para seguir a una parte de los pacientes que se van de alta, ¿a cuáles elige?
"""
from __future__ import annotations

import hashlib
import io

import numpy as np
import pandas as pd
import streamlit as st

import datos
import estilo
from datos import AZUL, GRIS, TERRACOTA, entero, formato
from src.analisis_calidad import resumen_calidad
from src.procesamiento_lotes import (ArchivoIncompatible, categorias_no_vistas,
                                     predecir_lote, preparar_lote)

LIMITE_MB = 30


def _descargar(df, nombre, etiqueta):
    st.download_button(etiqueta, df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=nombre, mime="text/csv")


def _cobertura(probabilidades, capacidad):
    """Qué porción de los reingresos esperados alcanza a cubrir el programa.

    Se suman las probabilidades de los pacientes elegidos y se divide entre la suma
    de todas. Es el número esperado de reingresos que el seguimiento alcanzaría a
    tocar, bajo el supuesto de que el modelo está bien calibrado — y lo está: el
    desvío máximo medido es de 0,0089.
    """
    orden = np.sort(probabilidades)[::-1]
    total = orden.sum()
    if total <= 0:
        return 0.0, 0.0
    elegidos = orden[:capacidad].sum()
    return elegidos / total, elegidos


def _calidad(datos_crudos, X, descartes, diagnostico, modelo):
    columnas = st.columns(4)
    columnas[0].metric("Filas recibidas", entero(diagnostico["recibidas"]))
    columnas[1].metric("Listas para predecir", entero(diagnostico["validas"]))
    columnas[2].metric("Descartadas", entero(diagnostico["excluidas"]))
    columnas[3].metric("Formato detectado",
                       "Archivo original" if diagnostico["formato"] == "uci"
                       else "Ya preparado")

    desconocidas = {col: val for col, val in
                    categorias_no_vistas(modelo, X, X.columns).items() if val}
    if desconocidas:
        detalle = "; ".join(
            f"<b>{col}</b>: " + ", ".join(f"{v} ({entero(n)} filas)" for v, n in vals.items())
            for col, vals in desconocidas.items())
        estilo.aviso_prototipo(
            f"Hay valores que el modelo nunca vio durante el entrenamiento, y los trata "
            f"como desconocidos sin lanzar ningún error. Revise estas columnas antes de "
            f"confiar en sus predicciones.<br>{detalle}")
    else:
        st.success("Todas las categorías del archivo coinciden con las que el modelo "
                   "aprendió. No hay valores desconocidos.", icon="✓")

    if not descartes.empty:
        with st.expander(f"Por qué se descartaron {entero(len(descartes))} filas"):
            st.dataframe(descartes.motivo.value_counts().rename("Filas").reset_index()
                         .rename(columns={"index": "Motivo", "motivo": "Motivo"}),
                         hide_index=True, width="stretch")
            st.caption("Los fallecidos y los derivados a cuidado paliativo se excluyen "
                       "porque no pueden reingresar: mantenerlos inflaría el desempeño.")
            _descargar(descartes, "exclusiones.csv", "Descargar el detalle")

    with st.expander("Calidad del archivo"):
        resumen = resumen_calidad(datos_crudos)
        por_columna = resumen["tabla"]
        fila = st.columns(4)
        fila[0].metric("Filas", entero(resumen["filas"]))
        fila[1].metric("Columnas", entero(resumen["columnas"]))
        fila[2].metric("Duplicados exactos", entero(resumen["duplicados"]))
        fila[3].metric("Celdas vacías", entero(resumen["celdas_faltantes"]))
        st.caption("Los duplicados y los valores atípicos se informan, no se eliminan: "
                   "esa decisión es del analista, no de la herramienta.")
        st.dataframe(por_columna, hide_index=True, width="stretch", height=260)
        _descargar(por_columna, "reporte_calidad.csv", "Descargar el reporte")


def _lista_priorizada(predicciones, umbral):
    st.markdown("## A quién llamar primero")
    st.markdown(
        "El modelo ordena. La capacidad la pone usted. Esa es toda la decisión: "
        "**cuántos seguimientos puede hacer esta semana.**")

    total = len(predicciones)
    sugerido = int((predicciones.probabilidad >= umbral).sum())

    izq, der = st.columns([1, 2])
    with izq:
        capacidad = st.number_input(
            "¿A cuántos pacientes puede hacer seguimiento?",
            min_value=1, max_value=total, value=min(max(sugerido, 1), total), step=10,
            help="Con el umbral oficial del modelo serían "
                 f"{entero(sugerido)} de {entero(total)}.")

    orden = predicciones.sort_values("probabilidad", ascending=False).reset_index(drop=True)
    elegidos = orden.head(int(capacidad)).copy()
    elegidos.insert(0, "Prioridad", range(1, len(elegidos) + 1))

    proporcion, esperados = _cobertura(predicciones.probabilidad.values, int(capacidad))
    corte = float(elegidos.probabilidad.min())

    with der:
        fila = st.columns(3)
        fila[0].metric("Pacientes elegidos", entero(len(elegidos)),
                       f"{formato(len(elegidos) / total * 100)} % del archivo")
        fila[1].metric("Reingresos que alcanzaría a cubrir",
                       f"{formato(proporcion * 100)} %",
                       f"≈ {formato(esperados, 1)} de {formato(predicciones.probabilidad.sum(), 1)} esperados")
        fila[2].metric("Riesgo del último de la lista", f"{formato(corte * 100)} %",
                       f"umbral implícito {formato(corte, 4)}")

    st.markdown(
        f'<div class="tarjeta" style="border-left:3px solid {AZUL}">'
        f'Con <b>{entero(len(elegidos))} seguimientos</b> alcanzaría a cubrir cerca del '
        f'<b>{formato(proporcion * 100)} %</b> de los reingresos esperados en este archivo. '
        f'Fijar la capacidad en ese número equivale a poner el umbral en '
        f'<b>{formato(corte, 4)}</b>: por eso decimos que el umbral es una decisión de '
        f'gestión y no un resultado del modelo.</div>', unsafe_allow_html=True)

    vista = elegidos.rename(columns={
        "fila_csv": "Fila del archivo", "probabilidad": "Riesgo estimado",
        "alerta": "Con el umbral oficial"})
    vista["Riesgo estimado"] = vista["Riesgo estimado"].map(lambda p: f"{formato(p * 100)} %")
    st.dataframe(vista.head(200), hide_index=True, width="stretch", height=420)
    if len(elegidos) > 200:
        st.caption(f"Se muestran los primeros 200 de {entero(len(elegidos))}. "
                   "La descarga trae la lista completa.")

    descarga = elegidos.rename(columns={
        "fila_csv": "fila_del_archivo", "probabilidad": "riesgo_estimado",
        "alerta": "con_umbral_oficial"})
    _descargar(descarga, "lista_de_seguimiento.csv",
               f"Descargar la lista de {entero(len(elegidos))} pacientes")

    with st.expander("Cómo se calcula la cobertura"):
        st.markdown(
            "Se suman las probabilidades de los pacientes elegidos y se dividen entre "
            "la suma de todas. Eso estima **cuántos de los reingresos que van a ocurrir "
            "quedarían dentro del programa**.\n\n"
            "El cálculo se apoya en que el modelo esté bien calibrado, y lo está: al "
            "agrupar el conjunto de prueba en diez grupos de riesgo, la mayor diferencia "
            "entre lo predicho y lo observado fue de 0,0089, menos de un punto porcentual.\n\n"
            "Lo que **no** dice: que esos reingresos se vayan a evitar. Solo que el "
            "paciente entra en la lista. Que el seguimiento sirva es otra pregunta, y "
            "este proyecto no la responde.")


def render():
    st.title("Cargar un archivo de pacientes")
    st.markdown(
        "Suba un archivo con las hospitalizaciones que acaban de terminar. La "
        "aplicación lo valida fila por fila, estima el riesgo de cada paciente y "
        "arma la lista de seguimiento según la capacidad del programa.")

    with st.expander("¿Qué archivo puedo subir?"):
        st.markdown(
            "Se aceptan dos formatos, en **CSV** y hasta 30 MB:\n\n"
            "1. El archivo original de UCI (`diabetic_data.csv`), con sus 50 columnas.\n"
            "2. Un CSV que ya traiga las 50 variables del modelo.\n\n"
            "Los vacíos pueden venir como celda vacía o como `?`. Nada se guarda en "
            "ningún servidor: el archivo se procesa en memoria y desaparece al cerrar "
            "la sesión.")

    archivo = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
    if archivo is None:
        return

    if archivo.size > LIMITE_MB * 1024 * 1024:
        st.error(f"El archivo pesa {formato(archivo.size / 1024 / 1024)} MB y el límite "
                 f"es de {LIMITE_MB} MB.")
        return

    numericas, categoricas, _ = datos.cargar_columnas()
    modelo = datos.cargar_modelo()
    umbral = datos.umbral_oficial()

    try:
        crudos = pd.read_csv(io.BytesIO(archivo.getvalue()), na_values=["?"],
                             low_memory=False)
        X, descartes, diagnostico = preparar_lote(crudos, numericas, categoricas)
    except (ArchivoIncompatible, pd.errors.ParserError, UnicodeDecodeError,
            ValueError, KeyError) as error:
        st.error(f"No se pudo procesar el archivo: {error}")
        return

    st.divider()
    _calidad(crudos, X, descartes, diagnostico, modelo)

    if X.empty:
        st.warning("No quedó ninguna fila válida para predecir.")
        return

    identidad = hashlib.sha256(archivo.getvalue()).hexdigest()
    st.divider()

    if st.button(f"Estimar el riesgo de {entero(len(X))} pacientes", type="primary"):
        with st.spinner("Calculando…"):
            st.session_state["lote_resultado"] = {
                "identidad": identidad,
                "predicciones": predecir_lote(modelo, X, umbral)}

    guardado = st.session_state.get("lote_resultado")
    if not guardado or guardado["identidad"] != identidad:
        st.info("Pulse el botón para estimar el riesgo de las filas válidas.")
        return

    predicciones = guardado["predicciones"]
    _lista_priorizada(predicciones, umbral)
    _descargar(predicciones, "predicciones_reingreso.csv",
               "Descargar todas las predicciones")
