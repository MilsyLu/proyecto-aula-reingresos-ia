# -*- coding: utf-8 -*-
"""Fija las cifras de la comparación Gradient Boosting contra red neuronal.

El laboratorio de Iván (`src/laboratorio_ml.py`) entrena los dos modelos en vivo y
no guarda nada: cada vez que alguien abre la pantalla se vuelve a calcular. Eso
está bien para un laboratorio, pero la pantalla «qué modelos probamos» necesita
un número citable, que no cambie entre una visita y otra.

Este script corre el experimento una sola vez, con semilla fija y las tres
configuraciones por algoritmo, y deja el resultado en `reports/`.

Genera:
  reports/metricas_06_mlp.csv        una fila por modelo, con prueba y sobreajuste
  reports/busqueda_06_laboratorio.csv  cada configuración probada y su brecha
  reports/curva_perdida_mlp.csv      la pérdida real de la red, iteración por iteración
  reports/particiones_06.csv         tamaño y prevalencia de cada conjunto
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

import laboratorio_ml as lab  # noqa: E402

SEMILLA = 42
BUSQUEDA = 3  # las tres configuraciones por algoritmo, para que sea una comparación justa


def main():
    cols = json.loads((BASE / "data/processed/columnas.json").read_text(encoding="utf-8"))
    NUM, CAT = cols["numericas"], cols["categoricas"]

    datos = pd.read_csv(BASE / "data/processed/cohorte_procesada.csv", low_memory=False)
    X = datos[NUM + CAT].copy()
    X[CAT] = X[CAT].astype(str)
    y = datos.y.astype(int)
    pacientes = datos.patient_nbr

    print(f"cohorte {len(X):,} filas, {X.shape[1]} columnas".replace(",", "."))
    print(f"semilla {SEMILLA}, {BUSQUEDA} configuraciones por algoritmo")
    print("entrenando (puede tardar unos minutos)...")

    inicio = time.time()
    r = lab.entrenar_experimento(X, y, pacientes, NUM, CAT,
                                 semilla=SEMILLA, busqueda=BUSQUEDA)
    print(f"listo en {time.time() - inicio:.1f} s\n")

    rep = BASE / "reports"
    comp = r["comparacion"]
    comp.to_csv(rep / "metricas_06_mlp.csv", index=False)
    r["busqueda"].to_csv(rep / "busqueda_06_laboratorio.csv", index=False)
    r["particiones"].to_csv(rep / "particiones_06.csv", index=False)

    curva = r["curvas"].get("Red neuronal MLP")
    if curva is not None:
        curva.to_csv(rep / "curva_perdida_mlp.csv", index=False)

    print(f"ganador: {r['elegido']}")
    print(r["justificacion"])
    print()
    for _, f in comp.iterrows():
        marca = "*" if f.seleccionado else " "
        print(f" {marca} {f.modelo:<22} AP prueba {f.AP_prueba:.4f}  "
              f"ROC-AUC {f.ROC_AUC_prueba:.4f}  brecha {f.brecha_AP:+.4f}")
    print()
    for nombre in ("metricas_06_mlp.csv", "busqueda_06_laboratorio.csv",
                   "particiones_06.csv", "curva_perdida_mlp.csv"):
        ruta = rep / nombre
        if ruta.exists():
            print(f"  {nombre}: {ruta.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
