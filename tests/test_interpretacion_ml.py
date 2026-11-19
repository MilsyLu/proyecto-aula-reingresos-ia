"""La explicación debe cambiar con los resultados, no inventar un ganador."""
import unittest
import pandas as pd

from src.interpretacion_ml import resumen_comprensible, informe_texto


def datos(ganador="Gradient Boosting", prueba_invertida=False):
    ap_gb = 0.24 if not prueba_invertida else 0.18
    ap_mlp = 0.21 if not prueba_invertida else 0.28
    return {
        "elegido": ganador,
        "comparacion": pd.DataFrame([
            {"modelo": "Gradient Boosting",
             "AP_validacion": 0.25, "AP_prueba": ap_gb,
             "VP": 6, "FN": 4, "FP": 24, "VN": 66,
             "recall_prueba": 0.6, "precision_prueba": 0.2},
            {"modelo": "Red neuronal MLP",
             "AP_validacion": 0.22, "AP_prueba": ap_mlp,
             "VP": 8, "FN": 2, "FP": 32, "VN": 58,
             "recall_prueba": 0.8, "precision_prueba": 0.2},
        ]),
    }


class InterpretacionMLTest(unittest.TestCase):
    def test_justifica_ganador_con_validacion(self):
        resumen = resumen_comprensible(datos())
        self.assertEqual(resumen["ganador"], "Gradient Boosting")
        self.assertIn("25,0 %", resumen["seleccion"])
        self.assertIn("22,0 %", resumen["seleccion"])
        self.assertIn("Gradient Boosting", resumen["prueba"])
        self.assertEqual(resumen["filas_prueba"], 100)

    def test_alertas_por_modelo_se_explica_en_prosa(self):
        resumen = resumen_comprensible(datos())
        self.assertEqual(len(resumen["decisiones"]), 2)
        texto = resumen["decisiones"][0]["texto"]
        self.assertIn("6", texto)
        self.assertIn("24", texto)
        self.assertEqual(resumen["decisiones"][0]["recall"], "60,0 %")

    def test_no_cambia_el_ganador_por_resultado_de_prueba(self):
        resumen = resumen_comprensible(datos(prueba_invertida=True))
        self.assertEqual(resumen["ganador"], "Gradient Boosting")
        self.assertIn("Red neuronal MLP", resumen["prueba"])
        self.assertIn("no se cambia", resumen["prueba"])

    def test_reporte_descargable_incluye_glosario_y_limites(self):
        texto = informe_texto(datos())
        self.assertIn("Falso negativo", texto)
        self.assertIn("LIMITACIONES", texto)
        self.assertIn("Gradient Boosting", texto)

    def test_comparacion_incompleta_se_rechaza(self):
        incompleto = datos()
        incompleto["comparacion"] = incompleto["comparacion"].iloc[:1]
        with self.assertRaises(ValueError):
            resumen_comprensible(incompleto)


if __name__ == "__main__":
    unittest.main()
