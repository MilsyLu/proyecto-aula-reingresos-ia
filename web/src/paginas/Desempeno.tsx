import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { entero, numero, porcentaje, veces } from '../lib/formato'

/**
 * Pantalla 12: desempeño y métricas.
 *
 * La pantalla empieza por las metas de la Fase 1, incluida la que no se
 * cumplió. Ponerla primero y no esconderla al final es una decisión: un
 * informe que solo muestra lo que salió bien no es un informe.
 *
 * Y la tabla de ganancia es la que de verdad responde la pregunta operativa.
 * «Precisión 0,178» no es una propiedad del modelo: es el valor que toma
 * cuando se alerta sobre el 38 % de la población. Si el programa solo alcanza
 * para el 2 %, entre esos pacientes reingresa el 43 %.
 */

interface Meta {
  'meta de la Fase 1': string
  objetivo: number
  'obtenido en prueba': number
  cumple: string
}

interface Final {
  conjunto: string
  AP: number
  ROC_AUC: number
  recall: number
  precision: number
  F1: number
  exactitud: number
  Brier: number
  VP: number
  FN: number
  FP: number
  VN: number
}

interface Tramo {
  fraccion: number
  pacientes: number
  tasa: number
  veces: number
  cobertura: number
}

interface Calibracion {
  'probabilidad media predicha': number
  'frecuencia observada': number
  diferencia: number
}

interface Umbral {
  umbral: number
  alertas: number
  '% de la poblacion': number
  recall: number
  precision: number
}

interface Datos {
  finales: Final[]
  calibracion: Calibracion[]
  metas: Meta[]
  umbrales: Umbral[]
  ganancia: Tramo[]
  tasa_base: number
  umbral: number
}

