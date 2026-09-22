# Vault — Master Context (Claude Code)

Las reglas del sistema son las mismas para todos los agentes y viven en un solo
archivo. No las dupliques aquí: si algo cambia, cámbialo allá.

@AGENTS.md

## Contexto del vault

Base de conocimiento y sistema de planeación personal de un estudiante de
Ingeniería de Sistemas en EAFIT. El vault es el "segundo cerebro": el agente
opera directamente sobre él, leyendo contexto, manteniendo tareas, planeando la
semana e insertando eventos y Google Tasks previa aprobación.

El contexto personal (bio, trabajo, preferencias, metas) vive en `/me.md`. Léelo
SOLO cuando la petición requiera saber algo personal — nunca para operaciones
rutinarias de vault, tareas o calendario.

Para trabajar en un proyecto, abre el agente en su carpeta: quedan juntos los
documentos y el código. Las materias pueden llevar código igual
(`10-university/.../<materia>/code/`). Las áreas paraguas agrupan subproyectos.

## Adjuntos

Las imágenes y PDFs pegados van en el `attachments/` del área, nunca en uno
global: así archivar un área se lleva sus imágenes con ella. Obsidian está
configurado para soltar los pegados ahí automáticamente ("In subfolder under
current folder" → `attachments`).

Los enlaces de imagen son wikilinks que Obsidian resuelve **por nombre de
archivo, no por ruta**, así que mover una nota entre áreas nunca rompe una
imagen; mové sus adjuntos con ella. Mantené los nombres de archivo únicos en
todo el vault: dos archivos con el mismo nombre hacen la resolución ambigua.

Ojo con la asimetría: los enlaces de `index.md` sí llevan ruta completa, porque
los resuelve `gcal.py scan` y no Obsidian (regla dura 4).

## Específico de Claude Code

El procedimiento de planeación semanal está en `plan-week/SKILL.md`. INVÓCALO
siempre antes de cualquier operación de calendario o tareas — nunca adivines
IDs ni comandos de memoria.
