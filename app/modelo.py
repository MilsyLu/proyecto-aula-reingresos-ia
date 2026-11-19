# -*- coding: utf-8 -*-
"""Construcción de la fila de entrada, predicción y explicación por paciente.

La explicación no usa SHAP. Usa una comparación contrafactual: se vuelve a predecir
poniéndole a una variable el valor típico de la población de entrenamiento y se mide
cuánto cambia el riesgo. Tiene tres ventajas sobre SHAP para este caso:

* Es exacta, no una aproximación.
* Se lee sola: "si no tuviera 5 ingresos previos, su riesgo bajaría del 30 % al 12 %".
* No añade dependencias ni tiempo de arranque.

El costo es que no reparte el riesgo total entre variables, pero esa suma tampoco es
lo que a un clínico le sirve.
"""
from __future__ import annotations

import pandas as pd

import datos

# --- opciones del formulario -------------------------------------------------
GENEROS = {"Female": "Femenino", "Male": "Masculino"}

DIAGNOSTICOS = {
    "Circulatorio": "Circulatorio",
    "Respiratorio": "Respiratorio",
    "Digestivo": "Digestivo",
    "Diabetes": "Diabetes",
    "Lesiones": "Lesiones",
    "Musculoesqueletico": "Musculoesquelético",
    "Genitourinario": "Genitourinario",
    "Neoplasias": "Neoplasias",
    "Otros": "Otros",
}

A1C = {
    "Ausente": "No se midió",
    "Norm": "Normal",
    ">7": "Mayor que 7",
    ">8": "Mayor que 8",
}

INSULINA = {"No": "No se usó", "Steady": "Sin cambio", "Up": "Se aumentó", "Down": "Se redujo"}

CAMBIO_MED = {"No": "No", "Ch": "Sí"}

EGRESOS = {
    "1": "A casa",
    "6": "A casa con atención domiciliaria",
    "3": "Transferido a centro de enfermería (SNF)",
    "2": "Transferido a otro hospital",
    "22": "Transferido a rehabilitación",
    "5": "Transferido a otra institución",
    "4": "Transferido a cuidado intermedio (ICF)",
}

TRANSFERENCIAS = {"2", "3", "4", "5", "22"}

# campo del formulario -> columna del modelo, para sacar el valor típico
EQUIVALENCIA = {
    "edad": "edad_num",
    "genero": "gender",
    "ingresos": "number_inpatient",
    "urgencias": "number_emergency",
    "consultas": "number_outpatient",
    "dias": "time_in_hospital",
    "labs": "num_lab_procedures",
    "meds": "num_medications",
    "diagnosticos": "number_diagnoses",
    "procedimientos": "num_procedures",
    "diag1": "grupo_diag_1",
    "a1c": "A1Cresult",
    "insulina": "insulin",
    "cambio": "change",
    "egreso": "discharge_disposition_id",
}

NOMBRE_CAMPO = {
    "edad": "Edad",
    "genero": "Género",
    "ingresos": "Hospitalizaciones previas",
    "urgencias": "Visitas a urgencias",
    "consultas": "Consultas externas",
    "dias": "Días de estancia",
    "labs": "Pruebas de laboratorio",
    "meds": "Medicamentos administrados",
    "diagnosticos": "Diagnósticos registrados",
    "procedimientos": "Procedimientos",
    "diag1": "Diagnóstico principal",
    "a1c": "Hemoglobina glicosilada",
    "insulina": "Insulina",
    "cambio": "Cambio de medicación",
    "egreso": "Tipo de egreso",
}

ETIQUETAS = {
    "genero": GENEROS, "diag1": DIAGNOSTICOS, "a1c": A1C,
    "insulina": INSULINA, "cambio": CAMBIO_MED, "egreso": EGRESOS,
}


def mostrar(campo, valor):
    """Cómo se le enseña al usuario el valor de un campo."""
    mapa = ETIQUETAS.get(campo)
    if mapa:
        return mapa.get(str(valor), str(valor))
    if isinstance(valor, float) and valor.is_integer():
        return datos.entero(valor)
    return datos.entero(valor) if isinstance(valor, (int, float)) else str(valor)


