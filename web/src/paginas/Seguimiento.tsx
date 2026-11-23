import { CalendarDays, List, Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { ErrorApi, api } from '../lib/api'
import { porcentaje } from '../lib/formato'
import {
  type Agenda, ESTADOS, type Estado, type ListaSeguimiento, NOMBRE_ESTADO,
  type PacienteSeguido, fechaCorta, moverSemana,
} from '../lib/tiposSeguimiento'

/**
 * Los pacientes registrados para seguimiento, en lista y en agenda.
 *
 * Son los únicos datos de esta aplicación que escribe una persona. Todo lo
 * demás sale de archivos que ya estaban; esto se crea desde la pantalla de
 * estimación y vive en la base de datos del servidor.
 *
 * Por eso la pantalla dice en voz alta que es un prototipo académico: guardar
 * datos de alguien, aunque sean de prueba, merece decirse.
 */
export function Seguimiento() {
  const [vista, setVista] = useState<'lista' | 'agenda'>('lista')
  const [lista, setLista] = useState<ListaSeguimiento | null>(null)
  const [agenda, setAgenda] = useState<Agenda | null>(null)
  const [lunes, setLunes] = useState('')
  const [filtro, setFiltro] = useState<Estado | ''>('')
  const [busqueda, setBusqueda] = useState('')
  const [error, setError] = useState<string | null>(null)

  const cargarLista = useCallback(async () => {
    try {
      const parametros = new URLSearchParams()
      if (filtro) parametros.set('estado', filtro)
      if (busqueda.trim()) parametros.set('q', busqueda.trim())
      setLista(await api.obtener<ListaSeguimiento>(`/seguimiento?${parametros}`))
      setError(null)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar el seguimiento.')
    }
  }, [filtro, busqueda])

  const cargarAgenda = useCallback(async (semana: string) => {
    try {
      const datos = await api.obtener<Agenda>(`/seguimiento/agenda?lunes=${semana}`)
      setAgenda(datos)
      setLunes(datos.lunes)
      setError(null)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar la agenda.')
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(cargarLista, busqueda ? 280 : 0)
    return () => clearTimeout(t)
  }, [cargarLista, busqueda])

  useEffect(() => {
    if (vista === 'agenda') cargarAgenda(lunes)
  }, [vista, cargarAgenda, lunes])

  async function cambiar(id: number, cambio: Record<string, string>) {
    try {
      await api.parchar(`/seguimiento/${id}`, cambio)
      await cargarLista()
      if (vista === 'agenda') await cargarAgenda(lunes)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo guardar el cambio.')
    }
  }

  async function quitar(p: PacienteSeguido) {
    if (!confirm(`¿Quitar a ${p.nombre} del seguimiento? No se puede deshacer.`)) return
    try {
      await api.borrar(`/seguimiento/${p.id}`)
      await cargarLista()
      if (vista === 'agenda') await cargarAgenda(lunes)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo quitar al paciente.')
    }
  }

  const cuentas = lista?.cuentas
  const hoy = new Date().toISOString().slice(0, 10)

  return (
    <div>
      <Encabezado
        antetitulo="Trabajar"
        titulo="Pacientes en seguimiento"
        acciones={
          <div className="conmutador">
            <button
              type="button"
              className={vista === 'lista' ? 'activo' : ''}
              onClick={() => setVista('lista')}
            >
              <List size={14} strokeWidth={1.7} aria-hidden="true" /> Lista
            </button>
            <button
              type="button"
              className={vista === 'agenda' ? 'activo' : ''}
              onClick={() => setVista('agenda')}
            >
              <CalendarDays size={14} strokeWidth={1.7} aria-hidden="true" /> Agenda
            </button>
          </div>
        }
      >
        <p>
          Los pacientes que usted registró desde la pantalla de estimación. El riesgo de cada
          uno lo calculó el modelo oficial en el momento de registrarlo.
        </p>
      </Encabezado>

      {cuentas && (
        <div className="tira" style={{ marginBottom: 18 }}>
          <div>
            <p className="tira-etiqueta">Registrados</p>
            <p className="tira-cifra">{lista?.total ?? 0}</p>
          </div>
          <div>
            <p className="tira-etiqueta">Por contactar</p>
            <p className="tira-cifra">{cuentas.pendiente}</p>
            <p className="tira-pie">Sin llamada ni fecha</p>
          </div>
          <div>
            <p className="tira-etiqueta">Agendados</p>
            <p className="tira-cifra">{cuentas.agendado}</p>
            <p className="tira-pie">Con fecha puesta</p>
          </div>
          <div>
            <p className="tira-etiqueta">Contactados</p>
            <p className="tira-cifra">{cuentas.contactado}</p>
            <p className="tira-pie">Ya se les llamó</p>
          </div>
        </div>
      )}

      {error && <p className="aviso-error">{error}</p>}

      {vista === 'lista' && (
        <div className="tarjeta">
          <div className="barra-filtros">
            <input
              value={busqueda}
              placeholder="Buscar por nombre o documento"
              onChange={(e) => setBusqueda(e.target.value)}
              aria-label="Buscar paciente"
            />
            <div className="fichas-filtro">
              <button
                type="button"
                className={filtro === '' ? 'ficha elegida' : 'ficha'}
                onClick={() => setFiltro('')}
              >
                Todos
              </button>
              {ESTADOS.map((e) => (
                <button
                  key={e}
                  type="button"
                  className={filtro === e ? 'ficha elegida' : 'ficha'}
                  onClick={() => setFiltro(e)}
                >
                  {NOMBRE_ESTADO[e]}
                </button>
              ))}
            </div>
          </div>

          {lista && lista.pacientes.length === 0 ? (
            <p className="vacio">
              {lista.total === 0
                ? 'Todavía no hay nadie en seguimiento. Estime un paciente y use «Registrar para seguimiento».'
                : 'Ningún paciente coincide con ese filtro.'}
            </p>
          ) : (
            <div className="tabla-ancha">
              <table>
                <thead>
                  <tr>
                    <th>Paciente</th>
                    <th>Riesgo</th>
                    <th>Alta</th>
                    <th>Estado</th>
                    <th>Agendar para</th>
                    <th>Notas</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {lista?.pacientes.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <b className="celda-nombre">{p.nombre}</b>
                        <small className="celda-sub">{p.resumen}</small>
                        {p.telefono && <small className="celda-sub">{p.telefono}</small>}
                      </td>
                      <td>
                        <span className={p.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>
                          {porcentaje(p.probabilidad)}
                        </span>
                        <small className="celda-sub">
                          {p.alerta ? 'Entra en la lista' : 'Bajo el umbral'}
                        </small>
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
                        <select
                          value={p.estado}
                          onChange={(e) => cambiar(p.id, { estado: e.target.value })}
                          aria-label={`Estado de ${p.nombre}`}
                        >
                          {ESTADOS.map((e) => (
                            <option key={e} value={e}>
                              {NOMBRE_ESTADO[e]}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <input
                          type="date"
                          value={p.fecha_agendada}
                          min={hoy}
                          onChange={(e) => cambiar(p.id, { fecha_agendada: e.target.value })}
                          aria-label={`Fecha de llamada de ${p.nombre}`}
                        />
                      </td>
                      <td>
                        <input
                          defaultValue={p.notas}
                          placeholder="Qué revisar"
                          onBlur={(e) => {
                            if (e.target.value !== p.notas) cambiar(p.id, { notas: e.target.value })
                          }}
                          aria-label={`Notas de ${p.nombre}`}
                        />
                      </td>
                      <td>
                        <button
                          type="button"
                          className="quitar"
                          onClick={() => quitar(p)}
                          aria-label={`Quitar a ${p.nombre}`}
                        >
                          <Trash2 size={14} strokeWidth={1.6} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {vista === 'agenda' && agenda && (
        <>
          <div className="semana-barra">
            <button
              type="button"
              className="pastilla pastilla-contorno pastilla-sm"
              onClick={() => setLunes(moverSemana(agenda.lunes, -1))}
            >
              ← Semana anterior
            </button>
            <b>
              Semana del {fechaCorta(agenda.lunes)} al{' '}
              {fechaCorta(agenda.dias[4]?.fecha ?? agenda.lunes)}
            </b>
            <button
              type="button"
              className="pastilla pastilla-contorno pastilla-sm"
              onClick={() => setLunes(moverSemana(agenda.lunes, 1))}
            >
              Semana siguiente →
            </button>
          </div>

          <div className="rejilla-semana">
            {agenda.dias.map((d) => (
              <div key={d.fecha} className={`dia tarjeta${d.fecha === agenda.hoy ? ' hoy' : ''}`}>
                <div className="dia-cabeza">
                  <span>{d.nombre}</span>
                  <b>{d.numero}</b>
                </div>
                {d.pacientes.length === 0 ? (
                  <p className="dia-vacio">Sin llamadas</p>
                ) : (
                  d.pacientes.map((p) => (
                    <div key={p.id} className={`cita${p.alerta ? ' caliente' : ''}`}>
                      <b>{p.nombre}</b>
                      <small>{porcentaje(p.probabilidad)} · {NOMBRE_ESTADO[p.estado]}</small>
                      {p.notas && <small className="cita-nota">{p.notas}</small>}
                    </div>
                  ))
                )}
              </div>
            ))}
          </div>

          {agenda.sin_agendar.length > 0 && (
            <div className="tarjeta tarjeta-pad" style={{ marginTop: 18 }}>
              <h3 className="tarjeta-titulo">
                Sin fecha todavía · {agenda.sin_agendar.length}
              </h3>
              <p className="tarjeta-sub">
                Están registrados y nadie les ha puesto día. Van de mayor a menor riesgo.
              </p>
              <div className="pendientes">
                {agenda.sin_agendar.map((p) => (
                  <div key={p.id} className="pendiente">
                    <span className={p.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>
                      {porcentaje(p.probabilidad)}
                    </span>
                    <b>{p.nombre}</b>
                    <input
                      type="date"
                      min={hoy}
                      onChange={(e) => cambiar(p.id, { fecha_agendada: e.target.value })}
                      aria-label={`Agendar a ${p.nombre}`}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      <p className="aviso-prototipo">
        Prototipo académico. Lo que registre aquí se guarda en el servidor del proyecto y se
        usa solo para demostrar cómo funcionaría el seguimiento.
      </p>
    </div>
  )
}
