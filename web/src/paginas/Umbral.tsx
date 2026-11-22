import { useCallback, useEffect, useRef, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { entero, porcentaje, veces } from '../lib/formato'

/**
 * Pantalla 7: fijar el umbral y la capacidad.
 *
 * Es la palanca de política del programa, y por eso está reservada a
 * coordinación: de ella depende a cuánta gente se llama y, por tanto, cuánto
 * cuesta el programa. Quien la mueve responde por esa decisión.
 *
 * La pantalla está construida alrededor de la pregunta que de verdad se hace
 * un coordinador —«¿a cuántos alcanzo a llamar?»— y no alrededor de la que se
 * hace un estadístico —«¿qué umbral pongo?»—. El umbral sale como consecuencia.
 */

interface Consecuencias {
  llamadas: number
  poblacion: number
  fraccion: number
  umbral_resultante: number
  umbral_oficial: number
  aciertan: number
  tasa: number
  tasa_base: number
  veces_la_base: number
  cobertura: number
  se_escapan: number
  reingresos_totales: number
  llamadas_de_mas: number
}

const ATAJOS = [100, 397, 993, 1987, 3974]

export function Umbral() {
  const [llamadas, setLlamadas] = useState(397)
  const [c, setC] = useState<Consecuencias | null>(null)
  const [error, setError] = useState<string | null>(null)
  const peticion = useRef(0)

  const consultar = useCallback(async (n: number) => {
    const mia = ++peticion.current
    try {
      const datos = await api.enviar<Consecuencias>('/capacidad', { llamadas: n })
      if (mia === peticion.current) {
        setC(datos)
        setError(null)
      }
    } catch (e) {
      if (mia === peticion.current) {
        setError(e instanceof ErrorApi ? e.message : 'No se pudo calcular.')
      }
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => consultar(llamadas), 220)
    return () => clearTimeout(t)
  }, [llamadas, consultar])

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="Fijar el umbral y la capacidad">
        <p>
          Esta es la decisión que el modelo no toma. Depende de a cuánta gente alcanza a llamar
          el equipo de seguimiento, y por eso la fija la coordinación del programa.
        </p>
      </Encabezado>

      <section className="bloque-u">
        <label className="antetitulo" htmlFor="cuantos">
          ¿A cuántos pacientes alcanza a llamar?
        </label>
        <div className="control-u">
          <input
            id="cuantos"
            type="range"
            min={50}
            max={6000}
            step={1}
            value={llamadas}
            onChange={(e) => setLlamadas(Number(e.target.value))}
          />
          <input
            type="number"
            className="numero-u"
            min={1}
            max={19870}
            value={llamadas}
            onChange={(e) => setLlamadas(Math.max(1, Number(e.target.value) || 1))}
            aria-label="Número exacto de llamadas"
          />
        </div>
        <div className="atajos">
          {ATAJOS.map((n) => (
            <button
              key={n}
              type="button"
              className={n === llamadas ? 'atajo activo' : 'atajo'}
              onClick={() => setLlamadas(n)}
            >
              {entero(n)}
            </button>
          ))}
        </div>
      </section>

      {error && <p className="error-u">{error}</p>}

      {c && (
        <>
          <section className="bloque-u">
            <h2>Qué pasa si llama a {entero(c.llamadas)}</h2>
            <div className="cifras-u">
              <Dato v={porcentaje(c.tasa)} n="de ellos reingresa de verdad" />
              <Dato v={veces(c.veces_la_base)} n={`la tasa general, que es ${porcentaje(c.tasa_base)}`} />
              <Dato v={porcentaje(c.cobertura)} n="de todos los reingresos quedan dentro de la lista" />
              <Dato v={porcentaje(c.umbral_resultante)} n="el umbral que resulta de ese corte" />
            </div>
          </section>

          <section className="bloque-u">
            <h2>Lo que cuesta esa decisión</h2>
            <p className="texto-u">
              Toda elección de umbral tiene dos costos, y conviene mirarlos juntos en vez de
              celebrar solo el primero.
            </p>
            <div className="costos">
              <div className="costo">
                <div className="costo-v">{entero(c.aciertan)}</div>
                <p className="costo-t">pacientes a los que llama y que sí van a volver</p>
                <p className="costo-n">
                  Es lo que el programa gana. De los {entero(c.reingresos_totales)} reingresos
                  del período, alcanza a cubrir {porcentaje(c.cobertura)}.
                </p>
              </div>
              <div className="costo">
                <div className="costo-v">{entero(c.se_escapan)}</div>
                <p className="costo-t">pacientes que van a volver y no reciben llamada</p>
                <p className="costo-n">
                  Es el costo real de poner el corte aquí. Subir el umbral los aumenta.
                </p>
              </div>
              <div className="costo">
                <div className="costo-v">{entero(c.llamadas_de_mas)}</div>
                <p className="costo-t">llamadas a personas que no iban a volver</p>
                <p className="costo-n">
                  Gastan tiempo del equipo, pero no hacen daño a nadie. En esa asimetría está la
                  razón para preferir alertar de más.
                </p>
              </div>
            </div>
          </section>

          <section className="bloque-u destacado">
            <h2>Por qué esta pantalla es de coordinación</h2>
            <p className="texto-u">
              El umbral oficial está en {porcentaje(c.umbral_oficial)}, elegido con un criterio
              escrito antes de verlo: alcanzar una sensibilidad de 0,60, que era la meta de la
              Fase 1. Con ese corte se alerta sobre el 38 % de los pacientes.
            </p>
            <p className="texto-u">
              Moverlo no es un ajuste técnico: cambia cuántas llamadas hay que hacer, cuánta
              gente hace falta para hacerlas y a cuántos pacientes se deja fuera. Es una
              decisión de política sanitaria, y quien la toma responde por ella. Por eso el
              personal asistencial ve el resultado pero no mueve el corte.
            </p>
          </section>

          <p className="nota-u">
            Todo esto se calcula sobre el conjunto de prueba, con {entero(c.poblacion)}{' '}
            hospitalizaciones, porque es el único sitio donde se sabe quién reingresó de verdad.
            En funcionamiento real no se podría medir: solo se sabe después.
          </p>
        </>
      )}

      <style>{`
        .bloque-u { padding-block: 36px; border-top: 1px solid var(--filete); }
        .bloque-u:first-of-type { border-top: 0; padding-top: 32px; }
        .bloque-u h2 { font-size: 26px; }
        .bloque-u.destacado {
          background: var(--superficie); border-radius: var(--radius-tarjeta);
          padding: 30px; border-top: 0; margin-top: 24px;
        }
        .texto-u { margin-top: 14px; font-size: 15px; line-height: 1.7; color: var(--apagado); max-width: 70ch; }
        .nota-u {
          margin-top: 32px; padding-top: 20px; border-top: 1px solid var(--filete);
          font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 76ch;
        }
        .error-u { margin-top: 20px; font-size: 14px; color: var(--color-dato-4); }

        .control-u { display: flex; align-items: center; gap: 18px; margin-top: 16px; max-width: 640px; }
        .control-u input[type="range"] { flex: 1; accent-color: var(--tinta); }
        .numero-u {
          width: 96px; background: var(--superficie); border: 1px solid var(--filete);
          border-radius: var(--radius-entrada); padding: 9px 11px;
          font-family: var(--font-sans); font-size: 15px; color: var(--tinta);
          font-variant-numeric: tabular-nums lining-nums; text-align: right;
        }
        .numero-u:focus { outline: none; border-color: var(--filete-fuerte); }
        .atajos { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 16px; }
        .atajo {
          border-radius: 999px; border: 1px solid var(--filete); background: transparent;
          cursor: pointer; padding: 6px 14px; font-family: var(--font-sans);
          font-size: 12.5px; color: var(--apagado);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .atajo:hover { border-color: var(--borde-suave); color: var(--tinta); }
        .atajo.activo { background: var(--relleno); color: var(--sobre-relleno); border-color: var(--relleno); }

        .cifras-u { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 26px; margin-top: 24px; }
        .dato-u-v {
          font-family: var(--font-serif); font-weight: 300; font-size: 38px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .dato-u-n { margin-top: 7px; font-size: 12px; line-height: 1.5; color: var(--apagado); }

        .costos { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; margin-top: 24px; }
        .costo { border: 1px solid var(--filete); border-radius: var(--radius-tarjeta); padding: 22px; }
        .costo-v {
          font-family: var(--font-serif); font-weight: 300; font-size: 36px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .costo-t { margin-top: 8px; font-size: 13.5px; line-height: 1.5; }
        .costo-n { margin-top: 12px; font-size: 12.5px; line-height: 1.6; color: var(--apagado); }
      `}</style>
    </div>
  )
}

function Dato({ v, n }: { v: string; n: string }) {
  return (
    <div>
      <div className="dato-u-v">{v}</div>
      <p className="dato-u-n">{n}</p>
    </div>
  )
}