# El archivo de valores por defecto calculó la moda de A1Cresult ignorando los
# vacíos, y por eso dice '>8'. En la cohorte real 82.509 de 99.343 pacientes no
# tienen la prueba, así que lo típico es no habérsela hecho.
TIPICO_CORREGIDO = {"a1c": "Ausente"}


def valores_tipicos():
    """El paciente promedio del conjunto de entrenamiento, campo por campo."""
    _, _, por_defecto = datos.cargar_columnas()
    tipicos = {campo: por_defecto[columna] for campo, columna in EQUIVALENCIA.items()}
    tipicos.update(TIPICO_CORREGIDO)
    return tipicos


def construir_fila(entradas: dict) -> pd.DataFrame:
    """Completa las 50 variables del modelo a partir de los 15 campos del formulario.

    Las 35 restantes toman el valor típico del entrenamiento. Las derivadas se
    recalculan siempre, porque dependen de lo que escribió el usuario.
    """
    numericas, categoricas, por_defecto = datos.cargar_columnas()
    fila = dict(por_defecto)

    dias = max(float(entradas["dias"]), 1.0)
    ingresos = float(entradas["ingresos"])
    urgencias = float(entradas["urgencias"])
    consultas = float(entradas["consultas"])
    meds = float(entradas["meds"])
    labs = float(entradas["labs"])
    a1c = entradas["a1c"]

    fila.update({
        "edad_num": float(entradas["edad"]),
        "gender": entradas["genero"],
        "number_inpatient": ingresos,
        "number_emergency": urgencias,
        "number_outpatient": consultas,
        "servicios_previos": ingresos + urgencias + consultas,
        "tuvo_ingreso_previo": float(ingresos > 0),
        "time_in_hospital": dias,
        "num_lab_procedures": labs,
        "num_medications": meds,
        "number_diagnoses": float(entradas["diagnosticos"]),
        "num_procedures": float(entradas["procedimientos"]),
        "meds_por_dia": meds / dias,
        "labs_por_dia": labs / dias,
        "grupo_diag_1": entradas["diag1"],
        "A1Cresult": a1c,
        # 'Ausente' es la categoria que el modelo aprendio para "no se midio"
        "a1c_medida": float(a1c != "Ausente"),
        "insulin": entradas["insulina"],
        "change": entradas["cambio"],
        "hubo_cambio_med": float(entradas["cambio"] == "Ch"),
        "discharge_disposition_id": str(entradas["egreso"]),
    })

    X = pd.DataFrame([fila])[numericas + categoricas]
    X[categoricas] = X[categoricas].astype(str)
    return X


def predecir(entradas: dict) -> float:
    modelo = datos.cargar_modelo()
    return float(modelo.predict_proba(construir_fila(entradas))[0, 1])


def explicar(entradas: dict, minimo=0.002):
    """Cuánto mueve cada dato el riesgo de este paciente.

    Para cada campo se sustituye su valor por el típico de la población y se vuelve
    a predecir. La diferencia es el efecto de ese dato. Son 15 predicciones, menos
    de una centésima de segundo.
    """
    base = predecir(entradas)
    tipicos = valores_tipicos()
    efectos = []
    for campo, tipico in tipicos.items():
        if campo not in entradas:
            continue
        if str(entradas[campo]) == str(tipico):
            continue
        alterado = dict(entradas)
        alterado[campo] = tipico
        sin_el = predecir(alterado)
        efecto = base - sin_el
        if abs(efecto) < minimo:
            continue
        efectos.append({
            "campo": campo,
            "nombre": NOMBRE_CAMPO[campo],
            "valor": mostrar(campo, entradas[campo]),
            "tipico": mostrar(campo, tipico),
            "riesgo_sin_el": sin_el,
            "efecto": efecto,
        })
    efectos.sort(key=lambda e: abs(e["efecto"]), reverse=True)
    return base, efectos
