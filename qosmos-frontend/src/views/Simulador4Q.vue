<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useQuantumStore } from '../stores/quantumState'
import BlochSphere from '../components/BlochSphere.vue'

const quantumStore = useQuantumStore()

// Selectores reactivos para aplicar compuertas
const selectedTarget = ref<number>(0)
const selectedControl = ref<number>(0)
const selectedTargetCnot = ref<number>(1)

// Interruptor para ver solo estados activos (>0%)
const showActiveOnly = ref<boolean>(true)

// --- VARIABLES DEL MODO FERIA CIENTÍFICA ---
const activeExperiment = ref<string | null>(null)
const currentStep = ref<number>(0)

// Iniciar un experimento guiado
const startExperiment = (expName: string) => {
  activeExperiment.value = expName
  currentStep.value = 0
  quantumStore.resetQubit() // Empezar de cero
  
  // Forzar selecciones correctas iniciales para comodidad del usuario
  if (expName === 'schrodinger' || expName === 'classical_vs_quantum') {
    selectedTarget.value = 0
  } else if (expName === 'entanglement') {
    selectedTarget.value = 0
    selectedControl.value = 0
    selectedTargetCnot.value = 1
  }
}

// Cancelar experimento
const cancelExperiment = () => {
  activeExperiment.value = null
  currentStep.value = 0
}

// Watcher para avanzar los pasos del tutorial de forma inteligente
watch(
  () => [quantumStore.gateHistory.length, quantumStore.isMeasured, selectedTarget.value, selectedControl.value, selectedTargetCnot.value] as const,
  () => {
    if (!activeExperiment.value) return
    
    const history = quantumStore.gateHistory
    const lastOp = history.length > 0 ? history[history.length - 1] : null
    
    if (activeExperiment.value === 'schrodinger') {
      if (currentStep.value === 0) {
        // H en Q0
        if (lastOp && lastOp.gate === 'H' && lastOp.target === 0) {
          currentStep.value = 1
        }
      } else if (currentStep.value === 1) {
        // Medir
        if (quantumStore.isMeasured) {
          currentStep.value = 2
        }
      } else if (currentStep.value === 2) {
        // Reiniciar
        if (!quantumStore.isMeasured && history.length === 0) {
          activeExperiment.value = null
          currentStep.value = 0
        }
      }
    } else if (activeExperiment.value === 'entanglement') {
      if (currentStep.value === 0) {
        // H en Q0
        if (lastOp && lastOp.gate === 'H' && lastOp.target === 0) {
          currentStep.value = 1
        }
      } else if (currentStep.value === 1) {
        // CNOT de 0 a 1
        if (lastOp && lastOp.gate === 'CNOT' && lastOp.control === 0 && lastOp.target === 1) {
          currentStep.value = 2
        }
      } else if (currentStep.value === 2) {
        // Medir
        if (quantumStore.isMeasured) {
          currentStep.value = 3
        }
      } else if (currentStep.value === 3) {
        // Reiniciar
        if (!quantumStore.isMeasured && history.length === 0) {
          activeExperiment.value = null
          currentStep.value = 0
        }
      }
    } else if (activeExperiment.value === 'classical_vs_quantum') {
      if (currentStep.value === 0) {
        // X en Q0
        if (lastOp && lastOp.gate === 'X' && lastOp.target === 0) {
          currentStep.value = 1
        }
      } else if (currentStep.value === 1) {
        // H en Q0
        if (lastOp && lastOp.gate === 'H' && lastOp.target === 0) {
          currentStep.value = 2
        }
      } else if (currentStep.value === 2) {
        // Medir
        if (quantumStore.isMeasured) {
          currentStep.value = 3
        }
      } else if (currentStep.value === 3) {
        // Reiniciar
        if (!quantumStore.isMeasured && history.length === 0) {
          activeExperiment.value = null
          currentStep.value = 0
        }
      }
    }
  }
)

