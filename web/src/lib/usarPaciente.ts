import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, ErrorApi } from './api'
import { LIMITES, type Opciones } from './tiposModelo'

/**
 * El estado del formulario de una hospitalizacion.
 *
 * Lo comparten Estimar y Paso a paso, y por eso vive aqui: que las dos
 * pantallas arranquen con el mismo paciente evita la confusion de ver 30,3 %
 * en una y 9,0 % en la otra sin saber por que.
 *
 * Los valores arrancan en los tipicos de la cohorte, que es el punto de
 * partida honesto: la primera cifra que ve alguien es la del paciente
 * promedio, no la de un caso escogido para impresionar.
 */
export function usarPaciente() {
  const [opciones, setOpciones] = useState<Opciones | null>(null)
  const [valores, setValores] = useState<Record<string, string | number>>({})
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let vigente = true
    api
      .obtener<Opciones>('/opciones')
      .then((datos) => {
        if (!vigente) return
        setOpciones(datos)
        setValores(Object.fromEntries(datos.campos.map((c) => [c.campo, c.tipico])))
      })
      .catch((falla) => {
        if (vigente) setError(falla instanceof ErrorApi ? falla.message : 'No se pudo cargar.')
      })
    return () => {
      vigente = false
    }
  }, [])

  const cambiar = useCallback((campo: string, valor: string | number) => {
    setValores((previos) => ({ ...previos, [campo]: valor }))
  }, [])

  const restablecer = useCallback(() => {
    if (opciones) {
      setValores(Object.fromEntries(opciones.campos.map((c) => [c.campo, c.tipico])))
    }
  }, [opciones])

  /** Los valores listos para la API: los numericos como numeros y dentro de rango. */
  const paraEnviar = useMemo(() => {
    const salida: Record<string, string | number> = {}
    for (const [campo, valor] of Object.entries(valores)) {
      const limite = LIMITES[campo]
      if (!limite) {
        salida[campo] = valor
        continue
      }
      const numero = Number(valor)
      // Un campo vacio o con letras se manda como el minimo en vez de como NaN:
      // asi la API responde algo util en lugar de un error de validacion que no
      // le dice nada a quien esta llenando el formulario.
      salida[campo] = Number.isFinite(numero)
        ? Math.min(Math.max(numero, limite.min), limite.max)
        : limite.min
    }
    return salida
  }, [valores])

  /** Si algo quedo fuera de rango, decirlo antes de enviar. */
  const fueraDeRango = useMemo(
    () =>
      Object.entries(valores)
        .filter(([campo, valor]) => {
          const limite = LIMITES[campo]
          if (!limite) return false
          const numero = Number(valor)
          return !Number.isFinite(numero) || numero < limite.min || numero > limite.max
        })
        .map(([campo]) => campo),
    [valores],
  )

  return { opciones, valores, cambiar, restablecer, paraEnviar, fueraDeRango, error }
}
