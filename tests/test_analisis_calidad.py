"""Pruebas del EDA descriptivo: no se eliminan datos ni se usan etiquetas para predecir."""
import unittest

import numpy as np
import pandas as pd

from src.analisis_calidad import (
    resumen_calidad, resumen_numericas, distribucion_objetivo,
)


class AnalisisCalidadTest(unittest.TestCase):
    def test_faltantes_y_duplicados(self):
        df = pd.DataFrame({
            "gender": ["Female", "Female", "?"],
            "time_in_hospital": [3, 3, 5],
        })
        resumen = resumen_calidad(df)
        self.assertEqual(resumen["filas"], 3)
        self.assertEqual(resumen["duplicados"], 1)
        fila = resumen["tabla"].set_index("columna").loc["gender"]
        self.assertEqual(fila["faltantes"], 1)

    def test_variables_numericas_y_outliers(self):
        df = pd.DataFrame({"time_in_hospital": [1, 2, 2, 3, 100]})
        estadisticas, atipicos = resumen_numericas(df)
        self.assertEqual(len(estadisticas), 1)
        self.assertEqual(atipicos.iloc[0]["posibles_atipicos_IQR"], 1)
        self.assertEqual(df.iloc[-1]["time_in_hospital"], 100)

    def test_objetivo_opcional(self):
        sin_etiqueta = distribucion_objetivo(pd.DataFrame({"gender": ["Male"]}))
        self.assertTrue(sin_etiqueta.empty)
        con_etiqueta = distribucion_objetivo(
            pd.DataFrame({"readmitted": ["<30", "NO", ">30", "<30"]})
        )
        self.assertEqual(con_etiqueta["registros"].sum(), 4)

    def test_valores_faltantes_no_eliminan_columnas(self):
        df = pd.DataFrame({"time_in_hospital": [np.nan, "?", 7]})
        calidad = resumen_calidad(df)
        self.assertEqual(calidad["celdas_faltantes"], 2)
        estadisticas, _ = resumen_numericas(df)
        self.assertEqual(estadisticas.iloc[0]["n"], 1)


if __name__ == "__main__":
    unittest.main()
