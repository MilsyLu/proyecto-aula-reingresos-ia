import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { TextoRevelado } from '../componentes/core/TextoRevelado'
import { api, ErrorApi } from '../lib/api'
import { entero, porcentaje } from '../lib/formato'

/**
 * Pantalla 8: de dónde salen los datos.
 *
 * Tres cosas que cualquiera debería poder preguntar y que casi nunca se
 * responden: de dónde vienen, a quién se dejó fuera, y cómo se partieron.
 *
 * La tercera es la que más importa. Partir por hospitalización en vez de por
 * paciente es el error más común en trabajos sobre este conjunto de datos, y
 * no avisa: el modelo reconoce a la misma persona en la prueba y el resultado
 * sale inflado.
 */

interface Particion {
  filas: number
  pacientes: number
  positivos: number
  prevalencia: number
}

interface Resumen {
  patrones_originales: number
  pacientes_originales: number
  columnas_originales: number
  excluidos: number
  patrones: number
  pacientes: number
  positivos: number
  prevalencia: number
  predictores: number
  numericas: number
  categoricas: number
  pacientes_con_una: number
  pacientes_con_varias: number
  max_hospitalizaciones: number
  particion: Record<string, Particion>
}

const ORDEN = ['entrenamiento', 'validacion', 'prueba']
const NOMBRES: Record<string, string> = {
  entrenamiento: 'Entrenamiento',
  validacion: 'Validación',
  prueba: 'Prueba',
}
const PARA_QUE: Record<string, string> = {
  entrenamiento: 'Con estos aprendió el modelo.',
  validacion: 'Con estos se eligió la configuración y el umbral.',
  prueba: 'Estos se miraron una sola vez, al final.',
}

