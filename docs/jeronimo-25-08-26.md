¿QUÉ CAMBIÓ CODEX?
Congelo el esquema de salida en el codigo (OUTPUT_SCHEMA_FIJO) porque el modelo proponia uno distinto en cada corrida, y agrego las validaciones deterministas: contract_check, validate_schedule_output y detect_overlaps con partir_bloque. Con eso los 5 casos del csv quedaron en PASS. Codex borro archivos inncesarios como eran los .DS_store que son locales y los agrego al gitignore

¿QUÉ RIESGO TÉCNICO ENCONTRÓ?
Que el esquema lo generaba el LLM y cambiaba en cada corrida (4 esquemas distintos), asi que no se podia validar de forma determinista. Ademas el modelo no sabe que dia es hoy: con "hoy lunes" y "manana" devolvia fechas de 2024, toco pasarle fechas absolutas.

¿QUÉ EVAL FALLA O FALTA?
Los 5 casos ya pasan pero se corren a mano desde el csv, falta automatizar ese runner. Tambien falta un eval que pruebe detect_overlaps contra eventos reales de Google Calendar, hoy solo se cruza con EVENTOS_CALENDARIO simulados.

¿QUÉ HARÍAMOS PRIMERO SI ESTO FUERA PRODUCTO REAL?
Si fuera un producto real nuestro primer acercamiento seria hacer el claude.md y la skill para que se pueda interactura con los datos del usuario y se tenga el flujo definido para utilizar el modelo.
