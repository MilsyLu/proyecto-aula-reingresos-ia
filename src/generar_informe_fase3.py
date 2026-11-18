# -*- coding: utf-8 -*-
"""Genera el informe final de la Fase 3 (.docx) del proyecto de aula."""
import json, re, sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"C:\Users\ASUS\Documents\UPC\proyecto-reingresos")
REP = BASE / "reports"
FIG = REP / "figures"
SALIDA = REP / "Fase_3_Informe_Final_Grupo04.docx"

AZUL = RGBColor(0x1F, 0x3B, 0x63)
GRIS = RGBColor(0x5A, 0x64, 0x72)
NEGRO = RGBColor(0x15, 0x20, 0x2B)
ROJO = RGBColor(0xA8, 0x3A, 0x22)
FUENTE = "Calibri"
CUERPO = 10
URL_APP = "https://reingresos-grupo04.streamlit.app/"
URL_REPO = "https://github.com/MilsyLu/proyecto-aula-reingresos-ia"

doc = Document()

# ------------------------------------------------------------------ estilos
st = doc.styles["Normal"]
st.font.name = FUENTE
st.font.size = Pt(CUERPO)
st.font.color.rgb = NEGRO
st._element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
pf = st.paragraph_format
pf.space_after = Pt(4)
pf.space_before = Pt(0)
pf.line_spacing = 1.0
pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

sec = doc.sections[0]
sec.top_margin = Cm(1.9)
sec.bottom_margin = Cm(1.9)
sec.left_margin = Cm(2.1)
sec.right_margin = Cm(2.1)


def sombrear(celda, color):
    tc = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:fill"), color)
    tc.append(sh)


def fragmentos(parrafo, texto, size=CUERPO, color=None):
    """Interpreta **negrita**, *cursiva* y `monoespaciada`."""
    for pieza in re.split(r"(\*\*.+?\*\*|`.+?`|\*.+?\*)", texto):
        if not pieza:
            continue
        r = parrafo.add_run()
        if pieza.startswith("**"):
            r.text, r.bold = pieza[2:-2], True
        elif pieza.startswith("`"):
            r.text, r.font.name = pieza[1:-1], "Consolas"
            r.font.size = Pt(size - 1.2)
        elif pieza.startswith("*"):
            r.text, r.italic = pieza[1:-1], True
        else:
            r.text = pieza
        if r.font.name != "Consolas":
            r.font.name = FUENTE
        r.font.size = Pt(size) if r.font.name != "Consolas" else r.font.size
        r.font.color.rgb = color or NEGRO
    return parrafo


