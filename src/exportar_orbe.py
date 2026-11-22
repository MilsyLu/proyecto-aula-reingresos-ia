# -*- coding: utf-8 -*-
"""Prepara los datos del orbe de la portada.

El orbe de la portada no es un adorno: cada una de sus partículas es una
hospitalización real del conjunto de prueba, con el riesgo que le calculó el
modelo y lo que de verdad pasó después. Eso convierte la primera pantalla en el
dato mismo, y permite responder «¿qué representa eso?» con algo distinto de
«nada, es decoración».

Se exporta una muestra aleatoria con semilla fija, no las 19.870 filas: en el
navegador 3.600 partículas ya saturan la vista, y bajar el peso del archivo
importa porque esto carga antes que nada.

Genera:
  web/public/cohorte.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

PARTICULAS = 3600
SEMILLA = 42


def main():
    prueba = pd.read_csv(BASE / "reports/predicciones_prueba.csv")
    umbral = json.loads((BASE / "reports/umbral_elegido.json").read_text(encoding="utf-8"))["umbral"]

    # Muestra aleatoria simple: conserva la distribución de riesgo y la
    # prevalencia sin necesidad de estratificar.
    muestra = prueba.sample(n=min(PARTICULAS, len(prueba)), random_state=SEMILLA)
    muestra = muestra.sort_values("probabilidad").reset_index(drop=True)

    riesgo = muestra.probabilidad.round(4).tolist()
    reingreso = muestra.reingreso_real.astype(int).tolist()

    datos = {
        "particulas": len(muestra),
        "umbral": round(float(umbral), 6),
        "riesgo": riesgo,
        "reingreso": reingreso,
        "contexto": {
            "origen": "conjunto de prueba, muestra aleatoria con semilla fija",
            "prueba_filas": int(len(prueba)),
            "prueba_prevalencia": round(float(prueba.reingreso_real.mean()), 4),
            "muestra_prevalencia": round(float(muestra.reingreso_real.mean()), 4),
            "riesgo_minimo": round(float(muestra.probabilidad.min()), 4),
            "riesgo_maximo": round(float(muestra.probabilidad.max()), 4),
        },
    }

    destino = BASE / "web" / "public" / "cohorte.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    # separators sin espacios: son 7.200 números, cada byte cuenta.
    destino.write_text(json.dumps(datos, separators=(",", ":")), encoding="utf-8")

    c = datos["contexto"]
    print(f"{len(muestra):,} partículas de {c['prueba_filas']:,} del conjunto de prueba"
          .replace(",", "."))
    print(f"prevalencia  prueba {c['prueba_prevalencia']:.4f}  "
          f"muestra {c['muestra_prevalencia']:.4f}")
    print(f"riesgo  de {c['riesgo_minimo']:.4f} a {c['riesgo_maximo']:.4f}  "
          f"umbral {umbral:.4f}")
    print(f"reingresaron {sum(reingreso):,} de {len(reingreso):,}".replace(",", "."))
    print(f"\n{destino.relative_to(BASE)}: {destino.stat().st_size / 1024:.1f} KB")

    # Si la muestra se aleja mucho de la prevalencia real, el orbe estaria
    # contando otra historia. Mejor enterarse aqui que en la sustentacion.
    desvio = abs(c["muestra_prevalencia"] - c["prueba_prevalencia"])
    if desvio > 0.015:
        print(f"\nAVISO: la muestra se aparta {desvio:.4f} de la prevalencia real.")
    else:
        print(f"la muestra representa bien a la cohorte (se aparta {desvio:.4f})")


if __name__ == "__main__":
    main()
