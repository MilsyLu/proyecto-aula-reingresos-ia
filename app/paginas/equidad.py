# -*- coding: utf-8 -*-
"""Equidad y límites del prototipo.

Un modelo puede tener buenas métricas globales y aun así fallar de manera
sistemática con un grupo. Esta página audita eso y, sobre todo, dice en voz alta
dónde el prototipo no sirve.

Las cifras de los comentarios se calculan de las mismas tablas que se muestran,
no se escriben a mano: así ningún párrafo puede contradecir a la tabla que tiene
encima. La disposición busca una sola pantalla: un atributo por pestaña, con la
tabla y su lectura lado a lado.
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


def _mostrar(df, columnas, tope=215):
    """Tabla con encabezados en español y números al estilo colombiano.

    La altura se ajusta al número de filas — 35 px por fila más el encabezado —
    para no dejar franjas vacías, y se topa para que no empuje nada fuera de
    pantalla: si hay más filas de las que caben, la tabla se desplaza sola.
    """
    visible = df[columnas].rename(columns=ENCABEZADOS)
    decimales = {ENCABEZADOS[c]: (lambda v: formato(v, 4))
                 for c in columnas if c not in ("grupo", "escenario", "n")}
    if "n" in columnas:
        decimales[ENCABEZADOS["n"]] = entero
    st.dataframe(visible.style.format(decimales), width="stretch",
                 hide_index=True, height=min(35 * len(visible) + 40, tope))


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
        "La prevalencia real es parecida en todos los grupos: el modelo alerta más "
        "sobre los mayores porque acumulan las señales que aprendió a reconocer."
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
        "permiten afirmar nada: no es lo mismo decir que no hay sesgo que decir que "
        "no hay datos para medirlo."
    )


COMENTARIOS = {
    "Edad": _comentario_edad,
    "Género": _comentario_genero,
    "Grupo racial": _comentario_raza,
}


def render():
    enc, aviso = st.columns([2, 1.2], vertical_alignment="center")
    with enc:
        st.markdown("## Equidad y límites del prototipo")
        st.caption("Buenas métricas globales no impiden fallar con un grupo entero.")
    with aviso:
        aviso_prototipo(
            "Prototipo académico. No está validado para uso clínico y no debe "
            "orientar decisiones de tratamiento ni de alta."
        )

    # ------------------------------------------ por subgrupo, uno por pestaña
    st.markdown("### Desempeño por subgrupo")
    for pestana, (atributo, archivo) in zip(st.tabs(list(SUBGRUPOS)),
                                            SUBGRUPOS.items()):
        with pestana:
            t = datos.cargar_tabla(archivo)
            tabla, lectura = st.columns([1.35, 1])
            with tabla:
                _mostrar(t, ["grupo", "n", "prevalencia", "tasa_alerta", "recall",
                             "precision", "ROC_AUC"])
            with lectura:
                COMENTARIOS[atributo](t)

    # ------------------------------------------------ a quién le funciona
    st.markdown("### A quién le funciona el modelo")
    sens = datos.cargar_tabla("metricas_05_sensibilidad.csv")

    tabla, lectura = st.columns([1.35, 1])
    with tabla:
        _mostrar(sens, ["escenario", "n", "prevalencia", "AP", "ROC_AUC",
                        "recall", "precision", "tasa_alerta"])

    escenarios = sens.set_index("escenario")
    completa = escenarios.loc["Prueba completa"]
    casa = escenarios.loc["Sin transferencias"]
    transferidos = escenarios.loc["Solo transferencias"]
    porcion_casa = casa.n / completa.n

    with lectura:
        st.error(
            f"**El {formato(completa.recall, 2)} global no es parejo.** Entre los "
            "transferidos a otra institución el modelo detecta "
            f"{formato(10 * transferidos.recall)} de cada 10 reingresos; entre "
            f"quienes se van a casa — el {formato(100 * porcion_casa, 0)} % de la "
            f"cohorte — detecta {formato(10 * casa.recall)} de cada 10. Para el "
            "paciente típico rinde menos de lo que sugiere la cifra global."
        )

    # ------------------------------------------------------ condiciones de uso
    st.markdown("### Condiciones de uso")
    # De cada N alertas, una es un reingreso real: el inverso de la precisión.
    por_alerta = round(1 / datos.metricas_finales()["precision"])
    condiciones = [
        "**Datos de 1999 a 2008, de EE. UU.** Nada garantiza igual desempeño en "
        "Colombia.",
        f"**La probabilidad no es un diagnóstico.** De cada {por_alerta} alertas, "
        "1 es un reingreso real.",
        "**`race` no es predictor**, pero otras variables transmiten el sesgo: "
        "por eso se audita.",
        "**No observa** soporte familiar, control ambulatorio ni adherencia: eso "
        "es lo que se le escapa.",
    ]
    for columna, texto in zip(st.columns(4), condiciones):
        columna.caption(texto)
