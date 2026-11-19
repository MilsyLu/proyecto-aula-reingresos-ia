"""Pruebas para la preparación de archivos de UCI y CSV ya transformados."""
import unittest
import pandas as pd

import numpy as np

from src.procesamiento_lotes import (
    ArchivoIncompatible, a_texto, agrupar_diagnostico, categorias_no_vistas,
    detectar_formato, preparar_lote, predecir_lote,
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

    def test_un_vacio_no_convierte_el_codigo_en_decimal(self):
        """Un solo vacio hacia que pandas leyera la columna como float y el
        codigo 6 llegara al modelo como '6.0', una categoria que no conoce."""
        serie = pd.Series([6, 1, None, 3])
        salida = a_texto(serie)
        self.assertEqual(list(salida.dropna()), ["6", "1", "3"])
        self.assertTrue(salida.isna().iloc[2])

    def test_el_vacio_de_texto_se_deja_vacio(self):
        """El pipeline entrenado rellena los vacios con 'Ausente'. Si aqui se
        escribiera 'nan', el codificador lo mandaria a -1 sin avisar."""
        salida = a_texto(pd.Series(["Cardiology", None, "Surgery"]))
        self.assertTrue(salida.isna().iloc[1])
        self.assertNotIn("nan", [str(v) for v in salida.dropna()])

    def test_categorias_no_vistas_detecta_lo_desconocido(self):
        class Enc:
            categories_ = [np.array(["1", "2", "3"])]

        class Paso:
            named_steps = {"ordinal": Enc()}
            steps = [("ordinal", Enc())]

        class Prep:
            transformers_ = [("categoricas", Paso(), ["codigo"])]

        class Modelo:
            named_steps = {"prep": Prep()}

        X = pd.DataFrame({"codigo": ["1", "9", "9", "2"]})
        self.assertEqual(categorias_no_vistas(Modelo(), X, ["codigo"]),
                         {"codigo": {"9": 2}})


if __name__ == "__main__":
    unittest.main()
