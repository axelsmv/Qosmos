<script setup lang="ts">
import { ref } from 'vue'

interface SimulationModule {
  id: string
  name: string
  description: string
  route: string
  status: 'active' | 'development'
  icon: string
  tags: string[]
}

const simulations = ref<SimulationModule[]>([
  {
    id: 'sim-4qubits',
    name: 'Simulador de 2 Qubits',
    description: 'Espacio de Hilbert ℂ⁴. Modelación matemática pura, visualización 3D interactiva de la Esfera de Bloch, compuertas cuánticas y entrelazamiento cuántico mediante matrices de 4x4.',
    route: '/simulador-4q',
    status: 'active',
    icon: '🔮',
    tags: ['Superposición', 'Entrelazamiento', 'Esfera 3D']
  },
  {
    id: 'sim-doubleslit',
    name: 'Experimento de Doble Rendija',
    description: 'Visualización fasorial en 2D de la función de onda cuántica como números complejos. Experimenta con la difracción, la interferencia constructiva/destructiva y la aceleración del disparo de electrones.',
    route: '/simulador-rendija',
    status: 'active',
    icon: '🌊',
    tags: ['Función de Onda', 'Fasores', 'Doble Rendija']
  },
  {
    id: 'sim-teleport',
    name: 'Teletransportación Cuántica',
    description: 'Protocolo de transferencia de estados cuánticos a distancia compartiendo un par de qubits entrelazados (Bell) y canales de comunicación clásicos.',
    route: '/simulador-teleport',
    status: 'active',
    icon: '📡',
    tags: ['Feria Científica', 'Entrelazamiento', 'Protocolos']
  },
  {
    id: 'sim-grover',
    name: 'Búsqueda de Grover',
    description: 'Algoritmo de Grover para búsqueda en bases de datos no ordenadas. Demostración interactiva de amplificación de amplitud paso a paso.',
    route: '/simulador-grover',
    status: 'active',
    icon: '🔍',
    tags: ['Feria Científica', 'Amplificación', 'Algoritmo']
  }
])
</script>

<template>
  <div class="home-container">
    <header class="home-header">
      <div class="logo-glow"></div>
      <h1>Qosmos</h1>
      <p class="subtitle">Plataforma de Simulación Cuántica Interactiva</p>
      <div class="divider"></div>
      <p class="description">
        Bienvenido a Qosmos, un entorno de laboratorio virtual para la demostración científica y educativa de la computación cuántica. Desarrollado por la Universidad de Tarapacá para Ingeniería Civil en Informática.
      </p>
    </header>

    <main class="menu-section">
      <h2 class="menu-title">Módulos de Simulación</h2>
      <div class="simulations-grid">
        <div 
          v-for="sim in simulations" 
          :key="sim.id" 
          class="sim-card"
          :class="{ 'card-active': sim.status === 'active', 'card-dev': sim.status === 'development' }"
        >
          <div class="card-icon">{{ sim.icon }}</div>
          <div class="card-content">
            <div class="card-header-row">
              <span class="status-badge" :class="sim.status">
                {{ sim.status === 'active' ? 'Disponible' : 'En desarrollo' }}
              </span>
              <h3>{{ sim.name }}</h3>
            </div>
            <p class="card-desc">{{ sim.description }}</p>
            <div class="card-tags">
              <span v-for="tag in sim.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
            <div class="card-action">
              <router-link 
                v-if="sim.status === 'active'" 
                :to="sim.route" 
                class="btn-enter"
              >
                Iniciar Simulación
              </router-link>
              <button 
                v-else 
                disabled 
                class="btn-disabled"
              >
                Próximamente
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="home-footer">
      <p>© 2026 Qosmos • Universidad de Tarapacá • Ingeniería Civil en Informática</p>
    </footer>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
}

.home-header {
  text-align: center;
  position: relative;
  margin-bottom: 50px;
  padding-top: 20px;
}

.logo-glow {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%);
  width: 180px;
  height: 180px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.15) 0%, rgba(129, 140, 248, 0) 70%);
  z-index: -1;
  pointer-events: none;
}

.home-header h1 {
  font-size: 4rem;
  margin: 0 0 10px 0;
  font-weight: 800;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 30px rgba(56, 189, 248, 0.3));
}

.subtitle {
  font-size: 1.3rem;
  color: #94a3b8;
  margin: 0;
  font-weight: 500;
}

.divider {
  width: 80px;
  height: 4px;
  background: linear-gradient(to right, #38bdf8, #818cf8);
  margin: 25px auto;
  border-radius: 2px;
}

.description {
  max-width: 700px;
  margin: 0 auto;
  color: #64748b;
  font-size: 1.05rem;
  line-height: 1.6;
}

/* Grilla de Módulos */
.menu-section {
  flex-grow: 1;
  margin-bottom: 50px;
}

.menu-title {
  font-size: 1.8rem;
  color: #cbd5e1;
  margin-bottom: 30px;
  font-weight: 600;
  text-align: left;
  border-left: 4px solid #38bdf8;
  padding-left: 15px;
}

.simulations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 30px;
}

.sim-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  padding: 30px;
  display: flex;
  gap: 20px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.sim-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: transparent;
  transition: background 0.3s ease;
}

.card-active::before {
  background: linear-gradient(90deg, #38bdf8, #818cf8);
}

.sim-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.card-active:hover {
  border-color: rgba(56, 189, 248, 0.3);
  box-shadow: 0 12px 40px rgba(56, 189, 248, 0.1);
}

.card-dev {
  opacity: 0.65;
  border-color: rgba(255, 255, 255, 0.04);
}

.card-dev::before {
  background: #475569;
}

.card-dev:hover {
  transform: none;
  box-shadow: none;
  border-color: rgba(255, 255, 255, 0.04);
}

.card-icon {
  font-size: 2.5rem;
  line-height: 1;
}

.card-content {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  flex-grow: 1;
}

.card-header-row {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 12px;
  gap: 6px;
}

.card-content h3 {
  margin: 0;
  font-size: 1.35rem;
  color: #f1f5f9;
  font-weight: 600;
}

.status-badge {
  font-size: 0.75rem;
  padding: 4px 8px;
  border-radius: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.active {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.status-badge.development {
  background: rgba(148, 163, 184, 0.1);
  color: #94a3b8;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.card-desc {
  color: #94a3b8;
  font-size: 0.95rem;
  line-height: 1.5;
  margin: 0 0 20px 0;
  flex-grow: 1;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 25px;
}

.tag {
  font-size: 0.8rem;
  background: rgba(30, 41, 59, 0.8);
  color: #38bdf8;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(56, 189, 248, 0.15);
}

.card-action {
  margin-top: auto;
}

.btn-enter {
  display: inline-block;
  width: 100%;
  text-align: center;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.4);
  padding: 12px 20px;
  border-radius: 10px;
  font-weight: bold;
  font-size: 0.95rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.btn-enter:hover {
  background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
  color: #ffffff;
  border-color: transparent;
  box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3);
  transform: translateY(-1px);
}

.btn-disabled {
  width: 100%;
  background: #1e293b;
  color: #475569;
  border: 1px solid #334155;
  padding: 12px 20px;
  border-radius: 10px;
  font-weight: bold;
  font-size: 0.95rem;
  cursor: not-allowed;
}

/* Footer */
.home-footer {
  text-align: center;
  border-top: 1px solid #1e293b;
  padding-top: 30px;
  margin-top: 50px;
}

.home-footer p {
  color: #475569;
  font-size: 0.85rem;
  margin: 0;
}

@media (max-width: 768px) {
  .sim-card {
    flex-direction: column;
  }
}
</style>
