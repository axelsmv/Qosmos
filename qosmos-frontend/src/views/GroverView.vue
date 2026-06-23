<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

// --- 1. VARIABLES REACTIVAS ---
const currentStep = ref<number>(0)
const targetIndex = ref<number>(5) // Índice del elemento buscado (0 a 7, default: 101)
const measuredState = ref<number | null>(null) // Qubit medido
const amplitudes = ref<number[]>([1, 0, 0, 0, 0, 0, 0, 0])

// Nombres de los estados binarios para la base
const stateLabels = ['000', '001', '010', '011', '100', '101', '110', '111']

// --- 2. CÁLCULOS DEL MOTOR DE GROVER ---
function runGroverStep(step: number) {
  let amps = Array(8).fill(0)
  
  if (step === 0) {
    // Estado base |000>
    amps[0] = 1.0
    amplitudes.value = amps
    return
  }

  // Paso 1: Superposición uniforme (Hadamard en todos)
  const initAmp = 1 / Math.sqrt(8) // ~0.3536
  amps = Array(8).fill(initAmp)

  if (step === 1) {
    amplitudes.value = amps
    return
  }

  // Paso 2: Iteración 1 - Oráculo (Inversión de fase del ganador)
  amps[targetIndex.value] = -initAmp

  if (step === 2) {
    amplitudes.value = amps
    return
  }

  // Paso 3: Iteración 1 - Difusor (Inversión sobre la media)
  let sum1 = amps.reduce((acc, v) => acc + v, 0)
  let mean1 = sum1 / 8
  amps = amps.map(v => 2 * mean1 - v)

  if (step === 3) {
    amplitudes.value = amps
    return
  }

  // Paso 4: Iteración 2 - Oráculo
  amps[targetIndex.value] = -amps[targetIndex.value]

  if (step === 4) {
    amplitudes.value = amps
    return
  }

  // Paso 5: Iteración 2 - Difusor (Óptimo)
  let sum2 = amps.reduce((acc, v) => acc + v, 0)
  let mean2 = sum2 / 8
  amps = amps.map(v => 2 * mean2 - v)

  if (step === 5) {
    amplitudes.value = amps
    return
  }

  // Paso 6: Medición Óptima (Colapso basado en Iteración 2)
  if (step === 6) {
    if (measuredState.value === null) {
      measuredState.value = sampleMeasurement(amps)
    }
    amps = Array(8).fill(0)
    amps[measuredState.value] = 1.0
    amplitudes.value = amps
    return
  }

  // Paso 7: Iteración 3 - Oráculo (Sobre-rotación)
  // Re-calculamos el difusor 2 para tener las amplitudes previas
  let prevAmps = Array(8).fill(initAmp)
  prevAmps[targetIndex.value] = -initAmp
  let m1 = prevAmps.reduce((acc, v) => acc + v, 0) / 8
  prevAmps = prevAmps.map(v => 2 * m1 - v) // amplitudes paso 3

  prevAmps[targetIndex.value] = -prevAmps[targetIndex.value] // oráculo 2 (paso 4)
  let m2 = prevAmps.reduce((acc, v) => acc + v, 0) / 8
  prevAmps = prevAmps.map(v => 2 * m2 - v) // difusor 2 (paso 5)

  // Aplicar oráculo 3
  prevAmps[targetIndex.value] = -prevAmps[targetIndex.value]
  amps = prevAmps

  if (step === 7) {
    amplitudes.value = amps
    return
  }

  // Paso 8: Iteración 3 - Difusor
  let sum3 = amps.reduce((acc, v) => acc + v, 0)
  let mean3 = sum3 / 8
  amps = amps.map(v => 2 * mean3 - v)

  if (step === 8) {
    amplitudes.value = amps
    return
  }

  // Paso 9: Medición de sobre-rotación (Colapso basado en Iteración 3)
  if (step === 9) {
    if (measuredState.value === null) {
      measuredState.value = sampleMeasurement(amps)
    }
    amps = Array(8).fill(0)
    amps[measuredState.value] = 1.0
    amplitudes.value = amps
    return
  }
}

// Muestra colapso cuántico
function sampleMeasurement(amps: number[]): number {
  const r = Math.random()
  const probs = amps.map(a => a * a)
  const sum = probs.reduce((acc, p) => acc + p, 0)
  const normProbs = probs.map(p => p / (sum || 1))
  
  let acc = 0
  for (let i = 0; i < 8; i++) {
    const p = normProbs[i]
    if (p !== undefined) {
      acc += p
      if (r <= acc) {
        return i
      }
    }
  }
  return 0
}

