import { Seguimiento } from './Seguimiento'

/** Vista de agenda independiente, sin duplicar su lógica de datos. */
export function AgendaTrabajo() {
  return <Seguimiento vistaInicial="agenda" soloVista />
}