export function Cohorte() {
  const [r, setR] = useState<Resumen | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Resumen>('/cohorte')
      .then(setR)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer los datos" titulo="De dónde salen los datos" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado antetitulo="Conocer los datos" titulo="De dónde salen los datos">
        <p>
          Quién está en la cohorte, a quién se dejó fuera y por qué, y cómo se repartieron los
          pacientes entre entrenamiento, validación y prueba.
        </p>
      </Encabezado>

      {!r && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {r && (
        <div className="bloques">
          <section>
            <h2>El archivo original</h2>
            <TextoRevelado className="bloque-texto" porPalabra={0.015}>
              Es un conjunto público: ciento treinta hospitales de Estados Unidos entre 1999 y
              2008. Cada fila es una hospitalización de una persona con diabetes, no una
              persona: eso es lo primero que hay que entender, y de ahí sale todo lo demás.
            </TextoRevelado>
            <div className="cifras-bloque">
              <Cifra valor={entero(r.patrones_originales)} nota="hospitalizaciones en el archivo" />
              <Cifra valor={entero(r.pacientes_originales)} nota="personas distintas en esas filas" />
              <Cifra valor={entero(r.columnas_originales)} nota="columnas por hospitalización" />
            </div>
          </section>

          <section>
            <h2>A quién se dejó fuera</h2>
            <TextoRevelado className="bloque-texto" porPalabra={0.015}>
              Se excluyeron los egresos por fallecimiento y por cuidados paliativos. No es una
              decisión estadística sino lógica: esas personas no pueden reingresar, y dejarlas
              dentro le enseña al modelo a predecir algo que no existe.
            </TextoRevelado>
            <div className="cifras-bloque">
              <Cifra valor={entero(r.excluidos)} nota="hospitalizaciones excluidas" />
              <Cifra valor={entero(r.patrones)} nota="hospitalizaciones que quedaron" />
              <Cifra valor={entero(r.pacientes)} nota="personas distintas" />
            </div>
          </section>

          <section>
            <h2>Una persona, varias hospitalizaciones</h2>
            <TextoRevelado className="bloque-texto" porPalabra={0.015}>
              Dieciséis mil personas aparecen más de una vez, y una llegó a cuarenta
              hospitalizaciones. Ignorar eso es el error más común en los trabajos sobre este
              conjunto de datos: si las visitas de alguien caen a lado y lado de la partición,
              el modelo lo reconoce en la prueba y el resultado sale inflado sin avisar.
            </TextoRevelado>
            <div className="cifras-bloque">
              <Cifra valor={entero(r.pacientes_con_una)} nota="personas con una sola hospitalización" />
              <Cifra valor={entero(r.pacientes_con_varias)} nota="personas con más de una" />
              <Cifra valor={entero(r.max_hospitalizaciones)} nota="el máximo de una sola persona" />
            </div>
          </section>

          <section>
            <h2>Cómo se repartió</h2>
            <TextoRevelado className="bloque-texto" porPalabra={0.015}>
              Por paciente, nunca por hospitalización. Nadie aparece en dos conjuntos. Que las
              tres prevalencias salgan casi idénticas no es casualidad ni suerte: es la señal de
              que el reparto quedó bien hecho.
            </TextoRevelado>
            <div className="tabla-envoltura">
              <table className="tabla-particion">
                <thead>
                  <tr>
                    <th>Conjunto</th>
                    <th className="n">Hospitalizaciones</th>
                    <th className="n">Personas</th>
                    <th className="n">Reingresaron</th>
                    <th className="n">Prevalencia</th>
                  </tr>
                </thead>
                <tbody>
                  {ORDEN.filter((k) => r.particion[k]).map((k) => {
                    const p = r.particion[k]
                    return (
                      <tr key={k}>
                        <td>
                          <strong>{NOMBRES[k]}</strong>
                          <span className="para-que">{PARA_QUE[k]}</span>
                        </td>
                        <td className="n">{entero(p.filas)}</td>
                        <td className="n">{entero(p.pacientes)}</td>
                        <td className="n">{entero(p.positivos)}</td>
                        <td className="n">{porcentaje(p.prevalencia, 2)}</td>
                      </tr>
                    )
                  })}
                  <tr className="total">
                    <td>
                      <strong>Toda la cohorte</strong>
                    </td>
                    <td className="n">{entero(r.patrones)}</td>
                    <td className="n">{entero(r.pacientes)}</td>
                    <td className="n">{entero(r.positivos)}</td>
                    <td className="n">{porcentaje(r.prevalencia, 2)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2>Qué mira el modelo</h2>
            <TextoRevelado className="bloque-texto" porPalabra={0.015}>
              Cincuenta variables por hospitalización. Doce de ellas no venían en el archivo: se
              calcularon a partir de las otras, porque el modelo no ve lo que uno no le enseña a
              mirar.
            </TextoRevelado>
            <div className="cifras-bloque">
              <Cifra valor={entero(r.predictores)} nota="variables en total" />
              <Cifra valor={entero(r.numericas)} nota="numéricas" />
              <Cifra valor={entero(r.categoricas)} nota="categóricas, de texto" />
            </div>
          </section>

          <p className="cierre">
            Esa prevalencia de {porcentaje(r.prevalencia, 2)} es la cifra que más se malinterpreta
            del proyecto. No es lo que acierta el modelo: es cuánta gente reingresa. Salió de
            contar casos reales, y sería la misma con cualquier otro modelo.
          </p>
        </div>
      )}

      <style>{`
        .bloques { margin-top: 20px; }
        .bloques section { padding-block: 38px; border-top: 1px solid var(--filete); }
        .bloques section:first-child { border-top: 0; padding-top: 24px; }
        .bloques h2 { font-size: 26px; }
        .bloque-texto {
          margin-top: 12px; font-size: 15.5px; line-height: 1.7;
          color: var(--apagado); max-width: 66ch;
        }
        .cifras-bloque {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 26px; margin-top: 26px; max-width: 760px;
        }
        .cifra-bloque-valor {
          font-family: var(--font-nunito); font-weight: 900; font-size: 34px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .cifra-bloque-nota { margin-top: 7px; font-size: 12.5px; line-height: 1.5; color: var(--apagado); }

        .tabla-envoltura { overflow-x: auto; margin-top: 26px; }
        .tabla-particion { width: 100%; border-collapse: collapse; min-width: 620px; }
        .tabla-particion th {
          text-align: left; font-size: 11px; font-weight: 500; letter-spacing: .14em;
          text-transform: uppercase; color: var(--apagado);
          padding: 0 14px 12px 0; border-bottom: 1px solid var(--filete);
        }
        .tabla-particion th.n, .tabla-particion td.n { text-align: right; padding-right: 0; }
        .tabla-particion td {
          padding: 15px 14px 15px 0; border-bottom: 1px solid var(--filete); font-size: 14.5px;
        }
        .tabla-particion .para-que {
          display: block; font-size: 12px; color: var(--apagado); margin-top: 4px; font-weight: 400;
        }
        .tabla-particion .total td { border-bottom: 0; }
        .tabla-particion .total strong { font-weight: 600; }

        .cierre {
          margin-top: 40px; padding-top: 24px; border-top: 1px solid var(--filete);
          font-size: 15px; line-height: 1.75; color: var(--apagado); max-width: 74ch;
        }
      `}</style>
    </div>
  )
}

function Cifra({ valor, nota }: { valor: string; nota: string }) {
  return (
    <div>
      <div className="cifra-bloque-valor">{valor}</div>
      <p className="cifra-bloque-nota">{nota}</p>
    </div>
  )
}
