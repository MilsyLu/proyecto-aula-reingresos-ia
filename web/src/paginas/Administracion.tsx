import { Link } from 'react-router-dom'
import { Encabezado } from '../componentes/Encabezado'

/** Operaciones reservadas a coordinación, separadas del trabajo asistencial. */
export function Administracion() {
  const enlaces = [
    { ruta: '../archivo', nombre: 'Cargar un archivo', detalle: 'Analizar CSV o Excel y generar una lista priorizada.' },
    { ruta: '../umbral', nombre: 'Configurar alertas', detalle: 'Consultar y gestionar el umbral del programa.' },
    { ruta: '../reportes', nombre: 'Descargar reportes', detalle: 'Documentos Excel y PDF para coordinación.' },
  ]
  return <div>
    <Encabezado antetitulo="Coordinación" titulo="Gestión administrativa">
      <p>Herramientas de configuración y carga, disponibles solo para este perfil.</p>
    </Encabezado>
    <div className="rejilla-admin" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 16 }}>
      {enlaces.map(e => <Link key={e.ruta} className="tarjeta tarjeta-pad" to={e.ruta} style={{ textDecoration: 'none', color: 'var(--tinta)', display: 'grid', gap: 10 }}>
        <h2 className="tarjeta-titulo">{e.nombre}</h2><p>{e.detalle}</p>
        <span style={{ color: 'var(--acento-texto)', fontWeight: 800 }}>Abrir</span>
      </Link>)}
    </div>
  </div>
}
