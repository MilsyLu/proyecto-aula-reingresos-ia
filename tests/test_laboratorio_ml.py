"""Pruebas del laboratorio de Machine Learning (sin dataset UCI real)."""
import unittest

import numpy as np
import pandas as pd

from src.laboratorio_ml import (
    DatosEntrenamientoInvalidos, entrenar_experimento,
    obtener_etiquetas, particionar,
)


class LaboratorioMLTest(unittest.TestCase):
    def setUp(self):
        # Cada paciente tiene dos hospitalizaciones; la partición debe
        # mantener juntas ambas filas y representar las dos clases.
        self.pacientes = pd.Series(np.repeat(np.arange(120), 2))
        self.y = pd.Series(np.repeat((np.arange(120) % 4 == 0).astype(int), 2))
        rng = np.random.default_rng(17)
        self.X = pd.DataFrame({
            "time_in_hospital": rng.integers(1, 15, len(self.y)).astype(float),
            "num_medications": rng.integers(1, 40, len(self.y)).astype(float),
            "gender": np.where(self.pacientes % 2, "Male", "Female"),
        })

    def test_etiquetas_uci(self):
        d = pd.DataFrame({"readmitted": ["<30", "NO", ">30"]})
        self.assertEqual(obtener_etiquetas(d).tolist(), [1, 0, 0])

    def test_rechaza_csv_sin_etiquetas(self):
        with self.assertRaises(DatosEntrenamientoInvalidos):
            obtener_etiquetas(pd.DataFrame({"gender": ["Female"]}))

    def test_ningun_paciente_compartido(self):
        ids = particionar(self.X, self.y, self.pacientes)
        grupos = [
            set(self.pacientes.iloc[ids[k]])
            for k in ("entrenamiento", "validacion", "prueba")
        ]
        self.assertTrue(grupos[0].isdisjoint(grupos[1]))
        self.assertTrue(grupos[0].isdisjoint(grupos[2]))
        self.assertTrue(grupos[1].isdisjoint(grupos[2]))
        self.assertEqual(sum(len(x) for x in ids.values()), len(self.X))

    def test_entrenamiento_comparado(self):
        resultado = entrenar_experimento(
            self.X, self.y, self.pacientes,
            numericas=["time_in_hospital", "num_medications"],
            categoricas=["gender"],
            neuronas=8, iteraciones=30,
        )
        modelos = set(resultado["comparacion"]["modelo"])
        self.assertEqual(modelos, {
            "Mayoritario", "Regresion logistica", "Red neuronal MLP"
        })
        self.assertEqual(resultado["particiones"]["registros"].sum(), len(self.X))
        self.assertTrue(0 <= resultado["prueba"]["AP"] <= 1)
        self.assertTrue(0 <= resultado["umbral"] <= 1)
        self.assertEqual(
            sum(resultado["prueba"][k] for k in ("VP", "FN", "FP", "VN")),
            len(resultado["predicciones_prueba"]),
        )


if __name__ == "__main__":
    unittest.main()
