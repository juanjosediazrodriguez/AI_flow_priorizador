# Evals del priorizador

El riesgo principal del proyecto no es que el modelo falle en escribir JSON. El riesgo es que invente fechas, cree bloques imposibles o cambie el esquema.

## Como usarlos

1. Ejecuta `Sesion_8_Use_case.ipynb` hasta definir `run_prototype`.
2. Prueba cada input de `time_slot_eval_cases.csv`.
3. Verifica tres cosas:
   - el output tiene solo `prioridad`, `razon`, `bloque_de_estudio`;
   - no inventa disponibilidad ni fechas;
   - si no hay espacio suficiente, pide confirmacion o marca imposibilidad.

## Siguiente validacion sugerida

Crear una funcion `validate_schedule_output(output, available_slots)` que rechace bloques fuera de disponibilidad o con solapamientos.
