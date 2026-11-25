import type { ComponentType } from 'react'
import {
  ArrowUpToLine,
  BookOpen,
  CalendarDays,
  Calculator,
  ChartColumn,
  ChartLine,
  Database,
  FileSpreadsheet,
  FileText,
  GitBranch,
  GitCompare,
  GraduationCap,
  Grid3x3,
  type LucideIcon,
  LayoutDashboard,
  ListOrdered,
  MessageCircle,
  Scale,
  SlidersHorizontal,
  Upload,
  Users,
  Weight,
} from 'lucide-react'
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
import { Pacientes } from './paginas/Pacientes'
import { Panel } from './paginas/Panel'
import { Modelos } from './paginas/Modelos'
import { PasoAPaso } from './paginas/PasoAPaso'
import { Reportes } from './paginas/Reportes'
import { Seguimiento } from './paginas/Seguimiento'
import { Techo } from './paginas/Techo'
import { Umbral } from './paginas/Umbral'
import { AgendaTrabajo } from './paginas/AgendaTrabajo'
import { LaboratorioIA } from './paginas/LaboratorioIA'
import { Administracion } from './paginas/Administracion'

/**
 * El registro de pantallas.
 *
 * Un solo sitio decide la ruta, el titulo del menu, su icono, el grupo al que
 * pertenece y el permiso que exige. La navegacion se dibuja sola a partir de
 * aqui, asi que agregar una pantalla es agregar una linea y nada mas: no hay
 * que tocar el menu, ni el enrutador, ni el control de acceso del front.
 *
 * El permiso debe coincidir exactamente con los de `api/autenticacion.py`.
 */

export type Grupo = 'Atención diaria' | 'Administración'

export const GRUPOS: Grupo[] = ['Atención diaria', 'Administración']

export interface Pantalla {
  /** Ruta relativa dentro de /app */
  ruta: string
  /** Como aparece en el menu */
  titulo: string
  grupo: Grupo
  /** Permiso que exige, verificado de verdad en la API */
  permiso: string
  /** El icono del menu. Tambien lo usa el buscador de Ctrl+K. */
  Icono: LucideIcon
  /**
   * Las pantallas donde se trabaja con el modelo van en teal en vez de morado.
   *
   * Sale del diseno que paso Michel, que usa esa misma division: el morado es
   * del programa y el teal es del modelo. Separa de un vistazo operar de
   * entender, sin que haga falta leer el titulo.
   */
  teal?: true
  /** Rutas técnicas accesibles por URL solo para administradores. */
  ocultarEnMenu?: true
  Componente: ComponentType
}