// Media de amplitudes para dibujar la línea en el gráfico
const meanAmplitude = computed(() => {
  if (currentStep.value === 0 || currentStep.value === 6 || currentStep.value === 9) return 0
  return amplitudes.value.reduce((acc, v) => acc + v, 0) / 8
})

// Probabilidad actual del ganador
const successProbability = computed(() => {
  if (currentStep.value === 0) return 0
  if (currentStep.value === 6 || currentStep.value === 9) {
    return measuredState.value === targetIndex.value ? 100 : 0
  }
  const winnerAmp = amplitudes.value[targetIndex.value]
  if (winnerAmp === undefined) return 0
  return Math.round(winnerAmp * winnerAmp * 1000) / 10
})

// Porcentaje de probabilidad seguro para la UI
const getProbabilityPercentage = (idx: number): number => {
  const amp = amplitudes.value[idx]
  if (amp === undefined) return 0
  return Math.round(amp * amp * 100)
}

// --- 3. SELECCIÓN DE COFRE (Paso 0) ---
const selectTarget = (index: number) => {
  if (currentStep.value === 0) {
    targetIndex.value = index
    measuredState.value = null
  }
}

// --- 4. CONTROL DE PASOS ---
const nextStep = () => {
  if (currentStep.value < 9) {
    // Al pasar a medición, reseteamos la medida anterior si la hubiera
    if (currentStep.value === 5 || currentStep.value === 8) {
      measuredState.value = null
    }
    currentStep.value++
    runGroverStep(currentStep.value)
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
    if (currentStep.value !== 6 && currentStep.value !== 9) {
      measuredState.value = null
    }
    runGroverStep(currentStep.value)
  }
}

const resetSimulation = () => {
  currentStep.value = 0
  measuredState.value = null
  runGroverStep(0)
}

onMounted(() => {
  runGroverStep(0)
})

// --- 5. TEXTOS DIDÁCTICOS (FERIA CIENTÍFICA) ---
const stepTitles = [
  'Paso 0: Preparar la Base de Datos',
  'Paso 1: Superposición de Caminos (Hadamards)',
  'Paso 2: Inversión de Fase (Oráculo 1)',
  'Paso 3: Inversión sobre la Media (Difusor 1)',
  'Paso 4: Inversión de Fase (Oráculo 2)',
  'Paso 5: Inversión sobre la Media (Difusor 2 - Óptimo)',
  'Paso 6: Medición en Estado Óptimo',
  'Paso 7: Inversión de Fase (Oráculo 3 - Sobre-rotación)',
  'Paso 8: Inversión sobre la Media (Difusor 3)',
  'Paso 9: Medición en Estado Sobre-rotado'
]

const stepDescriptions = [
  'Elige en qué cofre esconder la estrella (haz click en los cofres de la derecha). En el simulador, representamos la base de datos desordenada con 8 estados binarios de 3 qubits, de |000⟩ a |111⟩.',
  'Aplicamos compuertas Hadamard a todos los qubits. Esto genera una superposición uniforme: todos los cofres tienen la misma amplitud (+0.354) y una probabilidad del 12.5% de ser elegidos. ¡Todos son posibles a la vez!',
  'El Oráculo cuántico "marca" el cofre ganador. Invierte la fase (amplitud) del cofre objetivo, volviéndola negativa (-0.354). Observa cómo en el gráfico de barras la columna del ganador ahora apunta hacia abajo.',
  'Aplicamos el Difusor. Este refleja todas las amplitudes respecto a la línea de la media (promedio). Como la amplitud del ganador estaba abajo, la reflexión la "infla" hacia arriba (+0.884) y encoge las otras (+0.177). ¡La probabilidad sube al 78%!',
  'Volvemos a aplicar el Oráculo para marcar de nuevo el ganador. Su amplitud se invierte a valores negativos (-0.884) en preparación para la segunda amplificación.',
  'El Difusor actúa por segunda vez. La reflexión sobre la media eleva la amplitud del ganador a un asombroso +0.972 (94.5% de probabilidad) y reduce los demás a un valor negativo mínimo. ¡Hemos alcanzado el máximo óptimo!',
  'Colapsamos el estado midiendo el sistema. Con una probabilidad del 94.5%, el algoritmo cuántico abrirá el cofre correcto. Haz click en Siguiente para ver si ganaste.',
  '¿Qué pasa si no nos detenemos? Al aplicar el Oráculo por tercera vez, la amplitud del ganador se invierte nuevamente a valores negativos (-0.972).',
  'El Difusor vuelve a reflejar respecto a la media. Debido al exceso de rotación, la amplitud del ganador se desborda y cae a +0.574, bajando la probabilidad al 33% e inflando las otras. ¡El pajar ha crecido y la aguja se ha encogido!',
  'Medimos el sistema en sobre-rotación. Debido a que la probabilidad de éxito cayó al 33%, hay una gran posibilidad de que el algoritmo falle y abra un cofre vacío. ¡La precisión cuántica requiere saber cuándo detenerse!'
]

