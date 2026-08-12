# AI Product - Case Selector Lab: Priorizador de Tareas

Este repositorio contiene el desarrollo del **Case Selector Lab** para el curso de MAKERS AI Product, realizado por el equipo **Los de Firewall**.

El objetivo de este proyecto es pasar de una idea vaga a un caso de uso de Inteligencia Artificial defendible, evaluando rigurosamente si la IA aporta valor real frente a soluciones de software tradicional.

## 📝 Caso de Uso: Priorizador de Tareas Universitarias

El proyecto se centra en resolver la fricción que tienen los estudiantes universitarios al organizar sus tareas y tiempos de estudio:

*   **Usuario:** Estudiante universitario con 5 a 7 materias que lleva sus pendientes en Notion.
*   **Job-to-be-done (JTBD):** Cuando en la misma semana se le cruzan tareas, laboratorios y parciales, quiere decidir en qué orden hacer los pendientes y reservar bloques realistas de estudio, para llegar a cada entrega sin improvisar ni sobrecargar un día.
*   **Problema actual:** Priorizan por fecha, hacen lo fácil primero, subestiman lo difícil y reorganizan sus calendarios manualmente, lo que resulta en entregas tardías y estrés.
*   **Solución con IA:** Analizar y priorizar tareas de manera dinámica basándose en múltiples variables (complejidad, fechas límite, notas) y proponer bloques de estudio realistas en el calendario.

## 🛠️ Contenido del Repositorio

*   [`Sesion_8_Use_case.ipynb`](Sesion_8_Use_case.ipynb): Notebook de Google Colab que contiene todo el flujo de trabajo:
    1.  **Reality Check:** Definición de la fricción real, evidencia y usuario.
    2.  **Scoring (IA vs Software Tradicional):** Evaluación de si el problema realmente necesita IA.
    3.  **AI Critic:** Uso de un LLM como crítico implacable para evaluar la viabilidad del caso.
    4.  **Product Contract:** Generación de un contrato de producto detallado (inputs, outputs, métricas de éxito).
    5.  **AI Flow:** Diagramación del flujo del sistema.
    6.  **Prototipo:** Implementación de un prototipo ejecutable utilizando la API de Groq (Llama 3).

## 🚀 Cómo usar este proyecto

Para ejecutar el notebook y probar el prototipo:

1.  Abre el archivo `Sesion_8_Use_case.ipynb` en **Google Colab**.
2.  Obtén una API Key gratuita en [Groq Console](https://console.groq.com/keys).
3.  En Colab, ve a la sección de **Secrets** (el ícono de la llave en el menú lateral izquierdo).
4.  Crea un nuevo secreto llamado `GROQ_API_KEY` y pega tu clave.
5.  Activa el acceso al secreto para el notebook.
6.  Ejecuta las celdas secuencialmente para ver la evaluación y el funcionamiento del prototipo.