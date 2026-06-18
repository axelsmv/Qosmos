<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { RouterLink } from 'vue-router'
import * as THREE from 'three'

// --- 1. INTERFACES Y CONFIGURACIÓN FÍSICA ---
interface BlochVector {
  x: number
  y: number
  z: number
  purity: number
}

type Complex = { re: number; im: number }
type StateVector = Complex[]

// Presets de estado inicial para Alice (Q0)
const statePresets = [
  { name: '|0⟩ (Polo Norte)', theta: 0, phi: 0 },
  { name: '|1⟩ (Polo Sur)', theta: 180, phi: 0 },
  { name: '|+⟩ (Superposición X+)', theta: 90, phi: 0 },
  { name: '|−⟩ (Superposición X-)', theta: 90, phi: 180 },
  { name: '|i⟩ (Superposición Y+)', theta: 90, phi: 90 },
  { name: '|−i⟩ (Superposición Y-)', theta: 90, phi: 270 }
]

// --- 2. VARIABLES REACTIVAS DEL SIMULADOR ---
const currentStep = ref<number>(0)
const theta = ref<number>(0) // Ángulo polar (0 a 180)
const phi = ref<number>(0)   // Ángulo azimutal (0 a 360)

const measuredOutcome = ref<number | null>(null) // null o 0, 1, 2, 3
const isTransmitting = ref<boolean>(false)

const stateVector = ref<StateVector>(Array.from({ length: 8 }, () => ({ re: 0, im: 0 })))
const qubit0 = ref<BlochVector>({ x: 0, y: 0, z: 1, purity: 1 })
const qubit1 = ref<BlochVector>({ x: 0, y: 0, z: 1, purity: 1 })
const qubit2 = ref<BlochVector>({ x: 0, y: 0, z: 1, purity: 1 })

// --- 3. OPERACIONES MATEMÁTICAS CUÁNTICAS ---
const addComplex = (a: Complex, b: Complex): Complex => ({ re: a.re + b.re, im: a.im + b.im })
const mulComplex = (a: Complex, b: Complex): Complex => ({
  re: a.re * b.re - a.im * b.im,
  im: a.re * b.im + a.im * b.re
})
const conjComplex = (a: Complex): Complex => ({ re: a.re, im: -a.im })

function apply1QubitGate(state: StateVector, gate: Complex[][], target: number): StateVector {
  const nextState = Array.from({ length: 8 }, () => ({ re: 0, im: 0 }))
  const mask = 1 << target
  
  const g00 = gate[0]?.[0] || { re: 0, im: 0 }
  const g01 = gate[0]?.[1] || { re: 0, im: 0 }
  const g10 = gate[1]?.[0] || { re: 0, im: 0 }
  const g11 = gate[1]?.[1] || { re: 0, im: 0 }
  
  for (let i = 0; i < 8; i++) {
    if ((i & mask) === 0) {
      const i0 = i
      const i1 = i | mask
      
      const c0 = state[i0] || { re: 0, im: 0 }
      const c1 = state[i1] || { re: 0, im: 0 }
      
      nextState[i0] = addComplex(
        mulComplex(g00, c0),
        mulComplex(g01, c1)
      )
      
      nextState[i1] = addComplex(
        mulComplex(g10, c0),
        mulComplex(g11, c1)
      )
    }
  }
  return nextState
}

function applyCnotGate(state: StateVector, control: number, target: number): StateVector {
  const nextState = [...state]
  const controlMask = 1 << control
  const targetMask = 1 << target
  
  for (let i = 0; i < 8; i++) {
    if ((i & controlMask) !== 0 && (i & targetMask) === 0) {
      const i0 = i
      const i1 = i | targetMask
      const temp = nextState[i0]
      const val1 = nextState[i1]
      if (temp && val1) {
        nextState[i0] = val1
        nextState[i1] = temp
      }
    }
  }
  return nextState
}

function getQubitBlochVector(state: StateVector, qubit: number): BlochVector {
  const X_matrix = [
    [{ re: 0, im: 0 }, { re: 1, im: 0 }],
    [{ re: 1, im: 0 }, { re: 0, im: 0 }]
  ]
  const Y_matrix = [
    [{ re: 0, im: 0 }, { re: 0, im: -1 }],
    [{ re: 0, im: 1 }, { re: 0, im: 0 }]
  ]
  const Z_matrix = [
    [{ re: 1, im: 0 }, { re: 0, im: 0 }],
    [{ re: 0, im: 0 }, { re: -1, im: 0 }]
  ]
  
  const stateX = apply1QubitGate(state, X_matrix, qubit)
  const stateY = apply1QubitGate(state, Y_matrix, qubit)
  const stateZ = apply1QubitGate(state, Z_matrix, qubit)
  
  let x = 0
  let y = 0
  let z = 0
  
  for (let i = 0; i < 8; i++) {
    const s = state[i]
    const sx = stateX[i]
    const sy = stateY[i]
    const sz = stateZ[i]
    if (s && sx && sy && sz) {
      x += s.re * sx.re + s.im * sx.im
      y += s.re * sy.re + s.im * sy.im
      z += s.re * sz.re + s.im * sz.im
    }
  }
  
  const purity = Math.sqrt(x * x + y * y + z * z)
  
  return {
    x: Math.round(x * 10000) / 10000,
    y: Math.round(y * 10000) / 10000,
    z: Math.round(z * 10000) / 10000,
    purity: Math.round(purity * 10000) / 10000
  }
}

