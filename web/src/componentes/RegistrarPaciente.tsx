import { Check, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { ErrorApi, api } from '../lib/api'
import { porcentaje } from '../lib/formato'
import type { PacienteSeguido } from '../lib/tiposSeguimiento'

/**
 * Registrar para seguimiento al paciente que está en pantalla.
 *
 * Pide solo lo que hace falta para poder llamar a alguien: cómo se llama, un
 * teléfono y cuándo le dieron el alta. Lo clínico ya está escrito en el
 * formulario de al lado y viaja junto con el registro.
 *
 * El riesgo se vuelve a calcular en el servidor al guardar. Aquí se muestra el
 * de la pantalla solo para que la persona vea a quién está registrando.
 */
export function RegistrarPaciente({
  entradas,
  probabilidad,
  alerta,
  onCerrar,
  onGuardado,
}: {
  entradas: Record<string, string | number>
  probabilidad: number
  alerta: boolean
  onCerrar: () => void
  onGuardado: (p: PacienteSeguido) => void
}) {
  const [nombre, setNombre] = useState('')
  const [documento, setDocumento] = useState('')
  const [telefono, setTelefono] = useState('')
  const [fechaAlta, setFechaAlta] = useState(() => new Date().toISOString().slice(0, 10))
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const primero = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    primero.current?.focus()
    function tecla(e: KeyboardEvent) {
      if (e.key === 'Escape') onCerrar()
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [onCerrar])

  async function guardar(e: React.FormEvent) {
    e.preventDefault()
    if (!nombre.trim()) {
      setError('Escriba al menos el nombre del paciente.')
      return
    }
    setGuardando(true)
    setError(null)
    try {
      const creado = await api.enviar<PacienteSeguido>('/seguimiento', {
        nombre, documento, telefono, fecha_alta: fechaAlta, entradas,
      })
      onGuardado(creado)
    } catch (err) {
      setError(err instanceof ErrorApi ? err.message : 'No se pudo registrar al paciente.')
      setGuardando(false)
    }
  }

  return (
    <div
      className="buscador-velo"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCerrar()
      }}
    >
      <form
        className="registrar-caja"
        onSubmit={guardar}
        role="dialog"
        aria-modal="true"
        aria-label="Registrar paciente para seguimiento"
      >
        <div className="registrar-cabeza">
          <div>
            <p className="antetitulo">Registrar para seguimiento</p>
            <h3 className="tarjeta-titulo" style={{ marginTop: 7 }}>
              Riesgo estimado: {porcentaje(probabilidad)}
            </h3>
            <p className="tarjeta-sub">
              {alerta
                ? 'Supera el umbral: entra en la lista de llamadas.'
                : 'No alcanza el umbral, pero igual puede hacerle seguimiento.'}
            </p>
          </div>
          <button type="button" className="quitar" onClick={onCerrar} aria-label="Cerrar">
            <X size={17} strokeWidth={1.6} />
          </button>
        </div>

        <div className="registrar-campos">
          <label className="campo-registro" style={{ gridColumn: '1 / -1' }}>
            <span>Nombre del paciente</span>
            <input
              ref={primero}
              value={nombre}
              maxLength={120}
              onChange={(e) => setNombre(e.target.value)}
              placeholder="Nombre y apellido"
            />
          </label>
          <label className="campo-registro">
            <span>Documento</span>
            <input
              value={documento}
              maxLength={40}
              onChange={(e) => setDocumento(e.target.value)}
              placeholder="Opcional"
            />
          </label>
          <label className="campo-registro">
            <span>Teléfono</span>
            <input
              value={telefono}
              maxLength={40}
              onChange={(e) => setTelefono(e.target.value)}
              placeholder="Para la llamada"
            />
          </label>
          <label className="campo-registro" style={{ gridColumn: '1 / -1' }}>
            <span>Fecha del alta</span>
            <input
              type="date"
              value={fechaAlta}
              onChange={(e) => setFechaAlta(e.target.value)}
            />
            <small>Desde esta fecha corren los treinta días de la ventana.</small>
          </label>
        </div>

        {error && <p className="aviso-error" style={{ margin: '0 20px 14px' }}>{error}</p>}

        <div className="registrar-pie">
          <p>
            Se guardan también los quince datos de la hospitalización que están en el
            formulario, y el riesgo se recalcula en el servidor.
          </p>
          <div className="registrar-botones">
            <button type="button" className="pastilla pastilla-contorno pastilla-sm" onClick={onCerrar}>
              Cancelar
            </button>
            <button type="submit" className="pastilla pastilla-rellena pastilla-sm" disabled={guardando}>
              <Check size={14} strokeWidth={2} aria-hidden="true" />
              {guardando ? 'Guardando' : 'Registrar'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
