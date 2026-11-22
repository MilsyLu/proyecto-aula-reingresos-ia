"""Pruebas estructurales de la experiencia ReingresaIA.

Se comprueba que se mantengan rutas y permisos; hace falta la prueba visual
con Streamlit en un navegador para validar definitivamente el diseño.
"""
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parents[1]


class NavegacionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (RAIZ / "app" / "app.py").read_text(encoding="utf-8")
        cls.css = (RAIZ / "app" / "estilo.py").read_text(encoding="utf-8")
        cls.portada = (RAIZ / "app" / "paginas" / "portada.py").read_text(
            encoding="utf-8"
        )
        cls.lab = (RAIZ / "app" / "paginas" / "laboratorio.py").read_text(
            encoding="utf-8"
        )

    def test_identidad_y_navegacion_directa(self):
        self.assertIn('INICIO = "Archivo y lista de llamadas" if COORDINADOR else "Estimar un paciente"', self.app)
        self.assertIn('"EMPEZAR AQUÍ": ["Qué es esto"]', self.app)
        self.assertIn('"TRABAJAR": ["Estimar un paciente"]', self.app)
        self.assertIn('st.session_state["reia_pagina"]', self.app)
        self.assertIn('st.session_state["reia_menu_abierto"] = False', self.app)
        self.assertIn('key="alternar_menu_movil"', self.app)
        self.assertIn("ReingresaIA", self.app)
        self.assertIn("ReingresaIA", self.portada)

    def test_roles_y_funciones_no_se_pierden(self):
        self.assertIn("COORDINADOR = auth.es_coordinador()", self.app)
        self.assertIn('auth.exige("Laboratorio de modelos")', self.app)
        self.assertIn('auth.exige("Cargar archivo")', self.app)
        self.assertIn('auth.exige("Ficha del modelo")', self.app)
        self.assertIn("from paginas import estimar", self.app)
        self.assertIn("from paginas import lote", self.app)
        self.assertIn("from paginas import desempeno", self.app)
        self.assertIn("from paginas import equidad", self.app)

    def test_sidebar_siempre_recuperable(self):
        self.assertNotIn(
            'height: 0;',
            self.css.split("OCULTAR_CROMO")[1].split('"""')[1],
        )
        self.assertNotIn('[data-testid="stSidebar"] {{ display: none; }}', self.css)
        self.assertIn("stSidebarCollapsedControl", self.css)
        self.assertIn("initial_sidebar_state=", self.app)

    def test_laboratorio_tiene_cinco_etapas_y_resultados(self):
        for etiqueta in (
            "1 · Datos", "2 · Preparación", "3 · Entrenamiento",
            "4 · Comparación", "5 · Interpretación",
        ):
            self.assertIn(etiqueta, self.lab)
        self.assertIn('st.session_state["lab_datos"]', self.lab)
        self.assertIn('st.session_state["lab_resultado"]', self.lab)
        self.assertIn('_explicacion_sencilla(guardado["resultado"])', self.lab)
        self.assertIn('resultado["comparacion"]', self.lab)
        self.assertIn("entrenar_experimento(", self.lab)


if __name__ == "__main__":
    unittest.main()
