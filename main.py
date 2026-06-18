from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import math

# --- IMPORTACIONES DE IBM ---
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from pydantic import BaseModel
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

app = FastAPI(title="Qosmos Quantum Engine (4 Qubits)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. DEFINICIÓN DEL MUNDO CUÁNTICO (4 Qubits) ---
ket_0 = np.array([[1], [0]], dtype=complex)
ket_1 = np.array([[0], [1]], dtype=complex)

I_gate = np.array([[1, 0], [0, 1]], dtype=complex)
H_gate = (1 / np.sqrt(2)) * np.array([[1,  1],
                                      [1, -1]], dtype=complex)
X_gate = np.array([[0, 1],
                   [1, 0]], dtype=complex)
Y_gate = np.array([[0, -1j],
                   [1j, 0]], dtype=complex)
Z_gate = np.array([[1, 0],
                   [0, -1]], dtype=complex)

# El estado base para 4 qubits: |0000>
estado_base_4q = np.kron(np.kron(np.kron(ket_0, ket_0), ket_0), ket_0)
estado_actual = np.copy(estado_base_4q)

# --- 2. LÓGICA FÍSICO-MATEMÁTICA ---
def obtener_operador_un_qubit(gate_mat, target, N=4):
    I_op = np.identity(2, dtype=complex)
    op = 1
    for k in range(N):
        current = gate_mat if k == target else I_op
        op = np.kron(op, current) if not isinstance(op, int) else current
    return op

def obtener_operador_cnot(control, target, N=4):
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)
    P1 = np.array([[0, 0], [0, 1]], dtype=complex)
    I_op = np.identity(2, dtype=complex)
    X_op = np.array([[0, 1], [1, 0]], dtype=complex)
    
    # Término 0: si el control es 0, el target no cambia (Identidad)
    term0 = 1
    for k in range(N):
        current = P0 if k == control else (I_op if k == target else I_op)
        term0 = np.kron(term0, current) if not isinstance(term0, int) else current
        
    # Término 1: si el control es 1, el target aplica X (NOT)
    term1 = 1
    for k in range(N):
        current = P1 if k == control else (X_op if k == target else I_op)
        term1 = np.kron(term1, current) if not isinstance(term1, int) else current
        
    return term0 + term1

def calcular_bloch_qubit(estado, i, N=4):
    X_op = np.array([[0, 1], [1, 0]], dtype=complex)
    Y_op = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z_op = np.array([[1, 0], [0, -1]], dtype=complex)
    I_op = np.identity(2, dtype=complex)
    
    def construir_operador_sistema(op_local):
        op = 1
        for k in range(N):
            current = op_local if k == i else I_op
            op = np.kron(op, current) if not isinstance(op, int) else current
        return op
        
    op_X = construir_operador_sistema(X_op)
    op_Y = construir_operador_sistema(Y_op)
    op_Z = construir_operador_sistema(Z_op)
    
    x = np.dot(estado.conj().T, np.dot(op_X, estado))[0][0].real
    y = np.dot(estado.conj().T, np.dot(op_Y, estado))[0][0].real
    z = np.dot(estado.conj().T, np.dot(op_Z, estado))[0][0].real
    
    purity = np.sqrt(x**2 + y**2 + z**2)
    
    return {
        "x": round(float(x), 4),
        "y": round(float(y), 4),
        "z": round(float(z), 4),
        "purity": round(float(purity), 4)
    }

def calcular_vectores_bloch(estado):
    return {
        "q0": calcular_bloch_qubit(estado, 0, N=4),
        "q1": calcular_bloch_qubit(estado, 1, N=4),
        "q2": calcular_bloch_qubit(estado, 2, N=4),
        "q3": calcular_bloch_qubit(estado, 3, N=4)
    }

def vector_a_dirac(estado):
    terminos = []
    for i in range(16):
        amp = estado[i][0]
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
            
            binary_state = f"{i:04b}"
            terminos.append(f"{cadena}|{binary_state}⟩")
            
    ecuacion = " + ".join(terminos)
    return ecuacion.replace("+ -", "- ")

# --- 3. ENDPOINTS DE LA API ---
@app.get("/")
def read_root():
    return {"status": "Motor Cuántico Qosmos (4 Qubits) en línea"}

@app.get("/api/reset")
def reset_qubit():
    global estado_actual
    estado_actual = np.copy(estado_base_4q)
    return {"status": "Sistema reiniciado a |0000>"}

