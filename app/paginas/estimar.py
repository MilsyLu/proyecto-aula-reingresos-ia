# -*- coding: utf-8 -*-
"""Estimación individual: formulario, resultado y por qué salió así."""
from __future__ import annotations

import streamlit as st

import datos
import estilo
import modelo
from datos import AZUL, GRIS, TERRACOTA, VERDE, formato


def _campo_numero(etiqueta, minimo, maximo, valor, ayuda=None):
    return st.number_input(etiqueta, min_value=minimo, max_value=maximo,
                           value=valor, step=1, help=ayuda)


def _formulario():
    tipicos = modelo.valores_tipicos()
    with st.form("datos"):
        izq, centro, der = st.columns(3)

        with izq:
            st.markdown("**Paciente**")
            edad = _campo_numero("Edad", 1, 100, int(tipicos["edad"]),
                                 "El modelo se entrenó con edades agrupadas por décadas.")
            genero = st.selectbox("Género", list(modelo.GENEROS),
                                  format_func=lambda v: modelo.GENEROS[v])
            st.markdown("**Uso previo de servicios (último año)**")
            ingresos = _campo_numero("Hospitalizaciones previas", 0, 25, 0)
            urgencias = _campo_numero("Visitas a urgencias", 0, 80, 0)
            consultas = _campo_numero("Consultas externas", 0, 45, 0)

        with centro:
            st.markdown("**Esta hospitalización**")
            dias = _campo_numero("Días de estancia", 1, 20, int(tipicos["dias"]))
            labs = _campo_numero("Pruebas de laboratorio", 0, 140, int(tipicos["labs"]))
            meds = _campo_numero("Medicamentos administrados", 0, 85,
                                 int(tipicos["meds"]))
            diagnosticos = _campo_numero("Diagnósticos registrados", 1, 16,
                                         int(tipicos["diagnosticos"]))
            procedimientos = _campo_numero("Procedimientos", 0, 8,
                                           int(tipicos["procedimientos"]))

        with der:
            st.markdown("**Clínica**")
            diag1 = st.selectbox("Diagnóstico principal", list(modelo.DIAGNOSTICOS),
                                 format_func=lambda v: modelo.DIAGNOSTICOS[v])
            a1c = st.selectbox("Hemoglobina glicosilada (HbA1c)", list(modelo.A1C),
                               format_func=lambda v: modelo.A1C[v])
            insulina = st.selectbox("Insulina", list(modelo.INSULINA),
                                    format_func=lambda v: modelo.INSULINA[v])
            cambio = st.selectbox("Hubo cambio de medicación", list(modelo.CAMBIO_MED),
                                  format_func=lambda v: modelo.CAMBIO_MED[v])
            egreso = st.selectbox("Tipo de egreso", list(modelo.EGRESOS),
                                  format_func=lambda v: modelo.EGRESOS[v])

        enviado = st.form_submit_button("Calcular riesgo", type="primary",
                                        width="stretch")

    return enviado, {
        "edad": edad, "genero": genero, "ingresos": ingresos, "urgencias": urgencias,
        "consultas": consultas, "dias": dias, "labs": labs, "meds": meds,
        "diagnosticos": diagnosticos, "procedimientos": procedimientos,
        "diag1": diag1, "a1c": a1c, "insulina": insulina, "cambio": cambio,
        "egreso": egreso,
    }


