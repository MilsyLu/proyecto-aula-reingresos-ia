import {
  ArrowRight, Check, ClipboardList, Info, Minus, PhoneCall, Sigma,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useSesion } from '../lib/sesion'

/**
 * Pantalla 1: qué es esto y qué puede hacer.
 *
 * Es la primera que ve alguien que entra sin saber nada, así que no puede ser
 * un documento. Tiene que responder tres cosas antes de que la persona se
 * pierda: para qué sirve, qué NO hace, y por dónde empezar.
 *
 * Todo lo que se afirma aquí está medido y sale de `reports/`. Ninguna cifra
 * es de adorno.
 */

/** Las tarjetas que se pasan solas arriba a la derecha. */
const TARJETAS = [
  {
    antetitulo: 'La idea, en un ejemplo',
    cifra: '20.000',
    pie: 'personas dadas de alta',
    cifra2: '400',
    pie2: 'llamadas disponibles',
    nota: (
      <>
        El modelo ayuda a decidir por cuáles empezar. <b>Es un ejemplo ilustrativo</b>, no un
        dato de operación.
      </>
    ),
  },
  {
    antetitulo: 'Dónde sí sirve',
    cifra: '43,1 %',
    pie: 'reingresa en el 2 % de mayor riesgo',
    cifra2: '11,4 %',
    pie2: 'reingresa en la población general',
    nota: (
      <>
        <b>Casi cuatro veces más.</b> Acierta poco paciente por paciente, pero ordenando es
        donde vale la pena.
      </>
    ),
  },
  {
    antetitulo: 'Comparado con lo que se usa hoy',
    cifra: '0,666',
    pie: 'ROC-AUC de este modelo',
    cifra2: '0,648',
    pie2: 'el índice LACE, en su validación danesa',
    nota: (
      <>
        LACE y HOSPITAL (0,661) se usan hoy en hospitales de Canadá y Estados Unidos para esta
        misma decisión. <b>Estamos en ese rango.</b>
      </>
    ),
  },
  {
    antetitulo: 'El límite, medido',
    cifra: '0,6145',
    pie: 'todo lo que estos datos permiten',
    cifra2: '0,6171',
    pie2: 'lo que el modelo ya logra',
    nota: (
      <>
        <b>El modelo está en el techo.</b> Lo que falta no es un algoritmo mejor: son datos que
        el hospital no registra.
      </>
    ),
  },
  {
    antetitulo: 'De dónde salen los datos',
    cifra: '130',
    pie: 'hospitales de Estados Unidos',
    cifra2: '99.343',
    pie2: 'hospitalizaciones, entre 1999 y 2008',
    nota: (
      <>
        Conjunto público y anonimizado. <b>No hay pacientes identificables</b> en ninguna parte
        de esta aplicación.
      </>
    ),
  },
]

const PASOS = [
  {
    Icono: ClipboardList,
    titulo: 'Se revisa el alta',
    texto: 'Se introducen los datos de la hospitalización y del uso previo de servicios.',
  },
  {
    Icono: Sigma,
    titulo: 'Se calcula una estimación',
    texto: 'El modelo produce una probabilidad orientativa de reingreso a treinta días.',
  },
  {
    Icono: PhoneCall,
    titulo: 'El equipo prioriza',
    texto: 'La lista ayuda a organizar llamadas, teniendo siempre en cuenta el contexto clínico.',
  },
]

/**
 * El carrusel de arriba.
 *
 * Pasa solo cada siete segundos, pero se detiene si el cursor está encima: si
 * alguien se queda leyendo una tarjeta, que no se la quiten de delante. Y a
 * quien pidió no ver animaciones no se le mueve nunca.
 */
function Carrusel() {
  const [actual, setActual] = useState(0)
  const [quieto, setQuieto] = useState(false)

  useEffect(() => {
    if (quieto) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const t = setInterval(() => setActual((i) => (i + 1) % TARJETAS.length), 7000)
    return () => clearInterval(t)
  }, [quieto])

  const c = TARJETAS[actual]

  return (
    <div
      className="carrusel"
      onMouseEnter={() => setQuieto(true)}
      onMouseLeave={() => setQuieto(false)}
      aria-roledescription="carrusel"
      aria-label="Cifras del proyecto"
    >
      <div className="carrusel-cara" key={actual}>
        <p className="carrusel-antetitulo">{c.antetitulo}</p>

        <div className="carrusel-cifras">
          <div>
            <b>{c.cifra}</b>
            <small>{c.pie}</small>
          </div>
          <ArrowRight className="carrusel-flecha" size={22} strokeWidth={1.4} aria-hidden="true" />
          <div className="carrusel-caja">
            <b>{c.cifra2}</b>
            <small>{c.pie2}</small>
          </div>
        </div>

        <p className="carrusel-nota">{c.nota}</p>
      </div>

      <div className="carrusel-puntos">
        {TARJETAS.map((t, i) => (
          <button
            key={t.antetitulo}
            type="button"
            className={i === actual ? 'activo' : ''}
            aria-label={`Ver «${t.antetitulo}»`}
            aria-current={i === actual}
            onClick={() => setActual(i)}
          />
        ))}
      </div>
    </div>
  )
}