export function Desempeno() {
  const [d, setD] = useState<Datos | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Datos>('/desempeno')
      .then(setD)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer el modelo" titulo="Desempeño y métricas" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  const prueba = d?.finales.find((f) => f.conjunto === 'PRUEBA')

  return (
    <div>
      <Encabezado antetitulo="Conocer el modelo" titulo="Desempeño y métricas">
        <p>
          Qué tan bien rinde el modelo oficial sobre el conjunto de prueba, que se miró una sola
          vez. Empezando por la meta que no se cumplió.
        </p>
      </Encabezado>

      {!d && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {d && prueba && (
        <>
          <section className="bloque-d">
            <h2>Las metas de la Fase 1</h2>
            <p className="texto-d">
              Se fijaron antes de ver un solo resultado. Tres se cumplieron y una no, y la que
              no se cumplió va aquí arriba y no escondida al final.
            </p>
            <div className="metas">
              {d.metas.map((m) => {
                const cumple = m.cumple.trim().toUpperCase() === 'SI'
                return (
                  <div key={m['meta de la Fase 1']} className={cumple ? 'meta' : 'meta falla'}>
                    <p className="meta-nombre">{m['meta de la Fase 1']}</p>
                    <div className="meta-cifras">
                      <span>
                        objetivo <strong>{numero(m.objetivo, 4)}</strong>
                      </span>
                      <span>
                        obtenido <strong>{numero(m['obtenido en prueba'], 4)}</strong>
                      </span>
                    </div>
                    <p className="meta-estado">{cumple ? 'Cumple' : 'No cumple'}</p>
                  </div>
                )
              })}
            </div>
            <p className="nota-d">
              La precisión se quedó en 0,178 frente a la meta de 0,20. Dicho en claro: de cada
              seis pacientes que el modelo señala, uno reingresa de verdad. Subirla exigiría
              alertar a menos gente, y entonces se escaparían más de los que sí vuelven.
            </p>
          </section>

          <section className="bloque-d">
            <h2>A cuánta gente conviene llamar</h2>
            <p className="texto-d">
              Esta es la tabla que de verdad responde la pregunta operativa. La precisión no es
              una propiedad fija del modelo: depende de a cuántos se alerte. Mientras más corta
              la lista, más alta la proporción de aciertos, y menos reingresos se alcanzan a
              cubrir.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-d">
                <thead>
                  <tr>
                    <th>Si se llama al…</th>
                    <th className="n">Pacientes</th>
                    <th className="n">De ellos reingresa</th>
                    <th className="n">Veces la tasa base</th>
                    <th className="n">Cubre de los reingresos</th>
                  </tr>
                </thead>
                <tbody>
                  {d.ganancia.map((g) => (
                    <tr key={g.fraccion}>
                      <td>{porcentaje(g.fraccion, g.fraccion < 0.1 ? 0 : 1)} de mayor riesgo</td>
                      <td className="n">{entero(g.pacientes)}</td>
                      <td className="n">{porcentaje(g.tasa)}</td>
                      <td className="n">{veces(g.veces)}</td>
                      <td className="n">{porcentaje(g.cobertura)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="nota-d">
              Con la tasa general en {porcentaje(d.tasa_base)}, llamar a los 397 de mayor riesgo
              encuentra casi cuatro veces más reingresos que llamar al azar. Eso es lo que el
              modelo aporta, y se nota aunque la precisión sea baja.
            </p>
          </section>

          <section className="bloque-d">
            <h2>Las cifras del conjunto de prueba</h2>
            <div className="cifras-d">
              <Dato v={numero(prueba.AP, 4)} n="Average precision. Es la métrica principal" />
              <Dato v={numero(prueba.ROC_AUC, 4)} n="ROC-AUC, en el rango de LACE y HOSPITAL" />
              <Dato v={porcentaje(prueba.recall)} n="De los que reingresan, cuántos detecta" />
              <Dato v={porcentaje(prueba.precision)} n="De los que alerta, cuántos reingresan" />
              <Dato v={numero(prueba.Brier, 4)} n="Brier. Mientras más bajo, mejor calibrado" />
              <Dato
                v={porcentaje((prueba.VP + prueba.FP) / (prueba.VP + prueba.FN + prueba.FP + prueba.VN))}
                n="De la población recibe alerta"
              />
            </div>
            <div className="matriz">
              <p className="antetitulo">Qué pasó con las {entero(prueba.VP + prueba.FN + prueba.FP + prueba.VN)} hospitalizaciones</p>
              <div className="matriz-rejilla">
                <Celda n={prueba.VP} t="Alertó y reingresó" bien />
                <Celda n={prueba.FN} t="No alertó y reingresó" />
                <Celda n={prueba.FP} t="Alertó y no reingresó" />
                <Celda n={prueba.VN} t="No alertó y no reingresó" bien />
              </div>
              <p className="nota-d">
                Los {entero(prueba.FN)} de arriba a la derecha son los que se escapan, y son el
                costo real de poner el umbral donde está. Los {entero(prueba.FP)} de abajo a la
                izquierda son llamadas que no hacían falta: molestan, pero no hacen daño.
              </p>
            </div>
          </section>

          <section className="bloque-d">
            <h2>Si se mueve el umbral</h2>
            <p className="texto-d">
              Cada fila es una decisión distinta sobre a cuánta gente alertar. No hay una
              correcta: depende de cuántas llamadas puede hacer el programa.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-d">
                <thead>
                  <tr>
                    <th className="n">Umbral</th>
                    <th className="n">Alerta sobre</th>
                    <th className="n">Detecta</th>
                    <th className="n">Acierta</th>
                  </tr>
                </thead>
                <tbody>
                  {d.umbrales.map((u) => {
                    const esElegido = Math.abs(u.umbral - d.umbral) < 0.006
                    return (
                      <tr key={u.umbral} className={esElegido ? 'elegido' : undefined}>
                        <td className="n">
                          {numero(u.umbral, 3)}
                          {esElegido && <span className="marca-d">el del programa</span>}
                        </td>
                        <td className="n">{numero(u['% de la poblacion'], 1)}&nbsp;%</td>
                        <td className="n">{porcentaje(u.recall)}</td>
                        <td className="n">{porcentaje(u.precision)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bloque-d">
            <h2>Calibración</h2>
            <p className="texto-d">
              Cuando el modelo dice veinte por ciento, ¿reingresa de verdad el veinte por
              ciento? Esta tabla lo comprueba por tramos. Que las dos columnas se parezcan
              significa que la cifra se puede leer como una probabilidad y no solo como un
              puesto en la lista.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-d">
                <thead>
                  <tr>
                    <th className="n">El modelo dijo</th>
                    <th className="n">Reingresó de verdad</th>
                    <th className="n">Diferencia</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {d.calibracion.map((c, i) => (
                    <tr key={i}>
                      <td className="n">{porcentaje(c['probabilidad media predicha'])}</td>
                      <td className="n">{porcentaje(c['frecuencia observada'])}</td>
                      <td className="n">{numero(c.diferencia * 100, 2)} pts</td>
                      <td className="barra-cal">
                        <i
                          style={{
                            width: `${Math.min(Math.abs(c.diferencia) * 900, 100)}%`,
                            marginLeft: c.diferencia < 0 ? 'auto' : undefined,
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      <style>{`
        .bloque-d { padding-block: 40px; border-top: 1px solid var(--filete); }
        .bloque-d:first-of-type { border-top: 0; padding-top: 28px; }
        .bloque-d h2 { font-size: 27px; }
        .texto-d { margin-top: 12px; font-size: 15.5px; line-height: 1.7; color: var(--apagado); max-width: 68ch; }
        .nota-d { margin-top: 20px; font-size: 13px; line-height: 1.7; color: var(--apagado); max-width: 74ch; }

        .metas { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; margin-top: 24px; }
        .meta { border: 1px solid var(--filete); border-radius: var(--radius-tarjeta); padding: 18px; }
        .meta.falla { border-color: var(--color-dato-3); }
        .meta-nombre { font-size: 13.5px; line-height: 1.45; }
        .meta-cifras { display: flex; gap: 18px; margin-top: 14px; font-size: 12px; color: var(--apagado); flex-wrap: wrap; }
        .meta-cifras strong { font-weight: 600; color: var(--tinta); font-variant-numeric: tabular-nums lining-nums; }
        .meta-estado { margin-top: 12px; font-size: 11px; font-weight: 500; letter-spacing: .14em; text-transform: uppercase; color: var(--apagado); }
        .meta.falla .meta-estado { color: var(--color-dato-4); }

        .cifras-d { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 26px; margin-top: 26px; }
        .dato-d-v { font-family: var(--font-serif); font-weight: 300; font-size: 32px; letter-spacing: -0.02em; color: var(--tinta-fuerte); font-variant-numeric: tabular-nums lining-nums; }
        .dato-d-n { margin-top: 7px; font-size: 12px; line-height: 1.5; color: var(--apagado); }

        .matriz { margin-top: 36px; padding: 24px; background: var(--superficie); border-radius: var(--radius-tarjeta); }
        .matriz-rejilla { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-top: 16px; }
        .celda-m { border: 1px solid var(--filete); border-radius: var(--radius-entrada); padding: 16px; }
        .celda-m.bien { border-color: var(--borde-suave); }
        .celda-m-n { font-family: var(--font-serif); font-weight: 300; font-size: 28px; letter-spacing: -0.02em; font-variant-numeric: tabular-nums lining-nums; }
        .celda-m-t { margin-top: 6px; font-size: 12.5px; color: var(--apagado); }

        .tabla-envoltura { overflow-x: auto; margin-top: 24px; }
        .tabla-d { width: 100%; border-collapse: collapse; min-width: 560px; }
        .tabla-d th { text-align: left; font-size: 10.5px; font-weight: 500; letter-spacing: .12em; text-transform: uppercase; color: var(--apagado); white-space: nowrap; padding: 0 14px 11px 0; border-bottom: 1px solid var(--filete); }
        .tabla-d th.n, .tabla-d td.n { text-align: right; padding-right: 0; }
        .tabla-d td { padding: 13px 14px 13px 0; border-bottom: 1px solid var(--filete); font-size: 14px; white-space: nowrap; }
        .tabla-d .elegido td { background: var(--superficie-2); }
        .marca-d { display: inline-block; margin-left: 10px; border-radius: 999px; background: var(--relleno); color: var(--sobre-relleno); font-size: 10px; padding: 3px 9px; }
        .barra-cal { width: 120px; padding-right: 0 !important; }
        .barra-cal i { display: block; height: 5px; border-radius: 999px; background: var(--color-dato-3); }
      `}</style>
    </div>
  )
}

function Dato({ v, n }: { v: string; n: string }) {
  return (
    <div>
      <div className="dato-d-v">{v}</div>
      <p className="dato-d-n">{n}</p>
    </div>
  )
}

function Celda({ n, t, bien = false }: { n: number; t: string; bien?: boolean }) {
  return (
    <div className={bien ? 'celda-m bien' : 'celda-m'}>
      <div className="celda-m-n">{entero(n)}</div>
      <p className="celda-m-t">{t}</p>
    </div>
  )
}
