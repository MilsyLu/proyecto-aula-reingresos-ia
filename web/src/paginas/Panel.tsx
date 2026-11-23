import { Calculator, ClipboardList, FileSpreadsheet, Upload, Users } from 'lucide-react'
import { Suspense, lazy, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorApi, api } from '../lib/api'
import { entero, porcentaje } from '../lib/formato'
import type { PacienteSeguido } from '../lib/tiposSeguimiento'
import { NOMBRE_ESTADO, fechaCorta } from '../lib/tiposSeguimiento'

// three.js pesa medio mega: se carga solo cuando esta pantalla se abre, y
// nunca si el navegador no aguanta WebGL.
const OrbeParticulas = lazy(() =>
  import('../orbe/OrbeParticulas').then((m) => ({ default: m.OrbeParticulas })),
)

interface Datos {
  nombre: string
  rol: string
  puede_operar: boolean
  cifras: {
    registrados: number
    pendientes: number
    agendados: number
    contactados: number
    sobre_umbral: number
    proximos_siete_dias: number
    tasa_base: number
    umbral: number
  }
  urgentes: PacienteSeguido[]
}

/** «Buenos días» cambia según la hora: a las once de la noche suena raro. */
function saludo(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Buenos días'
  if (h < 19) return 'Buenas tardes'
  return 'Buenas noches'
}

/**
 * El panel de inicio: lo que hay que saber antes de hacer nada.
 *
 * Arriba va la única imagen de la aplicación, con el orbe de la portada
 * flotando al lado. Es el mismo orbe y son los mismos pacientes: conecta el
 * adentro con el afuera en vez de que parezcan dos productos distintos.
 *
 * Debajo, cifras y trabajo pendiente. Ninguna inventada: el seguimiento sale
 * de la base de datos y lo demás de los archivos del proyecto.
 */
export function Panel() {
  const [d, setDatos] = useState<Datos | null>(null)
  const [orbeFallo, setOrbeFallo] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Datos>('/panel')
      .then(setDatos)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar el panel.'))
  }, [])

  const atajos = [
    { a: 'estimar', Icono: Calculator, t: 'Estimar un paciente', s: 'El formulario y el riesgo' },
    { a: 'seguimiento', Icono: ClipboardList, t: 'Seguimiento', s: 'A quién hay que llamar' },
    { a: 'pacientes', Icono: Users, t: 'Lista priorizada', s: 'La cohorte por riesgo' },
    { a: 'reportes', Icono: FileSpreadsheet, t: 'Reportes', s: 'Excel y PDF' },
    ...(d?.puede_operar
      ? [{ a: 'archivo', Icono: Upload, t: 'Subir un archivo', s: 'La lista de llamadas del día' }]
      : []),
  ]

  return (
    <div>
      <section className={`portico${orbeFallo ? ' sin-orbe' : ''}`}>
        <div className="portico-texto">
          <p className="antetitulo" style={{ color: 'rgb(255 255 255 / .62)' }}>
            {saludo()}
          </p>
          <h1>{d?.nombre ?? 'ReingresaIA'}</h1>
          <p className="portico-bajada">
            Esta herramienta ordena a qué paciente conviene llamar primero después del alta.
            No decide altas ni tratamientos: solo dice por dónde empezar cuando no alcanza el
            tiempo para llamar a todos.
          </p>
          <Link to="estimar" className="pastilla pastilla-rellena pastilla-sm portico-boton">
            Estimar un paciente
          </Link>
        </div>

        {!orbeFallo && (
          <div className="portico-orbe" aria-hidden="true">
            <Suspense fallback={null}>
              <OrbeParticulas forma="cohorte" onFallo={() => setOrbeFallo(true)} />
            </Suspense>
          </div>
        )}
      </section>

      {error && <p className="aviso-error">{error}</p>}

      {d && (
        <>
          <div className="tira" style={{ marginBottom: 16 }}>
            <div>
              <p className="tira-etiqueta">En seguimiento</p>
              <p className="tira-cifra">{entero(d.cifras.registrados)}</p>
              <p className="tira-pie">
                {d.cifras.sobre_umbral > 0 ? (
                  <>
                    <b>{entero(d.cifras.sobre_umbral)}</b> sobre el umbral
                  </>
                ) : (
                  'Pacientes registrados'
                )}
              </p>
            </div>
            <div>
              <p className="tira-etiqueta">Por contactar</p>
              <p className="tira-cifra">{entero(d.cifras.pendientes)}</p>
              <p className="tira-pie">Sin llamada ni fecha</p>
            </div>
            <div>
              <p className="tira-etiqueta">Llamadas esta semana</p>
              <p className="tira-cifra">{entero(d.cifras.proximos_siete_dias)}</p>
              <p className="tira-pie">En los próximos siete días</p>
            </div>
            <div>
              <p className="tira-etiqueta">Umbral vigente</p>
              <p className="tira-cifra">{porcentaje(d.cifras.umbral)}</p>
              <p className="tira-pie">
                Tasa base de la cohorte: {porcentaje(d.cifras.tasa_base)}
              </p>
            </div>
          </div>

          <div className="panel-columnas">
            <div className="tarjeta">
              <div className="tarjeta-pad" style={{ paddingBottom: 12 }}>
                <h3 className="tarjeta-titulo">A quién llamar primero</h3>
                <p className="tarjeta-sub">
                  De los registrados, los de mayor riesgo que todavía no se han contactado.
                </p>
              </div>

              {d.urgentes.length === 0 ? (
                <p className="vacio">
                  No hay nadie esperando llamada. Estime un paciente y use «Registrar para
                  seguimiento» para que aparezca aquí.
                </p>
              ) : (
                <table>
                  <thead>
                    <tr>
                      <th>Paciente</th>
                      <th>Riesgo</th>
                      <th>Alta</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.urgentes.map((p) => (
                      <tr key={p.id}>
                        <td>
                          <b className="celda-nombre">{p.nombre}</b>
                          <small className="celda-sub">{p.resumen}</small>
                        </td>
                        <td>
                          <span className={p.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>
                            {porcentaje(p.probabilidad)}
                          </span>
                        </td>
                        <td>
                          {p.fecha_alta ? fechaCorta(p.fecha_alta) : '—'}
                          {p.dias_desde_alta !== null && (
                            <small className="celda-sub">
                              {p.dias_desde_alta <= 30
                                ? `Hace ${p.dias_desde_alta} días`
                                : 'Fuera de los 30 días'}
                            </small>
                          )}
                        </td>
                        <td>
                          <span className={`etiqueta etiqueta-${p.estado}`}>
                            {NOMBRE_ESTADO[p.estado]}
                            {p.fecha_agendada && ` · ${fechaCorta(p.fecha_agendada)}`}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              <div className="panel-pie">
                <Link to="seguimiento" className="pastilla pastilla-contorno pastilla-sm">
                  Ver todo el seguimiento
                </Link>
              </div>
            </div>

            <div className="atajos">
              {atajos.map(({ a, Icono, t, s }) => (
                <Link key={a} to={a} className="atajo tarjeta">
                  <span className="atajo-icono">
                    <Icono size={17} strokeWidth={1.6} aria-hidden="true" />
                  </span>
                  <span>
                    <b>{t}</b>
                    <small>{s}</small>
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