/** El encabezado de cada sección: antetítulo, titular y una nota a la derecha. */
function CabezaSeccion({
  antetitulo, titulo, nota,
}: { antetitulo: string; titulo: string; nota: string }) {
  return (
    <div className="cabeza-seccion">
      <div>
        <p className="antetitulo">{antetitulo}</p>
        <h2>{titulo}</h2>
      </div>
      <p className="cabeza-nota">{nota}</p>
    </div>
  )
}

export function Guia() {
  const { sesion } = useSesion()
  const esCoordinador = sesion?.rol === 'coordinador'

  return (
    <div className="guia">
      <section className="guia-portico">
        <div className="guia-intro">
          <p className="antetitulo">Empezar aquí · Orientación</p>
          <h1>¿Qué es esto y qué puede hacer?</h1>
          <p className="guia-bajada">
            ReingresaIA estima la probabilidad de que una persona con diabetes vuelva al hospital
            durante los treinta días posteriores al alta. Con esa estimación ayuda a ordenar a
            quién conviene llamar primero cuando el equipo no alcanza a contactar a todas las
            personas.
          </p>
          <Link to="../estimar" className="pastilla pastilla-rellena guia-boton">
            Conocer la estimación
            <ArrowRight size={16} strokeWidth={2} aria-hidden="true" />
          </Link>
        </div>

        <Carrusel />
      </section>

      <section>
        <CabezaSeccion
          antetitulo="Alcance de la herramienta"
          titulo="Decide un orden de prioridad. Nada más."
          nota="Es una ayuda para organizar el seguimiento, no una decisión clínica automática."
        />

        <div className="dos-caras">
          <div className="tarjeta cara si">
            <div className="cara-cabeza">
              <span className="cara-sello">
                <Check size={16} strokeWidth={2.4} aria-hidden="true" />
              </span>
              <div>
                <h3>Qué sí hace</h3>
                <p>
                  Estima y organiza una lista para que el equipo pueda empezar por los casos que
                  el modelo considera prioritarios.
                </p>
              </div>
            </div>
            <ul>
              <li>Apoya la planificación de llamadas</li>
              <li>Resume la información del alta en una sola cifra</li>
              <li>Deja la decisión en manos del equipo</li>
            </ul>
          </div>

          <div className="tarjeta cara no">
            <div className="cara-cabeza">
              <span className="cara-sello">
                <Minus size={16} strokeWidth={2.4} aria-hidden="true" />
              </span>
              <div>
                <h3>Qué no hace</h3>
                <p>
                  La estimación no determina la atención que una persona necesita ni reemplaza
                  una valoración profesional.
                </p>
              </div>
            </div>
            <ul>
              <li>No decide altas ni tratamientos</li>
              <li>No diagnostica ni descarta gravedad</li>
              <li>No sustituye el criterio clínico</li>
            </ul>
          </div>
        </div>
      </section>

      <section>
        <CabezaSeccion
          antetitulo="Un recorrido sencillo"
          titulo="De los datos a una llamada priorizada"
          nota="La estimación orienta la conversación; el equipo conserva el control."
        />

        <div className="tres-pasos">
          {PASOS.map(({ Icono, titulo, texto }, i) => (
            <div key={titulo} className="tarjeta paso">
              <div className="paso-cabeza">
                <span className="paso-sello">
                  <Icono size={17} strokeWidth={1.7} aria-hidden="true" />
                </span>
                <span className="paso-numero">{String(i + 1).padStart(2, '0')}</span>
              </div>
              <h3>{titulo}</h3>
              <p>{texto}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <CabezaSeccion
          antetitulo="Por dónde empezar"
          titulo="El menú está en el orden en que conviene recorrerlo"
          nota="Pulse cualquiera para ir directo."
        />

        <div className="atajos-guia">
          <Link to="../fases" className="tarjeta atajo-guia">
            <b>Cómo se construyó</b>
            <small>
              Las doce fases, de la pregunta inicial al despliegue. Si nunca ha visto cómo se
              entrena un modelo, empiece por ahí.
            </small>
          </Link>
          <Link to="../paso-a-paso" className="tarjeta atajo-guia">
            <b>El cálculo paso a paso</b>
            <small>
              De dónde sale exactamente esa cifra, árbol por árbol. Es la pantalla que responde
              a «¿y usted cómo sabe?».
            </small>
          </Link>
          <Link to="../asistente" className="tarjeta atajo-guia">
            <b>El asistente</b>
            <small>
              Pregúntele con sus palabras. Cuando no sabe algo, se lo dice en vez de inventarlo.
            </small>
          </Link>
          {esCoordinador && (
            <Link to="../archivo" className="tarjeta atajo-guia">
              <b>Archivo y lista de llamadas</b>
              <small>
                Suba el corte del día, diga a cuántas personas alcanza a llamar y reciba la
                lista ordenada.
              </small>
            </Link>
          )}
        </div>
      </section>

      <div className="franja-aviso">
        <span className="franja-sello">
          <Info size={15} strokeWidth={2} aria-hidden="true" />
        </span>
        <p>
          <b>Importante:</b> un resultado bajo no significa que una persona esté fuera de
          peligro. Este prototipo académico no está validado para tomar decisiones clínicas.
        </p>
        <Link to="../equidad" className="pastilla pastilla-contorno pastilla-sm">
          Conocer límites del modelo
          <ArrowRight size={14} strokeWidth={2} aria-hidden="true" />
        </Link>
      </div>
    </div>
  )
}
