import { ChevronLeft, ChevronRight, Pause, Play } from 'lucide-react'
import { Suspense, lazy, useCallback, useEffect, useState } from 'react'

// three.js pesa medio mega: solo se carga cuando esta pantalla se abre.
const OrbeParticulas = lazy(() =>
  import('../orbe/OrbeParticulas').then((m) => ({ default: m.OrbeParticulas })),
)

/**
 * Pantalla 2: cómo se construyó el modelo, en las doce fases de la asignatura.
 *
 * Cada fase trae lo que de verdad se hizo y la cifra que salió, no la
 * definición de libro. Todas las cifras provienen de archivos de `reports/`.
 *
 * La maqueta: el fondo ocupa la vista entera —la fotografía de la Tierra de
 * noche con el orbe de partículas girando a la derecha— y las fases pasan
 * encima como una baraja. El orbe es el mismo de la portada y son los mismos
 * pacientes: no es un adorno traído de fuera.
 */

interface Fase {
  numero: number
  titulo: string
  que: string
  cifra?: string
  pie?: string
}
const FASES: Fase[] = [
  {
    numero: 1,
    titulo: 'Definir el problema',
    que: 'Predecir si una persona con diabetes volverá al hospital antes de treinta días, para ordenar a quién llamar primero. La meta se fijó antes de ver resultados: alcanzar al menos el 60 % de los que reingresan.',
    cifra: '60 %',
    pie: 'La meta de sensibilidad, acordada en la Fase 1',
  },
  {
    numero: 2,
    titulo: 'Conseguir los datos',
    que: 'El conjunto público de 130 hospitales de Estados Unidos entre 1999 y 2008. Cada fila es una hospitalización, con cincuenta columnas: quién es el paciente, por dónde entró, qué le hicieron, qué medicación recibió y a dónde salió.',
    cifra: '101.766',
    pie: 'Hospitalizaciones en el archivo original',
  },
  {
    numero: 3,
    titulo: 'Explorar',
    que: 'Contar qué falta, qué se repite y qué está mal. Apareció lo primero importante: un mismo paciente puede tener varias hospitalizaciones. Ignorarlo habría arruinado todo lo que viene después.',
    cifra: '69.990',
    pie: 'Pacientes distintos en esas 101.766 hospitalizaciones',
  },
  {
    numero: 4,
    titulo: 'Limpiar',
    que: 'Se excluyeron los egresos por fallecimiento y por cuidados paliativos. No es un capricho estadístico: esas personas no pueden reingresar, y dejarlas dentro le enseña al modelo a predecir algo que no existe.',
    cifra: '99.343',
    pie: 'Hospitalizaciones que quedaron tras las exclusiones',
  },
  {
    numero: 5,
    titulo: 'Construir variables',
    que: 'A partir de lo que había se derivaron columnas nuevas: cuántos servicios había usado antes, cuántos medicamentos por día de estancia, si le midieron la hemoglobina glicosilada. El modelo no ve lo que uno no le enseña a mirar.',
    cifra: '12',
    pie: 'Variables derivadas que no venían en el archivo',
  },
  {
    numero: 6,
    titulo: 'Partir los datos',
    que: 'Entrenamiento, validación y prueba, repartidos por paciente y no por hospitalización. Si las dos visitas de una misma persona caen a lado y lado, el modelo la reconoce en la prueba y el resultado sale inflado. Es el error más común y el más silencioso.',
    cifra: '60 / 20 / 20',
    pie: 'El reparto, siempre agrupado por paciente',
  },
  {
    numero: 7,
    titulo: 'Elegir el algoritmo',
    que: 'Se probaron cuatro: el que siempre responde «no reingresa», una regresión logística, Gradient Boosting y una red neuronal. El primero sirve de trampa deliberada: acierta el 88,6 % y no alerta a nadie.',
    cifra: '4',
    pie: 'Algoritmos comparados sobre los mismos pacientes',
  },
  {
    numero: 8,
    titulo: 'Entrenar',
    que: 'El Gradient Boosting se detuvo solo en 135 árboles. Arranca en la tasa base de la cohorte y cada árbol mueve esa cifra un poco, hacia arriba o hacia abajo, según lo que encuentra.',
    cifra: '135',
    pie: 'Árboles, decididos por parada temprana',
  },
  {
    numero: 9,
    titulo: 'Buscar la configuración',
    que: 'Aquí está la decisión que más vale la pena contar. El primer puesto y el segundo empataron en puntaje, 0,2328 contra 0,2323, pero el primero se memoriza los datos tres veces y media menos. Se eligió ese: el que generaliza, no el que puntúa.',
    cifra: '0,052',
    pie: 'Su brecha de sobreajuste, contra 0,178 del segundo',
  },
  {
    numero: 10,
    titulo: 'Evaluar',
    que: 'El conjunto de prueba se miró una sola vez, al final. ROC-AUC de 0,666, dentro del rango del índice LACE y del HOSPITAL score, que son los que usan hoy los hospitales para esta misma decisión.',
    cifra: '0,666',
    pie: 'ROC-AUC en prueba. La red neuronal llegó a 0,6389',
  },
  {
    numero: 11,
    titulo: 'Medir los límites',
    que: 'Equidad por género, grupo racial y edad; calibración; y una auditoría del techo de información de los datos. Esa última dio el hallazgo incómodo: el modelo ya está en el límite de lo que estas columnas permiten.',
    cifra: '0,6145',
    pie: 'El techo medido. El modelo logra 0,6171',
  },
  {
    numero: 12,
    titulo: 'Entregar',
    que: 'Esta aplicación. Inicio de sesión con dos roles, estimación por paciente, carga de archivos, lista priorizada, y el cálculo abierto para que cualquiera pueda revisarlo.',
    cifra: '17',
    pie: 'Pantallas, incluida la que está leyendo',
  },
]

