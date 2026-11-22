import { useEffect, useState } from 'react'
import { Encabezado } from '../componentes/Encabezado'
import { api, ErrorApi } from '../lib/api'
import { numero } from '../lib/formato'

/**
 * Pantalla 13: qué pesa en el modelo.
 *
 * Importancia por permutación: se revuelve una columna al azar y se mide
 * cuánto empeora el modelo. Lo que no empeora nada, no estaba diciendo nada.
 *
 * Se muestran las cincuenta, no las diez primeras. Que cuarenta variables no
 * aporten es un hallazgo, no un detalle que convenga recortar.
 */

interface Variable {
  variable: string
  caida_AP: number
  desv: number
  pct_del_AP: number
}

interface Datos {
  variables: Variable[]
  con_aporte: number
  total: number
  suma_primeras_dos: number
}

/** Nombres legibles para las columnas que el modelo usa por su nombre técnico. */
const EN_ESPANOL: Record<string, string> = {
  number_inpatient: 'Hospitalizaciones en el año previo',
  discharge_disposition_id: 'Tipo de egreso',
  medical_specialty: 'Especialidad que atiende',
  grupo_diag_1: 'Diagnóstico principal',
  grupo_diag_2: 'Diagnóstico secundario',
  grupo_diag_3: 'Diagnóstico adicional',
  servicios_previos: 'Servicios usados antes (derivada)',
  admission_type_id: 'Tipo de ingreso',
  admission_source_id: 'Origen del ingreso',
  number_emergency: 'Visitas a urgencias',
  number_outpatient: 'Consultas externas',
  num_meds_activos: 'Medicamentos activos (derivada)',
  num_medications: 'Medicamentos administrados',
  num_lab_procedures: 'Pruebas de laboratorio',
  num_procedures: 'Procedimientos',
  number_diagnoses: 'Diagnósticos registrados',
  time_in_hospital: 'Días de estancia',
  edad_num: 'Edad',
  gender: 'Género',
  meds_por_dia: 'Medicamentos por día (derivada)',
  labs_por_dia: 'Pruebas por día (derivada)',
  tuvo_ingreso_previo: 'Tuvo ingreso previo (derivada)',
  hubo_cambio_med: 'Hubo cambio de medicación (derivada)',
  a1c_medida: 'Se midió la HbA1c (derivada)',
  glu_medida: 'Se midió la glucosa (derivada)',
  A1Cresult: 'Hemoglobina glicosilada',
  max_glu_serum: 'Glucosa en suero',
  change: 'Cambio de medicación',
  diabetesMed: 'Toma medicación para diabetes',
  insulin: 'Insulina',
}

