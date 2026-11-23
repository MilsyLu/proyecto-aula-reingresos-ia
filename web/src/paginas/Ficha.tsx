import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { numero, porcentaje } from '../lib/formato'

/**
 * Pantalla 16: la ficha del modelo.
 *
 * Una ficha técnica sirve para dos cosas: que alguien pueda reproducir lo que
 * se hizo, y que sepa para qué NO sirve. La segunda parte es la que casi nunca
 * se escribe, y aquí ocupa tanto espacio como la primera.
 */

interface Datos {
  hiperparametros: Record<string, number | string | null>
  metricas: Record<string, number>
  umbral: { umbral: number; criterio: string; recall_prueba: number; precision_prueba: number }
  metas: { 'meta de la Fase 1': string; cumple: string }[]
}

const NOMBRES: Record<string, string> = {
  learning_rate: 'Tasa de aprendizaje',
  max_leaf_nodes: 'Hojas máximas por árbol',
  min_samples_leaf: 'Pacientes mínimos por hoja',
  max_features: 'Fracción de variables por división',
  l2_regularization: 'Regularización L2',
  class_weight: 'Peso de las clases',
}

const PARA_QUE: Record<string, string> = {
  learning_rate: 'Cuánto corrige cada árbol. Baja y lenta generaliza mejor.',
  max_leaf_nodes: 'Qué tan detallado puede ser cada árbol. Quince es poco a propósito.',
  min_samples_leaf: 'Impide que una hoja se arme con un puñado de casos.',
  max_features: 'Cada división ve solo parte de las columnas, para no depender de una.',
  l2_regularization: 'Penaliza las predicciones extremas.',
  class_weight: 'Sin ajustar: balancear no mejoró nada en las pruebas.',
}

