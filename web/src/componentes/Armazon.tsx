import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useSesion } from '../lib/sesion'
import { GRUPOS, pantallasDe } from '../rutas'
import { InterruptorTema } from './InterruptorTema'

/**
 * El armazón de la aplicación: barra superior fija, menú lateral y el contenido.
 *
 * El menú se dibuja a partir del registro de pantallas filtrado por los permisos
 * que devolvió el servidor, así que un grupo entero desaparece si el rol no
 * tiene nada dentro. Nunca aparece un enlace que al pulsarlo rebote.
 */
export function Armazon() {
  const { sesion, salir } = useSesion()
  const navegar = useNavigate()
  const permisos = sesion?.permisos ?? []

  async function cerrar() {
    await salir()
    navegar('/', { replace: true })
  }

  return (
    <>
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 20,
          background: 'var(--lienzo)',
          borderBottom: '1px solid var(--filete)',
        }}
      >
        <div
          className="pagina"
          style={{
            paddingBlock: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 20,
          }}
        >
          <NavLink
            to="/"
            style={{
              fontFamily: 'var(--font-serif)',
              fontSize: 21,
              letterSpacing: '-0.01em',
              color: 'var(--tinta-fuerte)',
              textDecoration: 'none',
            }}
          >
            ReingresaIA
          </NavLink>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ textAlign: 'right', lineHeight: 1.3 }}>
              <p style={{ fontSize: 13, fontWeight: 500 }}>{sesion?.nombre}</p>
              <p style={{ fontSize: 11.5, color: 'var(--apagado)' }}>
                {sesion?.rol === 'coordinador' ? 'Coordinación del programa' : 'Personal asistencial'}
              </p>
            </div>
            <InterruptorTema />
            <button type="button" className="pastilla pastilla-contorno pastilla-sm" onClick={cerrar}>
              Salir
            </button>
          </div>
        </div>
      </header>

      <div className="armazon">
        <nav className="rail" aria-label="Secciones de la aplicación">
          {GRUPOS.map((grupo) => {
            const pantallas = pantallasDe(grupo, permisos)
            if (pantallas.length === 0) return null
            return (
              <div key={grupo} style={{ marginBottom: 26 }}>
                <p className="antetitulo" style={{ fontSize: 11, opacity: 0.65, marginBottom: 8 }}>
                  {grupo}
                </p>
                {pantallas.map(({ ruta, titulo }) => (
                  <NavLink key={ruta} to={ruta} className="enlace-rail">
                    {titulo}
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>

        <main style={{ paddingBlock: '44px 110px', minHeight: '72vh' }}>
          <Outlet />
        </main>
      </div>

      <style>{`
        .armazon {
          max-width: var(--container-pagina);
          margin-inline: auto;
          padding-inline: 40px;
          display: grid;
          grid-template-columns: 216px minmax(0, 1fr);
          gap: 56px;
          align-items: start;
        }
        .rail {
          position: sticky;
          top: 76px;
          padding-block: 44px 40px;
          border-right: 1px solid var(--filete);
          min-height: 72vh;
        }
        .enlace-rail {
          display: block;
          padding: 10px 20px 10px 0;
          font-size: 14.5px;
          font-weight: 500;
          letter-spacing: -0.01em;
          color: var(--apagado);
          text-decoration: none;
          transition: color .25s ease;
        }
        .enlace-rail:hover { color: var(--tinta); }
        .enlace-rail.active { color: var(--tinta-fuerte); }
        @media (width < 980px) {
          .armazon {
            grid-template-columns: 1fr;
            gap: 0;
            padding-inline: 24px;
          }
          .rail {
            position: static;
            min-height: 0;
            border-right: 0;
            border-bottom: 1px solid var(--filete);
            padding-block: 16px;
            display: flex;
            gap: 18px;
            overflow-x: auto;
          }
          .rail > div { margin-bottom: 0 !important; display: flex; gap: 18px; align-items: center; }
          .rail .antetitulo { display: none; }
          .enlace-rail { padding: 6px 0; white-space: nowrap; }
        }
      `}</style>
    </>
  )
}
