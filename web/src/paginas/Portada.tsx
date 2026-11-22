import { Suspense, lazy, useState } from 'react'
import { Link } from 'react-router-dom'
import { DeslizadorInfinito } from '../componentes/core/DeslizadorInfinito'
import { InterruptorTema } from '../componentes/InterruptorTema'
import { useSesion } from '../lib/sesion'
import { FORMAS, type Forma } from '../orbe/formas'

// three.js pesa. Se carga aparte para que el titular y las cifras aparezcan
// sin esperarlo, y si falla la portada sigue en pie.
const OrbeParticulas = lazy(() =>
  import('../orbe/OrbeParticulas').then((m) => ({ default: m.OrbeParticulas })),
)

const TECNOLOGIAS = [
  'Python',
  'scikit-learn',
  'pandas',
  'NumPy',
  'FastAPI',
  'React',
  'TypeScript',
  'Tailwind CSS',
  'three.js',
  'Docker',
]

export function Portada() {
  const { sesion } = useSesion()
  const [forma, setForma] = useState<Forma>('cohorte')
  const [orbeFallo, setOrbeFallo] = useState(false)
  const destino = sesion ? '/app' : '/entrar'

  return (
    <>
      <header className="sobre-foto portada-nav">
        <div className="pagina nav-fila">
          <Link to="/" className="marca-portada">
            ReingresaIA
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <InterruptorTema sobreFoto />
            <Link to={destino} className="pastilla pastilla-rellena pastilla-sm">
              {sesion ? 'Ir a la aplicación' : 'Entrar'}
            </Link>
          </div>
        </div>
      </header>

      {/* ---------------------------------------------------- héroe: el orbe */}
      <section className="heroe sobre-foto">
        <div className="pagina heroe-rejilla">
          <div className="heroe-texto">
            <p className="antetitulo" style={{ color: '#8a9a98' }}>
              Universidad Popular del Cesar · Grupo 04
            </p>
            <h1>Saber quién va a volver</h1>
            <p className="heroe-bajada">
              Predicción de reingreso hospitalario a 30 días en pacientes con diabetes. Ciento
              treinta hospitales, nueve años de historia clínica, un modelo que ordena a quién
              llamar primero.
            </p>
            <div className="heroe-botones">
              <Link to={destino} className="pastilla pastilla-rellena">
                {sesion ? 'Ir a la aplicación' : 'Entrar'}
              </Link>
            </div>
            <p className="heroe-pie">
              Cada punto es una hospitalización real del conjunto de prueba. En teal las que no
              alcanzan el umbral de alerta; en terracota las que sí. Las encendidas son las que
              de verdad volvieron al hospital.
            </p>
          </div>

          <div className="heroe-orbe">
            <div className="orbe-caja">
              {orbeFallo ? (
                <div className="orbe-respaldo" role="img" aria-label="La Tierra de noche vista desde el espacio" />
              ) : (
                <Suspense fallback={<div className="orbe-cargando" aria-hidden="true" />}>
                  <OrbeParticulas forma={forma} onFallo={() => setOrbeFallo(true)} />
                </Suspense>
              )}
            </div>
            {!orbeFallo && (
              <div className="orbe-formas" role="tablist" aria-label="Qué muestra el orbe">
                {FORMAS.map(({ id, etiqueta }) => (
                  <button
                    key={id}
                    type="button"
                    role="tab"
                    aria-selected={forma === id}
                    onClick={() => setForma(id)}
                    className={forma === id ? 'forma activa' : 'forma'}
                  >
                    {etiqueta}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------- cifras de la cohorte */}
      <section className="pagina seccion">
        <div className="cifras">
          <Cifra valor="99.343" nota="Hospitalizaciones analizadas, tras excluir fallecimientos y cuidados paliativos" />
          <Cifra valor="69.990" nota="Pacientes distintos. La partición se hizo por paciente, nunca por hospitalización" />
          <Cifra valor="0,666" nota="ROC-AUC en prueba, dentro del rango del índice LACE y del HOSPITAL score" />
          <Cifra valor="3,78×" nota="Más reingresos en el 2 % de mayor riesgo que llamando al azar" />
        </div>
      </section>

      {/* ------------------------------------------- comparación, sobre la foto */}
      <section className="comparacion sobre-foto">
        <div className="comparacion-foto" />
        <div className="comparacion-velo" />
        <div className="pagina comparacion-contenido">
          <p className="antetitulo" style={{ color: 'rgb(250 250 251 / 0.62)' }}>
            Validación externa · reingreso a 30 días
          </p>
          <h2>Cómo nos comparamos con lo que usan los hospitales</h2>
          <p className="comparacion-bajada">
            El índice LACE y el HOSPITAL score se aplican hoy en hospitales de Canadá, Estados
            Unidos y Europa para decidir a qué paciente llamar después del alta. Son el punto de
            referencia real, no un rival de laboratorio.
          </p>

          <div className="comparacion-filete" />

          <div className="cifras">
            <Cifra claro valor="0,666" nota="Nuestro modelo · Gradient Boosting" />
            <Cifra claro apagado valor="0,648" nota="Índice LACE · validación danesa" />
            <Cifra claro apagado valor="0,661" nota="HOSPITAL score · la misma validación" />
            <Cifra claro valor="0,0002" nota="Lo que nos falta para el techo de estos datos" />
          </div>

          <p className="comparacion-nota">
            Las tres primeras cifras vienen de poblaciones distintas, así que no es una
            comparación cabeza a cabeza: sitúan nuestro resultado dentro del rango publicado, no
            declaran un ganador.
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------- tecnologías */}
      <section className="seccion">
        <div className="pagina">
          <p className="antetitulo" style={{ textAlign: 'center' }}>
            Con qué está hecho
          </p>
        </div>
        <div style={{ marginTop: 28 }}>
          <DeslizadorInfinito>
            {TECNOLOGIAS.map((nombre) => (
              <span key={nombre} className="tecnologia">
                {nombre}
              </span>
            ))}
          </DeslizadorInfinito>
        </div>
      </section>

      <footer className="pagina" style={{ paddingBlock: '56px 72px', borderTop: '1px solid var(--filete)' }}>
        <p style={{ fontSize: 12, color: 'var(--apagado)', lineHeight: 1.7, maxWidth: '72ch' }}>
          Universidad Popular del Cesar · Ingeniería de Sistemas · Grupo 04. Michel Custodes,
          Iván Güette y Maira Torres. Prototipo académico: no está validado para decisiones
          clínicas y no contiene datos de pacientes reales.
        </p>
      </footer>

      <style>{`
        .portada-nav { position: absolute; top: 0; left: 0; right: 0; z-index: 6; }
        .nav-fila {
          padding-block: 26px;
          display: flex; align-items: center; justify-content: space-between; gap: 24px;
        }
        .marca-portada {
          font-family: var(--font-serif); font-size: 22px; letter-spacing: -0.01em;
          color: var(--color-hueso); text-decoration: none;
        }

        .heroe { position: relative; background: #05080c; overflow: hidden; }
        .heroe-rejilla {
          display: grid;
          grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
          gap: 48px;
          align-items: center;
          padding-block: 150px 90px;
          min-height: 700px;
        }
        .heroe-texto h1 { color: var(--color-hueso); margin-top: 16px; max-width: 13ch; }
        .heroe-bajada {
          color: rgb(250 250 251 / 0.8); max-width: 44ch; margin-top: 22px;
          font-size: 17px; line-height: 1.6;
        }
        .heroe-botones { display: flex; gap: 10px; margin-top: 32px; }
        .heroe-pie {
          margin-top: 44px; padding-top: 22px;
          border-top: 1px solid rgb(250 250 251 / 0.16);
          font-size: 12.5px; line-height: 1.65; color: rgb(250 250 251 / 0.56); max-width: 42ch;
        }

        .heroe-orbe { display: flex; flex-direction: column; align-items: center; gap: 18px; }
        .orbe-caja { width: 100%; max-width: 520px; aspect-ratio: 1; }
        .orbe-cargando { width: 100%; height: 100%; }
        .orbe-respaldo {
          width: 100%; height: 100%; border-radius: 50%;
          background-image: url('/imagenes/tierra-noche.webp');
          background-size: cover; background-position: center;
        }
        .orbe-formas {
          display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px;
          background: rgb(0 0 0 / 0.35); border: 1px solid rgb(250 250 251 / 0.12);
        }
        .forma {
          border: 0; background: none; cursor: pointer; border-radius: 999px;
          padding: 7px 14px; font-family: var(--font-sans); font-size: 11px;
          letter-spacing: 0.1em; text-transform: uppercase; color: #9fb0ae;
          transition: color .25s ease, background .25s ease; white-space: nowrap;
        }
        .forma:hover { color: var(--color-hueso); }
        .forma.activa { background: rgb(0 130 124 / 0.26); color: #d8fffb; }

        .seccion { padding-block: 104px; }
        .cifras { display: grid; grid-template-columns: repeat(4, 1fr); gap: 28px; }
        .cifra-valor {
          font-family: var(--font-serif); font-weight: 300;
          font-size: clamp(32px, 4.4vw, 54px); line-height: 1; letter-spacing: -0.02em;
          font-variant-numeric: tabular-nums lining-nums;
        }
        .cifra-nota { margin-top: 12px; font-size: 12.5px; line-height: 1.55; max-width: 23ch; }

        .comparacion { position: relative; overflow: hidden; background: #05080c; }
        .comparacion-foto {
          position: absolute; inset: 0;
          background-image: url('/imagenes/tierra-noche.webp');
          background-size: cover; background-position: 52% 38%;
        }
        /* Velo plano: Aira prohibe degradados, la fotografia carga el ambiente. */
        .comparacion-velo { position: absolute; inset: 0; background: rgb(5 9 14 / 0.62); }
        .comparacion-contenido { position: relative; z-index: 3; padding-block: 104px; }
        .comparacion-contenido h2 { color: var(--color-hueso); margin-top: 16px; max-width: 19ch; }
        .comparacion-bajada {
          margin-top: 20px; max-width: 58ch; font-size: 16px; line-height: 1.7;
          color: rgb(250 250 251 / 0.74);
        }
        .comparacion-filete {
          height: 1px; background: rgb(250 250 251 / 0.22); margin: 56px 0 40px;
        }
        .comparacion-nota {
          margin-top: 36px; font-size: 12px; line-height: 1.7;
          color: rgb(250 250 251 / 0.5); max-width: 76ch;
        }

        .tecnologia {
          font-family: var(--font-serif); font-weight: 300; font-size: 26px;
          letter-spacing: -0.02em; color: var(--apagado); white-space: nowrap;
        }

        @media (width < 980px) {
          .heroe-rejilla {
            grid-template-columns: 1fr; gap: 44px; padding-block: 120px 64px; min-height: 0;
          }
          .heroe-texto h1 { max-width: 100%; }
          .cifras { grid-template-columns: repeat(2, 1fr); gap: 34px; }
          .seccion { padding-block: 72px; }
          .comparacion-contenido { padding-block: 72px; }
        }
      `}</style>
    </>
  )
}

function Cifra({
  valor,
  nota,
  claro = false,
  apagado = false,
}: {
  valor: string
  nota: string
  claro?: boolean
  apagado?: boolean
}) {
  const colorValor = claro
    ? apagado
      ? 'rgb(250 250 251 / 0.62)'
      : 'var(--color-hueso)'
    : 'var(--tinta-fuerte)'
  const colorNota = claro ? 'rgb(250 250 251 / 0.66)' : 'var(--apagado)'

  return (
    <div>
      <div className="cifra-valor" style={{ color: colorValor }}>
        {valor}
      </div>
      <p className="cifra-nota" style={{ color: colorNota }}>
        {nota}
      </p>
    </div>
  )
}