// --- 4. MOTOR SIMULADOR PRINCIPAL ---
function runSimulationUpToStep(step: number) {
  let sv: StateVector = Array.from({ length: 8 }, () => ({ re: 0, im: 0 }))
  sv[0] = { re: 1, im: 0 }
  
  const thetaRad = (theta.value * Math.PI) / 180
  const phiRad = (phi.value * Math.PI) / 180
  const alpha = Math.cos(thetaRad / 2)
  const beta_re = Math.cos(phiRad) * Math.sin(thetaRad / 2)
  const beta_im = Math.sin(phiRad) * Math.sin(thetaRad / 2)
  
  sv[0] = { re: alpha, im: 0 }
  sv[1] = { re: beta_re, im: beta_im }
  
  if (step < 1) {
    stateVector.value = sv
    updateBlochVectors()
    return
  }
  
  const H_matrix = [
    [{ re: 1 / Math.sqrt(2), im: 0 }, { re: 1 / Math.sqrt(2), im: 0 }],
    [{ re: 1 / Math.sqrt(2), im: 0 }, { re: -1 / Math.sqrt(2), im: 0 }]
  ]
  sv = apply1QubitGate(sv, H_matrix, 1)
  sv = applyCnotGate(sv, 1, 2)
  
  if (step < 2) {
    stateVector.value = sv
    updateBlochVectors()
    return
  }
  
  sv = applyCnotGate(sv, 0, 1)
  sv = apply1QubitGate(sv, H_matrix, 0)
  
  if (step < 3) {
    stateVector.value = sv
    updateBlochVectors()
    return
  }
  
  if (measuredOutcome.value === null) {
    measuredOutcome.value = Math.floor(Math.random() * 4)
  }
  
  const m = measuredOutcome.value
  const collapsedSv = Array.from({ length: 8 }, () => ({ re: 0, im: 0 }))
  const idx0 = m
  const idx1 = m + 4
  
  const sv0 = sv[idx0]
  const sv1 = sv[idx1]
  if (sv0 && sv1) {
    collapsedSv[idx0] = { re: sv0.re * 2, im: sv0.im * 2 }
    collapsedSv[idx1] = { re: sv1.re * 2, im: sv1.im * 2 }
  }
  
  sv = collapsedSv
  
  if (step < 4) {
    stateVector.value = sv
    updateBlochVectors()
    return
  }
  
  const m0 = m & 1
  const m1 = (m >> 1) & 1
  
  if (m1 === 1) {
    const X_matrix = [
      [{ re: 0, im: 0 }, { re: 1, im: 0 }],
      [{ re: 1, im: 0 }, { re: 0, im: 0 }]
    ]
    sv = apply1QubitGate(sv, X_matrix, 2)
  }
  
  if (m0 === 1) {
    const Z_matrix = [
      [{ re: 1, im: 0 }, { re: 0, im: 0 }],
      [{ re: 0, im: 0 }, { re: -1, im: 0 }]
    ]
    sv = apply1QubitGate(sv, Z_matrix, 2)
  }
  
  stateVector.value = sv
  updateBlochVectors()
}

function updateBlochVectors() {
  qubit0.value = getQubitBlochVector(stateVector.value, 0)
  qubit1.value = getQubitBlochVector(stateVector.value, 1)
  qubit2.value = getQubitBlochVector(stateVector.value, 2)
  
  if (renderer0) renderer0.updateVector(qubit0.value.x, qubit0.value.y, qubit0.value.z)
  if (renderer1) renderer1.updateVector(qubit1.value.x, qubit1.value.y, qubit1.value.z)
  if (renderer2) renderer2.updateVector(qubit2.value.x, qubit2.value.y, qubit2.value.z)
}

// Watchers para responder al cambio de estado en vivo
watch([theta, phi], () => {
  if (currentStep.value === 0) {
    runSimulationUpToStep(0)
  }
})

// Aplicar presets de estado
const applyPreset = (presetTheta: number, presetPhi: number) => {
  theta.value = presetTheta
  phi.value = presetPhi
  if (currentStep.value !== 0) {
    currentStep.value = 0
  }
  runSimulationUpToStep(0)
}

// --- 5. RENDERIZACIÓN 3D CON THREE.JS ---
const container0 = ref<HTMLElement | null>(null)
const container1 = ref<HTMLElement | null>(null)
const container2 = ref<HTMLElement | null>(null)

let renderer0: BlochSphereRenderer | null = null
let renderer1: BlochSphereRenderer | null = null
let renderer2: BlochSphereRenderer | null = null

class BlochSphereRenderer {
  container: HTMLElement
  scene!: THREE.Scene
  camera!: THREE.PerspectiveCamera
  renderer!: THREE.WebGLRenderer
  stateArrow!: THREE.ArrowHelper
  animationId!: number
  color: number
  isDestroyed: boolean = false

  constructor(container: HTMLElement, color: number) {
    this.container = container
    this.color = color
    this.init()
  }

  init() {
    const width = this.container.clientWidth || 180
    const height = this.container.clientHeight || 180

    this.scene = new THREE.Scene()
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10)
    this.camera.position.set(1.8, 1.3, 2.2) 
    this.camera.lookAt(0, 0, 0)

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    this.renderer.setSize(width, height)
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    
    this.container.innerHTML = ''
    this.container.appendChild(this.renderer.domElement)

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8)
    this.scene.add(ambientLight)

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.4)
    dirLight.position.set(3, 4, 3)
    this.scene.add(dirLight)

    const sphereGeo = new THREE.SphereGeometry(1, 24, 24)
    const sphereMat = new THREE.MeshBasicMaterial({ 
      color: 0x38bdf8, 
      transparent: true, 
      opacity: 0.06, 
      wireframe: true 
    })
    const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat)
    this.scene.add(sphereMesh)

    // Ejes cartesianos
    this.createAxis(new THREE.Vector3(-1.25, 0, 0), new THREE.Vector3(1.25, 0, 0), 0xef4444) // X Rojo
    this.createAxis(new THREE.Vector3(0, 0, -1.25), new THREE.Vector3(0, 0, 1.25), 0x3b82f6) // Y Azul
    this.createAxis(new THREE.Vector3(0, -1.25, 0), new THREE.Vector3(0, 1.25, 0), 0x22c55e) // Z Verde

    // Anillos meridianos
    const ringGeo = new THREE.RingGeometry(0.99, 1.01, 32)
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x475569, side: THREE.DoubleSide, transparent: true, opacity: 0.25 })
    
    const equator = new THREE.Mesh(ringGeo, ringMat)
    equator.rotation.x = Math.PI / 2
    this.scene.add(equator)
    
    const meridian1 = new THREE.Mesh(ringGeo, ringMat)
    this.scene.add(meridian1)

    const meridian2 = new THREE.Mesh(ringGeo, ringMat)
    meridian2.rotation.y = Math.PI / 2
    this.scene.add(meridian2)

    // Polos Z
    const poleGeo = new THREE.SphereGeometry(0.04, 8, 8)
    const poleNorth = new THREE.Mesh(poleGeo, new THREE.MeshBasicMaterial({ color: 0x22c55e }))
    poleNorth.position.set(0, 1, 0)
    this.scene.add(poleNorth)
    
    const poleSouth = new THREE.Mesh(poleGeo, new THREE.MeshBasicMaterial({ color: 0xef4444 }))
    poleSouth.position.set(0, -1, 0)
    this.scene.add(poleSouth)

    const origin = new THREE.Vector3(0, 0, 0)
    const arrowDir = new THREE.Vector3(0, 1, 0)
    this.stateArrow = new THREE.ArrowHelper(arrowDir, origin, 1.0, this.color, 0.22, 0.08)
    this.scene.add(this.stateArrow)

    const animate = () => {
      if (this.isDestroyed) return
      this.animationId = requestAnimationFrame(animate)
      this.scene.rotation.y += 0.0035
      this.renderer.render(this.scene, this.camera)
    }
    animate()
  }

  createAxis(start: THREE.Vector3, end: THREE.Vector3, color: number) {
    const points = [start, end]
    const geo = new THREE.BufferGeometry().setFromPoints(points)
    const mat = new THREE.LineBasicMaterial({ color: color, transparent: true, opacity: 0.25 })
    const line = new THREE.Line(geo, mat)
    this.scene.add(line)
  }

  updateVector(x_bloch: number, y_bloch: number, z_bloch: number) {
    const dir = new THREE.Vector3(x_bloch, z_bloch, y_bloch)
    const length = dir.length()
    
    if (length > 0.05) {
      this.stateArrow.setDirection(dir.clone().normalize())
      this.stateArrow.setLength(length, Math.min(0.2, length * 0.2), Math.min(0.08, length * 0.08))
      this.stateArrow.visible = true
    } else {
      this.stateArrow.visible = false
    }
  }

  resize() {
    if (!this.container || this.isDestroyed) return
    const width = this.container.clientWidth
    const height = this.container.clientHeight
    if (width > 0 && height > 0) {
      this.camera.aspect = width / height
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(width, height)
    }
  }

  destroy() {
    this.isDestroyed = true
    cancelAnimationFrame(this.animationId)
    if (this.renderer) {
      this.renderer.dispose()
    }
  }
}

