<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as THREE from 'three'
import { useQuantumStore } from '../stores/quantumState'

const quantumStore = useQuantumStore()

const container = ref<HTMLElement | null>(null)

// Variables globales de Three.js
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let animationId: number
let stateArrow: THREE.ArrowHelper

// Función para mover la flecha
function updateVectorPosition(theta: number, phi: number) {
  const x = Math.sin(theta) * Math.cos(phi)
  const y = Math.cos(theta) 
  const z = Math.sin(theta) * Math.sin(phi)

  const newDirection = new THREE.Vector3(x, y, z).normalize()
  if (stateArrow) {
    stateArrow.setDirection(newDirection)
  }
}

// El vigía que detecta cuándo Python envía nuevos ángulos
watch(
  () => [quantumStore.theta, quantumStore.phi] as const,
  ([newTheta, newPhi]) => {
    updateVectorPosition(newTheta, newPhi)
  }
)

const initThreeJS = () => {
  if (!container.value) return

  // 1. Escena y Cámara
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, container.value.clientWidth / container.value.clientHeight, 0.1, 100)
  camera.position.set(2, 1.5, 2.5) 
  camera.lookAt(0, 0, 0)

  // 2. Renderizador 
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setSize(container.value.clientWidth, container.value.clientHeight)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.value.appendChild(renderer.domElement)

  // 3. Geometría de la Esfera 
  const geometry = new THREE.SphereGeometry(1, 32, 32)
  const material = new THREE.MeshBasicMaterial({ 
    color: 0x38bdf8, 
    transparent: true, 
    opacity: 0.15, 
    wireframe: true 
  })
  const sphere = new THREE.Mesh(geometry, material)
  scene.add(sphere)

  // 4. Ejes 
  const axesHelper = new THREE.AxesHelper(1.3)
  scene.add(axesHelper)

  // 5. Vector de Estado Base (Apuntando al polo norte)
  const origin = new THREE.Vector3(0, 0, 0)
  const arrowDir = new THREE.Vector3(0, 1, 0) 
  stateArrow = new THREE.ArrowHelper(arrowDir, origin, 1, 0xa855f7, 0.15, 0.1)
  scene.add(stateArrow)

  // Bucle de animación 
  const animate = () => {
    animationId = requestAnimationFrame(animate)
    scene.rotation.y += 0.002
    renderer.render(scene, camera)
  }
  animate()
}

const handleResize = () => {
  if (!container.value || !camera || !renderer) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

let resizeObserver: ResizeObserver

onMounted(async () => {
  await nextTick() 
  initThreeJS()
  
  resizeObserver = new ResizeObserver(() => {
    handleResize()
  })
  
  if (container.value) {
    resizeObserver.observe(container.value)
  }
})

onBeforeUnmount(() => {
  if (resizeObserver && container.value) {
    resizeObserver.disconnect()
  }
  cancelAnimationFrame(animationId)
  if (renderer) renderer.dispose()
})
</script>

<template>
  <div ref="container" class="canvas-container"></div>
</template>

<style scoped>
.canvas-container {
  width: 100%;
  height: 100%;
  min-height: 450px;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}
</style>