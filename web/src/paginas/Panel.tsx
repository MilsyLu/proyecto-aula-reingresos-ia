import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { ErrorApi, api } from '../lib/api'
import { entero, porcentaje } from '../lib/formato'
import type { PacienteSeguido } from '../lib/tiposSeguimiento'
import { NOMBRE_ESTADO, fechaCorta } from '../lib/tiposSeguimiento'
import { Encabezado } from '../componentes/Encabezado'

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

export function Panel() {
  const [datos, setDatos] = useState<Datos | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    api.obtener<Datos>('/panel').then(setDatos)
      .catch(e => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar el resumen.'))
  }, [])

  return <div>
    <Encabezado antetitulo="Atención diaria" titulo="Inicio">
      <p>Resumen de pacientes registrados y contactos pendientes.</p>
    </Encabezado>
    {error && <p className="aviso-error" role="alert">{error}</p>}
    {!datos && !error && <p>Cargando información de seguimiento…</p>}
    {datos && <>
      <div className="tira" style={{ marginBottom: 18 }}>
        <div><p className="tira-etiqueta">Pacientes registrados</p>
          <p className="tira-cifra">{entero(datos.cifras.registrados)}</p></div>
        <div><p className="tira-etiqueta">Pendientes de contacto</p>
          <p className="tira-cifra">{entero(datos.cifras.pendientes)}</p></div>
        <div><p className="tira-etiqueta">Con alerta de riesgo</p>
          <p className="tira-cifra">{entero(datos.cifras.sobre_umbral)}</p></div>
        <div><p className="tira-etiqueta">Llamadas próximas (7 días)</p>
          <p className="tira-cifra">{entero(datos.cifras.proximos_siete_dias)}</p></div>
      </div>
      <section className="tarjeta">
        <div className="cabeza-tarjeta">
          <div>
            <h2 className="tarjeta-titulo">Pacientes para contactar primero</h2>
            <p className="tarjeta-sub">Registros pendientes o agendados, ordenados por riesgo.</p>
          </div>
          <Link to="../seguimiento" className="pastilla pastilla-contorno pastilla-sm">Ver pacientes</Link>
        </div>
        {datos.urgentes.length === 0
          ? <p className="vacio">No hay pacientes pendientes. Puede registrar uno desde Estimar riesgo.</p>
          : <div className="tabla-ancha"><table>
              <thead><tr><th>Paciente</th><th>Riesgo</th><th>Alta</th><th>Estado</th></tr></thead>
              <tbody>{datos.urgentes.map(p => <tr key={p.id}>
                <td><b className="celda-nombre">{p.nombre}</b>
                  <small className="celda-sub">{p.resumen}</small></td>
                <td><span className={p.alerta ? 'riesgo-alto' : 'riesgo-bajo'}>
                  {porcentaje(p.probabilidad)}</span></td>
                <td>{p.fecha_alta ? fechaCorta(p.fecha_alta) : '—'}</td>
                <td>{NOMBRE_ESTADO[p.estado]}</td>
              </tr>)}</tbody>
            </table></div>}
      </section>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, marginTop: 20 }}>
        <Link to="../estimar" className="pastilla pastilla-rellena">Estimar riesgo</Link>
        <Link to="../seguimiento" className="pastilla pastilla-contorno">Gestionar pacientes</Link>
        <Link to="../agenda" className="pastilla pastilla-contorno">Ver agenda</Link>
        {datos.puede_operar && <Link to="../administracion" className="pastilla pastilla-contorno">Administración</Link>}
      </div>
    </>}
  </div>
}
