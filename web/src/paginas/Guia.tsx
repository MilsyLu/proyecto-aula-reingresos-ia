import { Encabezado } from '../componentes/Encabezado'
import { useSesion } from '../lib/sesion'

/**
 * Pantalla 1: qué es esto y qué puede hacer.
 *
 * Es la primera que ve alguien que entra sin saber nada. Tiene que responder
 * tres cosas antes de que la persona se pierda: para qué sirve, qué no hace, y
 * por dónde empezar.
 */
export function Guia() {
  const { sesion } = useSesion()
  const esCoordinador = sesion?.rol === 'coordinador'

  return (
    <div style={{ display: 'grid', gap: 64 }}>
      <Encabezado antetitulo="Empezar aquí" titulo="Qué es esto y qué puede hacer">
        <p>
          ReingresaIA estima qué tan probable es que una persona con diabetes vuelva al hospital
          antes de treinta días desde que le dieron el alta. Con esa estimación ordena una lista:
          a quién conviene llamar primero cuando el programa de seguimiento no alcanza para
          llamar a todos.
        </p>
      </Encabezado>

      <Bloque titulo="Qué decide y qué no decide">
        <p>
          Decide un <strong style={{ fontWeight: 600 }}>orden de prioridad</strong>. Nada más.
          Cuando el equipo tiene cupo para cuatrocientas llamadas y hay veinte mil pacientes
          dados de alta, el modelo dice por cuáles cuatrocientos empezar.
        </p>
        <p style={{ marginTop: 16 }}>
          No decide altas, no sugiere tratamientos, no reemplaza el criterio de nadie y no
          sustituye una valoración clínica. Un paciente que el modelo deja fuera de la lista
          puede estar grave: lo único que dice es que, en promedio, los de arriba vuelven más.
        </p>
      </Bloque>

      <Bloque titulo="Qué tan bien funciona">
        <p>
          Acierta poco paciente por paciente, y eso hay que decirlo de frente. Su ROC-AUC es
          0,666. Para comparar: el índice LACE, que se usa hoy en hospitales de Canadá y Estados
          Unidos para esta misma decisión, obtuvo 0,648 en su validación danesa, y el HOSPITAL
          score 0,661 en la misma.
        </p>
        <p style={{ marginTop: 16 }}>
          Donde sí sirve es ordenando. Entre el 2 % de mayor riesgo reingresa el 43,1 %, frente
          al 11,4 % de la población general: casi cuatro veces más. Eso es lo que convierte una
          lista de llamadas en algo que vale la pena hacer.
        </p>
        <p style={{ marginTop: 16 }}>
          Y hay un límite que no es culpa del modelo. Medimos cuánta información contienen estas
          columnas y el modelo ya está en ese techo. Lo que falta no es un algoritmo mejor: son
          datos que el hospital no registra, como si el paciente tiene quién lo cuide, si puede
          pagar los medicamentos o si tiene cómo llegar al control.
        </p>
      </Bloque>

      <Bloque titulo="Por dónde empezar">
        <p>El menú de la izquierda está en el orden en que conviene recorrerlo.</p>
        <ol className="lista-guia">
          <li>
            <strong>Cómo se construyó.</strong> Las doce fases, de la pregunta inicial al
            despliegue. Si nunca ha visto cómo se entrena un modelo, empiece por ahí.
          </li>
          <li>
            <strong>Estimar un paciente.</strong> Escriba los datos de una hospitalización y vea
            la estimación.
          </li>
          <li>
            <strong>Paso a paso del cálculo.</strong> De dónde sale exactamente esa cifra, árbol
            por árbol. Es la pantalla que responde a «¿y usted cómo sabe?».
          </li>
          <li>
            <strong>El asistente.</strong> Pregúntele con sus palabras. Si no sabe algo, se lo
            dice en vez de inventarlo.
          </li>
          {esCoordinador && (
            <li>
              <strong>Archivo y lista de llamadas.</strong> Suba el corte del día, diga a cuántas
              personas alcanza a llamar y reciba la lista ordenada.
            </li>
          )}
        </ol>
      </Bloque>

      <Bloque titulo="Por qué hay dos tipos de usuario">
        <p>
          Todo el conocimiento está abierto para los dos: los datos, las métricas, la equidad,
          los límites. Lo que está reservado para la coordinación son tres palancas: cargar
          archivos, fijar el umbral de alerta y disparar un entrenamiento.
        </p>
        <p style={{ marginTop: 16 }}>
          La razón es que el umbral no es un cálculo clínico sino una decisión de política: de él
          depende a cuánta gente se llama y, por tanto, cuánto cuesta el programa. Quien lo fija
          responde por esa decisión. Quien lo consume, no.
        </p>
      </Bloque>

      <div
        style={{
          borderTop: '1px solid var(--filete)',
          paddingTop: 24,
          maxWidth: '72ch',
        }}
      >
        <p style={{ fontSize: 13, color: 'var(--apagado)', lineHeight: 1.7 }}>
          Los datos provienen del conjunto público de 130 hospitales de Estados Unidos
          (1999-2008). No hay información de pacientes reales identificables, y el prototipo no
          está validado para uso clínico. Universidad Popular del Cesar, Grupo 04.
        </p>
      </div>

      <style>{`
        .lista-guia {
          margin: 20px 0 0;
          padding-left: 22px;
          display: grid;
          gap: 14px;
          color: var(--apagado);
          font-size: 15px;
          line-height: 1.65;
        }
        .lista-guia strong { color: var(--tinta); font-weight: 600; }
        .lista-guia::marker { color: var(--apagado); }
      `}</style>
    </div>
  )
}

function Bloque({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section style={{ maxWidth: '68ch' }}>
      <h2 style={{ fontSize: 'clamp(24px, 3vw, 30px)' }}>{titulo}</h2>
      <div style={{ marginTop: 18, fontSize: 16, lineHeight: 1.7, color: 'var(--apagado)' }}>
        {children}
      </div>
    </section>
  )
}
