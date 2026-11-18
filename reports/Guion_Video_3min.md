# Guion del video — 4 minutos

Proyecto de aula de IA · Grupo 04 · Predicción de reingresos hospitalarios a 30 días

**Duración objetivo:** 4:00 (el rango pedido es 3–5)
**Palabras:** ~620, a ritmo de conversación normal

---

## Antes de grabar

Ten abiertas estas tres ventanas y pasa entre ellas con `Alt+Tab`:

1. La aplicación: **https://reingresos-grupo04.streamlit.app/**
2. El informe final en PDF
3. El repositorio en GitHub

> Entra a la aplicación **cinco minutos antes** de grabar. Si lleva días sin usarse, Streamlit
> la deja dormida y tarda medio minuto en despertar. No querrás que eso pase en cámara.

---

## 0:00 – 0:35 · El problema

> **En pantalla:** tú hablando, o la portada del informe.

"Entre el quince y el veinte por ciento de los pacientes que salen de un hospital vuelven a
ser internados antes de treinta días. Y buena parte de esos regresos se considera evitable:
una indicación que no se entendió, un medicamento que no se consiguió, una cita de control que
nunca se dio.

Los hospitales responden con programas de seguimiento después del alta. Pero esos programas
cuestan y no alcanzan para todos.

De ahí sale la pregunta de nuestro proyecto: **si solo se puede hacer seguimiento a una parte
de los pacientes, ¿a cuáles conviene elegir?** Nuestro modelo no decide nada. Ordena la lista."

---

## 0:35 – 1:05 · Los datos

> **En pantalla:** la página "Ficha del modelo" de la aplicación.

"Trabajamos con una base pública de ciento treinta hospitales de Estados Unidos: casi cien mil
hospitalizaciones de setenta mil pacientes diabéticos.

El once coma tres nueve por ciento de esas hospitalizaciones terminó en un reingreso antes de
treinta días. Esa cifra es importante porque significa que un modelo que siempre dijera *no
reingresa* acertaría el ochenta y ocho por ciento de las veces **sin servir para nada**. Por
eso no usamos la exactitud como criterio."

---

## 1:05 – 1:45 · Cómo lo hicimos

> **En pantalla:** sigue en "Ficha del modelo", o el repositorio.

"Dos decisiones marcaron todo el trabajo.

La primera: **dividimos los datos por paciente, no por fila.** Dieciséis mil pacientes tienen
más de una hospitalización. Si hubiéramos repartido las filas al azar, la misma persona habría
quedado en entrenamiento y en evaluación, y el modelo nos habría dado un resultado inflado.

La segunda: **el conjunto de prueba se miró una sola vez**, al final, cuando ya no quedaba
nada por decidir.

El modelo final es un Gradient Boosting, elegido entre treinta configuraciones."

---

## 1:45 – 2:30 · La aplicación funcionando

> **En pantalla:** demostración en vivo. Página "Estimar riesgo".

"Esto es lo que entregamos."

*(Calcula con el perfil por defecto)*

"Un paciente típico da nueve por ciento de riesgo. Ahora subo las hospitalizaciones previas
a cinco…"

*(Lo cambias y vuelves a calcular)*

"…y sube a treinta por ciento. El modelo reacciona a lo que uno esperaría que reaccione."

> **En pantalla:** página "Desempeño del modelo", mueve el control del umbral.

"Y aquí está lo que más nos gusta de la aplicación: este control no es un adorno. **Mover el
umbral es una decisión de política, no de estadística.** Si lo bajo, detecto más reingresos
pero hago más llamadas inútiles. Si lo subo, al revés. El modelo no puede decidir dónde
ponerlo. Lo decide el hospital, según cuánta gente pueda seguir."

---

## 2:30 – 3:30 · Lo que encontramos al auditarlo

> **En pantalla:** página "Equidad y límites".

"Pero la parte de la que más aprendimos no fueron los resultados. Fue auditarlos.

**Primero:** dos variables administrativas cargan el cuarenta y tres por ciento del
desempeño. Las hospitalizaciones previas y el tipo de egreso. El modelo mira mucho más el
historial burocrático del paciente que su estado clínico.

**Segundo**, y este es el importante: nuestro modelo detecta seis de cada diez reingresos.
Pero cuando separamos a los pacientes según a dónde van, esa cifra se parte en dos. Entre los
que son **transferidos a otra institución** detecta casi nueve de cada diez. Entre los que se
van **a su casa**, menos de cinco de cada diez. Y los que se van a casa son el setenta y nueve
por ciento. Son, justamente, para quienes está pensado el programa de seguimiento.

**Tercero:** el modelo alerta sobre la mitad de los pacientes mayores de ochenta años, pero
el riesgo real de ese grupo es prácticamente igual al de los menores de cincuenta. Está
alertando de más sobre los mayores **sin que los datos lo justifiquen**."

---

## 3:30 – 4:00 · El veredicto

> **En pantalla:** tú hablando.

"Cumplimos tres de las cuatro metas que nos pusimos. La cuarta no, y la reportamos como no
cumplida: no existe ningún umbral donde el modelo detecte el sesenta por ciento de los
reingresos y a la vez acierte en una de cada cinco alertas. Pudimos haber bajado la meta.
No lo hicimos.

Nuestra conclusión es que **el enfoque funciona, pero este modelo todavía no debería orientar
decisiones clínicas.** Y creemos que saber decir eso, con los números en la mano, es el
resultado más serio del proyecto.

Gracias."

---

## Consejos para la grabación

| | |
|---|---|
| **Ritmo** | Lee en voz alta y cronométrate. Si te pasas de 4:30, recorta en el minuto 1:05–1:45 |
| **Números** | Dilos en palabras, no leas "0,6001". Di "seis de cada diez" |
| **Lo que no se puede cortar** | El minuto 2:30–3:30. Ahí está todo el valor del proyecto |
| **Si te trabas** | Para, respira y repite la frase entera. Se edita después |
| **Grabación de pantalla** | Xbox Game Bar (`Win + G`) sirve y ya viene en Windows |
