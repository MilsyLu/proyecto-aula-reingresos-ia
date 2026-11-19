# Procesamiento de CSV (primera entrega del aplicativo)

La aplicación acepta dos esquemas: el CSV original de UCI `diabetic_data.csv`
(50 columnas) o un CSV que ya incluya exactamente las 50 características del
modelo, definidas en `app/valores_por_defecto.json`.

El procesamiento replica la ingeniería de características del notebook 01.
Valida columnas, convierte faltantes `?`, excluye los egresos 11, 13, 14, 19,
20 y 21 y rechaza las filas con estancia no positiva o edad no reconocida.
No elimina automáticamente valores atípicos ni duplicados: dos hospitalizaciones
de un paciente pueden representar eventos diferentes.

Las transformaciones estadísticas restantes son realizadas por el pipeline
entrenado. No se ajusta un nuevo imputador con los datos subidos.

## Uso

1. Instala `requirements.txt`.
2. Ejecuta `streamlit run app/app.py`.
3. Elige **Procesamiento CSV**, carga tu archivo y revisa el diagnóstico.
4. Ejecuta el modelo y descarga los resultados y el informe de filas excluidas.

Los datos se procesan en memoria y no se guardan en el repositorio.
No subas archivos con información identificable de pacientes.

**Alcance:** esta modalidad es solo para inferencia, no para reentrenar ni
calcular métricas con etiquetas reales. Las demás fases del ciclo se documentan
en los notebooks y se integrarán progresivamente en la aplicación.

Pruebas: `python -m unittest discover -s tests -v`.


## Segunda iteración: EDA interactivo

La pantalla **Procesamiento CSV** muestra ahora:
- Conteo de filas, columnas, valores faltantes y duplicados exactos.
- Tabla de calidad por columna (tipo, porcentaje de faltantes y valores distintos).
- Distribución de faltantes y estadísticas descriptivas de las variables numéricas.
- Detección exploratoria de posibles valores extremos por la regla del rango intercuartílico.
- Distribución de `readmitted` o `y` solo cuando el CSV incluye una etiqueta real.
- Descarga de reporte de calidad y de los registros excluidos.

Los registros repetidos o los valores IQR extremos **no se descartan automáticamente**.
No deben confundirse con errores sin revisar el contexto de la hospitalización.

Los resultados de inferencia se mantienen en la sesión al pulsar el botón de descarga,
pero se invalidan si se carga un archivo con contenido diferente. Ningún dato nuevo
se utiliza para reentrenar el estimador o escoger el umbral.

## Pruebas y limitaciones actuales

Ejecutar:

```bash
python -m unittest discover -s tests -v
```

Esta versión no permite el entrenamiento interactivo ni la comparación externa con
etiquetas verificadas. El EDA es descriptivo, no realiza depuración destructiva.
La calidad del modelo en datos históricos no supone validación clínica en otra población.
Para archivos grandes, respetar el límite de 30 MB del prototipo.
