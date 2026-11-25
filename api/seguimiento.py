# -*- coding: utf-8 -*-
"""Pacientes registrados para seguimiento después del alta.

Idea de Michel: que estimar un paciente no termine en un número que se pierde
al recargar. Si el riesgo es alto, lo lógico es anotarlo y llamarlo, y para eso
hay que guardarlo en alguna parte.

Se usa SQLite de la biblioteca estándar. Es un archivo, no necesita servidor,
no agrega una dependencia y aguanta de sobra lo que esta aplicación va a
registrar. La conexión se abre y se cierra en cada petición: con un solo worker
de uvicorn eso es lo más simple y no hay forma de que dos hilos compartan una
conexión sin darse cuenta.

El archivo vive en `datos/`, que en el servidor es un volumen de Docker. Si no
lo fuera, cada redespliegue borraría los pacientes registrados.
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent.parent
for ruta in (str(BASE / "app"), str(BASE)):
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

import datos as datos_app  # noqa: E402
import modelo  # noqa: E402

from api import autenticacion as auth  # noqa: E402
from api.prediccion import Entradas, _valida  # noqa: E402

CARPETA = Path(os.environ.get("REINGRESAIA_DATOS", str(BASE / "datos")))
ARCHIVO = CARPETA / "seguimiento.db"

ESTADOS = ("pendiente", "agendado", "contactado", "cerrado")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS seguimiento (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  creado          TEXT    NOT NULL,
  registrado_por  TEXT    NOT NULL,
  nombre          TEXT    NOT NULL,
  documento       TEXT    NOT NULL DEFAULT '',
  telefono        TEXT    NOT NULL DEFAULT '',
  fecha_alta      TEXT    NOT NULL DEFAULT '',
  entradas        TEXT    NOT NULL,
  probabilidad    REAL    NOT NULL,
  umbral          REAL    NOT NULL,
  alerta          INTEGER NOT NULL,
  estado          TEXT    NOT NULL DEFAULT 'pendiente',
  fecha_agendada  TEXT    NOT NULL DEFAULT '',
  fecha_contacto  TEXT    NOT NULL DEFAULT '',
  notas           TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_seguimiento_estado ON seguimiento(estado);
CREATE INDEX IF NOT EXISTS idx_seguimiento_agenda ON seguimiento(fecha_agendada);
CREATE TABLE IF NOT EXISTS contactos (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  seguimiento_id  INTEGER NOT NULL REFERENCES seguimiento(id) ON DELETE CASCADE,
  creado          TEXT NOT NULL,
  registrado_por  TEXT NOT NULL,
  resultado       TEXT NOT NULL,
  observaciones   TEXT NOT NULL DEFAULT '',
  fecha_proxima   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_contactos_paciente
  ON contactos(seguimiento_id, creado DESC, id DESC);
"""


@contextmanager
def conexion():
    """Una conexión por petición, con las filas accesibles por nombre."""
    CARPETA.mkdir(parents=True, exist_ok=True)
    cx = sqlite3.connect(ARCHIVO, timeout=10)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA foreign_keys = ON")
    try:
        yield cx
        cx.commit()
    finally:
        cx.close()


def preparar() -> None:
    """Crea la tabla si no existe. Se llama al registrar las rutas."""
    with conexion() as cx:
        cx.executescript(ESQUEMA)


def _fila(r: sqlite3.Row) -> dict:
    entradas = json.loads(r["entradas"])
    return {
        "id": r["id"],
        "creado": r["creado"],
        "registrado_por": r["registrado_por"],
        "nombre": r["nombre"],
        "documento": r["documento"],
        "telefono": r["telefono"],
        "fecha_alta": r["fecha_alta"],
        "entradas": entradas,
        "probabilidad": r["probabilidad"],
        "umbral": r["umbral"],
        "alerta": bool(r["alerta"]),
        "estado": r["estado"],
        "fecha_agendada": r["fecha_agendada"],
        "fecha_contacto": r["fecha_contacto"],
        "notas": r["notas"],
        # Se calcula aqui y no en el navegador: asi la lista y el PDF dicen lo
        # mismo, que es justo donde se cuelan las diferencias de un dia.
        "dias_desde_alta": _dias_desde(r["fecha_alta"]),
        "resumen": _resumen(entradas),
    }


