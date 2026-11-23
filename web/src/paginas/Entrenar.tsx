import { useRef, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { TextoRevelado } from '../componentes/core/TextoRevelado'
import { numero } from '../lib/formato'
import { useSesion } from '../lib/sesion'

/**
 * Pantalla 17: entrene usted el modelo.
 *
 * Idea de Iván. Lo valioso no es que entrene —el laboratorio de Streamlit ya
 * lo hacía— sino que la espera se convierta en la clase: el servidor manda una
 * línea por fase a medida que ocurre, y aquí se revela una lámina con cada una.
 *
 * Cuatro momentos enseñan en vez de solo informar, y el más importante es el
 * primero: si se elige partir al azar, se entrena de las dos formas y se
 * muestran los dos números juntos.
 */

interface Fase {
  n: number
  titulo: string
  estado: 'corriendo' | 'listo'
  cifra?: string
  detalle?: string
  segundos?: number
}

interface Leccion {
  clave: string
  titulo: string
  texto: string
  cifras?: { v: string; n: string }[]
  tabla?: {
    umbral: number
    alertados: number
    pct_alertados: number
    detecta: number
    acierta: number
  }[]
}

interface Cierre {
  suyo: number
  oficial: number
  segundos: number
  texto: string
}

export function Entrenar() {
  const { sesion } = useSesion()
  const puedeEntrenar = sesion?.permisos.includes('Entrenar en vivo') ?? false

  const [fases, setFases] = useState<Fase[]>([])
  const [lecciones, setLecciones] = useState<Leccion[]>([])
  const [avisos, setAvisos] = useState<string[]>([])
  const [cierre, setCierre] = useState<Cierre | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [corriendo, setCorriendo] = useState(false)
  const [particion, setParticion] = useState<'paciente' | 'azar'>('paciente')
  const entrada = useRef<HTMLInputElement | null>(null)

  async function entrenar(archivo: File) {
    setFases([])
    setLecciones([])
    setAvisos([])
    setCierre(null)
    setError(null)
    setCorriendo(true)

    const cuerpo = new FormData()
    cuerpo.append('archivo', archivo)
    cuerpo.append('particion', particion)

    try {
      const respuesta = await fetch('/api/entrenar', {
        method: 'POST',
        body: cuerpo,
        credentials: 'include',
      })
      if (!respuesta.ok || !respuesta.body) {
        const cuerpoError = await respuesta.json().catch(() => null)
        throw new Error(cuerpoError?.detail ?? 'No se pudo empezar el entrenamiento.')
      }

      // El servidor manda una linea de JSON por fase. Se lee a medida que
      // llega: si se esperara al final, la espera no enseñaria nada.
      const lector = respuesta.body.getReader()
      const decodificador = new TextDecoder()
      let resto = ''

      for (;;) {
        const { done, value } = await lector.read()
        if (done) break
        resto += decodificador.decode(value, { stream: true })
        const lineas = resto.split('\n')
        // La ultima puede estar partida a la mitad: se guarda para la proxima.
        resto = lineas.pop() ?? ''

        for (const linea of lineas) {
          if (!linea.trim()) continue
          let evento: Record<string, unknown>
          try {
            evento = JSON.parse(linea)
          } catch {
            continue
          }
          if (evento.tipo === 'fase') {
            const f = evento as unknown as Fase
            setFases((previas) => {
              const sinEsta = previas.filter((p) => p.n !== f.n)
              return [...sinEsta, f].sort((a, b) => a.n - b.n)
            })
          } else if (evento.tipo === 'leccion') {
            setLecciones((l) => [...l, evento as unknown as Leccion])
          } else if (evento.tipo === 'aviso') {
            setAvisos((a) => [...a, String(evento.mensaje)])
          } else if (evento.tipo === 'cierre') {
            setCierre(evento as unknown as Cierre)
          } else if (evento.tipo === 'error') {
            setError(String(evento.mensaje))
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'El entrenamiento falló.')
    } finally {
      setCorriendo(false)
    }
  }

  return (
    <div>
      <Encabezado antetitulo="Aprender haciendo" titulo="Entrene usted el modelo">
        <p>
          Suba un archivo con desenlaces y vea el entrenamiento ocurrir, fase por fase. No es
          una simulación: el modelo se entrena de verdad en el servidor, y la espera es la
          clase.
        </p>
      </Encabezado>

      {!puedeEntrenar ? (
        <p className="aviso-e">
          Entrenar consume el servidor, así que está reservado a coordinación. Si quiere ver el
          recorrido, pídale a la coordinación del programa que lo corra: enseña lo mismo.
        </p>
      ) : (
        <>
          <section className="preparar">
            <div>
              <p className="antetitulo">Antes de empezar, una decisión</p>
              <h2>¿Cómo reparte los datos?</h2>
              <p className="texto-e">
                Hay que separar los datos en dos: unos para que el modelo aprenda y otros para
                comprobarlo. La forma de repartirlos parece un detalle y no lo es.
              </p>
              <div className="opciones-p">
                <button
                  type="button"
                  className={particion === 'paciente' ? 'opcion-p activa' : 'opcion-p'}
                  onClick={() => setParticion('paciente')}
                >
                  <strong>Por paciente</strong>
                  <span>
                    Cada persona queda entera de un solo lado. Es lo correcto, y es lo que hace
                    el modelo oficial.
                  </span>
                </button>
                <button
                  type="button"
                  className={particion === 'azar' ? 'opcion-p activa' : 'opcion-p'}
                  onClick={() => setParticion('azar')}
                >
                  <strong>Al azar</strong>
                  <span>
                    Se reparten hospitalizaciones sin mirar de quién son. Entrena de las dos
                    formas y le muestra la diferencia. Tarda el doble.
                  </span>
                </button>
              </div>
            </div>

            <div className="zona-e">
              <p>
                Suelte el archivo o{' '}
                <button type="button" className="enlace-e" onClick={() => entrada.current?.click()}>
                  búsquelo
                </button>
              </p>
              <p className="nota-zona">
                Tiene que traer la columna <code>readmitted</code> o <code>y</code>: sin saber
                quién reingresó no hay nada que aprender. Hasta 20 MB.
              </p>
              <input
                ref={entrada}
                type="file"
                accept=".csv,.xlsx,.xls,text/csv"
                hidden
                disabled={corriendo}
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) entrenar(f)
                  e.target.value = ''
                }}
              />
              {corriendo && <p className="antetitulo" style={{ marginTop: 14 }}>Entrenando</p>}
            </div>
          </section>

          {avisos.map((a, i) => (
            <p key={i} className="aviso-e">
              {a}
            </p>
          ))}
          {error && <p className="error-e">{error}</p>}

          {fases.length > 0 && (
            <section className="pista">
              {fases.map((f) => (
                <div key={f.n} className={f.estado === 'listo' ? 'fase-e lista' : 'fase-e'}>
                  <span className="fase-n">{String(f.n).padStart(2, '0')}</span>
                  <span className="fase-t">
                    {f.titulo}
                    {f.detalle && <em>{f.detalle}</em>}
                  </span>
                  <span className="fase-c">{f.cifra ?? (f.estado === 'corriendo' ? '…' : '')}</span>
                  <span className="fase-s">
                    {f.segundos !== undefined ? `${numero(f.segundos, 1)} s` : ''}
                  </span>
                </div>
              ))}
            </section>
          )}

          {lecciones.map((l) => (
            <section key={l.clave} className="leccion">
              <p className="antetitulo">Lo que esto enseña</p>
              <h3>{l.titulo}</h3>
              {l.cifras && (
                <div className="cifras-l">
                  {l.cifras.map((c, i) => (
                    <div key={i}>
                      <div className="cifra-l-v">{c.v}</div>
                      <p>{c.n}</p>
                    </div>
                  ))}
                </div>
              )}
              {l.tabla && (
                <div className="tabla-envoltura">
                  <table className="tabla-l">
                    <thead>
                      <tr>
                        <th className="n">Umbral</th>
                        <th className="n">Alerta sobre</th>
                        <th className="n">Detecta</th>
                        <th className="n">Acierta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {l.tabla.map((f, i) => (
                        <tr key={i}>
                          <td className="n">{numero(f.umbral, 3)}</td>
                          <td className="n">{numero(f.pct_alertados * 100, 1)}&nbsp;%</td>
                          <td className="n">{numero(f.detecta * 100, 1)}&nbsp;%</td>
                          <td className="n">{numero(f.acierta * 100, 1)}&nbsp;%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <TextoRevelado className="texto-l" porPalabra={0.013}>
                {l.texto}
              </TextoRevelado>
            </section>
          ))}

          {cierre && (
            <section className="cierre-e">
              <p className="antetitulo">Terminó en {numero(cierre.segundos, 1)} segundos</p>
              <div className="duelo-e">
                <div>
                  <div className="duelo-v">{numero(cierre.suyo, 4)}</div>
                  <p>el modelo que acaba de entrenar</p>
                </div>
                <div>
                  <div className="duelo-v">{numero(cierre.oficial, 4)}</div>
                  <p>el modelo oficial del proyecto</p>
                </div>
              </div>
              <p className="texto-e">{cierre.texto}</p>
            </section>
          )}
        </>
      )}

      <style>{`
        .preparar {
          display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 0.85fr);
          gap: 40px; align-items: start; margin-top: 40px;
        }
        .preparar h2 { font-size: 25px; margin-top: 8px; }
        .texto-e { margin-top: 12px; font-size: 14.5px; line-height: 1.7; color: var(--apagado); max-width: 62ch; }

        .opciones-p { display: grid; gap: 10px; margin-top: 20px; }
        .opcion-p {
          text-align: left; border: 1px solid var(--filete); border-radius: var(--radius-tarjeta);
          background: transparent; cursor: pointer; padding: 16px 18px;
          font-family: var(--font-sans); display: grid; gap: 6px;
          transition: border-color .2s ease;
        }
        .opcion-p:hover { border-color: var(--borde-suave); }
        .opcion-p.activa { border-color: var(--filete-fuerte); background: var(--superficie); }
        .opcion-p strong { font-size: 14.5px; font-weight: 600; color: var(--tinta); }
        .opcion-p span { font-size: 12.5px; line-height: 1.55; color: var(--apagado); }

        .zona-e {
          border: 1px dashed var(--borde-suave); border-radius: var(--radius-tarjeta);
          padding: 32px; text-align: center;
        }
        .zona-e > p:first-child { font-size: 15px; }
        .nota-zona { margin-top: 10px; font-size: 12px; line-height: 1.6; color: var(--apagado); }
        .nota-zona code {
          font-family: ui-monospace, monospace; font-size: 11.5px;
          background: var(--superficie-2); padding: 1px 5px; border-radius: 4px;
        }
        .enlace-e {
          background: none; border: 0; padding: 0; cursor: pointer; color: var(--tinta);
          font-family: var(--font-sans); font-size: 15px;
          text-decoration: underline; text-underline-offset: 3px;
        }

        .aviso-e {
          margin-top: 22px; padding: 16px 20px; border-radius: var(--radius-entrada);
          background: var(--superficie); font-size: 13.5px; line-height: 1.7;
          color: var(--apagado); max-width: 76ch;
        }
        .error-e { margin-top: 20px; font-size: 14px; line-height: 1.7; color: var(--color-dato-4); max-width: 72ch; }

        .pista { margin-top: 36px; border-top: 1px solid var(--filete); }
        .fase-e {
          display: grid; grid-template-columns: 34px minmax(0, 1fr) 130px 64px;
          gap: 14px; align-items: baseline;
          padding-block: 14px; border-bottom: 1px solid var(--filete);
          opacity: .45; transition: opacity .5s ease;
        }
        .fase-e.lista { opacity: 1; }
        .fase-n {
          font-family: var(--font-nunito); font-size: 17px; color: var(--apagado);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .fase-t { font-size: 14.5px; }
        .fase-t em {
          display: block; font-style: normal; font-size: 12px;
          color: var(--apagado); margin-top: 4px; line-height: 1.5;
        }
        .fase-c {
          text-align: right; font-family: var(--font-nunito); font-weight: 900;
          font-size: 21px; letter-spacing: -0.02em;
          font-variant-numeric: tabular-nums lining-nums;
        }
        .fase-s { text-align: right; font-size: 11.5px; color: var(--apagado); font-variant-numeric: tabular-nums lining-nums; }

        .leccion {
          margin-top: 28px; background: var(--superficie);
          border-radius: var(--radius-tarjeta); padding: 30px;
        }
        .leccion h3 { font-size: 24px; margin-top: 8px; max-width: 26ch; }
        .cifras-l { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 24px; margin-top: 22px; }
        .cifra-l-v {
          font-family: var(--font-nunito); font-weight: 900; font-size: 34px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .cifras-l p { margin-top: 6px; font-size: 12px; line-height: 1.5; color: var(--apagado); }
        .texto-l { margin-top: 22px; font-size: 14.5px; line-height: 1.75; color: var(--apagado); max-width: 70ch; }

        .tabla-envoltura { overflow-x: auto; margin-top: 20px; }
        .tabla-l { width: 100%; border-collapse: collapse; min-width: 420px; max-width: 540px; }
        .tabla-l th {
          text-align: right; font-size: 10.5px; font-weight: 500; letter-spacing: .12em;
          text-transform: uppercase; color: var(--apagado);
          padding: 0 0 10px 14px; border-bottom: 1px solid var(--filete);
        }
        .tabla-l td {
          padding: 10px 0 10px 14px; border-bottom: 1px solid var(--filete);
          font-size: 13.5px; text-align: right;
          font-variant-numeric: tabular-nums lining-nums;
        }

        .cierre-e {
          margin-top: 32px; border: 1px solid var(--filete-fuerte);
          border-radius: var(--radius-tarjeta); padding: 30px;
        }
        .duelo-e { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 28px; margin-top: 18px; }
        .duelo-v {
          font-family: var(--font-nunito); font-weight: 900; font-size: 40px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .duelo-e p { margin-top: 6px; font-size: 12.5px; color: var(--apagado); }

        @media (width < 1000px) {
          .preparar { grid-template-columns: 1fr; gap: 28px; }
          .fase-e { grid-template-columns: 30px minmax(0, 1fr) 90px; }
          .fase-s { display: none; }
        }
      `}</style>
    </div>
  )
}
