<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as THREE from 'three'
import { useQuantumStore } from '../stores/quantumState'

const quantumStore = useQuantumStore()

const container0 = ref<HTMLElement | null>(null)
const container1 = ref<HTMLElement | null>(null)
const container2 = ref<HTMLElement | null>(null)
const container3 = ref<HTMLElement | null>(null)

// Renderers para cada esfera
let renderer0: BlochSphereRenderer | null = null
let renderer1: BlochSphereRenderer | null = null
let renderer2: BlochSphereRenderer | null = null
let renderer3: BlochSphereRenderer | null = null

// Clase para manejar de forma modular el canvas 3D de cada esfera de Bloch
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
    const width = this.container.clientWidth || 140
    const height = this.container.clientHeight || 140

    // 1. Escena y Cámara
    this.scene = new THREE.Scene()
    
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 10)
    this.camera.position.set(1.8, 1.3, 2.2) 
    this.camera.lookAt(0, 0, 0)

    // 2. Renderizador WebGL
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    this.renderer.setSize(width, height)
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    
    this.container.innerHTML = ''
    this.container.appendChild(this.renderer.domElement)

    // 3. Luces
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
    this.scene.add(ambientLight)

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.5)
    dirLight.position.set(3, 4, 3)
    this.scene.add(dirLight)

    // 4. Geometría de la Esfera
    const sphereGeo = new THREE.SphereGeometry(1, 20, 20)
    const sphereMat = new THREE.MeshBasicMaterial({ 
      color: 0x38bdf8, 
      transparent: true, 
      opacity: 0.07, 
      wireframe: true 
    })
    const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat)
    this.scene.add(sphereMesh)

    // Ejes internos (Bloch original)
    // Eje X (Horizontal, Rojo)
    this.createAxis(new THREE.Vector3(-1.2, 0, 0), new THREE.Vector3(1.2, 0, 0), 0xef4444)
    // Eje Y (Profundidad, Azul)
    this.createAxis(new THREE.Vector3(0, 0, -1.2), new THREE.Vector3(0, 0, 1.2), 0x3b82f6)
    // Eje Z (Vertical, Verde)
    this.createAxis(new THREE.Vector3(0, -1.2, 0), new THREE.Vector3(0, 1.2, 0), 0x22c55e)

    // Círculos de referencia (Ecuador y meridianos principales)
    const ringGeo = new THREE.RingGeometry(0.99, 1.01, 32)
    const ringMat = new THREE.MeshBasicMaterial({ color: 0x475569, side: THREE.DoubleSide, transparent: true, opacity: 0.3 })
    
    // Ecuador (plano XZ en ThreeJS)
    const equator = new THREE.Mesh(ringGeo, ringMat)
    equator.rotation.x = Math.PI / 2
    this.scene.add(equator)
    
    // Meridiano principal 1 (plano XY)
    const meridian1 = new THREE.Mesh(ringGeo, ringMat)
    this.scene.add(meridian1)

    // Meridiano principal 2 (plano YZ)
    const meridian2 = new THREE.Mesh(ringGeo, ringMat)
    meridian2.rotation.y = Math.PI / 2
    this.scene.add(meridian2)

    // Esferas pequeñas representando los polos
    const poleGeo = new THREE.SphereGeometry(0.045, 8, 8)
    const poleMat0 = new THREE.MeshBasicMaterial({ color: 0x22c55e }) // Polo Norte |0⟩ (Verde)
    const poleMat1 = new THREE.MeshBasicMaterial({ color: 0xef4444 }) // Polo Sur |1⟩ (Rojo)
    
    const northPole = new THREE.Mesh(poleGeo, poleMat0)
    northPole.position.set(0, 1, 0)
    this.scene.add(northPole)
    
    const southPole = new THREE.Mesh(poleGeo, poleMat1)
    southPole.position.set(0, -1, 0)
    this.scene.add(southPole)

    // 5. Flecha de Estado (Vector de Bloch)
    const origin = new THREE.Vector3(0, 0, 0)
    const arrowDir = new THREE.Vector3(0, 1, 0)
    
    this.stateArrow = new THREE.ArrowHelper(arrowDir, origin, 1.0, this.color, 0.2, 0.08)
    this.scene.add(this.stateArrow)

    // Bucle de animación
    const animate = () => {
      if (this.isDestroyed) return
      this.animationId = requestAnimationFrame(animate)
      this.scene.rotation.y += 0.003
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
    // Mapeo Bloch -> Three.js
    const dir = new THREE.Vector3(x_bloch, z_bloch, y_bloch)
    const length = dir.length()
    
    if (length > 0.05) {
      this.stateArrow.setDirection(dir.clone().normalize())
      this.stateArrow.setLength(length, Math.min(0.2, length * 0.2), Math.min(0.08, length * 0.08))
      this.stateArrow.visible = true
    } else {
      // Ocultamos si es un estado totalmente entrelazado (mezclado)
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

// Formateadores para la UI
const formatCoord = (val: number) => {
  return val >= 0 ? `+${val.toFixed(2)}` : val.toFixed(2)
}

const formatPurity = (purity: number) => {
  return `${(purity * 100).toFixed(0)}%`
}

const getStatusLabel = (purity: number) => {
  if (purity > 0.95) return 'Puro'
  if (purity < 0.15) return 'Entrelazado'
  return 'Mixto'
}

const getStatusClass = (purity: number) => {
  if (purity > 0.95) return 'status-pure'
  if (purity < 0.15) return 'status-entangled'
  return 'status-mixed'
}

// Relación de cambios en los 4 qubits
watch(
  () => [quantumStore.qubit0, quantumStore.qubit1, quantumStore.qubit2, quantumStore.qubit3] as const,
  ([newQ0, newQ1, newQ2, newQ3]) => {
    if (renderer0) renderer0.updateVector(newQ0.x, newQ0.y, newQ0.z)
    if (renderer1) renderer1.updateVector(newQ1.x, newQ1.y, newQ1.z)
    if (renderer2) renderer2.updateVector(newQ2.x, newQ2.y, newQ2.z)
    if (renderer3) renderer3.updateVector(newQ3.x, newQ3.y, newQ3.z)
  },
  { deep: true }
)

const handleResize = () => {
  if (renderer0) renderer0.resize()
  if (renderer1) renderer1.resize()
  if (renderer2) renderer2.resize()
  if (renderer3) renderer3.resize()
}

let resizeObserver: ResizeObserver

onMounted(async () => {
  await nextTick()
  
  if (container0.value) {
    renderer0 = new BlochSphereRenderer(container0.value, 0xa855f7) // Q0 Púrpura
    renderer0.updateVector(quantumStore.qubit0.x, quantumStore.qubit0.y, quantumStore.qubit0.z)
  }
  if (container1.value) {
    renderer1 = new BlochSphereRenderer(container1.value, 0x06b6d4) // Q1 Celeste
    renderer1.updateVector(quantumStore.qubit1.x, quantumStore.qubit1.y, quantumStore.qubit1.z)
  }
  if (container2.value) {
    renderer2 = new BlochSphereRenderer(container2.value, 0x10b981) // Q2 Verde Esmeralda
    renderer2.updateVector(quantumStore.qubit2.x, quantumStore.qubit2.y, quantumStore.qubit2.z)
  }
  if (container3.value) {
    renderer3 = new BlochSphereRenderer(container3.value, 0xeab308) // Q3 Amarillo Ámbar
    renderer3.updateVector(quantumStore.qubit3.x, quantumStore.qubit3.y, quantumStore.qubit3.z)
  }

  resizeObserver = new ResizeObserver(() => {
    handleResize()
  })

  if (container0.value) resizeObserver.observe(container0.value)
  if (container1.value) resizeObserver.observe(container1.value)
  if (container2.value) resizeObserver.observe(container2.value)
  if (container3.value) resizeObserver.observe(container3.value)
})

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (renderer0) renderer0.destroy()
  if (renderer1) renderer1.destroy()
  if (renderer2) renderer2.destroy()
  if (renderer3) renderer3.destroy()
})
</script>

