import type { ReactNode } from 'react'
import { useId } from 'react'

/**
 * Franja que se desplaza sin fin y baja la velocidad al pasar el cursor.
 *
 * Michel eligió `InfiniteSlider` de motion-primitives, que es MIT. Esta es una
 * pieza propia con la misma idea y la misma forma de usarse, escrita aquí para
 * no depender de código que no hemos leído: si algún día se quiere la original,
 * el cambio es sustituir este archivo.
 *
 * El truco es viejo y funciona: se duplica el contenido y se desplaza la mitad
 * exacta del ancho. Como la segunda copia empieza justo donde termina la
 * primera, el salto al reiniciar no se ve.
 */
export function DeslizadorInfinito({
  children,
  segundos = 28,
  segundosAlPasar = 70,
  separacion = 56,
}: {
  children: ReactNode
  /** Cuánto tarda en dar una vuelta completa. Más segundos, más lento. */
  segundos?: number
  /** Cuánto tarda cuando el cursor está encima. Más alto para poder leer. */
  segundosAlPasar?: number
  separacion?: number
}) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, '')
  const clase = `franja-${id}`

  return (
    <div className={clase} aria-label="Tecnologías usadas en el proyecto">
      <div className="pista">
        <div className="grupo">{children}</div>
        {/* La copia es decorativa: un lector de pantalla no debe leerla dos veces. */}
        <div className="grupo" aria-hidden="true">
          {children}
        </div>
      </div>

      <style>{`
        .${clase} {
          overflow: hidden;
          width: 100%;
          /* Se desvanece en los bordes para que no parezca que el contenido
             se corta de golpe contra el margen. */
          mask-image: linear-gradient(90deg, transparent, #000 9%, #000 91%, transparent);
        }
        .${clase} .pista {
          display: flex;
          width: max-content;
          animation: correr-${id} ${segundos}s linear infinite;
        }
        .${clase}:hover .pista { animation-duration: ${segundosAlPasar}s; }
        .${clase} .grupo {
          display: flex;
          align-items: center;
          gap: ${separacion}px;
          padding-right: ${separacion}px;
          flex: none;
        }
        @keyframes correr-${id} {
          from { transform: translate3d(0, 0, 0); }
          to { transform: translate3d(-50%, 0, 0); }
        }
        @media (prefers-reduced-motion: reduce) {
          .${clase} .pista { animation: none; }
          .${clase} { mask-image: none; overflow-x: auto; }
        }
      `}</style>
    </div>
  )
}
