import { ArrowUp } from 'lucide-react'
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

/**
 * El modelo responde con **negrita** de Markdown y salían los asteriscos en
 * crudo. No se trae un renderizador entero de Markdown por esto: se parte el
 * texto por los pares de asteriscos y punto.
 *
 * Se parte, no se inyecta HTML: lo que viene del modelo nunca se interpreta
 * como marcado, solo se pinta en negrita el trozo que iba entre asteriscos.
 */
function conNegrita(texto: string) {
  return texto.split(/\*\*(.+?)\*\*/g).map((trozo, i) =>
    i % 2 === 1 ? <strong key={i}>{trozo}</strong> : trozo,
  )
}

export function ChatAsistente({
  estimacion,
  alto,
  saludo = 'Pregúnteme por qué este paciente dio ese riesgo, qué dato lo empuja, o qué tan de fiar es la cifra.',
  compacto = false,
}: {
  estimacion: Estimacion | null
  /**
   * Alto del hilo en píxeles. Sin él, el hilo ocupa el espacio que quede en la
   * tarjeta: crece con la conversación y no reserva hueco vacío por si acaso.
   * Reservarlo obligaba a bajar la página para ver lo de abajo, y eso es justo
   * lo que no queremos.
   */
  alto?: number
  saludo?: string
  /** El panel lateral de «Estimar» es estrecho: sin etiquetas ni campo grande. */
  compacto?: boolean
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
    <div className={`chat${compacto ? ' compacto' : ''}`}>
      <div className="chat-cabeza">
        <div className="chat-titulo">
          <span className="sello-bot">IA</span>
          <div>
            <h3 className="tarjeta-titulo">Conversación</h3>
            <p className="tarjeta-sub">Asistente educativo de ReingresaIA</p>
          </div>
        </div>
        {disponible !== false && <span className="en-linea">Disponible</span>}
      </div>

      <div
        className="chat-hilo"
        style={alto ? { maxHeight: alto, minHeight: alto } : undefined}
      >
        {disponible === false ? (
          <div className="turno de-bot">
            <div className="burbuja">
              El asistente no está configurado en este servidor. Todo lo demás funciona igual:
              el riesgo, el paso a paso y las métricas no dependen de él.
            </div>
          </div>
        ) : (
          <>
            {turnos.length === 0 && (
              <div className="turno de-bot">
                {!compacto && <p className="turno-quien">ReingresaIA</p>}
                <div className="burbuja">{saludo}</div>
              </div>
            )}

            {turnos.map((t, i) => (
              <div key={i} className={t.quien === 'usted' ? 'turno de-usted' : 'turno de-bot'}>
                {!compacto && (
                  <p className="turno-quien">{t.quien === 'usted' ? 'Tú' : 'ReingresaIA'}</p>
                )}
                <div className="burbuja">
                  {t.quien === 'asistente' ? conNegrita(t.texto) : t.texto}
                  {t.quien === 'asistente' && !compacto && (
                    <span className="burbuja-pie">
                      Respuesta orientativa · verifique siempre el contexto clínico
                    </span>
                  )}
                </div>
              </div>
            ))}

            {pensando && (
              <div className="turno de-bot">
                {!compacto && <p className="turno-quien">ReingresaIA</p>}
                <div className="burbuja">Pensando…</div>
              </div>
            )}

            {fallo && (
              <div className="turno de-bot">
                <div className="burbuja">{fallo}</div>
              </div>
            )}
          </>
        )}
        <div ref={fondo} />
      </div>

      {listo && sugerencias.length > 0 && turnos.length === 0 && (
        <div className="sugerencias">
          {!compacto && <p className="sugerencias-titulo">Para continuar</p>}
          <div className="sugerencias-fichas">
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
        </div>
      )}

      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault()
          enviar(pregunta)
        }}
      >
        <textarea
          value={pregunta}
          maxLength={600}
          rows={compacto ? 1 : 3}
          disabled={!listo || pensando}
          placeholder={listo ? 'Pregunta lo que quieras sobre este resultado…' : 'No disponible'}
          onChange={(e) => setPregunta(e.target.value)}
          onKeyDown={(e) => {
            // Enter envía; Mayús+Enter hace un salto de línea. Es lo que ya
            // espera cualquiera que haya escrito en un chat.
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              enviar(pregunta)
            }
          }}
          aria-label="Pregunta al asistente"
        />
        <button
          type="submit"
          className="enviar"
          disabled={!listo || pensando || !pregunta.trim()}
          aria-label="Enviar la pregunta"
        >
          <ArrowUp size={17} strokeWidth={2.4} aria-hidden="true" />
        </button>
      </form>

      <p className="chat-pie">
        El asistente explica el modelo: no ofrece diagnóstico ni recomendaciones de tratamiento.
      </p>
    </div>
  )
}
