# -*- coding: utf-8 -*-
"""Los reportes que se descargan: Excel y PDF.

Tres reportes, que son las tres preguntas que Michel planteó:

1. **Seguimiento** — a quién tengo registrado, con qué riesgo y en qué estado.
2. **Cohorte** — las predicciones sobre las 19.870 hospitalizaciones de prueba.
3. **Perfil del alto riesgo** — qué tienen en común los que el modelo alerta.

El tercero es el único que no es una exportación: es análisis. Sale de
`src/perfil_alto_riesgo.py`, que parte la cohorte en dos y compara variable por
variable. Se muestra también en pantalla, porque un hallazgo que solo vive
dentro de un archivo descargado no lo lee nadie.

División deliberada entre los dos formatos: **el Excel lleva los datos
completos** —es para trabajar encima— y **el PDF lleva el informe** —resumen,
cifras y una muestra—. Un PDF de veinte mil filas no se lo lee nadie y en este
servidor tardaría una eternidad en generarse.
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE), str(BASE / "src")):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from api import autenticacion as auth  # noqa: E402
from api import seguimiento as seg  # noqa: E402

PREDICCIONES = BASE / "reports/predicciones_prueba.csv"
PERFIL_CSV = BASE / "reports/perfil_alto_riesgo.csv"
PERFIL_JSON = BASE / "reports/perfil_alto_riesgo.json"

EGRESOS = {
    1: "A casa",
    2: "Traslado a otro hospital",
    3: "Centro de enfermería",
    4: "Cuidado intermedio",
    5: "Otra institución",
    6: "A casa con atención domiciliaria",
    22: "Rehabilitación",
}

NOMBRE_ESTADO = {
    "pendiente": "Pendiente",
    "agendado": "Agendado",
    "contactado": "Contactado",
    "cerrado": "Cerrado",
}

TIPOS = ("seguimiento", "cohorte", "perfil")


# ===========================================================================
# Los datos de cada reporte
# ===========================================================================

def _tabla_seguimiento() -> pd.DataFrame:
    with seg.conexion() as cx:
        filas = cx.execute("SELECT * FROM seguimiento ORDER BY probabilidad DESC").fetchall()

    if not filas:
        return pd.DataFrame(
            columns=["Nombre", "Documento", "Teléfono", "Fecha de alta", "Riesgo",
                     "Entra en la lista", "Estado", "Agendado para", "Contactado el",
                     "Perfil", "Notas", "Registrado por", "Registrado el"]
        )

    return pd.DataFrame([
        {
            "Nombre": f["nombre"],
            "Documento": f["documento"],
            "Teléfono": f["telefono"],
            "Fecha de alta": f["fecha_alta"],
            "Riesgo": round(f["probabilidad"] * 100, 1),
            "Entra en la lista": "Sí" if f["alerta"] else "No",
            "Estado": NOMBRE_ESTADO.get(f["estado"], f["estado"]),
            "Agendado para": f["fecha_agendada"],
            "Contactado el": f["fecha_contacto"],
            "Perfil": seg._resumen(json.loads(f["entradas"])),
            "Notas": f["notas"],
            "Registrado por": f["registrado_por"],
            "Registrado el": f["creado"],
        }
        for f in filas
    ])


def _tabla_cohorte() -> pd.DataFrame:
    d = pd.read_csv(PREDICCIONES)
    return pd.DataFrame({
        "Paciente": d.paciente,
        "Riesgo estimado (%)": (d.probabilidad * 100).round(2),
        "Entra en la lista": d.alerta.map({1: "Sí", 0: "No"}),
        "Reingresó de verdad": d.reingreso_real.map({1: "Sí", 0: "No"}),
        "Resultado": d.resultado,
        "Edad": d.edad,
        "Grupo de edad": d.grupo_edad,
        "Género": d.genero.map({"Female": "Mujer", "Male": "Hombre"}).fillna(d.genero),
        "Días de estancia": d.dias_estancia,
        "Hospitalizaciones previas": d.ingresos_previos,
        "Medicamentos": d.medicamentos,
        "Diagnósticos": d.diagnosticos,
        "Diagnóstico principal": d.diagnostico_principal,
        "Tipo de egreso": d.egreso.map(EGRESOS).fillna("Otro egreso"),
    }).sort_values("Riesgo estimado (%)", ascending=False)


def _sin_nan(filas: list[dict]) -> list[dict]:
    """NaN no es JSON valido y revienta la respuesta con un 500 silencioso.

    En el CSV del perfil hay celdas vacias a proposito --una fila de promedio
    no tiene nivel, una de proporcion no tiene reingreso del resto-- y pandas
    las lee como NaN. json.dumps las acepta; el serializador de FastAPI no.
    """
    return [
        {k: (None if isinstance(v, float) and v != v else v) for k, v in fila.items()}
        for fila in filas
    ]


def _perfil() -> tuple[pd.DataFrame, dict]:
    if not PERFIL_CSV.exists() or not PERFIL_JSON.exists():
        raise HTTPException(
            503,
            "El perfil de alto riesgo todavía no está calculado. "
            "Córrase «python src/perfil_alto_riesgo.py» una vez.",
        )
    t = pd.read_csv(PERFIL_CSV)
    return t, json.loads(PERFIL_JSON.read_text(encoding="utf-8"))


# ===========================================================================
# Excel
# ===========================================================================

def _excel(hojas: dict[str, pd.DataFrame]) -> bytes:
    """Un libro con una hoja por tabla, con la cabecera congelada y a filtro.

    Se escribe en modo `write_only`, que no guarda las celdas en memoria: con
    veinte mil filas en un servidor de un núcleo, eso es la diferencia entre
    dos segundos y quedarse sin memoria.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    libro = Workbook(write_only=True)
    cabecera_letra = Font(bold=True, color="FFFFFF", size=10)
    cabecera_fondo = PatternFill("solid", fgColor="5B3FD4")

    for nombre, tabla in hojas.items():
        hoja = libro.create_sheet(nombre[:31])
        hoja.freeze_panes = "A2"

        for i, columna in enumerate(tabla.columns, start=1):
            # Un ancho por columna, acotado: el nombre de un paciente no puede
            # estirar la columna hasta sacar las demas de la pantalla.
            largo = max([len(str(columna))] + [len(str(v)) for v in tabla[columna].head(200)])
            hoja.column_dimensions[get_column_letter(i)].width = min(max(largo + 3, 11), 42)

        fila = []
        for columna in tabla.columns:
            from openpyxl.cell import WriteOnlyCell

            celda = WriteOnlyCell(hoja, value=str(columna))
            celda.font = cabecera_letra
            celda.fill = cabecera_fondo
            celda.alignment = Alignment(vertical="center")
            fila.append(celda)
        hoja.append(fila)

        for valores in tabla.itertuples(index=False):
            hoja.append(list(valores))

    memoria = io.BytesIO()
    libro.save(memoria)
    return memoria.getvalue()


