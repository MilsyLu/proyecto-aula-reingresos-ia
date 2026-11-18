# Guion de sustentación — 22 minutos + preguntas

Proyecto de aula de IA · Grupo 04 · Predicción de reingresos hospitalarios a 30 días

---

## Cómo usar este guion

No está hecho para leerse. Está hecho para que sepas **qué tienes que lograr en cada bloque**.

Cada sección trae tres cosas:

- **La idea que no puede faltar** — si solo te acordaras de una frase, es esa.
- **Qué mostrar** — de dónde sacas el apoyo visual.
- **El detalle** — lo que desarrollas si te sobra tiempo.

Al final hay un bloque de **preguntas probables con su respuesta**. Esa parte vale tanto como
la exposición.

**Antes de empezar:** abre la aplicación cinco minutos antes. Si lleva días dormida tarda en
despertar.

---

# BLOQUE 1 · El problema (2 min)

### La idea que no puede faltar

> "Si un hospital solo puede hacer seguimiento a una parte de los pacientes que da de alta,
> ¿a cuáles elige? Nuestro modelo no decide. Ordena la lista."

### El detalle

- Entre el 15 y el 20 % de los pacientes reingresan antes de 30 días.
- Buena parte se considera **evitable**: no falló la atención durante el ingreso, falló lo
  que pasó después.
- Los programas de seguimiento post-alta existen, pero son caros y no alcanzan para todos.
- Elegimos población diabética porque concentra comorbilidades, medicación compleja y una tasa
  de reingreso superior a la media.

---

# BLOQUE 2 · Los datos (3 min)

### La idea que no puede faltar

> "El 11,39 % reingresa. Eso significa que un modelo que siempre diga *no reingresa* acierta
> el 88,61 % de las veces sin servir para nada. Por eso la exactitud no fue nuestro criterio."

### Qué mostrar

Página **Ficha del modelo** de la aplicación.

### El detalle

| | |
|---|---|
| Fuente | Diabetes 130-US hospitals, 1999–2008 (UCI) |
| Original | 101.766 hospitalizaciones · 71.518 pacientes · 50 columnas |
| Cohorte | 99.343 hospitalizaciones · 69.990 pacientes |
| Positivos | 11.314 (11,39 %) |

**Por qué quitamos 2.423 registros:** eran pacientes fallecidos o derivados a cuidado
paliativo. No pueden reingresar. Si los dejábamos, el modelo aprendía a predecir "no
reingresa" en casos donde el reingreso era **imposible por definición**, y el desempeño salía
inflado.

**La variable objetivo:** la columna original tiene tres valores —reingreso antes de 30 días,
después de 30 días, y no reingreso—. Lo volvimos binario: solo `<30` es positivo. Los
reingresos posteriores quedan fuera de la ventana en la que un programa de seguimiento puede
hacer algo.

---

# BLOQUE 3 · Metodología (5 min)

## 3.1 La partición (el punto que más vale)

### La idea que no puede faltar

> "Dividimos **por paciente**, no por fila. 16.341 pacientes tienen más de una
> hospitalización."

### El detalle

Si repartes las filas al azar, dos hospitalizaciones de la misma persona caen una en
entrenamiento y otra en prueba. El modelo **reconoce a la persona** en vez de aprender el
fenómeno, y el resultado sale optimista.

Usamos `StratifiedGroupKFold`, que hace dos cosas a la vez:

- **Group**: agrupa por el identificador del paciente, para que nadie quede en dos conjuntos.
- **Stratified**: mantiene el 11,39 % de positivos en cada parte.

| Conjunto | Hospitalizaciones | Pacientes | Prevalencia | Para qué |
|---|---|---|---|---|
| Entrenamiento | 59.605 | 41.988 | 11,390 % | Ajustar el modelo |
| Validación | 19.868 | 13.982 | 11,385 % | Decidir |
| Prueba | 19.870 | 14.020 | 11,389 % | Medir una vez |

