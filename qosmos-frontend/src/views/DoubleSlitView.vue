<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

// --- 1. CONFIGURACIÓN Y PARÁMETROS DE LA SIMULACIÓN ---
const isDoubleSlit = ref<boolean>(true)
const wavelength = ref<number>(4.0) // longitud de onda (lambda)
const slitDistance = ref<number>(4.0) // distancia d entre rendijas

// Animación general de ondas
const isPlaying = ref<boolean>(true)
const animationSpeed = ref<number>(1.0)
const time = ref<number>(0)

// Configuración de visualización unificada
const showPhasors = ref<boolean>(true)
const phasorOpacity = ref<number>(0.4) // slider de opacidad para el fondo

// Cuadrícula espacial para los fasores
const gridCols = 23
const gridRows = 11

// Frecuencia angular de rotación temporal
const omega = 0.15

// Sinc helper function for single-slit diffraction envelope
function sinc(val: number): number {
  if (Math.abs(val) < 0.0001) return 1.0
  return Math.sin(val) / val
}

// --- 2. CÁLCULO DE LA FUNCIÓN DE ONDA ---
// Posiciones de las rendijas en el eje Y (el centro es 6.0)
const slit1Y = computed(() => 6.0 - slitDistance.value / 2)
const slit2Y = computed(() => 6.0 + slitDistance.value / 2)

// Valores físicos calculados para la ecuación y el visor de fórmulas
// Escalar la longitud de onda de UI (2.0 a 6.0) a escala física (0.24 a 0.72)
// Multiplicamos por (d / 6.0)^1.8 para que las franjas se junten cuando las rendijas se acercan.
const wlPhys = computed(() => {
  const baseWl = wavelength.value * 0.12
  // Si las rendijas se acercan (menor slitDistance), la longitud de onda se reduce drásticamente.
  // Esto hace que la distancia entre franjas (Δy = λD/d) disminuya, juntando el patrón espacialmente.
  const scalingFactor = Math.pow(slitDistance.value / 6.0, 1.8)
  return baseWl * scalingFactor
})

const dPhys = computed(() => slitDistance.value * 0.8)
const currentSlitWidth = computed(() => 0.8 * (wlPhys.value / (wavelength.value * 0.12)))
const kVal = computed(() => (2 * Math.PI) / wlPhys.value)

// Función para calcular la función de onda complex en un punto (x, y)
function getWaveFunction(x: number, y: number, t: number) {
  const k = kVal.value
  const wl = wlPhys.value
  const sw = currentSlitWidth.value

  // Posición física de la rendija 1 (escalada por 0.8)
  const s1Y_phys = (isDoubleSlit.value ? slit1Y.value : 6.0) * 0.8

  // Distancia a la rendija 1
  const r1 = Math.sqrt(x * x + (y - s1Y_phys) * (y - s1Y_phys))
  // Onda cilíndrica de la rendija 1
  const phase1 = k * r1 - omega * t * animationSpeed.value
  
  // Difracción por rendija simple 1 (Envoltura sinc)
  const sinTheta1 = r1 > 0 ? (y - s1Y_phys) / r1 : 0
  const diff1 = sinc((Math.PI * sw * sinTheta1) / wl)
  
  const amp1 = (1.0 / Math.sqrt(r1 + 0.8)) * diff1
  const psi1_real = amp1 * Math.cos(phase1)
  const psi1_imag = amp1 * Math.sin(phase1)

  if (!isDoubleSlit.value) {
    return { real: psi1_real, imag: psi1_imag }
  }

  // Posición física de la rendija 2 (escalada por 0.8)
  const s2Y_phys = slit2Y.value * 0.8
  const r2 = Math.sqrt(x * x + (y - s2Y_phys) * (y - s2Y_phys))
  const phase2 = k * r2 - omega * t * animationSpeed.value
  
  // Difracción por rendija simple 2
  const sinTheta2 = r2 > 0 ? (y - s2Y_phys) / r2 : 0
  const diff2 = sinc((Math.PI * sw * sinTheta2) / wl)
  
  const amp2 = (1.0 / Math.sqrt(r2 + 0.8)) * diff2
  const psi2_real = amp2 * Math.cos(phase2)
  const psi2_imag = amp2 * Math.sin(phase2)

  // Superposición cuántica
  return {
    real: psi1_real + psi2_real,
    imag: psi1_imag + psi2_imag
  }
}

// --- 3. SELECCIÓN DE FASOR (ZOOM DETALLADO) ---
const selectedCell = ref<{ col: number; row: number }>({ col: 8, row: 6 })
const hoveredCell = ref<{ col: number; row: number } | null>(null)

const activeCell = computed(() => hoveredCell.value || selectedCell.value)