# ===========================================================================
# PDF
# ===========================================================================

def _pdf(titulo: str, bajada: str, bloques: list[tuple[str, object]]) -> bytes:
    """El informe en PDF, compuesto con reportlab.

    No se usa un conversor de Markdown ni un motor de plantillas: son cuatro
    tipos de bloque y componerlos a mano pesa menos que traer una dependencia
    entera para esto.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    TINTA = colors.HexColor("#1f1f1f")
    APAGADO = colors.HexColor("#70706f")
    FILETE = colors.HexColor("#d8dcf0")
    ACENTO = colors.HexColor("#5b3fd4")

    base = getSampleStyleSheet()
    est = {
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Times-Roman",
                             fontSize=21, leading=25, spaceAfter=4, textColor=TINTA),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Times-Roman",
                             fontSize=15, leading=19, spaceBefore=17, spaceAfter=6,
                             textColor=TINTA),
        "p": ParagraphStyle("p", parent=base["BodyText"], fontName="Helvetica",
                            fontSize=9.5, leading=14.5, spaceAfter=6, textColor=TINTA),
        "nota": ParagraphStyle("nota", parent=base["BodyText"], fontName="Helvetica-Oblique",
                               fontSize=8.5, leading=12.5, spaceBefore=4, textColor=APAGADO),
        "bajada": ParagraphStyle("bajada", parent=base["BodyText"], fontName="Helvetica",
                                 fontSize=10, leading=15, spaceAfter=10, textColor=APAGADO),
        "celda": ParagraphStyle("celda", parent=base["BodyText"], fontName="Helvetica",
                                fontSize=8, leading=11, textColor=TINTA),
        "celdacab": ParagraphStyle("celdacab", parent=base["BodyText"], fontName="Helvetica-Bold",
                                   fontSize=7.5, leading=10, textColor=colors.white),
    }

    historia: list = [Paragraph(titulo, est["h1"])]
    if bajada:
        historia.append(Paragraph(bajada, est["bajada"]))
    historia.append(HRFlowable(width="100%", thickness=1.1, color=ACENTO))
    historia.append(Spacer(1, 10))

    ancho_util = LETTER[0] - 4 * cm

    for clase, contenido in bloques:
        if clase == "titulo":
            historia.append(Paragraph(str(contenido), est["h2"]))
        elif clase == "parrafo":
            historia.append(Paragraph(str(contenido), est["p"]))
        elif clase == "nota":
            historia.append(Paragraph(str(contenido), est["nota"]))
        elif clase == "salto":
            historia.append(PageBreak())
        elif clase == "cifras":
            celdas = [[], []]
            for etiqueta, valor in contenido:  # type: ignore[union-attr]
                celdas[0].append(Paragraph(
                    f'<font size="7" color="#70706f">{etiqueta.upper()}</font>', est["celda"]))
                celdas[1].append(Paragraph(
                    f'<font size="16" face="Times-Roman">{valor}</font>', est["celda"]))
            t = Table(celdas, colWidths=[ancho_util / len(celdas[0])] * len(celdas[0]))
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("LINEBELOW", (0, 1), (-1, 1), 0.5, FILETE),
            ]))
            historia.append(t)
            historia.append(Spacer(1, 8))
        elif clase == "tabla":
            columnas, filas = contenido  # type: ignore[misc]
            datos = [[Paragraph(str(c), est["celdacab"]) for c in columnas]]
            datos += [[Paragraph(str(v), est["celda"]) for v in fila] for fila in filas]
            t = Table(datos, colWidths=[ancho_util / len(columnas)] * len(columnas),
                      repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACENTO),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6ff")]),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, FILETE),
            ]))
            historia.append(t)
            historia.append(Spacer(1, 10))

    memoria = io.BytesIO()
    documento = SimpleDocTemplate(
        memoria, pagesize=LETTER,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=titulo, author="ReingresaIA — Universidad Popular del Cesar, Grupo 04",
    )

    def pie(lienzo, doc):
        lienzo.saveState()
        lienzo.setFont("Helvetica", 7)
        lienzo.setFillColor(APAGADO)
        lienzo.drawString(2 * cm, 1.25 * cm, "ReingresaIA · prototipo académico · Grupo 04")
        lienzo.drawRightString(LETTER[0] - 2 * cm, 1.25 * cm, f"Página {doc.page}")
        lienzo.restoreState()

    documento.build(historia, onFirstPage=pie, onLaterPages=pie)
    return memoria.getvalue()


# ===========================================================================
# Formato colombiano: coma decimal y punto de miles
# ===========================================================================

def _n(x: float, decimales: int = 0) -> str:
    return f"{x:,.{decimales}f}".replace(",", "\u0000").replace(".", ",").replace("\u0000", ".")


def _pc(x: float, decimales: int = 1) -> str:
    return _n(x * 100, decimales) + " %"


def _hoy() -> str:
    meses = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre")
    h = datetime.now()
    return f"{h.day} de {meses[h.month - 1]} de {h.year}"


# ===========================================================================
# Los tres informes en PDF
# ===========================================================================

def _pdf_seguimiento() -> bytes:
    t = _tabla_seguimiento()
    pendientes = int((t["Estado"] == "Pendiente").sum()) if len(t) else 0
    en_lista = int((t["Entra en la lista"] == "Sí").sum()) if len(t) else 0

    bloques: list[tuple[str, object]] = [
        ("cifras", [
            ("Pacientes registrados", _n(len(t))),
            ("Sobre el umbral", _n(en_lista)),
            ("Sin contactar", _n(pendientes)),
        ]),
        ("parrafo",
         "Estos pacientes fueron registrados a mano desde la pantalla de estimación. "
         "El riesgo de cada uno lo calculó el modelo oficial en el momento de registrarlo, "
         "con los datos de la hospitalización que aparecen en la columna «Perfil»."),
    ]

    if len(t) == 0:
        bloques.append(("parrafo", "Todavía no hay ningún paciente registrado."))
    else:
        columnas = ["Nombre", "Riesgo", "Estado", "Agendado", "Perfil"]
        # Por diccionario y no por itertuples: las columnas llevan espacios y
        # tildes, y acceder a ellas como f._8 es una bomba de relojeria en
        # cuanto alguien reordene una columna.
        filas = [
            [r["Nombre"], f'{_n(r["Riesgo"], 1)} %', r["Estado"],
             r["Agendado para"] or "—", r["Perfil"]]
            for r in t.to_dict("records")
        ]
        bloques.append(("titulo", "Los pacientes, del de mayor riesgo al de menor"))
        bloques.append(("tabla", (columnas, filas)))

    bloques.append(("nota",
                    "Prototipo académico. Esta lista ordena a quién conviene llamar primero; "
                    "no decide altas ni tratamientos."))

    return _pdf("Pacientes en seguimiento", f"Generado el {_hoy()}", bloques)


def _pdf_cohorte() -> bytes:
    d = pd.read_csv(PREDICCIONES)
    alertados = int(d.alerta.sum())
    aciertos = int(d[(d.alerta == 1) & (d.reingreso_real == 1)].shape[0])
    reingresos = int(d.reingreso_real.sum())

    top = _tabla_cohorte().head(40)
    columnas = ["Paciente", "Riesgo", "¿Reingresó?", "Edad", "Hosp. previas", "Egreso"]
    filas = [
        [r["Paciente"], f'{_n(r["Riesgo estimado (%)"], 1)} %', r["Reingresó de verdad"],
         r["Edad"], r["Hospitalizaciones previas"], r["Tipo de egreso"]]
        for r in top.to_dict("records")
    ]

    bloques: list[tuple[str, object]] = [
        ("cifras", [
            ("Hospitalizaciones", _n(len(d))),
            ("Entran en la lista", _n(alertados)),
            ("Reingresos reales", _n(reingresos)),
            ("Alertas acertadas", _n(aciertos)),
        ]),
        ("parrafo",
         f"Son las {_n(len(d))} hospitalizaciones del conjunto de prueba, que el modelo nunca "
         "vio mientras se entrenaba. De ellas el modelo marca "
         f"{_n(alertados)} para llamar, y {_n(aciertos)} de esas personas reingresaron de "
         "verdad dentro de los 30 días."),
        ("parrafo",
         f"Dicho de otro modo: de cada {round(alertados / aciertos)} alertas, una corresponde a "
         "un reingreso real. Parece poco, y lo es; pero la tasa base de la cohorte es "
         f"{_pc(reingresos / len(d))}, así que una alerta del modelo acierta "
         f"{_n((aciertos / alertados) / (reingresos / len(d)), 1)} veces más que señalar "
         "a alguien al azar."),
        ("titulo", "Los 40 pacientes de mayor riesgo estimado"),
        ("tabla", (columnas, filas)),
        ("nota",
         "El Excel de este mismo reporte trae las "
         f"{_n(len(d))} filas completas, con todas las variables. Aquí solo caben las primeras."),
    ]
    return _pdf("Predicciones sobre la cohorte de prueba", f"Generado el {_hoy()}", bloques)


def _pdf_perfil() -> bytes:
    tabla, r = _perfil()

    promedios = tabla[tabla.tipo == "promedio"]
    filas_prom = [
        [p["variable"], _n(p["alto"], 2), _n(p["resto"], 2), f'{_n(p["veces"], 2)}x']
        for p in promedios.to_dict("records")
    ]

    proporciones = tabla[(tabla.tipo == "proporcion") & (tabla.n_alto >= 60)]
    proporciones = proporciones.sort_values("veces", ascending=False).head(14)
    filas_prop = [
        [p["variable"], p["nivel"], _pc(p["alto"]), _pc(p["resto"]), f'{_n(p["veces"], 2)}x']
        for p in proporciones.to_dict("records")
    ]

    bloques: list[tuple[str, object]] = [
        ("cifras", [
            ("Alto riesgo", _n(r["n_alto"])),
            ("Resto", _n(r["n_resto"])),
            ("Reingresan (alto)", _pc(r["reingreso_alto"])),
            ("Reingresan (resto)", _pc(r["reingreso_resto"])),
        ]),
        ("parrafo",
         "Este informe responde una pregunta sencilla: de los pacientes que el modelo marca "
         "como de alto riesgo, ¿qué tienen en común? El método es aritmética, no otro modelo: "
         "se parte la cohorte de prueba en dos —los que superan el umbral y los demás— y se "
         "compara variable por variable."),
        ("parrafo",
         f"Antes de mirar los rasgos, el control: de los {_n(r['n_alto'])} marcados como de "
         f"alto riesgo reingresaron el {_pc(r['reingreso_alto'])}, contra el "
         f"{_pc(r['reingreso_resto'])} de los demás. Son <b>{_n(r['veces_mas_reingreso'], 2)} "
         "veces más</b>. Si esta cifra no fuera mayor que uno, lo que sigue no valdría nada."),
        ("titulo", "Lo que más distingue al grupo de alto riesgo"),
        ("parrafo",
         "Promedios de cada grupo. La última columna dice cuántas veces más alto es el "
         "promedio entre los de alto riesgo."),
        ("tabla", (["Variable", "Alto riesgo", "Los demás", "Veces"], filas_prom)),
        ("titulo", "Y en qué categorías se concentran"),
        ("parrafo",
         "Qué proporción de cada grupo cae en cada categoría. Solo se muestran las "
         "categorías con al menos sesenta pacientes del lado de alto riesgo."),
        ("tabla", (["Variable", "Categoría", "Alto riesgo", "Los demás", "Veces"], filas_prop)),
        ("nota",
         "Calculado con src/perfil_alto_riesgo.py sobre reports/predicciones_prueba.csv. "
         "Es reproducible: corra el script y debe dar exactamente estas cifras."),
    ]
    return _pdf("Perfil del paciente de alto riesgo", f"Generado el {_hoy()}", bloques)


# ===========================================================================
# Las rutas
# ===========================================================================

def catalogo(_=Depends(auth.exige("Reportes"))):
    """Qué se puede descargar, y el perfil de alto riesgo para verlo en pantalla.

    El perfil viaja aquí entero a propósito: un hallazgo que solo vive dentro
    de un archivo descargado no lo lee nadie.
    """
    with seg.conexion() as cx:
        registrados = int(cx.execute("SELECT COUNT(*) FROM seguimiento").fetchone()[0])

    try:
        tabla, resumen = _perfil()
        perfil = {
            "resumen": resumen,
            "promedios": _sin_nan(tabla[tabla.tipo == "promedio"].to_dict("records")),
            "proporciones": _sin_nan(
                tabla[(tabla.tipo == "proporcion") & (tabla.n_alto >= 60)]
                .sort_values("veces", ascending=False)
                .head(14)
                .to_dict("records")
            ),
        }
    except HTTPException:
        perfil = None

    return {
        "reportes": [
            {
                "tipo": "seguimiento",
                "titulo": "Pacientes en seguimiento",
                "descripcion": "Quién está registrado, con qué riesgo y en qué estado va.",
                "filas": registrados,
            },
            {
                "tipo": "cohorte",
                "titulo": "Predicciones de la cohorte",
                "descripcion": (
                    "Las 19.870 hospitalizaciones de prueba con su riesgo estimado y "
                    "si reingresaron de verdad."
                ),
                "filas": 19870,
            },
            {
                "tipo": "perfil",
                "titulo": "Perfil del alto riesgo",
                "descripcion": "Qué tienen en común los pacientes que el modelo alerta.",
                "filas": len(tabla) if perfil else 0,
            },
        ],
        "perfil": perfil,
    }


EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _descarga(cuerpo: bytes, nombre: str, tipo_mime: str) -> Response:
    return Response(
        content=cuerpo,
        media_type=tipo_mime,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


def excel(tipo: str, _=Depends(auth.exige("Reportes"))):
    if tipo not in TIPOS:
        raise HTTPException(404, "Ese reporte no existe.")

    fecha = datetime.now().strftime("%Y-%m-%d")

    if tipo == "seguimiento":
        cuerpo = _excel({"Seguimiento": _tabla_seguimiento()})
    elif tipo == "cohorte":
        cuerpo = _excel({"Predicciones": _tabla_cohorte()})
    else:
        tabla, _r = _perfil()
        cuerpo = _excel({
            "Promedios": tabla[tabla.tipo == "promedio"].drop(columns=["tipo", "nivel"]),
            "Proporciones": tabla[tabla.tipo == "proporcion"].drop(columns=["tipo"]),
        })

    return _descarga(cuerpo, f"reingresaia-{tipo}-{fecha}.xlsx", EXCEL)


def pdf(tipo: str, _=Depends(auth.exige("Reportes"))):
    if tipo not in TIPOS:
        raise HTTPException(404, "Ese reporte no existe.")

    fecha = datetime.now().strftime("%Y-%m-%d")
    cuerpo = {
        "seguimiento": _pdf_seguimiento,
        "cohorte": _pdf_cohorte,
        "perfil": _pdf_perfil,
    }[tipo]()

    return _descarga(cuerpo, f"reingresaia-{tipo}-{fecha}.pdf", "application/pdf")


def registrar(app: FastAPI) -> None:
    app.get("/api/reportes")(catalogo)
    app.get("/api/reportes/{tipo}.xlsx")(excel)
    app.get("/api/reportes/{tipo}.pdf")(pdf)
