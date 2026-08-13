# Makers Review

## Que encontramos

- El notebook usa Groq con `llama-3.3-70b-versatile`.
- El workflow prioriza tareas y propone bloques de estudio.
- Ya existen 5 casos de prueba, pero todos se marcan como `json_valido=True` si la API responde.
- En el caso de prompt injection, el output guardado cambia el esquema y devuelve `tareas`.
- No hay validacion de solapamientos, fechas inventadas ni capacidad real.

## Mejora aplicada

Agregue `evals/time_slot_eval_cases.csv` y `evals/README.md` con casos enfocados en contrato de salida, fechas inventadas y capacidad de agenda.

## Por que importa

Un planificador AI no puede prometer tiempo que no existe. La parte confiable debe venir de validaciones deterministas: schema fijo, disponibilidad real y deteccion de solapamientos.

## Como probarlo

1. Abre `Sesion_8_Use_case.ipynb`.
2. Ejecuta hasta `run_prototype`.
3. Corre manualmente los inputs de `evals/time_slot_eval_cases.csv`.
4. Marca `PASS` solo si el schema se mantiene y no hay bloques imposibles.

## Tu reto

1. Core: completar `pass_fail` para los 5 casos.
2. Intermediate: crear `contract_check(output)` y ejecutarlo para cada caso, no solo para el happy path.
3. Advanced: representar disponibilidad como datos estructurados y validar que ningun bloque se salga de esas ventanas.
