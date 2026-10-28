# Predicción de reingresos hospitalarios a 30 días

Proyecto de aula de Inteligencia Artificial — **Grupo 04**
Universidad Popular del Cesar · Ingeniería de Sistemas · Séptimo semestre · 2026

**Integrantes:** Michel Custodes · Iván Güette · Maira Torres

---

## Qué hace este proyecto

Estima la probabilidad de que un paciente con diabetes **vuelva a ser hospitalizado antes de
30 días** después del alta, a partir de la información registrada durante su hospitalización.

Es un problema de **aprendizaje supervisado para clasificación binaria** sobre datos tabulares.
La unidad de análisis es la **hospitalización**, no la persona: un mismo paciente puede tener
varios registros.

**Variable objetivo:** se marca `1` cuando `readmitted` vale `<30`, y `0` cuando vale `>30` o `NO`.

---

## Datos

| | |
|---|---|
| Fuente | Diabetes 130-US Hospitals for Years 1999-2008 (Clore et al., 2014) |
| Repositorio | UCI Machine Learning Repository, dataset 296 |
| Licencia | CC BY 4.0 |
| Archivo original | 101.766 hospitalizaciones × 50 columnas |
| Pacientes distintos | 71.518 |
| Cohorte de trabajo | 99.343 hospitalizaciones · 69.990 pacientes |
| Positivos (`<30`) | 11.314 — el 11,39 % de la cohorte |

**Cohorte:** se excluyen 2.423 registros cuyo egreso corresponde a fallecimiento o a cuidados
paliativos (códigos de `discharge_disposition_id` 11, 13, 14, 19, 20 y 21), porque esos
pacientes no pueden reingresar y su inclusión distorsionaría el desenlace.

### Cómo conseguir los datos

El archivo `diabetic_data.csv` pesa 19 MB y **no se versiona en el repositorio**. Para
reproducir el trabajo, descárguelo de UCI y colóquelo en `data/raw/`:

```
https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008
```

`data/raw/IDs_mapping.csv` sí está incluido porque es pequeño y necesario para traducir los
códigos administrativos.

---

## Estructura del repositorio

```
proyecto-reingresos/
├── data/
│   ├── raw/           datos originales sin modificar (no versionados)
│   └── processed/     cohorte y particiones generadas (no versionadas)
├── notebooks/
│   ├── 00_EDA_fase1.ipynb                 análisis exploratorio (Fase 1)
│   ├── 01_preprocesamiento_particion.ipynb
│   ├── 02_modelos_baseline.ipynb
│   ├── 03_hiperparametros.ipynb
│   └── 04_evaluacion_comparada.ipynb
├── src/               funciones reutilizables
├── models/            modelos entrenados (no versionados)
├── reports/
│   ├── figures/       gráficas generadas
│   ├── Fase_1_...pdf  documento de la Fase 1
│   ├── Fase_2_Informe_Tecnico_Grupo04.pdf   informe técnico de la Fase 2
│   └── *.csv / *.json  métricas y resultados de cada notebook
├── requirements.txt
└── README.md
```

---

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
jupyter notebook
```

Los notebooks se ejecutan **en orden numérico**: cada uno guarda sus resultados en
`data/processed/` y el siguiente los lee desde ahí.

---

## Decisiones metodológicas

**Partición por paciente.** Los conjuntos de entrenamiento, validación y prueba se separan por
`patient_nbr`, no por fila. Como 16.341 personas tienen más de una hospitalización (hasta 40 en
un caso), repartir filas al azar dejaría a la misma persona en dos conjuntos y el modelo sería
evaluado sobre pacientes que ya conoció. **Ningún paciente aparece en más de un conjunto.**

**Partición 60/20/20** con `StratifiedGroupKFold`, conservando la proporción de positivos.

**Métrica principal: Average Precision (AP).** La clase positiva es minoritaria (11,39 %), así
que la exactitud no sirve como criterio: un modelo que siempre responda "no reingresa" obtendría
88,61 % de exactitud y no detectaría ningún caso.

**El conjunto de prueba se evalúa una sola vez**, con el flujo ya congelado. El umbral de
decisión se elige en validación, no en prueba.

**Transformaciones dentro de pipelines**, ajustadas únicamente con los datos de entrenamiento,
para evitar fuga de información.

---

## Modelos comparados

| Modelo | Papel |
|---|---|
| Clasificador mayoritario | Línea base trivial: referencia mínima que hay que superar |
| Regresión logística | Línea base interpretable |
| Gradient Boosting | Modelo propuesto: captura relaciones no lineales e interacciones |
| MLP sencilla | Extensión opcional — no ejecutada en la Fase 2 |

### Resultados de la Fase 2

Conjunto de prueba, evaluado una sola vez con el umbral 0,1123 fijado en validación:

| Métrica | Valor | IC 95 % |
|---|---|---|
| Average Precision | **0,2249** | [0,2047 ; 0,2467] |
| ROC-AUC | **0,6660** | [0,6527 ; 0,6786] |
| Sensibilidad (recall) | **0,6001** | [0,5766 ; 0,6202] |
| Precisión | 0,1781 | |
| Brier | 0,0963 | |

Validación y prueba coinciden casi exactamente (AP 0,2238 frente a 0,2249; ROC-AUC 0,6660 en
ambos), lo que indica que no hubo sobreajuste en la búsqueda de hiperparámetros ni fuga de
información entre conjuntos.

**Resultado negativo documentado:** ningún umbral alcanza a la vez sensibilidad ≥ 0,60 y
precisión ≥ 0,20. Con sensibilidad 0,60 la precisión cae a 0,177; exigiendo precisión 0,20 la
sensibilidad máxima es 0,481. Se informa tal cual, sin modificar el conjunto de prueba.

El detalle completo está en `reports/Fase_2_Informe_Tecnico_Grupo04.pdf`.

---

## Limitaciones

- Los datos corresponden a 1999–2008 y a hospitales de Estados Unidos.
- No permiten observar reingresos ocurridos fuera de la red de atención, ni distinguir
  reingresos programados de evitables.
- `race` se reserva para revisar diferencias entre subgrupos y se excluye del modelo principal;
  esto no elimina el sesgo que puedan transmitir otras variables.
- Es un prototipo académico. No es una herramienta de decisión clínica.

---

## Referencias

- Clore, J., Cios, K., DeShazo, J. y Strack, B. (2014). *Diabetes 130-US Hospitals for Years
  1999-2008*. UCI Machine Learning Repository.
- Strack, B. et al. (2014). Impact of HbA1c measurement on hospital readmission rates.
  *BioMed Research International*.
- Frizzell, J. D. et al. (2017). Prediction of 30-day all-cause readmissions in patients
  hospitalized for heart failure. *JAMA Cardiology*.
- Rajkomar, A. et al. (2018). Scalable and accurate deep learning with electronic health
  records. *npj Digital Medicine*.