const activePhasorData = computed(() => {
  const cell = activeCell.value
  // Mapeamos las coordenadas de la cuadrícula a escala física x, y
  const x = cell.col * 0.8
  const y = cell.row * 0.8
  const psi = getWaveFunction(x, y, time.value)
  const magnitude = Math.sqrt(psi.real * psi.real + psi.imag * psi.imag)
  let phase = Math.atan2(psi.imag, psi.real) * (180 / Math.PI)
  if (phase < 0) phase += 360

  return {
    col: cell.col,
    row: cell.row,
    real: psi.real,
    imag: psi.imag,
    magnitude: magnitude,
    phase: phase
  }
})

// --- 4. EXPLICACIONES NO TÉCNICAS (DINÁMICAS) ---
const intuitiveExplanation = computed(() => {
  if (!isDoubleSlit.value) {
    return "Rendija Única: La función de onda pasa por una abertura. No hay interferencia cuántica. Los electrones viajan siguiendo la difracción simple y se concentran mayoritariamente en el centro, sin cancelaciones de fase."
  }

  const d = slitDistance.value
  const wl = wavelength.value

  if (d <= 3 && wl >= 5) {
    return "Rendijas muy juntas y gran longitud de onda: Las ondas se mezclan formando franjas de interferencia muy anchas. Al acercar las rendijas (menor d), el patrón se expande y las franjas se separan entre sí."
  }
  if (d >= 5 && wl <= 3) {
    return "Rendijas lejanas y longitud de onda corta: Al alejar las rendijas (mayor d), las franjas de interferencia se contraen y se acercan entre sí, creando líneas de impacto muy delgadas y juntas."
  }
  if (wl <= 3.2) {
    return "Longitud de onda corta: Los fasores giran rápido en el espacio. El patrón de interferencia tiene franjas estrechas y concentradas."
  }
  
  return "Doble Rendija Estándar: Recuerda que la distancia entre franjas es inversamente proporcional a la separación de rendijas (Δy = λD/d). Por eso, al acercar las rendijas el patrón se separa (se expande), y al alejarlas el patrón se junta (se contrae)."
})

// --- 5. SIMULACIÓN DE ELECTRONES E INTERACCIÓN ---
interface Electron {
  id: number
  x: number // col unit
  y: number // row unit
  startY: number // row unit
  targetY: number // row unit
  progress: number // de 0 a 1
  speed: number
}

const electrons = ref<Electron[]>([])
const screenHits = ref<number[]>([]) // porcentaje Y de impactos
const binCounts = ref<number[]>(new Array(50).fill(0)) // conteo para histograma
const totalFiredCount = ref<number>(0)
const maxFiredCount = 1000

const isFiring = ref<boolean>(false)
const firingProgress = computed(() => Math.min((totalFiredCount.value / maxFiredCount) * 100, 100))

// Velocidad de disparo e intervalos
const initialInterval = 600 // ms
const currentInterval = ref<number>(initialInterval)
let firingTimeoutId: any = null

// Canvas
const particleCanvas = ref<HTMLCanvasElement | null>(null)
let canvasCtx: CanvasRenderingContext2D | null = null

// Matriz de destello para los fasores cuando pasa un electrón
const phasorGlows = ref<number[][]>(Array.from({ length: gridCols + 1 }, () => new Array(gridRows + 1).fill(0)))

// Genera un punto de impacto en la pantalla (eje Y) siguiendo la densidad de probabilidad |psi|^2
function sampleQuantumHit(): number {
  const screenX = gridCols * 0.8
  const samples = 150
  const probs: number[] = []
  let sum = 0

  for (let i = 0; i < samples; i++) {
    const yVal = (i / (samples - 1)) * gridRows * 0.8
    const psi = getWaveFunction(screenX, yVal, time.value)
    const intensity = psi.real * psi.real + psi.imag * psi.imag
    probs.push(intensity)
    sum += intensity
  }

  const r = Math.random() * sum
  let cumulative = 0
  for (let i = 0; i < samples; i++) {
    cumulative += probs[i] ?? 0
    if (r <= cumulative) {
      return (i / (samples - 1)) * 100
    }
  }
  return 50
}

let nextElectronId = 0
function fireSingleElectron() {
  if (totalFiredCount.value >= maxFiredCount || !isFiring.value) {
    if (totalFiredCount.value >= maxFiredCount) {
      isFiring.value = false
    }
    return
  }

  const targetPercentage = sampleQuantumHit()
  const targetY = (targetPercentage / 100) * gridRows
  const startY = isDoubleSlit.value ? (Math.random() > 0.5 ? slit1Y.value : slit2Y.value) : 6.0

  // --- ACELERACIÓN DINÁMICA COMPLETA ---
  const progressRatio = totalFiredCount.value / maxFiredCount
  
  // Aceleración de frecuencia: intervalo disminuye exponencialmente
  currentInterval.value = initialInterval * Math.pow(0.0025, progressRatio)
  if (currentInterval.value < 1.5) currentInterval.value = 1.5 // límite rápido

  // Aceleración física: la velocidad de vuelo de los electrones aumenta progresivamente
  const speedMultiplier = 1.0 + 3.5 * progressRatio
  const baseSpeed = 0.012 + Math.random() * 0.006
  const speed = baseSpeed * speedMultiplier

  electrons.value.push({
    id: nextElectronId++,
    x: 0,
    y: startY,
    startY: startY,
    targetY: targetY,
    progress: 0,
    speed: speed
  })

  totalFiredCount.value++
  firingTimeoutId = setTimeout(fireSingleElectron, currentInterval.value)
}