const handleResize = () => {
  if (renderer0) renderer0.resize()
  if (renderer1) renderer1.resize()
  if (renderer2) renderer2.resize()
}

onMounted(async () => {
  await nextTick()
  
  if (container0.value) renderer0 = new BlochSphereRenderer(container0.value, 0xa855f7) // Q0 Purple
  if (container1.value) renderer1 = new BlochSphereRenderer(container1.value, 0x06b6d4) // Q1 Cyan
  if (container2.value) renderer2 = new BlochSphereRenderer(container2.value, 0x10b981) // Q2 Emerald
  
  runSimulationUpToStep(0)
  
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  if (renderer0) renderer0.destroy()
  if (renderer1) renderer1.destroy()
  if (renderer2) renderer2.destroy()
})

// --- 6. TEXTOS Y ANALOGÍAS COMPLEMENTARIAS ---
const stepTitles = [
  'Paso 0: Preparar el Estado de Alice',
  'Paso 1: Generar el Enlace Entrelazado (Par Bell)',
  'Paso 2: Operación de Medición de Bell en Alice',
  'Paso 3: Colapso y Transmisión por Canal Clásico',
  'Paso 4: Corrección de Bob (Teletransportación Completa)'
]

const stepDescriptions = [
  'Alice prepara su qubit original q₀ en un estado cuántico deseado |ψ⟩. Puedes arrastrar los deslizadores de los ángulos θ y φ o usar los botones de preajustes rápidos para ver el estado en la esfera de Bloch.',
  'Alice y Bob crean un enlace entrelazado. Se aplica una compuerta Hadamard (H) en q₁ y una CNOT de q₁ a q₂, creando el par de Bell. Nota que los vectores de q₁ y q₂ se encogen al centro: ¡sus estados individuales se desdibujan y se vuelven uno solo correlacionado!',
  'Alice acopla el mensaje q₀ con su qubit del enlace entrelazado q₁ aplicando una CNOT de q₀ a q₁ y una compuerta H en q₀. Esto codifica el estado original en la base entrelazada.',
  'Alice mide q₀ y q₁, lo que colapsa irreversiblemente su superposición cuántica a un valor clásico (00, 01, 10 o 11). El estado de q₀ se destruye (No Clonación). Luego, Alice envía estos 2 bits clásicos a Bob usando fibra óptica o radio tradicional.',
  'Bob recibe los 2 bits clásicos. Dependiendo de los valores c₀ y c₁, Bob sabe cómo rotar su qubit q₂ para reconstruir el estado original: aplicando X (NOT) si c₁=1, y Z (Fase) si c₀=1. ¡Mira cómo la esfera de Bob recupera el vector de Alice!'
]

const stepAnalogies = [
  '💡 Analogía: Imagina que Alice quiere enviar una dirección secreta escrita en una brújula. Ella la ajusta en un ángulo específico, pero en física cuántica, no podemos simplemente hacerle una foto o copiarla directamente.',
  '💡 Analogía: Es como cortar una carta por la mitad en un patrón caótico y meter cada mitad en un sobre cerrado. Alice se queda un sobre y le envía el otro sobre a Bob. Aunque no saben qué mitad tienen, sus contenidos están atados.',
  '💡 Analogía: Alice mezcla el sobre secreto con su mitad de la carta cortada. Al compararlos localmente, está entrelazando el misterio de la brújula con la carta que comparte con Bob.',
  '💡 Analogía: Al medir, Alice destruye la brújula original. El resultado le da dos coordenadas clásicas simples (ej: "cara o cruz"). Alice teclea el resultado por WhatsApp y se lo envía a Bob. ¡Los bits viajan volando!',
  '💡 Analogía: Bob lee el mensaje. Si dice "cruz", gira su mitad de la carta 180 grados. Al aplicar la corrección física basada en los bits de Alice, la brújula en su mano adopta exactamente la dirección secreta original. ¡El estado ha sido recreado a kilómetros de distancia!'
]

// --- 7. NAVEGACIÓN Y CONTROLES DEL STEPPER ---
const nextStep = () => {
  if (currentStep.value < 4) {
    if (currentStep.value === 2) {
      // Activar animación al ir al paso 3 (medición)
      isTransmitting.value = true
      runSimulationUpToStep(3)
      setTimeout(() => {
        isTransmitting.value = false
      }, 1800)
    } else {
      runSimulationUpToStep(currentStep.value + 1)
    }
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    if (currentStep.value < 3) {
      measuredOutcome.value = null // reset measurement
    }
    runSimulationUpToStep(currentStep.value)
  }
}

const resetSimulation = () => {
  currentStep.value = 0
  measuredOutcome.value = null
  isTransmitting.value = false
  runSimulationUpToStep(0)
}

// Medida clásica en bits
const measuredBits = computed(() => {
  if (measuredOutcome.value === null) return { c0: 0, c1: 0 }
  return {
    c0: measuredOutcome.value & 1,
    c1: (measuredOutcome.value >> 1) & 1
  }
})