**La diferencia entre validación y prueba** (pregunta frecuente): validación es el conjunto
con el que *se toman decisiones*, y por eso se contamina —se mira muchas veces—. Prueba es el
que se mira *una sola vez*, cuando ya no queda nada por decidir.

## 3.2 Preprocesamiento

### La idea que no puede faltar

> "Todas las transformaciones se ajustaron **solo con entrenamiento**. Eso es lo que evita la
> fuga de información."

### El detalle

De las 50 columnas originales:

- **3 no son del paciente**: dos identificadores y la variable objetivo.
- **4 se reemplazaron**: la edad venía en rangos de texto y la volvimos número; los tres
  diagnósticos tenían más de 700 códigos cada uno y los agrupamos en 9 familias clínicas.
- **5 se quitaron**: el peso (vacío en el 96,9 %), el código de asegurador (vacío en el 39,6 %
  y no describe al paciente), dos medicamentos con un solo valor en toda la base, y **la raza,
  que apartamos a propósito para usarla como auditoría**.

Añadimos **12 variables derivadas**. El conjunto final: **50 predictores, 17 numéricos y 33
categóricos**.

> Si te preguntan qué es la mediana: es el valor del medio cuando ordenas todos los datos. Se
> usa en vez del promedio porque no se deja arrastrar por valores extremos.

## 3.3 Los modelos

Subimos en escalera, para que cada modelo tuviera que justificar su costo:

1. **Mayoritario** — siempre dice "no reingresa". Es el piso.
2. **Regresión logística** — la referencia real.
3. **Gradient Boosting** — el propuesto. Elegimos la variante por histogramas porque es unas
   nueve veces más rápida, maneja faltantes sola y acepta categóricas sin expandirlas.

**30 combinaciones** de hiperparámetros con búsqueda aleatoria, optimizando Average Precision,
con validación cruzada **dentro del entrenamiento**.

## 3.4 El umbral

### La idea que no puede faltar

> "El umbral no es una decisión estadística. Es una decisión de política."

Un clasificador devuelve una probabilidad, no un sí o un no. Convertirla en alerta exige fijar
un corte, y ese corte define cuántos reingresos detectas y cuántas llamadas inútiles haces.

Lo fijamos en **0,1123**, el valor que da sensibilidad 0,60 en validación, siguiendo la
prioridad que habíamos declarado en la Fase 1: **dejar pasar un reingreso cuesta más que hacer
una llamada de más.**

---

# BLOQUE 4 · Resultados (4 min)

### Qué mostrar

Página **Desempeño del modelo**.

### Las cifras

| Métrica | Prueba | IC 95 % |
|---|---|---|
| Average Precision | **0,2249** | 0,2047 – 0,2467 |
| ROC-AUC | **0,6660** | 0,6527 – 0,6786 |
| Sensibilidad | **0,6001** | 0,5766 – 0,6202 |
| Precisión | 0,1781 | |
| Brier | 0,0963 | |

### La idea que no puede faltar

> "El AP de prueba es 0,2249 y el de validación 0,2238. **Que coincidan es la prueba de que no
> hubo sobreajuste ni fuga.** El modelo rinde con datos nuevos lo mismo que rendía con los
> que ya conocía."

### En palabras de la vida real

"De cada 100 pacientes dados de alta, el modelo marcaría a 38. Entre esos 38 estarían 7 de los
11 que efectivamente van a reingresar, y 31 personas que no lo harían recibirían una llamada
que no necesitaban."

### La escalera completa

| Modelo | AP | Lectura |
|---|---|---|
| Mayoritario | 0,1139 | El azar |
| Regresión logística | 0,2136 | +88 % sobre el azar |
| Gradient Boosting ajustado | 0,2249 | +4,8 % sobre la logística |

> **Sé honesta con esto:** el salto grande no lo da el modelo sofisticado, lo da **tener un
> modelo**. Decirlo tú antes de que te lo pregunten juega a tu favor.

### La meta que no se cumplió

De las cuatro metas de la Fase 1 cumplimos tres. La de precisión no.

**Y no es que quedara cerca: es que la combinación no existe.**

