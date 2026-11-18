# Guía para armar el tablero en Power BI

Proyecto de aula de IA — Grupo 04 · Universidad Popular del Cesar

Esta guía construye un tablero de **tres páginas** sobre los resultados reales del modelo.
Se sigue de principio a fin sin escribir código, salvo copiar y pegar nueve fórmulas.

**Tiempo estimado:** 40 minutos.

---

## Antes de empezar

El archivo de datos ya está preparado:

```
reports\tablero_powerbi.csv
```

Son las **19.870 hospitalizaciones del conjunto de prueba** —el que el modelo nunca vio
durante el entrenamiento— con lo que el modelo predijo y lo que realmente pasó.

> Ese archivo se guardó con punto y coma y coma decimal **a propósito**, para que Power BI en
> español lo lea bien sin tener que cambiar nada.

### Qué significa cada columna

| Columna | Qué es |
|---|---|
| `Probabilidad` | Lo que el modelo estimó, entre 0 y 1 |
| `Alerta` | 1 si la probabilidad supera el umbral 0,1123; 0 si no |
| `Reingreso real` | 1 si el paciente sí volvió antes de 30 días |
| `Reingreso` | Lo mismo pero en texto: "Si reingreso" / "No reingreso" |
| `Resultado` | VP, FN, FP o VN ya clasificado |
| `Tipo de egreso` | "Transferido a otra institucion" o "Dado de alta a casa" |
| `Grupo racial`, `Genero`, `Grupo de edad` | Para la auditoría de equidad |
| `Edad`, `Dias de estancia`, `Ingresos previos`, `Medicamentos`, `Diagnosticos` | Datos del paciente |
| `Orden edad` | Columna auxiliar: sirve solo para ordenar los grupos de edad (paso 4.1) |

---

## Paso 1 · Traer los datos

1. Abre **Power BI Desktop**.
2. Cinta **Inicio** → **Obtener datos** → **Texto o CSV**.
3. Busca y selecciona `reports\tablero_powerbi.csv`.
4. En la ventana de vista previa, comprueba tres cosas:
   - **Origen del archivo:** `65001: Unicode (UTF-8)`
   - **Delimitador:** `Punto y coma`
   - La columna `Probabilidad` muestra números como `0,124993`
5. Botón **Cargar** (no "Transformar datos", no hace falta).

Al terminar, a la derecha debe aparecer la tabla **tablero_powerbi** con sus 16 columnas.

---

## Paso 2 · Crear las medidas

Una **medida** es un cálculo que se reajusta solo según lo que esté filtrado en pantalla. Son
el corazón del tablero: gracias a ellas, al hacer clic en "80 o más" todos los números se
recalculan para ese grupo.

Para cada una de las nueve fórmulas de abajo:

1. Cinta **Inicio** → **Nueva medida**.
2. Se abre una barra de fórmulas arriba. **Borra** lo que diga y **pega** la fórmula completa.
3. Pulsa **Enter**.

> Copia la fórmula entera, incluido el nombre y el signo igual.

```DAX
Hospitalizaciones = COUNTROWS('tablero_powerbi')
```

```DAX
Reingresos reales = SUM('tablero_powerbi'[Reingreso real])
```

```DAX
Alertas = SUM('tablero_powerbi'[Alerta])
```

```DAX
VP = CALCULATE([Alertas], 'tablero_powerbi'[Reingreso real] = 1)
```

```DAX
FN = [Reingresos reales] - [VP]
```

```DAX
FP = [Alertas] - [VP]
```

```DAX
Sensibilidad = DIVIDE([VP], [Reingresos reales])
```

```DAX
Precision = DIVIDE([VP], [Alertas])
```

```DAX
Tasa de alerta = DIVIDE([Alertas], [Hospitalizaciones])
```

### Darles formato de porcentaje

Las tres últimas (`Sensibilidad`, `Precision`, `Tasa de alerta`) salen como `0,60`. Para que
se vean como `60,0 %`:

1. Haz clic en la medida en el panel de la derecha.
2. Cinta **Herramientas de medidas** → en **Formato**, elige **Porcentaje** y pon **1** decimal.