def _dias_desde(fecha: str) -> int | None:
    if not fecha:
        return None
    try:
        return (date.today() - date.fromisoformat(fecha)).days
    except ValueError:
        return None


def _resumen(entradas: dict) -> str:
    """Una línea que dice quién es el paciente, para la tabla y la agenda."""
    partes = [f"{int(entradas.get('edad', 0))} años"]
    genero = entradas.get("genero")
    if genero:
        partes.append("Mujer" if genero == "Female" else "Hombre")
    ingresos = int(entradas.get("ingresos", 0))
    if ingresos:
        partes.append(f"{ingresos} hospitalización previa" if ingresos == 1
                      else f"{ingresos} hospitalizaciones previas")
    egreso = entradas.get("egreso")
    if egreso:
        partes.append(modelo.ETIQUETAS.get("egreso", {}).get(egreso, egreso))
    return " · ".join(partes)


class Registro(BaseModel):
    """Lo que se envía al registrar: la persona y la hospitalización."""

    nombre: str = Field(min_length=1, max_length=120)
    documento: str = Field(default="", max_length=40)
    telefono: str = Field(default="", max_length=40)
    fecha_alta: str = Field(default="", max_length=10)
    entradas: Entradas


class Cambio(BaseModel):
    estado: str | None = None
    fecha_agendada: str | None = Field(default=None, max_length=10)
    notas: str | None = Field(default=None, max_length=2000)