// Dirac Notation helper
const diracText = computed(() => {
  const thetaRad = (theta.value * Math.PI) / 180
  const phiRad = (phi.value * Math.PI) / 180
  const alpha = Math.cos(thetaRad / 2).toFixed(3)
  const beta_re = (Math.cos(phiRad) * Math.sin(thetaRad / 2)).toFixed(3)
  const beta_im = (Math.sin(phiRad) * Math.sin(thetaRad / 2)).toFixed(3)
  
  let betaPart = ''
  if (parseFloat(beta_im) === 0) {
    betaPart = `${beta_re}`
  } else {
    betaPart = `(${beta_re} + ${beta_im}i)`
  }
  
  return `|ψ⟩ = ${alpha}|0⟩ + ${betaPart}|1⟩`
})

const formatCoord = (val: number) => {
  return val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2)
}

const formatPurity = (purity: number) => {
  return `${(purity * 100).toFixed(0)}%`
}

// Formateador Dirac para Bob (Q2)
const bobDiracText = computed(() => {
  if (currentStep.value < 3) {
    return '|q₂⟩ = |0⟩ (En reposo / Entrelazado)'
  }
  
  const thetaRad = (theta.value * Math.PI) / 180
  const phiRad = (phi.value * Math.PI) / 180
  const alphaStr = Math.cos(thetaRad / 2).toFixed(3)
  const beta_re = Math.cos(phiRad) * Math.sin(thetaRad / 2)
  const beta_im = Math.sin(phiRad) * Math.sin(thetaRad / 2)
  
  if (currentStep.value === 3) {
    // Estado colapsado sin corregir
    const m = measuredOutcome.value
    if (m === 0) {
      return `|q₂⟩ = ${alphaStr}|0⟩ + ${beta_re.toFixed(3)}|1⟩ (Sin cambios)`
    } else if (m === 1) {
      return `|q₂⟩ = ${alphaStr}|0⟩ - ${beta_re.toFixed(3)}|1⟩ (Fase invertida)`
    } else if (m === 2) {
      return `|q₂⟩ = ${beta_re.toFixed(3)}|0⟩ + ${alphaStr}|1⟩ (Valores invertidos)`
    } else {
      return `|q₂⟩ = -${beta_re.toFixed(3)}|0⟩ + ${alphaStr}|1⟩ (Invertido y desfasado)`
    }
  }
  
  // Paso 4: Corregido
  const betaPart = Math.abs(beta_im) < 0.001 ? `${beta_re.toFixed(3)}` : `(${beta_re.toFixed(3)} + ${beta_im.toFixed(3)}i)`
  return `|q₂⟩ = ${alphaStr}|0⟩ + ${betaPart}|1⟩ (¡Idéntico a Alice!)`
})
</script>

