import { Moon, Sun } from 'lucide-react'
import { useTema } from '../lib/tema'

/**
 * El interruptor de tema.
 *
 * Los iconos son de linea y van en el gris apagado del sistema, como manda
 * Aira. Y la etiqueta dice el tema que esta puesto, no el que se activaria al
 * pulsar: eso ultimo confunde a casi todo el mundo.
 */
export function InterruptorTema({ sobreFoto = false }: { sobreFoto?: boolean }) {
  const { esOscuro, alternar } = useTema()
  const Icono = esOscuro ? Sun : Moon

  return (
    <button
      type="button"
      onClick={alternar}
      aria-label={esOscuro ? 'Cambiar al tema claro' : 'Cambiar al tema oscuro'}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 7,
        borderRadius: 999,
        cursor: 'pointer',
        fontFamily: 'var(--font-sans)',
        fontSize: 13,
        fontWeight: 500,
        padding: '8px 15px',
        background: 'transparent',
        color: sobreFoto ? 'var(--color-hueso)' : 'var(--tinta)',
        border: `1px solid ${sobreFoto ? 'rgb(250 250 251 / 0.4)' : 'var(--borde-suave)'}`,
        transition: 'border-color .3s ease',
      }}
    >
      <Icono size={14} strokeWidth={1.4} aria-hidden="true" />
      <span>{esOscuro ? 'Oscuro' : 'Claro'}</span>
    </button>
  )
}