// Obtener las instrucciones escritas en texto sencillo para cada paso
const tutorialInstruction = computed(() => {
  if (!activeExperiment.value) return ''
  
  if (activeExperiment.value === 'schrodinger') {
    if (currentStep.value === 0) {
      return 'Paso 1: Selecciona "Q0 (Púrpura)" arriba como Qubit Objetivo y haz clic en el botón "H" (Hadamard). Esto pondrá al gato en superposición: vivo y muerto al mismo tiempo.'
    }
    if (currentStep.value === 1) {
      return 'Paso 2: ¡Excelente! Q0 está ahora en superposición (mira cómo la aguja de la esfera púrpura está acostada en el ecuador, como una moneda girando). Haz clic en "⚡ Medir Sistema" para abrir la caja y observar el resultado.'
    }
    if (currentStep.value === 2) {
      return 'Experimento Completado: La observación forzó al sistema a colapsar a una sola realidad clásica (vivo |00⟩ o muerto |01⟩). Haz clic en "🔄 Reiniciar Registros" para comenzar otro.'
    }
  }
  
  if (activeExperiment.value === 'entanglement') {
    if (currentStep.value === 0) {
      return 'Paso 1: Primero, prepara Q0 en superposición. Asegúrate de seleccionar "Q0 (Púrpura)" en el selector y haz clic en "H".'
    }
    if (currentStep.value === 1) {
      return 'Paso 2: Ahora, entrelaza Q0 con Q1. En la sección de CNOT, selecciona Control: "Q0" y Objetivo: "Q1", luego haz clic en "Aplicar CNOT".'
    }
    if (currentStep.value === 2) {
      return 'Paso 3: ¡Logrado! Q0 y Q1 son gemelos. Fíjate cómo sus agujas se encogieron al centro. Haz clic en "⚡ Medir Sistema" para comprobar que al medir uno, el otro se decide en el acto.'
    }
    if (currentStep.value === 3) {
      return 'Experimento Completado: La medición colapsó a ambos qubits en el mismo estado de forma instantánea. Haz clic en "🔄 Reiniciar Registros" para finalizar.'
    }
  }
  
  if (activeExperiment.value === 'classical_vs_quantum') {
    if (currentStep.value === 0) {
      return 'Paso 1: Un bit clásico es como un interruptor. Asegúrate de seleccionar "Q0 (Púrpura)" y haz clic en "X" (NOT cuántico) para cambiar su valor clásico de 0 a 1.'
    }
    if (currentStep.value === 1) {
      return 'Paso 2: Ves que la aguja gira al polo sur (|1⟩), un estado clásico fijo. Ahora hagámoslo cuántico: haz clic en "H" en Q0 para ponerlo a girar.'
    }
    if (currentStep.value === 2) {
      return 'Paso 3: Q0 está ahora en superposición cuántica. Haz clic en "⚡ Medir Sistema" para observar a qué valor clásico cae.'
    }
    if (currentStep.value === 3) {
      return 'Experimento Completado: El qubit cuántico ha colapsado a una realidad clásica estable. Haz clic en "🔄 Reiniciar Registros" para terminar.'
    }
  }
  
  return ''
})

// Función para comprobar si un botón en particular debe brillar
const isButtonHighlighted = (buttonName: string) => {
  if (!activeExperiment.value) return false
  
  if (activeExperiment.value === 'schrodinger') {
    if (currentStep.value === 0 && buttonName === 'H' && selectedTarget.value === 0) return true
    if (currentStep.value === 0 && buttonName === 'target-select') return selectedTarget.value !== 0
    if (currentStep.value === 1 && buttonName === 'measure') return true
    if (currentStep.value === 2 && buttonName === 'reset') return true
  }
  
  if (activeExperiment.value === 'entanglement') {
    if (currentStep.value === 0 && buttonName === 'H' && selectedTarget.value === 0) return true
    if (currentStep.value === 0 && buttonName === 'target-select') return selectedTarget.value !== 0
    if (currentStep.value === 1 && buttonName === 'cnot' && selectedControl.value === 0 && selectedTargetCnot.value === 1) return true
    if (currentStep.value === 1 && buttonName === 'cnot-select') return selectedControl.value !== 0 || selectedTargetCnot.value !== 1
    if (currentStep.value === 2 && buttonName === 'measure') return true
    if (currentStep.value === 3 && buttonName === 'reset') return true
  }
  
  if (activeExperiment.value === 'classical_vs_quantum') {
    if (currentStep.value === 0 && buttonName === 'X' && selectedTarget.value === 0) return true
    if (currentStep.value === 0 && buttonName === 'target-select') return selectedTarget.value !== 0
    if (currentStep.value === 1 && buttonName === 'H' && selectedTarget.value === 0) return true
    if (currentStep.value === 1 && buttonName === 'target-select') return selectedTarget.value !== 0
    if (currentStep.value === 2 && buttonName === 'measure') return true
    if (currentStep.value === 3 && buttonName === 'reset') return true
  }
  
  return false
}

