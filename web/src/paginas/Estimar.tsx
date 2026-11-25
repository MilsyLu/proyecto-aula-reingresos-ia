import { useCallback, useRef, useState } from 'react'
import { UserPlus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Encabezado } from '../componentes/Encabezado'
import { ChatAsistente } from '../componentes/ChatAsistente'
import { FormularioPaciente } from '../componentes/FormularioPaciente'
import { RegistrarPaciente } from '../componentes/RegistrarPaciente'
import { api, ErrorApi } from '../lib/api'
import { porcentaje } from '../lib/formato'
import type { Estimacion } from '../lib/tiposModelo'
import { useSesion } from '../lib/sesion'
import type { PacienteSeguido } from '../lib/tiposSeguimiento'
import { usarPaciente } from '../lib/usarPaciente'

/**
 * Pantalla 3: estimar un paciente.
 *
 * El riesgo se recalcula solo al cambiar un campo, con una pequeña espera para
 * no disparar una petición por cada tecla. Que el número se mueva mientras uno
 * escribe es lo que convierte el formulario en algo que se entiende: se ve qué
 * dato pesa y cuál no mueve nada.
 */
export function Estimar() {
  const { opciones, valores, cambiar, restablecer, paraEnviar, fueraDeRango, error } =
    usarPaciente()
  const [resultado, setResultado] = useState<Estimacion | null>(null)
  const [calculando, setCalculando] = useState(false)
  const [fallo, setFallo] = useState<string | null>(null)
  const [registrando, setRegistrando] = useState(false)
  const [registrado, setRegistrado] = useState<PacienteSeguido | null>(null)
  const peticion = useRef(0)
  const { sesion } = useSesion()
  const puedeSeguir = (sesion?.permisos ?? []).includes('Seguimiento')

  const estimar = useCallback(async (entradas: Record<string, string | number>) => {
    const mia = ++peticion.current
    setCalculando(true)
    try {
      const datos = await api.enviar<Estimacion>('/estimar', entradas)
      // Si mientras tanto salió otra petición, esta ya no manda: sin esto, una
      // respuesta lenta puede pisar a una más nueva y mostrar un riesgo que no
      // corresponde a lo que está escrito en pantalla.
      if (mia === peticion.current) {
        setResultado(datos)
        setFallo(null)
        // Si se cambia un dato, el aviso de "ya quedo registrado" deja de
        // corresponder a lo que hay en pantalla.
        setRegistrado(null)
      }
    } catch (e) {
      if (mia === peticion.current) {
        setFallo(e instanceof ErrorApi ? e.message : 'No se pudo estimar.')
      }
    } finally {
      if (mia === peticion.current) setCalculando(false)
    }
  }, [])

  function cambiarDato(campo: string, valor: string | number) {
    peticion.current += 1
    cambiar(campo, valor)
    setResultado(null)
    setRegistrado(null)
    setFallo(null)
    setCalculando(false)
  }


  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Trabajar" titulo="Estimar un paciente" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }


  /** «Prioridad alta / media / baja», la pastilla amarilla del diseño. */
  function prioridad(e: Estimacion): string {
    if (e.supera) return 'Prioridad alta'
    if (e.probabilidad >= e.umbral / 2) return 'Prioridad media'
    return 'Prioridad baja'
  }


  return (
    <div>
      <Encabezado
        antetitulo="Apoyo a la decisión clínica"
        titulo="Estimar un paciente"
        acciones={
          opciones ? (
            <button
              type="button"
              className="pastilla pastilla-contorno pastilla-sm"
              onClick={() => { peticion.current += 1; restablecer(); setResultado(null); setRegistrado(null); setCalculando(false) }}
            >
              Limpiar formulario
            </button>
          ) : null
        }
      >
        <p>
          Complete los datos de la hospitalización y pulse «Calcular riesgo». Después podrá registrar el paciente para seguimiento.
        </p>
      </Encabezado>

      <div className="estimar-columnas">
        <section className="tarjeta">
          <div className="cabeza-tarjeta">
            <div>
              <h2 className="tarjeta-titulo">Datos del alta</h2>
              <p className="tarjeta-sub">
                Información necesaria para la estimación de reingreso
              </p>
            </div>
          </div>

          <div className="cuerpo-tarjeta">
            {opciones ? (
              <FormularioPaciente
                campos={opciones.campos}
                valores={valores}
                onCambio={cambiarDato}
                deshabilitado={false}
              />
            ) : (
              <p className="antetitulo">Cargando el formulario</p>
            )}

            <button type="button" className="pastilla pastilla-rellena"
              style={{ marginTop: 20, width: '100%', justifyContent: 'center' }}
              disabled={!opciones || calculando || fueraDeRango.length > 0}
              onClick={() => estimar(paraEnviar)}>
              {calculando ? 'Calculando…' : 'Calcular riesgo'}
            </button>
            {fueraDeRango.length > 0 && (
              <p className="aviso-rango">
                Revise los campos fuera de rango antes de calcular.
              </p>
            )}
            {fallo && <p className="aviso-rango">{fallo}</p>}
            {calculando && !resultado && <p className="antetitulo">Calculando</p>}

            <p className="nota-prototipo">
              Prototipo académico. Esta cifra ordena a quién llamar primero; no decide altas ni
              tratamientos.
            </p>
          </div>
        </section>

        <div className="columna-lado">
          {resultado && (
            <aside className="tarjeta tarjeta-resultado">
              <div className="tarjeta-pad">
                <div className={`resultado${resultado.supera ? ' alerta' : ''}`}>
                  <div className="circulo" aria-live="polite">
                    {porcentaje(resultado.probabilidad)}
                  </div>
                  <div className="resultado-texto">
                    <h3>Probabilidad estimada de reingreso a 30 días</h3>
                    <p>Estimación orientativa basada en los datos registrados; no es un diagnóstico.</p>
                    <p className="resultado-decision">
                      {resultado.supera
                        ? 'Entra en la lista de llamadas del programa.'
                        : 'No alcanza el umbral: queda fuera de la lista.'}
                    </p>
                  </div>
                  <span className="nivel">{prioridad(resultado)}</span>
                </div>


                {puedeSeguir &&
                  (registrado ? (
                    <div className="registrado-aviso">
                      <p>
                        <b>{registrado.nombre}</b> quedó en seguimiento con{' '}
                        {porcentaje(registrado.probabilidad)}.
                      </p>
                      <Link to="../seguimiento" className="pastilla pastilla-contorno pastilla-sm">
                        Ver el seguimiento
                      </Link>
                    </div>
                  ) : (
                    <button
                      type="button"
                      className="pastilla pastilla-rellena boton-registrar"
                      onClick={() => setRegistrando(true)}
                    >
                      <UserPlus size={15} strokeWidth={1.9} aria-hidden="true" />
                      Registrar para seguimiento
                    </button>
                  ))}
              </div>
            </aside>
          )}

          {resultado && <aside className="tarjeta tarjeta-pad">
            <details>
              <summary style={{ cursor: 'pointer', fontWeight: 800 }}>
                ¿Necesita ayuda para entender el resultado?
              </summary>
              <p className="tarjeta-sub" style={{ marginTop: 10 }}>
                Ayuda opcional, no sustituye el criterio de profesionales de salud.
              </p>
              <ChatAsistente estimacion={resultado} alto={240} compacto />
            </details>
          </aside>}

        </div>
      </div>

      {registrando && resultado && (
        <RegistrarPaciente
          entradas={paraEnviar}
          probabilidad={resultado.probabilidad}
          alerta={resultado.supera}
          onCerrar={() => setRegistrando(false)}
          onGuardado={(p) => {
            setRegistrando(false)
            setRegistrado(p)
          }}
        />
      )}

      <style>{`
        .estimar-columnas {
          display: grid;
          grid-template-columns: minmax(0, 1.24fr) minmax(340px, 1fr);
          gap: 19px;
          align-items: start;
        }
        .columna-lado { display: grid; gap: 14px; align-content: start; }
        .cuerpo-tarjeta { padding: 0 18px 18px; }

        /* El bloque del resultado, copiado del diseno que paso Michel: circulo
           con la cifra, titular al lado, y la pastilla de prioridad arriba. */
        .resultado {
          display: flex;
          gap: 15px;
          align-items: center;
          padding: 15px;
          background: var(--teal-suave);
          border: 1px solid #cdeee6;
          border-radius: 12px;
        }
        [data-tema='oscuro'] .resultado { border-color: #2c5551; }
        .resultado.alerta { background: #fdeee8; border-color: #f3cdbd; }
        [data-tema='oscuro'] .resultado.alerta { background: #3a2119; border-color: #5c3527; }

        .circulo {
          width: 96px; height: 96px; flex: none;
          border: 4px solid var(--teal);
          background: var(--superficie);
          border-radius: 50%;
          display: grid; place-items: center;
          font-family: var(--font-nunito);
          font-size: 23px; font-weight: 900;
          letter-spacing: -.03em;
          color: var(--teal-hondo);
          font-variant-numeric: tabular-nums lining-nums;
          transition: border-color .3s ease, color .3s ease;
        }
        .resultado.alerta .circulo { border-color: #c2410c; color: #c2410c; }
        [data-tema='oscuro'] .resultado.alerta .circulo { border-color: #e8845f; color: #f0a58a; }

        .resultado-texto h3 { font-size: 14px; }
        .resultado-texto p { margin-top: 6px; font-size: 12px; line-height: 1.55; color: #537774; }
        [data-tema='oscuro'] .resultado-texto p { color: #a9ccc7; }
        .resultado.alerta .resultado-texto p { color: #8a5340; }
        [data-tema='oscuro'] .resultado.alerta .resultado-texto p { color: #d9b4a4; }
        .resultado-decision { font-weight: 700; }
        .resultado .nivel { margin-left: auto; align-self: flex-start; }

        .cifras-riesgo {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
          margin-top: 16px;
        }
        .cifras-riesgo small {
          display: block; font-size: 10.5px; color: var(--apagado);
        }
        .cifras-riesgo b {
          display: block; margin-top: 4px;
          font-family: var(--font-nunito);
          font-size: 19px; font-weight: 900; letter-spacing: -.02em;
          color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }

        .barra-riesgo {
          position: relative; height: 7px; border-radius: 999px;
          background: var(--superficie-2); margin-top: 14px;
        }
        .barra-riesgo i {
          position: absolute; left: 0; top: 0; height: 7px; border-radius: 999px;
          background: linear-gradient(90deg, #00a99d, #c2410c);
          transition: width .45s cubic-bezier(.2,.75,.2,1);
        }
        .barra-riesgo b {
          position: absolute; top: -5px; width: 2px; height: 17px;
          border-radius: 2px; background: var(--apagado);
        }
        .barra-pie { margin-top: 7px; font-size: 10.5px; color: var(--apagado); }

        .boton-registrar {
          margin-top: 18px; width: 100%; justify-content: center;
          font-size: 13px; padding: 12px 16px;
        }
        .registrado-aviso {
          margin-top: 18px; padding: 12px 14px;
          border-radius: var(--radio-sm);
          background: var(--teal-suave);
          display: flex; align-items: center; justify-content: space-between;
          gap: 12px; flex-wrap: wrap;
        }
        .registrado-aviso p { font-size: 12px; color: var(--teal-hondo); }

        .peso-fila { margin-top: 15px; }
        .peso-fila:first-child { margin-top: 16px; }
        .peso-cabeza {
          display: flex; justify-content: space-between; gap: 12px;
          align-items: baseline; font-size: 12.5px;
        }
        .peso-cabeza strong { font-weight: 800; }
        .peso-valor {
          font-family: var(--font-nunito); font-weight: 900; font-size: 12px;
          font-variant-numeric: tabular-nums lining-nums; white-space: nowrap;
        }
        .peso-barra {
          height: 6px; background: var(--superficie-2);
          margin-top: 7px; border-radius: 999px; overflow: hidden;
        }
        .peso-barra i {
          display: block; height: 6px; border-radius: 999px;
          transition: width .45s cubic-bezier(.2,.75,.2,1);
        }
        .peso-pie { margin-top: 6px; font-size: 11px; color: var(--apagado); }
        .enlace-paso { margin-top: 18px; width: 100%; justify-content: center; }

        .aviso-rango { margin-top: 14px; font-size: 12px; color: #a8462c; }
        [data-tema='oscuro'] .aviso-rango { color: #f0c3b1; }
        .nota-prototipo { margin-top: 18px; font-size: 10.5px; color: var(--apagado); }

        @media (width < 1180px) {
          .estimar-columnas { grid-template-columns: 1fr; }
          .columna-lado { position: static; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); }
        }
        @media (width < 620px) {
          .resultado { flex-direction: column; align-items: flex-start; }
          .cifras-riesgo { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  )
}
