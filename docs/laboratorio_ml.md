# Laboratorio de modelos — recorrido aplicado del ciclo de Machine Learning

Esta sección sirve para demostrar el proceso de desarrollo de modelos de la
materia **Inteligencia Artificial**, sin convertir las 12 fases de las
diapositivas en 12 formularios separados. Las primeras etapas ya se abordaron
en los notebooks y documentos del proyecto; las operaciones interactivas
comienzan con un CSV etiquetado.

## Interfaz: cinco pasos, doce fases documentadas

| Vista del usuario | Evidencia del ciclo de ML |
| --- | --- |
| Contexto del proyecto | Definición del problema y recolección de datos (1–2) ya desarrolladas |
| Seleccionar, explorar y preparar | EDA, limpieza e ingeniería de características (3–5) |
| Configurar y entrenar | Partición por paciente, selección de algoritmo, entrenamiento y configuración MLP (6–9) |
| Interpretar resultados | Evaluación y comprobaciones de generalización interna (10–11) |
| Utilizar el sistema | Aplicación de inferencia/despliegue existente (12) |

**La sección no afirma que las doce fases se ejecutan en cada predicción.**
Algunos pasos son decisiones metodológicas previas y la evaluación clínica
externa todavía no existe.

## Modelo oficial y experimento: NO son lo mismo

- **Oficial:** `models/gradient_boosting_ajustado.joblib`, ya entrenado,
  seleccionado y evaluado en los notebooks. Las páginas `Estimar riesgo`
  y `Cargar archivo` siguen usándolo.
- **Experimental:** cada ejecución nueva compara `DummyClassifier`,
  `LogisticRegression` y `MLPClassifier` (una red neuronal supervisada).
  La elección se realiza con **Average Precision en validación**, y el
  umbral se fija también en validación. La prueba se usa para el reporte final
  de esa ejecución, nunca para elegir el algoritmo.
- No se escribe ni reemplaza el archivo `.joblib` oficial.
- El experimento se conserva únicamente en la sesión de Streamlit.
- La capa oculta (8–64 neuronas) y el máximo de iteraciones (30–120) son
  configurables; no se afirma que se haga una búsqueda exhaustiva de
  hiperparámetros. El proyecto ya documentó una búsqueda sobre
  Gradient Boosting en `notebooks/03_hiperparametros.ipynb`.

## Datos requeridos

- CSV original del proyecto UCI con `readmitted` y `patient_nbr`, o
  CSV preparado con las 50 características, una etiqueta binaria `y`
  y el identificador `patient_nbr`.
- `readmitted` debe ser `<30`, `>30` o `NO`.
- La etiqueta `y` debe contener únicamente `0` y `1`.
- El cargue admite hasta **30 MB**. Para mantener tiempos y memoria
  razonables, el experimento toma una muestra aleatoria reproducible de
  hasta **12.000 hospitalizaciones**, si hay más registros válidos.
- Se requieren al menos 120 registros válidos, 30 pacientes distintos
  y ambas clases (también en las tres particiones). Si no se cumplen,
  se muestra un error explicativo.

## Prevención de fugas y criterios

1. Aplicar las mismas transformaciones de características y criterios de
   exclusión que el notebook de preprocesamiento.
2. Dividir por paciente mediante `StratifiedGroupKFold`, aproximadamente
   **60/20/20**; las proporciones reales se muestran en la interfaz.
3. Ajustar imputación, escalado y codificación categórica únicamente en
   entrenamiento, dentro de cada `Pipeline`.
4. Comparar los tres clasificadores usando **AP en validación**.
5. Elegir el umbral en validación para buscar sensibilidad mínima 0,60.
6. Calcular matriz de confusión, AP, ROC-AUC, precisión y sensibilidad en
   prueba, una sola vez, tras seleccionar modelo y umbral.
7. Conservar el conjunto de prueba histórico original y las métricas oficiales.
8. Comunicar que una evaluación interna no implica validez en hospitales
   colombianos ni seguridad para decisiones clínicas.

No se elimina una fila únicamente por ser duplicada o atípica. Los datos
subidos no se utilizan para modificar el archivo del modelo oficial.

## Ejecutar y probar

Desde la raíz del repositorio:

```bash
pip install -r requirements.txt
streamlit run app/app.py
python -m unittest discover -s tests -v
```

Iniciar sesión con el **rol coordinador**; el laboratorio no está disponible
para el rol asistencial.

Prueba funcional: cargar `diabetic_data.csv` original, revisar la tabla de
calidad, escoger 24 neuronas y 65 iteraciones, ejecutar el entrenamiento,
revisar la comparación y descargar el resultado. Cambiar un hiperparámetro
invalida la visualización del experimento anterior para esa configuración.

Los resultados de ejemplo son exploratorios y pueden variar según el
dataset, las versiones de dependencias y las semillas de aleatoriedad.
