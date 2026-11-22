import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { entero, numero, porcentaje } from '../lib/formato'

/**
 * Pantalla 14: equidad y límites.
 *
 * La frase que ordena toda esta pantalla: no es lo mismo que no haya sesgo a
 * que no haya datos para medirlo. Varios grupos tienen tan pocos pacientes que
 * su cifra no significa nada, y eso se dice en vez de presentarla como si
 * significara algo.
 */

interface Resumen {
  atributo: string
  grupos_evaluados: number
  razon_paridad: number
  brecha_tasa_alerta: number
  brecha_recall: number
  grupo_menor_recall: string
  grupo_mayor_recall: string
  grupo_mas_alertado: string
}

interface Grupo {
  grupo: string
  n: number
  prevalencia: number
  tasa_alerta: number
  recall: number
  precision: number
  ROC_AUC: number
}

interface Escenario {
  escenario: string
  n: number
  prevalencia: number
  AP: number
  ROC_AUC: number
  recall: number
  precision: number
  tasa_alerta: number
}

interface Datos {
  resumen: Resumen[]
  raza: Grupo[]
  genero: Grupo[]
  edad: Grupo[]
  sensibilidad: Escenario[]
}

const MINIMO_CONFIABLE = 500

export function Equidad() {
  const [d, setD] = useState<Datos | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Datos>('/equidad')
      .then(setD)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer el modelo" titulo="Equidad y límites" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Conocer el modelo" titulo="Equidad y límites">
        <p>
          Si el modelo trata igual a todos los grupos, y —más importante— en cuáles no hay
          suficientes pacientes para poder afirmarlo.
        </p>
      </Encabezado>

      {!d && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {d && (
        <>
          <section className="bloque-e destacado">
            <h2>No es lo mismo que no haya sesgo a que no haya datos para medirlo</h2>
            <p className="texto-e">
              Esa distinción es lo más importante de esta pantalla. Hay grupos con ciento
              cuarenta pacientes: cualquier cifra que se calcule sobre ellos se mueve
              muchísimo con solo unos pocos casos distintos. Se muestran igual, pero marcados,
              porque esconderlos sería peor.
            </p>
          </section>

          <section className="bloque-e">
            <h2>La regla de los cuatro quintos</h2>
            <p className="texto-e">
              Una forma habitual de mirarlo: la razón entre el grupo menos favorecido y el más
              favorecido debería pasar de 0,80. Por debajo de eso hay que mirar con cuidado.
            </p>
            <div className="paridades">
              {d.resumen.map((r) => {
                const pasa = r.razon_paridad >= 0.8
                return (
                  <div key={r.atributo} className={pasa ? 'paridad' : 'paridad falla'}>
                    <p className="antetitulo">{r.atributo}</p>
                    <div className="paridad-v">{numero(r.razon_paridad, 3)}</div>
                    <p className="paridad-e">{pasa ? 'Pasa la regla' : 'No pasa la regla'}</p>
                    <dl>
                      <div>
                        <dt>Grupos evaluados</dt>
                        <dd>{r.grupos_evaluados}</dd>
                      </div>
                      <div>
                        <dt>Menos detectado</dt>
                        <dd>{r.grupo_menor_recall}</dd>
                      </div>
                      <div>
                        <dt>Más alertado</dt>
                        <dd>{r.grupo_mas_alertado}</dd>
                      </div>
                    </dl>
                  </div>
                )
              })}
            </div>
          </section>

          {[
            { titulo: 'Por grupo racial', filas: d.raza },
            { titulo: 'Por género', filas: d.genero },
            { titulo: 'Por edad', filas: d.edad },
          ]
            .filter((b) => b.filas.length > 0)
            .map((b) => (
              <section key={b.titulo} className="bloque-e">
                <h2>{b.titulo}</h2>
                <div className="tabla-envoltura">
                  <table className="tabla-e">
                    <thead>
                      <tr>
                        <th>Grupo</th>
                        <th className="n">Pacientes</th>
                        <th className="n">Reingresan</th>
                        <th className="n">Reciben alerta</th>
                        <th className="n">De los que vuelven, detecta</th>
                        <th className="n">ROC-AUC</th>
                      </tr>
                    </thead>
                    <tbody>
                      {b.filas.map((g) => {
                        const pocos = g.n < MINIMO_CONFIABLE
                        return (
                          <tr key={g.grupo} className={pocos ? 'pocos' : undefined}>
                            <td>
                              {g.grupo}
                              {pocos && <span className="aviso-pocos">pocos casos</span>}
                            </td>
                            <td className="n">{entero(g.n)}</td>
                            <td className="n">{porcentaje(g.prevalencia)}</td>
                            <td className="n">{porcentaje(g.tasa_alerta)}</td>
                            <td className="n">{porcentaje(g.recall)}</td>
                            <td className="n">{numero(g.ROC_AUC, 3)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            ))}

          <section className="bloque-e">
            <h2>Lo que de verdad preocupa</h2>
            <p className="texto-e">
              Entre los mayores de 80 años el modelo alerta sobre el 51,3 %, y entre los menores
              de 50 sobre el 30,2 %. Pero la proporción que de verdad reingresa es casi igual en
              los dos grupos: 11,9 % contra 11,5 %. El modelo está alertando mucho más a los
              mayores sin que su riesgo real lo justifique.
            </p>
            <p className="texto-e">
              Y su capacidad de distinguir cae con la edad: de 0,713 en los menores de 50 a
              0,619 en los mayores de 80. Dicho claro, con quienes más se usaría es con quienes
              peor funciona.
            </p>
          </section>

          {d.sensibilidad.length > 0 && (
            <section className="bloque-e">
              <h2>Dónde funciona y dónde no</h2>
              <p className="texto-e">
                El promedio esconde diferencias grandes. Estos escenarios las sacan a la luz.
              </p>
              <div className="tabla-envoltura">
                <table className="tabla-e">
                  <thead>
                    <tr>
                      <th>Escenario</th>
                      <th className="n">Pacientes</th>
                      <th className="n">Reingresan</th>
                      <th className="n">Detecta</th>
                      <th className="n">Acierta</th>
                      <th className="n">ROC-AUC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.sensibilidad.map((e) => (
                      <tr key={e.escenario}>
                        <td>{e.escenario}</td>
                        <td className="n">{entero(e.n)}</td>
                        <td className="n">{porcentaje(e.prevalencia)}</td>
                        <td className="n">{porcentaje(e.recall)}</td>
                        <td className="n">{porcentaje(e.precision)}</td>
                        <td className="n">{numero(e.ROC_AUC, 3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          <p className="nota-e">
            Todo esto se mide sobre el conjunto de prueba, y los datos son de hospitales de
            Estados Unidos entre 1999 y 2008. Un sistema de salud distinto, con otra población
            y otras reglas de egreso, daría cifras distintas. Antes de usar esto en cualquier
            parte habría que volver a medirlo con datos de ahí.
          </p>
        </>
      )}

      <style>{`
        .bloque-e { padding-block: 40px; border-top: 1px solid var(--filete); }
        .bloque-e:first-of-type { border-top: 0; padding-top: 28px; }
        .bloque-e h2 { font-size: 27px; max-width: 26ch; }
        .bloque-e.destacado {
          background: var(--superficie); border-radius: var(--radius-tarjeta);
          padding: 32px; border-top: 0; margin-top: 28px;
        }
        .texto-e { margin-top: 14px; font-size: 15.5px; line-height: 1.7; color: var(--apagado); max-width: 70ch; }

        .paridades { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; margin-top: 26px; }
        .paridad { border: 1px solid var(--filete); border-radius: var(--radius-tarjeta); padding: 20px; }
        .paridad.falla { border-color: var(--color-dato-3); }
        .paridad-v {
          font-family: var(--font-serif); font-weight: 300; font-size: 38px; margin-top: 10px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .paridad-e { margin-top: 4px; font-size: 11px; font-weight: 500; letter-spacing: .14em; text-transform: uppercase; color: var(--apagado); }
        .paridad.falla .paridad-e { color: var(--color-dato-4); }
        .paridad dl { margin: 18px 0 0; display: grid; gap: 9px; }
        .paridad dl div { display: flex; justify-content: space-between; gap: 10px; align-items: baseline; }
        .paridad dt { font-size: 12px; color: var(--apagado); }
        .paridad dd { margin: 0; font-size: 13px; text-align: right; }

        .tabla-envoltura { overflow-x: auto; margin-top: 24px; }
        .tabla-e { width: 100%; border-collapse: collapse; min-width: 680px; }
        .tabla-e th { text-align: left; font-size: 10.5px; font-weight: 500; letter-spacing: .12em; text-transform: uppercase; color: var(--apagado); padding: 0 14px 11px 0; border-bottom: 1px solid var(--filete); }
        .tabla-e th.n, .tabla-e td.n { text-align: right; padding-right: 0; }
        .tabla-e td { padding: 13px 14px 13px 0; border-bottom: 1px solid var(--filete); font-size: 14px; white-space: nowrap; }
        .tabla-e .pocos td { color: var(--apagado); }
        .aviso-pocos {
          display: inline-block; margin-left: 10px; border-radius: 999px;
          border: 1px solid var(--borde-suave); font-size: 10px; padding: 2px 8px; color: var(--apagado);
        }
        .nota-e {
          margin-top: 36px; padding-top: 20px; border-top: 1px solid var(--filete);
          font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 76ch;
        }
      `}</style>
    </div>
  )
}