function startFiring() {
  if (totalFiredCount.value >= maxFiredCount) {
    totalFiredCount.value = 0
    screenHits.value = []
    binCounts.value = new Array(50).fill(0)
    electrons.value = []
    currentInterval.value = initialInterval
  }
  isFiring.value = true
  fireSingleElectron()
}

function pauseFiring() {
  isFiring.value = false
  if (firingTimeoutId) clearTimeout(firingTimeoutId)
}

function resetSimulation() {
  isFiring.value = false
  if (firingTimeoutId) clearTimeout(firingTimeoutId)
  electrons.value = []
  screenHits.value = []
  binCounts.value = new Array(50).fill(0)
  totalFiredCount.value = 0
  currentInterval.value = initialInterval
}

// Bucle de animación
let requestId: number
const updateAnimation = () => {
  if (isPlaying.value) {
    time.value += 0.08
  }

  // Decaer el brillo de los fasores
  for (let c = 0; c <= gridCols; c++) {
    const colArray = phasorGlows.value[c]
    if (colArray) {
      for (let r = 0; r <= gridRows; r++) {
        const val = colArray[r]
        if (val !== undefined) {
          colArray[r] = val * 0.86
        }
      }
    }
  }

  // Dibujar Canvas
  if (particleCanvas.value) {
    if (!canvasCtx) {
      canvasCtx = particleCanvas.value.getContext('2d')
    }
    const ctx = canvasCtx
    if (ctx) {
      const w = particleCanvas.value.width
      const h = particleCanvas.value.height
      ctx.clearRect(0, 0, w, h)

      // 1. Dibujar el fondo oscuro degradado
      const bgGrad = ctx.createLinearGradient(0, 0, w, 0)
      bgGrad.addColorStop(0, '#040712')
      bgGrad.addColorStop(0.8, '#060a18')
      bgGrad.addColorStop(1, '#090f24')
      ctx.fillStyle = bgGrad
      ctx.fillRect(0, 0, w, h)

      // 2. Dibujar rendijas físicas en la izquierda
      ctx.fillStyle = '#0f172a'
      ctx.fillRect(0, 0, 16, h)

      ctx.fillStyle = '#38bdf8'
      const s1Y = isDoubleSlit.value ? slit1Y.value : 6.0
      const r1Y_px = (s1Y / gridRows) * (h - 30) + 15
      ctx.clearRect(0, r1Y_px - 8, 16, 16)
      if (isDoubleSlit.value) {
        const r2Y_px = (slit2Y.value / gridRows) * (h - 30) + 15
        ctx.clearRect(0, r2Y_px - 8, 16, 16)
      }

      // 3. PANTALLA DETECTORA DE IMPACTOS (Eje derecho, X = 670)
      const screenX_px = 650
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(screenX_px, 0)
      ctx.lineTo(screenX_px, h)
      ctx.stroke()

      // 4. HISTOGRAMA RESIDUAL DE IMPACTOS (Canvas)
      const maxCount = Math.max(...binCounts.value, 1)
      const binH = h / 50
      for (let i = 0; i < 50; i++) {
        const count = binCounts.value[i] ?? 0
        if (count > 0) {
          const barW = (count / maxCount) * 85 // ancho máximo 85px
          const barY = i * binH
          
          const hitGrad = ctx.createLinearGradient(screenX_px, barY, screenX_px + barW, barY)
          hitGrad.addColorStop(0, 'rgba(52, 211, 153, 0.65)')
          hitGrad.addColorStop(0.7, 'rgba(56, 189, 248, 0.4)')
          hitGrad.addColorStop(1, 'rgba(56, 189, 248, 0)')

          ctx.fillStyle = hitGrad
          ctx.fillRect(screenX_px, barY + 0.5, barW, binH - 1)
        }
      }

      // 5. CURVA LÍMITE TEÓRICA DE LA FUNCIÓN DE ONDA |psi|^2
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.85)' // verde esmeralda brillante
      ctx.lineWidth = 2.5
      ctx.shadowColor = '#10b981'
      ctx.shadowBlur = 6
      ctx.beginPath()
      const samples = 150
      for (let i = 0; i < samples; i++) {
        const yVal = (i / (samples - 1)) * gridRows * 0.8
        const psi = getWaveFunction(gridCols * 0.8, yVal, time.value)
        const intensity = psi.real * psi.real + psi.imag * psi.imag
        // Normalización para pantalla (amplitud máxima aproximada de 0.22)
        const plotX = screenX_px + (intensity / 0.24) * 85
        const plotY = (i / (samples - 1)) * h
        if (i === 0) ctx.moveTo(plotX, plotY)
        else ctx.lineTo(plotX, plotY)
      }
      ctx.stroke()
      ctx.shadowBlur = 0 // reiniciar sombras

      // 6. ACTUALIZAR Y DIBUJAR LOS ELECTRONES CON MINI-FASOR
      electrons.value = electrons.value.filter(el => {
        el.progress += el.speed

        if (el.progress >= 1.0) {
          // Impacto final
          const hitPercent = (el.targetY / gridRows) * 100
          screenHits.value.push(hitPercent)
          const binIndex = Math.min(Math.floor((el.targetY / gridRows) * 50), 49)
          if (binIndex >= 0) {
            binCounts.value[binIndex] = (binCounts.value[binIndex] ?? 0) + 1
          }
          return false
        }

        // Posición en pantalla (píxeles)
        const posX_px = el.progress * screenX_px
        const currentY = el.startY + (el.targetY - el.startY) * el.progress
        const posY_px = (currentY / gridRows) * (h - 30) + 15

        // Activar el destello en el nodo de fasores más cercano
        const colCell = Math.round(el.progress * gridCols)
        const rowCell = Math.round(currentY)
        if (colCell >= 1 && colCell <= gridCols && rowCell >= 1 && rowCell <= gridRows) {
          if (phasorGlows.value[colCell]) {
            phasorGlows.value[colCell][rowCell] = 1.0 // activar destello
          }
        }

        // Calcular la fase local para el mini-fasor del electrón
        const physX = el.progress * gridCols * 0.8
        const physY = currentY * 0.8
        const psiLoc = getWaveFunction(physX, physY, time.value)
        const phaseAngle = Math.atan2(psiLoc.imag, psiLoc.real)

        // Dibujar el mini-fasor (círculo fino + aguja) alrededor de la partícula
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.45)' // rojo pálido
        ctx.lineWidth = 1
        ctx.beginPath()
        ctx.arc(posX_px, posY_px, 10, 0, Math.PI * 2)
        ctx.stroke()

        // Aguja indicadora
        ctx.beginPath()
        ctx.moveTo(posX_px, posY_px)
        ctx.lineTo(posX_px + Math.cos(phaseAngle) * 10, posY_px + Math.sin(phaseAngle) * 10)
        ctx.stroke()

        // Dibujar electrón brillante
        const elGrad = ctx.createRadialGradient(posX_px, posY_px, 0.5, posX_px, posY_px, 5)
        elGrad.addColorStop(0, '#ffffff')
        elGrad.addColorStop(0.3, '#10b981')
        elGrad.addColorStop(0.8, 'rgba(56, 189, 248, 0.35)')
        elGrad.addColorStop(1, 'rgba(56, 189, 248, 0)')

        ctx.fillStyle = elGrad
        ctx.beginPath()
        ctx.arc(posX_px, posY_px, 5, 0, Math.PI * 2)
        ctx.fill()

        return true
      })
    }
  }

  requestId = requestAnimationFrame(updateAnimation)
}

