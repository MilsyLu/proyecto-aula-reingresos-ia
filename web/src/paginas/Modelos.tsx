import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { TextoRevelado } from '../componentes/core/TextoRevelado'
import { api, ErrorApi } from '../lib/api'
import { conSigno, numero, porcentaje } from '../lib/formato'

/**
 * Pantalla 11: qué modelos probamos y por qué ganó este.
 *
 * Responde dos preguntas que hasta ahora no tenían dónde responderse. Abre con
 * el modelo mayoritario a propósito: acierta el 88,6 % de las veces y no sirve
 * para nada, porque nunca alerta a nadie. Es la trampa de la exactitud
 * explicada en treinta segundos, y deja armado por qué este proyecto no se
 * mide así.
 *
 * Y la respuesta al «por qué este» no es «porque dio más alto», que sería
 * floja: el primer puesto y el segundo empataron en puntaje, pero el primero
 * se sobreajusta mucho menos.
 */

interface Baseline {
  modelo: string
  exactitud: number
  AP: number
  ROC_AUC: number
  precision: number
  recall: number
  VP: number
  FP: number
}

interface Comparacion {
  modelo: string
  AP: number
  ROC_AUC: number
  AP_sobre_prevalencia: number
  'mejora_vs_logistica_%': number
}

interface Laboratorio {
  modelo: string
  AP_prueba: number
  ROC_AUC_prueba: number
  brecha_AP: number
  recall_prueba: number
  precision_prueba: number
  seleccionado: boolean
}

interface Busqueda {
  puesto: number
  AP_validacion_cruzada: number
  AP_entrenamiento: number
  sobreajuste: number
}

interface Datos {
  baseline: Baseline[]
  comparacion: Comparacion[]
  laboratorio: Laboratorio[]
  busqueda_oficial: Busqueda[]
  oficial: Record<string, number>
}

