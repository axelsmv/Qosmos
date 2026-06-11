<script setup lang="ts">
import { useQuantumStore } from './stores/quantumState'
import BlochSphere from './components/BlochSphere.vue'

const quantumStore = useQuantumStore()

// Funciones envolventes para asegurar que Vue escuche los clics
const handleGate = (gateName: string) => {
  console.log(`[Frontend] Enviando compuerta: ${gateName}`);
  quantumStore.applyGate(gateName);
}

const handleMeasure = () => {
  console.log("[Frontend] Solicitando medición...");
  quantumStore.measureSystem();
}

const handleReset = () => {
  console.log("[Frontend] Reiniciando Qubit...");
  quantumStore.resetQubit();
}
</script>
<template>
  <main class="qosmos-container">
    <header class="qosmos-header">
      <h1>Qosmos</h1>
      <p>Simulador de Computación Cuántica • Física Contemporánea</p>
    </header>

    <div class="dashboard-container">
      <section class="panel-left-top">
        <div class="card gates-card">
          <h3>Compuertas Cuánticas</h3>
          <div class="gates-grid">
            <button @click="quantumStore.applyGate('H')" :disabled="quantumStore.isMeasured" class="btn-gate" title="Matriz Hadamard: 1/√2 [[1, 1], [1, -1]]">Hadamard (H)</button>
            <button @click="quantumStore.applyGate('X')" :disabled="quantumStore.isMeasured" class="btn-gate" title="Matriz Pauli-X (NOT): [[0, 1], [1, 0]]">Pauli-X</button>
            <button @click="quantumStore.applyGate('Y')" :disabled="quantumStore.isMeasured" class="btn-gate" title="Matriz Pauli-Y: [[0, -i], [i, 0]]">Pauli-Y</button>
            <button @click="quantumStore.applyGate('Z')" :disabled="quantumStore.isMeasured" class="btn-gate" title="Matriz Pauli-Z: [[1, 0], [0, -1]]">Pauli-Z</button>
            <button @click="quantumStore.applyGate('CNOT')" :disabled="quantumStore.isMeasured" class="btn-gate" title="Matriz CNOT (4x4): Invierte Qubit Objetivo si Qubit Control es 1">CNOT</button>
          </div>
          
          <div class="actions-block">
            <button @click="handleMeasure()" :disabled="quantumStore.isMeasured" class="btn-measure" 
                    :style="{ cursor: quantumStore.isMeasured ? 'not-allowed' : 'pointer', opacity: quantumStore.isMeasured ? 0.5 : 1 }">
              Medir Sistema (Colapsar)
            </button>
            <button @click="handleReset()" class="btn-reset">
              Reiniciar Qubit
            </button>
          </div>
        </div>
      </section>

      <section class="panel-left-bottom">
        <div class="card metrics-card">
          <h3>Medición y Probabilidades (Sistema de 2 Qubits)</h3>
          
          <div class="progress-bar-container">
            <div class="bar-label">Estado |00⟩: {{ quantumStore.prob00 }}%</div>
            <div class="progress-bar">
              <div class="progress-fill zero" :style="{ width: quantumStore.prob00 + '%' }"></div>
            </div>
          </div>
          
          <div class="progress-bar-container">
            <div class="bar-label">Estado |01⟩: {{ quantumStore.prob01 }}%</div>
            <div class="progress-bar">
              <div class="progress-fill orange" :style="{ width: quantumStore.prob01 + '%' }"></div>
            </div>
          </div>

          <div class="progress-bar-container">
            <div class="bar-label">Estado |10⟩: {{ quantumStore.prob10 }}%</div>
            <div class="progress-bar">
              <div class="progress-fill green" :style="{ width: quantumStore.prob10 + '%' }"></div>
            </div>
          </div>

          <div class="progress-bar-container">
            <div class="bar-label">Estado |11⟩: {{ quantumStore.prob11 }}%</div>
            <div class="progress-bar">
              <div class="progress-fill one" :style="{ width: quantumStore.prob11 + '%' }"></div>
            </div>
          </div>
        </div>
      </section>

      <section class="panel-center">
        <div class="card visualizer-card">
          <BlochSphere />
          <div class="coords-overlay">Espacio de Hilbert: C⁴ (2 Qubits)</div>
        </div>

        <div class="card xray-card" style="margin-top: 20px;">
          <h3><span style="color: #34d399;">⚙</span> Motor Matemático (Rayos X)</h3>
          <p style="color: #94a3b8; font-size: 0.9rem; margin-top: -10px;">Estado actual del vector (Notación de Dirac)</p>
          
          <div class="math-display">
            <span class="math-prefix">|ψ⟩ = </span>
            <span class="dirac-equation">{{ quantumStore.diracNotation }}</span>
          </div>
        </div>
      </section>

      <section class="panel-bottom">
        <div class="card timeline-card">
          <h3>Partitura del Circuito</h3>
          <div class="circuit-diagram">
            <div v-if="quantumStore.gateHistory.length === 0" class="empty-text">
              El sistema está en el estado base |00⟩.
            </div>
            <div v-else class="gate-sequence">
              <div class="quantum-wire"></div>
              <div class="qubit-label">|0⟩</div>
              <div v-for="(gate, index) in quantumStore.gateHistory" :key="index" 
                   class="gate-box" :class="{'measure-box': gate.startsWith('M')}">
                {{ gate }}
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

