import type { ReactNode } from 'react'

/**
 * El encabezado con el que abre cada pantalla.
 *
 * Aira lo define como patrón fijo: antetítulo en mayúscula pequeña con mucho
 * interletraje, titular en serif, y una frase que dice para qué sirve lo que
 * sigue. Tenerlo en un componente evita que cada pantalla lo escriba distinto.
 */
export function Encabezado({
  antetitulo,
  titulo,
  children,
}: {
  antetitulo: string
  titulo: string
  children?: ReactNode
}) {
  return (
    <div style={{ maxWidth: '60ch' }}>
      <p className="antetitulo">{antetitulo}</p>
      <h1 style={{ marginTop: 14, fontSize: 'clamp(32px, 4.4vw, 48px)', lineHeight: 1.12 }}>
        {titulo}
      </h1>
      {children && (
        <div
          style={{
            marginTop: 18,
            fontSize: 17,
            lineHeight: 1.6,
            color: 'var(--apagado)',
          }}
        >
          {children}
        </div>
      )}
    </div>
  )
}