// --- TRADUCTOR DE ANALOGÍAS CUÁNTICAS ---
const translatedDirac = computed(() => {
  const notation = quantumStore.diracNotation.trim()
  if (quantumStore.isMeasured) {
    return 'La superposición se ha roto de forma irreversible. La medición obligó al sistema a colapsar a una sola realidad clásica determinada.'
  }
  
  if (notation === '|00|' || notation === '|00⟩') {
    return 'El simulador está en reposo absoluto. Los 2 qubits tienen un valor físico de cero.'
  }
  
  const history = quantumStore.gateHistory
  const hasEntanglement = history.some(op => op.gate === 'CNOT')
  
  if (hasEntanglement && notation.includes('+')) {
    return '¡Entrelazamiento cuántico activo! Ambos qubits se han convertido en gemelos correlacionados. Su estado individual se difuminó y sus destinos ahora están atados.'
  }
  
  if (notation.includes('+') || notation.includes('-')) {
    return 'Superposición cuántica activa. Los qubits están en múltiples realidades paralelas al mismo tiempo. Es el equivalente a monedas girando rápido en el aire.'
  }
  
  if (notation === '|10⟩') {
    return 'Q0 (Púrpura) cambió a valor clásico 1. Es como pulsar un interruptor de luz en encendido.'
  }
  
  return 'El sistema cuántico se encuentra en un estado compuesto de superposición cuántica.'
})

// --- ESTILO DE LA LÍNEA VERTICAL DE CNOT EN LA PARTITURA ---
const getCnotLineStyleLocal = (control: number | undefined, target: number) => {
  if (control === undefined) return {}
  const min = Math.min(control, target)
  const max = Math.max(control, target)
  return {
    top: `${min * 44 + 22}px`,
    height: `${(max - min) * 44}px`
  }
}

// Filtrar las probabilidades para la vista del Dashboard
const filteredProbabilities = computed(() => {
  if (showActiveOnly.value) {
    return quantumStore.probabilities.filter(p => p.prob > 0.01)
  }
  return quantumStore.probabilities
})

// Función envolvente para enviar las compuertas
const handleGate = (gateName: string) => {
  console.log(`[Frontend] Enviando compuerta: ${gateName}`);
  if (gateName === 'CNOT') {
    if (selectedControl.value === selectedTargetCnot.value) {
      alert("El qubit de Control y Objetivo no pueden ser el mismo.");
      return;
    }
    quantumStore.applyGate(gateName, selectedTargetCnot.value, selectedControl.value);
  } else {
    quantumStore.applyGate(gateName, selectedTarget.value);
  }
}

const handleMeasure = () => {
  console.log("[Frontend] Solicitando medición...");
  quantumStore.measureSystem();
}

const handleReset = () => {
  console.log("[Frontend] Reiniciando Qubits...");
  quantumStore.resetQubit();
}

const ejecutarEnIBM = async () => {
  if (quantumStore.gateHistory.length === 0) {
    alert("¡Añade algunas compuertas al circuito primero!");
    return;
  }

  alert("Iniciando conexión segura con IBM Quantum. Esto puede tardar unos segundos...");
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/ibm-execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ gate_history: quantumStore.gateHistory })
    });
    
    const data = await response.json();
    console.log("Respuesta de IBM:", data);
    
    if (data.status === "Éxito") {
      alert(`¡Cálculo finalizado en IBM Cloud!\nResultados de hardware real: ${JSON.stringify(data.resultados_raw)}`);
    } else {
      alert("Error en la conexión con IBM: " + data.mensaje);
    }
  } catch (error) {
    console.error("Error al contactar al backend:", error);
  }
}
</script>

