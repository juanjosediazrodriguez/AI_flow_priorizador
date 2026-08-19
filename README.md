# AI Flow Priorizador: Case Selector Lab

> Una evaluación rigurosa del valor real de la IA en la priorización de tareas universitarias

**Curso:** MAKERS AI Product  
**Equipo:** Los de Firewall  
**Integrantes:** Jeronimo Campuzano, Juan Jose Diaz, Laura Andrea Castrillon

---

## 📋 Propósito del Proyecto

Este repositorio documenta el desarrollo de un **Case Selector Lab** que pasa de una idea vaga a un caso de uso defendible de Inteligencia Artificial. A través de un análisis riguroso, evaluamos si la IA realmente aporta valor frente a soluciones de software tradicional, aplicando un framework estructurado:

```
Reality Check → Scoring → AI Critic → Product Contract → AI Flow → Prototipo
```

---

## 🎯 Caso de Uso: Priorizador de Tareas Universitarias

### El Problema

Los estudiantes universitarios con 5 a 7 materias enfrentan una fricción significativa al organizar sus tareas:

- **Síntoma:** Cuando se cruzan tareas, laboratorios y parciales en la misma semana, no saben en qué orden priorizarlos
- **Comportamiento actual:** Priorizan por fecha límite, hacen lo fácil primero, subestiman lo difícil, reorganizan calendarios manualmente
- **Consecuencia:** Entregas tardías, estrés, improvisación

### Job-to-be-Done (JTBD)

> Cuando en la misma semana se me cruzan tareas, laboratorios y parciales, **quiero decidir en qué orden hacer los pendientes y reservar bloques realistas de estudio**, para llegar a cada entrega sin improvisar ni sobrecargar un día.

### La Solución: Priorizador Inteligente

Un sistema basado en IA que:

- **Analiza** tareas con múltiples variables: complejidad estimada, fechas límite, dependencias, notas previas
- **Prioriza dinámicamente** más allá de la fecha límite
- **Propone bloques de estudio realistas** en el calendario del estudiante
- **Ofrece alternativas** cuando hay conflictos de tiempo

---

## 📊 Estructura del Flujo

```
Reality Check (Fricción real)
    ↓
Scoring (IA vs Software Tradicional)
    ↓
AI Critic (¿Es viable? LLM como evaluador)
    ↓
Product Contract (Especificación rigurosa)
    ↓
AI Flow (Diagrama del sistema)
    ↓
Prototipo Ejecutable (API Groq + Llama 3)
```

---

## 🛠️ Contenido del Repositorio

### Archivo Principal: `Sesion_8_Use_case.ipynb`

El notebook de Google Colab contiene:

1. **Reality Check**  
   Definición rigurosa de la fricción, evidencia del problema y caracterización del usuario

2. **Scoring**  
   Matriz de evaluación IA vs. soluciones tradicionales (interfaz manual, simple app, IA)

3. **AI Critic**  
   Uso de un LLM como crítico para validar la viabilidad del caso de uso

4. **Product Contract**  
   Especificación detallada del producto:
   - Inputs esperados
   - Outputs esperados
   - Métricas de éxito

5. **AI Flow**  
   Diagramación del sistema y flujo de datos

6. **Prototipo**  
   Implementación ejecutable utilizando la API de Groq con Llama 3

---

## 🚀 Cómo Usar Este Proyecto

### Requisitos Previos

- Cuenta en Google Colab (gratuita)
- API Key de Groq (gratuita en [Groq Console](https://console.groq.com/keys))

### Pasos

#### 1️⃣ Abre el notebook en Colab

- Accede a [Google Colab](https://colab.research.google.com/)
- Sube o abre `Sesion_8_Use_case.ipynb`

#### 2️⃣ Obtén tu API Key de Groq

- Registrate en [Groq Console](https://console.groq.com/keys)
- Genera una nueva API Key (el plan gratuito es suficiente)

#### 3️⃣ Configura el secreto en Colab

- En el menú lateral de Colab, busca el ícono de **Secretos** (🔑)
- Crea un nuevo secreto llamado `GROQ_API_KEY`
- Pega tu clave de Groq
- Marca la opción para que el notebook acceda al secreto

#### 4️⃣ Ejecuta el notebook

- Ejecuta las celdas secuencialmente desde la parte superior
- Sigue los comentarios y explicaciones en cada sección
- Interactúa con el prototipo en la última sección

---

## 💡 Qué Aprenderás

Este proyecto ilustra:

- ✅ Cómo **validar si un caso de uso realmente necesita IA** (no todo problema necesita ML)
- ✅ **Estructura de un producto de IA defendible** (inputs, outputs, métricas)
- ✅ **Uso de LLMs como herramienta de evaluación crítica** (AI Critic)
- ✅ **Prototipado rápido** con APIs modernas (Groq, LLaMA 3)
- ✅ **Integración de IA** en flujos reales de estudiantes

---

## 🔧 Tecnologías Utilizadas

- **LLM:** Groq API (Llama 3.1 70B)
- **Entorno:** Google Colab (Python)
- **Librerías:**
  - `groq` (cliente oficial)
  - `json` (procesamiento de respuestas)

---

## 📈 Resultados Esperados

El prototipo demuestra que:

1. **La IA agrega valor** en casos complejos de múltiples variables (vs. simple ordenamiento por fecha)
2. **El modelo entiende contexto** (complejidad, dependencias, horarios disponibles)
3. **Propuestas realistas** considerando capacidad cognitiva del estudiante
4. **Mejor UX** que gestión manual o aplicaciones simples

---

