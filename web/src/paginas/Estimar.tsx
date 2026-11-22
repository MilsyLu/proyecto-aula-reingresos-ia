import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Encabezado } from '../componentes/Encabezado'
import { FormularioPaciente } from '../componentes/FormularioPaciente'
import { api, ErrorApi } from '../lib/api'
import { conSigno, porcentaje, veces } from '../lib/formato'
import type { Estimacion } from '../lib/tiposModelo'
import { usarPaciente } from '../lib/usarPaciente'

/**
 * Pantalla 3: estimar un paciente.
 *
 * El riesgo se recalcula solo al cambiar un campo, con una pequeña espera para
 * no disparar una petición por cada tecla. Que el número se mueva mientras uno
 * escribe es lo que convierte el formulario en algo que se entiende: se ve qué
 * dato pesa y cuál no mueve nada.
 */
export function Estimar() {
  const { opciones, valores, cambiar, restablecer, paraEnviar, fueraDeRango, error } =
    usarPaciente()
  const [resultado, setResultado] = useState<Estimacion | null>(null)
  const [calculando, setCalculando] = useState(false)
  const [fallo, setFallo] = useState<string | null>(null)
  const peticion = useRef(0)

  const estimar = useCallback(async (entradas: Record<string, string | number>) => {
    const mia = ++peticion.current
    setCalculando(true)
    try {
      const datos = await api.enviar<Estimacion>('/estimar', entradas)
      // Si mientras tanto salió otra petición, esta ya no manda: sin esto, una
      // respuesta lenta puede pisar a una más nueva y mostrar un riesgo que no
      // corresponde a lo que está escrito en pantalla.
      if (mia === peticion.current) {
        setResultado(datos)
        setFallo(null)
      }
    } catch (e) {
      if (mia === peticion.current) {
        setFallo(e instanceof ErrorApi ? e.message : 'No se pudo estimar.')
      }
    } finally {
      if (mia === peticion.current) setCalculando(false)
    }
  }, [])

  useEffect(() => {
    if (!opciones) return
    const temporizador = setTimeout(() => estimar(paraEnviar), 260)
    return () => clearTimeout(temporizador)
  }, [opciones, paraEnviar, estimar])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Trabajar" titulo="Estimar un paciente" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="Estimar un paciente">
        <p>
          Escriba los datos de una hospitalización que ya terminó. El riesgo se recalcula solo a
          medida que cambia los campos, así que se ve enseguida cuál pesa y cuál no mueve nada.
        </p>
      </Encabezado>

      <div className="estimar-columnas">
        <section>
          {opciones ? (
            <FormularioPaciente
              campos={opciones.campos}
              valores={valores}
              onCambio={cambiar}
              deshabilitado={false}
            />
          ) : (
            <p className="antetitulo">Cargando el formulario</p>
          )}

          {opciones && (
            <button
              type="button"
              className="pastilla pastilla-contorno pastilla-sm"
              style={{ marginTop: 24 }}
              onClick={restablecer}
            >
              Volver al paciente típico
            </button>
          )}
        </section>

        <aside className="estimar-resultado">
          <p className="antetitulo">Riesgo de reingreso · 30 días</p>

          <div className="riesgo-cifra" aria-live="polite">
            {resultado ? porcentaje(resultado.probabilidad) : '—'}
          </div>

          {resultado && (
            <>
              <div className="riesgo-barra">
                <i style={{ width: `${Math.min(resultado.probabilidad * 100, 100)}%` }} />
                <b style={{ left: `${resultado.umbral * 100}%` }} />
              </div>

              <div className="riesgo-datos">
                <div>
                  <p>Tasa base</p>
                  <p>{porcentaje(resultado.tasa_base)}</p>
                </div>
                <div>
                  <p>Umbral</p>
                  <p>{porcentaje(resultado.umbral)}</p>
                </div>
                <div>
                  <p>Veces la base</p>
                  <p>{veces(resultado.veces_la_base)}</p>
                </div>
              </div>

              <p className="riesgo-decision">
                {resultado.supera
                  ? 'Entra en la lista de llamadas del programa.'
                  : 'No alcanza el umbral: queda fuera de la lista.'}
              </p>

              <div className="riesgo-peso">
                <h3>Qué pesó en este resultado</h3>
                {resultado.efectos.length === 0 ? (
                  <p className="riesgo-nota">
                    Todos los datos están en su valor típico, así que el riesgo es el del
                    paciente promedio de la cohorte. Cambie algún campo para ver qué lo mueve.
                  </p>
                ) : (
                  <>
                    {resultado.efectos.map((e) => {
                      const ancho = Math.min(Math.abs(e.efecto) / 0.25, 1) * 100
                      return (
                        <div key={e.campo} className="peso-fila">
                          <div className="peso-cabeza">
                            <span>
                              {e.nombre}: <strong>{e.valor}</strong>
                            </span>
                            <span className="peso-valor">
                              {conSigno(e.efecto * 100)} pts
                            </span>
                          </div>
                          <div className="peso-barra">
                            <i
                              style={{
                                width: `${ancho}%`,
                                background:
                                  e.efecto >= 0 ? 'var(--color-dato-3)' : 'var(--color-teal)',
                              }}
                            />
                          </div>
                          <p className="peso-pie">
                            Con el valor típico ({e.tipico}) bajaría a {porcentaje(e.sin_el)}.
                          </p>
                        </div>
                      )
                    })}
                    <p className="riesgo-nota">
                      No es una aproximación estadística: cada cifra se obtiene volviéndole a
                      preguntar al modelo con ese dato cambiado.
                    </p>
                  </>
                )}
              </div>

              <Link to="../paso-a-paso" className="pastilla pastilla-contorno pastilla-sm riesgo-enlace">
                Ver el cálculo paso a paso
              </Link>
            </>
          )}

          {fueraDeRango.length > 0 && (
            <p className="riesgo-aviso">
              Hay valores fuera de rango; se está usando el más cercano permitido.
            </p>
          )}
          {fallo && <p className="riesgo-aviso">{fallo}</p>}
          {calculando && !resultado && <p className="antetitulo">Calculando</p>}
        </aside>
      </div>

      <style>{`
        .estimar-columnas {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 0.92fr);
          gap: 56px;
          align-items: start;
          margin-top: 44px;
        }
        .estimar-resultado { position: sticky; top: 96px; }
        .riesgo-cifra {
          font-family: var(--font-serif);
          font-weight: 300;
          font-size: clamp(50px, 7vw, 80px);
          line-height: .95;
          letter-spacing: -0.02em;
          color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
          margin-top: 12px;
        }
        .riesgo-barra {
          position: relative; height: 4px; background: var(--filete); margin-top: 26px;
        }
        .riesgo-barra i {
          position: absolute; left: 0; top: 0; height: 4px;
          background: var(--color-dato-3);
          transition: width .5s cubic-bezier(.2,.75,.2,1);
        }
        .riesgo-barra b {
          position: absolute; top: -7px; width: 1px; height: 18px; background: var(--apagado);
        }
        .riesgo-datos { display: flex; gap: 32px; margin-top: 18px; flex-wrap: wrap; }
        .riesgo-datos p:first-child {
          font-size: 11px; font-weight: 500; letter-spacing: .14em;
          text-transform: uppercase; color: var(--apagado);
        }
        .riesgo-datos p:last-child {
          font-size: 16px; margin-top: 5px;
          font-variant-numeric: tabular-nums lining-nums;
        }
        .riesgo-decision { margin-top: 20px; font-size: 14.5px; }
        .riesgo-peso {
          margin-top: 30px; padding: 24px;
          background: var(--superficie); border-radius: var(--radius-tarjeta);
        }
        .riesgo-peso h3 { font-size: 20px; }
        .peso-fila { margin-top: 18px; }
        .peso-cabeza {
          display: flex; justify-content: space-between; gap: 12px;
          align-items: baseline; font-size: 14px;
        }
        .peso-cabeza strong { font-weight: 600; }
        .peso-valor { font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; }
        .peso-barra { height: 6px; background: var(--filete); margin-top: 8px; border-radius: 999px; }
        .peso-barra i {
          display: block; height: 6px; border-radius: 999px;
          transition: width .5s cubic-bezier(.2,.75,.2,1);
        }
        .peso-pie { margin-top: 7px; font-size: 12.5px; color: var(--apagado); }
        .riesgo-nota { margin-top: 18px; font-size: 13px; line-height: 1.65; color: var(--apagado); }
        .riesgo-enlace { margin-top: 24px; }
        .riesgo-aviso { margin-top: 16px; font-size: 13px; color: var(--color-dato-4); }
        @media (width < 1040px) {
          .estimar-columnas { grid-template-columns: 1fr; gap: 40px; }
          .estimar-resultado { position: static; }
        }
      `}</style>
    </div>
  )
}
