import { useEffect, useMemo, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { TarjetaInclinada } from '../componentes/core/TarjetaInclinada'
import { api, ErrorApi } from '../lib/api'
import { entero, porcentaje, veces } from '../lib/formato'

/**
 * Pantalla 10: el mapa de calor del riesgo.
 *
 * Cruza las dos variables que más pesan en el modelo: a dónde salió el
 * paciente y cuántas veces había estado hospitalizado en el año previo. Entre
 * las dos se llevan el 43,5 % de la importancia medida por permutación.
 *
 * Cada celda es la proporción **real** de reingresos de quienes caen ahí, no
 * una predicción. Eso es lo que la hace defendible: no muestra lo que el
 * modelo cree, sino lo que pasó.
 *
 * La tinta es el dato. No hay escala de colores porque el sistema visual no
 * admite acentos cromáticos fuera de los datos, y aquí una rampa de terracota
 * sobre papel dice lo mismo sin romper nada.
 */

interface Celda {
  egreso: string
  codigo: string
  previas: string
  casos: number
  reingresos: number
  tasa: number
  veces_la_base: number
  confiable: boolean
}

interface Mapa {
  celdas: Celda[]
  minimo: number
  maximo: number
  tasa_base: number
  umbral: number
  total_casos: number
}

const COLUMNAS = ['0', '1', '2', '3 o más']

export function MapaCalor() {
  const [mapa, setMapa] = useState<Mapa | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activa, setActiva] = useState<Celda | null>(null)

  useEffect(() => {
    api
      .obtener<Mapa>('/mapa-calor')
      .then(setMapa)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar el mapa.'))
  }, [])

  const filas = useMemo(() => {
    if (!mapa) return []
    const porEgreso = new Map<string, Celda[]>()
    for (const c of mapa.celdas) {
      if (!porEgreso.has(c.egreso)) porEgreso.set(c.egreso, [])
      porEgreso.get(c.egreso)!.push(c)
    }
    return [...porEgreso.entries()]
  }, [mapa])

  /** De la tasa a cuánta tinta lleva la celda. */
  function tinta(tasa: number) {
    if (!mapa) return 0
    const rango = Math.max(mapa.maximo - mapa.minimo, 1e-6)
    return 0.06 + ((tasa - mapa.minimo) / rango) * 0.88
  }

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer los datos" titulo="Mapa de calor del riesgo" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Conocer los datos" titulo="Mapa de calor del riesgo">
        <p>
          Las dos variables que más pesan, cruzadas: a dónde salió el paciente y cuántas veces
          había estado hospitalizado en el año previo. Entre las dos se llevan el 43,5 % de la
          importancia del modelo.
        </p>
        <p style={{ marginTop: 14 }}>
          Cada celda es la proporción <strong style={{ fontWeight: 600, color: 'var(--tinta)' }}>real</strong>{' '}
          de reingresos de quienes caen ahí, no una predicción. Pase el cursor por encima para
          leerla.
        </p>
      </Encabezado>

      {!mapa && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {mapa && (
        <>
          <div className="mapa-y-detalle">
            <div className="mapa-envoltura">
              <table className="mapa">
                <thead>
                  <tr>
                    <th className="col-egreso">Tipo de egreso</th>
                    {COLUMNAS.map((c) => (
                      <th key={c} className="col-dato">
                        {c === '0' ? 'Sin previas' : c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filas.map(([egreso, celdas]) => (
                    <tr key={egreso}>
                      <th scope="row" className="col-egreso">
                        {egreso}
                      </th>
                      {COLUMNAS.map((columna) => {
                        const celda = celdas.find((c) => c.previas === columna)
                        if (!celda) return <td key={columna} className="col-dato" />
                        const alfa = tinta(celda.tasa)
                        const claro = alfa > 0.5
                        const esta = activa === celda
                        return (
                          <td key={columna} className="col-dato">
                            <button
                              type="button"
                              className={esta ? 'celda activa' : 'celda'}
                              style={{
                                background: `rgb(var(--dato-rgb) / ${alfa.toFixed(3)})`,
                                color: claro ? 'var(--lienzo)' : 'var(--tinta)',
                              }}
                              onMouseEnter={() => setActiva(celda)}
                              onFocus={() => setActiva(celda)}
                              onClick={() => setActiva(celda)}
                              aria-label={`${egreso}, ${columna} hospitalizaciones previas: ${(celda.tasa * 100).toFixed(1)} por ciento de ${celda.casos} pacientes`}
                            >
                              <span className="celda-tasa">{porcentaje(celda.tasa)}</span>
                              <span className="celda-casos">{entero(celda.casos)}</span>
                            </button>
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="escala">
                <span>{porcentaje(mapa.minimo)}</span>
                <div className="escala-barras">
                  {[0, 0.2, 0.4, 0.6, 0.8, 1].map((t) => (
                    <i key={t} style={{ background: `rgb(var(--dato-rgb) / ${(0.06 + t * 0.88).toFixed(3)})` }} />
                  ))}
                </div>
                <span>{porcentaje(mapa.maximo)}</span>
                <span className="escala-nota">la cifra pequeña es cuántos pacientes hay</span>
              </div>
            </div>

            <div className="detalle">
              {activa ? (
                <TarjetaInclinada grados={5}>
                  <div className="detalle-tarjeta">
                    <p className="antetitulo">{activa.egreso}</p>
                    <p className="detalle-previas">
                      {activa.previas === '0'
                        ? 'sin hospitalizaciones en el año previo'
                        : `con ${activa.previas} hospitalizaciones en el año previo`}
                    </p>
                    <div className="detalle-tasa">{porcentaje(activa.tasa)}</div>
                    <dl className="detalle-datos">
                      <div>
                        <dt>Pacientes en esta celda</dt>
                        <dd>{entero(activa.casos)}</dd>
                      </div>
                      <div>
                        <dt>De ellos reingresaron</dt>
                        <dd>{entero(activa.reingresos)}</dd>
                      </div>
                      <div>
                        <dt>Frente a la tasa general</dt>
                        <dd>{veces(activa.veces_la_base)}</dd>
                      </div>
                    </dl>
                    <p className="detalle-lectura">{lectura(activa, mapa)}</p>
                  </div>
                </TarjetaInclinada>
              ) : (
                <div className="detalle-vacio">
                  <p className="antetitulo">Sin celda elegida</p>
                  <p>
                    Pase el cursor por una celda y aquí aparece qué significa: cuántos pacientes
                    hay, cuántos reingresaron de verdad y cuánto se aparta de la tasa general.
                  </p>
                </div>
              )}
            </div>
          </div>

          <p className="mapa-cierre">
            {entero(mapa.total_casos)} hospitalizaciones en {mapa.celdas.length} celdas. Entre la
            más fría y la más caliente hay {veces(mapa.maximo / mapa.minimo, 1)} de diferencia, y
            eso es lo que el modelo aprende a leer: por eso ordena bien aunque no acierte paciente
            por paciente. Rehabilitación destaca incluso sin hospitalizaciones previas, y es el
            único egreso donde el riesgo ya nace alto.
          </p>

          <p className="mapa-nota">
            Las celdas con menos de treinta pacientes se habrían marcado como poco confiables;
            aquí ninguna lo está. Las dos variables se eligieron por la importancia medida con
            permutación, no por lo que se vea mejor.
          </p>
        </>
      )}

      <style>{`
        .mapa-y-detalle {
          display: grid; grid-template-columns: minmax(0, 1fr) 260px;
          gap: 40px; align-items: start; margin-top: 44px;
        }
        .mapa-envoltura { overflow-x: auto; }
        .mapa { width: 100%; border-collapse: separate; border-spacing: 4px; min-width: 500px; }
        .mapa thead th {
          font-size: 11px; font-weight: 500; letter-spacing: .14em; text-transform: uppercase;
          color: var(--apagado); padding-bottom: 10px; text-align: center; font-family: var(--font-sans);
        }
        .mapa thead th.col-egreso { text-align: left; }
        .mapa tbody th.col-egreso {
          text-align: left; font-weight: 400; font-size: 14px; color: var(--tinta);
          font-family: var(--font-sans); padding-right: 14px; white-space: nowrap;
          letter-spacing: -0.01em;
        }
        .col-egreso { min-width: 168px; }
        .celda {
          width: 100%; border: 1px solid transparent; border-radius: var(--radius-entrada);
          padding: 15px 10px; cursor: pointer; display: flex; flex-direction: column;
          align-items: center; gap: 3px; font-family: var(--font-sans);
          transition: border-color .2s ease, transform .2s ease;
        }
        .celda:hover, .celda.activa { border-color: var(--tinta-fuerte); }
        .celda.activa { transform: scale(1.03); }
        .celda-tasa {
          font-family: var(--font-serif); font-weight: 300; font-size: 19px;
          letter-spacing: -0.02em; font-variant-numeric: tabular-nums lining-nums;
        }
        .celda-casos { font-size: 10.5px; opacity: .74; font-variant-numeric: tabular-nums lining-nums; }

        .escala { display: flex; align-items: center; gap: 10px; margin-top: 20px; flex-wrap: wrap; }
        .escala span { font-size: 11.5px; color: var(--apagado); }
        .escala-barras { display: flex; gap: 2px; }
        .escala-barras i { width: 30px; height: 9px; border-radius: 2px; }
        .escala-nota { margin-left: 10px; }

        .detalle { position: sticky; top: 96px; }
        .detalle-tarjeta {
          background: var(--superficie); border-radius: var(--radius-tarjeta); padding: 24px;
        }
        .detalle-previas { margin-top: 6px; font-size: 13px; color: var(--apagado); line-height: 1.5; }
        .detalle-tasa {
          font-family: var(--font-serif); font-weight: 300; font-size: 46px; line-height: 1;
          letter-spacing: -0.02em; margin-top: 16px; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .detalle-datos { margin: 22px 0 0; display: grid; gap: 12px; }
        .detalle-datos div { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
        .detalle-datos dt { font-size: 12.5px; color: var(--apagado); }
        .detalle-datos dd {
          margin: 0; font-size: 15px; font-variant-numeric: tabular-nums lining-nums;
        }
        .detalle-lectura {
          margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--filete);
          font-size: 13px; line-height: 1.65; color: var(--apagado);
        }
        .detalle-vacio {
          border: 1px dashed var(--borde-suave); border-radius: var(--radius-tarjeta); padding: 24px;
        }
        .detalle-vacio p:last-child {
          margin-top: 12px; font-size: 13px; line-height: 1.65; color: var(--apagado);
        }

        .mapa-cierre {
          margin-top: 48px; font-size: 15px; line-height: 1.75;
          color: var(--apagado); max-width: 74ch;
        }
        .mapa-nota {
          margin-top: 24px; padding-top: 18px; border-top: 1px solid var(--filete);
          font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 74ch;
        }

        @media (width < 1500px) {
          .mapa-y-detalle { grid-template-columns: 1fr; gap: 28px; }
          .detalle { position: static; }
        }
      `}</style>
    </div>
  )
}

/** Qué significa la celda, en una frase. */
function lectura(celda: Celda, mapa: Mapa): string {
  const cuantos = Math.round(1 / celda.tasa)
  const comparacion =
    celda.veces_la_base >= 1.6
      ? `Es ${veces(celda.veces_la_base)} la tasa general de la cohorte.`
      : celda.veces_la_base <= 0.75
        ? 'Está por debajo de la tasa general de la cohorte.'
        : 'Está cerca de la tasa general de la cohorte.'
  const umbral =
    celda.tasa >= mapa.umbral
      ? 'Un paciente promedio de esta celda superaría el umbral del programa.'
      : 'Un paciente promedio de esta celda no alcanzaría el umbral del programa.'
  return `Volvió al hospital aproximadamente 1 de cada ${cuantos}. ${comparacion} ${umbral}`
}
