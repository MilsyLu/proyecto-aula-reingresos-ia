"""Comprobaciones de estructura para la navegación Streamlit.

Estas pruebas no sustituyen una prueba visual con navegador.
"""
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parents[1]


class NavegacionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (RAIZ / "app" / "app.py").read_text(encoding="utf-8")
        cls.css = (RAIZ / "app" / "estilo.py").read_text(encoding="utf-8")

    def test_solo_dos_areas_principales(self):
        self.assertIn('CLIENTE = "Resultados para el cliente"', self.app)
        self.assertIn('ADMIN = "Laboratorio y evaluación"', self.app)
        self.assertIn("options=areas", self.app)
        self.assertNotIn('st.sidebar.radio("Secciones"', self.app)

    def test_laboratorio_exclusivo_coordinador(self):
        self.assertIn("if auth.es_coordinador()", self.app)
        self.assertIn('auth.exige("Laboratorio de modelos")', self.app)
        self.assertIn('auth.exige("Cargar archivo")', self.app)

    def test_cliente_tiene_consulta_individual(self):
        self.assertIn("from paginas import estimar", self.app)
        self.assertIn("estimar.render()", self.app)
        self.assertIn("from paginas import lote", self.app)

    def test_control_apertura_no_se_oculta(self):
        self.assertNotIn('height: 0;', self.css.split("OCULTAR_CROMO")[1].split('"""')[1])
        self.assertIn("stSidebarCollapsedControl", self.css)
        self.assertIn("initial_sidebar_state=", self.app)


if __name__ == "__main__":
    unittest.main()