const stepAnalogies = [
  '💡 Analogía: Imagina que tienes 8 cofres idénticos en un programa de televisión y solo uno tiene el premio. Un buscador clásico tendría que abrirlos de uno en uno en el peor de los casos.',
  '💡 Analogía: Ponemos todos los cofres en un estado vibracional idéntico. Es como tener 8 monedas girando en el aire al mismo tiempo. Aún no se ha decidido nada.',
  '💡 Analogía: Pintamos una marca invisible detrás del cofre ganador. En el mundo cuántico, esto equivale a cambiar la dirección de la vibración (fase) de ese cofre en particular sin abrirlo.',
  '💡 Analogía: Usamos interferencia cuántica. Si sumamos todas las vibraciones y reflejamos el patrón, el cofre marcado se amplifica notablemente mientras los otros se cancelan. ¡La aguja empieza a destacar!',
  '💡 Analogía: Volvemos a cambiar la fase de la vibración del cofre correcto. Estamos concentrando más "energía cuántica" sobre él antes del golpe final.',
  '💡 Analogía: ¡El contraste es máximo! El cofre correcto vibra con tanta fuerza que casi silencia a los demás. Su probabilidad de ser elegido es de casi el 95%.',
  '💡 Analogía: ¡Abrimos la caja! La medición detiene las ondas cuánticas y colapsa la realidad. Casi el 100% de las veces, el premio estará en el cofre que vibra con más fuerza.',
  '💡 Analogía: Si dejas girar la lavadora de más, la ropa empieza a desordenarse de nuevo. La interferencia cuántica empieza a actuar de forma destructiva para el ganador.',
  '💡 Analogía: ¡Sobre-rotación! La probabilidad del ganador ha bajado al 33%, y los otros cofres recuperaron fuerza. Volvemos a tener un estado muy desordenado.',
  '💡 Analogía: Medir aquí es como jugar a la ruleta. Al no detenernos a tiempo, la interferencia destructiva diluyó el premio y el sistema tiene altas probabilidades de fallar y darnos un cofre vacío.'
]
</script>

