"""Traduce métricas comparativas a explicaciones comprensibles, sin IA externa.

Solo utiliza las cifras del experimento ejecutado. No diagnostica ni recomienda
intervenciones clínicas. Mantiene separada selección en validación de prueba.
"""
from __future__ import annotations

import pandas as pd


def porcentaje(valor, decimales=1):
    return f"{100 * float(valor):.{decimales}f}".replace(".", ",") + " %"


def resumen_comprensible(resultado: dict) -> dict:
    """Devuelve párrafos interpretativos, indicadores y glosario.

    La elección proviene del entrenamiento: mayor AP de validación. Aunque
    el modelo alternativo gane en prueba, no se cambia el ganador a posteriori.
    """
    tabla = resultado["comparacion"].set_index("modelo")
    ganador = resultado["elegido"]
    if ganador not in tabla.index or len(tabla) != 2:
        raise ValueError("Se requieren exactamente dos modelos comparables.")
    otro = next(nombre for nombre in tabla.index if nombre != ganador)
    g, a = tabla.loc[ganador], tabla.loc[otro]
    delta = float(g["AP_validacion"] - a["AP_validacion"])
    n = int(g["VP"] + g["FN"] + g["FP"] + g["VN"])
    positivos = int(g["VP"] + g["FN"])
    prevalencia = positivos / n if n else 0.0

    seleccion = (
        f"Se recomienda {ganador} porque, al analizar los datos de validación, "
        f"obtuvo una puntuación AP de {porcentaje(g['AP_validacion'])}, frente a "
        f"{porcentaje(a['AP_validacion'])} de {otro}. "
        f"La diferencia es de {delta * 100:.2f} puntos porcentuales "
        f"de AP (aproximadamente). La AP resume qué tan bien el modelo "
        "prioriza los verdaderos reingresos entre sus alertas al recorrer "
        "distintos umbrales. Es el criterio principal porque los reingresos "
        "son minoritarios."
    )
    if delta < 0.01:
        seleccion += (
            " La diferencia es menor a un punto porcentual de AP: "
            "no basta para declarar una superioridad sólida sin más pruebas."
        )

    g_test, a_test = float(g["AP_prueba"]), float(a["AP_prueba"])
    if g_test >= a_test:
        prueba = (
            f"En los datos reservados para la prueba, {ganador} también obtuvo "
            f"mayor o igual AP ({porcentaje(g_test)} frente a "
            f"{porcentaje(a_test)}). Esto respalda la decisión inicial, "
            "aunque no demuestra que ocurra lo mismo en otros hospitales."
        )
    else:
        prueba = (
            f"En la prueba final, {otro} obtuvo una AP mayor "
            f"({porcentaje(a_test)} frente a {porcentaje(g_test)} de {ganador}). "
            "Esto muestra incertidumbre en la comparación: no se cambia el "
            "ganador usando la prueba, porque eso sesgaría la evaluación. "
            "Conviene repetir el estudio con otros grupos independientes."
        )

    decisiones = []
    for nombre, fila in tabla.iterrows():
        vp, fn, fp, vn = [int(fila[k]) for k in ("VP", "FN", "FP", "VN")]
        alertas = vp + fp
        decisiones.append({
            "nombre": nombre,
            "texto": (
                f"Con {nombre}, de {positivos:,} reingresos reales se detectaron "
                f"{vp:,} y se pasaron por alto {fn:,}. "
                f"Se generaron {alertas:,} alertas: {vp:,} acertadas "
                f"y {fp:,} que no correspondían a un reingreso. "
                f"Los {vn:,} casos restantes eran personas que no reingresaron "
                "y tampoco recibieron alerta."
            ).replace(",", "."),
            "recall": porcentaje(fila["recall_prueba"]),
            "precision": porcentaje(fila["precision_prueba"]),
            "alertas": alertas,
            "vp": vp,
            "fp": fp,
            "fn": fn,
            "vn": vn,
        })

    glosario = [
        ("AP (Average Precision)",
         "Resume la capacidad para colocar casos que sí reingresan entre las primeras "
         "alertas al cambiar el umbral. Cuanto mayor, mejor. No es la probabilidad "
         "de acertar una alerta individual."),
        ("Sensibilidad / Recall",
         "De todas las hospitalizaciones que terminaron en un reingreso, qué "
         "proporción se identificó. Recall del 60 % significa detectar "
         "aproximadamente 6 de cada 10 reingresos reales."),
        ("Precisión",
         "De todas las alertas emitidas, cuántas correspondían a reingresos reales. "
         "Una precisión de 20 % significa aproximadamente 2 alertas acertadas de cada 10."),
        ("ROC-AUC",
         "Mide la capacidad general de ordenar un caso positivo por encima de uno "
         "negativo. Cerca de 0,5 corresponde aproximadamente al azar; 1 es ideal."),
        ("Verdadero positivo (VP)",
         "Hubo alerta y sí ocurrió un reingreso dentro de 30 días."),
        ("Falso positivo (FP)",
         "Hubo alerta, pero no ocurrió un reingreso dentro de 30 días. "
         "Puede consumir capacidad de seguimiento."),
        ("Falso negativo (FN)",
         "No hubo alerta, aunque sí ocurrió un reingreso. Es un caso no detectado."),
        ("Verdadero negativo (VN)",
         "No hubo alerta y tampoco ocurrió un reingreso."),
        ("Umbral",
         "Valor de probabilidad desde el que se genera una alerta. Cambiarlo "
         "modifica el equilibrio entre detectar más casos y emitir falsas alertas."),
        ("Entrenamiento, validación y prueba",
         "Entrenamiento enseña al algoritmo; validación sirve para elegir "
         "configuración, modelo y umbral; prueba verifica el resultado final "
         "en registros reservados que no se usaron para elegir."),
        ("Sobreajuste",
         "Sucede cuando un modelo funciona mucho mejor en entrenamiento que "
         "en datos nuevos. Una brecha alta de AP entre train y validación es "
         "señal para investigar, no una conclusión automática."),
        ("Red neuronal MLP y Gradient Boosting",
         "Una MLP aprende mediante capas de neuronas artificiales; "
         "Gradient Boosting combina muchos árboles pequeños para mejorar errores. "
         "El algoritmo más complejo no necesariamente tiene mejores resultados."),
    ]
    return {
        "ganador": ganador,
        "alternativo": otro,
        "seleccion": seleccion,
        "prueba": prueba,
        "filas_prueba": n,
        "prevalencia_prueba": prevalencia,
        "decisiones": decisiones,
        "glosario": glosario,
        "advertencia": (
            "Este análisis describe únicamente los datos de este experimento. "
            "Las probabilidades no indican que un paciente vaya a reingresar "
            "con certeza y el laboratorio no está validado para tomar "
            "decisiones clínicas. El modelo utilizado por el cliente no se "
            "modifica automáticamente."
        ),
    }


def informe_texto(resultado: dict) -> str:
    """Genera un informe en español para descargar y compartir."""
    info = resumen_comprensible(resultado)
    partes = [
        "LECTURA SENCILLA DE LA COMPARACIÓN DE MODELOS",
        "",
        "1. ¿POR QUÉ SE ELIGIÓ ESTE MODELO?",
        info["seleccion"], "",
        "2. ¿QUÉ PASÓ CON LOS DATOS DE PRUEBA?",
        info["prueba"], "",
        "3. ¿QUÉ SIGNIFICAN LAS ALERTAS?",
    ]
    for fila in info["decisiones"]:
        partes.extend([fila["texto"], ""])
    partes.extend(["4. DICCIONARIO DE MÉTRICAS"])
    for termino, explicacion in info["glosario"]:
        partes.extend([termino + ": " + explicacion, ""])
    partes.extend(["5. LIMITACIONES", info["advertencia"]])
    return "\n".join(partes)
