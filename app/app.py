# -*- coding: utf-8 -*-
"""
Prototipo de estimacion de riesgo de reingreso hospitalario a 30 dias.

Proyecto de aula de Inteligencia Artificial - Grupo 04
Universidad Popular del Cesar - Ingenieria de Sistemas - 2026

Prototipo academico. No es una herramienta de decision clinica.
"""
import json
import hashlib
import io
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent.parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from src.procesamiento_lotes import ArchivoIncompatible, preparar_lote, predecir_lote
from src.analisis_calidad import resumen_calidad, resumen_numericas, distribucion_objetivo
MODELO_RUTA = BASE / "models" / "gradient_boosting_ajustado.joblib"
REPORTES = BASE / "reports"

AZUL, TERRACOTA, VERDE, GRIS = "#1F3B63", "#A8502A", "#0C6B6A", "#5A6472"

st.set_page_config(page_title="Riesgo de reingreso a 30 dias",
                   page_icon="chart_with_upwards_trend", layout="wide")


# --------------------------------------------------------------------------- datos
@st.cache_resource
def cargar_modelo():
    return joblib.load(MODELO_RUTA)


@st.cache_data
def cargar_config():
    cfg = json.loads((Path(__file__).parent / "valores_por_defecto.json").read_text(encoding="utf-8"))
    umbral = json.loads((REPORTES / "umbral_elegido.json").read_text(encoding="utf-8"))
    return cfg, umbral


@st.cache_data
def cargar_predicciones():
    return pd.read_csv(REPORTES / "predicciones_prueba.csv")


@st.cache_data
def cargar_tabla(nombre):
    return pd.read_csv(REPORTES / nombre)


modelo = cargar_modelo()
CFG, UMB = cargar_config()
NUM, CAT, DEF = CFG["numericas"], CFG["categoricas"], CFG["por_defecto"]
UMBRAL = UMB["umbral"]


def num(valor, decimales=1):
    """Formatea un numero al estilo colombiano: coma decimal, punto de miles."""
    s = f"{valor:,.{decimales}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def metricas_en(df, umbral):
    """Recalcula las metricas del conjunto de prueba para un umbral dado."""
    alerta = (df.probabilidad >= umbral).astype(int)
    real = df.reingreso_real
    vp = int(((real == 1) & (alerta == 1)).sum())
    fn = int(((real == 1) & (alerta == 0)).sum())
    fp = int(((real == 0) & (alerta == 1)).sum())
    vn = int(((real == 0) & (alerta == 0)).sum())
    recall = vp / (vp + fn) if vp + fn else 0.0
    precision = vp / (vp + fp) if vp + fp else 0.0
    return dict(vp=vp, fn=fn, fp=fp, vn=vn, recall=recall, precision=precision,
                alertas=vp + fp, tasa=(vp + fp) / len(df),
                exactitud=(vp + vn) / len(df))


# --------------------------------------------------------------------------- barra lateral
st.sidebar.markdown(f"### <span style='color:{AZUL}'>Reingresos a 30 dias</span>",
                    unsafe_allow_html=True)