<template>
  <main class="grover-view-container">
    <!-- Encabezado con Botón de Retorno -->
    <header class="view-header">
      <div class="header-nav">
        <router-link to="/" class="btn-back">← Volver al Menú</router-link>
      </div>
      <h1>Búsqueda de Grover</h1>
      <p>Simulador Cuántico Didáctico de Amplificación de Amplitud paso a paso</p>
    </header>

    <div class="simulator-layout">
      <!-- PANEL IZQUIERDO: CONTROLES DEL STEPPER Y MODO FERIA -->
      <aside class="side-panel">
        <div class="card stepper-card">
          <div class="stepper-header-row">
            <h3 class="stepper-title">Control del Algoritmo</h3>
            <span class="step-badge">Paso {{ currentStep }} de {{ currentStep <= 6 ? '6' : '9' }}</span>
          </div>

          <h4 class="step-subtitle">{{ stepTitles[currentStep] }}</h4>
          <p class="step-description">{{ stepDescriptions[currentStep] }}</p>

          <!-- Componente Interactivo por Paso -->
          <div class="step-interactive-area">
            <!-- Paso 0: Selección de objetivo -->
            <div v-if="currentStep === 0" class="step-action-pane">
              <span class="instruction-badge">Haz click en los cofres de la derecha</span>
              <div class="target-readout font-mono">
                Elemento objetivo: <strong class="text-emerald">|{{ stateLabels[targetIndex] }}⟩</strong>
              </div>
              <button @click="nextStep" class="btn-step-action cyan-btn">
                Inicializar Superposición
              </button>
            </div>

            <!-- Paso de Medición Óptima o Sobre-rotada -->
            <div v-else-if="currentStep === 6 || currentStep === 9" class="step-action-pane">
              <div v-if="measuredState !== null" class="measurement-results">
                <div class="outcome-badge" :class="measuredState === targetIndex ? 'success' : 'fail'">
                  {{ measuredState === targetIndex ? '🏆 ¡ÉXITO!' : '❌ FALLO' }}
                </div>
                <p class="outcome-text font-mono">
                  Cofre abierto: |{{ stateLabels[measuredState] }}⟩ <br>
                  {{ measuredState === targetIndex ? '¡Encontraste la estrella en el cofre!' : 'El cofre estaba vacío.' }}
                </p>
              </div>
              
              <div class="action-buttons-row">
                <button v-if="currentStep === 6" @click="nextStep" class="btn-step-action purple-btn" style="flex: 1;">
                  Ver Sobre-rotación (Iteración 3)
                </button>
                <button @click="resetSimulation" class="btn-step-action reset-btn" style="flex: 1;">
                  Reiniciar
                </button>
              </div>
            </div>

            <!-- Pasos generales de la simulación -->
            <div v-else class="step-action-pane">
              <div class="metrics-row font-mono">
                <div class="metric-box">
                  <span class="metric-label">Prob. Éxito</span>
                  <span class="metric-value text-cyan">{{ successProbability }}%</span>
                </div>
                <div class="metric-box">
                  <span class="metric-label">Amplitud Media</span>
                  <span class="metric-value">{{ meanAmplitude.toFixed(3) }}</span>
                </div>
              </div>
              
              <button @click="nextStep" class="btn-step-action" :class="currentStep % 2 === 1 ? 'purple-btn' : 'cyan-btn'">
                {{ currentStep % 2 === 1 ? 'Aplicar Oráculo' : 'Aplicar Difusor' }}
              </button>
            </div>
          </div>

          <!-- Botones de Navegación del Stepper -->
          <div class="stepper-nav-row">
            <button 
              @click="prevStep" 
              :disabled="currentStep === 0" 
              class="btn-nav back"
            >
              ← Atrás
            </button>
            <button 
              @click="nextStep" 
              :disabled="currentStep === 9" 
              class="btn-nav next"
            >
              Siguiente →
            </button>
          </div>
        </div>

        <!-- CARD EXPLICATIVA DIDÁCTICA -->
        <div class="card analogy-card">
          <h3 style="color: #a855f7; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
            🎓 Explicación Didáctica
          </h3>
          <p class="analogy-text">{{ stepAnalogies[currentStep] }}</p>
        </div>

        <!-- CARD DE ECUACIONES Y MATEMÁTICA DE GROVER -->
        <div class="card math-explanation-card" style="border-left: 4px solid #38bdf8; background: rgba(56, 189, 248, 0.04); margin-top: 15px;">
          <h3><span style="color: #38bdf8;">📊</span> Ecuaciones de Grover</h3>
          <div class="math-content" style="font-size: 0.78rem; line-height: 1.45; color: #cbd5e1; display: grid; gap: 6px;">
            <p style="margin: 4px 0 0 0;"><strong>1. Superposición Uniforme:</strong></p>
            <div class="math-render">
              |<i>s</i>⟩ = <i>H</i><sup>⊗3</sup>|000⟩ = 
              <span class="math-frac" style="font-size: 0.85rem;">
                <span class="math-num">1</span>
                <span class="math-den">√8</span>
              </span>
              Σ |<i>x</i>⟩
            </div>
            <p style="margin: 4px 0 0 0;"><strong>2. Operador Oráculo (Fase):</strong></p>
            <div class="math-render">
              <i>U</i><sub><i>w</i></sub>|<i>x</i>⟩ = (-1)<sup><i>f</i>(<i>x</i>)</sup>|<i>x</i>⟩
            </div>
            <p style="margin: 4px 0 0 0;"><strong>3. Operador Difusor (Reflexión):</strong></p>
            <div class="math-render">
              <i>U</i><sub><i>s</i></sub> = 2|<i>s</i>⟩⟨<i>s</i>| - <i>I</i>
            </div>
            <p style="margin: 4px 0 0 0;"><strong>Inversión sobre la media:</strong></p>
            <div class="math-render">
              <i>α</i><sub><i>x</i></sub>' = 2<i>μ</i> - <i>α</i><sub><i>x</i></sub>
            </div>
            <p style="margin: 4px 0; font-size: 0.72rem; color: #94a3b8;">Donde <i>μ</i> es la amplitud promedio de todos los estados. El oráculo invierte la fase del ganador, y al reflejar sobre la media <i>μ</i>, el ganador se amplifica y los demás disminuyen.</p>
          </div>
        </div>
      </aside>

      <!-- PANEL PRINCIPAL: GRILLA DE COFRES Y GRÁFICO DE AMPLITUDES -->
      <main class="main-simulator">
        <!-- GRILLA DE COFRES (BASE DE DATOS) -->
        <div class="card database-card">
          <div class="database-header">
            <h3>Visualizador de Base de Datos (Base Computacional)</h3>
            <span class="db-info-badge">Selecciona haciendo click (Paso 0)</span>
          </div>

          <div class="chests-grid">
            <div 
              v-for="(label, idx) in stateLabels" 
              :key="label" 
              class="chest-wrapper"
              :class="{ 
                'target-chest': targetIndex === idx && currentStep === 0,
                'measured-chest': measuredState === idx && (currentStep === 6 || currentStep === 9),
                'active-click': currentStep === 0
              }"
              @click="selectTarget(idx)"
            >
              <!-- Icono de cofre cuántico -->
              <div class="chest-box-icon">
                <!-- Cofre cerrado -->
                <span v-if="measuredState !== idx || (currentStep !== 6 && currentStep !== 9)">📦</span>
                <!-- Cofre abierto con premio (Éxito) -->
                <span v-else-if="measuredState === targetIndex">⭐</span>
                <!-- Cofre abierto vacío (Fallo) -->
                <span v-else>🕳️</span>
              </div>
              <div class="chest-label font-mono">|{{ label }}⟩</div>
              <div class="chest-probability font-mono" v-if="currentStep !== 0 && currentStep !== 6 && currentStep !== 9">
                {{ getProbabilityPercentage(idx) }}%
              </div>
              <div class="winner-mark" v-if="targetIndex === idx && currentStep === 0">Ganador</div>
              <div class="winner-mark measured" v-if="measuredState === idx && (currentStep === 6 || currentStep === 9)">
                {{ measuredState === targetIndex ? '¡Encontrado!' : 'Vacío' }}
              </div>
            </div>
          </div>
        </div>

        <!-- GRÁFICO DE AMPLITUDES (SVG) -->
        <div class="card chart-card">
          <div class="chart-header-row">
            <h3>Gráfico de Amplitudes de Probabilidad</h3>
            <div class="legend-row">
              <span class="legend-item"><span class="legend-color cyan-bg"></span>Amplitud</span>
              <span class="legend-item"><span class="legend-color purple-bg"></span>Ganador</span>
              <span class="legend-item"><span class="legend-color dashed-line"></span>Promedio (Media)</span>
            </div>
          </div>

          <div class="svg-chart-container">
            <svg viewBox="0 0 560 230" class="amplitude-svg">
              <!-- Eje horizontal central (Línea de Amplitud 0.0) -->
              <line x1="10" y1="115" x2="550" y2="115" class="axis-line" />
              <text x="525" y="110" class="axis-lbl">0.0</text>
              <text x="525" y="40" class="axis-lbl">+1.0</text>
              <text x="525" y="195" class="axis-lbl">-1.0</text>

              <!-- Guías horizontales de rejilla (+1.0 y -1.0) -->
              <line x1="15" y1="35" x2="510" y2="35" class="grid-line" />
              <line x1="15" y1="195" x2="510" y2="195" class="grid-line" />

              <!-- Línea horizontal de Amplitud Promedio (Media) -->
              <line 
                x1="15" 
                :y1="115 - meanAmplitude * 80" 
                x2="510" 
                :y2="115 - meanAmplitude * 80" 
                class="mean-avg-line"
                v-if="currentStep !== 0 && currentStep !== 6 && currentStep !== 9"
              />
              <text 
                x="5" 
                :y="110 - meanAmplitude * 80" 
                class="mean-avg-text"
                v-if="currentStep !== 0 && currentStep !== 6 && currentStep !== 9"
              >
                Media: {{ meanAmplitude.toFixed(2) }}
              </text>

              <!-- Dibujar Barras de Amplitudes -->
              <g v-for="(amp, i) in amplitudes" :key="i">
                <!-- Barra -->
                <rect 
                  :x="30 + i * 60" 
                  :y="amp >= 0 ? 115 - amp * 80 : 115" 
                  width="36" 
                  :height="Math.abs(amp) * 80 || 2" 
                  class="amp-bar"
                  :class="{ 'winner-bar': targetIndex === i, 'negative-bar': amp < 0 }"
                />

                <!-- Texto de valor de amplitud arriba/abajo de la barra -->
                <text 
                  :x="48 + i * 60" 
                  :y="amp >= 0 ? 105 - amp * 80 : 130 - amp * 80" 
                  class="amp-val font-mono"
                >
                  {{ amp >= 0 ? '+' : '' }}{{ amp.toFixed(3) }}
                </text>

                <!-- Etiqueta del estado en el eje inferior -->
                <text 
                  :x="48 + i * 60" 
                  y="222" 
                  class="state-lbl font-mono"
                  :class="{ 'winner-text': targetIndex === i }"
                >
                  |{{ stateLabels[i] }}⟩
                </text>
              </g>
            </svg>
          </div>
        </div>
      </main>
    </div>
  </main>
