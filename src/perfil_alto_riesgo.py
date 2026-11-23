# -*- coding: utf-8 -*-
"""Qué tienen en común los pacientes que el modelo marca como de alto riesgo.

Lo pidió Michel para el módulo de reportes: no basta con exportar la lista de
quién tiene riesgo alto; hay que poder decir *por qué se parecen entre sí*.

El método es deliberadamente simple y por eso defendible: se parte la cohorte
de prueba en dos —los que superan el umbral y los demás— y se compara variable
por variable. No hay modelo encima de esto, no hay nada que ajustar. Es
aritmética sobre las mismas 19.870 hospitalizaciones que ya están publicadas en
`reports/predicciones_prueba.csv`, y cualquiera puede repetirla.

Se agrega una columna que no es decorativa: el reingreso REAL observado en cada
grupo. Sirve de control. Si el modelo marcara como alto riesgo a gente que
luego no reingresa más que el resto, esa columna lo delataría de inmediato.

    python src/perfil_alto_riesgo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

EGRESOS = {
    1: "A casa",
    2: "Traslado a otro hospital",
    3: "Centro de enfermería",
    4: "Cuidado intermedio",
    5: "Otra institución",
    6: "A casa con atención domiciliaria",
    22: "Rehabilitación",
}

# Las numéricas que se comparan por promedio, con el nombre que ve la persona.
NUMERICAS = {
    "ingresos_previos": "Hospitalizaciones en el año previo",
    "dias_estancia": "Días de estancia",
    "diagnosticos": "Diagnósticos registrados",
    "medicamentos": "Medicamentos administrados",
    "edad": "Edad",
}

# Las categóricas: se compara qué proporción de cada grupo cae en cada nivel.
CATEGORICAS = {
    "egreso_nombre": "Tipo de egreso",
    "grupo_edad": "Grupo de edad",
    "diagnostico_principal": "Diagnóstico principal",
    "genero": "Género",
}

# Como se escriben los niveles de cara a la persona. En el CSV crudo el grupo
# de edad viene como "80 o mas" y el genero en ingles: eso es correcto en los
# datos y es un descuido en un informe que va a leer un profesor.
NIVELES = {
    "80 o mas": "80 o más",
    "Female": "Mujer",
    "Male": "Hombre",
}

MINIMO = 100  # por debajo de esto un nivel no se reporta: la proporción baila


def main():
    d = pd.read_csv(BASE / "reports/predicciones_prueba.csv")
    d["egreso_nombre"] = d.egreso.map(EGRESOS).fillna("Otro egreso")

    alto = d[d.alerta == 1]
    resto = d[d.alerta == 0]
    print(f"Alto riesgo: {len(alto):,} · resto: {len(resto):,}".replace(",", "."))

    filas = []

    for columna, nombre in NUMERICAS.items():
        pa, pr = float(alto[columna].mean()), float(resto[columna].mean())
        filas.append({
            "variable": nombre,
            "tipo": "promedio",
            "nivel": "",
            "alto": round(pa, 2),
            "resto": round(pr, 2),
            "veces": round(pa / pr, 2) if pr else None,
            "n_alto": len(alto),
            "n_resto": len(resto),
            "reingreso_alto": round(float(alto.reingreso_real.mean()), 4),
            "reingreso_resto": round(float(resto.reingreso_real.mean()), 4),
        })

    for columna, nombre in CATEGORICAS.items():
        for nivel in sorted(d[columna].dropna().unique()):
            en_alto = alto[alto[columna] == nivel]
            en_resto = resto[resto[columna] == nivel]
            if len(en_alto) + len(en_resto) < MINIMO:
                continue
            pa = len(en_alto) / len(alto)
            pr = len(en_resto) / len(resto)
            todos = d[d[columna] == nivel]
            filas.append({
                "variable": nombre,
                "tipo": "proporcion",
                "nivel": NIVELES.get(str(nivel), str(nivel)),
                "alto": round(pa, 4),
                "resto": round(pr, 4),
                "veces": round(pa / pr, 2) if pr else None,
                "n_alto": len(en_alto),
                "n_resto": len(en_resto),
                # El reingreso real de quienes caen en ese nivel, sin importar
                # si el modelo los alerto: es el dato del mundo, no del modelo.
                "reingreso_alto": round(float(todos.reingreso_real.mean()), 4),
                "reingreso_resto": None,
            })

    tabla = pd.DataFrame(filas)
    salida = BASE / "reports/perfil_alto_riesgo.csv"
    tabla.to_csv(salida, index=False, encoding="utf-8")
    print(f"{salida.name}: {len(tabla)} filas")
    return d, alto, resto, tabla


def resumen(d, alto, resto, tabla) -> dict:
    """Las frases que van arriba de la pantalla y del PDF.

    Se arman desde los mismos números de la tabla, no a mano: si algún día se
    reentrena el modelo y el perfil cambia, el texto cambia con él.
    """
    proporciones = tabla[tabla.tipo == "proporcion"].copy()
    proporciones = proporciones[proporciones.n_alto >= 60]
    mas_marcados = proporciones.sort_values("veces", ascending=False).head(4)

    return {
        "n_total": int(len(d)),
        "n_alto": int(len(alto)),
        "n_resto": int(len(resto)),
        "porcentaje_alto": round(len(alto) / len(d), 4),
        "reingreso_alto": round(float(alto.reingreso_real.mean()), 4),
        "reingreso_resto": round(float(resto.reingreso_real.mean()), 4),
        "veces_mas_reingreso": round(
            float(alto.reingreso_real.mean()) / float(resto.reingreso_real.mean()), 2
        ),
        "rasgos": [
            {
                "variable": f.variable,
                "nivel": f.nivel,
                "alto": f.alto,
                "resto": f.resto,
                "veces": f.veces,
            }
            for f in mas_marcados.itertuples()
        ],
    }


if __name__ == "__main__":
    d, alto, resto, tabla = main()
    r = resumen(d, alto, resto, tabla)
    (BASE / "reports/perfil_alto_riesgo.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print()
    print(f"Reingreso real entre los alertados: {r['reingreso_alto']:.1%}")
    print(f"Reingreso real entre los demas:     {r['reingreso_resto']:.1%}")
    print(f"Son {r['veces_mas_reingreso']}x mas")
    print()
    print("Lo que mas distingue al grupo de alto riesgo:")
    for g in r["rasgos"]:
        print(f"  {g['variable']} = {g['nivel']}: {g['alto']:.1%} vs {g['resto']:.1%} ({g['veces']}x)")
    print()
    for f in tabla[tabla.tipo == "promedio"].itertuples():
        print(f"  {f.variable}: {f.alto} vs {f.resto} ({f.veces}x)")
