# -*- coding: utf-8 -*-
"""Conocer los datos: cuántos patrones hay y cómo se reparten.

Las cifras vienen precalculadas de `src/estadistica_descriptiva.py`, porque la
cohorte no se versiona y en el servidor no existe. Lo que viaja son cuatro
archivos de unos pocos kilobytes.
"""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

import datos as fuente
from datos import AZUL, GRIS, TERRACOTA, entero, formato


@st.cache_data(show_spinner=False)
def _resumen():
    ruta = fuente.REPORTES / "descriptiva_resumen.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


def _cabecera(r):
    fila = st.columns(5)
    fila[0].metric("Patrones", entero(r["patrones"]),
                   f"de {entero(r['patrones_originales'])} originales",
                   delta_color="off")
    fila[1].metric("Pacientes", entero(r["pacientes"]),
                   f"máx. {r['max_hospitalizaciones']} ingresos uno solo",
                   delta_color="off")
    fila[2].metric("Reingresos antes de 30 días", entero(r["positivos"]),
                   f"{formato(r['prevalencia'] * 100, 2)} % de los patrones",
                   delta_color="off")
    fila[3].metric("Predictores", entero(r["predictores"]),
                   f"{r['numericas']} numéricos · {r['categoricas']} categóricos",
                   delta_color="off")
    fila[4].metric("Excluidos", entero(r["excluidos"]),
                   "fallecidos y paliativos", delta_color="off")

    st.caption(
        f"Un **patrón** es una hospitalización, no un paciente: "
        f"{entero(r['pacientes_con_varias'])} personas tienen más de un ingreso en la "
        f"base y una llega a {r['max_hospitalizaciones']}. Por eso la partición se hace "
        f"por paciente y no por fila — si no, la misma persona quedaría a la vez en "
        f"entrenamiento y en prueba, y el modelo la reconocería en vez de aprender.")


def _particion(r):
    orden = ["entrenamiento", "validacion", "prueba"]
    etiqueta = {"entrenamiento": "Entrenamiento", "validacion": "Validación",
                "prueba": "Prueba"}
    tabla = pd.DataFrame([{
        "Conjunto": etiqueta[c],
        "Patrones": entero(r["particion"][c]["filas"]),
        "Pacientes": entero(r["particion"][c]["pacientes"]),
        "Reingresos": entero(r["particion"][c]["positivos"]),
        "Prevalencia": f"{formato(r['particion'][c]['prevalencia'] * 100, 3)} %",
    } for c in orden if c in r["particion"]])
    st.dataframe(tabla, hide_index=True, width="stretch", height=145)
    st.caption("La prevalencia es casi idéntica en los tres: eso es lo que hace la parte "
               "*estratificada* de la partición. Ningún paciente aparece en dos conjuntos.")


ENCABEZADOS_NUM = {
    "variable": "Variable", "n": "Casos", "faltantes": "Vacíos", "media": "Media",
    "mediana": "Mediana", "moda": "Moda", "desviacion": "Desv. típica",
    "minimo": "Mínimo", "q1": "Q1", "q3": "Q3", "maximo": "Máximo",
    "asimetria": "Asimetría",
}


def _numericas():
    tabla = fuente.cargar_tabla("descriptiva_numericas.csv")
    vista = tabla[list(ENCABEZADOS_NUM)].rename(columns=ENCABEZADOS_NUM)
    for columna in ("Media", "Mediana", "Moda", "Desv. típica", "Mínimo", "Q1", "Q3",
                    "Máximo", "Asimetría"):
        vista[columna] = vista[columna].map(lambda v: formato(v, 2))
    for columna in ("Casos", "Vacíos"):
        vista[columna] = vista[columna].map(entero)
    st.dataframe(vista, hide_index=True, width="stretch", height=330)

    sesgadas = tabla.loc[tabla.asimetria.abs() > 2, "variable"].tolist()
    if sesgadas:
        st.caption(
            f"**Media y mediana se separan mucho en varias variables.** En "
            f"{', '.join(sesgadas[:4])} la mayoría de pacientes está en cero y unos pocos "
            f"se van muy arriba. Por eso los vacíos se rellenan con la **mediana** y no "
            f"con la media: un paciente con 21 ingresos previos arrastraría el promedio.")


