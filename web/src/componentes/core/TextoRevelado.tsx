import { useEffect, useRef, useState } from 'react'

/**
 * Texto que entra palabra por palabra, con desenfoque que se despeja.
 *
 * Michel eligió `TextEffect` de motion-primitives con el preajuste
 * `fade-in-blur`. Esta es una pieza propia con el mismo efecto y la misma forma
 * de usarse, escrita aquí para no depender de código que no hemos leído.
 *
 * Se revela al entrar en pantalla, no al montarse: si se revelara al montar, el
 * texto del final de la página terminaría su animación antes de que nadie
 * llegue a verlo.
 *
 * Con `prefers-reduced-motion` el texto aparece de una vez. No se anima más
 * despacio: no se anima.
 */
export function TextoRevelado({
  children,
  etiqueta: Etiqueta = 'p',
  retardo = 0,
  porPalabra = 0.05,
  className,
  style,
}: {
  children: string
  etiqueta?: 'p' | 'h1' | 'h2' | 'h3' | 'span' | 'div'
  /** Segundos antes de empezar. */
  retardo?: number
  /** Segundos entre una palabra y la siguiente. */
  porPalabra?: number
  className?: string
  style?: React.CSSProperties
}) {
  const nodo = useRef<HTMLElement | null>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const elemento = nodo.current
    if (!elemento) return

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true)
      return
    }

    const observador = new IntersectionObserver(
      (entradas) => {
        if (entradas.some((e) => e.isIntersecting)) {
          setVisible(true)
          observador.disconnect()
        }
      },
      { threshold: 0.2, rootMargin: '0px 0px -8% 0px' },
    )
    observador.observe(elemento)
    return () => observador.disconnect()
  }, [])

  const palabras = children.split(' ')

  return (
    <Etiqueta
      ref={nodo as never}
      className={className}
      style={style}
      // El texto completo va en aria-label y las palabras quedan ocultas al
      // lector de pantalla: si no, lo leeria troceado palabra por palabra.
      aria-label={children}
    >
      <span aria-hidden="true">
        {palabras.map((palabra, i) => (
          <span
            key={`${palabra}-${i}`}
            style={{
              display: 'inline-block',
              whiteSpace: 'pre',
              opacity: visible ? 1 : 0,
              filter: visible ? 'blur(0)' : 'blur(9px)',
              transform: visible ? 'none' : 'translateY(14px)',
              transition: `opacity .6s ease ${retardo + i * porPalabra}s, filter .6s ease ${
                retardo + i * porPalabra
              }s, transform .6s cubic-bezier(.2,.75,.2,1) ${retardo + i * porPalabra}s`,
            }}
          >
            {palabra}
            {i < palabras.length - 1 ? ' ' : ''}
          </span>
        ))}
      </span>
    </Etiqueta>
  )
}
