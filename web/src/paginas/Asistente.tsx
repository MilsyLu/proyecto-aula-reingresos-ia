import { useEffect, useRef, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { porcentaje } from '../lib/formato'
import type { Estimacion } from '../lib/tiposModelo'
import { usarPaciente } from '../lib/usarPaciente'

/**
 * Pantalla 5: el asistente.
 *
 * Traduce el resultado a lenguaje corriente para quien no sabe de modelos.
 * Siempre responde sobre un paciente concreto, el que esté cargado: un
 * asistente que hable del modelo en abstracto no le sirve a nadie en la sala.
 *
 * Lo que viaja a Gemini es el resultado y las limitaciones medidas, nunca
 * datos que identifiquen a una persona.
 */

interface Turno {
  quien: 'usted' | 'asistente'
  texto: string
}

export function Asistente() {
  const { paraEnviar, opciones } = usarPaciente()
  const [estimacion, setEstimacion] = useState<Estimacion | null>(null)
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

  // El asistente necesita un paciente del que hablar.
  useEffect(() => {
    if (!opciones) return
    api
      .enviar<Estimacion>('/estimar', paraEnviar)
      .then(setEstimacion)
      .catch(() => setEstimacion(null))
  }, [opciones, paraEnviar])

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
      setFallo(e instanceof ErrorApi ? e.message : 'No se pudo preguntar.')
    } finally {
      setPensando(false)
    }
  }

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="El asistente">
        <p>
          Explica el resultado en palabras corrientes, para quien no sabe de modelos. Habla
          siempre del paciente que esté cargado, y cuando no sabe algo lo dice en vez de
          inventarlo.
        </p>
      </Encabezado>

      {estimacion && (
        <div className="sobre-quien">
          <p className="antetitulo">Hablando de</p>
          <p>
            Una hospitalización con <strong>{porcentaje(estimacion.probabilidad)}</strong> de
            riesgo estimado,{' '}
            {estimacion.supera ? 'por encima del umbral' : 'por debajo del umbral'} de{' '}
            {porcentaje(estimacion.umbral)}.{' '}
            <a href="../estimar">Cámbielo en la pantalla de estimar</a>.
          </p>
        </div>
      )}

      {disponible === false && (
        <p className="aviso-asistente">
          El asistente no está configurado en este servidor. Todo lo demás funciona igual: el
          modelo, las estimaciones y el cálculo paso a paso no dependen de él.
        </p>
      )}

      <div className="conversacion">
        {turnos.length === 0 && disponible && (
          <p className="conversacion-vacia">
            Pregúntele con sus palabras. Si le pregunta algo que no tiene que ver con este
            modelo, se lo va a decir.
          </p>
        )}

        {turnos.map((t, i) => (
          <div key={i} className={t.quien === 'usted' ? 'turno usted' : 'turno asistente'}>
            {t.quien === 'asistente' && <p className="antetitulo">Asistente</p>}
            <div className="turno-cuerpo">{t.texto}</div>
          </div>
        ))}

        {pensando && (
          <div className="turno asistente">
            <p className="antetitulo">Asistente</p>
            <div className="turno-cuerpo pensando">Pensando</div>
          </div>
        )}

        <div ref={fondo} />
      </div>

      {fallo && <p className="aviso-asistente">{fallo}</p>}

      <form
        className="preguntar"
        onSubmit={(e) => {
          e.preventDefault()
          enviar(pregunta)
        }}
      >
        <input
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          placeholder="Pregunte lo que quiera sobre este resultado"
          aria-label="Su pregunta"
          disabled={!disponible || !estimacion}
        />
        <button
          type="submit"
          aria-label="Enviar la pregunta"
          disabled={!disponible || !estimacion || pensando || !pregunta.trim()}
        >
          →
        </button>
      </form>

      {sugerencias.length > 0 && disponible && (
        <div className="sugerencias">
          {sugerencias.map((s) => (
            <button key={s} type="button" onClick={() => enviar(s)} disabled={pensando}>
              {s}
            </button>
          ))}
        </div>
      )}

      <p className="nota-asistente">
        Lo que viaja al modelo de lenguaje es el riesgo estimado, el umbral, los factores que
        más pesaron y las limitaciones medidas. Nunca datos que identifiquen a una persona: en
        esta aplicación no existen, y la regla queda escrita para cuando alguien conecte datos
        reales.
      </p>

      <style>{`
        .sobre-quien {
          margin-top: 36px; padding: 18px 22px;
          background: var(--superficie); border-radius: var(--radius-tarjeta);
          font-size: 14.5px; max-width: 70ch;
        }
        .sobre-quien p:last-child { margin-top: 8px; line-height: 1.6; }
        .sobre-quien strong { font-weight: 600; }
        .sobre-quien a { color: var(--tinta); text-decoration: underline; text-underline-offset: 3px; }

        .conversacion {
          margin-top: 32px; display: flex; flex-direction: column; gap: 22px;
          min-height: 180px; max-width: 76ch;
        }
        .conversacion-vacia { font-size: 14.5px; color: var(--apagado); line-height: 1.7; }
        .turno { max-width: 88%; }
        .turno.usted {
          align-self: flex-end; background: var(--relleno); color: var(--sobre-relleno);
          border-radius: var(--radius-tarjeta); padding: 12px 18px;
          font-size: 15px; line-height: 1.55; max-width: 74%;
        }
        .turno.asistente .turno-cuerpo {
          border-left: 1px solid var(--filete-fuerte); padding-left: 18px;
          font-size: 15.5px; line-height: 1.75; white-space: pre-wrap;
        }
        .turno.asistente .antetitulo { margin-bottom: 7px; }
        .pensando::after {
          content: '…'; animation: puntos 1.4s steps(4, end) infinite;
        }
        @keyframes puntos { 0% { opacity: .3 } 50% { opacity: 1 } 100% { opacity: .3 } }

        .preguntar {
          display: flex; align-items: center; gap: 12px; margin-top: 28px;
          background: var(--superficie); border-radius: var(--radius-tarjeta);
          padding: 12px 12px 12px 22px; max-width: 76ch;
        }
        .preguntar input {
          flex: 1; background: none; border: 0; outline: none;
          font-family: var(--font-sans); font-size: 16px; color: var(--tinta);
          letter-spacing: -0.009em;
        }
        .preguntar input::placeholder { color: var(--apagado); }
        .preguntar button {
          width: 40px; height: 40px; border-radius: 50%; border: 0; flex: none;
          cursor: pointer; background: var(--relleno); color: var(--sobre-relleno);
          font-size: 17px; line-height: 1;
        }
        .preguntar button:disabled { opacity: .4; cursor: default; }

        .sugerencias { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; max-width: 76ch; }
        .sugerencias button {
          border-radius: 999px; border: 0; cursor: pointer;
          background: var(--relleno); color: var(--sobre-relleno);
          font-family: var(--font-sans); font-size: 13px; padding: 8px 16px;
          letter-spacing: -0.009em; text-align: left;
        }
        .sugerencias button:disabled { opacity: .45; cursor: default; }

        .aviso-asistente {
          margin-top: 24px; font-size: 14px; line-height: 1.65;
          color: var(--color-dato-4); max-width: 70ch;
        }
        .nota-asistente {
          margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--filete);
          font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 76ch;
        }
      `}</style>
    </div>
  )
}
