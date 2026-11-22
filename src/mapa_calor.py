# -*- coding: utf-8 -*-
"""Cruza las dos variables que más pesan y mide la tasa real de cada celda.

Según la importancia por permutación, `number_inpatient` explica el 25,1 % de
la precisión media y `discharge_disposition_id` el 18,4 %. Entre las dos se
llevan el 43,5 %: cruzarlas no es una elección estética, es mirar donde está
casi la mitad de la señal.

Cada celda trae la proporción **real** de reingresos de los pacientes que caen
ahí, no una predicción. Eso es lo que la hace defendible: no se está mostrando
lo que el modelo cree, sino lo que de verdad pasó.

Se precalcula porque `data/processed/` no se versiona y en el servidor no
existe. El resultado pesa unos pocos kilobytes.

Genera:
  reports/mapa_calor.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

# Los siete egresos que de verdad ocurren. Los demás son casos sueltos y una
# celda con cuatro pacientes no dice nada: mostrarla sería invitar a leer ruido.
EGRESOS = {
    "1": "A casa",
    "3": "Centro de enfermería",
    "6": "A casa con atención domiciliaria",
    "2": "Traslado a otro hospital",
    "22": "Rehabilitación",
    "5": "Otra institución",
    "4": "Cuidado intermedio",
}

TRAMOS = [(-1, 0, "0"), (0, 1, "1"), (1, 2, "2"), (2, 100, "3 o más")]

MINIMO_CELDA = 30  # por debajo de esto la proporción no es confiable


def main():
    proc = pd.read_csv(BASE / "data/processed/cohorte_procesada.csv", low_memory=False)

    # El código de egreso puede venir como 6 o como 6.0 según lo que pandas
    # adivine al leer; normalizar evita perder filas por una coma decimal.
    proc["egreso"] = (
        proc.discharge_disposition_id.astype(str).str.replace(r"\.0$", "", regex=True)
    )
    proc = proc[proc.egreso.isin(EGRESOS)]

    base = float(proc.y.mean())
    filas = []

    for codigo, nombre in EGRESOS.items():
        del_egreso = proc[proc.egreso == codigo]
        for bajo, alto, etiqueta in TRAMOS:
            celda = del_egreso[
                (del_egreso.number_inpatient > bajo) & (del_egreso.number_inpatient <= alto)
            ]
            if len(celda) == 0:
                continue
            tasa = float(celda.y.mean())
            filas.append({
                "egreso": nombre,
                "codigo": codigo,
                "previas": etiqueta,
                "casos": int(len(celda)),
                "reingresos": int(celda.y.sum()),
                "tasa": round(tasa, 4),
                "veces_la_base": round(tasa / base, 2) if base else 0.0,
                "confiable": len(celda) >= MINIMO_CELDA,
            })

    tabla = pd.DataFrame(filas)
    # Las filas se ordenan por cuántos pacientes tienen: arriba los egresos
    # frecuentes, que es por donde cualquiera empieza a leer.
    orden = tabla.groupby("egreso").casos.sum().sort_values(ascending=False)
    tabla["orden"] = tabla.egreso.map({n: i for i, n in enumerate(orden.index)})
    tabla = tabla.sort_values(["orden", "previas"]).drop(columns="orden")

    destino = BASE / "reports" / "mapa_calor.csv"
    tabla.to_csv(destino, index=False)

    print(f"{len(proc):,} hospitalizaciones en {len(tabla)} celdas".replace(",", "."))
    print(f"tasa general {base * 100:.2f} %")
    print(f"celda más fría  {tabla.tasa.min() * 100:5.1f} %")
    print(f"celda más caliente {tabla.tasa.max() * 100:5.1f} %  "
          f"({tabla.tasa.max() / tabla.tasa.min():.1f} veces más)")
    pocas = (~tabla.confiable).sum()
    if pocas:
        print(f"celdas con menos de {MINIMO_CELDA} pacientes: {pocas} (marcadas como no confiables)")
    else:
        print(f"todas las celdas superan los {MINIMO_CELDA} pacientes")
    print(f"\n{destino.relative_to(BASE)}: {destino.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
