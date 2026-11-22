import { Link } from 'react-router-dom'
import { InterruptorTema } from '../componentes/InterruptorTema'
import { useSesion } from '../lib/sesion'

/**
 * La portada pública.
 *
 * Sigue el héroe fotográfico de Aira: fotografía a sangre con un velo oscuro
 * plano encima —plano, no degradado: el sistema prohíbe degradados—, titular en
 * serif centrado, dos pastillas y una franja de cifras bajo un filete.
 *
 * En la etapa 2 el orbe de partículas sustituye a la fotografía cuando el
 * equipo tiene WebGL, y la fotografía queda como respaldo.
 */
export function Portada() {
  const { sesion } = useSesion()

  return (
    <>
      <header className="sobre-foto portada-nav">
        <div
          className="pagina"
          style={{
            paddingBlock: 26,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 24,
          }}
        >
          <Link to="/" className="marca-portada">
            ReingresaIA
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <InterruptorTema sobreFoto />
            {sesion ? (
              <Link to="/app" className="pastilla pastilla-rellena pastilla-sm">
                Ir a la aplicación
              </Link>
            ) : (
              <Link to="/entrar" className="pastilla pastilla-rellena pastilla-sm">
                Entrar
              </Link>
            )}
          </div>
        </div>
      </header>

      <section className="heroe sobre-foto">
        <div className="heroe-foto" />
        <div className="heroe-velo" />
        <div className="pagina heroe-contenido">
          <h1>Saber quién va a volver</h1>
          <p className="heroe-bajada">
            Predicción de reingreso hospitalario a 30 días en pacientes con diabetes. Ciento
            treinta hospitales, nueve años de historia clínica, un modelo que ordena a quién
            llamar primero.
          </p>
          <div className="heroe-botones">
            <Link to={sesion ? '/app' : '/entrar'} className="pastilla pastilla-rellena">
              {sesion ? 'Ir a la aplicación' : 'Entrar'}
            </Link>
          </div>

          <div className="heroe-filete" />

          <div className="heroe-cifras">
            <Cifra valor="99.343" nota="Hospitalizaciones analizadas, tras excluir fallecimientos y cuidados paliativos" />
            <Cifra valor="69.990" nota="Pacientes distintos. La partición se hizo por paciente, nunca por hospitalización" />
            <Cifra valor="0,666" nota="ROC-AUC en prueba, dentro del rango del índice LACE y del HOSPITAL score" />
            <Cifra valor="3,78×" nota="Más reingresos en el 2 % de mayor riesgo que llamando al azar" />
          </div>
        </div>
      </section>

      <footer className="pagina" style={{ paddingBlock: '44px 64px' }}>
        <p style={{ fontSize: 12, color: 'var(--apagado)', lineHeight: 1.7, maxWidth: '70ch' }}>
          Universidad Popular del Cesar · Ingeniería de Sistemas · Grupo 04. Michel Custodes,
          Iván Güette y Maira Torres. Prototipo académico: no está validado para decisiones
          clínicas y no contiene datos de pacientes reales.
        </p>
      </footer>

      <style>{`
        .portada-nav { position: absolute; top: 0; left: 0; right: 0; z-index: 6; }
        .marca-portada {
          font-family: var(--font-serif);
          font-size: 22px;
          letter-spacing: -0.01em;
          color: var(--color-hueso);
          text-decoration: none;
        }
        .heroe {
          position: relative;
          min-height: 740px;
          display: flex;
          flex-direction: column;
          justify-content: flex-end;
          overflow: hidden;
          background: #05070b;
        }
        .heroe-foto {
          position: absolute;
          inset: 0;
          background-image: url('/imagenes/tierra-noche.webp');
          background-size: cover;
          background-position: 52% 42%;
        }
        /* Velo plano. Aira prohibe degradados: la fotografia carga el ambiente. */
        .heroe-velo { position: absolute; inset: 0; background: rgb(6 10 16 / 0.48); }
        .heroe-contenido {
          position: relative;
          z-index: 3;
          width: 100%;
          padding-block: 150px 56px;
          color: var(--color-hueso);
          text-align: center;
        }
        .heroe-contenido h1 { color: var(--color-hueso); max-width: 15ch; margin-inline: auto; }
        .heroe-bajada {
          color: rgb(250 250 251 / 0.84);
          max-width: 46ch;
          margin: 20px auto 0;
          font-size: 17px;
          line-height: 1.55;
        }
        .heroe-botones { display: flex; gap: 10px; justify-content: center; margin-top: 30px; }
        .heroe-filete { height: 1px; background: rgb(250 250 251 / 0.26); margin: 64px 0 40px; }
        .heroe-cifras { display: grid; grid-template-columns: repeat(4, 1fr); gap: 26px; }
        .heroe-cifra-valor {
          font-family: var(--font-serif);
          font-weight: 300;
          font-size: clamp(34px, 4.6vw, 56px);
          line-height: 1;
          letter-spacing: -0.02em;
          color: var(--color-hueso);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .heroe-cifra-nota {
          margin: 12px auto 0;
          font-size: 12.5px;
          line-height: 1.5;
          color: rgb(250 250 251 / 0.72);
          max-width: 21ch;
        }
        @media (width < 900px) {
          .heroe { min-height: 640px; }
          .heroe-contenido { padding-block: 120px 44px; }
          .heroe-cifras { grid-template-columns: repeat(2, 1fr); gap: 34px; }
        }
      `}</style>
    </>
  )
}

function Cifra({ valor, nota }: { valor: string; nota: string }) {
  return (
    <div>
      <div className="heroe-cifra-valor">{valor}</div>
      <p className="heroe-cifra-nota">{nota}</p>
    </div>
  )
}
