import { Search } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { pantallasVisibles } from '../rutas'

/**
 * El salto rápido entre pantallas, con Ctrl+K.
 *
 * Son diecisiete pantallas en cinco grupos. Recorrer el menú con el ratón para
 * llegar a la que uno ya sabe cómo se llama es trabajo de más, y en una
 * sustentación en vivo cada segundo buscando se nota.
 *
 * Solo lista lo que el rol puede abrir: nunca ofrece un atajo que al pulsarlo
 * rebotaría contra un 403.
 */
export function Buscador({ permisos }: { permisos: string[] }) {
  const [abierto, setAbierto] = useState(false)
  const [texto, setTexto] = useState('')
  const [elegido, setElegido] = useState(0)
  const campo = useRef<HTMLInputElement | null>(null)
  const navegar = useNavigate()

  const todas = useMemo(() => pantallasVisibles(permisos), [permisos])

  // Se comparan sin tildes: quien escribe deprisa escribe "estadistica".
  const limpio = (s: string) =>
    s
      .toLowerCase()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')

  const resultados = useMemo(() => {
    const q = limpio(texto.trim())
    if (!q) return todas
    return todas.filter((p) => limpio(p.titulo + ' ' + p.grupo).includes(q))
  }, [texto, todas])

  useEffect(() => {
    function tecla(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setAbierto((v) => !v)
        setTexto('')
        setElegido(0)
      }
      if (e.key === 'Escape') setAbierto(false)
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [])

  useEffect(() => {
    if (abierto) campo.current?.focus()
  }, [abierto])

  function ir(indice: number) {
    const destino = resultados[indice]
    if (!destino) return
    setAbierto(false)
    navegar(`/app/${destino.ruta}`)
  }

  return (
    <>
      <button
        type="button"
        className="boton-buscar"
        onClick={() => {
          setAbierto(true)
          setTexto('')
          setElegido(0)
        }}
      >
        <Search size={14} strokeWidth={1.6} aria-hidden="true" />
        <span>Buscar pantalla</span>
        <kbd>Ctrl K</kbd>
      </button>

      {abierto && (
        <div
          className="buscador-velo"
          role="presentation"
          onClick={(e) => {
            if (e.target === e.currentTarget) setAbierto(false)
          }}
        >
          <div className="buscador-caja" role="dialog" aria-modal="true" aria-label="Buscar pantalla">
            <div className="buscador-campo">
              <Search size={16} strokeWidth={1.6} aria-hidden="true" />
              <input
                ref={campo}
                value={texto}
                placeholder="Escriba el nombre de una pantalla"
                onChange={(e) => {
                  setTexto(e.target.value)
                  setElegido(0)
                }}
                onKeyDown={(e) => {
                  if (e.key === 'ArrowDown') {
                    e.preventDefault()
                    setElegido((i) => Math.min(i + 1, resultados.length - 1))
                  }
                  if (e.key === 'ArrowUp') {
                    e.preventDefault()
                    setElegido((i) => Math.max(i - 1, 0))
                  }
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    ir(elegido)
                  }
                }}
              />
            </div>

            <div className="buscador-lista">
              {resultados.length === 0 && (
                <p className="buscador-vacio">Ninguna pantalla se llama así.</p>
              )}
              {resultados.map((p, i) => (
                <button
                  key={p.ruta}
                  type="button"
                  className={i === elegido ? 'buscador-fila elegida' : 'buscador-fila'}
                  onMouseEnter={() => setElegido(i)}
                  onClick={() => ir(i)}
                >
                  <p.Icono size={15} strokeWidth={1.5} aria-hidden="true" />
                  <span>{p.titulo}</span>
                  <em>{p.grupo}</em>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  )
}
