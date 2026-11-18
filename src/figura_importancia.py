# -*- coding: utf-8 -*-
import sys
import pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(r"C:\Users\ASUS\Documents\UPC\proyecto-reingresos")
imp = pd.read_csv(BASE / "reports/importancia_permutacion.csv").head(15).iloc[::-1]

NOMBRES = {
    "number_inpatient": "Hospitalizaciones previas (1 ano)",
    "discharge_disposition_id": "Tipo de egreso",
    "medical_specialty": "Especialidad que atiende",
    "grupo_diag_2": "Diagnostico secundario (grupo)",
    "servicios_previos": "Servicios previos (derivada)",
    "grupo_diag_1": "Diagnostico principal (grupo)",
    "admission_type_id": "Tipo de ingreso",
    "admission_source_id": "Origen del ingreso",
    "number_emergency": "Visitas a urgencias (1 ano)",
    "grupo_diag_3": "Diagnostico adicional (grupo)",
    "num_meds_activos": "Medicamentos activos (derivada)",
    "metformin": "Metformina",
    "insulin": "Insulina",
    "num_medications": "Medicamentos administrados",
    "edad_num": "Edad",
}
imp["etiqueta"] = imp.variable.map(lambda v: NOMBRES.get(v, v))
colores = ["#C25A3C" if v in ("number_inpatient", "discharge_disposition_id")
           else "#1F3B63" for v in imp.variable]

fig, ax = plt.subplots(figsize=(8.2, 5.0), dpi=200)
b = ax.barh(imp.etiqueta, imp.pct_del_AP, color=colores, height=0.72)
etqs = [f"{v:.1f} %".replace(".", ",") for v in imp.pct_del_AP]
ax.bar_label(b, labels=etqs, padding=3, fontsize=8, color="#15202B")
ax.set_xlabel("Caida del AP al desordenar la variable  (% del AP total del modelo)", fontsize=9)
ax.set_xlim(0, 29)
ax.tick_params(labelsize=8.5)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.25, lw=0.6)
ax.set_axisbelow(True)
ax.set_title("Importancia por permutacion  ·  15 variables principales de 50\n"
             "conjunto de prueba (n = 19.870), 5 repeticiones",
             fontsize=10.5, loc="left", pad=10, color="#15202B")
fig.text(0.985, 0.015, "En naranja: las dos variables administrativas que concentran el 43,5 % del desempeno.",
         ha="right", fontsize=7.5, color="#5A6472")
fig.tight_layout(rect=[0, 0.035, 1, 1])
out = BASE / "reports/figures/05_importancia.png"
fig.savefig(out, bbox_inches="tight")
print("guardada:", out, out.stat().st_size, "bytes")