- Exigiendo sensibilidad 0,60 → la precisión máxima es 0,177.
- Exigiendo precisión 0,20 → la sensibilidad máxima es 0,481.

> "Pudimos haber bajado la meta para que el proyecto 'cumpliera'. No lo hicimos, porque eso
> vaciaba de sentido el haber fijado criterios antes de entrenar."

---

# BLOQUE 5 · Análisis crítico (4 min)

> **Este es el bloque que distingue el proyecto.** Si vas corta de tiempo, recorta el bloque 3,
> nunca este.

## Hallazgo 1 · El modelo mira lo administrativo

### Qué mostrar

Figura 5 del informe (la de barras naranjas y azules).

Medimos **importancia por permutación**: desordenas una variable al azar, vuelves a predecir y
ves cuánto cae el resultado. Si cae mucho, el modelo dependía de ella.

- `number_inpatient` (hospitalizaciones previas): **25,1 %**
- `discharge_disposition_id` (tipo de egreso): **18,4 %**
- **Las dos juntas: 43,5 %**
- De las 50 variables, **21 no aportan nada**.

> "El modelo se apoya mucho más en el historial administrativo del paciente que en su estado
> clínico actual. Los 23 medicamentos, la hemoglobina glicosilada, los procedimientos
> —justamente la información clínica rica que hacía atractivo este conjunto de datos— pesan
> muy poco."

## Hallazgo 2 · La cifra global esconde el caso de uso real

### Qué mostrar

Página **Equidad y límites**, la tabla de transferencias.

| | n | Sensibilidad |
|---|---|---|
| Prueba completa | 19.870 | 0,6001 |
| Transferidos a otra institución | 4.144 | **0,8822** |
| Dados de alta a casa | 15.726 | **0,4834** |

### La idea que no puede faltar

> "El 0,60 es un promedio entre dos poblaciones que el modelo trata de forma completamente
> distinta. Y los que se van a casa son el 79 % de la cohorte: justamente aquellos para
> quienes está pensado el programa de seguimiento. **La sensibilidad útil no es 0,60. Es
> 0,48.**"

**Por qué pasa:** que a un paciente lo transfieran a otra institución ya es, en sí mismo, una
señal casi definitiva de fragilidad. No está en condiciones de irse a su casa. El modelo
aprendió a reconocer esa señal, que es fácil, y eso le subió el promedio.

## Hallazgo 3 · El techo son los datos, no el modelo

- La logística llega a 0,654 de ROC-AUC y el Gradient Boosting a 0,666. **Cambiar de
  arquitectura da un 1,8 %.** La señal disponible está agotada, no mal explotada.
- La literatura sobre esta misma base reporta 0,64–0,70. Estamos dentro.
- Probamos un segundo conjunto de datos (reclamaciones sintéticas de Medicare) y dio igual o
  peor. **El techo no era una peculiaridad de nuestra base.**
- Lo que de verdad determina un reingreso —soporte familiar, si consiguió el medicamento, si
  le dieron cita— **no está en los datos**.

---

# BLOQUE 6 · Ética y sesgos (3 min)

### La idea que no puede faltar

> "Un modelo que ordena pacientes para recibir un recurso escaso **redistribuye atención**. Si
> se equivoca sistemáticamente contra un grupo, ese grupo recibe menos cuidado."

### Cómo lo medimos

- **Paridad demográfica**: ¿alerta por igual entre grupos? Referencia: la regla de los cuatro
  quintos (por debajo de 0,80 hay indicio de trato desigual).
- **Igualdad de oportunidad**: entre los que sí van a reingresar, ¿detecta a unos más que a
  otros?
- **Regla de prudencia**: no interpretamos ningún subgrupo con menos de 50 casos o menos de 10
  reingresos.

### Resultados

| Atributo | Razón de paridad | Veredicto |
|---|---|---|
| Género | 0,905 | Aceptable |
| Grupo racial | 0,786 | Requiere matiz |
| **Edad** | **0,569** | **Problema real** |

### Sobre la raza — di esto exactamente