<template>
  <main class="qosmos-container">
    <header class="qosmos-header">
      <div class="header-nav">
        <router-link to="/" class="btn-back">← Volver al Menú</router-link>
      </div>
      <h1>Qosmos</h1>
      <p>Simulador Cuántico Multiqubit • Panel de Laboratorio Físico (2 Qubits)</p>
    </header>

    <div class="dashboard-container">
      
      <!-- Panel de Control (Izquierda Superior) -->
      <section class="panel-left-top">
        
        <!-- MODO FERIA CIENTÍFICA (GUÍAS DE EXPERIMENTOS) -->
        <div class="card tutorial-card" style="margin-bottom: 15px;">
          <h3 style="color: #a855f7; display: flex; align-items: center; gap: 8px;">
            🎓 Modo Feria Científica
          </h3>
          <p style="font-size: 0.8rem; color: #94a3b8; margin-top: -5px; margin-bottom: 10px;">
            Elige un experimento interactivo para aprender física cuántica paso a paso.
          </p>
          <div class="tutorial-btn-grid">
            <button @click="startExperiment('schrodinger')" :class="['btn-exp', { active: activeExperiment === 'schrodinger' }]">
              🐱 Superposición
            </button>
            <button @click="startExperiment('entanglement')" :class="['btn-exp', { active: activeExperiment === 'entanglement' }]">
              ⚛️ Entrelazamiento
            </button>
            <button @click="startExperiment('classical_vs_quantum')" :class="['btn-exp', { active: activeExperiment === 'classical_vs_quantum' }]">
              🎛️ Clásico vs Cuántico
            </button>
          </div>
          
          <!-- Caja del Entrenador (Muestra el paso activo) -->
          <div v-if="activeExperiment" class="coach-box">
            <div class="coach-header">
              <span class="coach-badge">Guía de Feria</span>
              <button @click="cancelExperiment" class="btn-cancel-tutorial">Salir</button>
            </div>
            <p class="coach-text">{{ tutorialInstruction }}</p>
          </div>
        </div>

        <div class="card gates-card">
          <h3>Compuertas Cuánticas</h3>
          
          <!-- Control para Compuertas de 1 Qubit -->
          <div class="gate-section-block">
            <h4 class="section-title">Compuertas de 1 Qubit</h4>
            
            <div class="selector-row">
              <label for="target-select">Qubit Objetivo:</label>
              <select id="target-select" v-model="selectedTarget" class="qosmos-select" 
                      :class="{ 'highlight-pulse': isButtonHighlighted('target-select') }">
                <option :value="0">Q0 (Púrpura)</option>
                <option :value="1">Q1 (Celeste)</option>
              </select>
            </div>
            
            <div class="gates-grid-compact">
              <button @click="handleGate('H')" :disabled="quantumStore.isMeasured" class="btn-gate-new" :class="{ 'highlight-pulse': isButtonHighlighted('H') }" title="Hadamard (Superposición)">H</button>
              <button @click="handleGate('X')" :disabled="quantumStore.isMeasured" class="btn-gate-new" :class="{ 'highlight-pulse': isButtonHighlighted('X') }" title="Pauli-X (NOT cuántico)">X</button>
              <button @click="handleGate('Y')" :disabled="quantumStore.isMeasured" class="btn-gate-new" :class="{ 'highlight-pulse': isButtonHighlighted('Y') }" title="Pauli-Y">Y</button>
              <button @click="handleGate('Z')" :disabled="quantumStore.isMeasured" class="btn-gate-new" :class="{ 'highlight-pulse': isButtonHighlighted('Z') }" title="Pauli-Z">Z</button>
            </div>
          </div>
          
          <!-- Control para CNOT (2 Qubits) -->
          <div class="gate-section-block" style="margin-top: 15px;">
            <h4 class="section-title">Compuerta de Entrelazamiento (CNOT)</h4>
            
            <div class="cnot-selectors-row">
              <div class="select-group">
                <label>Control:</label>
                <select v-model="selectedControl" class="qosmos-select select-mini" :class="{ 'highlight-pulse': isButtonHighlighted('cnot-select') }">
                  <option :value="0">Q0</option>
                  <option :value="1">Q1</option>
                </select>
              </div>
              <div class="select-group">
                <label>Objetivo:</label>
                <select v-model="selectedTargetCnot" class="qosmos-select select-mini" :class="{ 'highlight-pulse': isButtonHighlighted('cnot-select') }">
                  <option :value="0">Q0</option>
                  <option :value="1">Q1</option>
                </select>
              </div>
            </div>
            
            <button @click="handleGate('CNOT')" :disabled="quantumStore.isMeasured" class="btn-gate-cnot" :class="{ 'highlight-pulse': isButtonHighlighted('cnot') }">
              Aplicar CNOT (q{{ selectedControl }} → q{{ selectedTargetCnot }})
            </button>
          </div>
          
          <!-- Botones de Acción Global -->
          <div class="actions-block-vertical">
            <button @click="handleMeasure()" :disabled="quantumStore.isMeasured" class="btn-measure" 
                    :class="{ 'highlight-pulse': isButtonHighlighted('measure') }"
                    :style="{ cursor: quantumStore.isMeasured ? 'not-allowed' : 'pointer', opacity: quantumStore.isMeasured ? 0.5 : 1 }">
              ⚡ Medir Sistema (Colapsar)
            </button>
            <button @click="handleReset()" class="btn-reset" :class="{ 'highlight-pulse': isButtonHighlighted('reset') }">
              🔄 Reiniciar Registros
            </button>
            <button @click="ejecutarEnIBM" class="btn-ibm">
              ☁️ Ejecutar en Procesador IBM
            </button>
          </div>
        </div>
      </section>

      <!-- Panel de Métricas/Probabilidades (Izquierda Inferior) -->
      <section class="panel-left-bottom">
        <div class="card metrics-card">
          <div class="metrics-title-row">
            <h3>Medición y Probabilidad</h3>
            <label class="toggle-active-only">
              <input type="checkbox" v-model="showActiveOnly">
              Solo activos
            </label>
          </div>
          
          <div class="probabilities-scroll-container">
            <div v-if="filteredProbabilities.length === 0" class="no-probs-text">
              No hay estados activos con probabilidad > 0%
            </div>
            <div v-else class="probs-list">
              <div v-for="state in filteredProbabilities" :key="state.label" class="progress-bar-container">
                <div class="bar-label">
                  <span>Estado |{{ state.label }}⟩</span>
                  <span>{{ state.prob }}%</span>
                </div>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: state.prob + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Panel de Esferas y Rayos X (Centro y Derecha) -->
      <section class="panel-center">
        <div class="card visualizer-card">
          <BlochSphere />
        </div>

        <div class="card xray-card" style="margin-top: 15px;">
          <h3><span style="color: #34d399;">⚙</span> Notación de Dirac (Estado de Superposición)</h3>
          <div class="math-display">
            <span class="math-prefix">|ψ⟩ = </span>
            <span class="dirac-equation">{{ quantumStore.diracNotation }}</span>
          </div>
          
          <!-- Traductor de Analogía para la Feria Científica -->
          <div class="dirac-analog-box">
            <div class="analog-header">💡 ¿Qué significa esto en la realidad?</div>
            <p class="analog-text">{{ translatedDirac }}</p>
          </div>
        </div>

        <!-- PANEL DE ECUACIONES Y NORMALIZACIÓN -->
        <div class="card math-card" style="margin-top: 15px; border-left: 4px solid #38bdf8; background: rgba(56, 189, 248, 0.04);">
          <h3><span style="color: #38bdf8;">📊</span> Ecuaciones y Normalización del Registro</h3>
          <div class="math-formulas-box" style="font-size: 0.8rem; line-height: 1.45; color: #cbd5e1; display: grid; gap: 8px;">
            <p style="margin: 4px 0 0 0;"><strong>Estado cuántico de 2 qubits (Espacio de Hilbert ℂ⁴):</strong></p>
            <div class="math-render">
              |<i>ψ</i>⟩ = <i>c</i><sub>00</sub>|00⟩ + <i>c</i><sub>01</sub>|01⟩ + <i>c</i><sub>10</sub>|10⟩ + <i>c</i><sub>11</sub>|11⟩
            </div>
            <p style="margin: 4px 0 0 0;"><strong>Condición de Normalización (Probabilidad total = 1):</strong></p>
            <div class="math-render">
              Σ |<i>c</i><sub><i>ij</i></sub>|² = |<i>c</i><sub>00</sub>|² + |<i>c</i><sub>01</sub>|² + |<i>c</i><sub>10</sub>|² + |<i>c</i><sub>11</sub>|² = 1
            </div>
            <p style="margin: 4px 0 0 0;"><strong>Compuertas aplicadas en este simulador:</strong></p>
            <ul style="margin: 3px 0; padding-left: 20px;">
              <li><strong>Hadamard (Superposición):</strong> <i>H</i> = 
                <span class="math-frac" style="font-size: 0.85rem;">
                  <span class="math-num">1</span>
                  <span class="math-den">√2</span>
                </span>
                [[1, 1], [1, -1]]
              </li>
              <li><strong>Pauli-X (Negación cuántica):</strong> <i>X</i> = [[0, 1], [1, 0]]</li>
              <li><strong>CNOT (Entrelazamiento):</strong> Invierte el qubit objetivo si el control es |1⟩.</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Partitura de Circuito Completo (Fila Inferior) -->
      <section class="panel-bottom">
        <div class="card timeline-card">
          <h3>Partitura de Circuito Cuántico (Quantum Composer)</h3>
          
          <div class="circuit-composer-container">
            <div v-if="quantumStore.gateHistory.length === 0" class="composer-empty-text">
              El circuito está vacío. Aplica compuertas en el panel de control.
            </div>
            
            <div v-else class="composer-timeline-board">
              <!-- Columna izquierda fija para los nombres de las líneas -->
              <div class="composer-labels-column">
                <div v-for="q in [0, 1]" :key="q" class="composer-label-cell">
                  |q{{ q }}⟩
                </div>
              </div>
              
              <!-- Contenedor del historial con scroll horizontal -->
              <div class="composer-gates-columns">
                <div v-for="(op, opIdx) in quantumStore.gateHistory" :key="opIdx" class="composer-gate-col">
                  
                  <!-- Línea vertical si es una CNOT -->
                  <div v-if="op.gate === 'CNOT'" class="cnot-vertical-line" :style="getCnotLineStyleLocal(op.control, op.target)"></div>
                  
                  <!-- Celdas para cada qubit en la columna -->
                  <div v-for="q in [0, 1]" :key="q" class="composer-gate-cell">
                    <!-- Segmento de línea horizontal de fondo -->
                    <div class="wire-segment-line"></div>
                    
                    <!-- Dibujar según la operación -->
                    <div v-if="op.target === q && op.gate !== 'CNOT'" class="composer-gate-box">
                      {{ op.gate }}
                    </div>
                    <div v-else-if="op.control === q && op.gate === 'CNOT'" class="composer-cnot-ctrl">
                      ●
                    </div>
                    <div v-else-if="op.target === q && op.gate === 'CNOT'" class="composer-cnot-targ">
                      ⊕
                    </div>
                    <div v-else-if="op.target === -1" class="composer-measure-box-score">
                      M
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

    </div>
  </main>
