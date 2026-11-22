import type { ComponentType } from 'react'
import { Archivo } from './paginas/Archivo'
import { Asistente } from './paginas/Asistente'
import { Cohorte } from './paginas/Cohorte'
import { Desempeno } from './paginas/Desempeno'
import { Descriptiva } from './paginas/Descriptiva'
import { Entrenar } from './paginas/Entrenar'
import { Equidad } from './paginas/Equidad'
import { Ficha } from './paginas/Ficha'
import { Importancia } from './paginas/Importancia'
import { Estimar } from './paginas/Estimar'
import { Fases } from './paginas/Fases'
import { Guia } from './paginas/Guia'
import { MapaCalor } from './paginas/MapaCalor'
import { Modelos } from './paginas/Modelos'
import { PasoAPaso } from './paginas/PasoAPaso'
import { Techo } from './paginas/Techo'
import { Umbral } from './paginas/Umbral'

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
  {
    ruta: 'cohorte',
    titulo: 'De dónde salen los datos',
    grupo: 'Conocer los datos',
    permiso: 'Conocer los datos',
    Componente: Cohorte,
  },
  {
    ruta: 'estadistica',
    titulo: 'Estadística descriptiva',
    grupo: 'Conocer los datos',
    permiso: 'Estadística descriptiva',
    Componente: Descriptiva,
  },
  {
    ruta: 'mapa-de-calor',
    titulo: 'Mapa de calor',
    grupo: 'Conocer los datos',
    permiso: 'Mapa de calor',
    Componente: MapaCalor,
  },
  {
    ruta: 'modelos',
    titulo: 'Qué modelos probamos',
    grupo: 'Conocer el modelo',
    permiso: 'Comparar modelos',
    Componente: Modelos,
  },
  {
    ruta: 'desempeno',
    titulo: 'Desempeño y métricas',
    grupo: 'Conocer el modelo',
    permiso: 'Desempeño',
    Componente: Desempeno,
  },
  {
    ruta: 'importancia',
    titulo: 'Qué pesa en el modelo',
    grupo: 'Conocer el modelo',
    permiso: 'Importancia',
    Componente: Importancia,
  },
  {
    ruta: 'equidad',
    titulo: 'Equidad y límites',
    grupo: 'Conocer el modelo',
    permiso: 'Equidad',
    Componente: Equidad,
  },
  {
    ruta: 'techo',
    titulo: 'El techo de los datos',
    grupo: 'Conocer el modelo',
    permiso: 'Techo de los datos',
    Componente: Techo,
  },
  {
    ruta: 'ficha',
    titulo: 'Ficha del modelo',
    grupo: 'Conocer el modelo',
    permiso: 'Ficha del modelo',
    Componente: Ficha,
  },
  {
    ruta: 'archivo',
    titulo: 'Archivo y lista de llamadas',
    grupo: 'Trabajar',
    permiso: 'Cargar archivo',
    Componente: Archivo,
  },
  {
    ruta: 'umbral',
    titulo: 'Fijar el umbral',
    grupo: 'Trabajar',
    permiso: 'Fijar umbral',
    Componente: Umbral,
  },
  {
    ruta: 'entrenar',
    titulo: 'Entrene usted el modelo',
    grupo: 'Aprender haciendo',
    permiso: 'Recorrido grabado',
    Componente: Entrenar,
  },
]

export function pantallasDe(grupo: Grupo, permisos: string[]): Pantalla[] {
  return PANTALLAS.filter((p) => p.grupo === grupo && permisos.includes(p.permiso))
}
