import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Encabezado } from '../componentes/Encabezado'
import { ErrorApi, api } from '../lib/api'
import { porcentaje } from '../lib/formato'
import { type Agenda, ESTADOS, type Estado, type ListaSeguimiento,
  NOMBRE_ESTADO, type PacienteSeguido, fechaCorta, moverSemana } from '../lib/tiposSeguimiento'

interface Contacto {
  id: number
  creado: string
  registrado_por: string
  resultado: 'contactado' | 'sin_respuesta' | 'reprogramar'
  observaciones: string
  fecha_proxima: string
}
const RESULTADOS = {
  contactado: 'Contacto realizado',
  sin_respuesta: 'No respondió',
  reprogramar: 'Reprogramado',
} as const

/** Área asistencial: pacientes, fichas y agenda, sin métricas de entrenamiento. */
export function Seguimiento({
  vistaInicial = 'lista',
  soloVista = true,
}: {
  vistaInicial?: 'lista' | 'agenda'
  soloVista?: boolean
}) {
  const [vista, setVista] = useState<'lista' | 'agenda'>(vistaInicial)
  const [lista, setLista] = useState<ListaSeguimiento | null>(null)
  const [agenda, setAgenda] = useState<Agenda | null>(null)
  const [lunes, setLunes] = useState('')
  const [filtro, setFiltro] = useState<Estado | ''>('')
  const [busqueda, setBusqueda] = useState('')
  const [seleccionado, setSeleccionado] = useState<number | null>(null)
  const [contactos, setContactos] = useState<Contacto[]>([])
  const [resultadoContacto, setResultadoContacto] = useState<keyof typeof RESULTADOS>('contactado')
  const [observaciones, setObservaciones] = useState('')
  const [proximaFecha, setProximaFecha] = useState('')
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cargarLista = useCallback(async () => {
    try {
      const p = new URLSearchParams()
      if (filtro) p.set('estado', filtro)
      if (busqueda.trim()) p.set('q', busqueda.trim())
      setLista(await api.obtener<ListaSeguimiento>(`/seguimiento?${p}`))
      setError(null)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar la lista.')
    }
  }, [filtro, busqueda])

  const cargarAgenda = useCallback(async (semana: string) => {
    try {
      const d = await api.obtener<Agenda>(`/seguimiento/agenda?lunes=${semana}`)
      setAgenda(d)
      setLunes(d.lunes)
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
  }, [vista, lunes, cargarAgenda])

  const paciente = lista?.pacientes.find(p => p.id === seleccionado)
  useEffect(() => {
    if (seleccionado === null) return
    let vigente = true
    api.obtener<{ contactos: Contacto[] }>(`/seguimiento/${seleccionado}/contactos`)
      .then(r => { if (vigente) setContactos(r.contactos) })
      .catch(() => { if (vigente) setContactos([]) })
    return () => { vigente = false }
  }, [seleccionado])

  async function cambiar(id: number, cambio: Record<string, string>) {
    try {
      await api.parchar(`/seguimiento/${id}`, cambio)
      await cargarLista()
      if (vista === 'agenda') await cargarAgenda(lunes)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo guardar el cambio.')
    }
  }

  async function registrarContacto(evento: React.FormEvent) {
    evento.preventDefault()
    if (seleccionado === null || guardando) return
    setGuardando(true)
    try {
      await api.enviar(`/seguimiento/${seleccionado}/contactos`, {
        resultado: resultadoContacto,
        observaciones, fecha_proxima: proximaFecha,
      })
      const r = await api.obtener<{ contactos: Contacto[] }>(
        `/seguimiento/${seleccionado}/contactos`
      )
      setContactos(r.contactos)
      setObservaciones('')
      setProximaFecha('')
      setError(null)
      await cargarLista()
      if (vista === 'agenda') await cargarAgenda(lunes)
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo registrar el contacto.')
    } finally {
      setGuardando(false)
    }
  }

  async function quitar(p: PacienteSeguido) {
    if (!confirm(`¿Eliminar a ${p.nombre} y su historial de seguimiento? Esta acción no se puede deshacer.`)) return
    try {
      await api.borrar(`/seguimiento/${p.id}`)
      setSeleccionado(null)
      setContactos([])
      await cargarLista()
    } catch (e) {
      setError(e instanceof ErrorApi ? e.message : 'No se pudo eliminar.')
    }
  }

  const hoy = new Date().toISOString().slice(0, 10)
  const mostrarLista = !soloVista || vistaInicial === 'lista'
  const mostrarAgenda = !soloVista || vistaInicial === 'agenda'

  return <div>
    <Encabezado antetitulo="Atención diaria"
      titulo={vistaInicial === 'agenda' ? 'Agenda de llamadas' : 'Pacientes'}>
      <p>{vistaInicial === 'agenda'
        ? 'Organice sus contactos y consulte los pacientes que aún no tienen fecha.'
        : 'Consulte pacientes registrados, ordenados por riesgo, y documente cada contacto.'}</p>
    </Encabezado>

    {!soloVista && <div className="conmutador" style={{ marginBottom: 16 }}>
      <button className={vista === 'lista' ? 'activo' : ''} onClick={() => setVista('lista')}>Pacientes</button>
      <button className={vista === 'agenda' ? 'activo' : ''} onClick={() => setVista('agenda')}>Agenda</button>
    </div>}

    {error && <p className="aviso-error" role="alert">{error}</p>}

    {mostrarLista && (soloVista ? vistaInicial === 'lista' : vista === 'lista') && <>
      <div className="tira" style={{ marginBottom: 16 }}>
        <div><p className="tira-etiqueta">Registrados</p><p className="tira-cifra">{lista?.total ?? '—'}</p></div>
        <div><p className="tira-etiqueta">Pendientes</p><p className="tira-cifra">{lista?.cuentas.pendiente ?? '—'}</p></div>
        <div><p className="tira-etiqueta">Agendados</p><p className="tira-cifra">{lista?.cuentas.agendado ?? '—'}</p></div>
        <div><p className="tira-etiqueta">Contactados</p><p className="tira-cifra">{lista?.cuentas.contactado ?? '—'}</p></div>
      </div>
      <div className="seguimiento-con-ficha" style={{ display: 'grid',
        gridTemplateColumns: 'minmax(0, 1.5fr) minmax(310px, .9fr)', gap: 16, alignItems: 'start' }}>
        <section className="tarjeta">
          <div className="cabeza-tarjeta"><div>
            <h2 className="tarjeta-titulo">Lista priorizada de seguimiento</h2>
            <p className="tarjeta-sub">Pacientes registrados, no la cohorte histórica de prueba.</p>
          </div></div>
          <div className="barra-filtros">
            <input value={busqueda} placeholder="Buscar nombre o documento"
              aria-label="Buscar paciente" onChange={e => setBusqueda(e.target.value)} />
            <select aria-label="Filtrar por estado" value={filtro}
              onChange={e => setFiltro(e.target.value as Estado | '')}>
              <option value="">Todos los estados</option>
              {ESTADOS.map(e => <option key={e} value={e}>{NOMBRE_ESTADO[e]}</option>)}
            </select>
          </div>
          {lista?.pacientes.length === 0
            ? <p className="vacio">No hay pacientes con ese filtro. <Link to="../estimar">Estimar un paciente</Link></p>
            : <div className="tabla-ancha"><table>
              <thead><tr><th>Paciente</th><th>Riesgo</th><th>Alta</th><th>Estado</th><th>Detalle</th></tr></thead>
              <tbody>{lista?.pacientes.map(p => <tr key={p.id} className={p.id === seleccionado ? 'elegida' : ''}>
                <td><b className="celda-nombre">{p.nombre}</b>
                  <small className="celda-sub">{p.resumen}</small></td>
                <td><b className={p.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>{porcentaje(p.probabilidad)}</b></td>
                <td>{p.fecha_alta ? fechaCorta(p.fecha_alta) : '—'}</td>
                <td>{NOMBRE_ESTADO[p.estado]}</td>
                <td><button className="pastilla pastilla-contorno pastilla-sm"
                  aria-label={`Ver ficha de ${p.nombre}`} type="button"
                  onClick={() => setSeleccionado(p.id)}>Ver ficha</button></td>
              </tr>)}</tbody>
            </table></div>}
        </section>
        <aside className="tarjeta tarjeta-pad">
          {!paciente ? <div><h2 className="tarjeta-titulo">Ficha de paciente</h2>
            <p className="tarjeta-sub" style={{ marginTop: 12 }}>
              Seleccione un paciente de la lista para consultar su seguimiento.
            </p></div> : <>
            <h2 className="tarjeta-titulo">{paciente.nombre}</h2>
            <p className="tarjeta-sub">{paciente.resumen}</p>
            <p style={{ marginTop: 14 }}><b>Riesgo estimado:</b> {porcentaje(paciente.probabilidad)}</p>
            <p><b>Teléfono:</b> {paciente.telefono || 'No registrado'}</p>
            <p><b>Documento:</b> {paciente.documento || 'No registrado'}</p>
            <p><b>Fecha de alta:</b> {paciente.fecha_alta ? fechaCorta(paciente.fecha_alta) : 'No registrada'}</p>
            <div style={{ display: 'grid', gap: 8, marginTop: 16 }}>
              <div>
                <b>Estado:</b> {NOMBRE_ESTADO[paciente.estado]}
                <p className="tarjeta-sub">El estado de contacto se actualiza al guardar una llamada.</p>
                <button type="button" className="pastilla pastilla-contorno pastilla-sm"
                  style={{ marginTop: 8 }}
                  onClick={() => cambiar(paciente.id, {
                    estado: paciente.estado === 'cerrado' ? 'pendiente' : 'cerrado',
                  })}>
                  {paciente.estado === 'cerrado' ? 'Reabrir seguimiento' : 'Cerrar seguimiento'}
                </button>
              </div>
              <label className="campo-registro"><span>Próxima llamada</span>
                <input type="date" key={`fecha-${paciente.id}-${paciente.fecha_agendada}`}
                  defaultValue={paciente.fecha_agendada} min={hoy}
                  onBlur={e => { if (e.target.value !== paciente.fecha_agendada)
                    cambiar(paciente.id, { fecha_agendada: e.target.value }) }} />
              </label>
              <label className="campo-registro"><span>Observaciones generales</span>
                <textarea rows={3} key={`notas-${paciente.id}-${paciente.notas}`}
                  defaultValue={paciente.notas} placeholder="Observaciones actuales"
                  onBlur={e => { if (e.target.value !== paciente.notas)
                    cambiar(paciente.id, { notas: e.target.value }) }} />
              </label>
            </div>
            <form onSubmit={registrarContacto} style={{ marginTop: 20, display: 'grid', gap: 10 }}>
              <h3 className="tarjeta-titulo">Registrar contacto</h3>
              <label className="campo-registro"><span>Resultado de la llamada</span>
                <select value={resultadoContacto} onChange={e => setResultadoContacto(e.target.value as keyof typeof RESULTADOS)}>
                  {Object.entries(RESULTADOS).map(([clave, etiqueta]) =>
                    <option key={clave} value={clave}>{etiqueta}</option>)}
                </select>
              </label>
              <label className="campo-registro"><span>Observaciones del contacto</span>
                <textarea rows={3} value={observaciones} onChange={e => setObservaciones(e.target.value)}
                  placeholder="Qué ocurrió durante el contacto" maxLength={2000} />
              </label>
              <label className="campo-registro"><span>Próxima llamada (opcional, salvo reprogramar)</span>
                <input type="date" min={hoy} value={proximaFecha} onChange={e => setProximaFecha(e.target.value)} />
              </label>
              <button type="submit" disabled={guardando} className="pastilla pastilla-rellena pastilla-sm">
                {guardando ? 'Guardando…' : 'Guardar contacto'}
              </button>
            </form>
            <details style={{ marginTop: 18 }}>
              <summary style={{ cursor: 'pointer', fontWeight: 800 }}>Historial de contactos ({contactos.length})</summary>
              <div style={{ display: 'grid', gap: 10, marginTop: 12 }}>
                {contactos.length === 0 && <p className="tarjeta-sub">Aún no se han registrado llamadas.</p>}
                {contactos.map(c => <div key={c.id} style={{
                  padding: 10, border: '1px solid var(--filete)', borderRadius: 9,
                }}>
                  <b>{RESULTADOS[c.resultado]}</b>
                  <small className="celda-sub">{c.creado.replace('T', ' ')} · {c.registrado_por}</small>
                  {c.observaciones && <p>{c.observaciones}</p>}
                  {c.fecha_proxima && <small className="celda-sub">Próximo contacto: {fechaCorta(c.fecha_proxima)}</small>}
                </div>)}
              </div>
            </details>
            <button className="pastilla pastilla-contorno pastilla-sm" type="button"
              style={{ marginTop: 16 }} onClick={() => quitar(paciente)}>
              Eliminar registro
            </button>
          </>}
        </aside>
      </div>
    </>}

    {mostrarAgenda && (soloVista ? vistaInicial === 'agenda' : vista === 'agenda') && <div>
      <div className="semana-barra">
        <button type="button" className="pastilla pastilla-contorno pastilla-sm"
          onClick={() => setLunes(moverSemana(agenda?.lunes || lunes || hoy, -1))}>Semana anterior</button>
        <b>{agenda ? `Semana del ${fechaCorta(agenda.lunes)}` : 'Cargando agenda'}</b>
        <button type="button" className="pastilla pastilla-contorno pastilla-sm"
          onClick={() => setLunes(moverSemana(agenda?.lunes || lunes || hoy, 1))}>Semana siguiente</button>
      </div>
      {agenda && <>
        <div className="rejilla-semana">
          {agenda.dias.map(d => <div key={d.fecha} className={`dia tarjeta${d.fecha === agenda.hoy ? ' hoy' : ''}`}>
            <div className="dia-cabeza"><span>{d.nombre}</span><b>{d.numero}</b></div>
            {d.pacientes.length === 0 ? <p className="dia-vacio">Sin llamadas</p>
              : d.pacientes.map(p => <div key={p.id} className={`cita${p.alerta ? ' caliente' : ''}`}>
                <b>{p.nombre}</b>
                <small>{porcentaje(p.probabilidad)} · {NOMBRE_ESTADO[p.estado]}</small>
              </div>)}
          </div>)}
        </div>
        <div className="tarjeta tarjeta-pad" style={{ marginTop: 16 }}>
          <h2 className="tarjeta-titulo">Pendientes sin fecha</h2>
          {agenda.sin_agendar.length === 0 ? <p className="tarjeta-sub">No hay pendientes sin agendar.</p> :
            <div className="pendientes">{agenda.sin_agendar.map(p =>
              <div className="pendiente" key={p.id}>
                <b>{p.nombre}</b><span>{porcentaje(p.probabilidad)}</span>
                <input type="date" min={hoy} aria-label={`Agendar a ${p.nombre}`}
                  onChange={e => cambiar(p.id, { fecha_agendada: e.target.value })} />
              </div>)}</div>}
        </div>
      </>}
    </div>}
    <p className="aviso-prototipo" style={{ marginTop: 20 }}>
      Prototipo académico. Registre únicamente información ficticia o anonimizada.
    </p>
    <style>{`
      @media (max-width: 1050px) {
        .seguimiento-con-ficha { grid-template-columns: minmax(0, 1fr) !important; }
      }
      .seguimiento-con-ficha .campo-registro input,
      .seguimiento-con-ficha .campo-registro select,
      .seguimiento-con-ficha .campo-registro textarea {
        width: 100%; min-height: 42px; padding: 10px 12px; border: 1px solid var(--filete);
        border-radius: var(--radio-sm); color: var(--tinta); background: var(--superficie); font-size: 15px;
      }
    `}</style>
  </div>
}