onMounted(() => {
  requestId = requestAnimationFrame(updateAnimation)
})

onUnmounted(() => {
  cancelAnimationFrame(requestId)
  if (firingTimeoutId) clearTimeout(firingTimeoutId)
})

watch([isDoubleSlit, wavelength, slitDistance], () => {
  resetSimulation()
})

// --- 7. CÁLCULO DE FASORES ---
function getPhasorRotation(col: number, row: number) {
  const x = col * 0.8
  const y = row * 0.8
  const psi = getWaveFunction(x, y, time.value)
  const angleRad = Math.atan2(psi.imag, psi.real)
  return angleRad * (180 / Math.PI)
}

function getPhasorLength(col: number, row: number) {
  const x = col * 0.8
  const y = row * 0.8
  const psi = getWaveFunction(x, y, time.value)
  const mag = Math.sqrt(psi.real * psi.real + psi.imag * psi.imag)
  
  // Mapeamos a longitud de flecha
  const maxLength = 11
  return Math.min(mag * 8, maxLength)
}

function getPhasorColor(col: number, row: number) {
  const x = col * 0.8
  const y = row * 0.8
  const psi = getWaveFunction(x, y, time.value)
  const mag = Math.sqrt(psi.real * psi.real + psi.imag * psi.imag)

  const opacity = Math.min(mag * 0.7, 1.0)
  return `rgba(56, 189, 248, ${opacity.toFixed(2)})`
}
</script>

