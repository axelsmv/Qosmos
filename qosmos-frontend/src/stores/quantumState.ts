import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface BlochVector {
  x: number
  y: number
  z: number
  purity: number
}

export interface Operation {
  gate: string
  target: number
  control?: number
}

export interface StateProbability {
  label: string
  prob: number
}

const generateInitialProbabilities = (): StateProbability[] => {
  const list: StateProbability[] = []
  for (let i = 0; i < 4; i++) {
    const label = i.toString(2).padStart(2, '0')
    list.push({ label, prob: i === 0 ? 100 : 0 })
  }
  return list
}

export const useQuantumStore = defineStore('quantum', () => {
  const isMeasured = ref<boolean>(false)
  
  // Tabla de probabilidades (4 estados posibles para 2 qubits)
  const probabilities = ref<StateProbability[]>(generateInitialProbabilities())
  
  // Vectores de Bloch para los 2 Qubits
  const qubit0 = ref<BlochVector>({ x: 0, y: 0, z: 1, purity: 1 })
  const qubit1 = ref<BlochVector>({ x: 0, y: 0, z: 1, purity: 1 })
  
  const diracNotation = ref<string>('|00⟩')
  const gateHistory = ref<Operation[]>([])

  async function applyGate(gateName: string, target: number = 0, control: number = 1) {
    if (isMeasured.value) return
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/gate/${gateName}?target=${target}&control=${control}`)
      if (!response.ok) throw new Error(`Error en compuerta ${gateName}`)
      
      const data = await response.json()
      
      if (data.error) {
        alert(data.error)
        return
      }

      // Añadimos la operación al historial
      gateHistory.value.push({
        gate: gateName,
        target,
        control: gateName === 'CNOT' ? control : undefined
      })

      // Actualizar probabilidades
      for (const state of probabilities.value) {
        state.prob = data.probabilidades[state.label] ?? 0
      }
      
      qubit0.value = data.bloch.q0
      qubit1.value = data.bloch.q1
      diracNotation.value = data.dirac
      
    } catch (error) {
      console.error("Fallo detallado de conexión:", error)
    }
  }

  async function resetQubit() {
    try {
      await fetch('http://127.0.0.1:8000/api/reset')
      probabilities.value = generateInitialProbabilities()
      gateHistory.value = []
      isMeasured.value = false // ¡Desbloqueamos el sistema!
      
      qubit0.value = { x: 0, y: 0, z: 1, purity: 1 }
      qubit1.value = { x: 0, y: 0, z: 1, purity: 1 }
      
      diracNotation.value = '|00⟩'
    } catch (error) {
      console.error("Error al reiniciar:", error)
    }
  }

  async function measureSystem() {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/measure')
      if (!response.ok) throw new Error('Error al medir el sistema')
      
      const data = await response.json()
      
      isMeasured.value = true 
      
      // Registramos la medición en el historial global
      gateHistory.value.push({
        gate: `M (${data.resultado_medicion})`,
        target: -1 // Qubit especial para medición global
      })
      
      // Actualizamos probabilidades
      for (const state of probabilities.value) {
        state.prob = data.probabilidades[state.label] ?? 0
      }
      
      // Actualizamos las esferas de Bloch
      qubit0.value = data.bloch.q0
      qubit1.value = data.bloch.q1
      
      diracNotation.value = data.dirac
      
    } catch (error) {
      console.error("Error en la medición:", error)
    }
  }

  return { 
    probabilities, qubit0, qubit1, gateHistory, isMeasured,
    applyGate, resetQubit, measureSystem, diracNotation
  }
})