# AI Flow Priorizador — reglas para cualquier agente

Fuente única de reglas del sistema. Vale para cualquier agente de IA que opere
este repositorio: Claude Code, Codex, Kiro, Cowork o el que venga después. Los
archivos específicos de cada proveedor (`CLAUDE.md` y equivalentes) importan
este archivo; no lo duplican.

Si tu entorno no carga este archivo solo, léelo antes de tocar nada.

## Qué es esto

Un sistema de planificación semanal *local-first*. El estudiante guarda sus
tareas y notas en un vault de Markdown; el agente decide prioridades y propone
bloques de estudio; un core determinista en Python valida esa propuesta contra
el calendario real y solo escribe cuando el humano aprueba.

El principio que ordena todo el diseño:

> **La IA propone, el código valida, el humano decide.**

No eres el dueño del sistema. Eres el que propone. Todo lo que pueda verificarse
con código, se verifica con código — no con tu criterio.

## Estructura del vault

- `00-inbox/` — captura rápida, sin procesar.
- `10-university/<semestre>/<materia>/` — `_course.md`, `TASKS.md`, más
  `notes/`, `assignments/`, `resources/`, `attachments/`.
- `20-personal/<area>/` — áreas de vida personal.
- `30-professional/<proyecto>/` — `_project.md`, `TASKS.md`, y el repo bajo
  `code/<repo>/`, que el git del vault ignora.
- `90-archive/` — cerrado. Excluido de todo escaneo.
- `_templates/` — plantillas de materia, proyecto, área y tareas.
- `index.md` — el registro de áreas. Lo que no esté enlazado aquí **no existe**
  para la planeación.
- `log.md` — bitácora append-only.

El punto de entrada de cualquier área es su `_course.md` o `_project.md`. Léelo
antes de trabajar dentro de esa carpeta.

## Reglas duras

1. Toda materia, proyecto y área personal DEBE tener un `TASKS.md` con el
   formato de línea estándar. Sin excepciones.
2. No hay lista central de tareas. La vista global se calcula con
   `gcal.py scan`, que recorre cada área enlazada desde `index.md` y excluye
   `90-archive/`. Un área que no esté en el índice es invisible para la
   planeación; `scan` reporta cualquier `TASKS.md` sin registrar.
3. Todo cambio estructural o de tareas agrega UNA línea a `log.md`:
   `YYYY-MM-DD HH:MM | area | accion`. Append-only: nunca edites ni borres
   líneas pasadas.
4. Mantén `index.md` al día cuando se creen, muevan o archiven áreas. Los
   enlaces del índice llevan la **ruta completa relativa a la raíz del vault**,
   porque `scan` los resuelve como rutas y no por nombre de nota.
5. Para estimar una tarea, lee primero su nota `ctx`. Si el contexto no alcanza,
   PREGUNTA. Nunca inventes una estimación.
6. Materia, proyecto o área nueva se crea **solo** con
   `_scripts/obsidian_code/obsidian.py`, que scaffoldea desde `_templates/` e
   incluye siempre el `TASKS.md`. Si faltan metadatos (profesor, horario,
   evaluación, repo), pregúntalos: el script falla cerrado antes que dejar
   huecos silenciosos.
7. Toda operación de Google Calendar y Google Tasks pasa por
   `_scripts/gcal/gcal.py`. Los eventos se crean únicamente con `gcal.py apply`,
   después de que `gcal.py check` imprimió la tabla de revisión y el humano
   aprobó su código. Nunca borres ni muevas eventos o tareas existentes.
8. Las tareas se editan en el `TASKS.md` de su propia área, que es la única
   fuente de verdad. Una tarea terminada se marca `[x]`, no se borra.

## Formato de línea de tarea

```
- [ ] <título> | due:YYYY-MM-DD | est:<horas>h | prio:high|med|low | ctx:<ruta/relativa.md>
```

`ctx` es opcional pero obligatorio en la práctica para cualquier tarea estimada
en más de 2h: sin él, `scan` la marca con un issue. `due` siempre absoluto —
nunca "mañana" ni "el lunes". Esa fue la causa del peor fallo del prototipo: el
modelo no sabe qué día es hoy y respondía con fechas de otro año.

## Herramientas

Dos CLIs, los dos deterministas, los dos sin capacidad de borrar.

### Estructura del vault — `_scripts/obsidian_code/obsidian.py`

```
python obsidian.py --vault PATH init
python obsidian.py --vault PATH course  --name N --semester S --professor P --schedule H --grading G
python obsidian.py --vault PATH project --name N --repo R
python obsidian.py --vault PATH area    --name N
python obsidian.py --vault PATH list
```

Corre siempre con `--dry-run` primero: imprime el árbol, la línea de log y la
del índice sin tocar el disco. No sobrescribe archivos ni borra nada; si la
carpeta ya existe, aborta.

### Calendario y planeación — `_scripts/gcal/gcal.py`

```
python gcal.py scan                        # TASKS.md -> JSON validado
python gcal.py busy  --start ISO --end ISO # lo que ya está agendado
python gcal.py check PLAN --table          # valida y devuelve el código de aprobación
python gcal.py apply PLAN --approved CODE  # único comando que escribe
```

IDs de calendario, zona horaria, ruta del vault y política de bloques viven en
`_scripts/gcal/config.json`, que está fuera de git. Nunca los adivines ni los
escribas en el código.

El procedimiento completo de planeación semanal está en `plan-week/SKILL.md`.
Léelo antes de cualquier operación de calendario.

## Los gates

Ninguno es opinión tuya. Todos son código, y todos fallan cerrado.

- **`scan`** rechaza tareas mal formadas antes de que las veas: fechas
  inválidas, estimaciones sin unidad, prioridades inventadas, `ctx` inexistente.
- **`check`** valida tu plan contra la política (hora mínima, duración máxima,
  descansos) y contra los eventos reales. Lo que choca no se descarta: se parte
  y se rescatan los tramos útiles.
- **El código de aprobación** es un hash de esa revisión exacta. Si el plan
  cambia un minuto, el código cambia. No puedes aprobar un plan y ejecutar otro.
- **`apply`** revalida contra datos frescos antes de escribir, y usa IDs de
  evento deterministas, así que reejecutarlo nunca duplica.

## Lo que nunca haces

- Inventar fechas, horarios, estimaciones o disponibilidad.
- Crear estructura a mano en vez de usar `obsidian.py`.
- Escribir en el calendario sin que el humano haya aprobado el código de `check`.
- Borrar o mover eventos, tareas, notas o líneas de `log.md`.
- Commitear `credentials.json`, `token.json` o `config.json`.
- Leer las carpetas listadas en `private_paths` de `config.json`.