export function Importancia() {
  const [d, setD] = useState<Datos | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [todas, setTodas] = useState(false)

  useEffect(() => {
    api
      .obtener<Datos>('/importancia')
      .then(setD)
      .catch((e) => setError(e instanceof ErrorApi ? e.message : 'No se pudo cargar.'))
  }, [])

  if (error) {
    return (
      <div>
        <Encabezado antetitulo="Conocer el modelo" titulo="Qué pesa en el modelo" />
        <p style={{ marginTop: 24, color: 'var(--color-dato-4)' }}>{error}</p>
      </div>
    )
  }

  const lista = d ? (todas ? d.variables : d.variables.slice(0, 15)) : []
  const maximo = d ? Math.max(...d.variables.map((v) => v.pct_del_AP)) : 1

  return (
    <div>
      <Encabezado antetitulo="Conocer el modelo" titulo="Qué pesa en el modelo">
        <p>
          Se revuelve una columna al azar y se mide cuánto empeora el modelo. Lo que no empeora
          nada es que no estaba diciendo nada. No es una opinión sobre qué debería importar: es
          lo que importa, medido.
        </p>
      </Encabezado>

      {!d && <p className="antetitulo" style={{ marginTop: 32 }}>Cargando</p>}

      {d && (
        <>
          <div className="resumen-i">
            <div>
              <div className="resumen-i-v">{numero(d.suma_primeras_dos, 1)}&nbsp;%</div>
              <p>se lo llevan las dos primeras variables</p>
            </div>
            <div>
              <div className="resumen-i-v">{d.con_aporte}</div>
              <p>de {d.total} variables aportan algo medible</p>
            </div>
            <div>
              <div className="resumen-i-v">{d.total - d.con_aporte}</div>
              <p>no aportan nada, o empeoran el modelo</p>
            </div>
          </div>

          <div className="lista-i">
            {lista.map((v, i) => (
              <div key={v.variable} className="fila-i">
                <span className="puesto-i">{i + 1}</span>
                <span className="nombre-i">
                  {EN_ESPANOL[v.variable] ?? v.variable}
                  {EN_ESPANOL[v.variable] && <em>{v.variable}</em>}
                </span>
                <span className="barra-i">
                  <i
                    style={{
                      width: `${Math.max((v.pct_del_AP / maximo) * 100, 0)}%`,
                      opacity: v.pct_del_AP > 0 ? 1 : 0.25,
                    }}
                  />
                </span>
                <span className="pct-i">{numero(v.pct_del_AP, 2)}&nbsp;%</span>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="pastilla pastilla-contorno pastilla-sm"
            style={{ marginTop: 22 }}
            onClick={() => setTodas((t) => !t)}
          >
            {todas ? 'Ver solo las quince primeras' : `Ver las ${d.total} variables`}
          </button>

          <p className="cierre-i">
            Las dos primeras se llevan el {numero(d.suma_primeras_dos, 1)} % entre las dos: cuántas
            veces estuvo hospitalizado antes, y a dónde salió. Por eso son las dos que cruza el
            mapa de calor.
          </p>
          <p className="cierre-i">
            Y hay algo incómodo en esta lista: los dieciséis antidiabéticos, la hemoglobina
            glicosilada y los conteos de laboratorio están casi al final. El modelo apenas los
            usa. Eso coincide con lo que encontró la auditoría del techo, donde las treinta y
            ocho variables clínicas juntas no agregan nada a las doce administrativas.
          </p>

          <p className="nota-i">
            La importancia por permutación se mide sobre el conjunto de validación, repitiendo
            cada mezcla varias veces. La columna de desviación del archivo original dice cuánto
            varía entre repeticiones; para las primeras variables es pequeña frente al efecto,
            así que el orden es estable.
          </p>
        </>
      )}

      <style>{`
        .resumen-i {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
          gap: 26px; margin-top: 40px;
        }
        .resumen-i-v {
          font-family: var(--font-serif); font-weight: 300; font-size: 38px;
          letter-spacing: -0.02em; color: var(--tinta-fuerte);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .resumen-i p { margin-top: 7px; font-size: 12.5px; line-height: 1.5; color: var(--apagado); }

        .lista-i { margin-top: 40px; }
        .fila-i {
          display: grid; grid-template-columns: 30px minmax(0, 1fr) 190px 74px;
          gap: 14px; align-items: center;
          padding-block: 11px; border-bottom: 1px solid var(--filete);
        }
        .puesto-i {
          font-family: var(--font-serif); font-size: 15px; color: var(--apagado);
          font-variant-numeric: tabular-nums lining-nums;
        }
        .nombre-i { font-size: 14px; }
        .nombre-i em {
          display: block; font-style: normal; font-size: 11px;
          color: var(--apagado); margin-top: 2px;
        }
        .barra-i { height: 6px; background: var(--filete); border-radius: 999px; }
        .barra-i i { display: block; height: 6px; border-radius: 999px; background: var(--color-dato-3); }
        .pct-i { text-align: right; font-size: 13.5px; font-variant-numeric: tabular-nums lining-nums; }

        .cierre-i {
          margin-top: 24px; font-size: 15px; line-height: 1.75;
          color: var(--apagado); max-width: 72ch;
        }
        .nota-i {
          margin-top: 32px; padding-top: 20px; border-top: 1px solid var(--filete);
          font-size: 12.5px; line-height: 1.7; color: var(--apagado); max-width: 74ch;
        }
        @media (width < 820px) {
          .fila-i { grid-template-columns: 26px minmax(0, 1fr) 64px; }
          .barra-i { display: none; }
        }
      `}</style>
    </div>
  )
}
