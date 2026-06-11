import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useQuantumStore = defineStore('quantum', () => {
  // Probabilidades de los 4 estados posibles para 2 Qubits
  const isMeasured = ref<boolean>(false)
  const prob00 = ref<number>(100)
  const prob01 = ref<number>(0)
  const prob10 = ref<number>(0)
  const prob11 = ref<number>(0)
  const theta = ref<number>(0)
  const phi = ref<number>(0)
  const diracNotation = ref<string>('|00⟩')

  const gateHistory = ref<string[]>([])

  // Función para actualizar las 4 barras
  function updateProbabilities(p00: number, p01: number, p10: number, p11: number) {
    prob00.value = p00
    prob01.value = p01
    prob10.value = p10
    prob11.value = p11
  }

  

  async function applyGate(gateName: string) {
    async function applyGate(gateName: string) {
    if (isMeasured.value) return // Si ya se midió, ignoramos los clics
    // ... (el resto del try/catch que ya tienes) ...
  }
    try {
      const response = await fetch(`http://127.0.0.1:8000/api/gate/${gateName}`)
      if (!response.ok) throw new Error(`Error en compuerta ${gateName}`)
      
      const data = await response.json()
      
      if (data.error) {
        console.warn(data.error)
        return
      }

      gateHistory.value.push(gateName)
      // Ahora leemos el nuevo formato del JSON enviado por Python
      updateProbabilities(
        data.probabilidades["00"], 
        data.probabilidades["01"], 
        data.probabilidades["10"], 
        data.probabilidades["11"]
      )
      theta.value = data.theta
      phi.value = data.phi
      // Justo debajo de donde actualizas theta y phi, añade:
      diracNotation.value = data.dirac
      
    } catch (error) {
      console.error("Fallo detallado de conexión:", error)
    }
  }

  async function resetQubit() {
    try {
      await fetch('http://127.0.0.1:8000/api/reset')
      prob00.value = 100
      prob01.value = 0
      prob10.value = 0
// ... (código existente) ...
      prob11.value = 0
      gateHistory.value = []
      isMeasured.value = false // ¡Desbloqueamos el sistema!
      theta.value = 0
      phi.value = 0
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
      
      // 1. Bloqueamos el sistema
      isMeasured.value = true 
      
      // 2. Registramos la medición en el historial (¡Solo una vez!)
      gateHistory.value.push(`M (${data.resultado_medicion})`)
      
      // 3. Actualizamos las barras al estado colapsado puro
      updateProbabilities(
        data.probabilidades["00"], 
        data.probabilidades["01"], 
        data.probabilidades["10"], 
        data.probabilidades["11"]
      )
      
      // 4. Actualizamos la Esfera de Bloch
      theta.value = data.theta
      phi.value = data.phi
      // Justo debajo de donde actualizas theta y phi, añade:
      diracNotation.value = data.dirac
      
    } catch (error) {
      console.error("Error en la medición:", error)
    }
}

  // No olvides agregar measureSystem al return del final del archivo:
return { 
    prob00, prob01, prob10, prob11, theta, phi, gateHistory, isMeasured,
    applyGate, resetQubit, measureSystem, diracNotation
  }
})