### Comprobación

Arrastra `Sensibilidad` a un objeto visual de **Tarjeta**. Debe dar **60,0 %**.
Si da otra cosa, alguna fórmula quedó mal escrita.

---

## Paso 3 · Página 1: Resumen del modelo

Cambia el nombre de la pestaña de abajo a **Resumen** (doble clic sobre ella).

### 3.1 Fila de tarjetas

Inserta **cinco tarjetas** (icono *Tarjeta* en Visualizaciones) y ponles una medida a cada una:

| Tarjeta | Campo | Debe mostrar |
|---|---|---|
| 1 | `Hospitalizaciones` | 19.870 |
| 2 | `Reingresos reales` | 2.263 |
| 3 | `Alertas` | 7.624 |
| 4 | `Sensibilidad` | 60,0 % |
| 5 | `Precision` | 17,8 % |

Colócalas en fila a lo largo de la parte superior.

### 3.2 Matriz de confusión

1. Inserta un objeto visual **Matriz**.
2. **Filas:** `Reingreso`
3. **Columnas:** `Alerta`
4. **Valores:** `Hospitalizaciones`

Debe quedar así:

| | 0 | 1 |
|---|---|---|
| **No reingreso** | 11.341 | 6.266 |
| **Si reingreso** | 905 | 1.358 |

> Esos cuatro números son el modelo entero. 1.358 reingresos detectados a tiempo, 905 que se
> escaparon, 6.266 falsas alarmas y 11.341 aciertos en negativo.

### 3.3 Distribución del riesgo

1. Inserta un **Gráfico de columnas agrupadas**.
2. **Eje X:** `Probabilidad`
3. En el eje X, haz clic en la flechita del campo → elige **No resumir**.
4. **Eje Y:** `Hospitalizaciones`
5. **Leyenda:** `Reingreso`

Se ve que las dos curvas se solapan mucho: es la razón visual de por qué la precisión es baja.

### 3.4 Segmentación por resultado

Inserta una **Segmentación de datos** con el campo `Resultado`. Al hacer clic en
"FN - reingreso no detectado" el resto de la página se filtra a los 905 casos que se
escaparon.

---

## Paso 4 · Página 2: Equidad

Nueva página (botón **+** abajo), nómbrala **Equidad**.

### 4.1 Tasa de alerta por grupo de edad

1. **Gráfico de columnas agrupadas**.
2. **Eje X:** `Grupo de edad`
3. **Eje Y:** `Tasa de alerta`

**Ordena bien los grupos.** Por orden alfabético "Menos de 50" quedaría al final, así que el
archivo trae una columna auxiliar llamada `Orden edad` para arreglarlo:

4. En el panel derecho, haz clic en el campo **`Grupo de edad`** (en la tabla, no en el
   gráfico).
5. Cinta **Herramientas de columnas** → **Ordenar por columna** → elige **`Orden edad`**.
6. Vuelve al gráfico, clic en los **tres puntos** de su esquina → **Ordenar eje** →
   `Grupo de edad`, y de nuevo tres puntos → **Orden ascendente**.

Debe subir de **30,2 %** a **51,3 %**. Ese es el hallazgo de equidad del proyecto.

### 4.2 La comparación que lo hace evidente

Repite el gráfico anterior **al lado**, pero en el eje Y pon **dos campos**: `Tasa de alerta` y
una medida nueva:

```DAX
Prevalencia real = DIVIDE([Reingresos reales], [Hospitalizaciones])
```

(dale formato de porcentaje con 1 decimal)

El contraste es el argumento completo: **la tasa de alerta sube 21 puntos con la edad, pero la
prevalencia real se mueve menos de medio punto.** El modelo alerta más sobre los mayores sin
que su riesgo real sea mayor.

### 4.3 Tabla por subgrupo

Inserta una **Tabla** con:

- `Grupo racial` (o `Genero`, o `Grupo de edad`)
- `Hospitalizaciones`
- `Prevalencia real`
- `Tasa de alerta`
- `Sensibilidad`
- `Precision`