/* Estilo base para todo el simulador */
body, .qosmos-container {
  font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: #0f172a; /* Fondo ultra oscuro */
  color: #f8fafc;
  min-height: 100vh;
  margin: 0;
  padding: 20px;
  box-sizing: border-box;
}

/* Header principal - Legible y elegante */
.qosmos-header {
  text-align: center;
  margin-bottom: 2rem;
  border-bottom: 2px solid #1e293b;
  padding-bottom: 1rem;
}

.qosmos-header h1 {
  font-size: 3rem; /* ¡Más grande y legible! */
  margin: 0;
  background: linear-gradient(to right, #38bdf8, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.qosmos-header p {
  color: #94a3b8;
  margin: 0.5rem 0 0 0;
  font-size: 1.1rem;
}

/* --- LAYOUT DEL DASHBOARD - LA SOLUCIÓN ESTRUCTURAL --- */
.dashboard-container {
  display: grid;
  grid-template-columns: 350px 1fr; /* Columna izquierda fija, derecha flexible */
  grid-template-areas: 
    "left-top center"
    "left-bottom center"
    "bottom bottom";
  gap: 20px;
  height: calc(100vh - 140px); /* Ajuste de altura dinámica */
  max-width: 1400px;
  margin: 0 auto;
}

/* Asignación de áreas a los paneles */
.panel-left-top { grid-area: left-top; display: flex; flex-direction: column; gap: 20px; }
.panel-left-bottom { grid-area: left-bottom; display: flex; flex-direction: column; gap: 20px; }
.panel-center { 
  grid-area: center; 
  min-height: 400px;
  display: flex;             /* Convertimos el panel en una columna flexible */
  flex-direction: column; 
  gap: 20px;                 /* Le damos un respiro entre la esfera y el panel de rayos X */
}
.panel-bottom { grid-area: bottom; margin-top: 10px; }

/* Estilo general para las tarjetas */
.card {
  background: rgba(17, 24, 39, 0.7); /* Vidrio esmerilado */
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  padding: 20px;
  border-radius: 16px;
  flex: 1; /* Para que llenen el espacio de forma uniforme */
}

.card h3 {
  margin-top: 0;
  margin-bottom: 1.25rem;
  font-size: 1.5rem; /* ¡Títulos mucho más grandes y claros! */
  color: #cbd5e1;
}

/* --- ESTILOS DE COMPUERTAS Y ACCIONES (¡Los botones que faltaban!) --- */
.gates-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 10px;
  margin-bottom: 1rem;
}

.btn-gate {
  background-color: #1e293b;
  color: #38bdf8;
  border: 1px solid #334155;
  padding: 15px; /* ¡Botones más grandes y cómodos! */
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
  transition: all 0.2s;
}

.btn-gate:hover:not(:disabled) {
  background-color: #334155;
  border-color: #38bdf8;
  transform: translateY(-2px);
}

.btn-gate:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background-color: #1e293b;
  color: #64748b;
  border-color: #334155;
}

