import { useEffect, useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { InterruptorTema } from '../componentes/InterruptorTema'
import { api, ErrorApi } from '../lib/api'
import { useSesion } from '../lib/sesion'

interface CuentaDemo {
  usuario: string
  clave: string
  rol: string
}

export function Entrar() {
  const { entrar, sesion } = useSesion()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? '/app'

  const [usuario, setUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)
  const [demo, setDemo] = useState<CuentaDemo[]>([])

  useEffect(() => {
    if (sesion) navegar(destino, { replace: true })
  }, [sesion, destino, navegar])

  // Las cuentas de demostración solo existen en el prototipo. En producción la
  // API devuelve una lista vacía y este bloque no se dibuja.
  useEffect(() => {
    api.obtener<CuentaDemo[]>('/cuentas-demo').then(setDemo).catch(() => setDemo([]))
  }, [])

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault()
    if (enviando) return
    setError(null)
    setEnviando(true)
    try {
      await entrar(usuario, contrasena)
      navegar(destino, { replace: true })
    } catch (falla) {
      setError(falla instanceof ErrorApi ? falla.message : 'No se pudo entrar.')
      setContrasena('')
    } finally {
      setEnviando(false)
    }
  }

  function usarCuenta(cuenta: CuentaDemo) {
    setUsuario(cuenta.usuario)
    setContrasena(cuenta.clave)
    setError(null)
  }

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      <header
        className="pagina"
        style={{
          paddingBlock: 26,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Link
          to="/"
          style={{
            fontFamily: 'var(--font-serif)',
            fontSize: 22,
            color: 'var(--tinta-fuerte)',
            textDecoration: 'none',
          }}
        >
          ReingresaIA
        </Link>
        <InterruptorTema />
      </header>

      <main
        className="pagina"
        style={{ flex: 1, display: 'grid', placeItems: 'center', paddingBlock: '40px 90px' }}
      >
        <div style={{ width: '100%', maxWidth: 400 }}>
          <p className="antetitulo">Acceso al programa</p>
          <h1 style={{ fontSize: 'clamp(34px, 5vw, 48px)', marginTop: 14 }}>Entrar</h1>
          <p style={{ color: 'var(--apagado)', marginTop: 16, fontSize: 15, lineHeight: 1.6 }}>
            Esta herramienta ordena a qué paciente conviene llamar primero después del alta. No
            decide altas ni tratamientos.
          </p>

          <form onSubmit={enviar} style={{ marginTop: 34 }}>
            <label className="antetitulo" htmlFor="usuario" style={{ display: 'block' }}>
              Usuario
            </label>
            <input
              id="usuario"
              className="campo"
              value={usuario}
              onChange={(e) => setUsuario(e.target.value)}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              required
            />

            <label
              className="antetitulo"
              htmlFor="contrasena"
              style={{ display: 'block', marginTop: 18 }}
            >
              Contraseña
            </label>
            <input
              id="contrasena"
              className="campo"
              type="password"
              value={contrasena}
              onChange={(e) => setContrasena(e.target.value)}
              autoComplete="current-password"
              required
            />

            {error && (
              <p
                role="alert"
                style={{ marginTop: 16, fontSize: 14, color: 'var(--color-dato-4)' }}
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              className="pastilla pastilla-rellena"
              style={{ marginTop: 24, width: '100%', justifyContent: 'center' }}
              disabled={enviando}
            >
              {enviando ? 'Verificando…' : 'Entrar'}
            </button>
          </form>

          {demo.length > 0 && (
            <div
              style={{
                marginTop: 40,
                paddingTop: 24,
                borderTop: '1px solid var(--filete)',
              }}
            >
              <p className="antetitulo">Cuentas de demostración</p>
              <p style={{ fontSize: 13, color: 'var(--apagado)', marginTop: 10, lineHeight: 1.6 }}>
                Pulse una para llenar el formulario. No protegen ningún dato sensible: la
                aplicación solo muestra resultados agregados de un conjunto público.
              </p>
              <div style={{ display: 'grid', gap: 8, marginTop: 16 }}>
                {demo.map((cuenta) => (
                  <button
                    key={cuenta.usuario}
                    type="button"
                    onClick={() => usarCuenta(cuenta)}
                    className="cuenta-demo"
                  >
                    <span style={{ fontWeight: 500 }}>{cuenta.rol}</span>
                    <span style={{ color: 'var(--apagado)', fontSize: 13 }}>{cuenta.usuario}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="pagina" style={{ paddingBlock: 28, borderTop: '1px solid var(--filete)' }}>
        <p style={{ fontSize: 12, color: 'var(--apagado)', lineHeight: 1.6 }}>
          Universidad Popular del Cesar · Grupo 04. Prototipo académico, no validado para
          decisiones clínicas y sin datos de pacientes reales.
        </p>
      </footer>

      <style>{`
        .campo {
          width: 100%;
          margin-top: 8px;
          background: var(--superficie);
          border: 1px solid var(--filete);
          border-radius: var(--radius-entrada);
          padding: 13px 15px;
          font-family: var(--font-sans);
          font-size: 15px;
          color: var(--tinta);
          letter-spacing: -0.009em;
        }
        .campo:focus { outline: none; border-color: var(--filete-fuerte); }
        .cuenta-demo {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          width: 100%;
          text-align: left;
          background: var(--superficie);
          border: 1px solid transparent;
          border-radius: var(--radius-entrada);
          padding: 12px 15px;
          font-family: var(--font-sans);
          font-size: 14px;
          color: var(--tinta);
          cursor: pointer;
          transition: border-color .25s ease;
        }
        .cuenta-demo:hover { border-color: var(--borde-suave); }
      `}</style>
    </div>
  )
}