<template>
  <div class="slit-view-container">
    <!-- Encabezado con Botón de Retorno -->
    <header class="view-header">
      <div class="header-nav">
        <router-link to="/" class="btn-back">← Volver al Menú</router-link>
      </div>
      <h1>Experimento de Doble Rendija</h1>
      <p>Superposición en Tiempo Real y Dualidad Onda-Partícula</p>
    </header>

    <div class="simulator-layout">
      <!-- PANEL IZQUIERDO: CONTROLES Y ZOOM FASOR -->
      <aside class="side-panel">
        
        <!-- CARD DE CONTROLES -->
        <div class="card control-card">
          <h3>Ajustes de Laboratorio</h3>
          
          <div class="control-group">
            <label>Aberturas Físicas</label>
            <div class="toggle-buttons">
              <button 
                @click="isDoubleSlit = false" 
                :class="{ active: !isDoubleSlit }"
                class="btn-toggle"
              >
                Rendija Única
              </button>
              <button 
                @click="isDoubleSlit = true" 
                :class="{ active: isDoubleSlit }"
                class="btn-toggle"
              >
                Doble Rendija
              </button>
            </div>
          </div>

          <!-- CONTROLES DE SUPERPOSICIÓN FASORES -->
          <div class="control-group">
            <div class="slider-header">
              <label>Superponer Fasores Cuánticos</label>
              <input type="checkbox" v-model="showPhasors" class="checkbox-toggle" />
            </div>
            <div class="slider-header" v-if="showPhasors">
              <span class="slider-info">Opacidad de Cuadrícula</span>
              <span class="value-readout">{{ Math.round(phasorOpacity * 100) }}%</span>
            </div>
            <input 
              v-if="showPhasors"
              v-model.number="phasorOpacity" 
              type="range" 
              min="0.1" 
              max="1.0" 
              step="0.05" 
              class="slider"
            />
          </div>

          <div class="control-group">
            <div class="slider-header">
              <label>Longitud de Onda ($\lambda$)</label>
              <span class="value-readout">{{ wavelength.toFixed(1) }} nm</span>
            </div>
            <input 
              v-model.number="wavelength" 
              type="range" 
              min="2.0" 
              max="6.0" 
              step="0.2" 
              class="slider"
            />
          </div>

          <div class="control-group" v-if="isDoubleSlit">
            <div class="slider-header">
              <label>Separación de Rendijas ($d$)</label>
              <span class="value-readout">{{ slitDistance.toFixed(1) }} nm</span>
            </div>
            <input 
              v-model.number="slitDistance" 
              type="range" 
              min="2.0" 
              max="6.0" 
              step="0.2" 
              class="slider"
            />
            <span class="slider-info">Relación inversa: Menor separación expande el patrón; mayor separación lo junta.</span>
          </div>

          <div class="control-group">
            <label>Tiempo de la Onda</label>
            <div class="speed-controls">
              <button @click="isPlaying = !isPlaying" class="btn-play">
                {{ isPlaying ? '⏸ Pausar' : '▶ Reproducir' }}
              </button>
              <input 
                v-model.number="animationSpeed" 
                type="range" 
                min="0" 
                max="2" 
                step="0.1" 
                class="slider speed-slider"
              />
            </div>
          </div>
        </div>

        <!-- EXPLICACIÓN NO TÉCNICA DINÁMICA -->
        <div class="card info-card">
          <h3>Guía de Observación</h3>
          <p class="explanation-text">{{ intuitiveExplanation }}</p>
        </div>

        <!-- CARD DE ECUACIONES EN TIEMPO REAL -->
        <div class="card math-card">
          <h3>Cálculos (Motor Cuántico)</h3>
          <div class="math-content">
            <div class="formula-block">
              <span class="formula-label">Función de Onda:</span>
              <div class="formula-tex">ψ(x,y,t) = ψ₁ + ψ₂</div>
            </div>
            <div class="formula-block">
              <span class="formula-label">Componente Cilíndrica:</span>
              <div class="formula-tex">ψⱼ = A/√(rⱼ) · e^(i(krⱼ - ωt)) · sinc(θⱼ)</div>
            </div>
            <div class="formula-params">
              <div class="param-row">
                <span class="param-name">Longitud Onda (λ):</span>
                <span class="param-value font-mono">{{ wlPhys.toFixed(3) }} nm</span>
              </div>
              <div class="param-row" v-if="isDoubleSlit">
                <span class="param-name">Separación (d):</span>
                <span class="param-value font-mono">{{ dPhys.toFixed(2) }} nm</span>
              </div>
              <div class="param-row">
                <span class="param-name">Ancho Rendija (a):</span>
                <span class="param-value font-mono">{{ currentSlitWidth.toFixed(3) }} nm</span>
              </div>
              <div class="param-row">
                <span class="param-name">Nº de Onda (k):</span>
                <span class="param-value font-mono">{{ kVal.toFixed(2) }} rad/nm</span>
              </div>
            </div>
          </div>
        </div>

        <!-- PANEL DE ZOOM FASORIAL (ESTILO IMAGEN RED CIRCLE) -->
        <div class="card zoom-card">
          <h3>Detalle del Estado Cuántico</h3>
          <p class="zoom-subtitle">Celda ({{ activePhasorData.col }}, {{ activePhasorData.row }})</p>
          
          <div class="zoom-circle-container">
            <div class="phasor-scope">
              <div class="axis horizontal"></div>
              <div class="axis vertical"></div>
              <span class="axis-label top">i</span>
              <span class="axis-label right">1</span>
              <span class="axis-label bottom">-i</span>
              <span class="axis-label left">-1</span>
              
              <div class="red-circle-outline">
                <div class="origin-dot"></div>
                <!-- Aguja de fase -->
                <div 
                  class="phasor-arrow" 
                  :style="{ 
                    transform: `rotate(${-activePhasorData.phase}deg) scaleX(${Math.min(activePhasorData.magnitude * 1.5, 1.0)})` 
                  }"
                >
                  <div class="arrow-head"></div>
                </div>
                <!-- Indicador de amplitud como esferas de arrastre -->
                <div 
                  class="phasor-dot" 
                  v-for="i in 4" 
                  :key="i"
                  :style="{
                    transform: `rotate(${-activePhasorData.phase}deg) translateX(${i * 22 * Math.min(activePhasorData.magnitude * 1.5, 1.0)}px)`
                  }"
                ></div>
              </div>
            </div>
          </div>

          <div class="digital-readout">
            <div class="readout-row">
              <span class="lbl">Fórmula:</span>
              <span class="val font-mono">
                {{ activePhasorData.real.toFixed(3) }} 
                {{ activePhasorData.imag >= 0 ? '+' : '' }} 
                {{ activePhasorData.imag.toFixed(3) }}i
              </span>
            </div>
            <div class="readout-row">
              <span class="lbl">Magnitud (Prob.):</span>
              <span class="val font-mono">{{ activePhasorData.magnitude.toFixed(3) }}</span>
            </div>
            <div class="readout-row">
              <span class="lbl">Fase cuántica:</span>
              <span class="val font-mono">{{ activePhasorData.phase.toFixed(1) }}°</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- PANEL PRINCIPAL: SIMULADOR FASORES Y ELECTRONES UNIFICADOS -->
      <main class="main-simulator">
        
        <div class="card viz-card">
          <div class="card-header-viz">
            <h3>Visualizador Cuántico Integrado</h3>
            <p>El chorro de electrones viaja en tiempo real. Activa <strong>Superponer Fasores</strong> para visualizar la función de onda de fondo y cómo los fasores brillan al paso de las partículas.</p>
          </div>

          <div class="simulation-status-bar">
            <div class="status-info">
              <span>Fuerza de ráfaga: <strong class="font-mono">{{ totalFiredCount }} / {{ maxFiredCount }} e-</strong></span>
              <span>Velocidad de disparo: 
                <strong class="font-mono text-emerald-400">
                  {{ currentInterval <= 1.5 ? 'Máxima (Acelerada)' : `${Math.round(1000 / currentInterval)} e-/s` }}
                </strong>
              </span>
            </div>
            
            <div class="progress-container-bar">
              <div class="progress-fill-bar" :style="{ width: firingProgress + '%' }"></div>
            </div>
          </div>

          <!-- ESPACIO DE TRABAJO SUPERPUESTO -->
          <div class="simulation-workspace">
            <!-- Lienzo Canvas de Electrones e Histograma residual -->
            <canvas ref="particleCanvas" width="750" height="370" class="canvas-stage"></canvas>

            <!-- Cuadrícula SVG de Fasores en segundo plano/superpuesta -->
            <svg 
              viewBox="0 0 750 370" 
              class="phasor-grid-svg" 
              :style="{ opacity: showPhasors ? phasorOpacity : 0 }"
            >
              <defs>
                <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse">
                  <path d="M 0 1 L 10 5 L 0 9 z" fill="#38bdf8" />
                </marker>
              </defs>

              <!-- Dibujar cuadrícula de círculos fasores -->
              <g v-for="col in gridCols" :key="'col-' + col">
                <g v-for="row in gridRows" :key="'row-' + row">
                  <g 
                    class="grid-cell-g"
                    :class="{ 
                      'selected': selectedCell.col === col && selectedCell.row === row,
                      'hovered': hoveredCell?.col === col && hoveredCell?.row === row
                    }"
                    @click="selectedCell = { col, row }"
                    @mouseenter="hoveredCell = { col, row }"
                    @mouseleave="hoveredCell = null"
                  >
                    <!-- Círculo de espacio complejo -->
                    <circle 
                      :cx="col * 27 + 20" 
                      :cy="row * 28 + 20" 
                      r="11" 
                      class="cell-circle"
                      :style="{
                        strokeWidth: 1 + (phasorGlows[col]?.[row] || 0) * 3,
                        stroke: (phasorGlows[col]?.[row] || 0) > 0.1 ? '#10b981' : undefined,
                        fill: (phasorGlows[col]?.[row] || 0) > 0.1 ? 'rgba(16, 185, 129, 0.25)' : undefined
                      }"
                    />

                    <!-- Flecha del Fasor (rotando según tiempo y espacio) -->
                    <line 
                      :x1="col * 27 + 20" 
                      :y1="row * 28 + 20" 
                      :x2="col * 27 + 20 + Math.cos(getPhasorRotation(col, row) * (Math.PI / 180)) * getPhasorLength(col, row)" 
                      :y2="row * 28 + 20 + Math.sin(getPhasorRotation(col, row) * (Math.PI / 180)) * getPhasorLength(col, row)" 
                      :stroke="(phasorGlows[col]?.[row] || 0) > 0.1 ? '#10b981' : getPhasorColor(col, row)"
                      stroke-width="2"
                      marker-end="url(#arrow)"
                    />
                  </g>
                </g>
              </g>
            </svg>
          </div>

          <div class="particle-controls-bar">
            <button v-if="!isFiring" @click="startFiring()" class="btn-fire start">
              🚀 Iniciar Disparo de Electrones
            </button>
            <button v-else @click="pauseFiring()" class="btn-fire pause">
              ⏸ Pausar Disparo
            </button>
            <button @click="resetSimulation()" class="btn-fire reset">
              🔄 Reiniciar Historial
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.slit-view-container {
  min-height: 100vh;
  padding: 20px;
  background-color: #080d1a;
  color: #f8fafc;
}

