"""Pruebas para la preparación de archivos de UCI y CSV ya transformados."""
import unittest
import pandas as pd

from src.procesamiento_lotes import (
    ArchivoIncompatible, agrupar_diagnostico, detectar_formato,
    preparar_lote, predecir_lote,
)


class ModeloFalso:
    def predict_proba(self, X):
        import numpy as np
        p = np.full(len(X), 0.2)
        return np.column_stack([1-p, p])


class LotesTest(unittest.TestCase):
    def setUp(self):
        self.numericas = ["time_in_hospital", "edad_num", "meds_por_dia"]
        self.categoricas = ["gender", "grupo_diag_1"]
        self.preparado = pd.DataFrame([
            {"time_in_hospital": 4, "edad_num": 65, "meds_por_dia": 3,
             "gender": "Female", "grupo_diag_1": "Diabetes"},
            {"time_in_hospital": 0, "edad_num": 55, "meds_por_dia": 2,
             "gender": "Male", "grupo_diag_1": "Otros"},
        ])

    def test_preparado_rechaza_estancia_invalida(self):
        X, descartes, resumen = preparar_lote(
            self.preparado, self.numericas, self.categoricas)
        self.assertEqual(resumen["validas"], 1)
        self.assertEqual(descartes.iloc[0]["fila_original"], 3)
        self.assertEqual(len(X), 1)

    def test_predicciones_conservan_numero_fila(self):
        X, _, _ = preparar_lote(
            self.preparado, self.numericas, self.categoricas)
        salida = predecir_lote(ModeloFalso(), X, 0.112346)
        self.assertEqual(salida.iloc[0]["fila_csv"], 2)
        self.assertEqual(salida.iloc[0]["alerta"], "Seguimiento")

    def test_esquema_invalido(self):
        with self.assertRaises(ArchivoIncompatible):
            detectar_formato(pd.DataFrame({"x": [1]}),
                            self.numericas, self.categoricas)

    def test_codigos_clinicos(self):
        self.assertEqual(agrupar_diagnostico("250.83"), "Diabetes")
        self.assertEqual(agrupar_diagnostico("V55"), "Otros")
        self.assertEqual(agrupar_diagnostico(None), "Desconocido")


if __name__ == "__main__":
    unittest.main()
