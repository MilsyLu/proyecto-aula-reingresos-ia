import { useEffect, useMemo, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { entero, numero, porcentaje } from '../lib/formato'

/**
 * Pantalla 9: estadística descriptiva.
 *
 * Media, mediana, moda, desviación, cuartiles y asimetría de las diecisiete
 * variables numéricas, y la moda y los valores distintos de las treinta y
 * tres categóricas.
 *
 * Y una cosa que una tabla de estadísticas sola no da: la distribución de cada
 * variable con la tasa de reingreso de cada tramo encima. Eso permite ver de
 * un golpe si una variable tiene algo que decir o si es plana.
 */

interface Numerica {
  variable: string
  clave: string
  n: number
  faltantes: number
  media: number
  mediana: number
  moda: number
  desviacion: number
  minimo: number
  q1: number
  q3: number
  maximo: number
  asimetria: number
}

interface Categorica {
  variable: string
  clave: string
  n: number
  faltantes: number
  distintos: number
  moda: string
  frecuencia_moda: number
  porcentaje_moda: number
}

interface Tramo {
  variable: string
  clave: string
  centro: number
  desde: number
  hasta: number
  casos: number
  reingresos: number
  tasa: number
}

interface Descriptiva {
  numericas: Numerica[]
  categoricas: Categorica[]
  histogramas: Tramo[]
}

export function Descriptiva() {
  const [d, setD] = useState<Descriptiva | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [elegida, setElegida] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Descriptiva>('/descriptiva')
      .then((datos) => {
        setD(datos)
        // Se abre en la variable que más pesa en el modelo, no en la primera
        // de la lista: es la que alguien querría mirar primero.
        const preferida = datos.numericas.find((n) => n.clave === 'number_inpatient')
        setElegida(preferida?.clave ?? datos.numericas[0]?.clave ?? null)
      })
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  const tramos = useMemo(
    () => (d && elegida ? d.histogramas.filter((h) => h.clave === elegida) : []),
    [d, elegida],
  )
  const variable = useMemo(
    () => d?.numericas.find((n) => n.clave === elegida) ?? null,
    [d, elegida],
  )

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer los datos" titulo="Estadística descriptiva" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Conocer los datos" titulo="Estadística descriptiva">
        <p>
          Lo que hay dentro de cada variable antes de que el modelo la toque. Media, mediana,
          moda, desviación, cuartiles y asimetría; y para cada una, cómo se reparten los
          pacientes y qué proporción reingresó en cada tramo.
        </p>
      </Encabezado>

      {!d && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {d && (
        <>
          {/* ------------------------------------------- distribución */}
          <section className="seccion-desc">
            <h2>Cómo se reparte cada variable</h2>
            <p className="desc-texto">
              Elija una. La altura de cada barra es cuántos pacientes caen en ese tramo; la
              línea encima es qué proporción de ellos reingresó. Cuando la línea sube con la
              barra, la variable tiene algo que decir.
            </p>

            <div className="selector">
              {d.numericas.map((n) => (
                <button
                  key={n.clave}
                  type="button"
                  className={n.clave === elegida ? 'opcion activa' : 'opcion'}
                  onClick={() => setElegida(n.clave)}
                >
                  {n.variable}
                </button>
              ))}
            </div>

            {variable && tramos.length > 0 && <Histograma tramos={tramos} variable={variable} />}
          </section>

          {/* --------------------------------------------- numéricas */}
          <section className="seccion-desc">
            <h2>Las diecisiete numéricas</h2>
            <p className="desc-texto">
              La asimetría de la última columna dice si la variable está cargada hacia un lado.
              Por encima de 2 significa que la mayoría de pacientes se amontona en valores
              bajos y unos pocos se van muy lejos, que es justo lo que pasa con las visitas a
              urgencias.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-desc">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th className="n">Media</th>
                    <th className="n">Mediana</th>
                    <th className="n">Moda</th>
                    <th className="n">Desv.</th>
                    <th className="n">Mín.</th>
                    <th className="n">Q1</th>
                    <th className="n">Q3</th>
                    <th className="n">Máx.</th>
                    <th className="n">Asimetría</th>
                  </tr>
                </thead>
                <tbody>
                  {d.numericas.map((v) => (
                    <tr
                      key={v.clave}
                      className={v.clave === elegida ? 'resaltada' : undefined}
                      onClick={() => setElegida(v.clave)}
                    >
                      <td>{v.variable}</td>
                      <td className="n">{numero(v.media, 2)}</td>
                      <td className="n">{numero(v.mediana, 1)}</td>
                      <td className="n">{numero(v.moda, 1)}</td>
                      <td className="n">{numero(v.desviacion, 2)}</td>
                      <td className="n">{numero(v.minimo, 0)}</td>
                      <td className="n">{numero(v.q1, 1)}</td>
                      <td className="n">{numero(v.q3, 1)}</td>
                      <td className="n">{numero(v.maximo, 0)}</td>
                      <td className="n">{numero(v.asimetria, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* -------------------------------------------- categóricas */}
          <section className="seccion-desc">
            <h2>Las treinta y tres categóricas</h2>
            <p className="desc-texto">
              Cuando una sola categoría se lleva más del noventa por ciento de los casos, la
              variable casi no distingue a nadie. Pasa con la mayoría de los antidiabéticos, y
              explica por qué pesan tan poco en el modelo.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-desc">
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th className="n">Valores distintos</th>
                    <th>Más frecuente</th>
                    <th className="n">Cuántos</th>
                    <th className="n">Porcentaje</th>
                  </tr>
                </thead>
                <tbody>
                  {d.categoricas.map((v) => (
                    <tr key={v.clave} className={v.porcentaje_moda > 90 ? 'apagada' : undefined}>
                      <td>{v.variable}</td>
                      <td className="n">{entero(v.distintos)}</td>
                      <td>{v.moda}</td>
                      <td className="n">{entero(v.frecuencia_moda)}</td>
                      <td className="n">{numero(v.porcentaje_moda, 1)}&nbsp;%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="desc-nota">
              Las filas atenuadas son las que tienen una categoría por encima del noventa por
              ciento. Se dejan a la vista a propósito: forman parte de los datos y esconderlas
              daría una idea equivocada de cuánta información hay de verdad.
            </p>
          </section>
        </>
      )}

      <style>{`
        .seccion-desc { padding-block: 40px; border-top: 1px solid var(--filete); }
        .seccion-desc:first-of-type { border-top: 0; padding-top: 28px; }
        .seccion-desc h2 { font-size: 26px; }
        .desc-texto {
          margin-top: 12px; font-size: 15px; line-height: 1.7;
          color: var(--apagado); max-width: 68ch;
        }
        .desc-nota { margin-top: 18px; font-size: 12.5px; line-height: 1.65; color: var(--apagado); max-width: 72ch; }

        .selector { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 22px; }
        .opcion {
          border-radius: 999px; border: 1px solid var(--filete); background: transparent;
          cursor: pointer; padding: 7px 14px; font-family: var(--font-sans);
          font-size: 12.5px; color: var(--apagado); letter-spacing: -0.009em;
          transition: border-color .2s ease, color .2s ease;
        }
        .opcion:hover { border-color: var(--borde-suave); color: var(--tinta); }
        .opcion.activa { background: var(--relleno); color: var(--sobre-relleno); border-color: var(--relleno); }

        .tabla-envoltura { overflow-x: auto; margin-top: 24px; }
        .tabla-desc { width: 100%; border-collapse: collapse; min-width: 760px; }
        .tabla-desc th {
          text-align: left; font-size: 10.5px; font-weight: 500; letter-spacing: .12em;
          text-transform: uppercase; color: var(--apagado); white-space: nowrap;
          padding: 0 12px 11px 0; border-bottom: 1px solid var(--filete);
        }
        .tabla-desc th.n, .tabla-desc td.n { text-align: right; padding-right: 0; }
        .tabla-desc td {
          padding: 11px 12px 11px 0; border-bottom: 1px solid var(--filete);
          font-size: 13.5px; white-space: nowrap;
        }
        .tabla-desc tbody tr { cursor: pointer; }
        .tabla-desc tbody tr:hover { background: var(--superficie); }
        .tabla-desc .resaltada { background: var(--superficie); }
        .tabla-desc .apagada td { color: var(--apagado); }
      `}</style>
    </div>
  )
}

/** Barras de cuántos pacientes hay y línea de qué proporción reingresó. */
function Histograma({ tramos, variable }: { tramos: Tramo[]; variable: Numerica }) {
  const maxCasos = Math.max(...tramos.map((t) => t.casos))
  const maxTasa = Math.max(...tramos.map((t) => t.tasa), 0.01)
  const ancho = 1040
  const alto = 240
  const base = alto - 34

  const X = (i: number) => 10 + (i / Math.max(tramos.length - 1, 1)) * (ancho - 20)
  const Ytasa = (t: number) => 14 + (1 - t / maxTasa) * (base - 24)

  const lineaTasa = tramos
    .map((t, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Ytasa(t.tasa).toFixed(1)}`)
    .join(' ')

  const anchoBarra = Math.max((ancho - 20) / tramos.length - 3, 2)

  return (
    <figure className="histograma">
      <svg
        viewBox={`0 0 ${ancho} ${alto}`}
        style={{ width: '100%', height: 'auto' }}
        role="img"
        aria-label={`Distribución de ${variable.variable} en ${tramos.length} tramos, con la tasa de reingreso de cada uno`}
      >
        {tramos.map((t, i) => {
          const h = (t.casos / maxCasos) * (base - 30)
          return (
            <rect
              key={i}
              x={X(i) - anchoBarra / 2}
              y={base - h}
              width={anchoBarra}
              height={h}
              rx="1.5"
              fill="rgb(var(--tinta-rgb) / 0.16)"
            >
              <title>
                {`de ${t.desde.toFixed(1)} a ${t.hasta.toFixed(1)}: ${t.casos} pacientes, ${(t.tasa * 100).toFixed(1)} % reingresó`}
              </title>
            </rect>
          )
        })}
        <line x1="0" y1={base} x2={ancho} y2={base} stroke="var(--filete)" strokeWidth="1" />
        <path d={lineaTasa} fill="none" stroke="var(--color-dato-3)" strokeWidth="2" strokeLinejoin="round" />
        {tramos.map((t, i) => (
          <circle key={i} cx={X(i)} cy={Ytasa(t.tasa)} r="2.5" fill="var(--color-dato-3)" />
        ))}
      </svg>
      <figcaption>
        <span>
          <i className="muestra barra" /> cuántos pacientes
        </span>
        <span>
          <i className="muestra linea" /> qué proporción reingresó, de 0 a {porcentaje(maxTasa)}
        </span>
        <span className="rango">
          {variable.variable}: de {numero(variable.minimo, 0)} a {numero(variable.maximo, 0)},
          mediana {numero(variable.mediana, 1)}
        </span>
      </figcaption>

      <style>{`
        .histograma { margin: 26px 0 0; }
        .histograma figcaption {
          display: flex; flex-wrap: wrap; gap: 20px; margin-top: 10px;
          font-size: 11.5px; color: var(--apagado); align-items: center;
        }
        .histograma figcaption span { display: inline-flex; align-items: center; gap: 6px; }
        .muestra { display: inline-block; }
        .muestra.barra { width: 10px; height: 10px; border-radius: 2px; background: rgb(var(--tinta-rgb) / 0.16); }
        .muestra.linea { width: 14px; height: 2px; background: var(--color-dato-3); }
        .histograma .rango { margin-left: auto; }
      `}</style>
    </figure>
  )
}
