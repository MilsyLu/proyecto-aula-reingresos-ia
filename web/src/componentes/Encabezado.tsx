import type { ReactNode } from 'react'

/**
 * El encabezado con el que abre cada pantalla.
 *
 * Mantiene el patrón de Aira —antetítulo en mayúscula pequeña, titular en
 * serif, y una frase que dice para qué sirve lo que sigue— pero en tamaño de
 * aplicación, no de revista. Dentro de un panel con menú lateral, un titular
 * de 48 px se lee como un error de maqueta y además empuja hacia abajo lo
 * único que la persona vino a ver.
 *
 * `acciones` es para los botones que pertenecen a la pantalla entera, que van
 * a la derecha y a la misma altura del titular.
 */
export function Encabezado({
  antetitulo,
  titulo,
  acciones,
  children,
}: {
  antetitulo: string
  titulo: string
  acciones?: ReactNode
  children?: ReactNode
}) {
  return (
    <div className="encabezado">
      <div className="encabezado-texto">
        <p className="antetitulo">{antetitulo}</p>
        <h1>{titulo}</h1>
        {children && <div className="encabezado-bajada">{children}</div>}
      </div>
      {acciones && <div className="encabezado-acciones">{acciones}</div>}
    </div>
  )
}
