import { Link } from 'react-router-dom'
import { Encabezado } from '../componentes/Encabezado'

/** El ciclo académico está detrás del producto, no en el menú asistencial. */
export function LaboratorioIA() {
  const grupos = [
    { titulo: 'Comprender los datos', enlaces: [
      ['guia', 'Contexto del proyecto'], ['fases', 'Las doce fases'],
      ['cohorte', 'Origen de los datos'], ['estadistica', 'Estadística descriptiva'],
      ['mapa-de-calor', 'Mapa de calor'],
    ] },
    { titulo: 'Entrenar y comparar', enlaces: [
      ['entrenar', 'Entrenamiento interactivo'], ['modelos', 'Comparación GB vs MLP'],
      ['desempeno', 'Métricas del modelo'], ['importancia', 'Importancia de variables'],
    ] },
    { titulo: 'Interpretación y límites', enlaces: [
      ['paso-a-paso', 'Cálculo paso a paso'], ['equidad', 'Equidad y límites'],
      ['techo', 'Limitaciones de los datos'], ['ficha', 'Ficha del modelo'],
      ['pacientes', 'Cohorte histórica de prueba'], ['asistente', 'Asistente académico'],
    ] },
  ]
  return <div>
    <Encabezado antetitulo="Administración" titulo="Laboratorio de IA">
      <p>Todo el proceso que ocurre detrás de la predicción, organizado por etapas.</p>
    </Encabezado>
    <div style={{ display: 'grid', gap: 18 }}>
      {grupos.map(grupo => <section key={grupo.titulo} className="tarjeta tarjeta-pad">
        <h2 className="tarjeta-titulo" style={{ marginBottom: 16 }}>{grupo.titulo}</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          {grupo.enlaces.map(([ruta, titulo]) => <Link key={ruta} to={`../${ruta}`} className="pastilla pastilla-contorno pastilla-sm">{titulo}</Link>)}
        </div>
      </section>)}
    </div>
  </div>
}