def crear(registro: Registro, peticion: Request, sesion=Depends(auth.exige("Seguimiento"))):
    """Guarda un paciente y vuelve a calcular su riesgo aquí mismo.

    No se cree la probabilidad que manda el navegador. Cuesta milisegundos
    recalcularla y evita que quede guardado un número que no corresponde a lo
    que el modelo diria hoy con esos datos.
    """
    valores = _valida(registro.entradas)
    probabilidad, _ = modelo.explicar(valores)
    umbral = float(datos_app.umbral_oficial())

    with conexion() as cx:
        cursor = cx.execute(
            """
            INSERT INTO seguimiento
              (creado, registrado_por, nombre, documento, telefono, fecha_alta,
               entradas, probabilidad, umbral, alerta, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendiente')
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                sesion.get("usuario", ""),
                registro.nombre.strip(),
                registro.documento.strip(),
                registro.telefono.strip(),
                registro.fecha_alta.strip(),
                json.dumps(valores, ensure_ascii=False),
                round(float(probabilidad), 6),
                round(umbral, 6),
                int(probabilidad >= umbral),
            ),
        )
        nuevo = cx.execute(
            "SELECT * FROM seguimiento WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return _fila(nuevo)


def listar(estado: str = "", q: str = "", _=Depends(auth.exige("Seguimiento"))):
    """Los pacientes registrados, del de mayor riesgo al de menor."""
    condiciones, parametros = [], []
    if estado in ESTADOS:
        condiciones.append("estado = ?")
        parametros.append(estado)
    if q.strip():
        condiciones.append("(nombre LIKE ? OR documento LIKE ?)")
        parametros += [f"%{q.strip()}%"] * 2

    donde = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    with conexion() as cx:
        filas = cx.execute(
            f"SELECT * FROM seguimiento {donde} ORDER BY probabilidad DESC, id DESC",
            parametros,
        ).fetchall()
        cuentas = dict(
            cx.execute("SELECT estado, COUNT(*) FROM seguimiento GROUP BY estado").fetchall()
        )

    return {
        "pacientes": [_fila(f) for f in filas],
        "cuentas": {e: int(cuentas.get(e, 0)) for e in ESTADOS},
        "total": sum(int(v) for v in cuentas.values()),
    }


def cambiar(id: int, cambio: Cambio, _=Depends(auth.exige("Seguimiento"))):
    """Cambia estado, fecha agendada o notas de un paciente."""
    campos, parametros = [], []

    if cambio.estado is not None:
        if cambio.estado not in ESTADOS:
            raise HTTPException(422, f"«{cambio.estado}» no es un estado de seguimiento.")
        campos.append("estado = ?")
        parametros.append(cambio.estado)
        # Marcar contactado sin dejar constancia de cuándo deja la lista inútil
        # para saber si se cumplió la ventana de los treinta días.
        if cambio.estado == "contactado":
            campos.append("fecha_contacto = ?")
            parametros.append(date.today().isoformat())

    if cambio.fecha_agendada is not None:
        fecha = cambio.fecha_agendada.strip()
        if fecha:
            try:
                date.fromisoformat(fecha)
            except ValueError:
                raise HTTPException(422, "La fecha debe venir como AAAA-MM-DD.")
        campos.append("fecha_agendada = ?")
        parametros.append(fecha)
        # Agendar y dejarlo en pendiente se contradice en la lista.
        if fecha and cambio.estado is None:
            campos.append("estado = ?")
            parametros.append("agendado")

    if cambio.notas is not None:
        campos.append("notas = ?")
        parametros.append(cambio.notas)

    if not campos:
        raise HTTPException(422, "No se indicó nada que cambiar.")

    with conexion() as cx:
        cx.execute(f"UPDATE seguimiento SET {', '.join(campos)} WHERE id = ?", [*parametros, id])
        fila = cx.execute("SELECT * FROM seguimiento WHERE id = ?", (id,)).fetchone()

    if fila is None:
        raise HTTPException(404, "Ese paciente no está en seguimiento.")
    return _fila(fila)


# Cada llamada queda registrada; las notas de seguimiento actuales
# pueden cambiar, pero nunca sobrescriben contactos anteriores.
RESULTADOS_CONTACTO = ("contactado", "sin_respuesta", "reprogramar")


class NuevoContacto(BaseModel):
    resultado: str
    observaciones: str = Field(default="", max_length=2000)
    fecha_proxima: str = Field(default="", max_length=10)


def contactos(id: int, _=Depends(auth.exige("Seguimiento"))):
    with conexion() as cx:
        existe = cx.execute("SELECT 1 FROM seguimiento WHERE id = ?", (id,)).fetchone()
        if existe is None:
            raise HTTPException(404, "Ese paciente no está en seguimiento.")
        filas = cx.execute(
            """SELECT id, seguimiento_id, creado, registrado_por, resultado,
                      observaciones, fecha_proxima
               FROM contactos WHERE seguimiento_id = ?
               ORDER BY creado DESC, id DESC""",
            (id,),
        ).fetchall()
    return {"contactos": [dict(f) for f in filas]}


def registrar_contacto(
    id: int, contacto: NuevoContacto,
    sesion=Depends(auth.exige("Seguimiento")),
):
    if contacto.resultado not in RESULTADOS_CONTACTO:
        raise HTTPException(422, "Resultado del contacto no reconocido.")
    proxima = contacto.fecha_proxima.strip()
    if proxima:
        try:
            fecha = date.fromisoformat(proxima)
        except ValueError:
            raise HTTPException(422, "La próxima fecha debe tener formato AAAA-MM-DD.")
        if fecha < date.today():
            raise HTTPException(422, "La próxima llamada no puede quedar en el pasado.")
    if contacto.resultado == "reprogramar" and not proxima:
        raise HTTPException(422, "Indique la fecha de la próxima llamada.")
    ahora = datetime.now().isoformat(timespec="seconds")
    with conexion() as cx:
        existe = cx.execute(
            "SELECT id FROM seguimiento WHERE id = ?", (id,)
        ).fetchone()
        if existe is None:
            raise HTTPException(404, "Ese paciente no está en seguimiento.")
        cursor = cx.execute(
            """INSERT INTO contactos
               (seguimiento_id, creado, registrado_por, resultado,
                observaciones, fecha_proxima)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (id, ahora, sesion.get("usuario", ""),
             contacto.resultado, contacto.observaciones.strip(), proxima),
        )
        if contacto.resultado == "contactado":
            nuevo_estado = "agendado" if proxima else "contactado"
            cx.execute(
                """UPDATE seguimiento SET estado = ?, fecha_contacto = ?,
                   fecha_agendada = ? WHERE id = ?""",
                (nuevo_estado, date.today().isoformat(), proxima, id),
            )
        elif proxima:
            cx.execute(
                "UPDATE seguimiento SET estado = 'agendado', fecha_agendada = ? WHERE id = ?",
                (proxima, id),
            )
        else:
            cx.execute(
                """UPDATE seguimiento SET estado = 'pendiente',
                   fecha_agendada = '' WHERE id = ?""",
                (id,),
            )
        fila = cx.execute("SELECT * FROM contactos WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(fila)


def borrar(id: int, _=Depends(auth.exige("Seguimiento"))):
    with conexion() as cx:
        cursor = cx.execute("DELETE FROM seguimiento WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        raise HTTPException(404, "Ese paciente no está en seguimiento.")
    return {"borrado": id}


def agenda(lunes: str = "", _=Depends(auth.exige("Seguimiento"))):
    """La semana de llamadas, de lunes a viernes.

    Devuelve siempre los cinco días, aunque estén vacíos: una rejilla a la que
    le faltan días según lo que haya agendado se lee como un error.
    """
    try:
        inicio = date.fromisoformat(lunes) if lunes else date.today()
    except ValueError:
        raise HTTPException(422, "La fecha debe venir como AAAA-MM-DD.")
    # En sabado o domingo lo util es la semana que viene, no la que acaba de
    # terminar: nadie agenda llamadas para el lunes que ya paso.
    if not lunes and inicio.weekday() >= 5:
        inicio = inicio + timedelta(days=7 - inicio.weekday())
    else:
        inicio = inicio - timedelta(days=inicio.weekday())
    fin = inicio + timedelta(days=4)

    with conexion() as cx:
        filas = cx.execute(
            """
            SELECT * FROM seguimiento
            WHERE fecha_agendada >= ? AND fecha_agendada <= ?
            ORDER BY fecha_agendada, probabilidad DESC
            """,
            (inicio.isoformat(), fin.isoformat()),
        ).fetchall()
        sin_agendar = cx.execute(
            """
            SELECT * FROM seguimiento
            WHERE fecha_agendada = '' AND estado = 'pendiente'
            ORDER BY probabilidad DESC LIMIT 30
            """
        ).fetchall()

    por_dia: dict[str, list[dict]] = {}
    for f in filas:
        por_dia.setdefault(f["fecha_agendada"], []).append(_fila(f))

    return {
        "lunes": inicio.isoformat(),
        "hoy": date.today().isoformat(),
        "dias": [
            {
                "fecha": (d := (inicio + timedelta(days=i))).isoformat(),
                "nombre": ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes")[i],
                "numero": d.day,
                "pacientes": por_dia.get(d.isoformat(), []),
            }
            for i in range(5)
        ],
        "sin_agendar": [_fila(f) for f in sin_agendar],
    }


def registrar(app: FastAPI) -> None:
    """Cuelga las rutas del seguimiento y crea la tabla si hace falta."""
    preparar()
    app.post("/api/seguimiento")(crear)
    app.get("/api/seguimiento")(listar)
    app.get("/api/seguimiento/agenda")(agenda)
    app.get("/api/seguimiento/{id}/contactos")(contactos)
    app.post("/api/seguimiento/{id}/contactos")(registrar_contacto)
    app.patch("/api/seguimiento/{id}")(cambiar)
    app.delete("/api/seguimiento/{id}")(borrar)