export function Modelos() {
  const [d, setD] = useState<Datos | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Datos>('/modelos')
      .then(setD)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer el modelo" titulo="Qué modelos probamos" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  const mayoritario = d?.baseline.find((b) => b.modelo === 'Mayoritario')
  const primero = d?.busqueda_oficial[0]
  const segundo = d?.busqueda_oficial[1]
  const maxAP = d ? Math.max(...d.comparacion.map((c) => c.AP)) : 1

  return (
    <div>
      <Encabezado
        antetitulo="Conocer el modelo"
        titulo="Qué modelos probamos y por qué ganó este"
      >
        <p>
          Cuatro algoritmos sobre los mismos pacientes y las mismas particiones. Uno de ellos
          está ahí para enseñar algo, no para competir.
        </p>
      </Encabezado>

      {!d && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {d && mayoritario && (
        <>
          {/* ------------------------------- la trampa de la exactitud */}
          <section className="bloque-m destacado">
            <p className="antetitulo">Empecemos por el que no sirve</p>
            <h2>Un modelo que acierta nueve de cada diez veces y es inútil</h2>
            <TextoRevelado className="texto-m" porPalabra={0.015}>
              El modelo mayoritario responde siempre lo mismo: que el paciente no va a
              reingresar. Como solo reingresa uno de cada nueve, acierta casi siempre. Y nunca
              alerta a nadie, así que no sirve absolutamente para nada.
            </TextoRevelado>
            <div className="trampa">
              <div>
                <div className="trampa-valor">{porcentaje(mayoritario.exactitud)}</div>
                <p>de exactitud</p>
              </div>
              <div>
                <div className="trampa-valor">{numero(mayoritario.ROC_AUC, 3)}</div>
                <p>de ROC-AUC, que es exactamente lanzar una moneda</p>
              </div>
              <div>
                <div className="trampa-valor">{numero(mayoritario.VP, 0)}</div>
                <p>pacientes detectados, de 2.262 que reingresaron</p>
              </div>
            </div>
            <p className="texto-m">
              Por eso este proyecto no se mide con exactitud. Se mide con <em>average
              precision</em>, que sí castiga a quien no alerta a nadie, y con sensibilidad, que
              dice a cuántos de los que vuelven se alcanzó a detectar.
            </p>
          </section>

          {/* --------------------------------------- la comparación */}
          <section className="bloque-m">
            <h2>Los cuatro, sobre los mismos pacientes</h2>
            <TextoRevelado className="texto-m" porPalabra={0.015}>
              Todos se evaluaron con la misma partición por paciente y el mismo conjunto de
              prueba, que se miró una sola vez. Comparar de otra forma no significaría nada.
            </TextoRevelado>
            <div className="tabla-envoltura">
              <table className="tabla-m">
                <thead>
                  <tr>
                    <th>Modelo</th>
                    <th className="n">AP</th>
                    <th />
                    <th className="n">ROC-AUC</th>
                    <th className="n">Veces la prevalencia</th>
                    <th className="n">Frente a la logística</th>
                  </tr>
                </thead>
                <tbody>
                  {d.comparacion.map((c) => {
                    const gana = c.modelo.includes('ajustado')
                    return (
                      <tr key={c.modelo} className={gana ? 'ganador' : undefined}>
                        <td>
                          {c.modelo}
                          {gana && <span className="marca">el elegido</span>}
                        </td>
                        <td className="n">{numero(c.AP, 4)}</td>
                        <td className="barra-celda">
                          <i style={{ width: `${(c.AP / maxAP) * 100}%` }} />
                        </td>
                        <td className="n">{numero(c.ROC_AUC, 3)}</td>
                        <td className="n">{numero(c.AP_sobre_prevalencia, 2)}×</td>
                        <td className="n">
                          {c['mejora_vs_logistica_%'] === 0
                            ? 'referencia'
                            : `${conSigno(c['mejora_vs_logistica_%'])} %`}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* ----------------------------------- la red neuronal */}
          {d.laboratorio.length > 0 && (
            <section className="bloque-m">
              <h2>Y la red neuronal</h2>
              <TextoRevelado className="texto-m" porPalabra={0.015}>
                La fase siete de la asignatura pedía probar una red neuronal. Se probó, con tres
                configuraciones y en las mismas condiciones que el Gradient Boosting. Perdió por
                partida doble: puntúa menos y se memoriza los datos más del doble.
              </TextoRevelado>
              <div className="tabla-envoltura">
                <table className="tabla-m">
                  <thead>
                    <tr>
                      <th>Algoritmo</th>
                      <th className="n">AP en prueba</th>
                      <th className="n">ROC-AUC</th>
                      <th className="n">Sensibilidad</th>
                      <th className="n">Sobreajuste</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.laboratorio.map((l) => (
                      <tr key={l.modelo} className={l.seleccionado ? 'ganador' : undefined}>
                        <td>
                          {l.modelo}
                          {l.seleccionado && <span className="marca">ganó</span>}
                        </td>
                        <td className="n">{numero(l.AP_prueba, 4)}</td>
                        <td className="n">{numero(l.ROC_AUC_prueba, 4)}</td>
                        <td className="n">{porcentaje(l.recall_prueba)}</td>
                        <td className="n">{conSigno(l.brecha_AP, 4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="nota-m">
                Esta comparación es una reproducción independiente, con su propia partición y
                120 iteraciones, así que su Gradient Boosting da 0,2206 donde el oficial da
                0,2238. No es una contradicción: son dos corridas distintas del mismo
                algoritmo, y que queden tan cerca es justamente lo que se espera.
              </p>
            </section>
          )}

          {/* --------------------------- por qué esta configuración */}
          {primero && segundo && (
            <section className="bloque-m destacado">
              <p className="antetitulo">La decisión que no se suele contar</p>
              <h2>Ganó el que menos se memoriza, no el que puntuaba más</h2>
              <TextoRevelado className="texto-m" porPalabra={0.015}>
                En la búsqueda de configuraciones el primer puesto y el segundo quedaron
                prácticamente empatados. Lo que los separa no es el puntaje sino cuánto se
                memorizan los datos de entrenamiento, y ahí la diferencia es enorme.
              </TextoRevelado>
              <div className="duelo">
                {[
                  { p: primero, titulo: 'La configuración elegida', gana: true },
                  { p: segundo, titulo: 'La segunda', gana: false },
                ].map(({ p, titulo, gana }) => (
                  <div key={titulo} className={gana ? 'duelo-caja gana' : 'duelo-caja'}>
                    <p className="antetitulo">{titulo}</p>
                    <dl>
                      <div>
                        <dt>Puntaje en validación</dt>
                        <dd>{numero(p.AP_validacion_cruzada, 4)}</dd>
                      </div>
                      <div>
                        <dt>Puntaje en entrenamiento</dt>
                        <dd>{numero(p.AP_entrenamiento, 4)}</dd>
                      </div>
                      <div className="brecha">
                        <dt>Cuánto se memoriza</dt>
                        <dd>{numero(p.sobreajuste, 4)}</dd>
                      </div>
                    </dl>
                  </div>
                ))}
              </div>
              <p className="texto-m">
                Empatados en lo que importa —{numero(primero.AP_validacion_cruzada, 4)} contra{' '}
                {numero(segundo.AP_validacion_cruzada, 4)}— pero el segundo se memoriza{' '}
                {numero(segundo.sobreajuste / primero.sobreajuste, 1)} veces más. Un modelo que
                se aprende los datos de memoria se ve brillante en el laboratorio y falla con
                pacientes nuevos. Se eligió el que generaliza.
              </p>
            </section>
          )}

          {/* ------------------------------------------- honestidad */}
          <section className="bloque-m">
            <h2>Lo que esto no demuestra</h2>
            <p className="texto-m">
              La ganancia del Gradient Boosting sobre una regresión logística es de apenas
              4,8 %. Si alguien prefiriera la logística porque sus coeficientes se leen
              directamente y este modelo necesita una pantalla entera para explicarse, tendría
              un argumento razonable. Se eligió el Gradient Boosting porque gana, pero gana
              poco, y eso también hay que decirlo.
            </p>
          </section>
        </>
      )}

      <style>{`
        .bloque-m { padding-block: 40px; border-top: 1px solid var(--filete); }
        .bloque-m:first-of-type { border-top: 0; padding-top: 28px; }
        .bloque-m h2 { font-size: 28px; margin-top: 8px; max-width: 24ch; }
        .bloque-m.destacado { background: var(--superficie); border-radius: var(--radius-tarjeta);
          padding: 34px; border-top: 0; margin-top: 28px; }
        .texto-m {
          margin-top: 14px; font-size: 15.5px; line-height: 1.7;
          color: var(--apagado); max-width: 66ch;
        }
        .texto-m em { font-style: italic; }
        .nota-m {
          margin-top: 20px; font-size: 12.5px; line-height: 1.7;
          color: var(--apagado); max-width: 74ch;
        }

        .trampa {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 28px; margin-top: 28px;
        }
        .trampa-valor {
          font-family: var(--font-nunito); font-weight: 900; font-size: 40px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .trampa p { margin-top: 7px; font-size: 12.5px; line-height: 1.5; color: var(--apagado); }

        .tabla-envoltura { overflow-x: auto; margin-top: 26px; }
        .tabla-m { width: 100%; border-collapse: collapse; min-width: 640px; }
        .tabla-m th {
          text-align: left; font-size: 10.5px; font-weight: 500; letter-spacing: .12em;
          text-transform: uppercase; color: var(--apagado); white-space: nowrap;
          padding: 0 14px 11px 0; border-bottom: 1px solid var(--filete);
        }
        .tabla-m th.n, .tabla-m td.n { text-align: right; padding-right: 0; }
        .tabla-m td {
          padding: 14px 14px 14px 0; border-bottom: 1px solid var(--filete); font-size: 14px;
        }
        .tabla-m .ganador td { background: var(--superficie-2); }
        .tabla-m .marca {
          display: inline-block; margin-left: 10px; border-radius: 999px;
          background: var(--relleno); color: var(--sobre-relleno);
          font-size: 10.5px; padding: 3px 9px; vertical-align: 1px;
        }
        .barra-celda { width: 130px; padding-right: 14px !important; }
        .barra-celda i {
          display: block; height: 5px; border-radius: 999px; background: var(--color-dato-3);
        }

        .duelo {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 18px; margin-top: 26px;
        }
        .duelo-caja {
          border: 1px solid var(--filete); border-radius: var(--radius-tarjeta); padding: 22px;
        }
        .duelo-caja.gana { border-color: var(--filete-fuerte); }
        .duelo-caja dl { margin: 16px 0 0; display: grid; gap: 11px; }
        .duelo-caja div { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
        .duelo-caja dt { font-size: 12.5px; color: var(--apagado); }
        .duelo-caja dd {
          margin: 0; font-size: 16px; font-variant-numeric: tabular-nums lining-nums;
        }
        .duelo-caja .brecha {
          padding-top: 11px; border-top: 1px solid var(--filete);
        }
        .duelo-caja .brecha dd { font-size: 20px; font-family: var(--font-nunito); font-weight: 900; }
      `}</style>
    </div>
  )
}