def _resultado(entradas, umbral):
    with st.spinner("Calculando…"):
        base, efectos = modelo.explicar(entradas)
    st.session_state["ultima_estimacion"] = {
        "entradas": entradas, "riesgo": base, "efectos": efectos, "umbral": umbral}

    prevalencia = 0.1139
    alerta = base >= umbral
    color = TERRACOTA if alerta else VERDE
    rotulo = "Entra en seguimiento" if alerta else "No entra en seguimiento"

    st.divider()
    izq, der = st.columns([1, 1.9])

    with izq:
        st.markdown(
            f'<div class="tarjeta" style="text-align:center;border-color:{color}">'
            f'<div class="etiqueta">Probabilidad estimada</div>'
            f'<div style="font-size:3.1rem;font-weight:600;color:{color};'
            f'line-height:1.15;margin:0.2rem 0">{formato(base * 100)} %</div>'
            f'<div style="color:{color};font-weight:600;font-size:0.9rem">{rotulo}</div>'
            f'</div>', unsafe_allow_html=True)
        st.progress(min(base / 0.5, 1.0))
        st.caption(f"Umbral de alerta: {formato(umbral * 100, 2)} %  ·  "
                   f"tasa general de la cohorte: {formato(prevalencia * 100)} %")

    with der:
        veces = base / prevalencia
        st.markdown("#### Cómo leer este número")
        st.markdown(
            f"- De cada 100 hospitalizaciones con este perfil, cerca de "
            f"**{formato(base * 100, 0)} terminan en un reingreso** antes de 30 días.\n"
            f"- Es **{formato(veces, 1)} veces** la tasa general de la cohorte, que es "
            f"{formato(prevalencia * 100)} %.\n"
            f"- El umbral de {formato(umbral * 100, 2)} % no es un cálculo: es una "
            f"**decisión de política** que fija la coordinación del programa según a "
            f"cuánta gente pueda hacerle seguimiento.")
        estilo.aviso_prototipo(
            "De cada 6 alertas, 1 corresponde a un reingreso real. Esta estimación "
            "puede <b>añadir</b> seguimiento, nunca restringir atención.")

    _explicacion(base, efectos)


def _explicacion(base, efectos):
    st.markdown("### Por qué salió este número")
    if not efectos:
        st.info("Este paciente se parece al perfil típico del conjunto de "
                "entrenamiento, así que ningún dato lo separa de la media.")
        return

    st.caption("Se vuelve a calcular el riesgo cambiando un dato a la vez por el valor "
               "típico de la población. La diferencia es lo que aporta ese dato.")

    for efecto in efectos[:6]:
        sube = efecto["efecto"] > 0
        color = TERRACOTA if sube else VERDE
        verbo = "subiría" if sube else "bajaría"
        destino = "bajaría" if sube else "subiría"
        st.markdown(
            f'<div class="tarjeta" style="padding:0.75rem 1rem;margin-bottom:0.55rem;'
            f'border-left:3px solid {color}">'
            f'<div style="display:flex;justify-content:space-between;align-items:baseline">'
            f'<div><b>{efecto["nombre"]}</b>: {efecto["valor"]}</div>'
            f'<div style="color:{color};font-weight:600">'
            f'{"+" if sube else "−"}{formato(abs(efecto["efecto"]) * 100)} puntos</div></div>'
            f'<div style="color:{GRIS};font-size:0.85rem;margin-top:3px">'
            f'Si fuera {efecto["tipico"]}, como la mayoría, el riesgo {destino} de '
            f'{formato(base * 100)} % a {formato(efecto["riesgo_sin_el"] * 100)} %.'
            f'</div></div>', unsafe_allow_html=True)

    with st.expander("¿De dónde sale esta explicación?"):
        st.markdown(
            "No usa SHAP ni ninguna aproximación. Para cada dato del formulario se "
            "sustituye su valor por el típico de la población de entrenamiento y se "
            "vuelve a consultar el modelo. La diferencia entre las dos predicciones "
            "**es** el aporte de ese dato, medido, no estimado.\n\n"
            "Lo que no hace: repartir el riesgo total entre las variables. Los efectos "
            "no suman el riesgo porque el modelo no es aditivo — hay interacciones "
            "entre variables que ninguna descomposición simple recoge.")


def render():
    umbral = datos.umbral_oficial()
    st.title("Estimar el riesgo de reingreso")
    st.markdown(
        "Describa la hospitalización que acaba de terminar. El modelo devuelve la "
        "**probabilidad estimada** de que el paciente vuelva a ser hospitalizado "
        "**antes de 30 días**.")

    enviado, entradas = _formulario()

    st.caption(
        "El formulario recoge las 15 variables más influyentes. Las 35 restantes toman "
        "el valor típico del conjunto de entrenamiento: la mediana para los números y "
        "la categoría más frecuente para el texto.")

    if enviado:
        _resultado(entradas, umbral)
    elif st.session_state.get("ultima_estimacion"):
        previa = st.session_state["ultima_estimacion"]
        _resultado(previa["entradas"], previa["umbral"])
