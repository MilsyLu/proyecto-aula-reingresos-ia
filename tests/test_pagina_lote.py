# -*- coding: utf-8 -*-
"""Recorre la página de cargue de principio a fin, con un Streamlit de mentira.

Por qué existe: los fallos de esta página solo aparecen cuando hay un archivo
subido, y esa rama no se ejecuta ni al revisar la sintaxis ni al abrir la
aplicación sin archivo. Asi se colaron un nombre de función duplicado y un icono
que Streamlit no acepta, los dos descubiertos por el usuario y no por las pruebas.

El doble de Streamlit no dibuja nada: solo deja que el código corra y apunta las
llamadas, para poder comprobar que ninguna revienta y que el contenido es el
esperado.
"""
from __future__ import annotations

import io
import sys
import types
import unittest
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent


class Columna:
    """Una columna de Streamlit: se usa como objeto y como gestor de contexto."""

    def __init__(self, diario):
        self.diario = diario

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def __getattr__(self, nombre):
        def llamada(*args, **kwargs):
            self.diario.append((nombre, args, kwargs))
            return None
        return llamada


class Contexto:
    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def streamlit_de_mentira(diario, respuestas):
    """`respuestas` fija lo que devuelven los controles (botones, campos...)."""
    st = types.ModuleType("streamlit")
    st.session_state = {}

    def anotar(nombre, devuelve=None):
        def llamada(*args, **kwargs):
            diario.append((nombre, args, kwargs))
            return respuestas.get(nombre, devuelve)
        return llamada

    for nombre in ("title", "subheader", "header", "markdown", "caption", "write",
                   "divider", "error", "warning", "success", "info", "dataframe",
                   "table", "code", "metric", "progress", "bar_chart", "json"):
        setattr(st, nombre, anotar(nombre))

    st.columns = lambda spec, **k: [Columna(diario)
                                    for _ in range(spec if isinstance(spec, int) else len(spec))]
    st.tabs = lambda nombres, **k: [Columna(diario) for _ in nombres]
    st.expander = lambda *a, **k: (diario.append(("expander", a, k)), Contexto())[1]
    st.spinner = lambda *a, **k: Contexto()
    st.form = lambda *a, **k: Contexto()
    st.container = lambda *a, **k: Contexto()
    st.chat_message = lambda *a, **k: Contexto()
    st.button = anotar("button", False)
    st.download_button = anotar("download_button", False)
    st.form_submit_button = anotar("form_submit_button", False)
    st.file_uploader = anotar("file_uploader", None)
    st.number_input = anotar("number_input", 1)
    st.selectbox = anotar("selectbox", None)
    st.radio = anotar("radio", None)
    st.slider = anotar("slider", 0.1)
    st.chat_input = anotar("chat_input", None)
    st.stop = lambda: None
    st.rerun = lambda: None
    st.set_page_config = lambda **k: None
    st.secrets = {}
    st.cache_data = lambda **k: (lambda f: f)
    st.cache_resource = lambda **k: (lambda f: f)
    return st


class ArchivoDeMentira:
    """Lo que devuelve st.file_uploader."""

    def __init__(self, contenido: bytes):
        self._contenido = contenido
        self.size = len(contenido)
        self.name = "prueba.csv"

    def getvalue(self):
        return self._contenido


def correr_pagina(csv: bytes, capacidad=50, pulsa_boton=True):
    """Ejecuta `lote.render()` de principio a fin y devuelve lo que dibujó."""
    diario = []
    respuestas = {"file_uploader": ArchivoDeMentira(csv),
                  "number_input": capacidad,
                  "button": pulsa_boton}
    st = streamlit_de_mentira(diario, respuestas)

    guardados = {n: sys.modules.pop(n, None)
                 for n in list(sys.modules) if n.startswith(("streamlit", "datos", "estilo",
                                                             "paginas", "src."))}
    sys.modules["streamlit"] = st
    for ruta in (str(RAIZ), str(RAIZ / "app")):
        if ruta not in sys.path:
            sys.path.insert(0, ruta)
    try:
        import importlib
        import paginas.lote as lote
        importlib.reload(lote)
        lote.render()
        # el botón ya guardó el resultado; una segunda pasada dibuja la lista
        lote.render()
    finally:
        for nombre, modulo in guardados.items():
            if modulo is not None:
                sys.modules[nombre] = modulo
    return diario


