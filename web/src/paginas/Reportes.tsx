import { FileSpreadsheet, FileText } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { ErrorApi, api, descargar } from '../lib/api'
import { entero, numero, porcentaje, veces } from '../lib/formato'

interface Fila {
  variable: string
  nivel: string | null
  alto: number
  resto: number
  veces: number | null
  n_alto: number
  n_resto: number
}

interface Catalogo {
  reportes: { tipo: string; titulo: string; descripcion: string; filas: number }[]
  perfil: {
    resumen: {
      n_total: number
      n_alto: number
      n_resto: number
      porcentaje_alto: number
      reingreso_alto: number
      reingreso_resto: number
      veces_mas_reingreso: number
    }
    promedios: Fila[]
    proporciones: Fila[]
  } | null
}

/**
 * Los reportes que se descargan, y el perfil del alto riesgo a la vista.
 *
 * El perfil se muestra en pantalla y no solo dentro del PDF a propósito: un
 * hallazgo que vive únicamente dentro de un archivo descargado no lo lee
 * nadie, y este es el hallazgo más interesante que tiene el proyecto después
 * del techo de los datos.
 */
export function Reportes() {
  const [datos, setDatos] = useState<Catalogo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [bajando, setBajando] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Catalogo>('/reportes')
      .then(setDatos)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  async function bajar(tipo: string, formato: 'xlsx' | 'pdf') {
    const clave = `${tipo}.${formato}`
    setBajando(clave)
    setError(null)
    try {
      await descargar(`/reportes/${tipo}.${formato}`)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo generar el archivo.')
    } finally {
      setBajando(null)
    }
  }

  const p = datos?.perfil

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="Reportes">
        <p>
          El Excel lleva los datos completos, para trabajar encima. El PDF lleva el informe
          redactado, para imprimir o adjuntar. No son el mismo archivo en dos formatos.
        </p>
      </Encabezado>

      {error && <p className="aviso-error">{error}</p>}

      <div className="rejilla-reportes escalonado">
        {datos?.reportes.map((r) => (
          <div key={r.tipo} className="tarjeta tarjeta-pad reporte">
            <h3 className="tarjeta-titulo">{r.titulo}</h3>
            <p className="tarjeta-sub">{r.descripcion}</p>
            <p className="reporte-filas">
              {r.filas === 0 ? 'Todavía sin datos' : `${entero(r.filas)} filas`}
            </p>
            <div className="reporte-botones">
              <button
                type="button"
                className="pastilla pastilla-contorno pastilla-sm"
                onClick={() => bajar(r.tipo, 'xlsx')}
                disabled={bajando !== null}
              >
                <FileSpreadsheet size={14} strokeWidth={1.6} aria-hidden="true" />
                {bajando === `${r.tipo}.xlsx` ? 'Generando' : 'Excel'}
              </button>
              <button
                type="button"
                className="pastilla pastilla-contorno pastilla-sm"
                onClick={() => bajar(r.tipo, 'pdf')}
                disabled={bajando !== null}
              >
                <FileText size={14} strokeWidth={1.6} aria-hidden="true" />
                {bajando === `${r.tipo}.pdf` ? 'Generando' : 'PDF'}
              </button>
            </div>
            {r.tipo === 'cohorte' && (
              <p className="reporte-nota">
                El Excel tarda unos segundos: son {entero(r.filas)} filas.
              </p>
            )}
          </div>
        ))}
      </div>

      {p && (
        <section className="perfil">
          <Encabezado
            antetitulo="Análisis"
            titulo="Qué tienen en común los de alto riesgo"
          >
            <p>
              Se parte la cohorte de prueba en dos —los que superan el umbral y los demás— y se
              compara variable por variable. No hay otro modelo encima: es aritmética sobre las{' '}
              {entero(p.resumen.n_total)} hospitalizaciones publicadas, y cualquiera puede
              repetirla.
            </p>
          </Encabezado>

          <div className="tira" style={{ marginBottom: 18 }}>
            <div>
              <p className="tira-etiqueta">Marcados de alto riesgo</p>
              <p className="tira-cifra">{entero(p.resumen.n_alto)}</p>
              <p className="tira-pie">{porcentaje(p.resumen.porcentaje_alto)} de la cohorte</p>
            </div>
            <div>
              <p className="tira-etiqueta">Reingresan (alto riesgo)</p>
              <p className="tira-cifra">{porcentaje(p.resumen.reingreso_alto)}</p>
              <p className="tira-pie">Observado, no estimado</p>
            </div>
            <div>
              <p className="tira-etiqueta">Reingresan (los demás)</p>
              <p className="tira-cifra">{porcentaje(p.resumen.reingreso_resto)}</p>
              <p className="tira-pie">Observado, no estimado</p>
            </div>
            <div>
              <p className="tira-etiqueta">Cuántas veces más</p>
              <p className="tira-cifra">{veces(p.resumen.veces_mas_reingreso)}</p>
              <p className="tira-pie">
                <b>El control</b> de todo lo demás
              </p>
            </div>
          </div>

          <p className="perfil-control">
            Antes de mirar los rasgos, lo primero: los que el modelo marca reingresan{' '}
            {veces(p.resumen.veces_mas_reingreso)} más que el resto. Si esa cifra no fuera mayor
            que uno, nada de lo que sigue valdría.
          </p>

          <div className="perfil-columnas">
            <div className="tarjeta">
              <div className="tarjeta-pad" style={{ paddingBottom: 12 }}>
                <h3 className="tarjeta-titulo">En promedio</h3>
                <p className="tarjeta-sub">
                  Cuánto vale cada variable en un grupo y en el otro.
                </p>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Variable</th>
                    <th>Alto riesgo</th>
                    <th>Los demás</th>
                    <th>Veces</th>
                  </tr>
                </thead>
                <tbody>
                  {p.promedios.map((f) => (
                    <tr key={f.variable}>
                      <td>{f.variable}</td>
                      <td className="cifra">{numero(f.alto, 2)}</td>
                      <td className="cifra apagado">{numero(f.resto, 2)}</td>
                      <td>
                        <Barra veces={f.veces} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="tarjeta">
              <div className="tarjeta-pad" style={{ paddingBottom: 12 }}>
                <h3 className="tarjeta-titulo">Y dónde se concentran</h3>
                <p className="tarjeta-sub">
                  Qué proporción de cada grupo cae en cada categoría.
                </p>
              </div>
              <div className="tabla-alta">
                <table>
                  <thead>
                    <tr>
                      <th>Categoría</th>
                      <th>Alto riesgo</th>
                      <th>Los demás</th>
                      <th>Veces</th>
                    </tr>
                  </thead>
                  <tbody>
                    {p.proporciones.map((f) => (
                      <tr key={`${f.variable}-${f.nivel}`}>
                        <td>
                          <b className="celda-nombre">{f.nivel}</b>
                          <small className="celda-sub">{f.variable}</small>
                        </td>
                        <td className="cifra">{porcentaje(f.alto)}</td>
                        <td className="cifra apagado">{porcentaje(f.resto)}</td>
                        <td>
                          <Barra veces={f.veces} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>
      )}

      <p className="aviso-prototipo">
        Calculado con src/perfil_alto_riesgo.py sobre reports/predicciones_prueba.csv. Es
        reproducible: corra el script y debe dar exactamente estas cifras.
      </p>
    </div>
  )
}

/** La columna de «veces»: el número y una barra que lo hace comparable de un vistazo. */
function Barra({ veces: v }: { veces: number | null }) {
  if (v === null) return <span className="apagado">—</span>
  // Escala logaritmica: hay rasgos de 1,1x y otros de 23x, y en escala lineal
  // el de 23 aplasta a todos los demas hasta dejarlos invisibles.
  const ancho = Math.min(Math.log10(Math.max(v, 1)) / Math.log10(25), 1) * 100
  return (
    <div className="veces">
      <b>{numero(v, 2)}×</b>
      <i>
        <span style={{ width: `${ancho}%` }} />
      </i>
    </div>
  )
}