const ESPERA = 6500

export function Fases() {
  const [actual, setActual] = useState(0)
  const [corriendo, setCorriendo] = useState(true)
  const [orbeFallo, setOrbeFallo] = useState(false)

  const mover = useCallback((paso: number) => {
    setActual((i) => (i + paso + FASES.length) % FASES.length)
  }, [])

  useEffect(() => {
    if (!corriendo) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    const t = setInterval(() => mover(1), ESPERA)
    return () => clearInterval(t)
  }, [corriendo, mover])

  // Las flechas del teclado mueven la baraja. En una sustentación es más
  // cómodo que buscar un botón con el ratón mientras uno habla.
  useEffect(() => {
    function tecla(e: KeyboardEvent) {
      const campo = document.activeElement?.tagName
      if (campo === 'INPUT' || campo === 'TEXTAREA') return
      if (e.key === 'ArrowRight') { mover(1); setCorriendo(false) }
      if (e.key === 'ArrowLeft') { mover(-1); setCorriendo(false) }
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [mover])

  const fase = FASES[actual]

  return (
    <div className="fases">
      <div className="fases-fondo" aria-hidden="true">
        {!orbeFallo && (
          <div className="fases-orbe">
            <Suspense fallback={null}>
              <OrbeParticulas forma="cohorte" onFallo={() => setOrbeFallo(true)} />
            </Suspense>
          </div>
        )}
      </div>

      <div className="fases-contenido">
        <div className="fases-izq">
          <p className="antetitulo fases-antetitulo">Empezar aquí · Cómo se construyó</p>
          <h1>Doce fases, de la pregunta al despliegue</h1>
          <p className="fases-bajada">
            Esto no es la teoría de un libro: es lo que de verdad se hizo, en orden, con la
            cifra que salió de cada paso. Las tarjetas pasan solas, o use las flechas del
            teclado.
          </p>

          <div className="fase-detalle" key={fase.numero}>
            <div className="fase-detalle-cabeza">
              <span className="fase-numerote">{String(fase.numero).padStart(2, '0')}</span>
              <h2>{fase.titulo}</h2>
            </div>
            <p className="fase-que">{fase.que}</p>
            {fase.cifra && (
              <div className="fase-cifra">
                <b>{fase.cifra}</b>
                <small>{fase.pie}</small>
              </div>
            )}
          </div>

          <div className="fases-mando">
            <button type="button" onClick={() => { mover(-1); setCorriendo(false) }} aria-label="Fase anterior">
              <ChevronLeft size={17} strokeWidth={2} />
            </button>
            <button
              type="button"
              onClick={() => setCorriendo((v) => !v)}
              aria-label={corriendo ? 'Detener el paso automático' : 'Reanudar el paso automático'}
            >
              {corriendo ? <Pause size={15} strokeWidth={2} /> : <Play size={15} strokeWidth={2} />}
            </button>
            <button type="button" onClick={() => { mover(1); setCorriendo(false) }} aria-label="Fase siguiente">
              <ChevronRight size={17} strokeWidth={2} />
            </button>
            <span className="fases-cuenta">
              {String(actual + 1).padStart(2, '0')} <i>/ {FASES.length}</i>
            </span>
            <div className="fases-riel">
              <i style={{ width: `${((actual + 1) / FASES.length) * 100}%` }} />
            </div>
          </div>
        </div>

        <div className="fases-baraja">
          {FASES.map((f, i) => {
            // Distancia desde la fase activa, en circulo. La de delante es 0;
            // las tres siguientes se apilan detras; el resto queda fuera.
            const d = (i - actual + FASES.length) % FASES.length
            const detras = d >= 1 && d <= 3
            const estado = d === 0 ? 'frente' : detras ? 'detras' : 'fuera'

            return (
              <button
                key={f.numero}
                type="button"
                className={`fase-carta ${estado}`}
                style={{ zIndex: FASES.length - d, '--d': d } as React.CSSProperties}
                tabIndex={d === 0 ? 0 : -1}
                aria-hidden={d !== 0}
                onClick={() => {
                  if (d !== 0) { setActual(i); setCorriendo(false) }
                }}
              >
                <span className="fase-carta-num">{String(f.numero).padStart(2, '0')}</span>
                <b>{f.titulo}</b>
                {f.cifra && (
                  <span className="fase-carta-cifra">
                    {f.cifra}
                    <i>{f.pie}</i>
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      <div className="fases-puntos">
        {FASES.map((f, i) => (
          <button
            key={f.numero}
            type="button"
            className={i === actual ? 'activo' : ''}
            aria-label={`Fase ${f.numero}: ${f.titulo}`}
            aria-current={i === actual}
            onClick={() => { setActual(i); setCorriendo(false) }}
          />
        ))}
      </div>
    </div>
  )
}
