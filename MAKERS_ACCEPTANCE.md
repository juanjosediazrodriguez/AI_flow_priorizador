# Gates Makers — revisión 2026-09-23

Referencia revisada: integración local de `origin/main` y `origin/develop` en `makers/review`.

| Gate | Estado | Evidencia | Para cerrar |
|---|---|---|---|
| Arquitectura atribuible | NO PASA | No existe arquitectura versionada del producto. | Diagrama + decisiones firmadas por Laura, Jerónimo y Juan José. |
| Uso de IA + evals | PARCIAL | El planner determinista pasa 31/31 pruebas; no hay before/after del agente IA. | Definir exactamente qué decide IA y qué calcula el scheduler. |
| Jailbreak y safety | NO PASA | No hay suite adversarial del agente. | Intentos de alterar calendario, prioridades y restricciones. |
| Mantenibilidad | PARCIAL | Hay tests; `planner.py` y `obsidian.py` superan 300 líneas. | Separar dominio, integraciones y CLI. |
| Producto ejecutable | PARCIAL | Scripts y notebook, sin experiencia de usuario integrada. | CLI o web mínima con crear-plan-replanificar. |
| Git profesional | NO PASA | `develop` compartida y sin `dev/nombre`; avance reciente mayormente documental. | Tres ramas individuales, PR e integración verificable. |

No cuenta como arquitectura un conjunto de instrucciones para agentes; deben documentar el sistema que ejecuta el usuario.
