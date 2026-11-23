import { ArrowRight, Info } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ChatAsistente } from '../componentes/ChatAsistente'
import { Encabezado } from '../componentes/Encabezado'
import { api } from '../lib/api'
import { porcentaje, veces } from '../lib/formato'
import type { Estimacion } from '../lib/tiposModelo'
import { usarPaciente } from '../lib/usarPaciente'

/**
 * Pantalla 5: el asistente.
 *
 * Traduce el resultado a lenguaje corriente para quien no sabe de modelos.
 * Siempre responde sobre un paciente concreto, el que esté cargado: un
 * asistente que hable del modelo en abstracto no le sirve a nadie en la sala.
 *
 * Por eso la columna de la izquierda muestra de qué está hablando. Sin ella,
 * la conversación queda flotando y nadie sabe a qué resultado se refiere.
 *
 * Lo que viaja a Gemini es el resultado y las limitaciones medidas, nunca
 * datos que identifiquen a una persona.
 */
export function Asistente() {
  const { paraEnviar, opciones } = usarPaciente()
  const [estimacion, setEstimacion] = useState<Estimacion | null>(null)

  useEffect(() => {
    if (!opciones) return
    api
      .enviar<Estimacion>('/estimar', paraEnviar)
      .then(setEstimacion)
      .catch(() => setEstimacion(null))
  }, [opciones, paraEnviar])

  const prioridad = !estimacion
    ? ''
    : estimacion.supera
      ? 'Prioridad alta'
      : estimacion.probabilidad >= estimacion.umbral / 2
        ? 'Prioridad media'
        : 'Prioridad baja'

  return (
    <div>
      <Encabezado
        antetitulo="Trabajar · Apoyo a la decisión clínica"
        titulo="El asistente"
        acciones={
          <Link to="../estimar" className="pastilla pastilla-contorno pastilla-sm">
            Ver estimación
            <ArrowRight size={14} strokeWidth={2} aria-hidden="true" />
          </Link>
        }
      >
        <p>
          Entiende el resultado con palabras sencillas. Pregunte sobre esta estimación y sus
          límites.
        </p>
      </Encabezado>

      <div className="asistente-columnas">
        <aside className="tarjeta contexto">
          <div className="contexto-pad">
            <p className="contexto-rotulo">Contexto actual</p>
            <h2>Una hospitalización reciente</h2>
            <p className="contexto-sub">
              La conversación usa el resultado que está cargado en la pantalla de estimación.
            </p>

            {estimacion ? (
              <div className="contexto-caja">
                <p className="contexto-etiqueta">Reingreso estimado a 30 días</p>
                <div className="contexto-cifra">
                  <b>{porcentaje(estimacion.probabilidad)}</b>
                  <span className="nivel">{prioridad}</span>
                </div>

                <div className="contexto-barra">
                  <i style={{ width: `${Math.min(estimacion.probabilidad * 100 * 4, 100)}%` }} />
                  <b style={{ left: `${Math.min(estimacion.umbral * 100 * 4, 100)}%` }} />
                </div>
                <div className="contexto-extremos">
                  <span>
                    Estimación <b>{porcentaje(estimacion.probabilidad)}</b>
                  </span>
                  <span>
                    Umbral <b>{porcentaje(estimacion.umbral)}</b>
                  </span>
                </div>

                <div className="contexto-pie">
                  <span>
                    Tasa base de la cohorte <b>{porcentaje(estimacion.tasa_base)}</b>
                  </span>
                  <span className="contexto-veces">{veces(estimacion.veces_la_base)}</span>
                </div>
              </div>
            ) : (
              <p className="vacio">Cargando la estimación</p>
            )}
          </div>

          <div className="contexto-aviso">
            <Info size={14} strokeWidth={2} aria-hidden="true" />
            <p>
              La cifra es ilustrativa: no proviene de una historia clínica real ni de un modelo
              validado para uso clínico.
            </p>
          </div>
        </aside>

        <div className="tarjeta">
          <ChatAsistente estimacion={estimacion} alto={330} />
        </div>
      </div>
    </div>
  )
}
