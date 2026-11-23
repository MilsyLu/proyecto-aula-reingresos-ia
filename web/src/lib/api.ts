/**
 * Cliente del backend.
 *
 * Una sola puerta de entrada a la API, para que ninguna pantalla improvise su
 * propio manejo de errores. Si el servidor responde mal, aqui se traduce a un
 * mensaje que una persona pueda leer, en vez de dejar escapar un 500 crudo.
 */

export class ErrorApi extends Error {
  // Declarado aparte y no como propiedad del constructor: el proyecto compila
  // con erasableSyntaxOnly, que prohibe la forma corta de TypeScript porque no
  // se puede borrar dejando JavaScript valido.
  readonly estado: number

  constructor(mensaje: string, estado: number) {
    super(mensaje)
    this.name = 'ErrorApi'
    this.estado = estado
  }
}

/** Mensajes en el tono de la aplicacion: de usted, sin culpar a quien lee. */
function mensajeDe(estado: number, detalle?: string): string {
  if (detalle) return detalle
  if (estado === 401) return 'La sesión expiró. Vuelva a entrar.'
  if (estado === 403) return 'Su perfil no tiene acceso a esta sección.'
  if (estado === 404) return 'No encontramos eso.'
  if (estado === 413) return 'El archivo pesa más de lo que admite el servidor.'
  if (estado === 429) return 'Ya hay un proceso en curso. Espere a que termine.'
  if (estado >= 500) return 'El servidor falló. Vuelva a intentarlo en un momento.'
  return 'No se pudo completar la operación.'
}

async function pedir<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  let respuesta: Response
  try {
    respuesta = await fetch(`/api${ruta}`, {
      credentials: 'include',
      ...opciones,
      headers: {
        ...(opciones.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...opciones.headers,
      },
    })
  } catch {
    // Ni siquiera llego a salir: no hay red, o el servidor esta apagado.
    throw new ErrorApi('No hay conexión con el servidor.', 0)
  }

  if (!respuesta.ok) {
    let detalle: string | undefined
    try {
      const cuerpo = await respuesta.json()
      detalle = typeof cuerpo?.detail === 'string' ? cuerpo.detail : undefined
    } catch {
      // el cuerpo no era JSON; nos quedamos con el mensaje por codigo
    }
    throw new ErrorApi(mensajeDe(respuesta.status, detalle), respuesta.status)
  }

  if (respuesta.status === 204) return undefined as T
  return (await respuesta.json()) as T
}

export const api = {
  obtener: <T>(ruta: string) => pedir<T>(ruta),
  enviar: <T>(ruta: string, datos: unknown) =>
    pedir<T>(ruta, { method: 'POST', body: JSON.stringify(datos) }),
  subir: <T>(ruta: string, formulario: FormData) =>
    pedir<T>(ruta, { method: 'POST', body: formulario }),
  parchar: <T>(ruta: string, datos: unknown) =>
    pedir<T>(ruta, { method: 'PATCH', body: JSON.stringify(datos) }),
  borrar: <T>(ruta: string) => pedir<T>(ruta, { method: 'DELETE' }),
}

/**
 * Baja un archivo que genera la API.
 *
 * No se usa un <a download> apuntando a la ruta: eso la abre sin la cookie en
 * algunos navegadores y ademas no deja ver el error si el servidor responde
 * mal. Asi se pide con fetch, se comprueba, y solo entonces se descarga.
 */
export async function descargar(ruta: string): Promise<void> {
  const respuesta = await fetch(`/api${ruta}`, { credentials: 'include' })
  if (!respuesta.ok) {
    throw new ErrorApi(mensajeDe(respuesta.status), respuesta.status)
  }

  const cabecera = respuesta.headers.get('Content-Disposition') ?? ''
  const nombre = /filename="([^"]+)"/.exec(cabecera)?.[1] ?? 'reporte'

  const bytes = await respuesta.blob()
  const url = URL.createObjectURL(bytes)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  enlace.click()
  URL.revokeObjectURL(url)
}

// --- tipos que comparten el front y la API ---------------------------------

export type Rol = 'clinico' | 'coordinador'

export interface Sesion {
  usuario: string
  nombre: string
  rol: Rol
  permisos: string[]
}
