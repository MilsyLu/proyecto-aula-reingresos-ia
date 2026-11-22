import { GRUPOS_CAMPOS, LIMITES, type CampoFormulario } from '../lib/tiposModelo'

/**
 * El formulario de la hospitalización, compartido por Estimar y Paso a paso.
 *
 * Los campos se agrupan como los piensa quien los llena —la persona, esta
 * hospitalización, el año previo, la medicación— y no en el orden en que el
 * modelo espera las columnas. Quince campos en una lista plana se leen como un
 * trámite; en cuatro grupos, como una historia clínica.
 *
 * Nada de deslizadores: se escriben los números. Un deslizador obliga a cazar
 * el valor exacto y nadie sabe nunca qué tan lejos está del siguiente.
 */
export function FormularioPaciente({
  campos,
  valores,
  onCambio,
  deshabilitado = false,
}: {
  campos: CampoFormulario[]
  valores: Record<string, string | number>
  onCambio: (campo: string, valor: string | number) => void
  deshabilitado?: boolean
}) {
  const porCampo = new Map(campos.map((c) => [c.campo, c]))

  return (
    <div style={{ display: 'grid', gap: 28 }}>
      {GRUPOS_CAMPOS.map((grupo) => (
        <fieldset key={grupo.titulo} className="grupo-campos">
          <legend className="antetitulo">{grupo.titulo}</legend>
          <div className="rejilla-campos">
            {grupo.campos.map((nombreCampo) => {
              const campo = porCampo.get(nombreCampo)
              if (!campo) return null
              const limite = LIMITES[nombreCampo]
              const valor = valores[nombreCampo] ?? ''

              return (
                <label key={nombreCampo} className="campo-paciente">
                  <span className="campo-etiqueta">{campo.nombre}</span>

                  {campo.opciones ? (
                    <select
                      value={String(valor)}
                      disabled={deshabilitado}
                      onChange={(e) => onCambio(nombreCampo, e.target.value)}
                    >
                      {campo.opciones.map((o) => (
                        <option key={o.valor} value={o.valor}>
                          {o.etiqueta}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="number"
                      inputMode="numeric"
                      value={String(valor)}
                      min={limite?.min}
                      max={limite?.max}
                      step={1}
                      disabled={deshabilitado}
                      onChange={(e) => onCambio(nombreCampo, e.target.value)}
                    />
                  )}

                  {limite && (
                    <span className="campo-rango">
                      de {limite.min} a {limite.max}
                    </span>
                  )}
                </label>
              )
            })}
          </div>
        </fieldset>
      ))}

      <style>{`
        .grupo-campos { border: 0; margin: 0; padding: 0; }
        .grupo-campos legend { padding: 0; margin-bottom: 14px; }
        .rejilla-campos {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 14px;
        }
        .campo-paciente { display: flex; flex-direction: column; gap: 6px; }
        .campo-etiqueta { font-size: 13.5px; color: var(--tinta); }
        .campo-paciente input,
        .campo-paciente select {
          background: var(--superficie);
          border: 1px solid var(--filete);
          border-radius: var(--radius-entrada);
          padding: 10px 12px;
          font-family: var(--font-sans);
          font-size: 15px;
          color: var(--tinta);
          letter-spacing: -0.009em;
          font-variant-numeric: tabular-nums lining-nums;
          width: 100%;
        }
        .campo-paciente select { cursor: pointer; appearance: none; }
        .campo-paciente input:focus,
        .campo-paciente select:focus { outline: none; border-color: var(--filete-fuerte); }
        .campo-paciente input:disabled,
        .campo-paciente select:disabled { opacity: .55; cursor: default; }
        .campo-rango { font-size: 11px; color: var(--apagado); }
      `}</style>
    </div>
  )
}