### 4.4 Segmentación por género

Una **Segmentación de datos** con `Genero`, para poder cruzar.

---

## Paso 5 · Página 3: El efecto del tipo de egreso

Nueva página, nómbrala **Tipo de egreso**.

### 5.1 Segmentación principal

**Segmentación de datos** con `Tipo de egreso`, bien visible arriba.

### 5.2 Tarjetas que reaccionan

Debajo, tres tarjetas: `Hospitalizaciones`, `Sensibilidad`, `Prevalencia real`.

Ahora haz clic en cada opción de la segmentación y observa:

| Selección | Hospitalizaciones | Sensibilidad |
|---|---|---|
| *(nada seleccionado)* | 19.870 | 60,0 % |
| Transferido a otra institucion | 4.144 | 88,2 % |
| Dado de alta a casa | 15.726 | 48,3 % |

**Esta es la diapositiva más importante del tablero.** El 60 % global es un promedio entre dos
poblaciones que el modelo trata de forma completamente distinta, y el grupo numeroso —el 79 %
que se va a casa, que es justo al que iría dirigido el programa de seguimiento— es el que peor
le sale.

### 5.3 Gráfico de apoyo

**Gráfico de columnas agrupadas** con eje X `Tipo de egreso` y eje Y `Sensibilidad`.

---

## Paso 6 · Guardar

**Archivo** → **Guardar como** → guárdalo dentro del proyecto como:

```
reports\Tablero_Reingresos_Grupo04.pbix
```

---

## Opcional · Umbral móvil

Si quieres que el tablero permita mover el umbral como lo hace la aplicación web:

1. Cinta **Modelado** → **Nuevo parámetro** → **Numérico**.
2. Rellena: **Nombre** `Umbral` · **Mínimo** `0,02` · **Máximo** `0,5` · **Incremento**
   `0,005` · **Valor predeterminado** `0,1123`. Deja marcado "Agregar segmentación".
3. Mira en el panel derecho cómo se llamó la medida que Power BI creó dentro de la tabla
   `Umbral` (suele llamarse **Valor de Umbral** o **Umbral Valor**). **Anótala tal cual.**
4. Crea estas dos medidas, **reemplazando** `'Umbral'[Valor de Umbral]` por el nombre que
   anotaste:

```DAX
Alertas moviles = CALCULATE(
    [Hospitalizaciones],
    FILTER('tablero_powerbi', 'tablero_powerbi'[Probabilidad] >= 'Umbral'[Valor de Umbral])
)
```

```DAX
VP movil = CALCULATE(
    [Hospitalizaciones],
    FILTER('tablero_powerbi',
        'tablero_powerbi'[Probabilidad] >= 'Umbral'[Valor de Umbral]
        && 'tablero_powerbi'[Reingreso real] = 1)
)
```

5. Y encima de ellas:

```DAX
Sensibilidad movil = DIVIDE([VP movil], [Reingresos reales])
```

```DAX
Precision movil = DIVIDE([VP movil], [Alertas moviles])
```

Pon `Sensibilidad movil` y `Precision movil` en dos tarjetas junto a la segmentación del
umbral. Al deslizarla se ve el intercambio: **subir el umbral mejora la precisión y empeora la
sensibilidad, siempre.** No hay ningún punto en el que las dos pasen de 0,20 y 0,60 a la vez,
que es exactamente la meta que el proyecto no pudo cumplir.

---

## Si algo no cuadra

| Síntoma | Causa | Solución |
|---|---|---|
| `Probabilidad` sale como 124993 | Power BI leyó el punto decimal como separador de miles | Vuelve a importar comprobando que el delimitador sea punto y coma |
| Los acentos salen raros (`Genero` → `Gnero`) | Codificación equivocada | Reimporta con origen `65001: Unicode (UTF-8)` |
| `Sensibilidad` da 0 o vacío | Alguna medida quedó mal escrita | Revisa que `VP` tenga `= 1` al final |
| `Sensibilidad` da algo distinto de 60,0 % | Hay un filtro activo en la página | Quita las selecciones de las segmentaciones |
