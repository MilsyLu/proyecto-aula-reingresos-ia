import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import type { Forma } from './formas'

/**
 * El orbe de la portada.
 *
 * Cada una de las 3.600 partículas es una hospitalización real del conjunto de
 * prueba, con el riesgo que le calculó el modelo y lo que de verdad pasó
 * después. No es decoración: si alguien pregunta qué representa, hay respuesta.
 *
 * El color sigue la regla del proyecto. Por debajo del umbral de alerta, teal;
 * por encima, terracota. Y las que de verdad reingresaron llevan un núcleo
 * encendido. Así la portada muestra de un vistazo las tres cosas que importan:
 * cuánta gente hay, a cuánta se alerta, y cuánta vuelve.
 *
 * Tres formas, que son tres maneras de mirar lo mismo:
 *   cohorte      — la nube de pacientes, ordenada por riesgo
 *   variables    — la retícula de las 50 columnas del modelo
 *   trayectorias — el flujo de quienes vuelven al hospital
 */

interface Cohorte {
  particulas: number
  umbral: number
  riesgo: number[]
  reingreso: number[]
}

/** ¿La tarjeta gráfica es real o es emulación por software? */
function esGraficaPorSoftware(): boolean {
  try {
    const lienzo = document.createElement('canvas')
    const gl = lienzo.getContext('webgl2')
    if (!gl) return true
    const ext = gl.getExtension('WEBGL_debug_renderer_info')
    const parametro = ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER
    const tarjeta = String(gl.getParameter(parametro) || '')
    gl.getExtension('WEBGL_lose_context')?.loseContext()
    return /SwiftShader|llvmpipe|softpipe|Software|Basic Render/i.test(tarjeta)
  } catch {
    return true
  }
}