/* Header */
.view-header {
  text-align: center;
  margin-bottom: 25px;
  border-bottom: 2px solid #1e293b;
  padding-bottom: 15px;
  position: relative;
}

.header-nav {
  position: absolute;
  left: 0;
  top: 15px;
}

.btn-back {
  background: rgba(30, 41, 59, 0.6);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
  font-size: 0.9rem;
  transition: all 0.2s ease;
  backdrop-filter: blur(8px);
}

.btn-back:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: #38bdf8;
  transform: translateX(-3px);
}

.view-header h1 {
  font-size: 2.8rem;
  margin: 0;
  background: linear-gradient(to right, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 15px rgba(56, 189, 248, 0.2));
}

.view-header p {
  color: #94a3b8;
  margin: 5px 0 0 0;
  font-size: 1.05rem;
}

/* Layout */
.simulator-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
  max-width: 1400px;
  margin: 0 auto;
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

/* Cards */
.card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.card h3 {
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 1.25rem;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 8px;
}

/* Controls */
.control-group {
  margin-bottom: 18px;
}

.control-group label {
  display: block;
  font-size: 0.95rem;
  color: #94a3b8;
  margin-bottom: 8px;
  font-weight: 500;
}

.toggle-buttons {
  display: flex;
  gap: 10px;
}

