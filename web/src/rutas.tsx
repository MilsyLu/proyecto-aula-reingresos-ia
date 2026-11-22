import type { ComponentType } from 'react'
import { Asistente } from './paginas/Asistente'
import { Estimar } from './paginas/Estimar'
import { Fases } from './paginas/Fases'
import { Guia } from './paginas/Guia'
import { PasoAPaso } from './paginas/PasoAPaso'

/**
 * El registro de pantallas.
 *
 * Un solo sitio decide la ruta, el titulo del menu, el grupo al que pertenece y
 * el permiso que exige. La navegacion se dibuja sola a partir de aqui, asi que
 * agregar una pantalla es agregar una linea y nada mas: no hay que tocar el
 * menu, ni el enrutador, ni el control de acceso del front.
 *
 * El permiso debe coincidir exactamente con los de `api/autenticacion.py`.
 */

export type Grupo =
  | 'Empezar aquí'
  | 'Trabajar'
  | 'Conocer los datos'
  | 'Conocer el modelo'
  | 'Aprender haciendo'

export const GRUPOS: Grupo[] = [
  'Empezar aquí',
  'Trabajar',
  'Conocer los datos',
  'Conocer el modelo',
  'Aprender haciendo',
]

export interface Pantalla {
  /** Ruta relativa dentro de /app */
  ruta: string
  /** Como aparece en el menu */
  titulo: string
  grupo: Grupo
  /** Permiso que exige, verificado de verdad en la API */
  permiso: string
  Componente: ComponentType
}

export const PANTALLAS: Pantalla[] = [
  {
    ruta: 'guia',
    titulo: 'Qué es esto',
    grupo: 'Empezar aquí',
    permiso: 'Guía',
    Componente: Guia,
  },
  {
    ruta: 'fases',
    titulo: 'Cómo se construyó',
    grupo: 'Empezar aquí',
    permiso: 'Las 12 fases',
    Componente: Fases,
  },
  {
    ruta: 'estimar',
    titulo: 'Estimar un paciente',
    grupo: 'Trabajar',
    permiso: 'Estimar riesgo',
    Componente: Estimar,
  },
  {
    ruta: 'paso-a-paso',
    titulo: 'El cálculo paso a paso',
    grupo: 'Trabajar',
    permiso: 'Paso a paso',
    Componente: PasoAPaso,
  },
  {
    ruta: 'asistente',
    titulo: 'El asistente',
    grupo: 'Trabajar',
    permiso: 'Asistente',
    Componente: Asistente,
  },
]

export function pantallasDe(grupo: Grupo, permisos: string[]): Pantalla[] {
  return PANTALLAS.filter((p) => p.grupo === grupo && permisos.includes(p.permiso))
}
