# Qosmos - Simulador de Computación Cuántica

Qosmos es una plataforma de simulación cuántica interactiva y full-stack diseñada con fines educativos y de demostración científica para el ámbito académico de la Ingeniería Civil en Informática en la Universidad de Tarapacá. El sistema permite modelar, visualizar y manipular un registro cuántico de 2 Qubits en tiempo real, conectando un motor físico-matemático robusto en el backend con una interfaz de usuario interactiva de alta fidelidad en el frontend.

---

## 1. Arquitectura del Sistema

El simulador está construido bajo una arquitectura desacoplada que separa estrictamente la capa de procesamiento matemático de la capa de presentación:

* Backend (Motor Cuántico): Desarrollado en Python utilizando FastAPI para la exposición de endpoints asíncronos y NumPy para el procesamiento optimizado de álgebra lineal compleja (matrices complejas, productos de Kronecker, multiplicación de tensores y cálculo estocástico).
* Frontend (Panel de Control): Construido con Vue 3 (Composition API) para la reactividad de la interfaz, Pinia para la gestión del estado cuántico global y una visualización geométrica interactiva en 3D para la Esfera de Bloch.

---

## 2. Características Implementadas

Actualmente, el simulador cuenta con las siguientes capacidades lógicas, físicas y visuales completamente integradas:

* Motor de Álgebra Lineal: Implementación matemática pura utilizando números complejos para las rotaciones en el espacio de Hilbert. Incluye las compuertas de un qubit (Hadamard, Pauli-X, Pauli-Y, Pauli-Z) y de dos qubits (CNOT para modelar el entrelazamiento cuántico mediante matrices de 4x4).
* Postulado de la Medición: Implementación de la Regla de Born mediante algoritmos de generación pseudoaleatoria ponderada. Al gatillar la medición, el sistema destruye la superposición de forma irreversible en la memoria del backend, fijando la probabilidad al 100% en un estado.
* Interfaz "Dashboard de Laboratorio": Diseño de tres paneles organizados bajo metodologías de visualización científica, estilo "Glassmorphism" y una partitura de circuito cuántico autogenerada con scrollbars dinámicos.
* Transparencia Matemática: Traducción algorítmica automatizada de la matriz compleja del backend a la Notación de Dirac tradicional (Ejemplo: |psi> = 0.707|00> + 0.707|11>), expuesta en tiempo real en un panel de terminal.

---

## 3. Requisitos e Instalación

### Backend (Python)
1. Instalar las dependencias requeridas:
   pip install fastapi uvicorn numpy

2. Levantar el servidor de desarrollo de la API:
   .\venv\Scripts\activate
   uvicorn main:app --reload
   (El servidor correrá por defecto en http://127.0.0.1:8000)

### Frontend (Vue 3)
1. Instalar los paquetes de Node.js:
   npm install

2. Ejecutar la aplicación en modo local:
   npm run dev

---

## 4. Flujo Metodológico de Demostración Científica

Para evaluar la consistencia del simulador durante una feria o defensa académica, se recomienda seguir el siguiente caso de prueba estandarizado:

1. Estado Base: El sistema inicializa en el polo norte de la esfera de Bloch con una probabilidad del 100% en el estado |00>.
2. Operación de Superposición: Al presionar Hadamard (H), la aguja geométrica viaja al ecuador de la esfera y el panel matemático computa la superposición equilibrada.
3. Entrelazamiento Cuántico: Al aplicar la compuerta CNOT, las barras de probabilidad clásica se dividen exactamente en 50% para |00> y 50% para |11>. El sistema se encuentra en un Estado de Bell.
4. Colapso Irreversible: Al presionar "Medir Sistema", la superposición se rompe de forma estocástica e instantánea. La interfaz congela sus controles y fija una barra al 100%.
5. Reinicio Físico: El botón "Reiniciar Qubit" libera el bloqueo del software y devuelve el vector al estado de vacío inicial.