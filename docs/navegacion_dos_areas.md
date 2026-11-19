# Interfaz simplificada — dos áreas

## Distribución de la plataforma

Después de iniciar sesión, el aplicativo tiene **dos áreas principales**
seleccionables en la parte superior, por lo que no depende de mantener
abierta la barra lateral.

### Resultados para el cliente

- **Consultar un paciente:** formulario de riesgo, explicación del modelo
  operativo y asistente opcional (se conserva `app/paginas/estimar.py`).
- **Entender el modelo:** ficha informativa y metodología del modelo
  actual (disponible también para personal asistencial).
- **Procesar varios pacientes:** carga CSV y priorización de seguimiento
  (`app/paginas/lote.py`). Esta subopción conserva el permiso
  existente: solo aparece para coordinación.

El perfil asistencial accede a la consulta individual y a la ficha del
modelo, sin abrir las funciones de coordinación. La sección
de entrenamiento no se expone al usuario asistencial.

### Laboratorio y evaluación

Solo para coordinación. Agrupa en una segunda navegación horizontal:
- **Entrenar y comparar:** validación, preparación, dos entrenamientos
  independientes (Gradient Boosting / MLP), métricas e interpretación
  comprensible de resultados.
- **Resultados del modelo oficial:** desempeño y matrices históricas.
- **Equidad y límites:** auditoría de subgrupos y advertencias.
- **Cómo se construyó:** ficha metodológica del modelo.

Los módulos internos existentes se reutilizan, sin mezclar resultados
experimentales con el modelo que usa el cliente.

## Corrección del botón de barra lateral

El CSS anterior aplicaba `height: 0` al encabezado de Streamlit,
pudiendo ocultar el control de reapertura. Se retiró esa regla,
se dejó visible el control nativo `stSidebarCollapsedControl` y la
navegación principal pasó al contenido de la página.

La portada utiliza el estado `collapsed` de Streamlit; con una
sesión iniciada, el estado por defecto es `expanded`. El usuario
puede contraer y expandir el panel sin perder la capacidad de navegar.

## Pruebas sugeridas

1. Ejecutar `python -m unittest discover -s tests -v`.
2. Abrir `streamlit run app/app.py`, iniciar sesión como coordinador.
3. Confirmar que aparecen **solo dos áreas** en la navegación principal.
4. Contraer el panel izquierdo, comprobar que vuelve a aparecer el control
   de apertura y cambiar entre las áreas sin reabrirlo.
5. En **Resultados**, comprobar consulta individual y CSV.
6. En **Laboratorio**, comprobar las cuatro subopciones y la explicación
   posterior a la comparación.
7. Cerrar sesión, iniciar con el rol asistencial, comprobar que el laboratorio
   no está disponible y que la consulta individual sigue funcionando.
8. Verificar visualmente en pantalla ancha y dispositivo móvil.

**Alcance:** este cambio reorganiza y simplifica la presentación de
funciones existentes. No reentrena el modelo oficial ni modifica sus datos,
archivos o métricas. Las pruebas estáticas no sustituyen la comprobación
visual del botón en un navegador real.
