# Evals del priorizador

El riesgo principal del proyecto no es que el modelo falle en escribir JSON. El riesgo es que invente fechas, cree bloques imposibles o cambie el esquema.

## Como usarlos

1. Ejecuta `Sesion_8_Use_case.ipynb` hasta definir `run_prototype`.
2. Prueba cada input de `time_slot_eval_cases.csv`.
3. Verifica tres cosas:
   - el output tiene solo `prioridad`, `razon`, `bloques_estudio`;
   - no inventa disponibilidad ni fechas;
   - si no hay espacio suficiente, pide confirmacion o marca imposibilidad.

## Por que el esquema esta congelado

`output_fields` lo genera un LLM en la Parte 4, asi que cambia en cada corrida.
Con el mismo prompt y `temperature=0` observamos cuatro esquemas distintos:
`{prioridad, razon, bloque_de_estudio}`, `{prioridad, bloques_estudio}`,
`{task_priority, estimated_hours, proposed_slots}` y `{prioridad, razon, bloques}`.

No se puede escribir un validador determinista contra un esquema que se mueve.
Por eso el modelo **propone** el contrato pero el codigo lo **fija**
(`OUTPUT_SCHEMA_FIJO`). Esa es la frontera del producto.

## Fechas relativas: el fallo mas caro

`happy_path` fallaba porque el input decia "hoy lunes" y "manana". El modelo no
sabe que dia es hoy, asi que respondio con fechas de 2024. Al pasar fechas
absolutas (`2026-08-26`), la misma llamada devolvio los dias correctos.

El arreglo no fue mejorar el prompt: fue darle el dato que faltaba.

## Siguiente validacion sugerida

`detect_overlaps(events, proposed_blocks)`: comparar los bloques propuestos
contra los eventos que YA existen en Google Calendar (via `_scripts/gcal`),
no solo contra la disponibilidad declarada, y exigir confirmacion humana
antes de crear nada.
