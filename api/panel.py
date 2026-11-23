# -*- coding: utf-8 -*-
"""El panel de inicio: lo que hay que saber antes de hacer nada.

Reúne en una sola petición lo que la primera pantalla necesita, en vez de
dejar que el navegador pida cuatro cosas a cuatro rutas distintas y las dibuje
a destiempo. En un servidor de un núcleo eso también se nota.

No inventa ninguna cifra: el seguimiento sale de la base de datos y lo demás
de los archivos de `reports/` que ya estaban publicados.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, Request

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

from api import autenticacion as auth  # noqa: E402
from api import pacientes as pac  # noqa: E402
from api import seguimiento as seg  # noqa: E402

TASA_BASE = 0.1139


def panel(peticion: Request, sesion=Depends(auth.exige("Guía"))):
    """Las cifras del panel y los pacientes que piden atención."""
    hoy = date.today()
    fin_semana = (hoy + timedelta(days=7)).isoformat()

    with seg.conexion() as cx:
        cuentas = dict(
            cx.execute("SELECT estado, COUNT(*) FROM seguimiento GROUP BY estado").fetchall()
        )
        sobre_umbral = int(
            cx.execute("SELECT COUNT(*) FROM seguimiento WHERE alerta = 1").fetchone()[0]
        )
        # Los que piden atencion: primero los de mayor riesgo sin contactar.
        urgentes = cx.execute(
            """
            SELECT * FROM seguimiento
            WHERE estado IN ('pendiente', 'agendado')
            ORDER BY probabilidad DESC LIMIT 8
            """
        ).fetchall()
        esta_semana = cx.execute(
            """
            SELECT COUNT(*) FROM seguimiento
            WHERE fecha_agendada >= ? AND fecha_agendada <= ?
            """,
            (hoy.isoformat(), fin_semana),
        ).fetchone()[0]

    _, umbral = pac._cohorte()
    registrados = sum(int(v) for v in cuentas.values())

    return {
        "nombre": sesion.get("nombre", ""),
        "rol": sesion.get("rol", ""),
        "puede_operar": "Fijar umbral" in set(sesion.get("permisos", [])),
        "cifras": {
            "registrados": registrados,
            "pendientes": int(cuentas.get("pendiente", 0)),
            "agendados": int(cuentas.get("agendado", 0)),
            "contactados": int(cuentas.get("contactado", 0)),
            "sobre_umbral": sobre_umbral,
            "proximos_siete_dias": int(esta_semana),
            "tasa_base": TASA_BASE,
            "umbral": round(umbral, 6),
        },
        "urgentes": [seg._fila(f) for f in urgentes],
    }


def registrar(app: FastAPI) -> None:
    app.get("/api/panel")(panel)