def _categoricas():
    tabla = fuente.cargar_tabla("descriptiva_categoricas.csv")
    vista = pd.DataFrame({
        "Variable": tabla.variable,
        "Valores distintos": tabla.distintos.map(entero),
        "Valor más frecuente": tabla.moda,
        "Veces": tabla.frecuencia_moda.map(entero),
        "% del total": tabla.porcentaje_moda.map(lambda v: f"{formato(v, 1)} %"),
        "Vacíos": tabla.faltantes.map(entero),
    })
    st.dataframe(vista, hide_index=True, width="stretch", height=330)
    st.caption(
        "La **moda** es el valor que más se repite. Donde el porcentaje es altísimo "
        "—los antidiabéticos que casi nadie usa— la variable casi no distingue a un "
        "paciente de otro, y eso explica que 21 de las 50 no aporten nada al modelo.")


def _distribuciones():
    tabla = fuente.cargar_tabla("descriptiva_histogramas.csv")
    variables = tabla.variable.unique().tolist()
    izq, der = st.columns([1, 2.4])
    with izq:
        elegida = st.selectbox("Variable", variables, label_visibility="collapsed")
    datos_var = tabla[tabla.variable == elegida]

    with der:
        st.caption(f"Cuántas hospitalizaciones caen en cada tramo de **{elegida}**, "
                   "y qué porcentaje de ellas terminó en reingreso.")

    # el centro del tramo viene con todos sus decimales; sin redondear, el eje
    # se llena de etiquetas como 3,3215000000000003
    paso = (datos_var.hasta - datos_var.desde).median()
    decimales = 0 if paso >= 2 else (1 if paso >= 0.2 else 2)
    etiquetas = datos_var.centro.map(lambda v: formato(v, decimales))
    marco = datos_var.assign(tramo=etiquetas)

    st.bar_chart(marco.set_index("tramo")[["casos"]].rename(
        columns={"casos": "Hospitalizaciones"}), color=AZUL, height=190)

    porcentaje = marco.assign(pct=marco.tasa * 100)
    st.bar_chart(porcentaje.set_index("tramo")[["pct"]].rename(
        columns={"pct": "% que reingresa"}), color=TERRACOTA, height=170)

    fila = st.columns(3)
    fila[0].metric("Tramos", entero(len(datos_var)))
    mas_lleno = datos_var.loc[datos_var.casos.idxmax()]
    fila[1].metric("Tramo más poblado",
                   f"{formato(mas_lleno.desde, 1)} – {formato(mas_lleno.hasta, 1)}",
                   f"{entero(mas_lleno.casos)} hospitalizaciones", delta_color="off")
    con_datos = datos_var[datos_var.casos >= 30]
    if not con_datos.empty:
        peor = con_datos.loc[con_datos.tasa.idxmax()]
        fila[2].metric("Tramo de mayor riesgo",
                       f"{formato(peor.desde, 1)} – {formato(peor.hasta, 1)}",
                       f"{formato(peor.tasa * 100, 1)} % reingresa", delta_color="off")


def render():
    r = _resumen()
    st.markdown("## Conocer los datos")
    st.caption("Estadística descriptiva de la cohorte con la que se entrenó el modelo. "
               "Las cifras se calculan una sola vez y se guardan; la aplicación solo las lee.")

    _cabecera(r)

    reparto, numericas, categoricas, distribucion = st.tabs(
        ["Cómo se repartieron", "Variables numéricas", "Variables categóricas",
         "Distribuciones"])

    with reparto:
        _particion(r)
    with numericas:
        _numericas()
    with categoricas:
        _categoricas()
    with distribucion:
        _distribuciones()
