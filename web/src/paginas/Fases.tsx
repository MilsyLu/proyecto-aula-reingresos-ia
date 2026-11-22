import { Encabezado } from '../componentes/Encabezado'
import { TextoRevelado } from '../componentes/core/TextoRevelado'

/**
 * Pantalla 2: cómo se construyó el modelo, en las doce fases de la asignatura.
 *
 * Cada fase trae lo que de verdad se hizo y la cifra que salió, no la
 * definición de libro. Todas las cifras provienen de archivos de `reports/`.
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

export function Fases() {
  return (
    <div style={{ display: 'grid', gap: 56 }}>
      <Encabezado antetitulo="Empezar aquí" titulo="Cómo se construyó, en doce fases">
        <p>
          De la pregunta inicial hasta esta pantalla. Cada fase trae lo que se hizo de verdad y
          la cifra que salió, no la definición del libro.
        </p>
      </Encabezado>

      <ol className="fases">
        {FASES.map((fase) => (
          <li key={fase.numero} className="fase">
            <div className="fase-numero" aria-hidden="true">
              {String(fase.numero).padStart(2, '0')}
            </div>
            <div className="fase-cuerpo">
              <h2 className="fase-titulo">{fase.titulo}</h2>
              <TextoRevelado className="fase-que" porPalabra={0.016}>
                {fase.que}
              </TextoRevelado>
            </div>
            {fase.cifra && (
              <div className="fase-dato">
                <div className="fase-cifra">{fase.cifra}</div>
                {fase.pie && <p className="fase-pie">{fase.pie}</p>}
              </div>
            )}
          </li>
        ))}
      </ol>

      <p
        style={{
          fontSize: 13,
          color: 'var(--apagado)',
          lineHeight: 1.7,
          maxWidth: '74ch',
          borderTop: '1px solid var(--filete)',
          paddingTop: 24,
        }}
      >
        Las doce fases corresponden a las de la asignatura. Todas las cifras de esta pantalla
        salen de archivos del repositorio, no están escritas a mano: se pueden volver a calcular
        corriendo los cuadernos.
      </p>

      <style>{`
        .fases { list-style: none; margin: 0; padding: 0; display: grid; gap: 0; }
        .fase {
          display: grid;
          grid-template-columns: 56px minmax(0, 1fr) 200px;
          gap: 28px;
          align-items: start;
          padding-block: 34px;
          border-top: 1px solid var(--filete);
        }
        .fase:last-child { border-bottom: 1px solid var(--filete); }
        .fase-numero {
          font-family: var(--font-serif);
          font-weight: 300;
          font-size: 30px;
          line-height: 1.1;
          letter-spacing: -0.02em;
          color: var(--apagado);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .fase-titulo { font-size: 24px; line-height: 1.2; }
        .fase-que {
          margin-top: 12px;
          font-size: 15.5px;
          line-height: 1.7;
          color: var(--apagado);
          max-width: 62ch;
        }
        .fase-dato { text-align: right; }
        .fase-cifra {
          font-family: var(--font-serif);
          font-weight: 300;
          font-size: 30px;
          line-height: 1.1;
          letter-spacing: -0.02em;
          color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .fase-pie {
          margin-top: 8px;
          font-size: 11.5px;
          line-height: 1.5;
          color: var(--apagado);
        }
        @media (width < 860px) {
          .fase { grid-template-columns: 44px minmax(0, 1fr); gap: 18px; }
          .fase-dato { grid-column: 2; text-align: left; margin-top: 16px; }
          .fase-pie { max-width: 40ch; }
        }
      `}</style>
    </div>
  )
}
