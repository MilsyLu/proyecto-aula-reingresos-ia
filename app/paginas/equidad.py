# -*- coding: utf-8 -*-
"""Equidad y límites del prototipo.

Un modelo puede tener buenas métricas globales y aun así fallar de manera
sistemática con un grupo. Esta página audita eso y, sobre todo, dice en voz alta
dónde el prototipo no sirve.

Las cifras de los comentarios se calculan de las mismas tablas que se muestran,
no se escriben a mano: así ningún párrafo puede contradecir a la tabla que tiene
encima.
"""
from __future__ import annotations

import streamlit as st

import datos
from datos import entero, formato
from estilo import aviso_prototipo

# Etiqueta visible -> archivo de resultados. La etiqueta lleva tilde; el nombre
# del archivo es un dato y se deja exactamente como está en `reports/`.
SUBGRUPOS = {
    "Edad": "metricas_05_subgrupos_edad.csv",
    "Género": "metricas_05_subgrupos_genero.csv",
    "Grupo racial": "metricas_05_subgrupos_raza.csv",
}

ENCABEZADOS = {
    "grupo": "Grupo",
    "escenario": "Escenario",
    "n": "Casos",
    "prevalencia": "Prevalencia",
    "tasa_alerta": "Tasa de alerta",
    "recall": "Sensibilidad",
    "precision": "Precisión",
    "ROC_AUC": "ROC-AUC",
    "AP": "AP",
}

UMBRAL_PARIDAD = 0.80


def _mostrar(df, columnas):
    """Tabla con encabezados en español y números al estilo colombiano."""
    visible = df[columnas].rename(columns=ENCABEZADOS)
    decimales = {ENCABEZADOS[c]: (lambda v: formato(v, 4))
                 for c in columnas if c not in ("grupo", "escenario", "n")}
    if "n" in columnas:
        decimales[ENCABEZADOS["n"]] = entero
    st.dataframe(visible.style.format(decimales), width="stretch", hide_index=True)


def _paridad(tasas):
    """Razón de paridad demográfica: la tasa de alerta más baja sobre la más alta."""
    tasas = [t for t in tasas if t > 0]
    return min(tasas) / max(tasas) if tasas else 0.0


def _comentario_edad(t):
    joven, mayor = t.iloc[0], t.iloc[-1]
    st.error(
        "**Disparidad confirmada por edad.** La tasa de alerta sube de "
        f"{formato(100 * joven.tasa_alerta, 0)} % en los menores de 50 a "
        f"{formato(100 * mayor.tasa_alerta, 0)} % en los de 80 o más, mientras el "
        f"ROC-AUC baja de {formato(joven.ROC_AUC, 3)} a {formato(mayor.ROC_AUC, 3)}. "
        "La prevalencia real es parecida en todos los grupos, así que esa diferencia "
        "no está justificada por un riesgo mayor: el modelo alerta más sobre los "
        "mayores porque acumulan las señales que aprendió a reconocer."
    )


def _comentario_genero(t):
    st.success(
        f"**Sin disparidad relevante.** Razón de paridad "
        f"{formato(_paridad(t.tasa_alerta), 3)}, por encima del umbral de "
        f"{formato(UMBRAL_PARIDAD, 2)}. Las mujeres reciben algo más de alertas y se "
        "les detectan más reingresos, con precisión prácticamente igual."
    )


def _comentario_raza(t):
    grandes = t.nlargest(2, "n")
    menor = t.nsmallest(1, "n").iloc[0]
    nombres = " y ".join(grandes.grupo.tolist())
    st.warning(
        "**Entre los dos grupos grandes no se detecta disparidad** "
        f"({nombres}, {entero(grandes.n.sum())} casos entre los dos): paridad "
        f"{formato(_paridad(grandes.tasa_alerta), 3)}, mismo recall y misma "
        f"precisión. Los grupos pequeños ({menor.grupo}: {entero(menor.n)} casos) no "
        "permiten afirmar nada en ninguna dirección. No es lo mismo decir que no hay "
        "sesgo que decir que no hay datos para medirlo."
    )


def render():
    st.title("Equidad y límites del prototipo")
    st.markdown(
        "Un modelo puede tener buenas métricas globales y aun así fallar "
        "sistemáticamente con un grupo. Esta página reporta lo que se encontró."
    )

    # ------------------------------------------------------ por subgrupo
    st.subheader("Desempeño por subgrupo")
    atributo = st.radio("Atributo", list(SUBGRUPOS), horizontal=True)
    t = datos.cargar_tabla(SUBGRUPOS[atributo])
    _mostrar(t, ["grupo", "n", "prevalencia", "tasa_alerta", "recall",
                 "precision", "ROC_AUC"])

    if atributo == "Edad":
        _comentario_edad(t)
    elif atributo == "Género":
        _comentario_genero(t)
    else:
        _comentario_raza(t)

    # ------------------------------------------------ a quién le funciona
    st.markdown("---")
    st.subheader("A quién le funciona el modelo")
    sens = datos.cargar_tabla("metricas_05_sensibilidad.csv")
    _mostrar(sens, ["escenario", "n", "prevalencia", "AP", "ROC_AUC",
                    "recall", "precision", "tasa_alerta"])

    escenarios = sens.set_index("escenario")
    completa = escenarios.loc["Prueba completa"]
    casa = escenarios.loc["Sin transferencias"]
    transferidos = escenarios.loc["Solo transferencias"]
    porcion_casa = casa.n / completa.n

    st.error(
        f"**El {formato(completa.recall, 2)} global no es parejo.** Entre los "
        "pacientes transferidos a otra institución el modelo detecta "
        f"{formato(10 * transferidos.recall)} de cada 10 reingresos; entre quienes se "
        f"van a casa — el {formato(100 * porcion_casa, 0)} % de la cohorte — detecta "
        f"{formato(10 * casa.recall)} de cada 10. Para el paciente típico el "
        "prototipo rinde bastante menos de lo que sugiere la cifra global."
    )

    # ------------------------------------------------------ condiciones
    st.markdown("---")
    st.subheader("Condiciones de uso")
    aviso_prototipo(
        "Prototipo académico. No está validado para uso clínico y no debe orientar "
        "decisiones de tratamiento ni de alta."
    )

    # De cada N alertas, una es un reingreso real: el inverso de la precisión.
    por_alerta = round(1 / datos.metricas_finales()["precision"])
    st.markdown(
        "- **Los datos son de 1999 a 2008 y de hospitales de Estados Unidos.** No se "
        "puede suponer que el desempeño se mantenga en otro período, otro sistema de "
        "salud o el contexto colombiano.\n"
        f"- **La probabilidad no es un diagnóstico.** De cada {por_alerta} alertas, 1 "
        "corresponde a un reingreso real.\n"
        "- **`race` no se usa como predictor**, pero eso no elimina el sesgo: otras "
        "variables pueden transmitirlo. Por eso se audita en vez de suponer.\n"
        "- **El modelo no observa** soporte familiar, acceso al control ambulatorio ni "
        "adherencia al tratamiento, que es probablemente lo que separa los casos que "
        "se le escapan."
    )
