/** Lo que devuelve `api/seguimiento.py`. */

export const ESTADOS = ['pendiente', 'agendado', 'contactado', 'cerrado'] as const
export type Estado = (typeof ESTADOS)[number]

export const NOMBRE_ESTADO: Record<Estado, string> = {
  pendiente: 'Pendiente',
  agendado: 'Agendado',
  contactado: 'Contactado',
  cerrado: 'Cerrado',
}

export interface PacienteSeguido {
  id: number
  creado: string
  registrado_por: string
  nombre: string
  documento: string
  telefono: string
  fecha_alta: string
  entradas: Record<string, string | number>
  probabilidad: number
  umbral: number
  alerta: boolean
  estado: Estado
  fecha_agendada: string
  fecha_contacto: string
  notas: string
  dias_desde_alta: number | null
  resumen: string
}

export interface ListaSeguimiento {
  pacientes: PacienteSeguido[]
  cuentas: Record<Estado, number>
  total: number
}

export interface DiaAgenda {
  fecha: string
  nombre: string
  numero: number
  pacientes: PacienteSeguido[]
}

export interface Agenda {
  lunes: string
  hoy: string
  dias: DiaAgenda[]
  sin_agendar: PacienteSeguido[]
}

/** 2026-11-25 → 25 de noviembre. Para leerlo, no para guardarlo. */
export function fechaCorta(iso: string): string {
  if (!iso) return ''
  const [a, m, d] = iso.split('-').map(Number)
  if (!a || !m || !d) return iso
  const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
  return `${d} de ${meses[m - 1]}`
}

/** El lunes de la semana siguiente o anterior, en ISO. */
export function moverSemana(lunesIso: string, semanas: number): string {
  const d = new Date(`${lunesIso}T12:00:00`)
  d.setDate(d.getDate() + semanas * 7)
  return d.toISOString().slice(0, 10)
}
