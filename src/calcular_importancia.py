# -*- coding: utf-8 -*-
"""Importancia por permutacion sobre el conjunto de prueba (metrica: average precision)."""
import json, sys, time
import numpy as np, pandas as pd, joblib
from pathlib import Path
from sklearn.inspection import permutation_importance

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(r"C:\Users\ASUS\Documents\UPC\proyecto-reingresos")

proc = pd.read_csv(BASE / "data/processed/cohorte_procesada.csv", low_memory=False)
cols = json.loads((BASE / "data/processed/columnas.json").read_text(encoding="utf-8"))
NUM, CAT = cols["numericas"], cols["categoricas"]
proc[CAT] = proc[CAT].astype(str)

modelo = joblib.load(BASE / "models/gradient_boosting_ajustado.joblib")
d = proc[proc.conjunto == "prueba"]
X, y = d[NUM + CAT], d.y.values
print(f"prueba: {X.shape[0]} filas, {X.shape[1]} predictores")

t0 = time.time()
r = permutation_importance(modelo, X, y, scoring="average_precision",
                           n_repeats=5, random_state=42, n_jobs=-1)
print(f"listo en {time.time()-t0:.0f} s")

imp = (pd.DataFrame({"variable": X.columns,
                     "caida_AP": r.importances_mean,
                     "desv": r.importances_std})
       .sort_values("caida_AP", ascending=False).reset_index(drop=True))
imp["pct_del_AP"] = imp.caida_AP / 0.224942 * 100
imp.to_csv(BASE / "reports/importancia_permutacion.csv", index=False)
print(imp.head(20).to_string(index=False))
print("\nsuma de caidas positivas:", imp[imp.caida_AP > 0].caida_AP.sum().round(4))
print("variables con caida <= 0:", int((imp.caida_AP <= 0).sum()))
