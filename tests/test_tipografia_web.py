"""Guardas de legibilidad para la interfaz web de ReingresaIA.

Este test es estático; el contraste, el recorte y el responsive deben
verificarse visualmente después de iniciar React.
"""
from pathlib import Path
import re
import unittest


RAIZ = Path(__file__).resolve().parents[1]
CSS = RAIZ / "web" / "src" / "estilos.css"


class TipografiaWebTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        texto = CSS.read_text(encoding="utf-8")
        cls.interior = texto[texto.index(".zona-app {"):]

    def test_base_de_app_legible(self):
        base = self.interior.split(".zona-app {", 1)[1].split("}", 1)[0]
        self.assertRegex(base, r"font-size:\s*16px\s*;")
        self.assertIn("line-height: 1.55", base)

    def test_no_hay_fuentes_menores_de_trece_pixeles(self):
        valores = [
            float(v)
            for v in re.findall(r"font-size:\s*([\d.]+)px", self.interior)
        ]
        self.assertTrue(valores)
        self.assertGreaterEqual(min(valores), 13)

    def test_menu_y_tablas_legibles(self):
        self.assertIn("--ancho-barra: 280px", self.interior)
        menu = self.interior.split(".zona-app .barra-enlace {", 1)[1].split("}", 1)[0]
        self.assertIn("font-size: 15px;", menu)
        self.assertIn(".zona-app table { font-size: 15px;", self.interior)
        self.assertIn(".zona-app input,", self.interior)

    def test_instrucciones_de_ejecucion(self):
        guia = (RAIZ / "docs" / "ejecucion_local_reingresaia.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("8001", guia)
        self.assertIn("5173", guia)
        self.assertIn("requirements-api.txt", guia)
        self.assertIn("npm ci", guia)


if __name__ == "__main__":
    unittest.main()
