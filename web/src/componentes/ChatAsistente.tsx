import { Sparkles } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { ErrorApi, api } from '../lib/api'
import type { Estimacion } from '../lib/tiposModelo'

/**
 * El chat del asistente, sin la pantalla alrededor.
 *
 * Vive en dos sitios: la pantalla suelta del asistente, para conversaciones
 * largas, y el panel pegado a la derecha de «Estimar un paciente», que es
 * donde de verdad hace falta porque la pregunta sale mirando el resultado.
 *
 * Siempre responde sobre un paciente concreto: el que reciba por `estimacion`.
 * Un asistente que hable del modelo en abstracto no le sirve a nadie en la sala.
 *
 * Lo que viaja a Gemini es el resultado y las limitaciones medidas, nunca
 * datos que identifiquen a una persona.
 */

interface Turno {
  quien: 'usted' | 'asistente'
  texto: string
}

export function ChatAsistente({
  estimacion,
  alto = 300,
  saludo = 'Pregúnteme por qué este paciente dio ese riesgo, qué dato lo empuja, o qué tan de fiar es la cifra.',
}: {
  estimacion: Estimacion | null
  /** Alto del hilo en píxeles. El panel lateral y la pantalla suelta difieren. */
  alto?: number
  saludo?: string
}) {
  const [disponible, setDisponible] = useState<boolean | null>(null)
  const [sugerencias, setSugerencias] = useState<string[]>([])
  const [turnos, setTurnos] = useState<Turno[]>([])
  const [pregunta, setPregunta] = useState('')
  const [pensando, setPensando] = useState(false)
  const [fallo, setFallo] = useState<string | null>(null)
  const fondo = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    api
      .obtener<{ disponible: boolean; sugerencias: string[] }>('/asistente')
      .then((d) => {
        setDisponible(d.disponible)
        setSugerencias(d.sugerencias)
      })
      .catch(() => setDisponible(false))
  }, [])

  useEffect(() => {
    fondo.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [turnos, pensando])

  async function enviar(texto: string) {
    const limpio = texto.trim()
    if (!limpio || pensando || !estimacion) return

    setTurnos((t) => [...t, { quien: 'usted', texto: limpio }])
    setPregunta('')
    setPensando(true)
    setFallo(null)

    try {
      const r = await api.enviar<{ respuesta: string }>('/asistente', {
        pregunta: limpio,
        riesgo: estimacion.probabilidad,
        umbral: estimacion.umbral,
        efectos: estimacion.efectos.map((e) => ({
          nombre: e.nombre,
          valor: e.valor,
          tipico: e.tipico,
          efecto: e.efecto,
          riesgo_sin_el: e.sin_el,
        })),
      })
      setTurnos((t) => [...t, { quien: 'asistente', texto: r.respuesta }])
    } catch (e) {
      // El servidor pide esperar entre preguntas y responde 429. Eso no es un
      // fallo: es una frase que hay que leer, no un error rojo.
      setFallo(e instanceof ErrorApi ? e.message : 'No se pudo preguntar.')
    } finally {
      setPensando(false)
    }
  }

  const listo = disponible === true && estimacion !== null

  return (
    <div className="chat">
      <div className="chat-cabeza">
        <div className="chat-titulo">
          <span className="sello-bot">
            <Sparkles size={16} strokeWidth={1.8} aria-hidden="true" />
          </span>
          <div>
            <h3 className="tarjeta-titulo">Asistente</h3>
            <p className="tarjeta-sub">
              {estimacion ? 'Sobre el paciente en pantalla' : 'Esperando un paciente'}
            </p>
          </div>
        </div>
        {disponible !== false && <span className="en-linea">Disponible</span>}
      </div>

      <div className="chat-hilo" style={{ maxHeight: alto, minHeight: alto }}>
        {disponible === false ? (
          <div className="burbuja de-bot">
            El asistente no está configurado en este servidor. Todo lo demás funciona igual: el
            riesgo, el paso a paso y las métricas no dependen de él.
          </div>
        ) : (
          <>
            <div className="burbuja de-bot">{saludo}</div>
            {turnos.map((t, i) => (
              <div
                key={i}
                className={t.quien === 'usted' ? 'burbuja de-usted' : 'burbuja de-bot'}
              >
                {t.texto}
              </div>
            ))}
            {pensando && <div className="burbuja de-bot">Pensando…</div>}
            {fallo && <div className="burbuja de-bot">{fallo}</div>}
          </>
        )}
        <div ref={fondo} />
      </div>

      {listo && sugerencias.length > 0 && turnos.length === 0 && (
        <div className="sugerencias">
          {sugerencias.slice(0, 3).map((s) => (
            <button
              key={s}
              type="button"
              className="sugerencia"
              disabled={pensando}
              onClick={() => enviar(s)}
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault()
          enviar(pregunta)
        }}
      >
        <input
          value={pregunta}
          maxLength={600}
          disabled={!listo || pensando}
          placeholder={listo ? 'Escriba su pregunta' : 'No disponible'}
          onChange={(e) => setPregunta(e.target.value)}
          aria-label="Pregunta al asistente"
        />
        <button
          type="submit"
          className="enviar"
          disabled={!listo || pensando || !pregunta.trim()}
          aria-label="Enviar la pregunta"
        >
          ↑
        </button>
      </form>

      <p className="chat-pie">Responde sobre este caso. Cuando no sabe algo, lo dice.</p>
    </div>
  )
}