</template>

<style scoped>
.grover-view-container {
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
  border: 1px solid rgba(56, 189, 248, 0.3);
  color: #38bdf8;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.88rem;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-block;
  backdrop-filter: blur(8px);
}

.btn-back:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.35);
  transform: translateX(-2px);
}

.view-header h1 {
  font-size: 2.3rem;
  margin: 0;
  background: linear-gradient(135deg, #38bdf8 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 800;
}

.view-header p {
  color: #94a3b8;
  margin: 6px 0 0 0;
  font-size: 0.95rem;
}

/* Layout Grid */
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

/* Cards */
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

/* Stepper Card */
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
  min-height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.step-action-pane {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
}

.instruction-badge {
  font-size: 0.72rem;
  background-color: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
  padding: 4px 8px;
  border-radius: 6px;
  text-align: center;
  animation: pulse-orange 1.5s infinite alternate;
}

@keyframes pulse-orange {
  0% { box-shadow: 0 0 2px rgba(245, 158, 11, 0.2); }
  100% { box-shadow: 0 0 10px rgba(245, 158, 11, 0.4); }
}

.target-readout {
  font-size: 0.82rem;
  color: #cbd5e1;
}

.text-emerald {
  color: #34d399;
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

.cyan-btn { background: #38bdf8; color: #0f172a; }
.cyan-btn:hover { background: #7dd3fc; box-shadow: 0 0 15px rgba(56, 189, 248, 0.35); }

.purple-btn { background: #a855f7; color: white; }
.purple-btn:hover { background: #c084fc; box-shadow: 0 0 15px rgba(168, 85, 247, 0.35); }

.reset-btn { background: #475569; color: white; }
.reset-btn:hover { background: #64748b; }

.action-buttons-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

/* Nav Stepper buttons */
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

/* Metrics */
.metrics-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.metric-box {
  flex: 1;
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: 8px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.metric-label {
  font-size: 0.65rem;
  color: #64748b;
  text-transform: uppercase;
  margin-bottom: 2px;
}

.metric-value {
  font-size: 1.05rem;
  font-weight: 700;
  color: #cbd5e1;
}

.text-cyan {
  color: #38bdf8;
}

/* Measurement Outcomes */
.measurement-results {
  text-align: center;
  width: 100%;
}

.outcome-badge {
  font-size: 0.95rem;
  font-weight: 800;
  padding: 4px 12px;
  border-radius: 8px;
  display: inline-block;
  margin-bottom: 6px;
}

.outcome-badge.success {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
}

.outcome-badge.fail {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.outcome-text {
  font-size: 0.82rem;
  color: #cbd5e1;
  line-height: 1.4;
  margin: 0;
}

/* Didactic analogies */
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

/* Database Card and Chest Grid */
.database-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 8px;
  margin-bottom: 15px;
}

.db-info-badge {
  font-size: 0.68rem;
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.04);
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.chests-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

@media (max-width: 576px) {
  .chests-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.chest-wrapper {
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  transition: all 0.2s ease;
  user-select: none;
}

.chest-wrapper.active-click {
  cursor: pointer;
}

.chest-wrapper.active-click:hover {
  background: rgba(56, 189, 248, 0.06);
  border-color: rgba(56, 189, 248, 0.25);
  transform: translateY(-2px);
}

.chest-wrapper.target-chest {
  border-color: #a855f7;
  background: rgba(168, 85, 247, 0.05);
  box-shadow: 0 0 12px rgba(168, 85, 247, 0.15);
}

.chest-wrapper.measured-chest {
  border-color: #38bdf8;
  background: rgba(56, 189, 248, 0.08);
  box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
}

.chest-wrapper.measured-chest.target-chest {
  border-color: #10b981;
  background: rgba(16, 185, 129, 0.08);
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.25);
}

.chest-box-icon {
  font-size: 2.2rem;
  line-height: 1;
  margin-bottom: 6px;
  transition: transform 0.2s;
}

.chest-wrapper:hover .chest-box-icon {
  transform: scale(1.1);
}

.chest-label {
  font-size: 0.8rem;
  color: #cbd5e1;
  font-weight: bold;
}

.chest-probability {
  font-size: 0.68rem;
  color: #38bdf8;
  margin-top: 2px;
}

.winner-mark {
  position: absolute;
  top: 6px;
  font-size: 0.58rem;
  background: #a855f7;
  color: white;
  padding: 1px 4px;
  border-radius: 4px;
  font-weight: 700;
  text-transform: uppercase;
}

.winner-mark.measured {
  background: #10b981;
}

/* Chart Card and SVG style */
.chart-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 8px;
  margin-bottom: 15px;
}

.legend-row {
  display: flex;
  gap: 12px;
  font-size: 0.72rem;
  color: #94a3b8;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-color {
  width: 8px;
  height: 8px;
  border-radius: 2px;
  display: inline-block;
}

.cyan-bg { background-color: #38bdf8; }
.purple-bg { background-color: #a855f7; }

.legend-color.dashed-line {
  width: 12px;
  height: 2px;
  background: transparent;
  border-top: 1.5px dashed #fbbf24;
  border-radius: 0;
}

.svg-chart-container {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 10px;
}

.amplitude-svg {
  width: 100%;
  display: block;
  overflow: visible;
}

.axis-line {
  stroke: #475569;
  stroke-width: 1.5;
}

.axis-lbl {
  fill: #64748b;
  font-size: 10px;
  text-anchor: start;
}

.grid-line {
  stroke: rgba(255, 255, 255, 0.03);
  stroke-width: 1;
}

.mean-avg-line {
  stroke: #f59e0b;
  stroke-width: 1.5;
  stroke-dasharray: 4 3;
  transition: all 0.3s ease;
}

.mean-avg-text {
  fill: #f59e0b;
  font-size: 9px;
  font-weight: bold;
  text-anchor: start;
  transition: all 0.3s ease;
}

.amp-bar {
  fill: #38bdf8;
  rx: 2;
  ry: 2;
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  opacity: 0.85;
}

.amp-bar.winner-bar {
  fill: #a855f7;
  opacity: 1;
  filter: drop-shadow(0 0 4px rgba(168, 85, 247, 0.4));
}

.amp-bar.negative-bar {
  opacity: 0.75;
}

.amp-bar.winner-bar.negative-bar {
  fill: #c084fc;
}

.amp-val {
  fill: #94a3b8;
  font-size: 9px;
  text-anchor: middle;
  transition: all 0.3s ease;
}

.winner-text {
  fill: #a855f7 !important;
  font-weight: bold;
}

.state-lbl {
  fill: #cbd5e1;
  font-size: 11px;
  text-anchor: middle;
}

/* Estilización premium para fórmulas matemáticas nativas */
.math-render {
  font-family: 'Cambria Math', 'Times New Roman', Times, serif;
  font-size: 1.15rem;
  color: #34d399;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #030712;
  padding: 8px 12px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.03);
  width: 100%;
  box-sizing: border-box;
}

.math-render i {
  font-style: italic;
  padding: 0 1px;
}

.math-frac {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  vertical-align: middle;
  padding: 0 4px;
  font-size: 0.95rem;
}

.math-num {
  border-bottom: 1px solid #34d399;
  padding-bottom: 1px;
  text-align: center;
  width: 100%;
}

.math-den {
  padding-top: 1px;
  text-align: center;
  width: 100%;
}
</style>
