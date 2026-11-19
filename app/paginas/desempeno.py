# -*- coding: utf-8 -*-
"""Desempeño del modelo en el conjunto de prueba.

Todas las cifras se leen de `reports/`: ninguna está escrita a mano, de modo que
si un notebook se vuelve a ejecutar la página queda al día sola.
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


def render():
    st.title("Desempeño del modelo")

    pred = datos.predicciones_prueba()
    final = datos.metricas_finales()
    umbral = datos.umbral_oficial()
    prevalencia = float(pred.reingreso_real.mean())

    st.caption(
        f"Conjunto de prueba: {entero(len(pred))} hospitalizaciones que el modelo "
        "nunca vio, evaluadas una sola vez."
    )

    c = st.columns(4)
    c[0].metric("Average precision", formato(final["AP"], 4),
                f"{formato(final['AP'] / prevalencia, 2)} × la prevalencia")
    c[1].metric("ROC-AUC", formato(final["ROC_AUC"], 4), "meta: 0,65")
    c[2].metric("Sensibilidad", formato(final["recall"], 4), "meta: 0,60")
    c[3].metric("Precisión", formato(final["precision"], 4), "meta: 0,20",
                delta_color="inverse")

    # ------------------------------------------------------------------ umbral
    st.markdown("---")
    st.subheader("El umbral es una decisión, no un cálculo")
    st.markdown(
        f"El umbral oficial del prototipo es **{formato(umbral, 4)}**, elegido en el "
        "conjunto de validación. Mueva el control para ver la compensación entre "
        "detectar más reingresos y generar más alertas falsas."
    )
    st.caption(
        "Este control es solo para visualizar. El resultado reportado en el informe "
        "corresponde al umbral fijado en validación, no a este deslizador."
    )

    u = st.slider("Umbral", 0.02, 0.50, float(umbral), step=0.0005, format="%.4f")
    m = datos.metricas_en(pred, u)
    reingresos = m["VP"] + m["FN"]

    k = st.columns(4)
    k[0].metric("Reingresos detectados", entero(m["VP"]), f"de {entero(reingresos)}",
                delta_color="off")
    k[1].metric("Sensibilidad", formato(m["recall"], 3))
    k[2].metric("Precisión", formato(m["precision"], 3))
    k[3].metric("Población alertada", f"{formato(100 * m['tasa_alerta'])} %")

    mc = pd.DataFrame(
        [[m["VP"], m["FN"]], [m["FP"], m["VN"]]],
        index=["Reingreso real: SÍ", "Reingreso real: NO"],
        columns=["Modelo alerta", "Modelo no alerta"],
    )

    izq, der = st.columns([1, 1])
    with izq:
        st.markdown("**Matriz de confusión**")
        st.dataframe(mc.style.format(entero), width="stretch")
    with der:
        st.markdown("**Lectura**")
        # La exactitud de un modelo que nunca alerte es, sencillamente, la
        # proporción de pacientes que no reingresan. Por eso no dice nada aquí.
        st.markdown(
            f"- **{entero(m['VP'])}** reingresos detectados a tiempo.\n"
            f"- **{entero(m['FN'])}** reingresos que se escaparon.\n"
            f"- **{entero(m['FP'])}** alertas sobre pacientes que no reingresaron.\n"
            f"- Exactitud global: **{formato(100 * m['exactitud'])} %** — y conviene "
            f"desconfiar de ese número: un modelo que nunca alerte alcanza "
            f"**{formato(100 * (1 - prevalencia))} %**."
        )

    # ------------------------------------------------------- comparación
    st.markdown("---")
    st.subheader("Comparación de modelos")
    comp, estilo = _tabla_comparacion()
    st.dataframe(estilo, width="stretch", hide_index=True)

    mejora = float(comp["mejora_vs_logistica_%"].iloc[-1])
    st.caption(
        f"Gradient Boosting mejora a la regresión logística en un {formato(mejora)} % "
        "de AP: una mejora real pero modesta, coherente con la literatura citada."
    )

    # ------------------------------------------------------- distribución
    st.markdown("---")
    st.subheader("Distribución de las probabilidades estimadas")
    hist = pd.DataFrame({
        "Reingreso real": pred.reingreso_real.map({1: "Sí reingresó",
                                                   0: "No reingresó"}),
        # Agrupa en cubetas de 0,02 para que el gráfico se lea.
        "bin": (pred.probabilidad * 50).astype(int) / 50,
    })
    conteo = hist.groupby(["bin", "Reingreso real"]).size().unstack(fill_value=0)
    st.bar_chart(conteo, color=[GRIS, TERRACOTA], height=300)
    st.caption(
        "Los dos grupos se superponen bastante: por eso la discriminación es "
        "moderada y el umbral importa tanto."
    )
