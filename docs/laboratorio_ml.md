# Laboratorio ML: comparación de dos modelos de predicción de reingresos

## Objetivo

Demostrar el flujo de aprendizaje supervisado con **dos modelos que
realmente se entrenan** sobre el mismo CSV y las mismas particiones:

1. **HistGradientBoostingClassifier** (modelo de árboles, misma familia que
   el modelo oficial del proyecto, con parámetros experimentales).
2. **MLPClassifier** (red neuronal feed-forward de scikit-learn).

Cada modelo tiene su propia preparación, búsqueda de configuraciones,
matriz de confusión, métricas y predicciones exportables. Se elige el mejor
**antes de evaluar prueba**: el criterio es mayor **Average Precision (AP)
en validación**, porque los reingresos son minoritarios.

No se compara una MLP nueva con las cifras históricas de otro conjunto
de datos: eso sería metodológicamente incorrecto. Ambos modelos nuevos
usan **exactamente las mismas filas**, y el modelo oficial histórico se
presenta separadamente como un artefacto ya publicado.

## Relación con las 12 fases de la asignatura

| Etapa observable | Evidencias que se muestran |
|---|---|
| Contexto y procedencia | Problema y fuente UCI ya definidos por el equipo (fases 1–2) |
| Carga y exploración | CSV etiquetado, estadísticas, faltantes, atípicos (fases 2–3) |
| Preparación | Exclusiones documentadas y 12 características derivadas (fases 4–5) |
| Partición | Separación aproximada 60/20/20 por paciente, sin fuga (fase 6) |
| Dos procesos de entrenamiento | Elección entre GB y MLP, entrenamiento real (fases 7–8) |
| Búsqueda de configuraciones | 1 a 3 combinaciones por algoritmo, seleccionadas en validación (fase 9) |
| Comparación y errores | Dos resultados de prueba, tablas y matrices de confusión (fase 10) |
| Robustez | Brecha de AP train/validation, curva de pérdida de MLP y límites (fase 11) |
| Entrega al cliente | Producto Streamlit existente, usando por ahora el modelo oficial (fase 12) |

## Seguridad experimental

- Solo se aceptan CSV con etiquetas reales `readmitted` o `y` y
  `patient_nbr` para no mezclar hospitalizaciones de una persona entre conjuntos.
- Hasta 30 MB por archivo, 12.000 filas por experimento y máximo tres
  configuraciones por modelo. La reducción a 12.000 filas es una muestra
  reproducible, y sus métricas **no se confunden** con las del modelo oficial.
- El esquema y las exclusiones provienen de `src/procesamiento_lotes.py`.
- GB usa numéricas sin escalar, codificación ordinal y categorías nativas
  del clasificador. MLP usa imputación, estandarización y one-hot.
- Todos los transformadores se ajustan **solo con entrenamiento**.
- Cada algoritmo prueba configuraciones en validación; la AP decide cuál
  es su mejor configuración. Luego se compara el mejor GB con la mejor MLP
  en esa misma validación. El umbral se fija por modelo en validación para
  intentar recall >= 0,60.
- **Después** de congelar la selección se obtienen las métricas de prueba
  para ambos modelos. El resultado de prueba nunca revierte esa decisión.
- Curvas: AP de entrenamiento/validación/prueba, brecha de sobreajuste y
  pérdida de optimización de la MLP. La pérdida MLP no es una curva de
  validación y no debe describirse como tal.
- El parámetro de 1–3 configuraciones es una búsqueda **acotada**, no una
  búsqueda exhaustiva ni una validación cruzada anidada.
- No se guardan ni sustituyen automáticamente modelos entrenados en
  `models/`. Las predicciones de clientes continúan usando
  `gradient_boosting_ajustado.joblib`.

## Justificación de cara al cliente

La pantalla recomienda el algoritmo de mayor AP de validación y expone la
precisión, sensibilidad, ROC-AUC y errores por separado. El objetivo es
fundamentar una futura selección para el cliente, **no promoverla
automáticamente**. Para actualizar el modelo operativo habría que probarlo
con una evaluación independiente, verificar sesgos y aprobar la nueva
versión. Ningún modelo está validado para decisiones clínicas actuales.

## Ejecución

```bash
git switch feature/aplicativo-ml
git pull origin feature/aplicativo-ml
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app/app.py
```

Inicie sesión como coordinador, abra **Laboratorio de modelos**, cargue el
CSV original `diabetic_data.csv` y ejecute la comparación. Descargue
`comparacion_gb_mlp.csv`, `busqueda_gb_mlp.csv` y los dos archivos con
probabilidades de prueba. Use datos públicos o anonimizados.
