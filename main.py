from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import math

app = FastAPI(title="Qosmos Quantum Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DEFINICIÓN DEL MUNDO CUÁNTICO (2 Qubits) ---
ket_0 = np.array([[1], [0]], dtype=complex)
ket_1 = np.array([[0], [1]], dtype=complex)

I_gate = np.array([[1, 0], [0, 1]], dtype=complex)
H_gate = (1 / np.sqrt(2)) * np.array([[1,  1],
                                      [1, -1]], dtype=complex)
X_gate = np.array([[0, 1],
                   [1, 0]], dtype=complex)
# ... (debajo de X_gate) ...
Y_gate = np.array([[0, -1j],
                   [1j, 0]], dtype=complex)

Z_gate = np.array([[1, 0],
                   [0, -1]], dtype=complex)

CNOT_gate = np.array([
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 1],
    [0, 0, 1, 0]
], dtype=complex)

estado_base_2q = np.kron(ket_0, ket_0)
estado_actual = np.copy(estado_base_2q)

# --- 2. LÓGICA FÍSICO-MATEMÁTICA ---
def calcular_angulos_bloch(alpha, beta):
    theta = 2 * math.acos(np.clip(abs(alpha), -1.0, 1.0))
    fase_alpha = np.angle(alpha)
    fase_beta = np.angle(beta)
    phi = fase_beta - fase_alpha
    if phi < 0:
        phi += 2 * math.pi
    return theta, phi

def vector_a_dirac(estado):
    terminos = []
    bases = ["|00⟩", "|01⟩", "|10⟩", "|11⟩"]
    
    for i in range(4):
        amp = estado[i][0]
        # Solo mostramos los estados que tienen probabilidad (amplitud > 0)
        if np.abs(amp) > 0.001:
            real = round(amp.real, 3)
            imag = round(amp.imag, 3)
            
            # Formateo inteligente del número complejo
            if imag == 0:
                cadena = f"{real}" if real != 1.0 else ""
                if real == -1.0: cadena = "-"
            elif real == 0:
                cadena = f"{imag}i" if imag != 1.0 else "i"
                if imag == -1.0: cadena = "-i"
            else:
                cadena = f"({real} + {imag}i)"
            
            terminos.append(f"{cadena}{bases[i]}")
            
    ecuacion = " + ".join(terminos)
    return ecuacion.replace("+ -", "- ")

# --- 3. ENDPOINTS DE LA API ---
@app.get("/")
def read_root():
    return {"status": "Motor Cuántico Qosmos en línea"}

@app.get("/api/reset")
def reset_qubit():
    global estado_actual
    estado_actual = np.copy(estado_base_2q)
    return {"status": "Sistema reiniciado a |00>"}

@app.get("/api/gate/{gate_name}")
def apply_gate(gate_name: str):
    global estado_actual
    
# 1. Aplicar la compuerta correcta escalando con la Identidad
    if gate_name == "H":
        operacion = np.kron(H_gate, I_gate)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "X":
        operacion = np.kron(X_gate, I_gate)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "Y":
        # Nueva compuerta Pauli-Y
        operacion = np.kron(Y_gate, I_gate)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "Z":
        # Nueva compuerta Pauli-Z
        operacion = np.kron(Z_gate, I_gate)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "CNOT":
        estado_actual = np.dot(CNOT_gate, estado_actual)
    else:
        return {"error": f"Compuerta {gate_name} no implementada"}
    
    # 2. Calcular probabilidades de los 4 estados posibles
    prob_00 = np.abs(estado_actual[0][0])**2 * 100
    prob_01 = np.abs(estado_actual[1][0])**2 * 100
    prob_10 = np.abs(estado_actual[2][0])**2 * 100
    prob_11 = np.abs(estado_actual[3][0])**2 * 100
    
    # 3. APROXIMACIÓN PARA LA ESFERA (Qubit 0)
    alpha_0 = estado_actual[0][0] + estado_actual[1][0]
    beta_0 = estado_actual[2][0] + estado_actual[3][0]
    
    # Normalizamos el vector resultante
    norm = np.sqrt(np.abs(alpha_0)**2 + np.abs(beta_0)**2)
    if norm > 0:
        alpha_0 = alpha_0 / norm
        beta_0 = beta_0 / norm
    else:
        alpha_0, beta_0 = 1.0, 0.0
        
    # 4. Calculamos las coordenadas (theta y phi)
    theta, phi = calcular_angulos_bloch(alpha_0, beta_0)
    
    # 5. Enviamos todo el paquete al frontend
    return {
        "estado_aplicado": gate_name,
        "probabilidades": {
            "00": round(prob_00, 2),
            "01": round(prob_01, 2),
            "10": round(prob_10, 2),
            "11": round(prob_11, 2)
        },
        "theta": theta,
        "phi": phi,
        "dirac": vector_a_dirac(estado_actual)
    }

@app.get("/api/measure")
def measure_system():
    global estado_actual
    
    # 1. Calculamos las probabilidades actuales del sistema
    prob_00 = np.abs(estado_actual[0][0])**2
    prob_01 = np.abs(estado_actual[1][0])**2
    prob_10 = np.abs(estado_actual[2][0])**2
    prob_11 = np.abs(estado_actual[3][0])**2
    
    lista_probs = [prob_00, prob_01, prob_10, prob_11]
    
    # Aseguramos que sumen exactamente 1.0 para evitar errores flotantes en NumPy
    lista_probs = np.array(lista_probs) / np.sum(lista_probs)
    
    # 2. Simulamos el colapso de la función de onda usando los pesos cuánticos
    estados_posibles = ["00", "01", "10", "11"]
    resultado = np.random.choice(estados_posibles, p=lista_probs)
    
    # 3. Forzamos el colapso irreversible del estado físico en la memoria
    if resultado == "00":
        estado_actual = np.array([[1], [0], [0], [0]], dtype=complex)
    elif resultado == "01":
        estado_actual = np.array([[0], [1], [0], [0]], dtype=complex)
    elif resultado == "10":
        estado_actual = np.array([[0], [0], [1], [0]], dtype=complex)
    elif resultado == "11":
        estado_actual = np.array([[0], [0], [0], [1]], dtype=complex)
        
    # 4. Recalculamos los ángulos para la Esfera de Bloch del estado colapsado
    alpha_0 = estado_actual[0][0] + estado_actual[1][0]
    beta_0 = estado_actual[2][0] + estado_actual[3][0]
    
    norm = np.sqrt(np.abs(alpha_0)**2 + np.abs(beta_0)**2)
    if norm > 0:
        alpha_0, beta_0 = alpha_0 / norm, beta_0 / norm
    
    theta, phi = calcular_angulos_bloch(alpha_0, beta_0)
    
    # 5. Devolvemos el estado colapsado (una barra al 100%, el resto al 0%)
    return {
        "resultado_medicion": resultado,
        "probabilidades": {
            "00": 100.0 if resultado == "00" else 0.0,
            "01": 100.0 if resultado == "01" else 0.0,
            "10": 100.0 if resultado == "10" else 0.0,
            "11": 100.0 if resultado == "11" else 0.0,
        },
        "theta": theta,
        "phi": phi,
        "dirac": vector_a_dirac(estado_actual)
    }