import { useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'

/**
 * Tarjeta que se inclina siguiendo el cursor.
 *
 * Michel eligió `Tilt` de motion-primitives, que es MIT. Esta es una pieza
 * propia con la misma idea y la misma forma de usarse, escrita aquí para no
 * depender de código que no hemos leído.
 *
 * La inclinación es pequeña a propósito. En una aplicación clínica, una
 * tarjeta que se mueve mucho distrae de la cifra que lleva dentro, que es lo
 * único que importa. Ocho grados se sienten y no molestan.
 *
 * No se inclina si quien usa la aplicación pidió menos movimiento, ni en
 * pantallas táctiles, donde no hay cursor que seguir y el efecto solo
 * conseguiría que la tarjeta tiemble al tocarla.
 */
export function TarjetaInclinada({
  children,
  grados = 8,
  invertido = false,
  className,
  style,
}: {
  children: ReactNode
  /** Cuánto se inclina en los bordes. */
  grados?: number
  /** Si se inclina hacia el cursor en vez de alejarse de él. */
  invertido?: boolean
  className?: string
  style?: CSSProperties
}) {
  const nodo = useRef<HTMLDivElement | null>(null)
  const [giro, setGiro] = useState({ x: 0, y: 0 })

  function seguir(e: React.PointerEvent) {
    if (e.pointerType !== 'mouse') return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const caja = nodo.current?.getBoundingClientRect()
    if (!caja) return
    const dx = (e.clientX - caja.left) / caja.width - 0.5
    const dy = (e.clientY - caja.top) / caja.height - 0.5
    const signo = invertido ? -1 : 1
    setGiro({ x: -dy * grados * 2 * signo, y: dx * grados * 2 * signo })
  }

  return (
    <div style={{ perspective: 900 }}>
      <div
        ref={nodo}
        className={className}
        onPointerMove={seguir}
        onPointerLeave={() => setGiro({ x: 0, y: 0 })}
        style={{
          ...style,
          transform: `rotateX(${giro.x.toFixed(2)}deg) rotateY(${giro.y.toFixed(2)}deg)`,
          transformStyle: 'preserve-3d',
          transition: 'transform .35s cubic-bezier(.2,.75,.2,1)',
          willChange: 'transform',
        }}
      >
        {children}
      </div>
    </div>
  )
}
