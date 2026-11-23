import { LogOut, Menu, PanelLeft, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useSesion } from '../lib/sesion'
import { GRUPOS, PANTALLAS, pantallasDe } from '../rutas'
import { Buscador } from './Buscador'
import { InterruptorTema } from './InterruptorTema'

const MEMORIA_BARRA = 'reingresaia-barra-colapsada'

/** Las iniciales para el avatar: «María Cárdenas» queda en «MC». */
function iniciales(nombre: string): string {
  return nombre
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? '')
    .join('')
}

/**
 * El armazón de la aplicación: menú lateral fijo, cinta superior y el contenido.
 *
 * El menú se dibuja a partir del registro de pantallas filtrado por los permisos
 * que devolvió el servidor, así que un grupo entero desaparece si el rol no
 * tiene nada dentro. Nunca aparece un enlace que al pulsarlo rebote.
 *
 * El contenido ya no está limitado a 1.200 px: ocupa el ancho que haya. En un
 * monitor ancho, dos franjas vacías a los lados no son respiración, son espacio
 * desperdiciado, y era la primera queja de Michel sobre esta pantalla.
 */
export function Armazon() {
  const { sesion, salir } = useSesion()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const permisos = sesion?.permisos ?? []

  const [colapsada, setColapsada] = useState(
    () => localStorage.getItem(MEMORIA_BARRA) === 'si',
  )
  const [menuMovil, setMenuMovil] = useState(false)

  // En celular el menú tapa la pantalla: si no se cierra solo al navegar, uno
  // pulsa una opción y se queda mirando el mismo menú.
  useEffect(() => {
    setMenuMovil(false)
  }, [ubicacion.pathname])

  function alternarBarra() {
    setColapsada((v) => {
      localStorage.setItem(MEMORIA_BARRA, v ? 'no' : 'si')
      return !v
    })
  }

  async function cerrar() {
    await salir()
    navegar('/', { replace: true })
  }

  const actual = PANTALLAS.find((p) => ubicacion.pathname.endsWith(`/${p.ruta}`))
  const nombre = sesion?.nombre ?? ''
  const rol =
    sesion?.rol === 'coordinador' ? 'Coordinación del programa' : 'Personal asistencial'

  return (
    <div
      className={`zona-app${colapsada ? ' colapsada' : ''}${actual?.teal ? ' zona-modelo' : ''}`}
    >
      <aside className={`barra${menuMovil ? ' abierta' : ''}`} aria-label="Secciones">
        <div className="barra-marca">
          <span className="marca-sello">R</span>
          <span className="marca-texto">
            <strong>ReingresaIA</strong>
            <small>Riesgo de reingreso a 30 días</small>
          </span>
          <button
            type="button"
            className="barra-cerrar"
            onClick={() => setMenuMovil(false)}
            aria-label="Cerrar el menú"
          >
            <X size={17} strokeWidth={1.6} />
          </button>
        </div>

        <nav className="barra-nav">
          {GRUPOS.map((grupo) => {
            const pantallas = pantallasDe(grupo, permisos)
            if (pantallas.length === 0) return null
            return (
              <div key={grupo} className="barra-grupo">
                <p className="barra-grupo-titulo">{grupo}</p>
                {pantallas.map(({ ruta, titulo, Icono }) => (
                  <NavLink key={ruta} to={ruta} className="barra-enlace" title={titulo}>
                    <Icono size={16} strokeWidth={1.6} aria-hidden="true" />
                    <span>{titulo}</span>
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>

        <div className="barra-pie">
          <div className="barra-persona">
            <span className="avatar">{iniciales(nombre)}</span>
            <span className="barra-persona-texto">
              <strong>{nombre}</strong>
              <small>{rol}</small>
            </span>
          </div>
          <button type="button" className="barra-colapsar" onClick={alternarBarra}>
            <PanelLeft size={15} strokeWidth={1.6} aria-hidden="true" />
            <span>Contraer el menú</span>
          </button>
        </div>
      </aside>

      {menuMovil && (
        <button
          type="button"
          className="velo-movil"
          aria-label="Cerrar el menú"
          onClick={() => setMenuMovil(false)}
        />
      )}

      <div className="columna">
        <header className="cinta">
          <div className="cinta-izq">
            <button
              type="button"
              className="boton-hamburguesa"
              onClick={() => setMenuMovil(true)}
              aria-label="Abrir el menú"
            >
              <Menu size={18} strokeWidth={1.7} />
            </button>
            <p className="miga">
              <span>{actual?.grupo ?? 'ReingresaIA'}</span>
              <i aria-hidden="true">/</i>
              <b>{actual?.titulo ?? 'Inicio'}</b>
            </p>
          </div>

          <div className="cinta-der">
            <Buscador permisos={permisos} />
            <InterruptorTema />
            <button
              type="button"
              className="boton-salir"
              onClick={cerrar}
              aria-label="Cerrar la sesión"
            >
              <LogOut size={15} strokeWidth={1.6} aria-hidden="true" />
              <span>Salir</span>
            </button>
          </div>
        </header>

        <main className="lienzo-app">
          {/* La clave fuerza a React a remontar al cambiar de ruta, y con eso se
              vuelve a disparar la animación de entrada de la pantalla. */}
          <div className="pantalla" key={ubicacion.pathname}>
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