<template>
  <main class="teleport-view-container">
    <!-- Encabezado con Botón de Retorno -->
    <header class="view-header">
      <div class="header-nav">
        <router-link to="/" class="btn-back">← Volver al Menú</router-link>
      </div>
      <h1>Teletransportador Cuántico</h1>
      <p>Simulador Dinámico de Estado Físico de 3 Qubits</p>
    </header>

    <div class="simulator-layout">
      <!-- PANEL IZQUIERDO: CONTROLES DEL STEPPER Y MODO FERIA -->
      <aside class="side-panel">
        <div class="card stepper-card">
          <div class="stepper-header-row">
            <h3 class="stepper-title">Control del Protocolo</h3>
            <span class="step-badge">Paso {{ currentStep }} de 4</span>
          </div>

          <h4 class="step-subtitle">{{ stepTitles[currentStep] }}</h4>
          <p class="step-description">{{ stepDescriptions[currentStep] }}</p>

          <!-- Componentes interactivos por paso -->
          <div class="step-interactive-area">
            <!-- Paso 0: Control de Sliders de Estado -->
            <div v-if="currentStep === 0" class="state-prep-controls">
              <div class="preset-buttons-grid">
                <button 
                  v-for="preset in statePresets" 
                  :key="preset.name" 
                  @click="applyPreset(preset.theta, preset.phi)"
                  class="btn-preset"
                >
                  {{ preset.name }}
                </button>
              </div>

              <div class="slider-group">
                <div class="slider-info-row">
                  <label>Ángulo Polar (θ - Latitud)</label>
                  <span>{{ theta }}°</span>
                </div>
                <input 
                  type="range" 
                  v-model.number="theta" 
                  min="0" 
                  max="180" 
                  class="slider"
                />
              </div>

              <div class="slider-group">
                <div class="slider-info-row">
                  <label>Ángulo Azimutal (φ - Longitud)</label>
                  <span>{{ phi }}°</span>
                </div>
                <input 
                  type="range" 
                  v-model.number="phi" 
                  min="0" 
                  max="360" 
                  class="slider"
                />
              </div>

              <div class="math-readout">
                <span>Estado de Alice:</span>
                <strong class="font-mono text-purple">{{ diracText }}</strong>
              </div>
            </div>

            <!-- Paso 1: Generar Bell Pair -->
            <div v-if="currentStep === 1" class="step-action-pane">
              <div class="bell-graphics">
                <span class="bell-wave cyan-pulse">q₁ (Alice)</span>
                <span class="bell-link">🔗 Entrelazamiento</span>
                <span class="bell-wave emerald-pulse">q₂ (Bob)</span>
              </div>
              <button @click="nextStep" class="btn-step-action cyan-btn">
                Crear Enlace Entrelazado
              </button>
            </div>

            <!-- Paso 2: Bell Measurement prep -->
            <div v-if="currentStep === 2" class="step-action-pane">
              <div class="bell-operations-graphics">
                <div class="op-box">q₀ ──●── [H] ──</div>
                <div class="op-box">q₁ ──⊕─────────</div>
              </div>
              <button @click="nextStep" class="btn-step-action purple-btn">
                Aplicar Compuertas de Alice
              </button>
            </div>

            <!-- Paso 3: Medición y envío -->
            <div v-if="currentStep === 3" class="step-action-pane">
              <div v-if="measuredOutcome !== null" class="measurement-results-card">
                <div class="bit-badge-wrapper">
                  <div class="bit-circle">c₀ = {{ measuredBits.c0 }}</div>
                  <div class="bit-circle">c₁ = {{ measuredBits.c1 }}</div>
                </div>
                <p class="medida-text">¡Medición completada! Bits enviados por canal clásico.</p>
              </div>
              <button @click="nextStep" class="btn-step-action blue-btn" :disabled="isTransmitting">
                {{ isTransmitting ? 'Transmitiendo Bits...' : 'Medir y Transmitir' }}
              </button>
            </div>

            <!-- Paso 4: Correcciones y Finalización -->
            <div v-if="currentStep === 4" class="step-action-pane">
              <div class="success-alert">
                <div class="success-icon">✨</div>
                <div>
                  <strong>¡Teletransportación Completada!</strong>
                  <p style="margin: 3px 0 0 0; font-size: 0.75rem; color: #a7f3d0;">
                    El estado cuántico original de Alice se ha recreado exactamente en el qubit de Bob sin clonarse.
                  </p>
                </div>
              </div>
              <button @click="resetSimulation" class="btn-step-action reset-btn">
                Simular de Nuevo (Reiniciar)
              </button>
            </div>
          </div>

          <!-- Botones de Navegación del Stepper -->
          <div class="stepper-nav-row">
            <button 
              @click="prevStep" 
              :disabled="currentStep === 0 || isTransmitting" 
              class="btn-nav back"
            >
              ← Atrás
            </button>
            <button 
              @click="nextStep" 
              :disabled="currentStep === 4 || isTransmitting" 
              class="btn-nav next"
            >
              Siguiente →
            </button>
          </div>
        </div>

        <!-- CARD MODO FERIA CIENTÍFICA -->
        <div class="card analogy-card">
          <h3 style="color: #a855f7; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            🎓 Explicación Didáctica
          </h3>
          <p class="analogy-text">{{ stepAnalogies[currentStep] }}</p>
        </div>
      </aside>

      <!-- PANEL PRINCIPAL: ESFERAS DE BLOCH Y CIRCUITO -->
      <main class="main-simulator">
        <!-- SECCIÓN DE ESFERAS DE BLOCH -->
        <div class="card visualizer-card">
          <div class="visualizer-header">
            <h3>Visualización en la Esfera de Bloch</h3>
            <span class="purity-badge">3 Qubits en Espacio de Hilbert ℂ⁸</span>
          </div>

          <div class="bloch-spheres-grid">
            <!-- Qubit 0 -->
            <div class="qubit-card q0-border" :class="{ 'active-q': currentStep <= 3 }">
              <div class="qubit-header">
                <span class="q-badge q0-bg">q₀</span>
                <span>Alice (Original)</span>
              </div>
              <div ref="container0" class="canvas-container"></div>
              <div class="qubit-data font-mono">
                <div class="coord-row">
                  <span>Vector:</span>
                  <span>[{{ formatCoord(qubit0.x) }}, {{ formatCoord(qubit0.y) }}, {{ formatCoord(qubit0.z) }}]</span>
                </div>
                <div class="coord-row">
                  <span>Coherencia:</span>
                  <span>{{ formatPurity(qubit0.purity) }}</span>
                </div>
              </div>
            </div>

            <!-- Qubit 1 -->
            <div class="qubit-card q1-border" :class="{ 'active-q': currentStep >= 1 }">
              <div class="qubit-header">
                <span class="q-badge q1-bg">q₁</span>
                <span>Alice (Enlace)</span>
              </div>
              <div ref="container1" class="canvas-container"></div>
              <div class="qubit-data font-mono">
                <div class="coord-row">
                  <span>Vector:</span>
                  <span>[{{ formatCoord(qubit1.x) }}, {{ formatCoord(qubit1.y) }}, {{ formatCoord(qubit1.z) }}]</span>
                </div>
                <div class="coord-row">
                  <span>Coherencia:</span>
                  <span>{{ formatPurity(qubit1.purity) }}</span>
                </div>
              </div>
            </div>

            <!-- Qubit 2 -->
            <div class="qubit-card q2-border" :class="{ 'active-q': currentStep >= 1 }">
              <div class="qubit-header">
                <span class="q-badge q2-bg">q₂</span>
                <span>Bob (Destinatario)</span>
              </div>
              <div ref="container2" class="canvas-container"></div>
              <div class="qubit-data font-mono">
                <div class="coord-row">
                  <span>Vector:</span>
                  <span>[{{ formatCoord(qubit2.x) }}, {{ formatCoord(qubit2.y) }}, {{ formatCoord(qubit2.z) }}]</span>
                </div>
                <div class="coord-row">
                  <span>Coherencia:</span>
                  <span>{{ formatPurity(qubit2.purity) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ANIMACIÓN CLÁSICA TRANSPORTE BITS -->
          <div class="animation-stage-container" style="position: relative; overflow: hidden; height: 30px; margin-top: 10px;">
            <div class="classical-channel-container" v-if="isTransmitting">
              <div class="classical-fiber-line"></div>
              <div class="flying-packet packet-0">c₀ = {{ measuredBits.c0 }}</div>
              <div class="flying-packet packet-1">c₁ = {{ measuredBits.c1 }}</div>
            </div>
          </div>
        </div>

        <!-- ESQUEMA DE CIRCUITO SVG DINÁMICO -->
        <div class="card circuit-card">
          <h3>Circuito Cuántico del Teletransportador</h3>
          <div class="circuit-svg-container">
            <svg viewBox="0 0 680 180" class="circuit-svg">
              <!-- Grid wires -->
              <line x1="80" y1="40" x2="600" y2="40" class="wire" :class="{ highlighted: currentStep >= 0 }" />
              <line x1="80" y1="90" x2="600" y2="90" class="wire" :class="{ highlighted: currentStep >= 1 }" />
              <line x1="80" y1="140" x2="600" y2="140" class="wire" :class="{ highlighted: currentStep >= 1 }" />

              <!-- Wire Labels -->
              <text x="30" y="44" class="label-q">|q₀⟩</text>
              <text x="30" y="94" class="label-q">|q₁⟩</text>
              <text x="30" y="144" class="label-q">|q₂⟩</text>

              <!-- Alice/Bob Boundary divider -->
              <line x1="380" y1="10" x2="380" y2="170" class="boundary-line" />
              <text x="210" y="22" class="boundary-label">Laboratorio de Alice</text>
              <text x="440" y="22" class="boundary-label">Laboratorio de Bob</text>

              <!-- Step 0: Prep box -->
              <g class="gate-group" :class="{ active: currentStep === 0 }">
                <rect x="90" y="25" width="50" height="30" class="gate-box prep" />
                <text x="115" y="44" class="gate-text">Prep</text>
              </g>

              <!-- Step 1: Bell State Generation -->
              <g class="gate-group" :class="{ active: currentStep === 1, done: currentStep > 1 }">
                <!-- H on q1 -->
                <rect x="160" y="75" width="30" height="30" class="gate-box" />
                <text x="175" y="94" class="gate-text">H</text>
                <!-- CNOT q1 -> q2 -->
                <circle cx="215" cy="90" r="4" class="cnot-control" />
                <line x1="215" y1="90" x2="215" y2="140" class="cnot-line" />
                <circle cx="215" cy="140" r="8" class="cnot-target-bg" />
                <line x1="215" y1="132" x2="215" y2="148" class="cnot-target-line" />
                <line x1="207" y1="140" x2="223" y2="140" class="cnot-target-line" />
              </g>

              <!-- Step 2: Bell Measurement Prep -->
              <g class="gate-group" :class="{ active: currentStep === 2, done: currentStep > 2 }">
                <!-- CNOT q0 -> q1 -->
                <circle cx="270" cy="40" r="4" class="cnot-control" />
                <line x1="270" y1="40" x2="270" y2="90" class="cnot-line" />
                <circle cx="270" cy="90" r="8" class="cnot-target-bg" />
                <line x1="270" y1="82" x2="270" y2="98" class="cnot-target-line" />
                <line x1="262" y1="90" x2="278" y2="90" class="cnot-target-line" />

                <!-- H on q0 -->
                <rect x="310" y="25" width="30" height="30" class="gate-box" />
                <text x="325" y="44" class="gate-text">H</text>
              </g>

              <!-- Step 3: Measurement boxes -->
              <g class="gate-group" :class="{ active: currentStep === 3, done: currentStep > 3 }">
                <!-- M on q0 -->
                <rect x="395" y="25" width="30" height="30" class="gate-box measure" />
                <path d="M 402 48 Q 410 37 418 48 M 410 49 L 417 38" class="measure-icon" />
                <text x="428" y="42" class="measured-bit-val" v-if="currentStep >= 3">{{ measuredBits.c0 }}</text>

                <!-- M on q1 -->
                <rect x="395" y="75" width="30" height="30" class="gate-box measure" />
                <path d="M 402 98 Q 410 87 418 98 M 410 99 L 417 88" class="measure-icon" />
                <text x="428" y="92" class="measured-bit-val" v-if="currentStep >= 3">{{ measuredBits.c1 }}</text>

                <!-- Classical double lines from Alice to Bob's corrections -->
                <line x1="410" y1="55" x2="410" y2="120" class="classical-wire-vert" />
                <line x1="413" y1="55" x2="413" y2="120" class="classical-wire-vert" />
                <line x1="410" y1="120" x2="555" y2="120" class="classical-wire-horiz" />
                <line x1="413" y1="123" x2="555" y2="123" class="classical-wire-horiz" />

                <line x1="425" y1="90" x2="425" y2="105" class="classical-wire-vert" />
                <line x1="428" y1="90" x2="428" y2="105" class="classical-wire-vert" />
                <line x1="428" y1="105" x2="495" y2="105" class="classical-wire-horiz" />
                <line x1="425" y1="108" x2="495" y2="108" class="classical-wire-horiz" />
              </g>

              <!-- Step 4: Corrections by Bob -->
              <g class="gate-group" :class="{ active: currentStep === 4 }">
                <!-- X Correction -->
                <rect x="480" y="125" width="30" height="30" class="gate-box correction-gate" :class="{ triggered: measuredBits.c1 === 1 && currentStep >= 4 }" />
                <text x="495" y="144" class="gate-text font-bold">X</text>

                <!-- Z Correction -->
                <rect x="540" y="125" width="30" height="30" class="gate-box correction-gate" :class="{ triggered: measuredBits.c0 === 1 && currentStep >= 4 }" />
                <text x="555" y="144" class="gate-text font-bold">Z</text>
              </g>
            </svg>
          </div>
        </div>

        <!-- COMPARADOR DE ESTADOS FINALES -->
        <div class="card comparison-card" v-if="currentStep >= 3">
          <div class="comparison-header">
            <h3>Comparador de Estados Cuánticos</h3>
            <span class="status-indicator" :class="{ success: currentStep === 4 }">
              {{ currentStep === 4 ? 'Teletransportación Completada con Éxito' : 'Esperando Corrección de Bob...' }}
            </span>
          </div>

          <div class="comparison-grid">
            <div class="comp-col">
              <span class="comp-lbl">Estado inicial en Alice (|ψ⟩):</span>
              <div class="state-math-box purple-border">
                <span class="font-mono">{{ diracText }}</span>
              </div>
            </div>
            
            <div class="arrow-between">➔</div>

            <div class="comp-col">
              <span class="comp-lbl">Estado final en Bob (|q₂⟩):</span>
              <div class="state-math-box" :class="currentStep === 4 ? 'emerald-border animate-glow' : 'gray-border'">
                <span class="font-mono">{{ bobDiracText }}</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </main>
</template>

<style scoped>
.teleport-view-container {
  min-height: 100vh;
  padding: 20px;
  background-color: #080d1a;
  color: #f8fafc;
  box-sizing: border-box;
}

/* Header */
.view-header {
  text-align: center;
  margin-bottom: 25px;
  border-bottom: 2px solid #1e293b;
  padding-bottom: 12px;
  position: relative;
}

.header-nav {
  position: absolute;
  left: 0;
  top: 5px;
  z-index: 10;
}

.btn-back {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #38bdf8;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.88rem;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-block;
}

.btn-back:hover {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.35);
  transform: translateX(-2px);
}

.view-header h1 {
  font-size: 2.3rem;
  margin: 0;
  background: linear-gradient(135deg, #a855f7 0%, #38bdf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
}

.view-header p {
  color: #94a3b8;
  margin: 6px 0 0 0;
  font-size: 0.95rem;
}

/* layout grid */
.simulator-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 992px) {
  .simulator-layout {
    grid-template-columns: 1fr;
  }
}

.side-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-simulator {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Glass cards */
.card {
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  padding: 20px;
  border-radius: 16px;
}

.card h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1.15rem;
  color: #e2e8f0;
  font-weight: 600;
}

/* Stepper CSS */
.stepper-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.stepper-title {
  color: #38bdf8 !important;
  margin: 0 !important;
}

.step-badge {
  font-size: 0.75rem;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: bold;
  border: 1px solid rgba(56, 189, 248, 0.2);
}

.step-subtitle {
  margin: 0 0 8px 0;
  font-size: 1.05rem;
  color: #f1f5f9;
}

.step-description {
  font-size: 0.86rem;
  line-height: 1.5;
  color: #94a3b8;
  margin: 0 0 15px 0;
}

.step-interactive-area {
  background: rgba(30, 41, 59, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 15px;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* Stepper navigation buttons */
.stepper-nav-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.btn-nav {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.btn-nav.back {
  background: #1e293b;
  color: #94a3b8;
  border-color: #334155;
}

.btn-nav.back:hover:not(:disabled) {
  background: #334155;
  color: #f1f5f9;
}

.btn-nav.next {
  background: #38bdf8;
  color: #0f172a;
}

.btn-nav.next:hover:not(:disabled) {
  background: #7dd3fc;
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
}

.btn-nav:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Didactic Analogies */
.analogy-card {
  border-left: 4px solid #a855f7;
  background: rgba(168, 85, 247, 0.04);
}

.analogy-text {
  font-size: 0.82rem;
  line-height: 1.45;
  color: #cbd5e1;
  margin: 0;
}

/* State Preparation inputs */
.preset-buttons-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  margin-bottom: 15px;
}

.btn-preset {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 0.72rem;
  padding: 6px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-preset:hover {
  background: rgba(168, 85, 247, 0.15);
  border-color: rgba(168, 85, 247, 0.4);
  color: #d8b4fe;
}

.slider-group {
  margin-bottom: 12px;
}

.slider-info-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.76rem;
  color: #94a3b8;
  margin-bottom: 4px;
}

.slider {
  width: 100%;
  height: 6px;
  background: #1e293b;
  border-radius: 3px;
  outline: none;
  -webkit-appearance: none;
}

.slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #38bdf8;
  cursor: pointer;
  transition: background 0.15s;
}

.slider::-webkit-slider-thumb:hover {
  background: #7dd3fc;
}

.math-readout {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
  font-size: 0.8rem;
  border-top: 1px dashed rgba(255, 255, 255, 0.05);
  padding-top: 8px;
}

.text-purple {
  color: #c084fc;
}

/* Actions steps pane */
.step-action-pane {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.btn-step-action {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  font-weight: bold;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  text-align: center;
}

.cyan-btn { background: #06b6d4; color: #081d24; }
.cyan-btn:hover { background: #22d3ee; box-shadow: 0 0 15px rgba(6, 182, 212, 0.35); }

.purple-btn { background: #a855f7; color: #ffffff; }
.purple-btn:hover { background: #c084fc; box-shadow: 0 0 15px rgba(168, 85, 247, 0.35); }

.blue-btn { background: #38bdf8; color: #0f172a; }
.blue-btn:hover:not(:disabled) { background: #7dd3fc; box-shadow: 0 0 15px rgba(56, 189, 248, 0.35); }
.blue-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.reset-btn { background: #10b981; color: white; }
.reset-btn:hover { background: #34d399; box-shadow: 0 0 15px rgba(16, 185, 129, 0.35); }

/* Bell Step graphic */
.bell-graphics {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.72rem;
  margin-bottom: 5px;
}

.bell-wave {
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: bold;
}

.cyan-pulse {
  background: rgba(6, 182, 212, 0.15);
  color: #22d3ee;
  border: 1px solid rgba(6, 182, 212, 0.25);
  animation: pulse-cyan 1.5s infinite alternate;
}

.emerald-pulse {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
  animation: pulse-emerald 1.5s infinite alternate;
}

.bell-link {
  color: #94a3b8;
  font-style: italic;
}

@keyframes pulse-cyan {
  0% { box-shadow: 0 0 5px rgba(6, 182, 212, 0.2); }
  100% { box-shadow: 0 0 15px rgba(6, 182, 212, 0.5); }
}

@keyframes pulse-emerald {
  0% { box-shadow: 0 0 5px rgba(16, 185, 129, 0.2); }
  100% { box-shadow: 0 0 15px rgba(16, 185, 129, 0.5); }
}

/* Bell operation graphic */
.bell-operations-graphics {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-family: monospace;
  font-size: 0.85rem;
  color: #cbd5e1;
  background: rgba(15, 23, 42, 0.4);
  padding: 8px 15px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

/* Measurement results */
.measurement-results-card {
  text-align: center;
  width: 100%;
}

.bit-badge-wrapper {
  display: flex;
  justify-content: center;
  gap: 15px;
  margin-bottom: 8px;
}

.bit-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #0f172a;
  border: 2px solid #38bdf8;
  color: #38bdf8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-family: monospace;
  font-size: 1rem;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.2);
}

.medida-text {
  font-size: 0.78rem;
  color: #34d399;
  margin: 0;
}

/* Success Card */
.success-alert {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  text-align: left;
}

.success-icon {
  font-size: 1.2rem;
  line-height: 1;
}

.success-alert strong {
  color: #34d399;
  font-size: 0.85rem;
}

/* Bloch Spheres rendering */
.visualizer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 8px;
  margin-bottom: 12px;
}

.purity-badge {
  background: rgba(15, 23, 42, 0.7);
  padding: 3px 8px;
  border-radius: 6px;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  border: 1px solid rgba(56, 189, 248, 0.2);
}

.bloch-spheres-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

@media (max-width: 576px) {
  .bloch-spheres-grid {
    grid-template-columns: 1fr;
  }
}

.qubit-card {
  background: rgba(30, 41, 59, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: all 0.3s ease;
  opacity: 0.4;
}

.qubit-card.active-q {
  opacity: 1;
  background: rgba(30, 41, 59, 0.55);
}

.q0-border.active-q { border-color: rgba(168, 85, 247, 0.3); }
.q1-border.active-q { border-color: rgba(6, 182, 212, 0.3); }
.q2-border.active-q { border-color: rgba(16, 185, 129, 0.3); }

.qubit-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  padding-bottom: 5px;
  margin-bottom: 5px;
  font-size: 0.8rem;
  font-weight: bold;
  color: #cbd5e1;
}

.q-badge {
  font-size: 0.65rem;
  font-weight: 900;
  padding: 1px 5px;
  border-radius: 4px;
  color: white;
}

.q0-bg { background-color: #a855f7; }
.q1-bg { background-color: #06b6d4; }
.q2-bg { background-color: #10b981; }

.canvas-container {
  width: 100%;
  height: 150px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}

.qubit-data {
  width: 100%;
  font-size: 0.68rem;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
  border-top: 1px dashed rgba(255, 255, 255, 0.03);
  padding-top: 4px;
}

.coord-row {
  display: flex;
  justify-content: space-between;
}

/* Classical transmission channel fiber */
.classical-channel-container {
  position: absolute;
  top: 50%;
  left: 10%;
  right: 10%;
  height: 4px;
  transform: translateY(-50%);
  z-index: 10;
}

.classical-fiber-line {
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(90deg, #38bdf8 0px, #38bdf8 8px, transparent 8px, transparent 16px);
  animation: fiber-pulse 0.8s linear infinite;
  opacity: 0.5;
  border-radius: 2px;
}

.flying-packet {
  position: absolute;
  padding: 2px 6px;
  background: #080d1a;
  border: 1px solid #38bdf8;
  border-radius: 4px;
  color: #38bdf8;
  font-family: monospace;
  font-size: 0.72rem;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
}

.packet-0 {
  animation: fly-right 1.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.packet-1 {
  animation: fly-right 1.5s cubic-bezier(0.2, 0.8, 0.2, 1) 0.25s forwards;
}

@keyframes fly-right {
  0% { left: 0%; opacity: 0; transform: scale(0.6) translateY(-18px); }
  8% { opacity: 1; transform: scale(1) translateY(-18px); }
  90% { opacity: 1; transform: scale(1) translateY(-18px); }
  100% { left: 100%; opacity: 0; transform: scale(0.6) translateY(-18px); }
}

@keyframes fiber-pulse {
  0% { background-position: 0px 0; }
  100% { background-position: 16px 0; }
}

/* Quantum Circuit SVG style */
.circuit-svg-container {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 15px;
  overflow-x: auto;
}

.circuit-svg {
  width: 100%;
  min-width: 600px;
  height: auto;
  display: block;
}

.wire {
  stroke: #1e293b;
  stroke-width: 2.5;
  transition: stroke 0.3s;
}

.wire.highlighted {
  stroke: #475569;
}

.label-q {
  fill: #94a3b8;
  font-family: monospace;
  font-size: 13px;
  font-weight: bold;
}

.boundary-line {
  stroke: rgba(255, 255, 255, 0.08);
  stroke-dasharray: 4 4;
  stroke-width: 1.5;
}

.boundary-label {
  fill: #64748b;
  font-size: 11px;
  text-anchor: middle;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.gate-box {
  fill: #1e293b;
  stroke: #475569;
  stroke-width: 1.5;
  rx: 4;
  ry: 4;
  transition: all 0.3s;
}

.gate-text {
  fill: #cbd5e1;
  font-size: 12px;
  font-family: Arial, sans-serif;
  text-anchor: middle;
}

.gate-group {
  opacity: 0.25;
  transition: opacity 0.3s;
}

.gate-group.active {
  opacity: 1;
}

.gate-group.done {
  opacity: 0.85;
}

.gate-group.active .gate-box {
  stroke: #38bdf8;
  fill: rgba(56, 189, 248, 0.15);
  filter: drop-shadow(0 0 3px rgba(56, 189, 248, 0.3));
}

.gate-group.active .gate-text {
  fill: #38bdf8;
  font-weight: bold;
}

/* Specific Gates style */
.gate-box.prep {
  fill: rgba(168, 85, 247, 0.05);
  stroke: rgba(168, 85, 247, 0.3);
}

.gate-group.active .gate-box.prep {
  fill: rgba(168, 85, 247, 0.2);
  stroke: #a855f7;
  filter: drop-shadow(0 0 5px rgba(168, 85, 247, 0.4));
}

.gate-group.active .gate-box.prep + text {
  fill: #d8b4fe;
  font-weight: bold;
}

.cnot-control {
  fill: #cbd5e1;
  transition: fill 0.3s;
}

.gate-group.active .cnot-control {
  fill: #38bdf8;
}

.cnot-line {
  stroke: #475569;
  stroke-width: 1.5;
  transition: stroke 0.3s;
}

.gate-group.active .cnot-line {
  stroke: #38bdf8;
}

.cnot-target-bg {
  fill: #1e293b;
  stroke: #475569;
  stroke-width: 1.5;
  transition: all 0.3s;
}

.gate-group.active .cnot-target-bg {
  stroke: #38bdf8;
  fill: rgba(56, 189, 248, 0.1);
}

.cnot-target-line {
  stroke: #cbd5e1;
  stroke-width: 1.5;
  transition: stroke 0.3s;
}

.gate-group.active .cnot-target-line {
  stroke: #38bdf8;
}

.gate-box.measure {
  fill: rgba(15, 23, 42, 0.4);
  stroke: #475569;
}

.gate-group.active .gate-box.measure {
  stroke: #38bdf8;
  fill: rgba(56, 189, 248, 0.12);
}

.measure-icon {
  stroke: #cbd5e1;
  stroke-width: 1.5;
  fill: none;
  transition: stroke 0.3s;
}

.gate-group.active .measure-icon {
  stroke: #38bdf8;
}

.measured-bit-val {
  fill: #34d399;
  font-family: monospace;
  font-size: 13px;
  font-weight: bold;
}

/* Classical wires */
.classical-wire-vert, .classical-wire-horiz {
  stroke: #1e293b;
  stroke-width: 1.2;
  transition: stroke 0.3s;
}

.gate-group.active .classical-wire-vert,
.gate-group.active .classical-wire-horiz,
.gate-group.done .classical-wire-vert,
.gate-group.done .classical-wire-horiz {
  stroke: rgba(56, 189, 248, 0.4);
}

.gate-box.correction-gate {
  fill: #1e293b;
  stroke: #334155;
  opacity: 0.4;
}

.gate-box.correction-gate.triggered {
  stroke: #10b981;
  fill: rgba(16, 185, 129, 0.18);
  opacity: 1;
  filter: drop-shadow(0 0 5px rgba(16, 185, 129, 0.4));
}

.gate-group.active .gate-box.correction-gate {
  opacity: 0.9;
  stroke: #475569;
}

/* Comparison Card */
.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 8px;
}

.status-indicator {
  font-size: 0.72rem;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: bold;
}

.status-indicator.success {
  color: #34d399;
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.25);
  animation: glow-pulse-green 1.5s infinite alternate;
}

.comparison-grid {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 15px;
}

@media (max-width: 768px) {
  .comparison-grid {
    flex-direction: column;
  }
  .arrow-between {
    transform: rotate(90deg);
  }
}

.comp-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
}

.comp-lbl {
  font-size: 0.76rem;
  color: #94a3b8;
}

.state-math-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 12px;
  font-size: 0.85rem;
  text-align: center;
}

.purple-border {
  border-color: rgba(168, 85, 247, 0.35);
  background: rgba(168, 85, 247, 0.03);
}

.emerald-border {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.gray-border {
  border-color: rgba(255, 255, 255, 0.05);
}

.arrow-between {
  font-size: 1.5rem;
  color: #475569;
  user-select: none;
}

@keyframes glow-pulse-green {
  0% { box-shadow: 0 0 5px rgba(16, 185, 129, 0.2); }
  100% { box-shadow: 0 0 15px rgba(16, 185, 129, 0.5); }
}

.animate-glow {
  animation: glow-pulse-green 1.5s infinite alternate;
}
</style>