def h1(texto, numero=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(13)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(f"{numero}. {texto}" if numero else texto)
    r.bold = True
    r.font.name = FUENTE
    r.font.size = Pt(13)
    r.font.color.rgb = AZUL
    return p


def h2(texto):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(texto)
    r.bold = True
    r.font.name = FUENTE
    r.font.size = Pt(10.5)
    r.font.color.rgb = AZUL
    return p


def t(texto, size=CUERPO, color=None, espacio=4, justificar=True):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(espacio)
    p.alignment = (WD_ALIGN_PARAGRAPH.JUSTIFY if justificar
                   else WD_ALIGN_PARAGRAPH.LEFT)
    return fragmentos(p, texto, size, color)


def vinieta(texto, size=CUERPO, nivel=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Cm(0.55 + 0.45 * nivel)
    p.paragraph_format.first_line_indent = Cm(-0.32)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return fragmentos(p, texto, size)


def nota(texto, size=8.2):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.space_before = Pt(1)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return fragmentos(p, texto, size, GRIS)


def tabla(cabecera, filas, anchos=None, size=8.6, titulo=None, alinear_der=None):
    if titulo:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(7)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        fragmentos(p, titulo, 8.6, AZUL)
    tb = doc.add_table(rows=1, cols=len(cabecera))
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    alinear_der = alinear_der or set()
    for i, texto in enumerate(cabecera):
        c = tb.rows[0].cells[i]
        c.text = ""
        pr = c.paragraphs[0]
        pr.paragraph_format.space_after = Pt(1)
        pr.paragraph_format.space_before = Pt(1)
        pr.alignment = (WD_ALIGN_PARAGRAPH.RIGHT if i in alinear_der
                        else WD_ALIGN_PARAGRAPH.LEFT)
        r = pr.add_run(texto)
        r.bold = True
        r.font.size = Pt(size)
        r.font.name = FUENTE
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sombrear(c, "1F3B63")
    for n, fila in enumerate(filas):
        celdas = tb.add_row().cells
        for i, texto in enumerate(fila):
            c = celdas[i]
            c.text = ""
            pr = c.paragraphs[0]
            pr.paragraph_format.space_after = Pt(1)
            pr.paragraph_format.space_before = Pt(1)
            pr.alignment = (WD_ALIGN_PARAGRAPH.RIGHT if i in alinear_der
                            else WD_ALIGN_PARAGRAPH.LEFT)
            fragmentos(pr, str(texto), size)
            if n % 2 == 1:
                sombrear(c, "F3F5F8")
    if anchos:
        for fila in tb.rows:
            for i, a in enumerate(anchos):
                fila.cells[i].width = Cm(a)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return tb


def figura(nombre, ancho, pie):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(FIG / nombre), width=Cm(ancho))
    pp = doc.add_paragraph()
    pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pp.paragraph_format.space_after = Pt(8)
    fragmentos(pp, pie, 8.2, GRIS)


# ============================================================= PORTADA
for _ in range(2):
    doc.add_paragraph().paragraph_format.space_after = Pt(0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(2)
r = p.add_run("UNIVERSIDAD POPULAR DEL CESAR")
r.bold = True
r.font.size = Pt(12)
r.font.name = FUENTE
r.font.color.rgb = AZUL

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(26)
r = p.add_run("Facultad de Ingenieria y Tecnologicas  ·  Ingenieria de Sistemas\n"
              "Inteligencia Artificial  ·  Proyecto de Aula  ·  Grupo 04")
r.font.size = Pt(9.5)
r.font.name = FUENTE
r.font.color.rgb = GRIS

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run("Prediccion del reingreso hospitalario a 30 dias\nen pacientes diabeticos")
r.bold = True
r.font.size = Pt(20)
r.font.name = FUENTE
r.font.color.rgb = NEGRO

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(30)
r = p.add_run("Informe final  ·  Fase 3: modelo, despliegue y evaluacion critica")
r.font.size = Pt(11)
r.font.name = FUENTE
r.font.color.rgb = AZUL

tb = doc.add_table(rows=0, cols=2)
tb.alignment = WD_TABLE_ALIGNMENT.CENTER
for clave, valor in [
    ("Integrantes", "Michel Josefina Custodes Rodriguez\nIvan Guette\nMaira Torres"),
    ("Conjunto de datos", "Diabetes 130-US hospitals for years 1999-2008 (UCI)"),
    ("Aplicacion desplegada", URL_APP),
    ("Repositorio", URL_REPO),
    ("Fecha", "Noviembre de 2026"),
]:
    c = tb.add_row().cells
    c[0].width, c[1].width = Cm(4.0), Cm(11.0)
    pr = c[0].paragraphs[0]
    pr.paragraph_format.space_after = Pt(3)
    r = pr.add_run(clave)
    r.bold = True
    r.font.size = Pt(9.5)
    r.font.name = FUENTE
    r.font.color.rgb = AZUL
    pr = c[1].paragraphs[0]
    pr.paragraph_format.space_after = Pt(3)
    r = pr.add_run(valor)
    r.font.size = Pt(9.5)
    r.font.name = FUENTE
    r.font.color.rgb = NEGRO

doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ============================================================= INDICE
h1("Contenido")
SECCIONES = [
    ("1", "Resumen ejecutivo"),
    ("2", "Planteamiento del problema y objetivos"),
    ("3", "Datos y cohorte de trabajo"),
    ("4", "Metodologia"),
    ("5", "Resultados"),
    ("6", "Analisis critico"),
    ("7", "Discusion etica y de sesgos"),
    ("8", "Despliegue de la solucion"),
    ("9", "Limitaciones"),
    ("10", "Conclusiones"),
    ("11", "Trabajo futuro"),
    ("12", "Referencias"),
    ("", "Anexo A. Tablas completas de la auditoria de equidad"),
]
ARCHIVO_PAG = REP / "paginas_informe_f3.json"
PAGINAS = (json.loads(ARCHIVO_PAG.read_text(encoding="utf-8"))
           if ARCHIVO_PAG.exists() else {})

tb_indice = doc.add_table(rows=0, cols=3)
for num, nombre in SECCIONES:
    c = tb_indice.add_row().cells
    c[0].width, c[1].width, c[2].width = Cm(1.0), Cm(14.0), Cm(1.4)
    for celda, texto, neg, al in [
        (c[0], num, True, WD_ALIGN_PARAGRAPH.LEFT),
        (c[1], nombre, False, WD_ALIGN_PARAGRAPH.LEFT),
        (c[2], str(PAGINAS.get(nombre) or "__"), False, WD_ALIGN_PARAGRAPH.RIGHT),
    ]:
        pr = celda.paragraphs[0]
        pr.paragraph_format.space_after = Pt(3)
        pr.alignment = al
        r = pr.add_run(texto)
        r.bold = neg
        r.font.size = Pt(10)
        r.font.name = FUENTE
        r.font.color.rgb = AZUL if neg else NEGRO

nota("Las figuras y tablas del informe se numeran de forma independiente. El Anexo A "
     "reproduce las tablas de la auditoria de equidad con todas sus columnas.", 9)

h1("El proyecto en cifras")
t("Resumen de una pagina para lectura rapida. Cada dato esta desarrollado en la seccion "
  "que se indica.", 9.2, GRIS)
tabla(
    ["", "Dato", "Seccion"],
    [["**Problema**", "Predecir el reingreso hospitalario antes de 30 dias en pacientes "
      "diabeticos, en el momento del alta", "2"],
     ["**Datos**", "Diabetes 130-US hospitals (UCI), 1999-2008  ·  130 hospitales", "3.1"],
     ["**Cohorte**", "99.343 hospitalizaciones  ·  69.990 pacientes  ·  50 predictores", "3.3"],
     ["**Prevalencia**", "11,39 % de las hospitalizaciones terminan en reingreso", "3.3"],
     ["**Particion**", "60 / 20 / 20 **por paciente**, con `StratifiedGroupKFold`", "4.1"],
     ["**Modelo final**", "`HistGradientBoostingClassifier`, elegido entre 30 configuraciones",
      "4.3 - 4.4"],
     ["**Umbral**", "0,1123, fijado en validacion para alcanzar sensibilidad 0,60", "4.5"],
     ["**AP en prueba**", "**0,2249**  (IC 95 %: 0,2047 - 0,2467)  =  1,97 x la prevalencia", "5.2"],
     ["**ROC-AUC**", "0,6660  (IC 95 %: 0,6527 - 0,6786)", "5.2"],
     ["**Sensibilidad**", "0,6001 - detecta 6 de cada 10 reingresos reales", "5.2"],
     ["**Precision**", "0,1781 - acierta 1 de cada 5,6 alertas", "5.2"],
     ["**Calibracion**", "Brier 0,0963; desvio maximo de 0,0089 entre lo predicho y lo observado",
      "5.3"],
     ["**Metas de la Fase 1**", "3 de 4 cumplidas; la de precision no se alcanza en "
      "ningun umbral", "5.4"],
     ["**Hallazgo critico 1**", "Dos variables administrativas concentran el **43,5 %** del "
      "desempeno", "6.1"],
     ["**Hallazgo critico 2**", "La sensibilidad cae de 0,88 (transferidos) a **0,48** "
      "(alta a casa, 79 % de los casos)", "6.2"],
     ["**Hallazgo critico 3**", "Razon de paridad por edad de **0,569**, sin diferencia de "
      "riesgo real que la justifique", "7.4"],
     ["**Veredicto**", "Viabilidad tecnica demostrada; **uso clinico no recomendado** en el "
      "estado actual", "10"]],
    anchos=[3.1, 11.1, 1.4], size=8.4, alinear_der={2})

doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

# ============================================================= 1 RESUMEN
h1("Resumen ejecutivo", 1)
t("Entre el 15 y el 20 % de los pacientes dados de alta de un hospital vuelven a ser "
  "ingresados antes de 30 dias, y buena parte de esos reingresos se considera evitable. "
  "Este proyecto construyo y desplego un modelo de aprendizaje automatico que estima, al "
  "momento del alta, la probabilidad de que un paciente diabetico vuelva a ser hospitalizado "
  "dentro de ese plazo, con el fin de priorizar a quienes mas se beneficiarian de un "
  "seguimiento reforzado.")
t("Se trabajo con **99.343 hospitalizaciones de 69.990 pacientes** del conjunto publico "
  "*Diabetes 130-US hospitals for years 1999-2008*. El 11,39 % de esas hospitalizaciones "
  "terminaron en reingreso antes de 30 dias. Los datos se dividieron **por paciente** "
  "(60 / 20 / 20) para que ninguna persona apareciera a la vez en entrenamiento y en "
  "evaluacion, y todas las transformaciones se ajustaron unicamente con el conjunto de "
  "entrenamiento.")
t("El modelo final es un **Gradient Boosting** (`HistGradientBoostingClassifier`) con 50 "
  "predictores e hiperparametros elegidos entre 30 combinaciones por busqueda aleatoria. "
  "Sobre el conjunto de prueba, que nunca se uso para tomar decisiones, obtuvo un "
  "**Average Precision de 0,2249** (IC 95 %: 0,2047-0,2467), **1,97 veces** la prevalencia "
  "base, y un **ROC-AUC de 0,6660**. Con el umbral de decision fijado en validacion "
  "(0,1123), el modelo **detecta 6 de cada 10 reingresos** reales, al costo de que **solo 1 "
  "de cada 6 alertas** corresponde a un reingreso verdadero.")
t("De las cuatro metas que el grupo se fijo en la Fase 1, **se cumplieron tres**: AP por "
  "encima de 1,5 veces la prevalencia, ROC-AUC de al menos 0,65 y sensibilidad de al menos "
  "0,60. **La cuarta no se cumplio**: no existe ningun umbral que alcance simultaneamente "
  "una sensibilidad de 0,60 y una precision de 0,20. Se documenta como resultado negativo y "
  "no se ajusto el criterio para aparentar exito.")
t("La auditoria critica revelo dos hallazgos que condicionan cualquier uso del modelo. "
  "Primero, **dos variables administrativas concentran el 43,5 % del desempeno**: el numero "
  "de hospitalizaciones previas y el tipo de egreso. Segundo, al separar la prueba segun el "
  "tipo de egreso, la sensibilidad se descompone en **0,8822 para pacientes transferidos a "
  "otra institucion** frente a **0,4834 para quienes se van a casa**, que son el 79 % de la "
  "cohorte y justamente el grupo al que iria dirigido el programa de seguimiento. En el "
  "frente de equidad, la razon de paridad por edad es de **0,569**: el modelo alerta sobre "
  "el 51,3 % de los pacientes de 80 anos o mas y sobre el 30,2 % de los menores de 50, "
  "aunque la prevalencia real de reingreso es practicamente igual en ambos grupos.")
t("La solucion se entrego como una **aplicacion web publica** y un **tablero local**, "
  "ambos acompanados de la ficha del modelo y de sus condiciones de uso. El veredicto del "
  "grupo es que el prototipo **demuestra la viabilidad tecnica del enfoque pero no esta en "
  "condiciones de orientar decisiones clinicas**, y el informe explica con detalle por que.")

# ============================================================= 2 PROBLEMA
h1("Planteamiento del problema y objetivos", 2)
h2("2.1  El problema")
t("Un reingreso hospitalario temprano es un evento costoso y, con frecuencia, evitable. "
  "Cuando un paciente vuelve a ser hospitalizado pocos dias despues del alta, lo habitual "
  "es que el problema no fuera la atencion recibida durante el ingreso sino lo que ocurrio "
  "despues: una indicacion mal comprendida, un medicamento que no se consiguio, una cita de "
  "control que no se dio o un entorno sin soporte. Los sistemas de salud responden con "
  "programas de seguimiento posterior al alta -llamadas, visitas domiciliarias, citas "
  "tempranas-, pero esos programas son caros y no alcanzan para todos los pacientes.")
t("De ahi la pregunta operativa del proyecto: **si solo se puede hacer seguimiento reforzado "
  "a una fraccion de los pacientes que se van de alta, a cuales conviene elegir.** El "
  "modelo no pretende decidir nada; pretende ordenar la lista.")
t("La poblacion diabetica es un buen punto de partida porque concentra multiples "
  "comorbilidades, regimenes de medicacion complejos y una tasa de reingreso superior a la "
  "media hospitalaria.")

h2("2.2  Objetivo general")
t("Construir, evaluar de forma honesta y desplegar un modelo de clasificacion que estime la "
  "probabilidad de reingreso hospitalario antes de 30 dias en pacientes diabeticos, a partir "
  "de informacion disponible en el momento del alta.")

h2("2.3  Metas cuantitativas fijadas en la Fase 1")
t("El grupo definio cuatro metas **antes** de entrenar ningun modelo, para no elegir el "
  "criterio de exito despues de ver los resultados. Se reproducen aqui porque la seccion 5 "
  "las evalua una por una.")
tabla(
    ["#", "Meta", "Justificacion"],
    [["1", "AP >= 1,5 x prevalencia (0,1708)",
      "El modelo debe superar claramente al azar en la metrica adecuada para clases desbalanceadas."],
     ["2", "ROC-AUC >= 0,65",
      "Umbral habitual en la literatura de reingresos para considerar util un modelo."],
     ["3", "Sensibilidad >= 0,60",
      "Dejar pasar un reingreso cuesta mas que una llamada de mas; se prioriza detectar."],
     ["4", "Precision >= 0,20 junto al recall",
      "Para que el programa de seguimiento sea sostenible, 1 de cada 5 alertas deberia acertar."]],
    anchos=[0.9, 4.6, 10.9])

# ============================================================= 3 DATOS
h1("Datos y cohorte de trabajo", 3)
h2("3.1  Origen")
t("Se utilizo el conjunto **Diabetes 130-US hospitals for years 1999-2008**, publicado en el "
  "repositorio de aprendizaje automatico de la Universidad de California en Irvine y "
  "descrito por Strack *et al.* (2014). Reune **101.766 hospitalizaciones** de **71.518 "
  "pacientes** distintos, atendidos en 130 hospitales de Estados Unidos, con 50 columnas por "
  "registro: datos demograficos, tipo y origen del ingreso, tipo de egreso, diagnosticos "
  "codificados en CIE-9, numero de procedimientos y examenes, 23 medicamentos antidiabeticos "
  "y el uso de servicios en el ano previo.")
t("Cada fila es una **hospitalizacion**, no un paciente. Un mismo paciente puede aparecer "
  "varias veces, y de hecho **16.341 pacientes de la cohorte final tienen mas de una "
  "hospitalizacion registrada**. Este detalle, que parece menor, determina por completo la "
  "forma correcta de partir los datos (seccion 4.1).")

h2("3.2  Variable objetivo")
t("La columna `readmitted` trae tres valores: `<30` (reingreso antes de 30 dias), `>30` "
  "(reingreso posterior) y `NO`. El problema se planteo como **clasificacion binaria**: "
  "la clase positiva es unicamente `<30`. Los reingresos posteriores a 30 dias se agruparon "
  "con los no reingresos porque quedan fuera de la ventana en la que un programa de "
  "seguimiento al alta puede actuar.")

h2("3.3  Cohorte de trabajo")
t("Se excluyeron las hospitalizaciones cuyo egreso hace imposible el reingreso o lo vuelve "
  "clinicamente irrelevante: pacientes **fallecidos** y pacientes derivados a **cuidado "
  "paliativo** (codigos de egreso 11, 13, 14, 19, 20 y 21). Son 2.423 registros. Mantenerlos "
  "habria inflado artificialmente el desempeno, porque el modelo habria aprendido a "
  "predecir 'no reingresa' en casos donde el reingreso era imposible por definicion.")
tabla(
    ["Concepto", "Hospitalizaciones", "Pacientes"],
    [["Base original", "101.766", "71.518"],
     ["Menos fallecidos y cuidado paliativo", "-2.423", "-1.528"],
     ["**Cohorte de trabajo**", "**99.343**", "**69.990**"],
     ["De ellas, reingresos antes de 30 dias", "11.314  (11,39 %)", "-"]],
    anchos=[8.0, 4.5, 3.9], alinear_der={1, 2})
nota("La prevalencia del 11,39 % es la cifra de referencia de todo el informe: un modelo que "
     "siempre dijera 'no reingresa' acertaria el 88,61 % de las veces sin servir para nada. "
     "Por eso la exactitud no se uso como metrica de decision.")

# ============================================================= 4 METODOLOGIA
h1("Metodologia", 4)
h2("4.1  Particion por paciente")
t("El error mas facil de cometer con estos datos es partirlos al azar por filas. Si dos "
  "hospitalizaciones del mismo paciente caen una en entrenamiento y otra en prueba, el "
  "modelo puede reconocer a la persona en lugar de aprender el fenomeno, y el desempeno "
  "medido resulta optimista.")
t("Se uso `StratifiedGroupKFold` de scikit-learn, que agrupa por `patient_nbr` -el "
  "identificador anonimo del paciente- y simultaneamente conserva la proporcion de "
  "reingresos en cada parte. El resultado es una particion **60 / 20 / 20** en la que "
  "**ningun paciente aparece en dos conjuntos** y la prevalencia es practicamente identica "
  "en los tres.")
tabla(
    ["Conjunto", "Hospitalizaciones", "Pacientes", "Prevalencia", "Para que se uso"],
    [["Entrenamiento", "59.605", "41.988", "11,390 %", "Ajustar el modelo"],
     ["Validacion", "19.868", "13.982", "11,385 %", "Comparar modelos y fijar el umbral"],
     ["Prueba", "19.870", "14.020", "11,389 %", "Medir una sola vez, al final"]],
    anchos=[2.9, 3.0, 2.3, 2.3, 5.9], alinear_der={1, 2, 3})
t("La distincion entre validacion y prueba es deliberada. **Validacion es el conjunto con "
  "el que se toman decisiones** -que modelo, que hiperparametros, que umbral- y por eso se "
  "contamina: se mira muchas veces. **Prueba es el conjunto que se mira una sola vez**, "
  "cuando ya no queda nada por decidir. Si se usara la prueba para elegir, dejaria de ser "
  "una estimacion honesta de lo que pasara con pacientes nuevos.")

h2("4.2  Preprocesamiento sin fuga de informacion")
t("De las 50 columnas originales, 12 no se usaron como predictores:")
vinieta("**3 no son informacion del paciente**: `encounter_id` y `patient_nbr` son "
        "identificadores, y `readmitted` es la variable objetivo.")
vinieta("**4 se reemplazaron por versiones derivadas**: `age` venia en rangos de texto y se "
        "convirtio en `edad_num` (el punto medio de cada rango); los tres diagnosticos CIE-9 "
        "`diag_1`, `diag_2` y `diag_3` tenian mas de 700 codigos distintos cada uno y se "
        "agruparon en 9 familias clinicas (circulatorio, respiratorio, digestivo, diabetes, "
        "lesiones, musculoesqueletico, genitourinario, neoplasias y otros).")
vinieta("**5 se retiraron**: `weight` esta vacia en el 96,9 % de los registros; `payer_code` "
        "esta vacia en el 39,6 % y describe al asegurador, no al paciente; `examide` y "
        "`citoglipton` tienen un unico valor en toda la base, de modo que no aportan "
        "informacion; y `race` se aparto deliberadamente del modelo para **reservarla como "
        "atributo de auditoria** (seccion 7).")
t("A cambio se construyeron **12 variables derivadas** que condensan informacion dispersa: "
  "`servicios_previos` (suma de ingresos, urgencias y consultas del ano anterior), "
  "`tuvo_ingreso_previo`, `meds_por_dia`, `labs_por_dia`, `num_meds_activos`, "
  "`hubo_cambio_med`, `a1c_medida`, `glu_medida`, ademas de `edad_num` y los tres "
  "`grupo_diag`. El conjunto final de predictores quedo en **50 variables: 17 numericas y "
  "33 categoricas**.")
t("Todas las transformaciones se encapsularon en un `Pipeline` con `ColumnTransformer` y "
  "**se ajustaron unicamente sobre el conjunto de entrenamiento**. Esto es lo que evita la "
  "fuga de informacion: la mediana que rellena los faltantes, el promedio que estandariza y "
  "la lista de categorias conocidas salen solo del entrenamiento; a validacion y prueba se "
  "les aplican esos mismos valores ya calculados.")
tabla(
    ["Paso", "Para modelos lineales", "Para modelos de arboles"],
    [["Faltantes numericos", "Mediana del entrenamiento", "Se dejan; el algoritmo los maneja"],
     ["Faltantes categoricos", "Categoria 'Ausente'", "Categoria 'Ausente'"],
     ["Escala", "Estandarizacion (media 0, desv. 1)", "No se requiere"],
     ["Codificacion", "One-Hot con `min_frequency=20`", "Ordinal + soporte nativo"],
     ["Columnas resultantes", "200", "50"]],
    anchos=[3.4, 6.5, 6.5])
nota("`min_frequency=20` agrupa en 'infrecuente' toda categoria con menos de 20 apariciones "
     "en entrenamiento. Sin ese limite, codigos raros de diagnostico o especialidad habrian "
     "generado cientos de columnas casi vacias.")

h2("4.3  Modelos evaluados")
t("Se siguio una escalera de complejidad creciente, de modo que cada modelo tuviera que "
  "justificar su costo frente al anterior:")
vinieta("**Clasificador mayoritario**: siempre responde 'no reingresa'. Es el piso absoluto; "
        "sirve para mostrar que la exactitud del 88,6 % no significa nada.")
vinieta("**Regresion logistica** (con y sin `class_weight='balanced'`): modelo lineal, "
        "interpretable, rapido. Es la referencia real contra la que se mide la ganancia.")
vinieta("**Gradient Boosting** (`HistGradientBoostingClassifier`), por defecto y ajustado. "
        "Se escogio la variante basada en histogramas por ser unas nueve veces mas rapida "
        "que `GradientBoostingClassifier` sobre este volumen de datos, manejar valores "
        "faltantes de forma nativa y admitir variables categoricas sin expandirlas.")

h2("4.4  Ajuste de hiperparametros")
t("Se exploraron **30 combinaciones** con `RandomizedSearchCV`, optimizando **Average "
  "Precision** y validando con `StratifiedGroupKFold` de 5 particiones **dentro del "
  "conjunto de entrenamiento**, de modo que la validacion externa siguiera intacta. La "
  "semilla se fijo en 42 para que el resultado sea reproducible.")
tabla(
    ["Hiperparametro", "Valor elegido", "Que controla"],
    [["`learning_rate`", "0,05", "Cuanto corrige cada arbol nuevo"],
     ["`max_leaf_nodes`", "15", "Profundidad efectiva de cada arbol"],
     ["`min_samples_leaf`", "100", "Minimo de casos por hoja; evita memorizar"],
     ["`l2_regularization`", "0,5", "Penalizacion que suaviza las predicciones"],
     ["`max_features`", "0,8", "Fraccion de variables que ve cada arbol"],
     ["`class_weight`", "None", "No se reponderaron las clases"]],
    anchos=[4.2, 3.0, 9.2])
t("El ultimo renglon merece explicacion. Reponderar la clase minoritaria es la respuesta "
  "automatica ante el desbalance, pero la busqueda la descarto: **mover el umbral de "
  "decision resulto mas eficaz que reponderar**, y ademas deja las probabilidades mejor "
  "calibradas. El desbalance se trato, pero se trato en el umbral, no en el entrenamiento.")
figura("03_sobreajuste.png", 12.5,
       "Figura 1. Las 30 configuraciones probadas. En el eje horizontal, cuanto memoriza cada "
       "una (AP de entrenamiento menos AP de validacion cruzada); en el vertical, cuanto "
       "rinde con datos nuevos.")
t("La figura 1 deja ver algo que vale la pena subrayar: **las configuraciones que mas "
  "memorizan no son las que mejor rinden**. Las que se situan a la derecha, con diferencias "
  "de hasta 0,24 entre entrenamiento y validacion, obtienen resultados peores que las de la "
  "izquierda. La configuracion ganadora es de las mas sobrias -arboles de 15 hojas con "
  "minimo 100 casos por hoja- y su sobreajuste es de apenas 0,05. Todas las combinaciones "
  "probadas superan a la regresion logistica, pero ninguna por mucho.")

h2("4.5  Eleccion del umbral de decision")
t("Un clasificador no devuelve 'si' o 'no', devuelve una probabilidad. Convertirla en una "
  "alerta exige fijar un corte, y ese corte **no es una decision estadistica sino una "
  "decision de politica**: define cuantos reingresos se detectan y cuantas llamadas inutiles "
  "se hacen.")
t("Siguiendo la prioridad declarada en la Fase 1 -detectar pesa mas que acertar-, el umbral "
  "se fijo en el valor que alcanza **sensibilidad 0,60 en validacion**, lo que dio "
  "**0,112346**. Se fijo en validacion y se aplico sin modificar a la prueba.")

# ============================================================= 5 RESULTADOS
h1("Resultados", 5)
h2("5.1  Comparacion de modelos (conjunto de validacion)")
tabla(
    ["Modelo", "AP", "ROC-AUC", "AP / prevalencia", "Mejora vs. logistica"],
    [["Mayoritario", "0,1139", "0,500", "1,00 x", "-46,7 %"],
     ["Regresion logistica", "0,2136", "0,654", "1,88 x", "referencia"],
     ["Gradient Boosting por defecto", "0,2192", "0,662", "1,93 x", "+2,6 %"],
     ["**Gradient Boosting ajustado**", "**0,2238**", "**0,666**", "**1,97 x**", "**+4,8 %**"]],
    anchos=[5.6, 2.3, 2.3, 3.0, 3.2], alinear_der={1, 2, 3, 4})
t("La lectura honesta de esta tabla es que **el salto grande no lo da el modelo sofisticado "
  "sino tener un modelo**: pasar del mayoritario a una regresion logistica casi duplica el "
  "AP. El Gradient Boosting ajustado anade un 4,8 % sobre la logistica, una ganancia real "
  "pero modesta, coherente con lo que reporta la literatura para este conjunto de datos.")
figura("02_curvas_baseline.png", 13.5,
       "Figura 2. Curvas ROC y precision-recall de los modelos de referencia en validacion. "
       "La linea horizontal de la curva PR marca la prevalencia (0,1139), que es el nivel del azar.")

h2("5.2  Desempeno final en el conjunto de prueba")
t("El modelo elegido se evaluo **una sola vez** sobre la prueba, con el umbral ya fijado. "
  "Los intervalos de confianza del 95 % se obtuvieron por bootstrap de 500 remuestreos "
  "**sobre pacientes completos**, no sobre filas, para no romper el agrupamiento.")
tabla(
    ["Metrica", "Validacion", "Prueba", "IC 95 % (prueba)", "Lectura"],
    [["Average Precision", "0,2238", "**0,2249**", "0,2047 - 0,2467", "1,97 veces el azar"],
     ["ROC-AUC", "0,6660", "**0,6660**", "0,6527 - 0,6786", "Discriminacion moderada"],
     ["Sensibilidad (recall)", "0,5999", "**0,6001**", "0,5766 - 0,6202", "Detecta 6 de cada 10"],
     ["Precision", "0,1771", "**0,1781**", "-", "Acierta 1 de cada 5,6 alertas"],
     ["Brier", "0,0963", "**0,0963**", "-", "Probabilidades bien calibradas"],
     ["Exactitud", "0,6371", "0,6391", "-", "Irrelevante: el trivial logra 0,8861"]],
    anchos=[3.8, 2.4, 2.4, 3.2, 4.6], alinear_der={1, 2, 3})
t("El dato mas tranquilizador de esta tabla no es ninguna de las cifras en si, sino **su "
  "coincidencia con validacion**. Que el AP de prueba (0,2249) sea practicamente igual al de "
  "validacion (0,2238) indica que no hubo sobreajuste ni fuga de informacion: el modelo "
  "rinde con datos nuevos lo mismo que rendia con los datos que ya conocia.")
tabla(
    ["Matriz de confusion (prueba, umbral 0,1123)", "El modelo alerta", "El modelo no alerta"],
    [["**Reingreso real: SI** (2.263 casos)", "1.358  (detectados)", "905  (se escapan)"],
     ["**Reingreso real: NO** (17.607 casos)", "6.266  (falsa alarma)", "11.341  (correctos)"]],
    anchos=[7.0, 4.3, 4.3], alinear_der={1, 2})
t("En terminos operativos: de cada 100 pacientes dados de alta, el modelo marcaria a 38; "
  "entre esos 38 estarian 7 de los 11 que efectivamente van a reingresar, y 31 personas que "
  "no lo haran recibirian una llamada que no necesitaban. Si una llamada de seguimiento "
  "cuesta mucho menos que un reingreso evitado -que es la hipotesis del programa-, el "
  "balance puede ser favorable; si no, no lo es. **El modelo no puede responder esa "
  "pregunta: la responde la institucion.**")
figura("04_prueba_final.png", 13.5,
       "Figura 3. Desempeno del modelo final sobre el conjunto de prueba.")

h2("5.3  Calibracion")
t("Discriminar y calibrar son cosas distintas. Un modelo **discrimina** bien si ordena "
  "correctamente a los pacientes de mayor a menor riesgo; **calibra** bien si, cuando dice "
  "'12 %', aproximadamente el 12 % de esos pacientes reingresa. Para un tablero clinico la "
  "calibracion importa tanto como el orden, porque el numero se le muestra a una persona.")
t("El puntaje de Brier es 0,0963. Al agrupar la prueba en diez grupos de riesgo creciente, "
  "la mayor diferencia entre probabilidad predicha y frecuencia observada es de **0,0089**, "
  "es decir menos de un punto porcentual.")
tabla(
    ["Grupo de riesgo", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    [["Probabilidad predicha", "4,2 %", "5,6 %", "6,7 %", "7,7 %", "8,9 %", "10,3 %",
      "11,8 %", "13,9 %", "17,3 %", "27,0 %"],
     ["Reingresos observados", "4,6 %", "5,9 %", "6,6 %", "7,7 %", "9,6 %", "9,8 %",
      "12,2 %", "13,0 %", "17,1 %", "27,4 %"]],
    anchos=[3.5, 1.27, 1.27, 1.27, 1.27, 1.27, 1.27, 1.27, 1.27, 1.27, 1.27],
    size=8.0, alinear_der=set(range(1, 11)))
nota("Las dos filas se siguen de cerca en todo el rango. La probabilidad que muestra la "
     "aplicacion puede leerse literalmente.")
figura("04_calibracion.png", 12.0,
       "Figura 4. Curva de calibracion sobre el conjunto de prueba. Cuanto mas cerca esten "
       "los puntos de la diagonal, mas fiel es la probabilidad que anuncia el modelo.")
t("Esta es, en opinion del grupo, la propiedad mas solida del modelo y conviene no "
  "perderla de vista: **el modelo discrimina de forma modesta pero estima bien**. "
  "Distinguir quien reingresara le cuesta, pero cuando afirma que un paciente tiene un "
  "17 % de riesgo, ese numero es confiable. Para un tablero que un profesional va a leer, "
  "esa honestidad en la escala es una virtud y no un detalle tecnico.")

h2("5.4  Cumplimiento de las metas de la Fase 1")
tabla(
    ["Meta", "Objetivo", "Obtenido", "Cumple"],
    [["AP >= 1,5 x prevalencia", "0,1708", "0,2249", "**SI**"],
     ["ROC-AUC >= 0,65", "0,650", "0,666", "**SI**"],
     ["Sensibilidad >= 0,60", "0,600", "0,6001", "**SI**"],
     ["Precision >= 0,20 junto al recall", "0,200", "0,1781", "**NO**"]],
    anchos=[7.0, 2.6, 2.6, 3.4], alinear_der={1, 2, 3})
t("La cuarta meta exige leerse con cuidado, porque **no es que el modelo quedara cerca: es "
  "que la combinacion pedida no existe en ningun umbral**. Al recorrer todos los cortes "
  "posibles se observa que:")
vinieta("Si se exige **sensibilidad 0,60**, la precision maxima alcanzable es **0,177**.")
vinieta("Si se exige **precision 0,20**, la sensibilidad maxima alcanzable es **0,481**.")
t("Se decidio **documentar el incumplimiento en lugar de relajar la meta**. Bajar el listado "
  "a posteriori para que el proyecto 'cumpla' habria vaciado de sentido el ejercicio de "
  "haber fijado criterios antes de entrenar.")

h2("5.5  El intercambio entre detectar y acertar")
t("Conviene mostrar por que la cuarta meta es inalcanzable, porque el motivo no es un "
  "defecto del modelo sino la forma misma del problema. La tabla recorre todos los umbrales "
  "evaluados en validacion: a medida que el corte sube, el modelo alerta sobre menos "
  "pacientes, acierta mas en cada alerta y, al mismo tiempo, deja escapar mas reingresos.")
tabla(
    ["Umbral", "Alertas", "% de la poblacion", "Sensibilidad", "Precision", "Detectados",
     "Se escapan"],
    [["0,06", "16.213", "81,6 %", "0,916", "0,128", "2.072", "190"],
     ["0,08", "12.336", "62,1 %", "0,793", "0,145", "1.794", "468"],
     ["0,10", "9.370", "47,2 %", "0,676", "0,163", "1.529", "733"],
     ["**0,1123**", "**7.669**", "**38,6 %**", "**0,600**", "**0,177**", "**1.358**", "**904**"],
     ["0,14", "4.853", "24,4 %", "0,446", "0,208", "1.009", "1.253"],
     ["0,16", "3.540", "17,8 %", "0,359", "0,229", "812", "1.450"],
     ["0,20", "1.845", "9,3 %", "0,227", "0,279", "514", "1.748"],
     ["0,30", "536", "2,7 %", "0,089", "0,377", "202", "2.060"]],
    anchos=[2.0, 2.0, 2.6, 2.4, 2.1, 2.3, 2.2], size=8.4,
    alinear_der={1, 2, 3, 4, 5, 6})
t("La precision no cruza 0,20 hasta el umbral 0,14, y en ese punto la sensibilidad ya cayo "
  "a 0,446. **Las dos metas se cruzan en sentidos opuestos y no hay ningun punto donde "
  "ambas se cumplan.** El grupo eligio el renglon resaltado por la prioridad declarada en "
  "la Fase 1: dejar pasar un reingreso se considero mas costoso que hacer una llamada de "
  "mas.")
t("La tabla tambien sirve como herramienta de decision para una institucion. Un hospital "
  "con capacidad para seguir al 25 % de sus altas tendria que situarse en el umbral 0,14 y "
  "aceptar que detectara 4 de cada 10 reingresos; uno con capacidad para el 60 % podria "
  "bajar a 0,08 y detectar 8 de cada 10. **La aplicacion desplegada incorpora este control "
  "de forma interactiva** precisamente para que esa conversacion pueda tenerse con numeros "
  "a la vista.")

# ============================================================= 6 ANALISIS CRITICO
h1("Analisis critico", 6)
h2("6.1  Que mira realmente el modelo")
t("Para entender de donde sale el desempeno se midio la **importancia por permutacion** "
  "sobre el conjunto de prueba: se desordena una variable al azar, se vuelve a predecir y "
  "se observa cuanto cae el AP. Si la caida es grande, el modelo dependia de esa variable.")
figura("05_importancia.png", 14.5,
       "Figura 5. Importancia por permutacion, 15 variables principales de 50 "
       "(prueba, 5 repeticiones). La barra mide la caida del AP como porcentaje del AP total.")
t("El resultado es nitido y algo incomodo. **Dos variables concentran el 43,5 % del "
  "desempeno**:")
vinieta("`number_inpatient`, el numero de hospitalizaciones del paciente en el ano previo, "
        "aporta el **25,1 %**. Es un hallazgo esperable y clinicamente sensato: quien ya "
        "ingreso varias veces vuelve a ingresar.")
vinieta("`discharge_disposition_id`, el tipo de egreso, aporta el **18,4 %**. Esta variable "
        "**no describe al paciente sino a donde se le envia**, y es la raiz del problema "
        "que documenta la seccion 6.2.")
t("Las otras 48 variables se reparten el 56,5 % restante en porciones pequenas, y **21 de "
  "ellas no aportan nada o empeoran levemente el modelo** al permutarlas. Entre las que si "
  "aportan algo aparecen la especialidad que atiende, los grupos de diagnostico y la "
  "variable derivada `servicios_previos`, lo que confirma que el trabajo de ingenieria de "
  "caracteristicas sirvio, aunque de forma marginal.")
t("La conclusion critica es que **el modelo se apoya mucho mas en el historial "
  "administrativo del paciente que en su estado clinico actual**. Los 23 medicamentos "
  "antidiabeticos, el resultado de HbA1c y el numero de procedimientos -justamente la "
  "informacion clinica rica que hacia atractivo este conjunto de datos- pesan muy poco.")

h2("6.2  La dependencia del tipo de egreso")
t("El peso de `discharge_disposition_id` llevo a un analisis de sensibilidad: se partio el "
  "conjunto de prueba segun si el paciente fue **transferido a otra institucion** (codigos "
  "2, 3, 4, 5, 10, 16, 22, 23, 24, 27, 28, 29 y 30 del mapa oficial) o fue **dado de alta a "
  "su domicilio**, y se recalcularon las metricas por separado.")
tabla(
    ["Escenario", "n", "Prevalencia", "AP", "ROC-AUC", "Sensibilidad", "Tasa de alerta"],
    [["Prueba completa", "19.870", "11,39 %", "0,2249", "0,6660", "0,6001", "38,4 %"],
     ["Solo transferidos", "4.144", "15,97 %", "0,2541", "0,6330", "**0,8822**", "77,7 %"],
     ["Dados de alta a casa", "15.726", "10,18 %", "0,2098", "0,6587", "**0,4834**", "28,0 %"]],
    anchos=[4.2, 1.9, 2.1, 1.8, 1.9, 2.2, 2.3], alinear_der={1, 2, 3, 4, 5, 6})
t("La sensibilidad global de 0,6001 **es un promedio que oculta dos comportamientos muy "
  "distintos**. Entre los pacientes transferidos a otra institucion el modelo detecta casi "
  "9 de cada 10 reingresos, pero entre quienes se van a casa detecta menos de 5 de cada 10. "
  "Y los que se van a casa son el **79 % de la cohorte**.")
t("La explicacion es que una transferencia entre instituciones es, en si misma, una senal "
  "casi definitiva de fragilidad: el paciente no esta en condiciones de irse a su casa. El "
  "modelo aprendio a reconocer esa senal, que es facil, y eso le subio el promedio. **Pero "
  "el programa de seguimiento al alta esta pensado precisamente para el paciente que se va "
  "a su casa**, que es el caso en el que el modelo rinde peor.")
figura("05_sensibilidad.png", 13.0,
       "Figura 6. Desempeno segun el tipo de egreso. La cifra global es un promedio entre "
       "dos poblaciones que el modelo trata de forma muy distinta.")
t("Este hallazgo no invalida el modelo, pero **cambia la cifra que habria que reportar a una "
  "institucion**. La sensibilidad util para el caso de uso real no es 0,60 sino **0,48**.")

h2("6.3  El techo del conjunto de datos")
t("Un ROC-AUC de 0,666 es modesto en terminos absolutos, y conviene preguntarse si el "
  "problema es el modelo o los datos. La evidencia apunta a los datos:")
vinieta("La regresion logistica alcanza 0,654 y el Gradient Boosting ajustado 0,666. "
        "**Un salto de arquitectura produce una ganancia de 1,8 %**, lo que sugiere que la "
        "senal disponible esta practicamente agotada, no mal explotada.")
vinieta("Los trabajos publicados sobre este mismo conjunto reportan valores en el rango "
        "0,64-0,70. El resultado obtenido esta dentro de ese rango.")
vinieta("Las variables que mas determinan un reingreso real -soporte familiar, acceso "
        "efectivo a la medicacion, adherencia al tratamiento, existencia de una cita de "
        "control- **simplemente no estan en la base**.")
t("Como contraste, el grupo evaluo un segundo conjunto de datos (CMS DE-SynPUF, reclamaciones "
  "sinteticas de Medicare 2008-2010) para verificar si el techo era propio de esta base. "
  "Los resultados fueron equivalentes o inferiores (AP 0,1664 y ROC-AUC 0,6607 con "
  "regresion logistica), por lo que **se decidio no cambiar de conjunto de datos a mitad "
  "del proyecto**: el techo no era una peculiaridad de la base elegida.")

# ============================================================= 7 ETICA
h1("Discusion etica y de sesgos", 7)
t("Un modelo que ordena pacientes para recibir un recurso escaso **redistribuye atencion**. "
  "Si se equivoca sistematicamente en contra de un grupo, ese grupo recibe menos cuidado. "
  "Por eso la auditoria de equidad no se trato como un anexo sino como parte del criterio de "
  "aceptacion.")

h2("7.1  Como se midio")
t("Se evaluaron dos criterios complementarios sobre el conjunto de prueba, con el umbral "
  "definitivo:")
vinieta("**Paridad demografica**: comparar la *tasa de alerta* entre grupos. Se reporta la "
        "**razon de paridad** (tasa menor / tasa mayor) y se usa como referencia la **regla "
        "de los cuatro quintos**: por debajo de 0,80 hay indicio de trato desigual.")
vinieta("**Igualdad de oportunidad**: comparar la *sensibilidad* entre grupos. Responde a "
        "la pregunta que de verdad importa: entre los pacientes que si van a reingresar, "
        "¿el modelo detecta a unos mas que a otros?")
t("Se fijo ademas una regla de prudencia estadistica: **no se interpreta ningun subgrupo con "
  "menos de 50 casos o menos de 10 reingresos**, para no leer ruido como sesgo.")
t("`race` se excluyo del modelo pero se conservo para auditar. Conviene decirlo con "
  "claridad: **excluir una variable sensible no elimina el sesgo**, porque otras variables "
  "la representan indirectamente. Solo impide usarla de forma explicita y permite medir el "
  "sesgo que de todos modos queda.")

h2("7.2  Resultados por subgrupo")
tabla(
    ["Atributo", "Grupos", "Razon de paridad", "Brecha de sensibilidad", "Veredicto"],
    [["Genero", "2", "0,905", "0,055", "Dentro de lo aceptable"],
     ["Grupo racial", "6", "0,786", "0,169", "Requiere matiz (7.3)"],
     ["Edad", "5", "**0,569**", "0,108", "**Disparidad relevante**"]],
    anchos=[3.0, 1.6, 3.0, 3.6, 4.4], alinear_der={1, 2, 3})

h2("7.3  Genero y grupo racial")
t("Por **genero** no se observan diferencias preocupantes: el modelo alerta sobre el 40,1 % "
  "de las mujeres y el 36,3 % de los hombres, con sensibilidades de 0,625 y 0,570. La razon "
  "de paridad de 0,905 supera comodamente el umbral de 0,80.")
t("Por **grupo racial** la razon de paridad global es **0,786**, apenas por debajo del "
  "umbral, y aqui la lectura literal seria enganosa. La razon baja la produce el grupo "
  "`Asian`, que tiene solo **143 casos** en la prueba. Si se comparan los dos grupos con "
  "tamano suficiente para una conclusion solida -`Caucasian` con 14.717 casos y "
  "`AfricanAmerican` con 3.782- las tasas de alerta son **38,6 % y 39,1 %**, una razon de "
  "paridad de **0,987**, es decir practicamente iguales.")
t("La formulacion honesta es entonces: **entre los dos grupos grandes el modelo trata por "
  "igual; sobre los grupos pequenos no hay datos suficientes para afirmar nada.** No es lo "
  "mismo decir 'no hay sesgo' que decir 'no hay datos para medirlo', y el proyecto se "
  "cuida de no confundir ambas cosas.")

h2("7.4  Edad: el hallazgo que si preocupa")
t("La disparidad por edad es la unica que el grupo considera un problema real del modelo.")
tabla(
    ["Grupo de edad", "n", "Prevalencia real", "Tasa de alerta", "Sensibilidad", "ROC-AUC"],
    [["Menos de 50", "3.078", "11,50 %", "**30,2 %**", "0,593", "**0,713**"],
     ["50 a 60", "3.451", "8,92 %", "29,2 %", "0,545", "0,697"],
     ["60 a 70", "4.519", "12,35 %", "37,3 %", "0,615", "0,670"],
     ["70 a 80", "4.912", "11,77 %", "40,6 %", "0,576", "0,633"],
     ["80 o mas", "3.910", "11,89 %", "**51,3 %**", "0,654", "**0,619**"]],
    anchos=[3.2, 1.9, 2.8, 2.6, 2.4, 2.4], alinear_der={1, 2, 3, 4, 5})
t("Hay dos cosas que leer en esta tabla, y las dos apuntan en la misma direccion:")
vinieta("**La tasa de alerta crece con la edad** (30,2 % → 51,3 %), pero **la prevalencia "
        "real no lo hace**: es 11,50 % en los menores de 50 y 11,89 % en los mayores de 80. "
        "Es decir, el modelo alerta mucho mas sobre los pacientes mayores **sin que su "
        "riesgo real sea mayor**. La diferencia no esta justificada por los datos.")
vinieta("**La capacidad de discriminar cae con la edad** (ROC-AUC 0,713 → 0,619). "
        "Paradojicamente, el modelo es *menos* capaz de distinguir quien reingresara "
        "justamente en el grupo sobre el que mas alerta.")
t("La explicacion mas plausible es que el modelo esta usando la edad y sus correlatos "
  "-numero de medicamentos, cantidad de diagnosticos, tipo de egreso- como un indicador "
  "general de fragilidad, que efectivamente aumenta con la edad pero que **en esta cohorte "
  "no se traduce en mas reingresos a 30 dias**.")
t("La consecuencia practica es concreta: si el programa de seguimiento se aplicara tal "
  "cual, **la mitad de los pacientes mayores de 80 anos entraria en la lista**, consumiendo "
  "recursos que tal vez rindan mas en otros grupos, y los menores de 50 con riesgo real "
  "quedarian subrepresentados.")
figura("05_equidad.png", 13.0,
       "Figura 7. Tasa de alerta y sensibilidad por subgrupo. La linea punteada marca la "
       "regla de los cuatro quintos (0,80).")

h2("7.5  Lo que no se pudo auditar")
t("Hay dimensiones que el conjunto de datos no permite examinar y que conviene declarar:")
vinieta("**Nivel socioeconomico**: la unica aproximacion disponible era `payer_code`, "
        "incompleta en el 39,6 % de los casos y referida al asegurador, no al paciente.")
vinieta("**Hospital de atencion**: los 130 hospitales no estan identificados, de modo que no "
        "se puede verificar si el modelo rinde peor en centros pequenos o rurales.")
vinieta("**Grupos pequenos**: `Asian`, `Hispanic` y `Other` suman menos del 5 % de la "
        "prueba. Las cifras existen pero no sostienen una conclusion.")

h2("7.6  Riesgos de uso y salvaguardas propuestas")
tabla(
    ["Riesgo", "Salvaguarda propuesta"],
    [["Que la alerta se interprete como diagnostico",
      "La aplicacion muestra siempre que de cada 6 alertas 1 corresponde a un reingreso real, "
      "y rotula el prototipo como no clinico."],
     ["Que se niegue el alta o se condicione un servicio por una puntuacion alta",
      "Declarar en la ficha del modelo que la salida solo puede **anadir** seguimiento, nunca "
      "restringir atencion."],
     ["Que la disparidad por edad se traslade a la asignacion de recursos",
      "Monitorear la tasa de alerta por grupo etario y, de usarse, evaluar umbrales "
      "diferenciados o una cuota por grupo."],
     ["Que el desempeno se degrade con el tiempo",
      "Reevaluar con datos propios antes de cualquier uso y repetir la auditoria de forma "
      "periodica."],
     ["Que se use fuera de la poblacion para la que se entreno",
      "Los datos son de hospitales de Estados Unidos entre 1999 y 2008; se declara "
      "explicitamente que no hay evidencia de validez en el sistema de salud colombiano."]],
    anchos=[6.0, 9.6])

# ============================================================= 8 DESPLIEGUE
h1("Despliegue de la solucion", 8)
h2("8.1  Aplicacion web")
t(f"La solucion esta publicada y operativa en **{URL_APP}**. Es una aplicacion construida "
  "con Streamlit que carga el modelo entrenado y se organiza en cuatro paginas:")
vinieta("**Estimar riesgo**: un formulario con las 17 variables mas influyentes devuelve la "
        "probabilidad estimada y si supera el umbral de alerta. Las 33 variables restantes "
        "toman el valor tipico del entrenamiento, y la interfaz lo declara de forma visible "
        "para no aparentar una precision que no tiene.")
vinieta("**Desempeno del modelo**: matriz de confusion, comparacion de modelos y un control "
        "deslizante que permite mover el umbral y ver en vivo el intercambio entre "
        "reingresos detectados y falsas alarmas. Es la pagina que hace tangible que el "
        "umbral es una decision de politica.")
vinieta("**Equidad y limites**: las tablas por subgrupo, el analisis de sensibilidad por "
        "tipo de egreso y las condiciones de uso.")
vinieta("**Ficha del modelo**: datos, particion, algoritmo, hiperparametros, umbral y "
        "cumplimiento de las metas de la Fase 1, con enlace al repositorio.")
t("El despliegue se hizo sobre Streamlit Community Cloud conectado directamente al "
  "repositorio de GitHub, de modo que **cada cambio publicado en la rama principal "
  "redespliega la aplicacion automaticamente**. El modelo serializado se versiona junto al "
  "codigo y las dependencias estan fijadas por version en `requirements.txt`, incluida "
  "`scikit-learn==1.9.1`, que es la version con la que se serializo el modelo.")

h2("8.2  Tablero de analisis")
t("Como complemento se exporto `reports/predicciones_prueba.csv`, con las 19.870 filas del "
  "conjunto de prueba, su probabilidad estimada, la alerta resultante y el valor real, mas "
  "los atributos de auditoria. Ese archivo alimenta un tablero local que permite recorrer "
  "el desempeno por subgrupo sin necesidad de ejecutar codigo, pensado para un publico no "
  "tecnico.")

h2("8.3  Reproducibilidad")
t(f"Todo el trabajo esta en **{URL_REPO}**, organizado en cinco cuadernos que se ejecutan en "
  "orden: preprocesamiento y particion, modelos de referencia, ajuste del Gradient Boosting, "
  "eleccion del umbral y evaluacion final, y auditoria de equidad. Las semillas estan "
  "fijadas, la particion es determinista y cada cuaderno guarda sus resultados en "
  "`reports/`, de modo que las cifras de este informe pueden regenerarse completas desde "
  "los datos crudos.")

# ============================================================= 9 LIMITACIONES
h1("Limitaciones", 9)
t("El grupo reconoce las siguientes limitaciones, ordenadas de mayor a menor gravedad:")
vinieta("**El desempeno util es menor que el reportado globalmente.** La sensibilidad de "
        "0,60 se descompone en 0,88 para pacientes transferidos y **0,48 para los que se "
        "van a casa**, que son el caso de uso real (seccion 6.2).")
vinieta("**Existe una disparidad por edad no justificada por el riesgo.** Razon de paridad "
        "de 0,569, con mayor tasa de alerta y menor capacidad de discriminacion en los "
        "pacientes de mas edad (seccion 7.4).")
vinieta("**La precision es baja.** Con el umbral elegido, 5 de cada 6 alertas son falsas. "
        "La meta de precision 0,20 no se alcanza en ningun umbral compatible con la "
        "sensibilidad pedida.")
vinieta("**Los datos son antiguos y de otro sistema de salud.** Hospitales de Estados "
        "Unidos entre 1999 y 2008. Las practicas clinicas, los medicamentos y la "
        "organizacion asistencial han cambiado, y no hay evidencia de validez en Colombia.")
vinieta("**Faltan los determinantes mas importantes del reingreso.** Soporte familiar, "
        "acceso efectivo a medicamentos, adherencia y continuidad del cuidado ambulatorio no "
        "estan en la base, y probablemente explican buena parte de lo que el modelo no logra "
        "explicar.")
vinieta("**El modelo depende de dos variables administrativas** que concentran el 43,5 % de "
        "su desempeno, una de las cuales -el tipo de egreso- describe una decision del "
        "hospital mas que una condicion del paciente.")
vinieta("**No se evaluo la estabilidad temporal.** La particion es por paciente, no por "
        "periodo, de modo que no se verifico si un modelo entrenado con los anos iniciales "
        "mantiene su desempeno en los anos finales.")

# ============================================================= 10 CONCLUSIONES
h1("Conclusiones", 10)
t("**1. El objetivo tecnico se alcanzo.** Se construyo, evaluo y desplego un modelo "
  "completo, con particion correcta por paciente, sin fuga de informacion y con el conjunto "
  "de prueba intacto hasta el final. El AP de 0,2249 casi duplica el azar y tres de las "
  "cuatro metas de la Fase 1 se cumplieron.")
t("**2. La ganancia del modelo complejo sobre el simple es pequena.** La regresion "
  "logistica alcanza un AP de 0,2136 y el Gradient Boosting ajustado 0,2249: una mejora del "
  "4,8 %. El valor del proyecto esta mucho mas en el procedimiento -particion, umbral, "
  "auditoria- que en la eleccion del algoritmo.")
t("**3. La cifra global oculta el desempeno en el caso de uso real.** Separar por tipo de "
  "egreso mostro que la sensibilidad cae de 0,88 a 0,48 justo en la poblacion a la que "
  "iria dirigido el programa. Es el resultado mas importante del proyecto y no se habria "
  "visto sin el analisis de sensibilidad.")
t("**4. Existe una disparidad por edad que debe resolverse antes de cualquier uso.** El "
  "modelo alerta sobre la mitad de los pacientes de 80 anos o mas sin que su riesgo real lo "
  "justifique, y es en ese grupo donde peor discrimina.")
t("**5. Una meta no se cumplio y se reporta como tal.** No existe umbral que alcance a la "
  "vez sensibilidad 0,60 y precision 0,20. Documentarlo, en lugar de ajustar el criterio, "
  "forma parte de lo que el grupo entiende por evaluacion honesta.")
t("**6. El veredicto global es viabilidad demostrada, uso no recomendado.** El prototipo "
  "muestra que el enfoque funciona y que la infraestructura esta resuelta, pero su "
  "desempeno real y sus sesgos **no permiten orientar decisiones clinicas** en su estado "
  "actual.")

# ============================================================= 11 FUTURO
h1("Trabajo futuro", 11)
tabla(
    ["Linea", "Que se haria", "Que resolveria"],
    [["Corregir la disparidad por edad",
      "Evaluar umbrales por grupo etario o restriccion de paridad durante el entrenamiento",
      "La razon de paridad de 0,569"],
     ["Modelo especifico para alta domiciliaria",
      "Entrenar solo con los pacientes que se van a casa, sin usar el tipo de egreso",
      "La caida de sensibilidad a 0,48 en el caso de uso real"],
     ["Incorporar determinantes sociales",
      "Anadir soporte familiar, acceso a medicacion y existencia de cita de control",
      "El techo de ROC-AUC en 0,67"],
     ["Validacion temporal",
      "Entrenar con los primeros anos y evaluar en los ultimos",
      "La estabilidad del modelo en el tiempo"],
     ["Explicacion por paciente",
      "Anadir valores SHAP a la aplicacion",
      "Que el clinico sepa por que se alerto a ese paciente"],
     ["Evaluacion economica",
      "Modelar el costo de la llamada frente al del reingreso evitado",
      "Si el umbral elegido es el correcto para la institucion"]],
    anchos=[3.8, 6.4, 5.4])

# ============================================================= 12 REFERENCIAS
h1("Referencias", 12)
for ref in [
    "Strack, B., DeShazo, J. P., Gennings, C., Olmo, J. L., Ventura, S., Cios, K. J. y Clore, "
    "J. N. (2014). Impact of HbA1c measurement on hospital readmission rates: analysis of "
    "70,000 clinical database patient records. *BioMed Research International*, 2014.",
    "Clore, J., Cios, K., DeShazo, J. y Strack, B. (2014). *Diabetes 130-US Hospitals for "
    "Years 1999-2008* [conjunto de datos]. UCI Machine Learning Repository.",
    "Pedregosa, F. *et al.* (2011). Scikit-learn: Machine Learning in Python. *Journal of "
    "Machine Learning Research*, 12, 2825-2830.",
    "Barocas, S., Hardt, M. y Narayanan, A. (2023). *Fairness and Machine Learning: Limitations "
    "and Opportunities*. MIT Press.",
    "Hardt, M., Price, E. y Srebro, N. (2016). Equality of Opportunity in Supervised Learning. "
    "*Advances in Neural Information Processing Systems*, 29.",
    "Mitchell, M. *et al.* (2019). Model Cards for Model Reporting. *Proceedings of the "
    "Conference on Fairness, Accountability, and Transparency*, 220-229.",
    "Centers for Medicare & Medicaid Services (2008-2010). *Data Entrepreneurs' Synthetic "
    "Public Use File (DE-SynPUF)*.",
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Cm(0.7)
    p.paragraph_format.first_line_indent = Cm(-0.7)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    fragmentos(p, ref, 9)

# ============================================================= ANEXO
h1("Anexo A. Tablas completas de la auditoria de equidad")
t("Se reproducen las tablas por subgrupo con todas sus columnas, calculadas sobre el "
  "conjunto de prueba (n = 19.870) con el umbral definitivo de 0,1123. Los subgrupos con "
  "menos de 50 casos o menos de 10 reingresos no se incluyen.")

tabla(
    ["Grupo racial", "n", "Prevalencia", "Tasa alerta", "Sensib.", "Precision", "ROC-AUC", "Brier"],
    [["Caucasian", "14.717", "11,39 %", "38,6 %", "0,595", "0,175", "0,661", "0,0966"],
     ["AfricanAmerican", "3.782", "11,63 %", "39,1 %", "0,602", "0,179", "0,662", "0,0984"],
     ["Hispanic", "486", "13,17 %", "34,8 %", "0,672", "0,254", "0,760", "0,1019"],
     ["Sin registro", "449", "7,35 %", "31,4 %", "0,545", "0,128", "0,683", "0,0679"],
     ["Other", "293", "9,56 %", "36,9 %", "0,714", "0,185", "0,689", "0,0825"],
     ["Asian", "143", "14,69 %", "30,8 %", "0,714", "0,341", "0,762", "0,1102"]],
    anchos=[3.0, 1.7, 2.1, 1.9, 1.6, 1.8, 1.7, 1.6], size=8.2,
    alinear_der={1, 2, 3, 4, 5, 6, 7},
    titulo="Tabla A.1  Desempeno por grupo racial (variable excluida del modelo, usada solo para auditar)")
nota("Razon de paridad global: 0,786. Entre los dos grupos con tamano suficiente "
     "(`Caucasian` y `AfricanAmerican`) la razon es 0,987.")

tabla(
    ["Genero", "n", "Prevalencia", "Tasa alerta", "Sensib.", "Precision", "ROC-AUC", "Brier"],
    [["Femenino", "10.772", "11,33 %", "40,1 %", "0,625", "0,177", "0,674", "0,0952"],
     ["Masculino", "9.098", "11,46 %", "36,3 %", "0,570", "0,180", "0,657", "0,0976"]],
    anchos=[3.0, 1.7, 2.1, 1.9, 1.6, 1.8, 1.7, 1.6], size=8.2,
    alinear_der={1, 2, 3, 4, 5, 6, 7},
    titulo="Tabla A.2  Desempeno por genero")
nota("Razon de paridad: 0,905. Brecha de sensibilidad: 0,055.")

tabla(
    ["Grupo de edad", "n", "Prevalencia", "Tasa alerta", "Sensib.", "Precision", "ROC-AUC", "Brier"],
    [["Menos de 50", "3.078", "11,50 %", "30,2 %", "0,593", "0,226", "0,713", "0,0925"],
     ["50 a 60", "3.451", "8,92 %", "29,2 %", "0,545", "0,167", "0,697", "0,0775"],
     ["60 a 70", "4.519", "12,35 %", "37,3 %", "0,615", "0,203", "0,670", "0,1030"],
     ["70 a 80", "4.912", "11,77 %", "40,6 %", "0,576", "0,167", "0,633", "0,1006"],
     ["80 o mas", "3.910", "11,89 %", "51,3 %", "0,654", "0,151", "0,619", "0,1028"]],
    anchos=[3.0, 1.7, 2.1, 1.9, 1.6, 1.8, 1.7, 1.6], size=8.2,
    alinear_der={1, 2, 3, 4, 5, 6, 7},
    titulo="Tabla A.3  Desempeno por grupo de edad")
nota("Razon de paridad: 0,569. La tasa de alerta sube 21 puntos entre el grupo mas joven y "
     "el mas viejo mientras la prevalencia real se mueve menos de medio punto.")

tabla(
    ["Variable", "Caida del AP", "% del AP total"],
    [["`number_inpatient` - hospitalizaciones previas en el ano", "0,0565", "25,1 %"],
     ["`discharge_disposition_id` - tipo de egreso", "0,0414", "18,4 %"],
     ["`medical_specialty` - especialidad que atiende", "0,0070", "3,1 %"],
     ["`grupo_diag_2` - diagnostico secundario agrupado", "0,0047", "2,1 %"],
     ["`servicios_previos` - derivada, uso de servicios en el ano", "0,0046", "2,0 %"],
     ["`grupo_diag_1` - diagnostico principal agrupado", "0,0042", "1,9 %"],
     ["`admission_type_id` - tipo de ingreso", "0,0031", "1,4 %"],
     ["`admission_source_id` - origen del ingreso", "0,0023", "1,0 %"],
     ["`number_emergency` - visitas a urgencias en el ano", "0,0023", "1,0 %"],
     ["`grupo_diag_3` - diagnostico adicional agrupado", "0,0019", "0,8 %"],
     ["Las 40 variables restantes, en conjunto", "0,0065", "2,9 %"]],
    anchos=[10.2, 2.8, 2.6], size=8.2, alinear_der={1, 2},
    titulo="Tabla A.4  Importancia por permutacion (prueba, 5 repeticiones, metrica AP)")
nota("De las 50 variables, 21 presentan una caida nula o negativa: el modelo no las usa o "
     "le estorban levemente.")

doc.save(SALIDA)
print("guardado:", SALIDA)
print("tablas:", len(doc.tables), " parrafos:", len(doc.paragraphs))
palabras = sum(len(p.text.split()) for p in doc.paragraphs)
palabras += sum(len(c.text.split()) for tb in doc.tables for f in tb.rows for c in f.cells)
print("palabras aprox:", palabras)