.actions-block { display: flex; gap: 10px; }
.btn-measure { flex: 1; padding: 12px; background-color: #8b5cf6; color: white; border: none; border-radius: 6px; font-weight: bold; font-size: 1rem; }
.btn-reset { flex: 1; padding: 12px; background-color: #ef4444; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 1rem; }

/* --- ESTILOS DE PROBABILIDADES CON GRADIENTES --- */
.progress-bar-container { margin-bottom: 1rem; }
.bar-label { font-size: 1rem; margin-bottom: 0.25rem; color: #94a3b8; }
.progress-bar { background-color: #0f172a; height: 16px; border-radius: 8px; overflow: hidden; }
.progress-fill { height: 100%; transition: width 0.3s ease; }
.progress-fill.zero { background: linear-gradient(to right, #38bdf8, #8b5cf6); } /* Gradiente profesional */
.progress-fill.orange { background-color: #f59e0b; }
.progress-fill.green { background-color: #10b981; }
.progress-fill.one { background-color: #a855f7; }

/* --- ESTILOS DEL VISUALIZADOR 3D --- */
.visualizer-card {
  flex: 1;                   /* Reemplazamos height: 100% por flex: 1 para que ceda espacio */
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
  position: relative;
  border-radius: 16px;
}

.coords-overlay {
  position: absolute;
  bottom: 20px;
  background: rgba(15, 23, 42, 0.8);
  padding: 8px 16px;
  border-radius: 8px;
  color: #38bdf8;
  font-family: monospace;
  font-size: 1rem;
  border: 1px solid #334155;
}

/* --- ESTILOS DE LA PARTITURA DEL CIRCUITO --- */
.circuit-diagram {
  background-color: #0f172a;
  padding: 20px;
  border-radius: 8px;
  min-height: 80px;
  overflow-x: auto;
  border: 1px solid #1e293b;
  display: flex;
  align-items: center;
}

.gate-sequence { display: flex; align-items: center; gap: 15px; position: relative; min-width: max-content; padding-right: 20px; }
.quantum-wire { position: absolute; top: 50%; left: 40px; right: -20px; height: 2px; background-color: #334155; z-index: 0; }
.qubit-label { font-family: monospace; color: #94a3b8; font-size: 1.4rem; font-weight: bold; background-color: #0f172a; padding-right: 10px; z-index: 1; }

@keyframes pulse-glow { 0% { box-shadow: 0 0 5px #38bdf8; } 50% { box-shadow: 0 0 20px #38bdf8; } 100% { box-shadow: 0 0 5px #38bdf8; } }
.gate-box { animation: pulse-glow 2s infinite; background-color: #1e293b; border: 2px solid #38bdf8; color: #38bdf8; padding: 10px 15px; border-radius: 4px; font-family: monospace; font-weight: bold; font-size: 1.1rem; min-width: 40px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.4); flex-shrink: 0; z-index: 1; }
.measure-box { background-color: #8b5cf6; border-color: #a855f7; color: white; border-radius: 8px; }
.empty-text { color: #64748b; font-style: italic; z-index: 1; font-size: 1rem; }

/* Scrollbar personalizado horizontal */
.circuit-diagram::-webkit-scrollbar { height: 10px; }
.circuit-diagram::-webkit-scrollbar-track { background: #0f172a; border-radius: 8px; }
.circuit-diagram::-webkit-scrollbar-thumb { background: #334155; border-radius: 8px; border: 2px solid #0f172a; }
.circuit-diagram::-webkit-scrollbar-thumb:hover { background: #38bdf8; cursor: pointer; }

/* --- ESTILOS DEL PANEL DE RAYOS X --- */
.xray-card {
  background: rgba(6, 78, 59, 0.2); /* Un leve tinte verde terminal */
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.math-display {
  background-color: #022c22;
  border: 1px solid #047857;
  padding: 15px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  overflow-x: auto;
  box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
}

.math-prefix {
  color: #34d399;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-weight: bold;
  font-size: 1.4rem;
  margin-right: 10px;
}

.dirac-equation {
  color: #a7f3d0;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 1.4rem;
  letter-spacing: 1px;
}

</style>