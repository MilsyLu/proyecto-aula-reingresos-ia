import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { FormularioPaciente } from '../componentes/FormularioPaciente'
import { TextoRevelado } from '../componentes/core/TextoRevelado'
import { api, ErrorApi } from '../lib/api'
import { conSigno, entero, numero, porcentaje, veces } from '../lib/formato'
import type { Trazado } from '../lib/tiposModelo'
import { usarPaciente } from '../lib/usarPaciente'

/**
 * Pantalla 4: el cálculo paso a paso.
 *
 * Esta es la pantalla que responde a «¿y usted cómo sabe?». Abre el cálculo
 * real del modelo en sus ocho pasos, y el sexto muestra los 135 árboles uno
 * por uno. La suma de todos reconstruye la probabilidad hasta el sexto
 * decimal, y eso se verifica en pantalla: si alguna vez dejara de coincidir,
 * la propia aplicación lo dice.
 */
export function PasoAPaso() {
  const { opciones, valores, cambiar, paraEnviar, error } = usarPaciente()
  const [t, setT] = useState<Trazado | null>(null)
  const [fallo, setFallo] = useState<string | null>(null)
  const peticion = useRef(0)

  const trazar = useCallback(async (entradas: Record<string, string | number>) => {
    const mia = ++peticion.current
    try {
      const datos = await api.enviar<Trazado>('/trazado', entradas)
      if (mia === peticion.current) {
        setT(datos)
        setFallo(null)
      }
    } catch (e) {
      if (mia === peticion.current) {
        setFallo(e instanceof ErrorApi ? e.message : 'No se pudo calcular el trazado.')
      }
    }
  }, [])

  useEffect(() => {
    if (!opciones) return
    const temporizador = setTimeout(() => trazar(paraEnviar), 300)
    return () => clearTimeout(temporizador)
  }, [opciones, paraEnviar, trazar])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Trabajar" titulo="El cálculo, paso a paso" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Trabajar" titulo="El cálculo, paso a paso">
        <p>
          De lo que usted escribe a la probabilidad final, sin saltarse nada. No es una
          ilustración: es el cálculo real, y la suma de los 135 árboles reconstruye el resultado
          del modelo hasta el sexto decimal.
        </p>
      </Encabezado>

      {opciones && (
        <details className="editor-paciente">
          <summary>Cambiar el paciente</summary>
          <div style={{ marginTop: 22 }}>
            <FormularioPaciente campos={opciones.campos} valores={valores} onCambio={cambiar} />
          </div>
        </details>
      )}

      {fallo && <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{fallo}</p>}
      {!t && !fallo && <p className="antetitulo" style={{ marginTop: 32 }}>Calculando</p>}

      {t && (
        <div className="pasos">
          <Paso n={1} titulo="Lo que se escribió">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              Quince campos. Los que están en su valor típico no mueven el resultado: el modelo
              los ve, pero no encuentra en ellos nada que lo aparte de la tasa base.
            </TextoRevelado>
            <div className="fichas">
              {t.escrito.map((c) => (
                <span key={c.campo} className={c.es_tipico ? 'ficha tipica' : 'ficha'}>
                  {c.nombre}: <strong>{c.valor}</strong>
                  {c.es_tipico && <em>típico</em>}
                </span>
              ))}
            </div>
          </Paso>

          <Paso n={2} titulo="Las cincuenta columnas">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              El modelo no espera quince datos sino cincuenta. Las que el formulario no pregunta
              se rellenan con el valor más frecuente de la cohorte, y cinco se calculan a partir
              de las otras. Conviene decirlo claro: el modelo no adivina esas treinta.
            </TextoRevelado>
            <div className="mini-cifras">
              <Dato valor={entero(t.columnas.resumen.del_formulario)} nota="del formulario" />
              <Dato valor={entero(t.columnas.resumen.calculadas)} nota="calculadas a partir de las otras" />
              <Dato valor={entero(t.columnas.resumen.tipicas)} nota="con el valor típico de la cohorte" />
            </div>
          </Paso>

          <Paso n={3} titulo="Los vacíos">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              Lo que llega vacío no se descarta ni se inventa: se marca como Ausente, que es una
              categoría que el modelo aprendió durante el entrenamiento. Para este paciente no
              quedó ninguna columna vacía.
            </TextoRevelado>
            {t.vacios.length > 0 && (
              <div className="fichas">
                {t.vacios.map((v) => (
                  <span key={v.columna} className="ficha">
                    {v.columna} → <strong>{v.relleno}</strong>
                  </span>
                ))}
              </div>
            )}
          </Paso>

          <Paso n={4} titulo="De palabras a números">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              Las treinta y tres columnas de texto se convierten en números, cada categoría al
              suyo. Si llegara una que el modelo no vio en el entrenamiento recibiría un menos
              uno, y la predicción saldría degradada sin avisar. Por eso se comprueba y se dice.
            </TextoRevelado>
            <p className={t.codificadas.no_vistas.length ? 'alerta' : 'paso-nota'}>
              {t.codificadas.no_vistas.length === 0
                ? 'Las treinta y tres categorías son conocidas.'
                : `Hay ${t.codificadas.no_vistas.length} categorías que el modelo no conoce. La estimación no es de fiar.`}
            </p>
            <div className="fichas">
              {t.codificadas.detalle
                .filter((c) => c.valor !== 'No' && c.valor !== 'Ausente')
                .slice(0, 8)
                .map((c) => (
                  <span key={c.columna} className={c.conocida ? 'ficha' : 'ficha mala'}>
                    {c.columna}: {c.valor} → <strong>{c.codigo}</strong>
                  </span>
                ))}
            </div>
          </Paso>

          <Paso n={5} titulo="El punto de partida">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              Antes del primer árbol el modelo ya dice algo, y dice la verdad del conjunto: la
              proporción de pacientes que reingresa. De ahí arranca todo, y es la razón por la
              que el once por ciento no es un error del modelo sino el punto de partida.
            </TextoRevelado>
            <div className="mini-cifras">
              <Dato valor={numero(t.partida.log_odds, 4)} nota="en log-odds, como lo calcula por dentro" />
              <Dato valor={porcentaje(t.partida.probabilidad)} nota="la misma cifra, en probabilidad" />
            </div>
          </Paso>

          <Paso n={6} titulo={`Los ${t.arboles.total} árboles`} destacado>
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              Cada árbol mueve la cifra un poco, hacia arriba o hacia abajo. No son ciento
              treinta y cinco decisiones independientes sino una sola subida, y la mayor parte
              ocurre al principio.
            </TextoRevelado>
            <Curva trazado={t} />
            <div className="mini-cifras" style={{ marginTop: 26 }}>
              <Dato
                valor={`${Math.round(t.arboles.fraccion_primeros_quince * 100)} %`}
                nota="del recorrido lo hacen los quince primeros"
              />
              <Dato
                valor={`#${t.arboles.mas_fuertes[0]?.n}`}
                nota={`el que más mueve, con ${conSigno(t.arboles.mas_fuertes[0]?.aporte ?? 0, 4)} en log-odds`}
              />
              <Dato valor={entero(t.arboles.total)} nota="árboles en total, decididos por parada temprana" />
            </div>
            <details className="tabla-arboles">
              <summary>Ver los diez que más mueven</summary>
              <table>
                <thead>
                  <tr>
                    <th>Árbol</th>
                    <th className="n">Aporte en log-odds</th>
                    <th className="n">Riesgo tras ese árbol</th>
                  </tr>
                </thead>
                <tbody>
                  {t.arboles.mas_fuertes.map((a) => (
                    <tr key={a.n}>
                      <td>#{a.n}</td>
                      <td className="n">{conSigno(a.aporte, 4)}</td>
                      <td className="n">{porcentaje(a.probabilidad)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </details>
          </Paso>

          <Paso n={7} titulo="De log-odds a probabilidad">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              La suma de todos los árboles da un número en log-odds, que no significa nada para
              nadie. La función logística lo convierte en una probabilidad, que sí.
            </TextoRevelado>
            <div className="mini-cifras">
              <Dato valor={numero(t.final.log_odds, 4)} nota="la suma final, en log-odds" />
              <Dato valor={porcentaje(t.final.probabilidad, 2)} nota="convertida a probabilidad" />
            </div>
            <p className={t.final.coincide ? 'comprobacion' : 'alerta'}>
              {t.final.coincide
                ? `Coincide con lo que responde el modelo (${numero(t.final.del_modelo * 100, 4)} %). La reconstrucción es exacta.`
                : 'La reconstrucción no coincide con el modelo. Algo se rompió en el preprocesamiento.'}
            </p>
          </Paso>

          <Paso n={8} titulo="El umbral">
            <TextoRevelado className="paso-texto" porPalabra={0.014}>
              La última decisión no es del modelo sino del programa. El umbral dice a cuánta
              gente alcanza a llamar el equipo de seguimiento, y por eso lo fija la coordinación
              y no el personal asistencial.
            </TextoRevelado>
            <div className="mini-cifras">
              <Dato valor={porcentaje(t.umbral.valor)} nota="el umbral del programa" />
              <Dato
                valor={t.umbral.veces_la_base ? veces(t.umbral.veces_la_base) : '—'}
                nota="veces la tasa base de la cohorte"
              />
              <Dato
                valor={t.umbral.supera ? 'Sí' : 'No'}
                nota={t.umbral.supera ? 'entra en la lista de llamadas' : 'queda fuera de la lista'}
              />
            </div>
          </Paso>
        </div>
      )}

      <style>{`
        .editor-paciente {
          margin-top: 36px; padding: 20px 24px;
          background: var(--superficie); border-radius: var(--radius-tarjeta);
        }
        .editor-paciente summary {
          cursor: pointer; font-size: 14px; font-weight: 500; list-style: none;
        }
        .editor-paciente summary::-webkit-details-marker { display: none; }
        .editor-paciente summary::before { content: '＋  '; color: var(--apagado); }
        .editor-paciente[open] summary::before { content: '−  '; }

        .pasos { margin-top: 20px; }
        .paso {
          display: grid; grid-template-columns: 56px minmax(0, 1fr); gap: 28px;
          padding-block: 38px; border-top: 1px solid var(--filete);
        }
        .paso:last-child { border-bottom: 1px solid var(--filete); }
        .paso-numero {
          font-family: var(--font-serif); font-weight: 300; font-size: 30px;
          line-height: 1.1; letter-spacing: -0.02em; color: var(--apagado);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .paso h2 { font-size: 26px; line-height: 1.2; }
        .paso-texto {
          margin-top: 12px; font-size: 15.5px; line-height: 1.7;
          color: var(--apagado); max-width: 64ch;
        }
        .paso-nota { margin-top: 14px; font-size: 13.5px; color: var(--apagado); }
        .comprobacion { margin-top: 16px; font-size: 13.5px; color: var(--tinta); }
        .alerta { margin-top: 16px; font-size: 13.5px; color: var(--color-dato-4); font-weight: 500; }

        .fichas { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 18px; }
        .ficha {
          display: inline-flex; align-items: baseline; gap: 5px;
          border-radius: 999px; background: var(--superficie-2);
          padding: 5px 13px; font-size: 12.5px; color: var(--tinta);
        }
        .ficha strong { font-weight: 600; font-variant-numeric: tabular-nums lining-nums; }
        .ficha em { font-style: normal; font-size: 10.5px; color: var(--apagado); margin-left: 3px; }
        .ficha.tipica { background: transparent; border: 1px solid var(--filete); color: var(--apagado); }
        .ficha.mala { background: var(--color-dato-1); color: var(--color-dato-5); }

        .mini-cifras {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
          gap: 24px; margin-top: 22px;
        }
        .mini-cifra-valor {
          font-family: var(--font-serif); font-weight: 300; font-size: 28px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .mini-cifra-nota { margin-top: 7px; font-size: 12px; line-height: 1.5; color: var(--apagado); }

        .tabla-arboles { margin-top: 26px; }
        .tabla-arboles summary {
          cursor: pointer; font-size: 13.5px; color: var(--apagado); list-style: none;
        }
        .tabla-arboles summary::-webkit-details-marker { display: none; }
        .tabla-arboles summary::before { content: '＋  '; }
        .tabla-arboles[open] summary::before { content: '−  '; }
        .tabla-arboles table { width: 100%; border-collapse: collapse; margin-top: 16px; max-width: 520px; }
        .tabla-arboles th {
          text-align: left; font-size: 11px; font-weight: 500; letter-spacing: .14em;
          text-transform: uppercase; color: var(--apagado);
          padding: 0 10px 10px 0; border-bottom: 1px solid var(--filete);
        }
        .tabla-arboles td { padding: 10px 10px 10px 0; border-bottom: 1px solid var(--filete); font-size: 14px; }
        .tabla-arboles .n { text-align: right; padding-right: 0; }

        @media (width < 760px) {
          .paso { grid-template-columns: 40px minmax(0, 1fr); gap: 16px; }
        }
      `}</style>
    </div>
  )
}

function Paso({
  n,
  titulo,
  destacado = false,
  children,
}: {
  n: number
  titulo: string
  destacado?: boolean
  children: React.ReactNode
}) {
  return (
    <section className="paso">
      <div className="paso-numero" aria-hidden="true">
        {String(n).padStart(2, '0')}
      </div>
      <div>
        <h2 style={destacado ? { color: 'var(--tinta-fuerte)' } : undefined}>{titulo}</h2>
        {children}
      </div>
    </section>
  )
}

function Dato({ valor, nota }: { valor: string; nota: string }) {
  return (
    <div>
      <div className="mini-cifra-valor">{valor}</div>
      <p className="mini-cifra-nota">{nota}</p>
    </div>
  )
}

/** La subida del riesgo a lo largo de los árboles, dibujándose al llegar. */
function Curva({ trazado }: { trazado: Trazado }) {
  const ruta = useRef<SVGPathElement | null>(null)
  const [visible, setVisible] = useState(false)

  const { d, cx, cy, minimo, maximo } = useMemo(() => {
    const puntos = [trazado.partida.probabilidad, ...trazado.arboles.pasos.map((p) => p.probabilidad)]
    const min = Math.min(...puntos)
    const max = Math.max(...puntos)
    const margen = Math.max((max - min) * 0.14, 0.004)
    const lo = min - margen
    const hi = max + margen
    const X = (i: number) => 6 + (i / (puntos.length - 1)) * 1028
    const Y = (v: number) => 206 - ((v - lo) / (hi - lo)) * 186
    return {
      d: puntos.map((v, i) => `${i ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join(' '),
      cx: X(puntos.length - 1),
      cy: Y(puntos[puntos.length - 1]),
      minimo: lo,
      maximo: hi,
    }
  }, [trazado])

  useEffect(() => {
    const nodo = ruta.current
    if (!nodo) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setVisible(true)
      return
    }
    const observador = new IntersectionObserver(
      (e) => {
        if (e.some((x) => x.isIntersecting)) {
          setVisible(true)
          observador.disconnect()
        }
      },
      { threshold: 0.3 },
    )
    observador.observe(nodo)
    return () => observador.disconnect()
  }, [d])

  const largo = 4000

  return (
    <figure style={{ margin: '26px 0 0' }}>
      <svg
        viewBox="0 0 1040 224"
        style={{ width: '100%', height: 'auto' }}
        role="img"
        aria-label={`Curva del riesgo a lo largo de ${trazado.arboles.total} árboles, de ${(trazado.partida.probabilidad * 100).toFixed(1)} por ciento a ${(trazado.final.probabilidad * 100).toFixed(1)} por ciento`}
      >
        <line x1="0" y1="212" x2="1040" y2="212" stroke="var(--filete)" strokeWidth="1" />
        <path
          ref={ruta}
          d={d}
          fill="none"
          stroke="var(--color-dato-3)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{
            strokeDasharray: largo,
            strokeDashoffset: visible ? 0 : largo,
            transition: 'stroke-dashoffset 1.9s cubic-bezier(.3,.6,.25,1)',
          }}
        />
        <circle
          cx={cx}
          cy={cy}
          r="5"
          fill="var(--color-dato-3)"
          style={{ opacity: visible ? 1 : 0, transition: 'opacity .5s ease 1.9s' }}
        />
      </svg>
      <figcaption
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: 11.5,
          color: 'var(--apagado)',
          marginTop: 6,
        }}
      >
        <span>árbol 1</span>
        <span>
          de {porcentaje(minimo)} a {porcentaje(maximo)} en el eje vertical
        </span>
        <span>árbol {trazado.arboles.total}</span>
      </figcaption>
    </figure>
  )
}