<template>
  <div class="bloch-component-wrapper">
    <div class="bloch-component-header">
      <span class="hilbert-badge">Espacio de Hilbert: ℂ¹⁶ (4 Qubits)</span>
    </div>
    
    <div class="bloch-spheres-wrapper">
      
      <!-- Esfera Qubit 0 -->
      <div class="qubit-visual-card">
        <div class="qubit-title-row">
          <span class="qubit-badge badge-q0">Q0</span>
          <span class="qubit-title-text">Qubit 0</span>
        </div>
        <div ref="container0" class="canvas-container"></div>
        <div class="qubit-stats">
          <div class="stats-row">
            <span>Vector:</span>
            <span class="math-font">[{{ formatCoord(quantumStore.qubit0.x) }}, {{ formatCoord(quantumStore.qubit0.y) }}, {{ formatCoord(quantumStore.qubit0.z) }}]</span>
          </div>
          <div class="stats-row">
            <span>Coherencia:</span>
            <span class="math-font">{{ formatPurity(quantumStore.qubit0.purity) }}</span>
          </div>
          <div :class="['status-badge', getStatusClass(quantumStore.qubit0.purity)]">
            {{ getStatusLabel(quantumStore.qubit0.purity) }}
          </div>
        </div>
      </div>

      <!-- Esfera Qubit 1 -->
      <div class="qubit-visual-card">
        <div class="qubit-title-row">
          <span class="qubit-badge badge-q1">Q1</span>
          <span class="qubit-title-text">Qubit 1</span>
        </div>
        <div ref="container1" class="canvas-container"></div>
        <div class="qubit-stats">
          <div class="stats-row">
            <span>Vector:</span>
            <span class="math-font">[{{ formatCoord(quantumStore.qubit1.x) }}, {{ formatCoord(quantumStore.qubit1.y) }}, {{ formatCoord(quantumStore.qubit1.z) }}]</span>
          </div>
          <div class="stats-row">
            <span>Coherencia:</span>
            <span class="math-font">{{ formatPurity(quantumStore.qubit1.purity) }}</span>
          </div>
          <div :class="['status-badge', getStatusClass(quantumStore.qubit1.purity)]">
            {{ getStatusLabel(quantumStore.qubit1.purity) }}
          </div>
        </div>
      </div>

      <!-- Esfera Qubit 2 -->
      <div class="qubit-visual-card">
        <div class="qubit-title-row">
          <span class="qubit-badge badge-q2">Q2</span>
          <span class="qubit-title-text">Qubit 2</span>
        </div>
        <div ref="container2" class="canvas-container"></div>
        <div class="qubit-stats">
          <div class="stats-row">
            <span>Vector:</span>
            <span class="math-font">[{{ formatCoord(quantumStore.qubit2.x) }}, {{ formatCoord(quantumStore.qubit2.y) }}, {{ formatCoord(quantumStore.qubit2.z) }}]</span>
          </div>
          <div class="stats-row">
            <span>Coherencia:</span>
            <span class="math-font">{{ formatPurity(quantumStore.qubit2.purity) }}</span>
          </div>
          <div :class="['status-badge', getStatusClass(quantumStore.qubit2.purity)]">
            {{ getStatusLabel(quantumStore.qubit2.purity) }}
          </div>
        </div>
      </div>

      <!-- Esfera Qubit 3 -->
      <div class="qubit-visual-card">
        <div class="qubit-title-row">
          <span class="qubit-badge badge-q3">Q3</span>
          <span class="qubit-title-text">Qubit 3</span>
        </div>
        <div ref="container3" class="canvas-container"></div>
        <div class="qubit-stats">
          <div class="stats-row">
            <span>Vector:</span>
            <span class="math-font">[{{ formatCoord(quantumStore.qubit3.x) }}, {{ formatCoord(quantumStore.qubit3.y) }}, {{ formatCoord(quantumStore.qubit3.z) }}]</span>
          </div>
          <div class="stats-row">
            <span>Coherencia:</span>
            <span class="math-font">{{ formatPurity(quantumStore.qubit3.purity) }}</span>
          </div>
          <div :class="['status-badge', getStatusClass(quantumStore.qubit3.purity)]">
            {{ getStatusLabel(quantumStore.qubit3.purity) }}
          </div>
        </div>
      </div>

    </div>

    <!-- Guía didáctica interactiva -->
    <div class="educational-guide-card">
      <h4 class="guide-title">💡 ¿Cómo leer las Esferas de Bloch del Registro Cuántico?</h4>
      <div class="guide-grid">
        <div class="guide-item">
          <strong>🟢 Polo Norte (|0⟩) / 🔴 Polo Sur (|1⟩):</strong> Estados clásicos de base puros.
        </div>
        <div class="guide-item">
          <strong>🌐 Ecuador:</strong> Estado de **Superposición** pura (las probabilidades clásica de colapsar son 50% / 50%).
        </div>
        <div class="guide-item">
          <strong>⚛️ Flecha que Desaparece:</strong> Cuando aplicas **CNOT**, los qubits se entrelazan y pierden su coherencia individual (su estado no se puede representar de forma aislada). La pureza/coherencia baja y la flecha se encoge al centro.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.bloch-component-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bloch-spheres-wrapper {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  width: 100%;
}