.btn-toggle {
  flex: 1;
  background-color: #1e293b;
  color: #64748b;
  border: 1px solid #334155;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.btn-toggle.active {
  background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
  color: #ffffff;
  border-color: #3b82f6;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

.btn-toggle:hover:not(.active) {
  background-color: #334155;
  color: #cbd5e1;
}

.checkbox-toggle {
  width: 18px;
  height: 18px;
  accent-color: #38bdf8;
  cursor: pointer;
}

.slider-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.value-readout {
  font-family: monospace;
  color: #38bdf8;
  font-weight: bold;
}

.slider {
  width: 100%;
  height: 6px;
  background: #1e293b;
  border-radius: 3px;
  outline: none;
  accent-color: #38bdf8;
  margin-bottom: 5px;
}

.slider-info {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
}

.speed-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-play {
  background-color: #10b981;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: bold;
  white-space: nowrap;
}

.btn-play:hover {
  background-color: #059669;
}

/* Info Card */
.info-card {
  border-left: 4px solid #3b82f6;
  background: rgba(30, 58, 138, 0.1);
}

.explanation-text {
  font-size: 0.9rem;
  line-height: 1.5;
  color: #94a3b8;
  margin: 0;
}

/* Zoom Card */
.zoom-subtitle {
  color: #475569;
  font-size: 0.8rem;
  margin: -5px 0 15px 0;
}

.zoom-circle-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 20px 0;
}

