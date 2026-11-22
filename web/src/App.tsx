import type { ReactNode } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { Armazon } from './componentes/Armazon'
import { useSesion } from './lib/sesion'
import { Entrar } from './paginas/Entrar'
import { Portada } from './paginas/Portada'
import { PANTALLAS } from './rutas'

/** Mientras se le pregunta al servidor si la cookie sigue viva, no se decide nada. */
function Esperando() {
  return (
    <div style={{ minHeight: '60vh', display: 'grid', placeItems: 'center' }} aria-live="polite">
      <p className="antetitulo">Abriendo su sesión</p>
    </div>
  )
}

/**
 * Puerta de entrada del front. La de verdad está en la API, en cada ruta: esto
 * solo evita mostrar pantallas que de todas formas rebotarían.
 */
function Protegida({ children }: { children: ReactNode }) {
  const { sesion, cargando } = useSesion()
  const ubicacion = useLocation()

  if (cargando) return <Esperando />
  if (!sesion) return <Navigate to="/entrar" state={{ desde: ubicacion.pathname }} replace />
  return <>{children}</>
}

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Portada />} />
      <Route path="/entrar" element={<Entrar />} />

      <Route
        path="/app"
        element={
          <Protegida>
            <Armazon />
          </Protegida>
        }
      >
        <Route index element={<Navigate to={PANTALLAS[0].ruta} replace />} />
        {PANTALLAS.map(({ ruta, Componente }) => (
          <Route key={ruta} path={ruta} element={<Componente />} />
        ))}
        <Route path="*" element={<Navigate to={PANTALLAS[0].ruta} replace />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