> "La razón de 0,786 la baja el grupo `Asian`, que tiene solo 143 casos. Entre los dos grupos
> con tamaño suficiente, `Caucasian` con 14.717 y `AfricanAmerican` con 3.782, la razón es
> **0,987**: prácticamente iguales.
>
> **No es lo mismo decir que no hay sesgo que decir que no hay datos para medirlo.**"

### Sobre la edad — el hallazgo que sí preocupa

| Edad | Prevalencia real | Tasa de alerta | ROC-AUC |
|---|---|---|---|
| Menos de 50 | 11,50 % | **30,2 %** | **0,713** |
| 80 o más | 11,89 % | **51,3 %** | **0,619** |

Dos cosas, y las dos apuntan igual:

1. **Alerta mucho más sobre los mayores, pero su riesgo real es casi idéntico.** La diferencia
   no está justificada por los datos.
2. **Y encima discrimina peor justo en ese grupo** (el ROC-AUC baja de 0,713 a 0,619).

> "Si el programa se aplicara tal cual, la mitad de los mayores de 80 entraría en la lista,
> consumiendo recursos que tal vez rindan más en otro lado."

### Sobre excluir la raza del modelo

> "Excluir una variable sensible **no elimina el sesgo**, porque otras la representan
> indirectamente. Solo impide usarla explícitamente. Por eso la conservamos: para poder medir
> el sesgo que de todos modos queda."

---

# BLOQUE 7 · La solución entregada (3 min)

### Qué mostrar

Demostración en vivo. **Esta parte se ensaya.**

1. **Estimar riesgo** — calcula con el perfil por defecto: **9,0 %**. Sube las
   hospitalizaciones previas a 5 → sube a **30 %**. "Reacciona a lo que uno esperaría."
2. **Desempeño** — mueve el control del umbral. "Esto no es un adorno: hace tangible que el
   umbral es una decisión de política. Si lo bajo detecto más y molesto más. El modelo no
   puede decidir dónde ponerlo; lo decide el hospital según a cuánta gente pueda seguir."
3. **Equidad y límites** — "aquí publicamos lo que el modelo hace mal."
4. **Ficha del modelo** — "y aquí todo lo necesario para auditarlo."

### Lo que conviene decir

> "La aplicación muestra siempre que de cada 6 alertas solo 1 corresponde a un reingreso real.
> Lo pusimos a la vista a propósito: un prototipo que esconde su tasa de error es más
> peligroso que útil."

**Reproducibilidad:** cinco cuadernos que se ejecutan en orden, semillas fijadas, partición
determinista. Cualquiera puede regenerar todas las cifras del informe desde los datos crudos.

---

# BLOQUE 8 · Conclusiones (2 min)

1. **El objetivo técnico se alcanzó.** Partición correcta, sin fuga, prueba intacta hasta el
   final. AP casi duplica el azar y tres de cuatro metas cumplidas.
2. **La ganancia del modelo complejo es pequeña.** El valor está en el procedimiento, no en el
   algoritmo.
3. **La cifra global escondía el caso de uso real**: 0,88 contra 0,48. Es nuestro resultado
   más importante y no se habría visto sin el análisis de sensibilidad.
4. **Hay una disparidad por edad** que debe resolverse antes de cualquier uso.
5. **Una meta no se cumplió y la reportamos como tal.**

### El cierre

> "Nuestro veredicto es: **viabilidad demostrada, uso clínico no recomendado.** El enfoque
> funciona y la infraestructura está resuelta, pero el desempeño real y los sesgos no permiten
> que esto oriente decisiones sobre pacientes hoy.
>
> Y creemos que poder decir eso, con los números en la mano, es el resultado más serio del
> proyecto."

---

# PREGUNTAS PROBABLES

### "¿Por qué el modelo rinde tan poco? Un AUC de 0,666 es bajo."

> "Sí, y lo decimos en el informe. Pero no es un problema del modelo: la regresión logística
> llega a 0,654 y el Gradient Boosting a 0,666. Cambiar de arquitectura da un 1,8 %. La señal
> disponible está agotada. Lo que de verdad determina un reingreso —si tiene quien lo cuide,
> si consiguió el medicamento, si le dieron cita— no está en estos datos. Lo comprobamos
> además con un segundo conjunto de datos, y dio igual o peor."