@app.get("/api/gate/{gate_name}")
def apply_gate(gate_name: str, target: int = 0, control: int = 1):
    global estado_actual
    
    if target < 0 or target >= 4 or control < 0 or control >= 4:
        return {"error": "Índice de qubit fuera de rango (debe ser 0, 1, 2 o 3)"}
        
    if gate_name == "CNOT" and control == target:
        return {"error": "El qubit de control y el qubit objetivo no pueden ser el mismo"}

    # Aplicar operador adecuado
    if gate_name == "H":
        operacion = obtener_operador_un_qubit(H_gate, target, N=4)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "X":
        operacion = obtener_operador_un_qubit(X_gate, target, N=4)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "Y":
        operacion = obtener_operador_un_qubit(Y_gate, target, N=4)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "Z":
        operacion = obtener_operador_un_qubit(Z_gate, target, N=4)
        estado_actual = np.dot(operacion, estado_actual)
    elif gate_name == "CNOT":
        operacion = obtener_operador_cnot(control, target, N=4)
        estado_actual = np.dot(operacion, estado_actual)
    else:
        return {"error": f"Compuerta {gate_name} no implementada"}
        
    # Calcular probabilidades de los 16 estados posibles
    probabilidades = {}
    for i in range(16):
        prob = np.abs(estado_actual[i][0])**2 * 100
        probabilidades[f"{i:04b}"] = round(prob, 2)
        
    bloch_data = calcular_vectores_bloch(estado_actual)
    
    return {
        "estado_aplicado": gate_name,
        "probabilidades": probabilidades,
        "bloch": bloch_data,
        "dirac": vector_a_dirac(estado_actual)
    }

@app.get("/api/measure")
def measure_system():
    global estado_actual
    
    # 1. Calculamos las probabilidades actuales
    lista_probs = []
    for i in range(16):
        lista_probs.append(np.abs(estado_actual[i][0])**2)
        
    lista_probs = np.array(lista_probs)
    sum_probs = np.sum(lista_probs)
    if sum_probs > 0:
        lista_probs = lista_probs / sum_probs
    else:
        lista_probs = np.zeros(16)
        lista_probs[0] = 1.0
        
    # 2. Simulamos el colapso usando los pesos cuánticos
    estados_posibles = [f"{i:04b}" for i in range(16)]
    resultado = np.random.choice(estados_posibles, p=lista_probs)
    
    # 3. Forzamos el colapso irreversible en la memoria
    estado_actual = np.zeros((16, 1), dtype=complex)
    idx_colapso = int(resultado, 2)
    estado_actual[idx_colapso][0] = 1.0
    
    # Recalculamos probabilidades colapsadas (una al 100%, el resto 0%)
    probabilidades = {}
    for i in range(16):
        probabilidades[f"{i:04b}"] = 100.0 if i == idx_colapso else 0.0
        
    bloch_data = calcular_vectores_bloch(estado_actual)
    
    return {
        "resultado_medicion": resultado,
        "probabilidades": probabilidades,
        "bloch": bloch_data,
        "dirac": vector_a_dirac(estado_actual)
    }

class GateOperation(BaseModel):
    gate: str
    target: int
    control: int | None = None

class CircuitoData(BaseModel):
    gate_history: list[GateOperation]

@app.post("/api/ibm-execute")
async def ejecutar_en_ibm(data: CircuitoData):
    try:
        # 1. Autenticación
        service = QiskitRuntimeService(
            channel="ibm_quantum_platform", 
            token="TepOJrAZaz-aN-Lhpn6yWC5NOKtvP3pEz8PiJhvmZCK9",
            instance="crn:v1:bluemix:public:quantum-computing:us-east:a/9121f4dd89804c189a3036d7045e341c:61e316ff-99fa-43a0-9950-df0867b1b738::"
        )
        
        # 2. Elegimos el procesador físico
        backend = service.least_busy(simulator=False, operational=True)
        print(f"🚀 Ejecutando circuito en hardware real de 4 Qubits: {backend.name}...")
        
        # 3. Construimos el circuito lógico de 4 qubits
        qc = QuantumCircuit(4, 4)
        
        for op in data.gate_history:
            if op.gate == 'H':
                qc.h(op.target)
            elif op.gate == 'X':
                qc.x(op.target)
            elif op.gate == 'Y':
                qc.y(op.target)
            elif op.gate == 'Z':
                qc.z(op.target)
            elif op.gate == 'CNOT':
                if op.control is not None:
                    qc.cx(op.control, op.target)
                
        # 4. Añadimos la medición en los 4 qubits
        qc.measure([0, 1, 2, 3], [0, 1, 2, 3])
        
        # 5. Compilamos el circuito para adaptarlo a la arquitectura física
        pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
        isa_circuit = pm.run(qc)
        
        # 6. Enviamos el trabajo físico usando el circuito transpilado (isa_circuit)
        sampler = SamplerV2(backend)
        job = sampler.run([isa_circuit], shots=1024)
        
        # Esperamos los resultados
        result = job.result()
        pub_result = result[0]
        conteos = pub_result.data.c.get_counts()
        
        return {
            "status": "Éxito",
            "mensaje": f"Ejecutado físicamente en {backend.name}",
            "resultados_raw": conteos
        }
        
    except Exception as e:
        return {"status": "Error", "mensaje": str(e)}