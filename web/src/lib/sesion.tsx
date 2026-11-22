import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { api, type Sesion } from './api'

/**
 * Quien entro y que puede hacer.
 *
 * Los permisos los decide el servidor, nunca el navegador. Lo que el front
 * guarda aqui sirve para no mostrar enlaces que de todas formas rebotarian:
 * es comodidad visual, no seguridad. Cada endpoint vuelve a verificar el rol.
 */

interface Contexto {
  sesion: Sesion | null
  cargando: boolean
  entrar: (usuario: string, contrasena: string) => Promise<void>
  salir: () => Promise<void>
  puede: (permiso: string) => boolean
}

const ContextoSesion = createContext<Contexto | null>(null)

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(null)
  const [cargando, setCargando] = useState(true)

  // Al recargar la pagina se le pregunta al servidor si la cookie sigue viva.
  // Responde 200 con sesion en null cuando no hay nadie dentro: no entrar
  // todavia no es un error.
  useEffect(() => {
    let vigente = true
    api
      .obtener<{ sesion: Sesion | null }>('/sesion')
      .then(({ sesion: datos }) => {
        if (vigente) setSesion(datos)
      })
      .catch(() => {
        if (vigente) setSesion(null)
      })
      .finally(() => {
        if (vigente) setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [])

  const entrar = useCallback(async (usuario: string, contrasena: string) => {
    const datos = await api.enviar<Sesion>('/entrar', { usuario, contrasena })
    setSesion(datos)
  }, [])

  const salir = useCallback(async () => {
    try {
      await api.enviar('/salir', {})
    } finally {
      // Aunque el servidor falle, aqui se cierra: nadie se queda dentro
      // porque la peticion de salida no respondio.
      setSesion(null)
    }
  }, [])

  const puede = useCallback(
    (permiso: string) => Boolean(sesion?.permisos.includes(permiso)),
    [sesion],
  )

  const valor = useMemo(
    () => ({ sesion, cargando, entrar, salir, puede }),
    [sesion, cargando, entrar, salir, puede],
  )

  return <ContextoSesion.Provider value={valor}>{children}</ContextoSesion.Provider>
}

export function useSesion() {
  const contexto = useContext(ContextoSesion)
  if (!contexto) throw new Error('useSesion se usó fuera del ProveedorSesion')
  return contexto
}
