# -*- coding: utf-8 -*-
"""Auditoría del techo de información de la cohorte.

Reproduce el método de Chowdhury et al. (2026), "The Ceiling Is in the Channel",
arXiv:2609.01909, sobre nuestros propios datos.

La idea: el techo no es una propiedad del modelo sino de las columnas que se
registraron. Si un oráculo conociera la probabilidad verdadera P(y=1 | X), su
exactitud balanceada sería ½(1 + κ), donde κ = TV(P0, P1) es cuánto se separan
las distribuciones de X entre quienes reingresan y quienes no.

κ se estima sobre una muestra balanceada con validación cruzada agrupada por
paciente: κ̂ = promedio |2·η̂(x) − 1|, con η̂ fuera de pliegue. Que la media de la
confianza del modelo sirva de estimador es lo que hace el método barato.

Dos diagnósticos obligatorios, que el artículo exige y aquí se cumplen:

  * Piso por permutación: con etiquetas barajadas el techo debe caer a ~0,5.
    Si no cae, el estimador está inflado y no sirve.
  * Curva de subajuste: se reentrena con 25/50/75/100 % de la muestra. Si el
    techo aún sube al final, se reporta como cota inferior, no como el techo.

Además separa los dos canales de información para responder qué dato falta:
administrativo (quién es y por dónde entró y salió) contra clínico (qué le
encontraron y qué le dieron).

Salida: reports/auditoria_techo.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OrdinalEncoder

sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parent.parent
SEMILLA = 42
PLIEGUES = 5

# Canal administrativo: lo que se sabe sin examinar al paciente. Quién es, por
# dónde entró, a dónde salió, cuántas veces había venido antes.
ADMIN = [
    "edad_num", "gender", "admission_type_id", "discharge_disposition_id",
    "admission_source_id", "medical_specialty", "time_in_hospital",
    "number_outpatient", "number_emergency", "number_inpatient",
    "servicios_previos", "tuvo_ingreso_previo",
]


def construir(numericas, categoricas):
    """El mismo preprocesamiento del modelo oficial, para que sea comparable."""
    return Pipeline([
        ("prep", ColumnTransformer([
            ("numericas", FunctionTransformer(feature_names_out="one-to-one"), numericas),
            ("categoricas", Pipeline([
                ("imputar", SimpleImputer(strategy="constant", fill_value="Ausente")),
                ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value",
                                           unknown_value=-1)),
            ]), categoricas),
        ])),
        ("modelo", HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
            early_stopping=True, validation_fraction=0.12,
            random_state=SEMILLA)),
    ])


def balancear(df, rng):
    """Submuestra la clase mayoritaria hasta igualar. El techo se define sobre
    una mezcla 50/50: así ½(1+κ) es directamente la exactitud balanceada."""
    pos = df.index[df.y == 1].to_numpy()
    neg = df.index[df.y == 0].to_numpy()
    neg = rng.choice(neg, size=len(pos), replace=False)
    return df.loc[np.concatenate([pos, neg])].sample(frac=1.0, random_state=SEMILLA)


def cross_fit(df, numericas, categoricas, etiquetas=None):
    """Probabilidades fuera de pliegue, agrupadas por paciente.

    Agrupar por paciente importa: si las hospitalizaciones de una misma persona
    caen a lado y lado de la partición, el modelo la reconoce y el techo sale
    inflado.
    """
    X = df[numericas + categoricas].copy()
    X[categoricas] = X[categoricas].astype(str)
    y = df.y.to_numpy() if etiquetas is None else etiquetas
    grupos = df.patient_nbr.to_numpy()

    fuera = np.zeros(len(df), dtype=float)
    cv = StratifiedGroupKFold(n_splits=PLIEGUES, shuffle=True, random_state=SEMILLA)
    for entrena, prueba in cv.split(X, y, groups=grupos):
        m = construir(numericas, categoricas)
        m.fit(X.iloc[entrena], y[entrena])
        fuera[prueba] = m.predict_proba(X.iloc[prueba])[:, 1]
    return fuera, y


def techo_de(eta):
    """κ̂ = promedio de |2η−1|; techo = ½(1+κ̂)."""
    kappa = float(np.mean(np.abs(2.0 * eta - 1.0)))
    return 0.5 * (1.0 + kappa), kappa


def ba_lograda(eta, y, umbral=0.5):
    """Exactitud balanceada del modelo: el promedio de sensibilidad y especificidad."""
    pred = eta >= umbral
    sens = float(((pred == 1) & (y == 1)).sum() / max((y == 1).sum(), 1))
    esp = float(((pred == 0) & (y == 0)).sum() / max((y == 0).sum(), 1))
    return 0.5 * (sens + esp)


def ic_bootstrap(eta, grupos, repeticiones=300):
    """IC 95 % del techo, remuestreando pacientes enteros, no filas sueltas."""
    rng = np.random.default_rng(SEMILLA)
    unicos = np.unique(grupos)
    por_paciente = {g: np.where(grupos == g)[0] for g in unicos}
    valores = []
    for _ in range(repeticiones):
        elegidos = rng.choice(unicos, size=len(unicos), replace=True)
        idx = np.concatenate([por_paciente[g] for g in elegidos])
        valores.append(techo_de(eta[idx])[0])
    return float(np.percentile(valores, 2.5)), float(np.percentile(valores, 97.5))


def main():
    cols = json.loads((BASE / "data/processed/columnas.json").read_text(encoding="utf-8"))
    NUM, CAT = cols["numericas"], cols["categoricas"]
    proc = pd.read_csv(BASE / "data/processed/cohorte_procesada.csv", low_memory=False)
    proc = proc.reset_index(drop=True)

    rng = np.random.default_rng(SEMILLA)
    bal = balancear(proc, rng).reset_index(drop=True)
    print(f"cohorte {len(proc):,} filas  |  muestra balanceada {len(bal):,} "
          f"({bal.patient_nbr.nunique():,} pacientes)".replace(",", "."))

    salida = {
        "cohorte": {
            "filas": int(len(proc)),
            "pacientes": int(proc.patient_nbr.nunique()),
            "prevalencia": float(proc.y.mean()),
            "balanceada": int(len(bal)),
        },
        "pliegues": PLIEGUES,
        "metodo": "Chowdhury et al. 2026, arXiv:2609.01909",
    }

    # ---------------------------------------------------- canal completo
    eta, y = cross_fit(bal, NUM, CAT)
    techo, kappa = techo_de(eta)
    ba = ba_lograda(eta, y)
    lo, hi = ic_bootstrap(eta, bal.patient_nbr.to_numpy())
    salida["completo"] = {
        "techo": techo, "kappa": kappa, "ic95": [lo, hi],
        "ba_lograda": ba, "brecha": techo - ba,
    }
    print(f"\nCANAL COMPLETO  techo {techo:.4f}  IC95 [{lo:.4f}, {hi:.4f}]")
    print(f"                BA lograda {ba:.4f}   brecha {techo - ba:+.4f}")

    # ------------------------------------------- piso por permutación
    barajadas = rng.permutation(bal.y.to_numpy())
    eta_nula, _ = cross_fit(bal, NUM, CAT, etiquetas=barajadas)
    techo_nulo = techo_de(eta_nula)[0]
    salida["piso_permutacion"] = {"techo": techo_nulo, "exceso": techo_nulo - 0.5}
    print(f"PISO (etiquetas barajadas)  {techo_nulo:.4f}  "
          f"exceso sobre 0,5: {techo_nulo - 0.5:+.4f}")

    # ------------------------------------------------ curva de subajuste
    curva = []
    for fraccion in (0.25, 0.50, 0.75):
        sub = bal.sample(frac=fraccion, random_state=SEMILLA).reset_index(drop=True)
        e, _ = cross_fit(sub, NUM, CAT)
        curva.append({"fraccion": fraccion, "techo": techo_de(e)[0]})
        print(f"  subajuste {int(fraccion*100):>3} %  techo {curva[-1]['techo']:.4f}")
    curva.append({"fraccion": 1.0, "techo": techo})
    ultimo = curva[-1]["techo"] - curva[-2]["techo"]
    salida["subajuste"] = {
        "curva": curva, "incremento_final": ultimo,
        "veredicto": "cota inferior" if abs(ultimo) > 0.002 else "convergido",
    }
    print(f"  subajuste 100 %  techo {techo:.4f}   incremento final {ultimo:+.4f}"
          f"  -> {salida['subajuste']['veredicto']}")

    # ------------------------------------------------- canales separados
    admin_num = [c for c in NUM if c in ADMIN]
    admin_cat = [c for c in CAT if c in ADMIN]
    clin_num = [c for c in NUM if c not in ADMIN]
    clin_cat = [c for c in CAT if c not in ADMIN]

    eta_a, _ = cross_fit(bal, admin_num, admin_cat)
    eta_b, _ = cross_fit(bal, clin_num, clin_cat)
    ta = techo_de(eta_a)[0]
    tb = techo_de(eta_b)[0]
    salida["canales"] = {
        "administrativo": {"techo": ta, "variables": len(admin_num) + len(admin_cat)},
        "clinico": {"techo": tb, "variables": len(clin_num) + len(clin_cat)},
        "juntos": {"techo": techo, "variables": len(NUM) + len(CAT)},
        "complementariedad": techo - max(ta, tb),
    }
    print(f"\nCANAL ADMINISTRATIVO ({len(admin_num)+len(admin_cat)} var)  techo {ta:.4f}")
    print(f"CANAL CLINICO        ({len(clin_num)+len(clin_cat)} var)  techo {tb:.4f}")
    print(f"JUNTOS               ({len(NUM)+len(CAT)} var)  techo {techo:.4f}"
          f"   complementariedad {techo - max(ta, tb):+.4f}")

    destino = BASE / "reports" / "auditoria_techo.json"
    destino.write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nguardado en {destino.relative_to(BASE)}")


if __name__ == "__main__":
    main()