export function OrbeParticulas({
  forma,
  onFallo,
}: {
  forma: Forma
  onFallo?: () => void
}) {
  const contenedor = useRef<HTMLDivElement | null>(null)
  const formaRef = useRef(0)
  const [cohorte, setCohorte] = useState<Cohorte | null>(null)

  useEffect(() => {
    formaRef.current = forma === 'cohorte' ? 0 : forma === 'variables' ? 1 : 2
  }, [forma])

  // Los datos primero: sin ellos el orbe no tiene nada que dibujar.
  useEffect(() => {
    let vigente = true
    fetch('/cohorte.json')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('sin datos'))))
      .then((datos: Cohorte) => {
        if (vigente) setCohorte(datos)
      })
      .catch(() => {
        if (vigente) onFallo?.()
      })
    return () => {
      vigente = false
    }
  }, [onFallo])

  useEffect(() => {
    const nodo = contenedor.current
    if (!nodo || !cohorte) return

    const sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const porSoftware = esGraficaPorSoftware()

    let renderizador: THREE.WebGLRenderer
    try {
      renderizador = new THREE.WebGLRenderer({
        antialias: !porSoftware,
        alpha: true,
        powerPreference: 'high-performance',
      })
    } catch {
      onFallo?.()
      return
    }

    const densidad = porSoftware ? 1 : Math.min(window.devicePixelRatio || 1, 2)
    renderizador.outputColorSpace = THREE.SRGBColorSpace
    renderizador.setPixelRatio(densidad)

    const ancho = nodo.clientWidth || 520
    const alto = nodo.clientHeight || 520
    renderizador.setSize(ancho, alto)
    renderizador.domElement.style.display = 'block'
    renderizador.domElement.style.width = '100%'
    renderizador.domElement.style.height = '100%'
    nodo.appendChild(renderizador.domElement)

    const escena = new THREE.Scene()
    const camara = new THREE.PerspectiveCamera(42, ancho / alto, 0.1, 100)
    camara.position.set(0, 0, 5.2)

    // En pantallas pequenas se baja la cantidad: 3.600 particulas con mezcla
    // aditiva calientan un celular modesto.
    const total = ancho < 620 ? Math.min(1200, cohorte.particulas) : cohorte.particulas

    const enEsfera = new Float32Array(total * 3)
    const enReticula = new Float32Array(total * 3)
    const enFlujo = new Float32Array(total * 3)
    const semillas = new Float32Array(total)
    const riesgos = new Float32Array(total)
    const reingresos = new Float32Array(total)

    const anguloAureo = Math.PI * (3 - Math.sqrt(5))
    const lado = Math.ceil(Math.cbrt(total))
    const paso = cohorte.particulas / total

    // El riesgo se normaliza contra su propio rango: si se normalizara contra
    // 0-1, con un maximo real de 0,53 casi todo quedaria del mismo color.
    let minimo = Infinity
    let maximo = -Infinity
    for (let i = 0; i < total; i++) {
      const v = cohorte.riesgo[Math.floor(i * paso)]
      if (v < minimo) minimo = v
      if (v > maximo) maximo = v
    }
    const rango = Math.max(maximo - minimo, 1e-6)

    for (let i = 0; i < total; i++) {
      const fuente = Math.floor(i * paso)
      const i3 = i * 3

      // 1. Esfera de Fibonacci. El radio depende del riesgo: los pacientes de
      //    mayor riesgo quedan en la capa exterior, que es la que se ve.
      const t = i / total
      const y = 1 - t * 2
      const radioEnY = Math.sqrt(Math.max(0, 1 - y * y))
      const theta = anguloAureo * i
      const riesgoNormalizado = (cohorte.riesgo[fuente] - minimo) / rango
      const capa = 1.12 + riesgoNormalizado * 0.72

      enEsfera[i3] = Math.cos(theta) * radioEnY * capa
      enEsfera[i3 + 1] = y * capa
      enEsfera[i3 + 2] = Math.sin(theta) * radioEnY * capa

      // 2. Reticula: las 50 columnas como una matriz en el espacio.
      const gx = (i % lado) / (lado - 1) - 0.5
      const gy = (Math.floor(i / lado) % lado) / (lado - 1) - 0.5
      const gz = Math.floor(i / (lado * lado)) / (lado - 1) - 0.5
      enReticula[i3] = gx * 2.85
      enReticula[i3 + 1] = gy * 2.85
      enReticula[i3 + 2] = gz * 2.85

      // 3. Flujo toroidal: volver al hospital es un ciclo que se cierra.
      const mayor = t * Math.PI * 24
      const menor = t * Math.PI * 2
      const R = 1.45
      const r = 0.55 + 0.18 * Math.sin(mayor * 2)
      enFlujo[i3] = (R + r * Math.cos(mayor)) * Math.cos(menor)
      enFlujo[i3 + 1] = r * Math.sin(mayor) * 1.15
      enFlujo[i3 + 2] = (R + r * Math.cos(mayor)) * Math.sin(menor)

      semillas[i] = ((i * 9301 + 49297) % 233280) / 233280
      riesgos[i] = cohorte.riesgo[fuente]
      reingresos[i] = cohorte.reingreso[fuente]
    }

    const geometria = new THREE.BufferGeometry()
    geometria.setAttribute('position', new THREE.BufferAttribute(enEsfera, 3))
    geometria.setAttribute('aReticula', new THREE.BufferAttribute(enReticula, 3))
    geometria.setAttribute('aFlujo', new THREE.BufferAttribute(enFlujo, 3))
    geometria.setAttribute('aSemilla', new THREE.BufferAttribute(semillas, 1))
    geometria.setAttribute('aRiesgo', new THREE.BufferAttribute(riesgos, 1))
    geometria.setAttribute('aReingreso', new THREE.BufferAttribute(reingresos, 1))

    const uniformes = {
      uTiempo: { value: 0 },
      uDensidad: { value: densidad },
      uForma: { value: formaRef.current },
      uPuntero: { value: new THREE.Vector2(0, 0) },
      uUmbral: { value: cohorte.umbral },
      uMaximo: { value: maximo },
      // Teal para lo que no alcanza el umbral; terracota para lo que lo pasa.
      //
      // Los dos pares viven en la mitad clara de su rampa a proposito. Sobre un
      // fondo casi negro y con mezcla aditiva, un color oscuro no se ve apagado:
      // desaparece. Y como el 62 % de la cohorte queda por debajo del umbral,
      // usar ahi el teal mas hondo dejaba el orbe practicamente vacio.
      uTealHondo: { value: new THREE.Color('#2f9e97') },
      uTealClaro: { value: new THREE.Color('#bdf5f0') },
      uDatoClaro: { value: new THREE.Color('#f0b79b') },
      uDatoHondo: { value: new THREE.Color('#d4603d') },
      uBlanco: { value: new THREE.Color('#fff6f0') },
    }

    const material = new THREE.ShaderMaterial({
      uniforms: uniformes,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      vertexShader: `
        attribute vec3 aReticula;
        attribute vec3 aFlujo;
        attribute float aSemilla;
        attribute float aRiesgo;
        attribute float aReingreso;

        uniform float uTiempo;
        uniform float uDensidad;
        uniform float uForma;
        uniform vec2 uPuntero;

        varying float vAlfa;
        varying float vRiesgo;
        varying float vReingreso;
        varying float vHondura;

        void main() {
          float aReticulaPeso = smoothstep(0.0, 1.0, clamp(uForma, 0.0, 1.0))
                              * (1.0 - smoothstep(1.0, 2.0, uForma));
          float aFlujoPeso = smoothstep(1.0, 2.0, clamp(uForma, 1.0, 2.0));
          float aEsferaPeso = max(0.0, 1.0 - smoothstep(0.0, 1.0, uForma));

          vec3 base = position * aEsferaPeso + aReticula * aReticulaPeso + aFlujo * aFlujoPeso;

          float onda = sin(base.y * 2.2 + uTiempo * 1.1 + aSemilla * 6.2831) * 0.055;
          float rizo = cos(base.x * 2.5 - uTiempo * 0.9 + aSemilla * 3.1415) * 0.042;
          vec3 movido = base + normalize(base + vec3(0.0001)) * (onda + rizo);

          movido.x += uPuntero.x * 0.14 * (0.4 + aSemilla * 0.6);
          movido.y += uPuntero.y * 0.14 * (0.4 + aSemilla * 0.6);

          vec4 posicionVista = modelViewMatrix * vec4(movido, 1.0);
          gl_Position = projectionMatrix * posicionVista;

          // Las que reingresaron se dibujan mas grandes: son 424 de 3.600 y si
          // no, se pierden entre las demas.
          float tamano = mix(13.0, 23.0, aSemilla) + aReingreso * 8.0;
          gl_PointSize = tamano * uDensidad * (1.0 / max(1.2, -posicionVista.z));

          // Las de atras se atenuan para que se lea el volumen, pero sin
          // apagarse del todo: el orbe tiene que verse lleno, no hueco.
          vHondura = clamp((-posicionVista.z - 2.6) / 4.2, 0.0, 1.0);
          vAlfa = mix(1.0, 0.34, vHondura);
          vRiesgo = aRiesgo;
          vReingreso = aReingreso;
        }
      `,
      fragmentShader: `
        uniform float uUmbral;
        uniform float uMaximo;
        uniform vec3 uTealHondo;
        uniform vec3 uTealClaro;
        uniform vec3 uDatoClaro;
        uniform vec3 uDatoHondo;
        uniform vec3 uBlanco;

        varying float vAlfa;
        varying float vRiesgo;
        varying float vReingreso;
        varying float vHondura;

        void main() {
          vec2 uv = gl_PointCoord - vec2(0.5);
          float distancia = length(uv);
          if (distancia > 0.5) discard;

          float cuerpo = smoothstep(0.5, 0.06, distancia);
          float nucleo = smoothstep(0.22, 0.0, distancia);

          vec3 color;
          if (vRiesgo < uUmbral) {
            // No alcanza el umbral: no entra en la lista de llamadas.
            color = mix(uTealHondo, uTealClaro, vRiesgo / max(uUmbral, 0.0001));
          } else {
            float t = (vRiesgo - uUmbral) / max(uMaximo - uUmbral, 0.0001);
            color = mix(uDatoClaro, uDatoHondo, clamp(t, 0.0, 1.0));
          }

          // Quienes de verdad reingresaron llevan el nucleo encendido.
          color = mix(color, uBlanco, nucleo * (0.25 + vReingreso * 0.6) * (1.0 - vHondura));

          float alfa = cuerpo * vAlfa * (0.72 + vReingreso * 0.28);
          gl_FragColor = vec4(color, alfa);
        }
      `,
    })

    const puntos = new THREE.Points(geometria, material)
    escena.add(puntos)

    const destino = { x: 0, y: 0 }
    const actual = { x: 0, y: 0 }

    function alMover(e: PointerEvent) {
      const caja = nodo!.getBoundingClientRect()
      if (!caja.width || !caja.height) return
      destino.x = Math.max(-1, Math.min(1, ((e.clientX - caja.left) / caja.width) * 2 - 1))
      destino.y = Math.max(-1, Math.min(1, -(((e.clientY - caja.top) / caja.height) * 2 - 1)))
    }
    function alSalir() {
      destino.x = 0
      destino.y = 0
    }
    function alRedimensionar() {
      const w = nodo!.clientWidth || 520
      const h = nodo!.clientHeight || 520
      camara.aspect = w / h
      camara.updateProjectionMatrix()
      renderizador.setSize(w, h)
    }

    nodo.addEventListener('pointermove', alMover)
    nodo.addEventListener('pointerleave', alSalir)
    window.addEventListener('resize', alRedimensionar)

    let cuadro = 0
    let desmontado = false
    const reloj = new THREE.Clock()

    function dibujar() {
      if (desmontado) return
      const dt = Math.min(reloj.getDelta(), 0.1)

      if (!sinMovimiento) {
        uniformes.uTiempo.value = reloj.getElapsedTime()
        puntos.rotation.y += dt * 0.12
        puntos.rotation.x = THREE.MathUtils.damp(puntos.rotation.x, destino.y * 0.26, 3.5, dt)
      }

      actual.x = THREE.MathUtils.damp(actual.x, destino.x, 4.5, dt)
      actual.y = THREE.MathUtils.damp(actual.y, destino.y, 4.5, dt)
      uniformes.uPuntero.value.set(actual.x, actual.y)
      uniformes.uForma.value = THREE.MathUtils.damp(
        uniformes.uForma.value,
        formaRef.current,
        4.2,
        dt,
      )

      renderizador.render(escena, camara)

      // Con movimiento reducido se dibuja un solo cuadro y se para del todo.
      if (sinMovimiento) return
      cuadro = requestAnimationFrame(dibujar)
    }

    dibujar()

    return () => {
      desmontado = true
      cancelAnimationFrame(cuadro)
      nodo.removeEventListener('pointermove', alMover)
      nodo.removeEventListener('pointerleave', alSalir)
      window.removeEventListener('resize', alRedimensionar)
      geometria.dispose()
      material.dispose()
      renderizador.dispose()
      if (renderizador.domElement.parentNode === nodo) {
        nodo.removeChild(renderizador.domElement)
      }
    }
  }, [cohorte, onFallo])

  return (
    <div
      ref={contenedor}
      style={{ width: '100%', height: '100%', cursor: 'grab' }}
      aria-hidden="true"
    />
  )
}
