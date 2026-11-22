import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { TextoRevelado } from '../componentes/core/TextoRevelado'
import { api, ErrorApi } from '../lib/api'
import { conSigno, entero, numero } from '../lib/formato'

/**
 * Pantalla 15: el techo de los datos.
 *
 * La pregunta que casi nadie se hace: ¿el modelo rinde poco porque está mal
 * hecho, o porque los datos no traen más? Se puede medir, y se midió.
 *
 * Reproduce el método de Chowdhury y colegas (2026) sobre nuestros datos. Que
 * los dos diagnósticos de control salgan bien es lo que hace creíble el
 * resultado: con etiquetas barajadas el techo cae a la mitad, como debe.
 */

interface Canal {
  techo: number
  variables: number
}

interface Auditoria {
  cohorte: { filas: number; pacientes: number; prevalencia: number; balanceada: number }
  pliegues: number
  metodo: string
  completo: { techo: number; kappa: number; ic95: [number, number]; ba_lograda: number; brecha: number }
  piso_permutacion: { techo: number; exceso: number }
  subajuste: { curva: { fraccion: number; techo: number }[]; incremento_final: number; veredicto: string }
  canales: {
    administrativo: Canal
    clinico: Canal
    juntos: Canal
    complementariedad: number
  }
}

export function Techo() {
  const [a, setA] = useState<Auditoria | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .obtener<Auditoria>('/techo')
      .then(setA)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer el modelo" titulo="El techo de los datos" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  return (
    <div>
      <Encabezado
        antetitulo="Conocer el modelo"
        titulo="Hasta dónde se puede llegar con estos datos"
      >
        <p>
          La pregunta que casi nadie se hace: ¿el modelo rinde poco porque está mal hecho, o
          porque los datos no traen más? Se puede medir, y lo medimos.
        </p>
      </Encabezado>

      {!a && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {a && (
        <>
          <section className="bloque-t destacado">
            <p className="antetitulo">El resultado</p>
            <h2>El modelo ya está en el techo</h2>
            <TextoRevelado className="texto-t" porPalabra={0.015}>
              El techo es la exactitud balanceada que alcanzaría un oráculo que conociera la
              probabilidad verdadera de reingreso con las columnas que tenemos. Ningún modelo,
              por bueno que sea, puede pasar de ahí.
            </TextoRevelado>
            <div className="cifras-t">
              <Dato
                v={numero(a.completo.techo, 4)}
                n={`techo estimado. Intervalo de ${numero(a.completo.ic95[0], 4)} a ${numero(a.completo.ic95[1], 4)}`}
              />
              <Dato v={numero(a.completo.ba_lograda, 4)} n="lo que logra nuestro modelo" />
              <Dato v={conSigno(a.completo.brecha, 4)} n="la brecha entre los dos" />
            </div>
            <p className="texto-t">
              La brecha salió <strong>negativa</strong>, y eso tiene una lectura precisa: el
              modelo ya extrae toda la información que estas columnas permiten, y el techo
              estimado es una cota inferior del techo verdadero. Queda margen, pero pequeño.
            </p>
          </section>

          <section className="bloque-t">
            <h2>Por qué creerle a esta medición</h2>
            <p className="texto-t">
              Un método que mide techos puede dar cualquier número si está mal hecho. Por eso
              trae dos controles, y los dos salieron como debían.
            </p>
            <div className="controles">
              <div className="control">
                <p className="antetitulo">Control 1 · etiquetas barajadas</p>
                <div className="control-v">{numero(a.piso_permutacion.techo, 4)}</div>
                <p>
                  Se repite todo con las etiquetas revueltas al azar, donde no hay nada que
                  aprender. El techo debería caer a 0,5 y cayó a{' '}
                  {numero(a.piso_permutacion.techo, 4)}: se pasa apenas{' '}
                  {numero(a.piso_permutacion.exceso, 4)}. Si hubiera salido alto, el estimador
                  estaría inventando señal donde no hay.
                </p>
              </div>
              <div className="control">
                <p className="antetitulo">Control 2 · curva de subajuste</p>
                <div className="control-v">{conSigno(a.subajuste.incremento_final, 4)}</div>
                <p>
                  Se reentrena con un cuarto, la mitad, tres cuartos y todos los datos. Si el
                  techo todavía sube al final, no se ha estabilizado. Subió{' '}
                  {numero(a.subajuste.incremento_final, 4)}, así que se reporta como{' '}
                  <strong>{a.subajuste.veredicto}</strong> y no como el techo definitivo.
                </p>
              </div>
            </div>
            <div className="curva-sub">
              {a.subajuste.curva.map((p) => (
                <div key={p.fraccion}>
                  <div className="curva-v">{numero(p.techo, 4)}</div>
                  <p>con el {Math.round(p.fraccion * 100)} % de los datos</p>
                </div>
              ))}
            </div>
          </section>

          <section className="bloque-t destacado">
            <p className="antetitulo">El hallazgo incómodo</p>
            <h2>Qué dato nos está faltando</h2>
            <TextoRevelado className="texto-t" porPalabra={0.015}>
              Se separaron las columnas en dos canales y se midió el techo de cada uno por
              aparte. El resultado no es el que esperábamos y es el más útil del trabajo.
            </TextoRevelado>
            <div className="tabla-envoltura">
              <table className="tabla-t">
                <thead>
                  <tr>
                    <th>Canal</th>
                    <th className="n">Variables</th>
                    <th className="n">Techo</th>
                    <th>Qué contiene</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Administrativo</td>
                    <td className="n">{a.canales.administrativo.variables}</td>
                    <td className="n">{numero(a.canales.administrativo.techo, 4)}</td>
                    <td className="que">
                      Edad, sexo, por dónde entró, a dónde salió, cuánto se quedó, cuántas veces
                      había venido antes
                    </td>
                  </tr>
                  <tr>
                    <td>Clínico</td>
                    <td className="n">{a.canales.clinico.variables}</td>
                    <td className="n">{numero(a.canales.clinico.techo, 4)}</td>
                    <td className="que">
                      Laboratorios, hemoglobina glicosilada, diagnósticos, los dieciséis
                      antidiabéticos, cambios de medicación
                    </td>
                  </tr>
                  <tr className="juntos">
                    <td>
                      <strong>Los dos juntos</strong>
                    </td>
                    <td className="n">{a.canales.juntos.variables}</td>
                    <td className="n">
                      <strong>{numero(a.canales.juntos.techo, 4)}</strong>
                    </td>
                    <td className="que">
                      Complementariedad: {conSigno(a.canales.complementariedad, 4)}. Sumarlos no
                      aporta nada
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="texto-t">
              Las {a.canales.clinico.variables} variables clínicas no agregan nada que las{' '}
              {a.canales.administrativo.variables} administrativas no dijeran ya. Todo lo que el
              modelo sabe cabe en: quién es el paciente, por dónde entró, a dónde salió y
              cuántas veces había vuelto.
            </p>
            <p className="nota-t">
              Con la trampa incluida, porque alguien la va a notar: el canal administrativo
              incluye las hospitalizaciones previas, que es la variable más fuerte de todas, y
              eso explica buena parte de su ventaja.
            </p>
          </section>

          <section className="bloque-t">
            <h2>Qué hacer con esto</h2>
            <p className="texto-t">
              La conclusión práctica no es cambiar de algoritmo. Para subir el techo habría que
              empezar a registrar lo que hoy no está en ninguna columna: si el paciente tiene
              quién lo cuide, si puede pagar los medicamentos, si entendió las instrucciones del
              alta, si tiene cómo llegar al control.
            </p>
            <p className="texto-t">
              Eso es una recomendación para el hospital, no para el equipo de datos. Y es,
              probablemente, lo más valioso que este trabajo puede decir.
            </p>
          </section>

          <p className="nota-t">
            Método: {a.metodo}. Medido sobre una muestra balanceada de{' '}
            {entero(a.cohorte.balanceada)} filas de las {entero(a.cohorte.filas)} de la cohorte,
            con validación cruzada de {a.pliegues} pliegues agrupada por paciente. El intervalo
            viene de remuestrear pacientes enteros, no filas sueltas: remuestrear filas daría un
            intervalo más estrecho de lo que corresponde.
          </p>
        </>
      )}

      <style>{`
        .bloque-t { padding-block: 40px; border-top: 1px solid var(--filete); }
        .bloque-t:first-of-type { border-top: 0; padding-top: 28px; }
        .bloque-t h2 { font-size: 28px; margin-top: 8px; max-width: 24ch; }
        .bloque-t.destacado {
          background: var(--superficie); border-radius: var(--radius-tarjeta);
          padding: 34px; border-top: 0; margin-top: 28px;
        }
        .texto-t { margin-top: 16px; font-size: 15.5px; line-height: 1.7; color: var(--apagado); max-width: 68ch; }
        .texto-t strong { font-weight: 600; color: var(--tinta); }
        .nota-t { margin-top: 24px; font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 76ch; }

        .cifras-t { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 26px; margin-top: 28px; }
        .dato-t-v { font-family: var(--font-serif); font-weight: 300; font-size: 40px; letter-spacing: -0.02em; color: var(--tinta-fuerte); font-variant-numeric: tabular-nums lining-nums; }
        .dato-t-n { margin-top: 7px; font-size: 12px; line-height: 1.5; color: var(--apagado); }

        .controles { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px; margin-top: 26px; }
        .control { border: 1px solid var(--filete); border-radius: var(--radius-tarjeta); padding: 22px; }
        .control-v { font-family: var(--font-serif); font-weight: 300; font-size: 34px; margin-top: 10px; letter-spacing: -0.02em; color: var(--tinta-fuerte); font-variant-numeric: tabular-nums lining-nums; }
        .control p:last-child { margin-top: 12px; font-size: 13px; line-height: 1.65; color: var(--apagado); }
        .control strong { font-weight: 600; color: var(--tinta); }

        .curva-sub { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 20px; margin-top: 26px; }
        .curva-v { font-family: var(--font-serif); font-weight: 300; font-size: 24px; letter-spacing: -0.02em; font-variant-numeric: tabular-nums lining-nums; }
        .curva-sub p { margin-top: 5px; font-size: 11.5px; color: var(--apagado); }

        .tabla-envoltura { overflow-x: auto; margin-top: 26px; }
        .tabla-t { width: 100%; border-collapse: collapse; min-width: 640px; }
        .tabla-t th { text-align: left; font-size: 10.5px; font-weight: 500; letter-spacing: .12em; text-transform: uppercase; color: var(--apagado); padding: 0 14px 11px 0; border-bottom: 1px solid var(--filete); }
        .tabla-t th.n, .tabla-t td.n { text-align: right; padding-right: 14px; }
        .tabla-t td { padding: 14px 14px 14px 0; border-bottom: 1px solid var(--filete); font-size: 14px; }
        .tabla-t td.que { font-size: 12.5px; color: var(--apagado); line-height: 1.5; white-space: normal; }
        .tabla-t .juntos td { background: var(--superficie-2); }
      `}</style>
    </div>
  )
}

function Dato({ v, n }: { v: string; n: string }) {
  return (
    <div>
      <div className="dato-t-v">{v}</div>
      <p className="dato-t-n">{n}</p>
    </div>
  )
}
