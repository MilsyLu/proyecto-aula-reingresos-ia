import { useCallback, useEffect, useState } from 'react'

/**
 * Tema claro u oscuro.
 *
 * El oscuro no es un tema aparte: es la inversion de superficie que el propio
 * Aira define como su movimiento compositivo principal. Por eso comparten los
 * mismos tokens, solo que al reves (ver estilos.css).
 *
 * La preferencia se guarda en el navegador de quien usa la aplicacion. Puede
 * fallar —navegacion privada, almacenamiento lleno, permisos—, asi que todo va
 * en try/catch y la pagina funciona igual si no se puede guardar.
 */

type Tema = 'claro' | 'oscuro'
const CLAVE = 'reingresaia-tema'

function leerGuardado(): Tema | null {
  try {
    const valor = localStorage.getItem(CLAVE)
    return valor === 'claro' || valor === 'oscuro' ? valor : null
  } catch {
    return null
  }
}

function temaInicial(): Tema {
  const guardado = leerGuardado()
  if (guardado) return guardado
  // Sin preferencia propia, se respeta la del sistema operativo.
  if (typeof window !== 'undefined' && window.matchMedia?.('(prefers-color-scheme: dark)').matches) {
    return 'oscuro'
  }
  return 'claro'
}

export function useTema() {
  const [tema, setTema] = useState<Tema>(temaInicial)

  useEffect(() => {
    document.documentElement.setAttribute('data-tema', tema)
    try {
      localStorage.setItem(CLAVE, tema)
    } catch {
      // si no se puede guardar, el tema igual queda aplicado en esta visita
    }
  }, [tema])

  const alternar = useCallback(() => {
    setTema((actual) => (actual === 'oscuro' ? 'claro' : 'oscuro'))
  }, [])

  return { tema, alternar, esOscuro: tema === 'oscuro' }
}
