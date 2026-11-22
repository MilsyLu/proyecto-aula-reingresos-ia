/**
 * Las tres formas del orbe, en su propio archivo.
 *
 * Vive aparte del componente a proposito. La portada necesita los nombres de
 * las formas para dibujar los botones, pero no debe arrastrar three.js al
 * cargar: si importara esto desde OrbeParticulas.tsx, el empaquetador juntaria
 * los dos y la carga diferida no serviria de nada. Son 529 kB de diferencia.
 */

export type Forma = 'cohorte' | 'variables' | 'trayectorias'

export const FORMAS: { id: Forma; etiqueta: string }[] = [
  { id: 'cohorte', etiqueta: 'La cohorte' },
  { id: 'variables', etiqueta: 'Las 50 variables' },
  { id: 'trayectorias', etiqueta: 'Las trayectorias' },
]
