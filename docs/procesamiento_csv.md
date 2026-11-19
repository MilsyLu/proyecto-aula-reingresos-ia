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
