import { useCallback, useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { ErrorApi, api } from '../lib/api'
import { entero, porcentaje } from '../lib/formato'

interface Paciente {
  puesto: number
  paciente: number
  probabilidad: number
  nivel: 'alto' | 'medio' | 'bajo'
  alerta: boolean
  reingreso_real: boolean
  resultado: string
  edad: number
  grupo_edad: string
  genero: string
  dias_estancia: number
  ingresos_previos: number
  medicamentos: number
  diagnosticos: number
  diagnostico_principal: string
  egreso: string
}

interface Pagina {
  pacientes: Paciente[]
  total: number
  pagina: number
  paginas: number
  umbral: number
}

interface Resumen {
  total: number
  umbral: number
  tramos: { nivel: string; pacientes: number; reingreso_real: number }[]
}

const NOMBRE_NIVEL: Record<string, string> = {
  alto: 'Alto',
  medio: 'Medio',
  bajo: 'Bajo',
}

/**
 * La cohorte de prueba ordenada por riesgo.
 *
 * No son pacientes inventados para que la tabla se vea llena: son las 19.870
 * hospitalizaciones que el modelo nunca vio mientras se entrenaba, con la
 * probabilidad que les dio y con el desenlace real al lado.
 *
 * Que esté el desenlace real es lo que hace útil esta pantalla y lo que la
 * distingue de una lista de trabajo: se puede abrir un paciente de 40 % y ver
 * si reingresó o no. Es el modelo mostrando dónde acierta y dónde falla.
 */
export function Pacientes() {
  const [datos, setDatos] = useState<Pagina | null>(null)
  const [resumen, setResumen] = useState<Resumen | null>(null)
  const [elegido, setElegido] = useState<Paciente | null>(null)
  const [nivel, setNivel] = useState('')
  const [desenlace, setDesenlace] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(1)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.obtener<Resumen>('/pacientes/resumen').then(setResumen).catch(() => {})
  }, [])

  const cargar = useCallback(async () => {
    try {
      const p = new URLSearchParams({ pagina: String(pagina) })
      if (nivel) p.set('nivel', nivel)
      if (desenlace) p.set('desenlace', desenlace)
      if (busqueda.trim()) p.set('q', busqueda.trim())
      const r = await api.obtener<Pagina>(`/pacientes?${p}`)
      setDatos(r)
      setError(null)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar la lista.')
    }
  }, [pagina, nivel, desenlace, busqueda])

  useEffect(() => {
    const t = setTimeout(cargar, busqueda ? 280 : 0)
    return () => clearTimeout(t)
  }, [cargar, busqueda])

  // Cambiar de filtro con la pagina 7 puesta deja una tabla vacia sin explicar
  // por que: se vuelve al principio.
  useEffect(() => {
    setPagina(1)
  }, [nivel, desenlace, busqueda])

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="Lista priorizada">
        <p>
          Las {entero(resumen?.total ?? 19870)} hospitalizaciones del conjunto de prueba,
          ordenadas por el riesgo que les dio el modelo. Al lado de cada una está lo que pasó
          de verdad, así que se ve dónde acierta y dónde falla.
        </p>
      </Encabezado>

      {resumen && (
        <div className="tira" style={{ marginBottom: 18 }}>
          {resumen.tramos.map((t) => (
            <div key={t.nivel}>
              <p className="tira-etiqueta">Riesgo {NOMBRE_NIVEL[t.nivel]?.toLowerCase()}</p>
              <p className="tira-cifra">{entero(t.pacientes)}</p>
              <p className="tira-pie">
                Reingresaron <b>{porcentaje(t.reingreso_real)}</b>
              </p>
            </div>
          ))}
          <div>
            <p className="tira-etiqueta">Umbral del programa</p>
            <p className="tira-cifra">{porcentaje(resumen.umbral)}</p>
            <p className="tira-pie">Por encima, entra en la lista</p>
          </div>
        </div>
      )}

      {error && <p className="aviso-error">{error}</p>}

      <div className="lista-columnas">
        <div className="tarjeta">
          <div className="barra-filtros">
            <input
              value={busqueda}
              placeholder="Buscar por número de paciente"
              onChange={(e) => setBusqueda(e.target.value)}
              aria-label="Buscar paciente"
            />
            <div className="fichas-filtro">
              {[['', 'Todos'], ['alto', 'Alto'], ['medio', 'Medio'], ['bajo', 'Bajo']].map(
                ([v, t]) => (
                  <button
                    key={v}
                    type="button"
                    className={nivel === v ? 'ficha elegida' : 'ficha'}
                    onClick={() => setNivel(v)}
                  >
                    {t}
                  </button>
                ),
              )}
              <span className="separador-ficha" aria-hidden="true" />
              {[['', 'Todos'], ['reingresaron', 'Reingresaron'], ['no-reingresaron', 'No']].map(
                ([v, t]) => (
                  <button
                    key={`d-${v}`}
                    type="button"
                    className={desenlace === v ? 'ficha elegida' : 'ficha'}
                    onClick={() => setDesenlace(v)}
                  >
                    {t}
                  </button>
                ),
              )}
            </div>
          </div>

          {datos && datos.pacientes.length === 0 ? (
            <p className="vacio">Ningún paciente coincide con esos filtros.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>Paciente</th>
                  <th>Riesgo</th>
                  <th>Perfil</th>
                  <th>¿Reingresó?</th>
                </tr>
              </thead>
              <tbody>
                {datos?.pacientes.map((p) => (
                  <tr
                    key={p.paciente}
                    className={elegido?.paciente === p.paciente ? 'clicable elegida' : 'clicable'}
                    onClick={() => setElegido(p)}
                  >
                    <td className="puesto">{entero(p.puesto)}</td>
                    <td>
                      <b className="celda-nombre">{p.paciente}</b>
                      <small className="celda-sub">
                        {p.edad} años · {p.genero}
                      </small>
                    </td>
                    <td>
                      <span className={p.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>
                        {porcentaje(p.probabilidad)}
                      </span>
                      <small className="celda-sub">{NOMBRE_NIVEL[p.nivel]}</small>
                    </td>
                    <td>
                      <span className="perfil-celda">{p.egreso}</span>
                      <small className="celda-sub">
                        {p.ingresos_previos === 0
                          ? 'Sin hospitalizaciones previas'
                          : `${p.ingresos_previos} previa${p.ingresos_previos > 1 ? 's' : ''}`}
                        {' · '}
                        {p.dias_estancia} días
                      </small>
                    </td>
                    <td>
                      <span className={p.reingreso_real ? 'etiqueta etiqueta-pendiente' : 'etiqueta etiqueta-cerrado'}>
                        {p.reingreso_real ? 'Sí' : 'No'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {datos && datos.paginas > 1 && (
            <div className="paginador">
              <button
                type="button"
                className="pastilla pastilla-contorno pastilla-sm"
                disabled={datos.pagina <= 1}
                onClick={() => setPagina((n) => n - 1)}
              >
                ← Anterior
              </button>
              <span>
                Página {entero(datos.pagina)} de {entero(datos.paginas)} ·{' '}
                {entero(datos.total)} pacientes
              </span>
              <button
                type="button"
                className="pastilla pastilla-contorno pastilla-sm"
                disabled={datos.pagina >= datos.paginas}
                onClick={() => setPagina((n) => n + 1)}
              >
                Siguiente →
              </button>
            </div>
          )}
        </div>

        <aside className="tarjeta tarjeta-pad ficha-paciente">
          {elegido ? (
            <>
              <p className="antetitulo">Paciente {elegido.paciente}</p>
              <div className="ficha-riesgo">
                <span className={elegido.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>
                  {porcentaje(elegido.probabilidad)}
                </span>
                <small>
                  Puesto {entero(elegido.puesto)} de {entero(resumen?.total ?? 0)}
                </small>
              </div>

              <p className="ficha-veredicto">{elegido.resultado}</p>

              <div className="ficha-datos">
                {[
                  ['Edad', `${elegido.edad} años`],
                  ['Género', elegido.genero],
                  ['Días de estancia', String(elegido.dias_estancia)],
                  ['Hospitalizaciones previas', String(elegido.ingresos_previos)],
                  ['Diagnósticos', String(elegido.diagnosticos)],
                  ['Medicamentos', String(elegido.medicamentos)],
                  ['Diagnóstico principal', elegido.diagnostico_principal],
                  ['Tipo de egreso', elegido.egreso],
                ].map(([k, v]) => (
                  <div key={k}>
                    <small>{k}</small>
                    <b>{v}</b>
                  </div>
                ))}
              </div>

              <p className="riesgo-nota">
                Los datos vienen anonimizados: el número es lo único que identifica la
                hospitalización, y es a propósito.
              </p>
            </>
          ) : (
            <p className="vacio">Pulse una fila para ver la ficha del paciente.</p>
          )}
        </aside>
      </div>
    </div>
  )
}