### "¿Por qué no usaron una red neuronal?"

> "La consideramos y la dejamos fuera a propósito. Con una señal que la logística ya explota
> casi por completo, una red añadiría complejidad y opacidad sin ganancia medible. Además, en
> un contexto clínico la explicabilidad vale: podemos decir qué variables pesan y cuánto, y
> con una red sería más difícil. Es una línea de trabajo futuro, pero no la prioridad."

### "¿Cómo manejaron el desbalance de clases?"

> "De tres formas. Primero, usando Average Precision y no exactitud como criterio. Segundo,
> probando `class_weight='balanced'` en la búsqueda de hiperparámetros: **la búsqueda lo
> descartó**, mover el umbral resultó más eficaz y además deja mejor calibradas las
> probabilidades. Tercero, eligiendo el umbral explícitamente en validación. El desbalance lo
> tratamos en el umbral, no en el entrenamiento."

### "¿Cómo se aseguran de que no hubo fuga de información?"

> "Tres cosas. Las transformaciones se ajustaron solo con entrenamiento, dentro de un
> `Pipeline`. La partición es por paciente, así que nadie aparece en dos conjuntos. Y el
> resultado lo confirma: el AP de validación es 0,2238 y el de prueba 0,2249. Si hubiera
> fuga, la prueba habría salido peor."

### "¿Por qué quitaron la raza si podría ser predictiva?"

> "Por una decisión ética, y la documentamos. La apartamos del modelo pero la conservamos
> **para auditarlo**. Y somos explícitos en algo: excluirla no elimina el sesgo, porque otras
> variables la representan indirectamente. Solo impide usarla de forma explícita."

### "¿Este modelo se podría usar en un hospital de Valledupar?"

> "Hoy no, y por varias razones. Los datos son de hospitales de Estados Unidos entre 1999 y
> 2008: otro sistema de salud, otras prácticas, otros medicamentos. Haría falta reentrenarlo
> con datos locales y repetir toda la auditoría. Y aun así, la disparidad por edad habría que
> resolverla antes."

### "¿Qué pasa si el modelo se equivoca con un paciente?"

> "Por diseño, no puede hacer daño directo: la salida solo puede **añadir** seguimiento, nunca
> quitar atención. Lo dejamos escrito en la ficha del modelo. El riesgo real es otro: que
> alguien lo lea como un diagnóstico. Por eso la aplicación muestra siempre que de cada 6
> alertas solo 1 acierta."

### "¿Por qué eligieron Average Precision y no exactitud o F1?"

> "La exactitud no sirve: el modelo trivial saca 88,61 %. El F1 mezcla precisión y
> sensibilidad en un solo número y esconde el intercambio, que es justo lo que queríamos ver.
> El Average Precision resume el comportamiento del modelo **en todos los umbrales** y está
> pensado para clases desbalanceadas. Y además reportamos la matriz de confusión completa,
> para que nadie tenga que confiar en un solo número."

### "¿Qué aprendieron?"

> "Que la parte difícil no fue entrenar el modelo. Fue auditarlo. Nuestro mejor resultado no
> es una métrica: es haber descubierto que el 0,60 que íbamos a reportar escondía un 0,48 en
> la población que de verdad importaba."

### Si no sabes la respuesta

> "No lo medimos. Lo que sí puedo decirle es [lo más cercano que sí midieron], y mediría
> [cómo] para responderlo."

No inventes. Decir "no lo medimos" con claridad puntúa mejor que improvisar.

---

## Reparto sugerido entre los tres

| Integrante | Bloques | Minutos |
|---|---|---|
| 1 | Problema, datos, metodología (1–3) | ~10 |
| 2 | Resultados y análisis crítico (4–5) | ~8 |
| 3 | Ética, demostración y conclusiones (6–8) | ~8 |

Las preguntas las responde **quien domine el tema**, no quien expuso ese bloque. Acuérdenlo
antes.