</template>

<style>
/* --- ESTILOS UNIFICADOS Y LIMPIOS PARA QOSMOS --- */
body, .qosmos-container {
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: #0b0f19;
  color: #f8fafc;
  min-height: 100vh;
  margin: 0;
  padding: 15px;
  box-sizing: border-box;
}

.qosmos-header {
  text-align: center;
  margin-bottom: 15px;
  border-bottom: 2px solid #1e293b;
  padding-bottom: 10px;
  position: relative;
}

.header-nav {
  position: absolute;
  left: 0;
  top: 10px;
  z-index: 10;
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
  display: inline-block;
}

.btn-back:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: #38bdf8;
  transform: translateX(-3px);
}

.qosmos-header h1 {
  font-size: 2.5rem;
  margin: 0;
  background: linear-gradient(to right, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.qosmos-header p {
  color: #94a3b8;
  margin: 5px 0 0 0;
  font-size: 0.95rem;
}

/* --- LAYOUT GRID DEL DASHBOARD --- */
.dashboard-container {
  display: grid;
  grid-template-columns: 320px 1fr;
  grid-template-areas: 
    "left-top center"
    "left-bottom center"
    "bottom bottom";
  gap: 15px;
  max-width: 1400px;
  margin: 0 auto;
}

.panel-left-top { grid-area: left-top; display: flex; flex-direction: column; }
.panel-left-bottom { grid-area: left-bottom; display: flex; flex-direction: column; }
.panel-center { 
  grid-area: center; 
  display: flex;
  flex-direction: column; 
  gap: 15px;
}
.panel-bottom { grid-area: bottom; }

/* Tarjetas Estilo Glassmorphism */
.card {
  background: rgba(17, 24, 39, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
  padding: 15px;
  border-radius: 16px;
}

.card h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.2rem;
  color: #e2e8f0;
}

/* --- ESTILOS DE LA SECCIÓN TUTORIAL (MODO FERIA CIENTÍFICA) --- */
.tutorial-btn-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 5px;
  margin-bottom: 10px;
}

.btn-exp {
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 0.68rem;
  padding: 6px 2px;
  cursor: pointer;
  font-weight: bold;
  transition: all 0.2s;
}

.btn-exp:hover {
  background-color: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.3);
  color: #38bdf8;
}

