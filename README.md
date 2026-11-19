# Predicción de reingresos hospitalarios a 30 días

Proyecto de aula de Inteligencia Artificial — **Grupo 04**
Universidad Popular del Cesar · Ingeniería de Sistemas · Séptimo semestre · 2026

> **Versión experimental ReingresaIA:** la rama
> [`experiment/reingresaia-ui`](https://github.com/MilsyLu/proyecto-aula-reingresos-ia/tree/experiment/reingresaia-ui)
> aplica una identidad visual propia y organiza el aplicativo en dos áreas:
> **Predicción de riesgo** y **Laboratorio de IA**. El laboratorio ofrece un
> recorrido guiado por cinco etapas y deja la evidencia técnica desplegable.
> La aplicación pública enlazada abajo no necesariamente ejecuta esta rama.
> [Ver guía del experimento](docs/reingresaia_experimental.md).

**Integrantes:** Michel Custodes · Iván Güette · Maira Torres

### 🔗 Aplicación en vivo: **https://reingresos-grupo04.streamlit.app/**

Entra con usuario y contraseña. Hay **dos roles**, y no son decorativos: reproducen la tesis
del proyecto. El umbral de alerta es una decisión de política sanitaria, no un cálculo
clínico, así que quien lo fija no es quien lo consume.

| | **Personal asistencial** | **Coordinación del programa** |
|---|---|---|
| Estimar el riesgo de un paciente | ✅ | ✅ |
| Ver por qué se alertó | ✅ | ✅ |
| Preguntarle al asistente | ✅ | ✅ |
| Cargar un archivo y priorizar | ❌ | ✅ |
| Desempeño del modelo | ❌ | ✅ |
| Equidad y límites | ❌ | ✅ |

Las credenciales de demostración aparecen en la pantalla de entrada y están en
`app/usuarios_demo.toml`. Para usar cuentas reales, pegue una sección `[usuarios]` con esa
misma forma en los secretos de la aplicación en Streamlit Cloud: lo que esté ahí manda sobre
el archivo.

---

## Laboratorio de Machine Learning (rama de desarrollo)

El **Laboratorio de modelos** entrena y compara **dos modelos de clasificación
distintos** sobre el mismo conjunto de datos: Gradient Boosting y una red
neuronal MLP. Cada uno utiliza su propia preparación de características,
configuraciones y produce métricas, matriz de confusión y predicciones
individuales de prueba.

La elección se basa en la **Average Precision de validación**, antes de
consultar el conjunto de prueba. La aplicación muestra ambos resultados y
explica por qué uno es preferible. También incluye ajuste acotado de
hiperparámetros, gráfica de pérdida de la MLP y revisión de sobreajuste.

Para entrenar se requiere un CSV etiquetado (`readmitted` o `y`) y
`patient_nbr`, porque las hospitalizaciones de un mismo paciente deben
permanecer en la misma partición. Los experimentos NO reemplazan el modelo
histórico de Gradient Boosting usado en las pantallas de clientes.

La definición del problema y recolección histórica permanecen documentadas
en los notebooks; el laboratorio demuestra la preparación, partición,
entrenamiento, comparación, evaluación y generalización interna sin
simular que las doce fases se repiten en cada predicción.

Ver [documentación del laboratorio](docs/laboratorio_ml.md).

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
│   ├── 04_evaluacion_comparada.ipynb
│   └── 05_equidad_sensibilidad.ipynb      auditoría de equidad y sensibilidad
├── app/
│   ├── app.py              enrutador y sesión
│   ├── auth.py             inicio de sesión, roles y control de acceso
│   ├── datos.py            carga del modelo y de los resultados, con caché
│   ├── estilo.py           hoja de estilos (portada oscura, interior claro)
│   ├── modelo.py           predicción y explicación por paciente
│   ├── asistente.py        asistente de lenguaje natural (Gemini, opcional)
│   ├── paginas/            una por sección
│   ├── assets/             vídeo y cartel de la portada
│   ├── usuarios_demo.toml  cuentas de demostración, con hash
│   └── valores_por_defecto.json   valores típicos de las variables no pedidas
├── src/               funciones reutilizables
├── models/            modelo entrenado (versionado: lo necesita la app)
├── reports/
│   ├── figures/       gráficas generadas
│   ├── Fase_1_...pdf                        documento de la Fase 1
│   ├── Fase_2_Informe_Tecnico_Grupo04.pdf   informe técnico de la Fase 2
│   ├── Fase_3_Informe_Final_Grupo04.pdf     informe final (15 páginas)
│   ├── Guia_Tablero_PowerBI.md              cómo armar el tablero paso a paso
│   ├── tablero_powerbi.csv                  datos listos para Power BI
│   ├── predicciones_prueba.csv              19.870 filas del conjunto de prueba
│   └── *.csv / *.json  métricas y resultados de cada notebook
├── requirements.txt
└── README.md
```

---

## Cómo ejecutarlo

**1. Instalar las dependencias**

```bash
pip install -r requirements.txt
```

**2. Reproducir el análisis** — los notebooks se ejecutan **en orden numérico**: cada uno
guarda sus resultados en `data/processed/` o en `reports/`, y el siguiente los lee desde ahí.

```bash
jupyter notebook
```

**3. Levantar la aplicación en local**

```bash
streamlit run app/app.py
```

> Ejecútelo **desde la raíz del proyecto**. Streamlit lee `.streamlit/config.toml` relativo a
> la carpeta actual, y si arranca desde otro sitio la aplicación hereda el modo oscuro del
> sistema y los campos salen negros sobre fondo claro.

**4. Opcional: encender el asistente**

El asistente de lenguaje natural necesita una clave de Gemini. En local, una variable de
entorno `GEMINI_API_KEY`; en Streamlit Cloud, un secreto con ese mismo nombre. Sin clave el
asistente se apaga solo y el resto de la aplicación funciona igual.

La aplicación carga `models/gradient_boosting_ajustado.joblib` y
`reports/predicciones_prueba.csv`, ambos versionados, así que funciona sin haber ejecutado los
notebooks. Las versiones de `requirements.txt` están fijadas a propósito: el modelo se
serializó con `scikit-learn==1.9.1` y otra versión puede no cargarlo.

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

### Cumplimiento de las metas de la Fase 1

| Meta | Objetivo | Obtenido | |
|---|---|---|---|
| AP ≥ 1,5 × prevalencia | 0,1708 | 0,2249 | ✅ |
| ROC-AUC ≥ 0,65 | 0,650 | 0,666 | ✅ |
| Sensibilidad ≥ 0,60 | 0,600 | 0,6001 | ✅ |
| Precisión ≥ 0,20 junto al recall | 0,200 | 0,1781 | ❌ |

---

## Resultados de la Fase 3

La Fase 3 añadió el despliegue y la evaluación crítica. Produjo tres hallazgos que condicionan
cualquier uso del modelo.

**1. Dos variables administrativas concentran el 43,5 % del desempeño.** La importancia por
permutación sobre el conjunto de prueba muestra que `number_inpatient` (hospitalizaciones
previas) aporta el 25,1 % del AP y `discharge_disposition_id` (tipo de egreso) el 18,4 %. De
las 50 variables, 21 no aportan nada. El modelo se apoya más en el historial administrativo
del paciente que en su estado clínico.

**2. La sensibilidad global oculta dos comportamientos muy distintos.** Al separar el conjunto
de prueba por tipo de egreso:

| Escenario | n | Prevalencia | AP | Sensibilidad |
|---|---|---|---|---|
| Prueba completa | 19.870 | 11,39 % | 0,2249 | 0,6001 |
| Transferidos a otra institución | 4.144 | 15,97 % | 0,2541 | **0,8822** |
| Dados de alta a casa | 15.726 | 10,18 % | 0,2098 | **0,4834** |

Los pacientes que se van a casa son el **79 % de la cohorte** y son justamente el destinatario
de un programa de seguimiento al alta. **La sensibilidad útil para el caso de uso real no es
0,60 sino 0,48.**

**3. Hay una disparidad por edad no justificada por el riesgo.** Razón de paridad de **0,569**:

| Grupo de edad | n | Prevalencia real | Tasa de alerta | ROC-AUC |
|---|---|---|---|---|
| Menos de 50 | 3.078 | 11,50 % | 30,2 % | 0,713 |
| 50 a 60 | 3.451 | 8,92 % | 29,2 % | 0,697 |
| 60 a 70 | 4.519 | 12,35 % | 37,3 % | 0,670 |
| 70 a 80 | 4.912 | 11,77 % | 40,6 % | 0,633 |
| 80 o más | 3.910 | 11,89 % | **51,3 %** | **0,619** |

La tasa de alerta sube 21 puntos con la edad mientras la prevalencia real se mueve menos de
medio punto, y la capacidad de discriminar cae justo en el grupo sobre el que más se alerta.

Por **género** la razón de paridad es 0,905, dentro de lo aceptable. Por **grupo racial** es
0,786, pero la baja la produce el grupo `Asian` (143 casos); entre los dos grupos con tamaño
suficiente (`Caucasian` y `AfricanAmerican`) la razón es 0,987. No es lo mismo decir "no hay
sesgo" que decir "no hay datos para medirlo".

El informe completo está en `reports/Fase_3_Informe_Final_Grupo04.pdf` (15 páginas).

> **Nota sobre el informe y la aplicación.** El informe describe la aplicación tal como se
> entregó en la Fase 3: cuatro páginas, sin inicio de sesión. Después de la entrega la
> aplicación siguió creciendo —roles, cargue de archivos, lista priorizada, explicación por
> paciente y asistente— así que la sección 8 del informe se queda corta frente a lo que hay
> hoy. Se deja así a propósito: el informe documenta lo que se entregó, no lo que vino
> después. Este README describe el estado actual.

### Entregables de la Fase 3

| Entregable | Dónde |
|---|---|
| Aplicación desplegada | https://reingresos-grupo04.streamlit.app/ — con inicio de sesión y dos roles |
| Lista priorizada por capacidad | en la aplicación, sección **Cargar archivo** |
| Explicación por paciente | en la aplicación, dentro de **Estimar riesgo** |
| Informe final (15 pág.) | `reports/Fase_3_Informe_Final_Grupo04.pdf` · también en `.docx` |
| Tablero de Power BI | datos en `reports/tablero_powerbi.csv` · guía en `reports/Guia_Tablero_PowerBI.md` |
| Auditoría de equidad | `notebooks/05_equidad_sensibilidad.ipynb` |

---

## Limitaciones

- **La sensibilidad útil es 0,48, no 0,60**, en la población a la que iría dirigido el
  programa (pacientes dados de alta a su casa).
- **Hay una disparidad por edad no justificada por el riesgo real** (razón de paridad 0,569).
- **La precisión es baja**: con el umbral elegido, 5 de cada 6 alertas son falsas, y la meta de
  precisión 0,20 no se alcanza en ningún umbral compatible con la sensibilidad pedida.
- Los datos corresponden a 1999–2008 y a hospitales de Estados Unidos. No hay evidencia de
  validez en el sistema de salud colombiano.
- Faltan los determinantes más importantes del reingreso: soporte familiar, acceso efectivo a
  la medicación, adherencia y continuidad del cuidado ambulatorio.
- No permiten observar reingresos ocurridos fuera de la red de atención, ni distinguir
  reingresos programados de evitables.
- `race` se reserva para revisar diferencias entre subgrupos y se excluye del modelo principal;
  esto no elimina el sesgo que puedan transmitir otras variables.
- No se evaluó la estabilidad temporal: la partición es por paciente, no por periodo.
- **Es un prototipo académico. No es una herramienta de decisión clínica.**

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