@media (max-width: 480px) {
  .bloch-spheres-wrapper {
    grid-template-columns: 1fr;
  }
}

.qubit-visual-card {
  background: rgba(30, 41, 59, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.qubit-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  padding-bottom: 5px;
  margin-bottom: 5px;
}

.qubit-badge {
  font-size: 0.7rem;
  font-weight: bold;
  padding: 1px 5px;
  border-radius: 4px;
  color: white;
}

.badge-q0 { background-color: #a855f7; }
.badge-q1 { background-color: #06b6d4; }
.badge-q2 { background-color: #10b981; }
.badge-q3 { background-color: #eab308; }

.qubit-title-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: #e2e8f0;
}

.canvas-container {
  width: 100%;
  height: 140px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  position: relative;
}

.qubit-stats {
  width: 100%;
  margin-top: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.02);
  padding-bottom: 1px;
}

.math-font {
  color: #cbd5e1;
  font-weight: 600;
}

.status-badge {
  display: block;
  width: 100%;
  padding: 2px;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 700;
  text-align: center;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-pure {
  background-color: rgba(34, 197, 94, 0.1);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.status-mixed {
  background-color: rgba(245, 158, 11, 0.1);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.2);
}

.status-entangled {
  background-color: rgba(139, 92, 246, 0.1);
  color: #c084fc;
  border: 1px solid rgba(139, 92, 246, 0.2);
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.1);
}

.educational-guide-card {
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 12px;
  padding: 10px;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.3);
}

.guide-title {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 0.85rem;
  color: #38bdf8;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid rgba(56, 189, 248, 0.1);
  padding-bottom: 5px;
}

.guide-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.guide-item {
  font-size: 0.74rem;
  line-height: 1.3;
  color: #94a3b8;
}

.guide-item strong {
  color: #e2e8f0;
}

.bloch-component-header {
  display: flex;
  justify-content: flex-end;
  width: 100%;
}

.hilbert-badge {
  background: rgba(15, 23, 42, 0.7);
  padding: 3px 8px;
  border-radius: 6px;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.68rem;
  border: 1px solid rgba(56, 189, 248, 0.2);
  box-shadow: 0 0 6px rgba(56, 189, 248, 0.05);
}
</style>