st.sidebar.caption("Proyecto de aula de IA - Grupo 04\nUniversidad Popular del Cesar")
pagina = st.sidebar.radio("Ir a", ["Estimar riesgo", "Procesamiento CSV", "Ciclo de ML (12 fases)",
                                   "Desempeno del modelo", "Equidad y limites", "Ficha del modelo"],
                          label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.warning("Prototipo academico. No es una herramienta de decision clinica.")


# =========================================================== 1. ESTIMAR RIESGO
if pagina == "Estimar riesgo":
    st.title("Estimar el riesgo de reingreso")
    st.markdown(
        "Describa la hospitalizacion que acaba de terminar. El modelo devuelve la "
        "**probabilidad estimada** de que el paciente vuelva a ser hospitalizado "
        "**antes de 30 dias**."
    )

    with st.form("datos"):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("**Paciente**")
            edad = st.slider("Edad", 5, 95, 65, 5)
            genero = st.selectbox("Genero", ["Female", "Male"],
                                  format_func=lambda v: "Femenino" if v == "Female" else "Masculino")
            st.markdown("**Uso previo de servicios (ultimo ano)**")
            ingresos = st.number_input("Hospitalizaciones previas", 0, 21, 0)
            urgencias = st.number_input("Visitas a urgencias", 0, 76, 0)
            consultas = st.number_input("Consultas externas", 0, 40, 0)

        with c2:
            st.markdown("**Esta hospitalizacion**")
            dias = st.slider("Dias de estancia", 1, 14, 4)
            labs = st.slider("Pruebas de laboratorio", 1, 132, 44)
            meds = st.slider("Medicamentos administrados", 1, 81, 15)
            diags = st.slider("Diagnosticos registrados", 1, 16, 8)
            procs = st.slider("Procedimientos", 0, 6, 1)

        with c3:
            st.markdown("**Clinica**")
            diag1 = st.selectbox("Diagnostico principal",
                                 ["Circulatorio", "Respiratorio", "Digestivo", "Diabetes",
                                  "Lesiones", "Musculoesqueletico", "Genitourinario",
                                  "Neoplasias", "Otros"])
            a1c = st.selectbox("Hemoglobina glicosilada (HbA1c)",
                               ["nan", "Norm", ">7", ">8"],
                               format_func=lambda v: "No se midio" if v == "nan" else v)
            insulina = st.selectbox("Insulina", ["No", "Steady", "Up", "Down"],
                                    format_func=lambda v: {"No": "No se uso", "Steady": "Sin cambio",
                                                           "Up": "Se aumento", "Down": "Se redujo"}[v])
            cambio = st.selectbox("Hubo cambio de medicacion", ["No", "Ch"],
                                  format_func=lambda v: "No" if v == "No" else "Si")
            egreso = st.selectbox(
                "Tipo de egreso",
                ["1", "6", "3", "2", "22", "5", "4"],
                format_func=lambda v: {
                    "1": "A casa", "6": "A casa con atencion domiciliaria",
                    "3": "Transferido a centro de enfermeria (SNF)",
                    "2": "Transferido a otro hospital",
                    "22": "Transferido a rehabilitacion",
                    "5": "Transferido a otra institucion",
                    "4": "Transferido a cuidado intermedio (ICF)"}[v])

        enviar = st.form_submit_button("Calcular riesgo", type="primary",
                                       use_container_width=True)

    if enviar:
        fila = dict(DEF)  # el resto de variables toma el valor tipico de entrenamiento
        fila.update({
            "edad_num": float(edad), "gender": genero,
            "number_inpatient": float(ingresos), "number_emergency": float(urgencias),
            "number_outpatient": float(consultas),
            "servicios_previos": float(ingresos + urgencias + consultas),
            "tuvo_ingreso_previo": float(ingresos > 0),
            "time_in_hospital": float(dias), "num_lab_procedures": float(labs),
            "num_medications": float(meds), "number_diagnoses": float(diags),
            "num_procedures": float(procs),
            "meds_por_dia": meds / dias, "labs_por_dia": labs / dias,
            "grupo_diag_1": diag1, "A1Cresult": a1c,
            "a1c_medida": float(a1c != "nan"),
            "insulin": insulina, "change": cambio,
            "hubo_cambio_med": float(cambio == "Ch"),
            "discharge_disposition_id": egreso,
        })
        X = pd.DataFrame([fila])[NUM + CAT]
        X[CAT] = X[CAT].astype(str)
        p = float(modelo.predict_proba(X)[0, 1])

        st.markdown("---")
        a, b = st.columns([1, 1.6])

        with a:
            color = TERRACOTA if p >= UMBRAL else VERDE
            st.markdown(
                f"<div style='text-align:center;padding:26px;border:2px solid {color};"
                f"border-radius:12px'>"
                f"<div style='font-size:14px;color:{GRIS}'>Probabilidad estimada</div>"
                f"<div style='font-size:62px;font-weight:700;color:{color};line-height:1.1'>"
                f"{num(100*p)} %</div>"
                f"<div style='font-size:15px;font-weight:600;color:{color}'>"
                f"{'SE RECOMIENDA SEGUIMIENTO' if p >= UMBRAL else 'Sin alerta'}</div>"
                f"</div>", unsafe_allow_html=True)

        with b:
            base = 0.1139
            veces = p / base
            st.markdown("#### Como leer este numero")
            st.markdown(
                f"- De cada 100 hospitalizaciones con este perfil, cerca de "
                f"**{100*p:.0f} terminan en un reingreso** antes de 30 dias.\n"
                f"- La tasa general de la cohorte es **11,4 %**. Este caso esta "
                f"**{num(veces)} veces** esa tasa.\n"
                f"- El umbral de alerta del prototipo es **{num(100*UMBRAL, 2)} %**, "
                f"elegido en validacion para detectar 6 de cada 10 reingresos."
            )
            st.progress(min(p / 0.5, 1.0))
            st.caption("Barra en escala 0 % a 50 %.")

        if p >= UMBRAL:
            st.info("**Que significa la alerta.** De cada 6 alertas, aproximadamente 1 "
                    "corresponde a un reingreso real. La alerta sirve para priorizar "
                    "seguimiento, no para anunciar que el reingreso va a ocurrir.")

        st.caption(
            "Las variables que no aparecen en el formulario toman el valor tipico del "
            "conjunto de entrenamiento (mediana para numeros, categoria mas frecuente "
            "para texto). El formulario recoge las variables mas influyentes, no las 50."
        )


# ========================================================= 2. PROCESAMIENTO CSV
elif pagina == "Procesamiento CSV":
    st.title("Procesamiento masivo de hospitalizaciones")
    st.markdown(
        "Cargue un archivo CSV con el esquema original **Diabetes 130-US Hospitals** "
        "o con las **50 variables ya preparadas** del modelo. El sistema valida el "
        "archivo, muestra sus problemas de calidad y estima el riesgo por fila."
    )
    st.warning(
        "Prototipo academico: use datos anonimizados. Los archivos se procesan "
        "en memoria, sin almacenamiento permanente. No es una decision clinica."
    )
    archivo = st.file_uploader("Seleccionar CSV", type=["csv"])
    if archivo is not None:
        if archivo.size > 30 * 1024 * 1024:
            st.error("El archivo supera el limite de 30 MB para esta version.")
        else:
            try:
                datos = pd.read_csv(io.BytesIO(archivo.getvalue()),
                                    na_values=["?"], low_memory=False)
                X_lote, descartes, resumen = preparar_lote(datos, NUM, CAT)
            except (ArchivoIncompatible, pd.errors.ParserError,
                    UnicodeDecodeError, ValueError, KeyError) as error:
                st.error(f"No se pudo procesar el archivo: {error}")
            else:
                c1, c2, c3 = st.columns(3)
                c1.metric("Filas recibidas", f"{resumen['recibidas']:,}")
                c2.metric("Validas para prediccion", f"{resumen['validas']:,}")
                c3.metric("Excluidas", f"{resumen['excluidas']:,}")
                st.caption(
                    f"Esquema detectado: {resumen['formato']}. "
                    "El numero de fila del reporte corresponde al CSV con cabecera."
                )
                st.subheader("Exploracion y calidad del dataset (EDA)")
                calidad = resumen_calidad(datos)
                numericas_eda, atipicos_eda = resumen_numericas(datos)
                objetivo_eda = distribucion_objetivo(datos)
                a, b, c = st.columns(3)
                a.metric("Columnas", calidad["columnas"])
                b.metric("Celdas sin dato", f'{calidad["celdas_faltantes"]:,}')
                c.metric("Filas duplicadas exactas", f'{calidad["duplicados"]:,}')
                st.caption(
                    "Los duplicados y valores extremos solo se informan: una "
                    "hospitalizacion no debe eliminarse automaticamente."
                )
                st.dataframe(calidad["tabla"], use_container_width=True, hide_index=True)
                faltantes = calidad["tabla"].query("faltantes > 0")
                if faltantes.empty:
                    st.success("No se encontraron valores faltantes.")
                else:
                    st.bar_chart(faltantes.set_index("columna")["porcentaje_faltante"],
                                 x_label="Columna", y_label="% faltante")
                if not numericas_eda.empty:
                    st.markdown("#### Variables numericas")
                    st.dataframe(numericas_eda.round(2), use_container_width=True,
                                 hide_index=True)
                    campo = st.selectbox("Distribucion de variable numerica",
                                         numericas_eda["variable"].tolist())
                    serie = pd.to_numeric(datos[campo], errors="coerce").dropna()
                    st.bar_chart(serie.round().value_counts().sort_index().rename("Filas"),
                                 x_label=campo, y_label="Cantidad")
                    st.markdown("#### Posibles valores atipicos (IQR)")
                    st.dataframe(atipicos_eda, use_container_width=True,
                                 hide_index=True)
                    st.caption(
                        "La regla IQR es exploratoria: no elimina registros ni "
                        "diagnostica errores en las observaciones."
                    )
                if not objetivo_eda.empty:
                    st.markdown("#### Distribucion de la variable objetivo")
                    st.dataframe(objetivo_eda, hide_index=True, use_container_width=True)
                    st.bar_chart(objetivo_eda.set_index("categoria")["registros"])
                    st.caption(
                        "La etiqueta real se presenta solo como descripcion; "
                        "nunca se utiliza para construir la prediccion."
                    )
                st.download_button(
                    "Descargar reporte de calidad",
                    calidad["tabla"].to_csv(index=False).encode("utf-8-sig"),
                    "reporte_calidad.csv", mime="text/csv",
                )
                if not descartes.empty:
                    st.subheader("Registros excluidos")
                    st.dataframe(descartes.head(100), use_container_width=True,
                                 hide_index=True)
                    st.download_button(
                        "Descargar reporte de exclusiones",
                        descartes.to_csv(index=False).encode("utf-8-sig"),
                        "exclusiones.csv", mime="text/csv"
                    )
                if X_lote.empty:
                    st.warning("Ningun registro valido para predecir.")
                else:
                    identidad = hashlib.sha256(archivo.getvalue()).hexdigest()
                    if st.button("Predecir registros validos", type="primary"):
                        try:
                            with st.spinner("Calculando probabilidades..."):
                                predicciones = predecir_lote(modelo, X_lote, UMBRAL)
                            st.session_state["lote_resultado"] = {
                                "identidad": identidad,
                                "predicciones": predicciones,
                            }
                        except (ValueError, TypeError) as error:
                            st.error(f"No fue posible generar predicciones: {error}")
                    resultado = st.session_state.get("lote_resultado")
                    if resultado and resultado["identidad"] == identidad:
                        predicciones = resultado["predicciones"]
                        st.success(f"Predicciones generadas: {len(predicciones):,}")
                        st.metric("Alertas de seguimiento",
                                  int((predicciones["alerta"] == "Seguimiento").sum()))
                        st.dataframe(predicciones.head(200), use_container_width=True,
                                     hide_index=True)
                        st.download_button(
                            "Descargar CSV con predicciones",
                            predicciones.to_csv(index=False).encode("utf-8-sig"),
                            "predicciones_reingreso.csv", mime="text/csv",
                        )
                        st.caption(
                            "El resultado se conserva mientras el archivo actual no "
                            "cambie. No se modifica el modelo ni se evalua su "
                            "rendimiento sin resultados reales verificados."
                        )

# ============================================== CICLO DE VIDA (12 FASES)
elif pagina == "Ciclo de ML (12 fases)":
    st.title("Las 12 fases del ciclo de Machine Learning")
    st.markdown(
        "Esta seccion conecta el programa entregado con las doce fases de "
        "desarrollo del modelo explicadas en clase. Una parte se ejecuto "
        "durante la investigacion (notebooks) y otra funciona en vivo "
        "mediante el formulario y el procesamiento CSV."
    )
    st.info(
        "Consultar una fase no vuelve a entrenar el modelo. Para reproducir "
        "un experimento, ejecute los notebooks en orden con el dataset UCI."
    )
    fases = [
        ("01", "Definir el problema",
         "Clasificacion binaria: reingreso antes de 30 dias (<30). "
         "La metrica principal es Average Precision por el desbalance de clases.",
         "README.md y reports/Fase_1_Proyecto_IA_Grupo04_Reingresos.pdf",
         "Documentada"),
        ("02", "Recoleccion de datos",
         "Dataset UCI Diabetes 130-US Hospitals (1999-2008). "
         "Puede cargarse un nuevo CSV en Procesamiento CSV.",
         "data/raw/IDs_mapping.csv; notebooks/01_preprocesamiento_particion.ipynb",
         "Carga interactiva"),
        ("03", "Exploracion y analisis (EDA)",
         "Resumen, faltantes, duplicados, distribuciones y valores extremos "
         "en archivos nuevos; EDA original en notebook 00.",
         "notebooks/00_EDA_fase1.ipynb; src/analisis_calidad.py",
         "EDA interactivo"),
        ("04", "Limpieza y preparacion",
         "Se validan esquemas y registros; se mantiene la imputacion "
         "del pipeline entrenado y se registran las exclusiones.",
         "notebooks/01_preprocesamiento_particion.ipynb; src/procesamiento_lotes.py",
         "Procesamiento interactivo"),
        ("05", "Ingenieria de caracteristicas",
         "12 caracteristicas derivadas, incluyendo uso previo, "
         "medicamentos por dia y grupos diagnosticos ICD-9.",
         "notebooks/01_preprocesamiento_particion.ipynb; src/procesamiento_lotes.py",
         "Procesamiento interactivo"),
        ("06", "Dividir los datos",
         "Particion 60/20/20 agrupada por paciente para evitar fugas "
         "entre entrenamiento, validacion y prueba.",
         "notebooks/01_preprocesamiento_particion.ipynb",
         "Experimento documentado"),
        ("07", "Seleccionar el algoritmo",
         "Se compararon clasificador mayoritario, regresion logistica "
         "y Gradient Boosting; se eligio el ultimo.",
         "notebooks/02_modelos_baseline.ipynb; reports/metricas_03_comparacion.csv",
         "Experimento documentado"),
        ("08", "Entrenar el modelo",
         "HistGradientBoostingClassifier entrenado y guardado como "
         "pipeline para inferencia.",
         "notebooks/03_hiperparametros.ipynb; models/gradient_boosting_ajustado.joblib",
         "Modelo disponible"),
        ("09", "Ajustar hiperparametros",
         "30 configuraciones con RandomizedSearchCV y "
         "validacion cruzada agrupada por paciente.",
         "notebooks/03_hiperparametros.ipynb; reports/mejores_hiperparametros.json",
         "Experimento documentado"),
        ("10", "Evaluar el modelo",
         "Se reportan AP, ROC-AUC, recall, precision, "
         "matriz de confusion y Brier en datos de prueba.",
         "notebooks/04_evaluacion_comparada.ipynb; reports/metricas_04_final.csv",
         "Resultados visibles"),
        ("11", "Validar generalizacion",
         "Separacion por paciente, validacion cruzada y "
         "auditoria de equidad/sensibilidad. No constituye validacion "
         "clinica externa en datos actuales.",
         "notebooks/05_equidad_sensibilidad.ipynb; reports/metricas_05_sensibilidad.csv",
         "Validacion interna"),
        ("12", "Desplegar el modelo",
         "Aplicacion Streamlit con prediccion manual, "
         "prediccion masiva y consulta de metricas.",
         "app/app.py; README.md",
         "Prototipo integrado"),
    ]
    for numero, nombre, explicacion, archivos, evidencia in fases:
        with st.expander(f"{numero} · {nombre} — {evidencia}"):
            st.write(explicacion)
            st.caption("Evidencia en el repositorio: " + archivos)
    st.caption(
        "Los CSV nuevos sin etiquetas conocidas sirven para inferencia, no "
        "para medir precision o reentrenar. Las doce etapas no se ejecutan "
        "todas en cada prediccion."
    )

# =========================================================== 2. DESEMPENO
elif pagina == "Desempeno del modelo":
    st.title("Desempeno del modelo")
    st.caption("Conjunto de prueba: 19.870 hospitalizaciones que el modelo nunca vio, "
               "evaluadas una sola vez.")

    pred = cargar_predicciones()

    c = st.columns(4)
    c[0].metric("Average precision", "0,2249", "1,97 x la prevalencia")
    c[1].metric("ROC-AUC", "0,6660", "meta: 0,65")
    c[2].metric("Sensibilidad", "0,6001", "meta: 0,60")
    c[3].metric("Precision", "0,1781", "meta: 0,20", delta_color="inverse")

    st.markdown("---")
    st.subheader("El umbral es una decision, no un calculo")
    st.markdown(
        f"El umbral oficial del prototipo es **{UMBRAL:.4f}**, elegido en el conjunto de "
        "validacion. Mueva el control para ver la compensacion entre detectar mas "
        "reingresos y generar mas alertas falsas."
    )
    st.caption("Este control es solo para visualizar. El resultado reportado en el informe "
               "corresponde al umbral fijado en validacion, no a este deslizador.")

    u = st.slider("Umbral", 0.02, 0.50, float(UMBRAL), 0.0005, format="%.4f")
    m = metricas_en(pred, u)

    k = st.columns(4)
    k[0].metric("Reingresos detectados", f"{m['vp']:,}".replace(",", "."),
                f"de {m['vp']+m['fn']:,}".replace(",", "."))
    k[1].metric("Sensibilidad", f"{m['recall']:.3f}".replace(".", ","))
    k[2].metric("Precision", f"{m['precision']:.3f}".replace(".", ","))
    k[3].metric("Poblacion alertada", f"{100*m['tasa']:.1f} %".replace(".", ","))

    mc = pd.DataFrame(
        [[m["vp"], m["fn"]], [m["fp"], m["vn"]]],
        index=["Reingreso real: SI", "Reingreso real: NO"],
        columns=["Modelo alerta", "Modelo no alerta"])
    izq, der = st.columns([1, 1])
    with izq:
        st.markdown("**Matriz de confusion**")
        st.dataframe(mc.style.format("{:,.0f}"), use_container_width=True)
    with der:
        st.markdown("**Lectura**")
        st.markdown(
            f"- **{m['vp']:,}** reingresos detectados a tiempo.\n"
            f"- **{m['fn']:,}** reingresos que se escaparon.\n"
            f"- **{m['fp']:,}** alertas sobre pacientes que no reingresaron.\n"
            f"- Exactitud global: **{100*m['exactitud']:.1f} %** — y conviene desconfiar "
            f"de ese numero: un modelo que nunca alerte alcanza 88,6 %."
            .replace(",", "."))

    st.markdown("---")
    st.subheader("Comparacion de modelos")
    comp = cargar_tabla("metricas_03_comparacion.csv")
    st.dataframe(comp, use_container_width=True, hide_index=True)
    st.caption("Gradient Boosting mejora a la regresion logistica en un 4,8 % de AP: "
               "una mejora real pero modesta, coherente con la literatura citada.")

    st.markdown("---")
    st.subheader("Distribucion de las probabilidades estimadas")
    hist = pd.DataFrame({
        "Reingreso real": np.where(pred.reingreso_real == 1, "Si reingreso", "No reingreso"),
        "Probabilidad": pred.probabilidad})
    st.bar_chart(
        hist.assign(bin=(hist.Probabilidad * 50).astype(int) / 50)
            .groupby(["bin", "Reingreso real"]).size().unstack(fill_value=0),
        color=[GRIS, TERRACOTA], height=300)
    st.caption("Los dos grupos se superponen bastante: por eso la discriminacion es "
               "moderada y el umbral importa tanto.")

# =========================================================== 3. EQUIDAD
elif pagina == "Equidad y limites":
    st.title("Equidad y limites del prototipo")
    st.markdown("Un modelo puede tener buenas metricas globales y aun asi fallar "
                "sistematicamente con un grupo. Esta pagina reporta lo que se encontro.")

    st.subheader("Desempeno por subgrupo")
    cual = st.radio("Atributo", ["Edad", "Genero", "Grupo racial"], horizontal=True)
    archivo = {"Edad": "metricas_05_subgrupos_edad.csv",
               "Genero": "metricas_05_subgrupos_genero.csv",
               "Grupo racial": "metricas_05_subgrupos_raza.csv"}[cual]
    t = cargar_tabla(archivo)
    muestra = t[["grupo", "n", "prevalencia", "tasa_alerta", "recall", "precision", "ROC_AUC"]]
    st.dataframe(muestra.style.format({
        "prevalencia": "{:.4f}", "tasa_alerta": "{:.4f}", "recall": "{:.4f}",
        "precision": "{:.4f}", "ROC_AUC": "{:.4f}"}), use_container_width=True,
        hide_index=True)

    if cual == "Edad":
        st.error(
            "**Disparidad confirmada por edad.** La tasa de alerta sube de 30 % en los "
            "menores de 50 a 51 % en los de 80 o mas, mientras el ROC-AUC baja de 0,713 a "
            "0,619. La prevalencia real es parecida en todos los grupos, asi que esa "
            "diferencia no esta justificada por un riesgo mayor: el modelo alerta mas "
            "sobre los mayores porque acumulan las senales que aprendio a reconocer.")
    elif cual == "Genero":
        st.success(
            "**Sin disparidad relevante.** Razon de paridad 0,905, por encima del umbral "
            "de 0,80. Las mujeres reciben algo mas de alertas y se les detectan mas "
            "reingresos, con precision practicamente igual.")
    else:
        st.warning(
            "**Entre los dos grupos grandes no se detecta disparidad** (Caucasian y "
            "AfricanAmerican, 18.499 casos entre los dos): paridad 0,987, mismo recall y "
            "misma precision. Los grupos pequenos (Asian: 143 casos) no permiten afirmar "
            "nada en ninguna direccion. No es lo mismo decir que no hay sesgo que decir "
            "que no hay datos para medirlo.")

    st.markdown("---")
    st.subheader("A quien le funciona el modelo")
    sens = cargar_tabla("metricas_05_sensibilidad.csv")
    st.dataframe(sens.style.format({
        "prevalencia": "{:.4f}", "AP": "{:.4f}", "ROC_AUC": "{:.4f}",
        "recall": "{:.4f}", "precision": "{:.4f}", "tasa_alerta": "{:.4f}"}),
        use_container_width=True, hide_index=True)
    st.error(
        "**El 0,60 global no es parejo.** Entre los pacientes transferidos a otra "
        "institucion el modelo detecta casi 9 de cada 10 reingresos; entre quienes se van "
        "a casa — el 79 % de la cohorte — detecta menos de 5 de cada 10. Para el paciente "
        "tipico el prototipo rinde bastante menos de lo que sugiere la cifra global.")

    st.markdown("---")
    st.subheader("Condiciones de uso")
    st.markdown(
        "- **Es un prototipo academico.** No esta validado para uso clinico y no debe "
        "orientar decisiones de tratamiento ni de alta.\n"
        "- **Los datos son de 1999 a 2008 y de hospitales de Estados Unidos.** No se "
        "puede suponer que el desempeno se mantenga en otro periodo, otro sistema de "
        "salud o el contexto colombiano.\n"
        "- **La probabilidad no es un diagnostico.** De cada 6 alertas, 1 corresponde a "
        "un reingreso real.\n"
        "- **`race` no se usa como predictor**, pero eso no elimina el sesgo: otras "
        "variables pueden transmitirlo. Por eso se audita en vez de suponer.\n"
        "- **El modelo no observa** soporte familiar, acceso al control ambulatorio ni "
        "adherencia al tratamiento, que es probablemente lo que separa los casos que se "
        "le escapan.")

# =========================================================== 4. FICHA
else:
    st.title("Ficha del modelo")

    a, b = st.columns(2)
    with a:
        st.markdown(f"""
#### Que hace
Estima la probabilidad de que una hospitalizacion de un paciente con diabetes
termine en un **reingreso antes de 30 dias**.

#### Datos
- **Fuente:** Diabetes 130-US Hospitals 1999-2008, UCI (dataset 296)
- **Cohorte:** 99.343 hospitalizaciones, 69.990 pacientes
- **Prevalencia:** 11,39 %
- **Particion:** 60/20/20 **por paciente**, con `StratifiedGroupKFold`

#### Modelo
- `HistGradientBoostingClassifier`
- 50 predictores: 17 numericos, 33 categoricos
- Elegido entre **30 combinaciones** de hiperparametros
- Umbral de decision: **{UMBRAL:.4f}**, fijado en validacion
        """)
    with b:
        st.markdown("""
#### Desempeno en prueba
| Metrica | Valor | IC 95 % |
|---|---|---|
| Average precision | 0,2249 | [0,2047 ; 0,2467] |
| ROC-AUC | 0,6660 | [0,6527 ; 0,6786] |
| Sensibilidad | 0,6001 | [0,5766 ; 0,6202] |
| Precision | 0,1781 | |
| Brier | 0,0963 | |

#### Metas de la Fase 1
| Meta | Resultado |
|---|---|
| AP >= 1,5 x prevalencia | Si (1,97 x) |
| ROC-AUC >= 0,65 | Si (0,6660) |
| Sensibilidad >= 0,60 | Si (0,6001) |
| Precision >= 0,20 junto al recall | **No** (0,1781) |

Ningun umbral cumple las dos ultimas a la vez. Se documenta sin alterar el
conjunto de prueba.
        """)

    st.markdown("---")
    st.markdown(
        "**Equipo:** Michel Custodes - Ivan Guette - Maira Torres &nbsp;&nbsp;|&nbsp;&nbsp; "
        "Universidad Popular del Cesar, Ingenieria de Sistemas, 2026\n\n"
        "**Repositorio:** https://github.com/MilsyLu/proyecto-aula-reingresos-ia")
