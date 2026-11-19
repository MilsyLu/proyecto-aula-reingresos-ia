# Prototipo experimental de interfaz ReingresaIA

> Rama: `experiment/reingresaia-ui`. Parte de `feature/aplicativo-ml`.
> No modifica `main` ni sustituye el modelo oficial del cliente.

## Identidad

**ReingresaIA** — *Plataforma inteligente de predicción de reingresos
hospitalarios a 30 días.*

El objetivo es separar con claridad la consulta del resultado y el
trabajo de IA que ocurre detrás. La interfaz evita mostrar métricas
técnicas a quienes solo consultan riesgos.

## Las dos áreas principales

**1. Predicción de riesgo** (personal asistencial y coordinación):
- Consultar paciente: formulario y estimación con modelo oficial.
- Analizar archivo CSV: predicciones masivas y priorización, solo coordinación.
- Sobre el modelo: ficha y limitaciones, disponible para ambos perfiles.

**2. Laboratorio de IA** (solo coordinación):
- Experimento guiado: datos, preparación, entrenamiento, comparación
  e interpretación sencilla.
- Evidencia del proyecto: modelo oficial, equidad y metodología
  agrupados en tres pestañas secundarias.

La navegación principal está en el área central, no dentro de la barra lateral.

## Laboratorio: cinco etapas, no doce pantallas

1. **Datos:** contexto de origen UCI, cargue CSV con etiquetas verificadas
   (`readmitted` o `y`) e identificador `patient_nbr`. Los pasos
   originales de planteamiento y obtención del dataset se documentan,
   no se simulan.
2. **Preparación:** calidad, registros excluidos, distribuciones y
   características. Los detalles extensos están en pestañas desplegables.
3. **Entrenamiento:** configurar MLP y número acotado de configuraciones,
   entrenar Gradient Boosting y MLP con el mismo conjunto y partición.
4. **Comparación:** resultados paralelos, AP de validación/prueba y
   recomendación. Las matrices, ajustes, curvas y CSV quedan plegados
   para no saturar la pantalla.
5. **Interpretación:** explicar sin jerga qué se eligió, qué significa
   cada métrica, qué alertas fueron correctas y cuáles son las limitaciones.
   La explicación se puede descargar.

La selección del mejor algoritmo siempre se hace por AP de **validación**;
no se ajusta el ganador después de mirar los datos de prueba. Cada
experimento conserva sus métricas aisladas del archivo oficial
`models/gradient_boosting_ajustado.joblib`.

### Estado entre etapas

- Una carga válida guarda únicamente en la sesión los datos procesados
  y su referencia de origen; al cambiar de etapa no requiere repetir
  el cargue.
- Un nuevo archivo invalida los resultados del experimento anterior.
- Cambiar la configuración requiere entrenar otra vez.
- El cierre de sesión limpia los resultados y datos del laboratorio.
- No se muestran resultados antes de entrenar ambos algoritmos.
- Límite de carga de 30 MB y muestra reproducible de hasta 12.000 registros
  por ejecución.

## Barra lateral y presentación

Se respetan los controles nativos de Streamlit: la portada inicia con
la barra contraída, pero el CSS ya no usa `display:none` para
suprimirla ni anula la altura del encabezado. La navegación de áreas
sigue visible incluso cuando el panel lateral está contraído.

El interior utiliza espacios de lectura, un encabezado de marca
consistente, subnavegación horizontal y detalles técnicos plegables.

## Verificación recomendada antes de fusionar

```bash
git fetch origin
git switch experiment/reingresaia-ui
git pull origin experiment/reingresaia-ui
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app/app.py
```

Verificar visualmente:

1. Inicio de sesión en escritorio y móvil; plegar y reabrir barra lateral.
2. Perfil asistencial: solo área de predicción, con consulta y ficha.
3. Perfil coordinador: dos áreas, subopciones y CSV.
4. Laboratorio: subir `diabetic_data.csv` en Datos y avanzar a Preparación.
5. Revisar que el archivo continúe al avanzar y retroceder.
6. Entrenar ambos modelos; ver las métricas lado a lado y el texto explicativo.
7. Cambiar el CSV; comprobar que se invalidan los resultados previos.
8. Cerrar la sesión; confirmar que los datos de entrenamiento se descartan.

**No se consideran aprobadas las pruebas de ejecución ni diseño visual
hasta comprobar el aplicativo con un navegador real.**
