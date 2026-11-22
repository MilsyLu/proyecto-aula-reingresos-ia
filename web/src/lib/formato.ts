/**
 * Numeros al estilo colombiano: coma decimal y punto de miles.
 *
 * Esto no es un capricho de estilo. La aplicacion muestra probabilidades,
 * conteos de pacientes y metricas en la misma pantalla; si unas van con punto
 * decimal y otras con coma, el lector duda de la cifra. Un unico lugar que
 * formatee evita que cada pantalla improvise.
 */

/** 0,666 · 30,3 · 1.234,5 */
export function numero(valor: number, decimales = 1): string {
  return valor.toLocaleString('es-CO', {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  })
}

/** 99.343 */
export function entero(valor: number): string {
  return Math.round(valor).toLocaleString('es-CO', { maximumFractionDigits: 0 })
}

/**
 * Recibe una proporcion (0,303) y devuelve un porcentaje (30,3 %).
 * El espacio antes del simbolo es el que manda la norma en espanol, y es
 * un espacio duro para que el numero nunca quede separado del signo.
 */
export function porcentaje(proporcion: number, decimales = 1): string {
  return `${numero(proporcion * 100, decimales)} %`
}

/** Para cifras que ya vienen en escala 0-100. */
export function porcentajeDirecto(valor: number, decimales = 1): string {
  return `${numero(valor, decimales)} %`
}

/** 3,78× — cuantas veces algo supera a su referencia. */
export function veces(valor: number, decimales = 2): string {
  return `${numero(valor, decimales)}×`
}

/** +21,3 / −4,8 — con el signo siempre visible y el menos tipografico. */
export function conSigno(valor: number, decimales = 1): string {
  const texto = numero(Math.abs(valor), decimales)
  if (valor > 0) return `+${texto}`
  if (valor < 0) return `−${texto}`
  return texto
}

/** 13,0 s · 1 min 52 s — para los tiempos del entrenamiento en vivo. */
export function duracion(segundos: number): string {
  if (segundos < 60) return `${numero(segundos, 1)} s`
  const min = Math.floor(segundos / 60)
  const resto = Math.round(segundos % 60)
  return `${min} min ${resto} s`
}
