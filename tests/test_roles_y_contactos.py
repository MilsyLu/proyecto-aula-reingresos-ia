"""Permisos asistenciales, histórico de llamadas y organización web."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from api import autenticacion, seguimiento

RAIZ = Path(__file__).resolve().parents[1]


class PermisosAsistencialesTest(unittest.TestCase):
    def test_personal_asistencial_no_ve_laboratorio(self):
        p = autenticacion.PERMISOS["clinico"]
        for nombre in ("Guía", "Estimar riesgo", "Seguimiento", "Asistente"):
            self.assertIn(nombre, p)
        for nombre in ("Cargar archivo", "Fijar umbral", "Comparar modelos",
                       "Recorrido grabado", "Desempeño", "Mapa de calor", "Reportes"):
            self.assertNotIn(nombre, p)

    def test_coordinacion_conserva_laboratorio_y_operacion(self):
        p = autenticacion.PERMISOS["coordinador"]
        for nombre in ("Seguimiento", "Cargar archivo", "Fijar umbral",
                       "Reportes", "Comparar modelos", "Recorrido grabado"):
            self.assertIn(nombre, p)

    def test_menu_cuatro_opciones_asistenciales(self):
        rutas = (RAIZ / "web/src/rutas.tsx").read_text(encoding="utf-8")
        self.assertIn("ruta: 'panel'", rutas)
        self.assertIn("ruta: 'seguimiento'", rutas)
        self.assertIn("ruta: 'estimar'", rutas)
        self.assertIn("ruta: 'agenda'", rutas)
        self.assertIn("ocultarEnMenu: true", rutas)
        app = (RAIZ / "web/src/App.tsx").read_text(encoding="utf-8")
        self.assertIn("PermisoRuta", app)
        self.assertIn("sesion.permisos.includes(permiso)", app)


class HistorialContactosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        carpeta = Path(self.tmp.name)
        parch_carpeta = patch.object(seguimiento, "CARPETA", carpeta)
        parch_archivo = patch.object(seguimiento, "ARCHIVO", carpeta / "seguimiento.db")
        parch_carpeta.start()
        parch_archivo.start()
        self.addCleanup(parch_carpeta.stop)
        self.addCleanup(parch_archivo.stop)
        seguimiento.preparar()
        with seguimiento.conexion() as db:
            db.execute(
                """INSERT INTO seguimiento
                   (creado, registrado_por, nombre, entradas,
                    probabilidad, umbral, alerta)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("2026-11-24", "demo", "Paciente de prueba", json.dumps({}),
                 .4, .2, 1),
            )
            self.identificador = int(db.execute(
                "SELECT id FROM seguimiento LIMIT 1"
            ).fetchone()["id"])

    def test_contactos_no_sobrescriben_anteriores(self):
        usuario = {"usuario": "coordinador"}
        seguimiento.registrar_contacto(
            self.identificador,
            seguimiento.NuevoContacto(
                resultado="sin_respuesta", observaciones="No contestó"
            ),
            sesion=usuario,
        )
        seguimiento.registrar_contacto(
            self.identificador,
            seguimiento.NuevoContacto(
                resultado="contactado", observaciones="Llamada completada"
            ),
            sesion=usuario,
        )
        r = seguimiento.contactos(self.identificador, _=usuario)
        self.assertEqual(len(r["contactos"]), 2)
        self.assertEqual(r["contactos"][0]["observaciones"], "Llamada completada")
        self.assertEqual(r["contactos"][1]["observaciones"], "No contestó")
        with seguimiento.conexion() as db:
            estado = db.execute(
                "SELECT estado FROM seguimiento WHERE id = ?", (self.identificador,)
            ).fetchone()["estado"]
        self.assertEqual(estado, "contactado")

    def test_reprogramar_exige_fecha(self):
        with self.assertRaises(HTTPException) as ex:
            seguimiento.registrar_contacto(
                self.identificador,
                seguimiento.NuevoContacto(resultado="reprogramar"),
                sesion={"usuario": "coordinador"},
            )
        self.assertEqual(ex.exception.status_code, 422)

    def test_contactos_de_pacientes_son_independientes(self):
        with seguimiento.conexion() as db:
            db.execute(
                """INSERT INTO seguimiento
                   (creado, registrado_por, nombre, entradas,
                    probabilidad, umbral, alerta)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                ("2026-11-24", "demo", "Otro paciente", "{}", .1, .2, 0),
            )
            segundo = int(db.execute(
                "SELECT MAX(id) AS id FROM seguimiento"
            ).fetchone()["id"])
        seguimiento.registrar_contacto(
            self.identificador, seguimiento.NuevoContacto(resultado="contactado"),
            sesion={"usuario": "coordinador"},
        )
        self.assertEqual(len(seguimiento.contactos(segundo, _={})["contactos"]), 0)


if __name__ == "__main__":
    unittest.main()