.btn-exp.active {
  background-color: rgba(168, 85, 247, 0.2);
  border-color: rgba(168, 85, 247, 0.5);
  color: #c084fc;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.15);
}

.coach-box {
  background: rgba(168, 85, 247, 0.08);
  border: 1px solid rgba(168, 85, 247, 0.25);
  border-radius: 8px;
  padding: 8px 10px;
  margin-top: 5px;
  position: relative;
}

.coach-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.coach-badge {
  font-size: 0.65rem;
  background-color: #a855f7;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: bold;
  text-transform: uppercase;
}

.btn-cancel-tutorial {
  background: none;
  border: none;
  color: #ef4444;
  font-size: 0.68rem;
  font-weight: bold;
  cursor: pointer;
  padding: 0;
}

.btn-cancel-tutorial:hover {
  text-decoration: underline;
}

.coach-text {
  font-size: 0.76rem;
  line-height: 1.35;
  color: #cbd5e1;
  margin: 0;
}

/* Animación de Pulso de Brillo */
@keyframes pulse-glowing {
  0% { box-shadow: 0 0 5px #38bdf8; border-color: #38bdf8; }
  50% { box-shadow: 0 0 20px #8b5cf6, 0 0 30px #38bdf8; border-color: #a855f7; }
  100% { box-shadow: 0 0 5px #38bdf8; border-color: #38bdf8; }
}

.highlight-pulse {
  animation: pulse-glowing 1s infinite !important;
  border-color: #a855f7 !important;
  transform: scale(1.02);
  z-index: 50;
  position: relative;
}

/* --- ESTILOS DEL TRADUCTOR DE ANALOGÍAS --- */
.dirac-analog-box {
  margin-top: 10px;
  background-color: rgba(2, 44, 34, 0.4);
  border: 1px dashed rgba(52, 211, 153, 0.3);
  border-radius: 8px;
  padding: 8px 10px;
}

.analog-header {
  font-size: 0.76rem;
  color: #34d399;
  font-weight: bold;
  margin-bottom: 3px;
}

.analog-text {
  font-size: 0.74rem;
  line-height: 1.35;
  color: #cbd5e1;
  margin: 0;
}

/* --- COMPUERTAS Y SELECTORES --- */
.gate-section-block {
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 10px;
}

.section-title {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 0.85rem;
  color: #38bdf8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.selector-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.82rem;
}

.qosmos-select {
  background-color: #0f172a;
  color: #38bdf8;
  border: 1px solid #334155;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.8rem;
  cursor: pointer;
  outline: none;
}

.qosmos-select:focus {
  border-color: #38bdf8;
}

.gates-grid-compact {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}

.btn-gate-new {
  background-color: #1e293b;
  color: #38bdf8;
  border: 1px solid #334155;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-gate-new:hover:not(:disabled) {
  background-color: #334155;
  transform: translateY(-1px);
  border-color: #38bdf8;
}

.btn-gate-new:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* CNOT */
.cnot-selectors-row {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.select-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 0.78rem;
  color: #94a3b8;
}

.select-mini {
  width: 100%;
}

.btn-gate-cnot {
  width: 100%;
  background-color: #0e7490;
  color: #cffafe;
  border: 1px solid #0891b2;
  padding: 8px;
  border-radius: 6px;
  font-weight: bold;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-gate-cnot:hover:not(:disabled) {
  background-color: #0891b2;
  transform: translateY(-1px);
}

.btn-gate-cnot:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Acciones Globales */
.actions-block-vertical {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 15px;
}

.btn-measure {
  padding: 10px;
  background-color: #6d28d9;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  font-size: 0.88rem;
  transition: all 0.2s;
}

.btn-reset {
  padding: 10px;
  background-color: #b91c1c;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.88rem;
  transition: all 0.2s;
}

.btn-ibm {
  padding: 10px;
  background-color: #1d4ed8;
  color: white;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  font-size: 0.88rem;
}

/* --- PROBABILIDADES --- */
.metrics-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.toggle-active-only {
  font-size: 0.72rem;
  color: #38bdf8;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: rgba(56, 189, 248, 0.08);
  padding: 3px 6px;
  border-radius: 4px;
  border: 1px solid rgba(56, 189, 248, 0.15);
}

.probabilities-scroll-container {
  max-height: 140px;
  overflow-y: auto;
  padding-right: 5px;
}

.probs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.no-probs-text {
  font-size: 0.78rem;
  color: #64748b;
  font-style: italic;
  text-align: center;
  padding: 20px 0;
}

.progress-bar-container {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.78rem;
  color: #cbd5e1;
  font-family: 'JetBrains Mono', monospace;
}

.progress-bar {
  background-color: #0f172a;
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(to right, #38bdf8, #8b5cf6);
  transition: width 0.3s ease;
}

/* Personalización del Scrollbar */
.probabilities-scroll-container::-webkit-scrollbar { width: 5px; }
.probabilities-scroll-container::-webkit-scrollbar-track { background: #0f172a; border-radius: 4px; }
.probabilities-scroll-container::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
.probabilities-scroll-container::-webkit-scrollbar-thumb:hover { background: #38bdf8; }

/* --- VISUALIZADOR Y RAYOS X --- */
.visualizer-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  background: radial-gradient(circle at center, #151d30 0%, #0b0f19 100%);
  position: relative;
  border-radius: 16px;
}

.xray-card {
  background: rgba(6, 78, 59, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.22);
}

.math-display {
  background-color: #022c22;
  border: 1px solid #047857;
  padding: 10px 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  overflow-x: auto;
  box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
}

.math-prefix {
  color: #34d399;
  font-family: 'JetBrains Mono', monospace;
  font-weight: bold;
  font-size: 1.15rem;
  margin-right: 5px;
}

.dirac-equation {
  color: #a7f3d0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.15rem;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

/* --- PARTITURA DE CIRCUITO COMPLETO --- */
.circuit-composer-container {
  background-color: #080d16;
  padding: 15px;
  border-radius: 12px;
  min-height: 120px;
  border: 1px solid #1e293b;
  display: flex;
  align-items: center;
  overflow-x: auto;
}

.composer-empty-text {
  color: #475569;
  font-style: italic;
  font-size: 0.9rem;
  text-align: center;
  width: 100%;
}

.composer-timeline-board {
  display: flex;
  position: relative;
}

.composer-labels-column {
  display: flex;
  flex-direction: column;
  border-right: 2px solid #1e293b;
  padding-right: 10px;
  background-color: #080d16;
  z-index: 10;
  flex-shrink: 0;
}

.composer-label-cell {
  height: 44px;
  display: flex;
  align-items: center;
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.05rem;
  font-weight: bold;
  color: #94a3b8;
}

.composer-gates-columns {
  display: flex;
  flex-direction: row;
  padding-left: 10px;
}

.composer-gate-col {
  display: flex;
  flex-direction: column;
  position: relative;
  width: 50px;
  flex-shrink: 0;
  align-items: center;
}

.composer-gate-cell {
  height: 44px;
  width: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.wire-segment-line {
  position: absolute;
  left: 0;
  right: 0;
  top: 21px; /* Mitad de los 44px */
  height: 2px;
  background-color: #1e293b;
  z-index: 0;
}

/* Caja de Compuertas en Partitura */
.composer-gate-box {
  background-color: #1e293b;
  border: 2px solid #38bdf8;
  color: #38bdf8;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-weight: bold;
  font-size: 0.95rem;
  border-radius: 4px;
  z-index: 2;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
  transition: all 0.2s;
}

/* CNOT Nodos */
.composer-cnot-ctrl {
  color: #06b6d4;
  font-size: 1.4rem;
  z-index: 3;
  background-color: #080d16;
  border-radius: 50%;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.composer-cnot-targ {
  color: #06b6d4;
  font-size: 1.5rem;
  z-index: 3;
  background-color: #080d16;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.composer-measure-box-score {
  background-color: #6d28d9;
  border: 2px solid #a78bfa;
  color: white;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-weight: bold;
  font-size: 0.9rem;
  border-radius: 6px;
  z-index: 2;
  box-shadow: 0 2px 5px rgba(0,0,0,0.5);
}

/* Línea Vertical para CNOT */
.cnot-vertical-line {
  position: absolute;
  left: 24px; /* Centro de los 50px */
  width: 2px;
  background-color: #06b6d4;
  z-index: 1;
}

/* Scrollbar para Circuit Score */
.circuit-composer-container::-webkit-scrollbar { height: 8px; }
.circuit-composer-container::-webkit-scrollbar-track { background: #080d16; border-radius: 4px; }
.circuit-composer-container::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
.circuit-composer-container::-webkit-scrollbar-thumb:hover { background: #38bdf8; }

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