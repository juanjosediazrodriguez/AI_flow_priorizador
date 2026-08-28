# Makers Review

## Que encontramos

- El notebook usa Groq con `llama-3.3-70b-versatile`.
- El workflow prioriza tareas y propone bloques de estudio.
- Ya existen 5 casos de prueba, pero todos se marcan como `json_valido=True` si la API responde.
- En el caso de prompt injection, el output guardado cambia el esquema y devuelve `tareas`.
- El repo ahora incluye scripts en `_scripts/gcal/` para empezar a conectar agenda real.
- No hay validacion automatizada que compruebe solapamientos, fechas inventadas ni capacidad real antes de usar Google Calendar.

## Mejora aplicada

Integre los cambios nuevos de agenda, elimine `.DS_Store` del tracking y agregue `.DS_Store` al `.gitignore`.

La mejora docente anterior se mantiene: `evals/time_slot_eval_cases.csv` y `evals/README.md` con casos enfocados en contrato de salida, fechas inventadas y capacidad de agenda.

## Por que importa

Un planificador AI no puede prometer tiempo que no existe. La parte confiable debe venir de validaciones deterministas: schema fijo, disponibilidad real y deteccion de solapamientos.

## Como probarlo

1. Abre `Sesion_8_Use_case.ipynb`.
2. Ejecuta hasta `run_prototype`.
3. Corre manualmente los inputs de `evals/time_slot_eval_cases.csv`.
4. Revisa `_scripts/gcal/README.md` antes de intentar operaciones reales de calendario.
5. Marca `PASS` solo si el schema se mantiene y no hay bloques imposibles.

## Tu reto

1. Core: completar `pass_fail` para los 5 casos.
2. Intermediate: crear `contract_check(output)` y ejecutarlo para cada caso, no solo para el happy path.
3. Advanced: antes de crear eventos reales, implementar `detect_overlaps(events, proposed_blocks)` y exigir confirmacion humana.

<!-- MAKERS_REVIEW_2026_08_27_START -->
## Revision docente - 2026-08-27

### Lo que vimos

- Juan Jose Diaz hizo un avance fuerte sobre makers/review: schema congelado, evals PASS y buena explicacion de fechas relativas.
- Jeronimo empezo a ordenar estructura del repo, lo cual es necesario para mantener el proyecto.
- Laura tiene que dejar mas evidencia tecnica individual visible.
- El riesgo principal del producto es proponer horarios incorrectos, ambiguos o solapados.
- La siguiente mejora debe salir del prompt y entrar a validacion deterministica.

### Reto de hoy

Implementen o especifiquen detect_overlaps(events, proposed_blocks):

1. Caso feliz: bloque libre.
2. Caso con solapamiento.
3. Caso con fecha relativa como "manana".
4. Caso con timezone o formato raro.
5. Caso sin disponibilidad suficiente.

### Tarea obligatoria: diagrama de arquitectura

Crear docs/arquitectura.md con un diagrama Mermaid que muestre:

`mermaid
flowchart LR
  Usuario --> SolicitudAgenda
  Calendario --> EventosExistentes
  SolicitudAgenda --> Modelo
  Modelo --> BloquesPropuestos
  EventosExistentes --> ValidadorSolapamientos
  BloquesPropuestos --> ValidadorSolapamientos
  ValidadorSolapamientos --> AgendaSegura
`

Debe quedar claro que el modelo propone, pero el codigo valida fechas, disponibilidad y solapamientos.

### Criterio de aceptacion

No basta con que el agente sugiera una hora. Tiene que demostrar que esa hora no choca con nada.
<!-- MAKERS_REVIEW_2026_08_27_END -->

