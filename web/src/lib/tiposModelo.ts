/** Lo que la API devuelve para estimar y trazar. Compartido por las pantallas. */

export interface OpcionCampo {
  valor: string
  etiqueta: string
}

export interface CampoFormulario {
  campo: string
  nombre: string
  tipico: string | number
  tipico_mostrado: string
  opciones: OpcionCampo[] | null
}

export interface Opciones {
  campos: CampoFormulario[]
  umbral: number
  tasa_base: number
}

export interface Efecto {
  campo: string
  nombre: string
  valor: string
  tipico: string
  sin_el: number
  efecto: number
}

export interface Estimacion {
  probabilidad: number
  umbral: number
  supera: boolean
  tasa_base: number
  veces_la_base: number
  efectos: Efecto[]
}

export interface PasoArbol {
  n: number
  aporte: number
  acumulado: number
  probabilidad: number
}

export interface Trazado {
  escrito: { campo: string; nombre: string; valor: string; es_tipico: boolean }[]
  columnas: {
    resumen: { total: number; del_formulario: number; calculadas: number; tipicas: number }
    detalle: { columna: string; valor: string; origen: string }[]
  }
  vacios: { columna: string; relleno: string }[]
  codificadas: {
    detalle: { columna: string; valor: string; codigo: number; conocida: boolean; posibles: number }[]
    no_vistas: { columna: string; valor: string }[]
  }
  partida: { log_odds: number; probabilidad: number }
  arboles: {
    total: number
    pasos: PasoArbol[]
    mas_fuertes: PasoArbol[]
    fraccion_primeros_quince: number
  }
  final: { log_odds: number; probabilidad: number; del_modelo: number; coincide: boolean }
  umbral: { valor: number; supera: boolean; tasa_base: number; veces_la_base: number | null }
}

/** Los quince campos, agrupados como los piensa quien los llena. */
export const GRUPOS_CAMPOS: { titulo: string; campos: string[] }[] = [
  { titulo: 'La persona', campos: ['edad', 'genero'] },
  {
    titulo: 'Esta hospitalización',
    campos: ['dias', 'diag1', 'egreso', 'diagnosticos', 'procedimientos', 'labs', 'meds'],
  },
  { titulo: 'En el año previo', campos: ['ingresos', 'urgencias', 'consultas'] },
  { titulo: 'Medicación', campos: ['a1c', 'insulina', 'cambio'] },
]

/** Topes que la API también valida. Aquí evitan el viaje de ida y vuelta. */
export const LIMITES: Record<string, { min: number; max: number }> = {
  edad: { min: 0, max: 100 },
  ingresos: { min: 0, max: 25 },
  urgencias: { min: 0, max: 80 },
  consultas: { min: 0, max: 45 },
  dias: { min: 1, max: 14 },
  labs: { min: 0, max: 140 },
  meds: { min: 0, max: 85 },
  diagnosticos: { min: 1, max: 16 },
  procedimientos: { min: 0, max: 7 },
}