/* Phasor Scope */
.phasor-scope {
  width: 170px;
  height: 170px;
  border-radius: 50%;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.axis {
  position: absolute;
  background-color: rgba(220, 38, 38, 0.15);
}

.axis.horizontal {
  width: 100%;
  height: 1px;
  top: 50%;
  left: 0;
}

.axis.vertical {
  width: 1px;
  height: 100%;
  left: 50%;
  top: 0;
}

.axis-label {
  position: absolute;
  color: rgba(220, 38, 38, 0.6);
  font-family: monospace;
  font-size: 0.8rem;
  font-weight: bold;
}

.axis-label.top { top: 5px; left: calc(50% + 5px); }
.axis-label.right { right: 8px; top: calc(50% - 16px); }
.axis-label.bottom { bottom: 5px; left: calc(50% + 5px); }
.axis-label.left { left: 8px; top: calc(50% - 16px); }

/* Círculo Rojo */
.red-circle-outline {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  border: 2px solid #dc2626;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(220, 38, 38, 0.03);
  box-shadow: 0 0 15px rgba(220, 38, 38, 0.15);
}

.origin-dot {
  width: 8px;
  height: 8px;
  background-color: #dc2626;
  border-radius: 50%;
  position: absolute;
  z-index: 5;
}

.phasor-arrow {
  position: absolute;
  width: 60px;
  height: 2px;
  background-color: #dc2626;
  transform-origin: left center;
  left: 50%;
  z-index: 3;
}

.arrow-head {
  position: absolute;
  right: -2px;
  top: -6px;
  width: 0;
  height: 0;
  border-top: 7px solid transparent;
  border-bottom: 7px solid transparent;
  border-left: 10px solid #dc2626;
}

.phasor-dot {
  width: 5px;
  height: 5px;
  background-color: #dc2626;
  border-radius: 50%;
  position: absolute;
  left: calc(50% - 2px);
  transform-origin: left center;
  pointer-events: none;
  z-index: 2;
}

.digital-readout {
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 12px;
  font-size: 0.85rem;
}

.readout-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.readout-row .lbl {
  color: #64748b;
}

.readout-row .val {
  color: #e2e8f0;
}

/* Viz Cards */
.viz-card {
  display: flex;
  flex-direction: column;
}

.card-header-viz h3 {
  border: none;
  margin-bottom: 2px;
  padding-bottom: 0;
}

.card-header-viz p {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0 0 15px 0;
}

/* ESPACIO DE TRABAJO SUPERPUESTO */
.simulation-workspace {
  position: relative;
  width: 750px;
  height: 370px;
  background-color: #040810;
  border: 1px solid #1e293b;
  border-radius: 12px;
  overflow: hidden;
  margin: 0 auto;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}

.canvas-stage {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.phasor-grid-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  pointer-events: none; /* Dejar que pasen los eventos del mouse excepto celdas */
  background: transparent;
  transition: opacity 0.2s ease;
}

.grid-cell-g {
  cursor: pointer;
  pointer-events: auto; /* Las celdas individuales sí capturan clics */
}

.cell-circle {
  fill: rgba(30, 41, 59, 0.15);
  stroke: rgba(255, 255, 255, 0.04);
  stroke-width: 1;
  transition: stroke 0.2s, stroke-width 0.1s, fill 0.1s;
}

.grid-cell-g:hover .cell-circle {
  stroke: rgba(56, 189, 248, 0.4);
  fill: rgba(56, 189, 248, 0.05);
}

.grid-cell-g.selected .cell-circle {
  stroke: #ef4444 !important;
  stroke-width: 1.8 !important;
  fill: rgba(239, 68, 68, 0.1) !important;
}

.grid-cell-g.hovered .cell-circle {
  stroke: #38bdf8;
  stroke-width: 1.2;
}

/* Status Bar */
.simulation-status-bar {
  background-color: #0b132b;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: 8px;
  padding: 10px 15px;
  margin-bottom: 15px;
}

.status-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: #94a3b8;
  margin-bottom: 8px;
}

.progress-container-bar {
  width: 100%;
  height: 6px;
  background-color: #1e293b;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill-bar {
  height: 100%;
  background: linear-gradient(to right, #10b981, #38bdf8);
  transition: width 0.1s linear;
}

.particle-controls-bar {
  display: flex;
  gap: 15px;
  margin-top: 15px;
}

.btn-fire {
  flex: 1;
  border: none;
  padding: 12px;
  font-size: 0.95rem;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-fire.start {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
}

.btn-fire.start:hover {
  transform: translateY(-1px);
  box-shadow: 0 0 18px rgba(16, 185, 129, 0.5);
}

.btn-fire.pause {
  background-color: #d97706;
  color: white;
}

.btn-fire.pause:hover {
  background-color: #b45309;
}

.btn-fire.reset {
  background-color: #1e293b;
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
  max-width: 200px;
}

.btn-fire.reset:hover {
  background-color: #334155;
  border-color: #38bdf8;
}

.text-emerald-400 {
  color: #34d399;
}

@media (max-width: 992px) {
  .simulator-layout {
    grid-template-columns: 1fr;
  }
}

/* Math Card styles */
.math-card {
  border-left: 4px solid #10b981;
  background: rgba(16, 185, 129, 0.05);
}

.math-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.formula-block {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.formula-label {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: bold;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.formula-tex {
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  background-color: #030712;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.03);
  color: #34d399;
  font-size: 0.85rem;
  overflow-x: auto;
  white-space: nowrap;
}

.formula-params {
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 10px;
}

.param-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
}

.param-name {
  color: #94a3b8;
}

.param-value {
  color: #38bdf8;
  font-weight: bold;
}
</style>