export function Ficha() {
  const [d, setD] = useState<Datos | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Datos>('/ficha')
      .then(setD)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer el modelo" titulo="Ficha del modelo" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Conocer el modelo" titulo="Ficha del modelo">
        <p>
          Qué es, cómo se entrenó y para qué no sirve. La última parte es la que casi nunca se
          escribe, y aquí ocupa tanto espacio como las otras dos.
        </p>
      </Encabezado>

      {!d && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {d && (
        <>
          <section className="bloque-f">
            <h2>Identificación</h2>
            <dl className="ficha-dl">
              <Fila t="Nombre" v="ReingresaIA — modelo oficial" />
              <Fila t="Algoritmo" v="HistGradientBoostingClassifier de scikit-learn" />
              <Fila t="Árboles" v="135, detenidos por parada temprana sobre un máximo de 400" />
              <Fila t="Qué predice" v="Probabilidad de reingreso hospitalario antes de 30 días" />
              <Fila t="Entradas" v="50 variables por hospitalización, 17 numéricas y 33 categóricas" />
              <Fila
                t="Datos de entrenamiento"
                v="130 hospitales de Estados Unidos, 1999-2008. 99.343 hospitalizaciones de 69.990 personas"
              />
              <Fila t="Partición" v="60 / 20 / 20 agrupada por paciente, nunca por hospitalización" />
              <Fila t="Versiones" v="scikit-learn 1.9.1, pandas 3.0.5, numpy 2.5.2" />
            </dl>
          </section>

          <section className="bloque-f">
            <h2>Configuración</h2>
            <p className="texto-f">
              Elegida en validación cruzada entre varias combinaciones. No ganó la de mejor
              puntaje sino la que menos se memorizaba los datos.
            </p>
            <div className="tabla-envoltura">
              <table className="tabla-f">
                <tbody>
                  {Object.entries(d.hiperparametros).map(([clave, valor]) => (
                    <tr key={clave}>
                      <td className="param">
                        {NOMBRES[clave] ?? clave}
                        <em>{clave}</em>
                      </td>
                      <td className="valor">
                        {valor === null ? 'sin ajustar' : String(valor)}
                      </td>
                      <td className="explica">{PARA_QUE[clave] ?? ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="bloque-f">
            <h2>Desempeño y umbral</h2>
            <div className="cifras-f">
              <Dato v={numero(d.metricas.AP, 4)} n="Average precision en prueba" />
              <Dato v={numero(d.metricas.ROC_AUC, 4)} n="ROC-AUC en prueba" />
              <Dato v={porcentaje(d.metricas.recall)} n="De los que reingresan, cuántos detecta" />
              <Dato v={porcentaje(d.metricas.precision)} n="De los que alerta, cuántos reingresan" />
              <Dato v={numero(d.metricas.Brier, 4)} n="Brier. Mide qué tan bien calibrado está" />
              <Dato v={porcentaje(d.umbral.umbral)} n="Umbral de alerta del programa" />
            </div>
            <p className="texto-f">
              El umbral se eligió con un criterio escrito antes de verlo: {d.umbral.criterio}. No
              es una propiedad del modelo sino una decisión de política sanitaria, y por eso la
              aplicación solo deja cambiarlo desde el perfil de coordinación.
            </p>
          </section>

          <section className="bloque-f destacado">
            <h2>Para qué NO sirve</h2>
            <ul className="prohibiciones">
              <li>
                <strong>No decide altas.</strong> Un paciente que el modelo no señala puede estar
                grave. Lo único que dice es que, en promedio, los de arriba vuelven más.
              </li>
              <li>
                <strong>No sugiere tratamientos</strong> ni sustituye una valoración clínica.
              </li>
              <li>
                <strong>No sirve para negar o restringir atención.</strong> Entrar en la lista
                significa recibir una llamada de seguimiento, nunca lo contrario.
              </li>
              <li>
                <strong>No está validado para uso clínico.</strong> Es un prototipo académico.
                Usarlo de verdad exigiría validación prospectiva en la institución y con datos
                locales.
              </li>
              <li>
                <strong>No sirve fuera de su población.</strong> Son pacientes diabéticos de
                hospitales estadounidenses de hace más de quince años. Otro sistema de salud
                daría cifras distintas.
              </li>
              <li>
                <strong>No trata igual a todas las edades.</strong> Alerta sobre el 51 % de los
                mayores de 80 y sobre el 30 % de los menores de 50, aunque su riesgo real es
                casi el mismo.
              </li>
            </ul>
          </section>

          <section className="bloque-f">
            <h2>Metas de la Fase 1</h2>
            <div className="metas-f">
              {d.metas.map((m) => {
                const cumple = m.cumple.trim().toUpperCase() === 'SI'
                return (
                  <div key={m['meta de la Fase 1']} className={cumple ? 'meta-f' : 'meta-f falla'}>
                    <span>{m['meta de la Fase 1']}</span>
                    <span className="estado-f">{cumple ? 'cumple' : 'no cumple'}</span>
                  </div>
                )
              })}
            </div>
            <p className="nota-f">
              Tres de cuatro. La precisión se quedó en 0,178 frente a la meta de 0,20, y se deja
              escrito así en vez de cambiar la meta después de ver el resultado.
            </p>
          </section>

          <p className="nota-f">
            Universidad Popular del Cesar · Ingeniería de Sistemas · Grupo 04. Michel Custodes,
            Iván Güette y Maira Torres. Los datos provienen del conjunto público Diabetes
            130-US Hospitals, sin información identificable de pacientes.
          </p>
        </>
      )}

      <style>{`
        .bloque-f { padding-block: 38px; border-top: 1px solid var(--filete); }
        .bloque-f:first-of-type { border-top: 0; padding-top: 28px; }
        .bloque-f h2 { font-size: 26px; }
        .bloque-f.destacado {
          background: var(--superficie); border-radius: var(--radius-tarjeta);
          padding: 32px; border-top: 0; margin-top: 28px;
        }
        .texto-f { margin-top: 14px; font-size: 15px; line-height: 1.7; color: var(--apagado); max-width: 70ch; }
        .nota-f { margin-top: 22px; font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 76ch; }

        .ficha-dl { margin: 22px 0 0; display: grid; gap: 0; }
        .ficha-dl > div {
          display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 20px;
          padding-block: 13px; border-bottom: 1px solid var(--filete);
        }
        .ficha-dl dt { font-size: 12.5px; color: var(--apagado); }
        .ficha-dl dd { margin: 0; font-size: 14.5px; line-height: 1.55; }

        .tabla-envoltura { overflow-x: auto; margin-top: 22px; }
        .tabla-f { width: 100%; border-collapse: collapse; min-width: 620px; }
        .tabla-f td { padding: 14px 16px 14px 0; border-bottom: 1px solid var(--filete); font-size: 14px; vertical-align: top; }
        .tabla-f .param { width: 240px; }
        .tabla-f .param em { display: block; font-style: normal; font-size: 11px; color: var(--apagado); margin-top: 3px; }
        .tabla-f .valor { width: 120px; font-variant-numeric: tabular-nums lining-nums; }
        .tabla-f .explica { font-size: 12.5px; color: var(--apagado); line-height: 1.55; }

        .cifras-f { display: grid; grid-template-columns: repeat(auto-fit, minmax(165px, 1fr)); gap: 24px; margin-top: 24px; }
        .dato-f-v { font-family: var(--font-nunito); font-weight: 900; font-size: 30px; letter-spacing: -0.02em; color: var(--tinta-fuerte); font-variant-numeric: tabular-nums lining-nums; }
        .dato-f-n { margin-top: 6px; font-size: 11.5px; line-height: 1.5; color: var(--apagado); }

        .prohibiciones { margin: 20px 0 0; padding-left: 20px; display: grid; gap: 14px; max-width: 72ch; }
        .prohibiciones li { font-size: 14.5px; line-height: 1.7; color: var(--apagado); }
        .prohibiciones strong { font-weight: 600; color: var(--tinta); }

        .metas-f { margin-top: 20px; display: grid; gap: 0; max-width: 60ch; }
        .meta-f {
          display: flex; justify-content: space-between; gap: 16px; align-items: baseline;
          padding-block: 12px; border-bottom: 1px solid var(--filete); font-size: 14px;
        }
        .estado-f {
          font-size: 10.5px; font-weight: 500; letter-spacing: .14em;
          text-transform: uppercase; color: var(--apagado); white-space: nowrap;
        }
        .meta-f.falla .estado-f { color: var(--color-dato-4); }
      `}</style>
    </div>
  )
}

function Fila({ t, v }: { t: string; v: string }) {
  return (
    <div>
      <dt>{t}</dt>
      <dd>{v}</dd>
    </div>
  )
}

function Dato({ v, n }: { v: string; n: string }) {
  return (
    <div>
      <div className="dato-f-v">{v}</div>
      <p className="dato-f-n">{n}</p>
    </div>
  )
}
