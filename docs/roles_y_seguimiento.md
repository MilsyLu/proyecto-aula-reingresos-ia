# ReingresaIA — experiencia por roles y registro de contactos

Este diseño se implementó **solo** en la rama
`experiment/reingresaia-ui`. La rama `main` no se modifica.

## Personal asistencial: únicamente cuatro apartados

| Apartado | Función del usuario |
| --- | --- |
| **Inicio** | Pacientes registrados, pendientes, con alerta, llamadas próximas y lista prioritaria |
| **Pacientes** | Buscar, filtrar y consultar fichas; editar observaciones, agendar, cerrar/reabrir seguimiento; registrar y revisar llamadas |
| **Estimar riesgo** | Revisar los 15 datos de la hospitalización, calcular una probabilidad y registrar el caso |
| **Agenda** | Revisar la semana, llamar y programar pendientes sin fecha |

En estos apartados NO aparecen las 12 fases, el mapa de calor, las métricas
de entrenamiento, la arquitectura del modelo, los hiperparámetros ni la
comparación experimental. La explicación del resultado no se interpreta como
un diagnóstico ni una certeza de reingreso.

El formulario requiere pulsar **Calcular riesgo** y confirmar que se han
revisado los valores. El asistente solo aparece como ayuda desplegable
después de obtener el resultado. No tiene acceso independiente en el
menú asistencial.

## Administrador

El administrador conserva las cuatro funciones asistenciales y además
dispone de dos áreas de administración con subopciones agrupadas:

- **Gestión administrativa:** carga masiva CSV/Excel, configuración del
  umbral y reportes Excel/PDF.
- **Laboratorio de IA:** definición del problema, 12 fases, origen de datos,
  EDA, entrenamiento, comparación de Gradient Boosting y MLP,
  métricas, importancia, equidad, limitaciones y trazado interno.

La lista histórica de hospitalizaciones del conjunto de prueba se conserva
en el laboratorio, separada de los pacientes operativos guardados para
seguimiento. No deben confundirse ni sumarse como la misma población.

Los roles se verifican tanto en el menú como en las rutas del frontend
y en las dependencias de autorización de la API.

## Ficha del paciente

- Identificación: nombre, documento, teléfono, resumen clínico con edad
  y sexo, fecha de alta.
- Riesgo: probabilidad estimada con el modelo oficial y estado de alerta.
- Seguimiento: estado, fecha de próxima llamada, observaciones generales.
- Contactos: fecha/hora de registro, usuario que hizo la gestión,
  resultado de la llamada, observaciones de ese contacto y próxima fecha
  cuando corresponda.

Los contactos históricos se conservan en una tabla SQLite independiente
(`contactos`) y no se sobrescriben al cambiar las notas generales.
Las opciones de resultado son `contactado`, `sin_respuesta` y
`reprogramar`. Reprogramar exige una fecha no anterior a hoy.

Las rutas nuevas son:

- `GET /api/seguimiento/{id}/contactos`
- `POST /api/seguimiento/{id}/contactos`

Se conserva la API previa para listar pacientes, cambiar observaciones y
agendar. La tabla histórica se crea automáticamente con
`CREATE TABLE IF NOT EXISTS`; no elimina la información anterior.

La eliminación de un registro de seguimiento también elimina su historial
relacionado y pide confirmación explícita en la interfaz.

## Prueba de aceptación (Windows)

1. Iniciar API FastAPI y frontend React con los comandos de
   `docs/ejecucion_local_reingresaia.md`.
2. Iniciar sesión con perfil **Personal asistencial**. Confirmar que el
   menú tiene exactamente Inicio, Pacientes, Estimar riesgo y Agenda.
3. Intentar abrir por URL `/app/modelos`, `/app/entrenar`,
   `/app/archivo` y `/app/umbral`: deben redirigir a Inicio; la API
   también debe denegar peticiones sin permiso.
4. Estimar un caso, confirmar los datos, pulsar Calcular riesgo y
   registrarlo para seguimiento.
5. Abrir Pacientes, seleccionar el registro, guardar dos contactos con
   resultados distintos y recargar: deben conservarse ambos.
6. Agendar una llamada y comprobarla en Agenda.
7. Iniciar sesión con perfil **Administrador**; comprobar gestión
   administrativa, carga masiva y laboratorio.
8. Revisar claridad del texto, scroll de tablas y ficha lateral con
   tema claro/oscuro y en ancho reducido.

**Seguridad:** prototipo académico. Utilice exclusivamente información
ficticia o anonimizada, nunca datos personales reales de pacientes.
