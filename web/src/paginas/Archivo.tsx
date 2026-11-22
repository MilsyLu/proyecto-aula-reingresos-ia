import { useRef, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { ErrorApi, api } from '../lib/api'
import { entero, porcentaje } from '../lib/formato'

/**
 * Pantalla 6: del archivo a la lista de llamadas.
 *
 * El coordinador sube el corte del día, dice a cuántas personas alcanza a
 * llamar, y recibe esa cantidad de pacientes ordenados por riesgo.
 *
 * La cobertura que se muestra arriba no cuenta columnas: pesa cada una por su
 * importancia. Un archivo con cuarenta columnas irrelevantes y sin las dos que
 * mandan tiene cobertura baja, y eso es justo lo que hay que saber antes de
 * creerle a la lista.
 */

interface Fila {
  puesto: number
  fila_csv: number
  probabilidad: number
  alerta: boolean
}

interface Resultado {
  filas_archivo: number
  descartados: number
  analizadas: number
  cobertura: number
  reconocidas: Record<string, string>
  sin_reconocer: string[]
  faltan_importantes: string[]
  rellenadas: number
  categorias_no_vistas: unknown[]
  umbral: number
  sobre_umbral: number
  lista: Fila[]
}

export function Archivo() {
  const [r, setR] = useState<Resultado | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [capacidad, setCapacidad] = useState(50)
  const [arrastrando, setArrastrando] = useState(false)
  const entrada = useRef<HTMLInputElement | null>(null)

  async function subir(archivo: File) {
    setCargando(true)
    setError(null)
    setR(null)
    const cuerpo = new FormData()
    cuerpo.append('archivo', archivo)
    try {
      const datos = await api.subir<Resultado>('/archivo', cuerpo)
      setR(datos)
      setCapacidad(Math.min(50, datos.analizadas))
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo analizar el archivo.')
    } finally {
      setCargando(false)
    }
  }

  function descargar() {
    if (!r) return
    const filas = r.lista.slice(0, capacidad)
    const csv = [
      'puesto,fila_del_archivo,riesgo,entra_en_la_lista',
      ...filas.map(
        (f) =>
          `${f.puesto},${f.fila_csv},${(f.probabilidad * 100).toFixed(2).replace('.', ',')},${f.alerta ? 'si' : 'no'}`,
      ),
    ].join('\n')
    // El BOM hace que Excel abra las tildes bien. Sin él, «días» sale roto.
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `lista-de-llamadas-${filas.length}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const lista = r ? r.lista.slice(0, capacidad) : []
  const alertados = lista.filter((f) => f.alerta).length

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="Del archivo a la lista de llamadas">
        <p>
          Suba el corte del día, diga a cuántas personas alcanza a llamar, y reciba esa cantidad
          de pacientes ordenados por riesgo. Reconoce las columnas aunque vengan en español y
          aunque falten.
        </p>
      </Encabezado>

      <div
        className={arrastrando ? 'zona arrastrando' : 'zona'}
        onDragOver={(e) => {
          e.preventDefault()
          setArrastrando(true)
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault()
          setArrastrando(false)
          const f = e.dataTransfer.files?.[0]
          if (f) subir(f)
        }}
      >
        <p className="zona-texto">
          Suelte aquí el archivo, o{' '}
          <button type="button" className="enlace" onClick={() => entrada.current?.click()}>
            búsquelo en su computador
          </button>
        </p>
        <p className="zona-nota">
          CSV o Excel · reconoce nombres de columna en español e inglés · descarta
          fallecimientos y cuidados paliativos · hasta 20 MB
        </p>
        <input
          ref={entrada}
          type="file"
          accept=".csv,.xlsx,.xls,text/csv"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) subir(f)
            e.target.value = ''
          }}
        />
      </div>

      {cargando && <p className="antetitulo" style={{ marginTop: 24 }}>Analizando el archivo</p>}
      {error && <p className="error-a">{error}</p>}

      {r && (
        <>
          <div className="resumen-a">
            <Dato v={entero(r.filas_archivo)} n="filas en el archivo" />
            <Dato v={entero(r.descartados)} n="descartadas por fallecimiento o paliativos" />
            <Dato v={entero(r.analizadas)} n="hospitalizaciones analizadas" />
            <Dato
              v={porcentaje(r.cobertura, 0)}
              n="de cobertura, pesada por importancia y no por número de columnas"
              aviso={r.cobertura < 0.6}
            />
          </div>

          {r.cobertura < 0.6 && (
            <p className="aviso-a">
              La cobertura es baja. El modelo está rellenando con valores típicos las columnas
              que faltan, así que la lista sirve para ordenar pero los porcentajes son menos
              fiables de lo normal. Faltan sobre todo: {r.faltan_importantes.slice(0, 4).join(', ')}.
            </p>
          )}

          <section className="bloque-a">
            <h2>¿A cuántos alcanza a llamar?</h2>
            <input
              className="deslizador"
              type="range"
              min={1}
              max={Math.min(r.analizadas, 1000)}
              value={capacidad}
              onChange={(e) => setCapacidad(Number(e.target.value))}
              aria-label="Cuántos pacientes puede llamar"
            />
            <div className="cifras-cap">
              <Dato v={entero(capacidad)} n="pacientes en la lista" />
              <Dato v={entero(alertados)} n="de ellos superan el umbral del programa" />
              <Dato
                v={lista.length ? porcentaje(lista[lista.length - 1].probabilidad) : '—'}
                n="riesgo del último de la lista"
              />
              <Dato
                v={lista.length ? porcentaje(lista[0].probabilidad) : '—'}
                n="riesgo del primero"
              />
            </div>
            <button
              type="button"
              className="pastilla pastilla-rellena pastilla-sm"
              style={{ marginTop: 22 }}
              onClick={descargar}
            >
              Descargar la lista en CSV
            </button>
          </section>

          <section className="bloque-a">
            <h2>Los primeros de la lista</h2>
            <p className="texto-a">
              Ordenados por riesgo. La columna de la izquierda es la fila del archivo que usted
              subió, para que pueda volver a su propio registro.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-a">
                <thead>
                  <tr>
                    <th className="n">#</th>
                    <th className="n">Fila del archivo</th>
                    <th className="n">Riesgo</th>
                    <th />
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {lista.slice(0, 25).map((f) => (
                    <tr key={f.puesto}>
                      <td className="n puesto">{f.puesto}</td>
                      <td className="n">{entero(f.fila_csv)}</td>
                      <td className="n">{porcentaje(f.probabilidad)}</td>
                      <td className="barra-a">
                        <i style={{ width: `${Math.min(f.probabilidad * 180, 100)}%` }} />
                      </td>
                      <td>
                        {f.alerta ? (
                          <span className="etiqueta">Sobre el umbral</span>
                        ) : (
                          <span className="apagado">Bajo el umbral</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {capacidad > 25 && (
              <p className="texto-a">
                Se muestran los 25 primeros. La descarga trae los {entero(capacidad)} completos.
              </p>
            )}
          </section>

          <section className="bloque-a">
            <h2>Qué entendió del archivo</h2>
            <div className="columnas-a">
              <div>
                <p className="antetitulo">Reconocidas</p>
                <div className="fichas-a">
                  {Object.entries(r.reconocidas)
                    .slice(0, 24)
                    .map(([esperada, encontrada]) => (
                      <span key={esperada} className="ficha-a">
                        {encontrada} → <strong>{esperada}</strong>
                      </span>
                    ))}
                </div>
              </div>
              {r.sin_reconocer.length > 0 && (
                <div>
                  <p className="antetitulo">No reconocidas, se ignoran</p>
                  <div className="fichas-a">
                    {r.sin_reconocer.map((c) => (
                      <span key={c} className="ficha-a apagada">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <p className="nota-a">
              {r.rellenadas} columnas se completaron con el valor típico de la cohorte porque el
              archivo no las traía. Eso siempre produce un número: por eso la cobertura de
              arriba importa más que el hecho de que la lista exista.
            </p>
          </section>
        </>
      )}

      <style>{`
        .zona {
          margin-top: 40px; border: 1px dashed var(--borde-suave);
          border-radius: var(--radius-tarjeta); padding: 46px; text-align: center;
          transition: border-color .2s ease, background .2s ease;
        }
        .zona.arrastrando { border-color: var(--filete-fuerte); background: var(--superficie); }
        .zona-texto { font-size: 15px; }
        .zona-nota { margin-top: 10px; font-size: 12px; color: var(--apagado); line-height: 1.6; }
        .enlace {
          background: none; border: 0; padding: 0; cursor: pointer; color: var(--tinta);
          font-family: var(--font-sans); font-size: 15px;
          text-decoration: underline; text-underline-offset: 3px;
        }
        .error-a { margin-top: 24px; font-size: 14.5px; line-height: 1.7; color: var(--color-dato-4); max-width: 72ch; }
        .aviso-a {
          margin-top: 20px; padding: 16px 20px; border-radius: var(--radius-entrada);
          border: 1px solid var(--color-dato-3); font-size: 13.5px; line-height: 1.7;
          color: var(--apagado); max-width: 76ch;
        }

        .resumen-a, .cifras-cap {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
          gap: 26px; margin-top: 32px;
        }
        .dato-a-v {
          font-family: var(--font-serif); font-weight: 300; font-size: 32px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .dato-a-v.aviso { color: var(--color-dato-4); }
        .dato-a-n { margin-top: 7px; font-size: 12px; line-height: 1.5; color: var(--apagado); }

        .bloque-a { padding-block: 38px; border-top: 1px solid var(--filete); margin-top: 20px; }
        .bloque-a h2 { font-size: 25px; }
        .texto-a { margin-top: 12px; font-size: 14.5px; line-height: 1.7; color: var(--apagado); max-width: 70ch; }
        .nota-a { margin-top: 22px; font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 76ch; }

        .deslizador { width: 100%; max-width: 560px; margin-top: 20px; accent-color: var(--tinta); }

        .tabla-envoltura { overflow-x: auto; margin-top: 22px; }
        .tabla-a { width: 100%; border-collapse: collapse; min-width: 560px; }
        .tabla-a th {
          text-align: left; font-size: 10.5px; font-weight: 500; letter-spacing: .12em;
          text-transform: uppercase; color: var(--apagado);
          padding: 0 14px 11px 0; border-bottom: 1px solid var(--filete);
        }
        .tabla-a th.n, .tabla-a td.n { text-align: right; padding-right: 14px; }
        .tabla-a td { padding: 11px 14px 11px 0; border-bottom: 1px solid var(--filete); font-size: 14px; }
        .tabla-a .puesto { font-family: var(--font-serif); color: var(--apagado); }
        .barra-a { width: 120px; }
        .barra-a i { display: block; height: 5px; border-radius: 999px; background: var(--color-dato-3); }
        .etiqueta {
          display: inline-block; border-radius: 999px; background: var(--superficie-2);
          font-size: 11px; padding: 3px 10px;
        }
        .apagado { font-size: 12.5px; color: var(--apagado); }

        .columnas-a { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 28px; margin-top: 22px; }
        .fichas-a { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
        .ficha-a {
          border-radius: 999px; background: var(--superficie); padding: 5px 12px;
          font-size: 11.5px; color: var(--tinta);
        }
        .ficha-a strong { font-weight: 600; }
        .ficha-a.apagada { background: transparent; border: 1px solid var(--filete); color: var(--apagado); }
      `}</style>
    </div>
  )
}

function Dato({ v, n, aviso = false }: { v: string; n: string; aviso?: boolean }) {
  return (
    <div>
      <div className={aviso ? 'dato-a-v aviso' : 'dato-a-v'}>{v}</div>
      <p className="dato-a-n">{n}</p>
    </div>
  )
}
