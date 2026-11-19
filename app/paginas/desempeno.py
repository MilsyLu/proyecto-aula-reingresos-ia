# -*- coding: utf-8 -*-
"""Desempeño del modelo en el conjunto de prueba.

Todas las cifras se leen de `reports/`: ninguna está escrita a mano, de modo que
si un notebook se vuelve a ejecutar la página queda al día sola.

La página está armada para caber en una pantalla: encabezado y métricas en una
misma fila, el umbral junto a sus cifras en la siguiente, y lo secundario
(comparación y distribución) dentro de pestañas.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

import datos
from datos import GRIS, TERRACOTA, entero, formato


def _tabla_comparacion():
    """La comparación de modelos, con encabezados legibles.

    Se renombran solo los encabezados: los nombres de los modelos son valores del
    CSV y se dejan tal cual para no desalinear la tabla con el informe.
    """
    comp = datos.cargar_tabla("metricas_03_comparacion.csv")
    visible = comp.rename(columns={
        "modelo": "Modelo",
        "AP": "AP",
        "ROC_AUC": "ROC-AUC",
        "AP_sobre_prevalencia": "AP sobre prevalencia",
        "mejora_vs_logistica_%": "Mejora vs. logística (%)",
    })
    estilo = visible.style.format({
        "AP": lambda v: formato(v, 4),
        "ROC-AUC": lambda v: formato(v, 4),
        "AP sobre prevalencia": lambda v: formato(v, 2),
        "Mejora vs. logística (%)": lambda v: formato(v, 1),
    })
    return comp, estilo


def _ganancia():
    """La precisión no es una propiedad del modelo: depende de a cuántos se llame.

    Es la lectura que falta cuando alguien ve "precisión 0,178" y concluye que el
    modelo acierta el 18 % de las veces. Ese 0,178 es el valor en el punto donde
    está el umbral, que alerta sobre el 38 % de la población. Si el programa solo
    alcanza para el 2 %, entre esos pacientes reingresa el 43 %.
    """
    tabla, base = datos.ganancia_por_tramo()
    izquierda, derecha = st.columns([1.45, 1])

    with izquierda:
        vista = pd.DataFrame({
            "Se hace seguimiento a": [
                f"{formato(f * 100)} %  ({entero(n)})"
                for f, n in zip(tabla.fraccion, tabla.pacientes)],
            "De ellos reingresan": [f"{formato(t * 100)} %" for t in tabla.tasa],
            "Veces la tasa general": [f"{formato(v, 2)} ×" for v in tabla.veces],
            "Reingresos cubiertos": [f"{formato(c * 100)} %" for c in tabla.cobertura],
        })
        st.dataframe(vista, width="stretch", hide_index=True, height=285)

    with derecha:
        mejor = tabla.iloc[0]
        actual = tabla[tabla.fraccion == 0.384].iloc[0]
        st.markdown(
            f"**La precisión no es una propiedad del modelo.** Es su valor en el punto "
            f"donde está el umbral, que alerta sobre el "
            f"{formato(actual.fraccion * 100)} % de la población.")
        st.caption(
            f"Llamar a los {entero(mejor.pacientes)} de mayor riesgo encuentra reingresos "
            f"al {formato(mejor.tasa * 100)} %, **{formato(mejor.veces, 1)} veces** la tasa "
            f"general de la cohorte ({formato(base * 100)} %). El modelo no acierta un "
            f"porcentaje fijo: concentra el riesgo, y cuánto lo concentra depende de a "
            f"cuánta gente alcance el programa.")
        st.caption(
            "Por eso la sección **Cargar archivo** pregunta por la capacidad en vez de "
            "fijar un umbral: la decisión de dónde cortar es de gestión, no del modelo.")


def render():
    pred = datos.predicciones_prueba()
    final = datos.metricas_finales()
    umbral = datos.umbral_oficial()
    prevalencia = float(pred.reingreso_real.mean())

    # ------------------------------------------ encabezado + métricas finales
    enc, g1, g2, g3, g4 = st.columns([1.6, 1, 1, 1, 1], vertical_alignment="center")
    with enc:
        st.markdown("## Desempeño del modelo")
        st.caption(
            f"{entero(len(pred))} hospitalizaciones que el modelo nunca vio, "
            "evaluadas una sola vez."
        )
    g1.metric("Average precision", formato(final["AP"], 4),
              f"{formato(final['AP'] / prevalencia, 2)} × prevalencia")
    g2.metric("ROC-AUC", formato(final["ROC_AUC"], 4), "meta: 0,65")
    g3.metric("Sensibilidad", formato(final["recall"], 4), "meta: 0,60")
    g4.metric("Precisión", formato(final["precision"], 4), "meta: 0,20",
              delta_color="inverse")

    # ------------------------------------------------------------------ umbral
    ctl, k1, k2, k3, k4 = st.columns([1.6, 1, 1, 1, 1], vertical_alignment="center")
    with ctl:
        u = st.slider(f"Umbral — oficial {formato(umbral, 4)}, fijado en validación",
                      0.02, 0.50, float(umbral), step=0.0005, format="%.4f")
        st.caption("El deslizador solo explora; el informe reporta el umbral oficial.")

    m = datos.metricas_en(pred, u)
    reingresos = m["VP"] + m["FN"]

    # Etiquetas cortas a propósito: con la barra lateral abierta las columnas
    # quedan estrechas y Streamlit recorta cualquier título largo con puntos.
    k1.metric("Detectados", entero(m["VP"]),
              f"de {entero(reingresos)} reingresos", delta_color="off")
    k2.metric("Sensibilidad", formato(m["recall"], 3))
    k3.metric("Precisión", formato(m["precision"], 3))
    k4.metric("Alertados", f"{formato(100 * m['tasa_alerta'])} %",
              "de la población", delta_color="off")

    # ------------------------------------------------ matriz de confusión
    mc = pd.DataFrame(
        [[m["VP"], m["FN"]], [m["FP"], m["VN"]]],
        index=["Reingreso real: SÍ", "Reingreso real: NO"],
        columns=["Modelo alerta", "Modelo no alerta"],
    )

    izq, der = st.columns([1, 1.15])
    with izq:
        st.markdown("**Matriz de confusión**")
        st.dataframe(mc.style.format(entero), width="stretch", height=110)
    with der:
        st.markdown("**Lectura**")
        # La exactitud de un modelo que nunca alerte es, sencillamente, la
        # proporción de pacientes que no reingresan. Por eso no dice nada aquí.
        st.caption(
            f"- **{entero(m['VP'])}** reingresos detectados a tiempo; "
            f"**{entero(m['FN'])}** se escaparon.\n"
            f"- **{entero(m['FP'])}** alertas sobre pacientes que no reingresaron.\n"
            f"- Exactitud global **{formato(100 * m['exactitud'])} %**, cifra "
            f"engañosa: no alertar nunca da **{formato(100 * (1 - prevalencia))} %**."
        )

    # --------------------------------------- lo secundario, en pestañas
    ganancia, comparacion, distribucion = st.tabs(
        ["Ganancia según el tamaño de la lista", "Comparación de modelos",
         "Distribución de las probabilidades"]
    )

    with ganancia:
        _ganancia()

    with comparacion:
        comp, estilo = _tabla_comparacion()
        st.dataframe(estilo, width="stretch", hide_index=True, height=180)
        mejora = float(comp["mejora_vs_logistica_%"].iloc[-1])
        st.caption(
            f"Gradient Boosting mejora a la logística en {formato(mejora)} % de AP: "
            "real pero modesta, coherente con la literatura citada."
        )

    with distribucion:
        hist = pd.DataFrame({
            "Reingreso real": pred.reingreso_real.map({1: "Sí reingresó",
                                                       0: "No reingresó"}),
            # Agrupa en cubetas de 0,02 para que el gráfico se lea.
            "bin": (pred.probabilidad * 50).astype(int) / 50,
        })
        conteo = hist.groupby(["bin", "Reingreso real"]).size().unstack(fill_value=0)
        st.bar_chart(conteo, color=[GRIS, TERRACOTA], height=210)
        st.caption(
            "Los dos grupos se superponen: por eso la discriminación es moderada "
            "y el umbral importa tanto."
        )