def textos(diario):
    """Todo lo que la página mandó dibujar, argumentos y opciones incluidos."""
    partes = []
    for _, args, kwargs in diario:
        partes.extend(str(a) for a in args)
        partes.extend(f"{k}={v}" for k, v in kwargs.items())
    return " ".join(partes)


class CargueDeArchivos(unittest.TestCase):

    def test_archivo_ajeno_se_procesa_y_avisa_la_cobertura(self):
        """Un CSV con otros nombres de columna: se aprovecha lo que se reconozca."""
        datos = pd.DataFrame({
            "age": [65, 72, 48, 80, 55] * 4,
            "gender": ["Female", "Male"] * 10,
            "num_previous_admissions": [0, 3, 1, 5, 2] * 4,
            "length_of_stay": [4, 9, 2, 14, 6] * 4,
            "medications_count": [12, 20, 8, 25, 15] * 4,
            "procedures_count": [1, 3, 0, 2, 1] * 4,
            "chronic_conditions": [5, 9, 3, 8, 6] * 4,
            "algo_que_no_existe": list(range(20)),
        })
        diario = correr_pagina(datos.to_csv(index=False).encode("utf-8"), capacidad=5)
        todo = textos(diario)

        self.assertNotIn("No se pudo procesar", todo)
        self.assertIn("Cobertura del modelo", todo)
        self.assertIn("A quién llamar primero", todo)
        # la lista priorizada llega hasta el final, con su descarga
        self.assertIn("Descargar la lista de", todo)
        self.assertIn("lista_de_seguimiento.csv", todo)

    def test_sin_ninguna_columna_reconocida_no_predice(self):
        """Si nada se reconoce, el modelo daría el mismo número a todos."""
        datos = pd.DataFrame({"columna_a": range(10), "columna_b": list("abcdefghij")})
        diario = correr_pagina(datos.to_csv(index=False).encode("utf-8"))
        todo = textos(diario)

        self.assertIn("No se reconoció", todo)
        self.assertNotIn("A quién llamar primero", todo)

    def test_el_archivo_original_de_uci_usa_el_camino_estricto(self):
        crudo = RAIZ / "data" / "raw" / "diabetic_data.csv"
        if not crudo.exists():
            self.skipTest("el archivo original de UCI no está en esta máquina")
        muestra = pd.read_csv(crudo, nrows=60, low_memory=False)
        diario = correr_pagina(muestra.to_csv(index=False).encode("utf-8"), capacidad=10)
        todo = textos(diario)

        self.assertNotIn("No se pudo procesar", todo)
        self.assertIn("Archivo original", todo)
        self.assertIn("A quién llamar primero", todo)
        # con el esquema completo no hace falta la tarjeta de cobertura
        self.assertNotIn("Cobertura del modelo", todo)

    def test_ningun_icono_invalido(self):
        """Streamlit solo acepta un emoji o ':material/...:' en icon=."""
        import re
        for ruta in (RAIZ / "app").rglob("*.py"):
            texto = ruta.read_text(encoding="utf-8")
            for encontrado in re.finditer(r'icon\s*=\s*"([^"]*)"', texto):
                valor = encontrado.group(1)
                self.assertTrue(
                    valor.startswith(":material/") or len(valor) <= 2,
                    f"{ruta.name}: icon={valor!r} no es un emoji ni un icono de Material")


if __name__ == "__main__":
    unittest.main()