export const PANTALLAS: Pantalla[] = [
  {
    ruta: 'panel',
    titulo: 'Inicio',
    grupo: 'Atención diaria',
    permiso: 'Guía',
    Icono: LayoutDashboard,
    Componente: Panel,
  },
  {
    ruta: 'seguimiento',
    titulo: 'Pacientes',
    grupo: 'Atención diaria',
    permiso: 'Seguimiento',
    Icono: CalendarDays,
    Componente: Seguimiento,
  },
  {
    ruta: 'estimar',
    titulo: 'Estimar riesgo',
    grupo: 'Atención diaria',
    permiso: 'Estimar riesgo',
    Icono: Calculator,
    teal: true,
    Componente: Estimar,
  },
  {
    ruta: 'agenda',
    titulo: 'Agenda',
    grupo: 'Atención diaria',
    permiso: 'Seguimiento',
    Icono: CalendarDays,
    Componente: AgendaTrabajo,
  },
  {
    ruta: 'administracion',
    titulo: 'Gestión administrativa',
    grupo: 'Administración',
    permiso: 'Cargar archivo',
    Icono: SlidersHorizontal,
    Componente: Administracion,
  },
  {
    ruta: 'laboratorio-ia',
    titulo: 'Laboratorio de IA',
    grupo: 'Administración',
    permiso: 'Comparar modelos',
    Icono: GraduationCap,
    Componente: LaboratorioIA,
  },
  {
    ruta: 'guia',
    titulo: 'Qué es esto',
    grupo: 'Administración',
    permiso: 'Guía',
    Icono: BookOpen,
    teal: true,
    ocultarEnMenu: true,
    Componente: Guia,
  },
  {
    ruta: 'fases',
    titulo: 'Cómo se construyó',
    grupo: 'Administración',
    permiso: 'Las 12 fases',
    Icono: GitBranch,
    ocultarEnMenu: true,
    Componente: Fases,
  },
  {
    ruta: 'paso-a-paso',
    titulo: 'El cálculo paso a paso',
    grupo: 'Administración',
    permiso: 'Paso a paso',
    Icono: ListOrdered,
    teal: true,
    ocultarEnMenu: true,
    Componente: PasoAPaso,
  },
  {
    ruta: 'asistente',
    titulo: 'El asistente',
    grupo: 'Administración',
    permiso: 'Asistente',
    Icono: MessageCircle,
    teal: true,
    ocultarEnMenu: true,
    Componente: Asistente,
  },
  {
    ruta: 'pacientes',
    titulo: 'Lista priorizada',
    grupo: 'Administración',
    permiso: 'Lista priorizada',
    Icono: Users,
    ocultarEnMenu: true,
    Componente: Pacientes,
  },
  {
    ruta: 'reportes',
    titulo: 'Reportes',
    grupo: 'Administración',
    permiso: 'Reportes',
    Icono: FileSpreadsheet,
    ocultarEnMenu: true,
    Componente: Reportes,
  },
  {
    ruta: 'archivo',
    titulo: 'Archivo y lista de llamadas',
    grupo: 'Administración',
    permiso: 'Cargar archivo',
    Icono: Upload,
    ocultarEnMenu: true,
    Componente: Archivo,
  },
  {
    ruta: 'umbral',
    titulo: 'Fijar el umbral',
    grupo: 'Administración',
    permiso: 'Fijar umbral',
    Icono: SlidersHorizontal,
    ocultarEnMenu: true,
    Componente: Umbral,
  },
  {
    ruta: 'cohorte',
    titulo: 'De dónde salen los datos',
    grupo: 'Administración',
    permiso: 'Conocer los datos',
    Icono: Database,
    ocultarEnMenu: true,
    Componente: Cohorte,
  },
  {
    ruta: 'estadistica',
    titulo: 'Estadística descriptiva',
    grupo: 'Administración',
    permiso: 'Estadística descriptiva',
    Icono: ChartColumn,
    ocultarEnMenu: true,
    Componente: Descriptiva,
  },
  {
    ruta: 'mapa-de-calor',
    titulo: 'Mapa de calor',
    grupo: 'Administración',
    permiso: 'Mapa de calor',
    Icono: Grid3x3,
    ocultarEnMenu: true,
    Componente: MapaCalor,
  },
  {
    ruta: 'modelos',
    titulo: 'Qué modelos probamos',
    grupo: 'Administración',
    permiso: 'Comparar modelos',
    Icono: GitCompare,
    ocultarEnMenu: true,
    Componente: Modelos,
  },
  {
    ruta: 'desempeno',
    titulo: 'Desempeño y métricas',
    grupo: 'Administración',
    permiso: 'Desempeño',
    Icono: ChartLine,
    ocultarEnMenu: true,
    Componente: Desempeno,
  },
  {
    ruta: 'importancia',
    titulo: 'Qué pesa en el modelo',
    grupo: 'Administración',
    permiso: 'Importancia',
    Icono: Weight,
    ocultarEnMenu: true,
    Componente: Importancia,
  },
  {
    ruta: 'equidad',
    titulo: 'Equidad y límites',
    grupo: 'Administración',
    permiso: 'Equidad',
    Icono: Scale,
    ocultarEnMenu: true,
    Componente: Equidad,
  },
  {
    ruta: 'techo',
    titulo: 'El techo de los datos',
    grupo: 'Administración',
    permiso: 'Techo de los datos',
    Icono: ArrowUpToLine,
    ocultarEnMenu: true,
    Componente: Techo,
  },
  {
    ruta: 'ficha',
    titulo: 'Ficha del modelo',
    grupo: 'Administración',
    permiso: 'Ficha del modelo',
    Icono: FileText,
    ocultarEnMenu: true,
    Componente: Ficha,
  },
  {
    ruta: 'entrenar',
    titulo: 'Entrene usted el modelo',
    grupo: 'Administración',
    permiso: 'Recorrido grabado',
    Icono: GraduationCap,
    teal: true,
    ocultarEnMenu: true,
    Componente: Entrenar,
  },
]

/**
 * La pantalla con la que abre la aplicación.
 *
 * El panel, que es lo primero del menú y resume lo que hay que saber antes de
 * hacer nada: a quién falta llamar, cuántos hay en seguimiento y el umbral
 * vigente. Estimar un paciente queda a un clic, de primera en «Trabajar» y
 * también entre los accesos rápidos del propio panel.
 */
export const INICIO = 'panel'

export function pantallasDe(grupo: Grupo, permisos: string[]): Pantalla[] {
  return PANTALLAS.filter((p) => p.grupo === grupo && !p.ocultarEnMenu && permisos.includes(p.permiso))
}

/** Todas las que el rol puede abrir, en el orden del menú. Lo usa el buscador. */
export function pantallasVisibles(permisos: string[]): Pantalla[] {
  return PANTALLAS.filter((p) => permisos.includes(p.permiso))
}
