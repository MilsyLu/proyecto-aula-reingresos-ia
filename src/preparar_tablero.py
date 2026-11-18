# -*- coding: utf-8 -*-
"""Prepara el archivo que consume el tablero de Power BI.

Lo escribe con separador ';' y coma decimal para que Power BI en configuracion
regional de Colombia lo importe sin tener que tocar nada.
"""
import sys
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent
ENTRADA = BASE / "reports/predicciones_prueba.csv"
SALIDA = BASE / "reports/tablero_powerbi.csv"

d = pd.read_csv(ENTRADA)

# nombres legibles para que las visualizaciones no necesiten renombrar nada
d = d.rename(columns={
    "reingreso_real": "Reingreso real",
    "probabilidad": "Probabilidad",
    "alerta": "Alerta",
    "grupo_racial": "Grupo racial",
    "genero": "Genero",
    "grupo_edad": "Grupo de edad",
    "edad": "Edad",
    "dias_estancia": "Dias de estancia",
    "ingresos_previos": "Ingresos previos",
    "medicamentos": "Medicamentos",
    "diagnosticos": "Diagnosticos",
    "diagnostico_principal": "Diagnostico principal",
    "es_transferencia": "Es transferencia",
    "resultado": "Resultado",
})
d["Probabilidad"] = d.Probabilidad.round(6)
d["Tipo de egreso"] = d["Es transferencia"].map({1: "Transferido a otra institucion",
                                                 0: "Dado de alta a casa"})
d["Reingreso"] = d["Reingreso real"].map({1: "Si reingreso", 0: "No reingreso"})

# columna auxiliar: los grupos de edad no se ordenan bien alfabeticamente
# ("Menos de 50" quedaria al final). Power BI ordena por esta.
d["Orden edad"] = d["Grupo de edad"].map({"Menos de 50": 1, "50 a 60": 2,
                                          "60 a 70": 3, "70 a 80": 4, "80 o mas": 5})
d = d.drop(columns=["paciente", "egreso"])

d.to_csv(SALIDA, index=False, sep=";", decimal=",", encoding="utf-8-sig")
print(f"guardado: {SALIDA}")
print(f"{len(d):,} filas x {d.shape[1]} columnas".replace(",", "."))
print("columnas:", ", ".join(d.columns))
