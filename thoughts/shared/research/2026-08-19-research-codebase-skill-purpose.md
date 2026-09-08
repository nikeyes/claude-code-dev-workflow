---
date: 2026-08-19T08:22:00+0000
researcher: Jorge Castro
git_commit: 0ef62fc9f7e23c9a979b109ffcd61fc423c445aa
branch: feat/codex
repository: stepwise-dev
topic: "¿Para qué sirve el documento core/skills/research-codebase/SKILL.md?"
tags: [research, codebase, skills, workflow]
status: complete
last_updated: 2026-08-19
last_updated_by: Jorge Castro
---

# Research: Propósito de la skill research-codebase

## Research Question

¿Para qué sirve `core/skills/research-codebase/SKILL.md`?

## Summary

El documento define la skill `research-codebase`, que dirige una investigación del repositorio para responder una pregunta concreta sobre cómo existe y funciona el código actualmente. Su salida no es una modificación del código: es un documento persistente de investigación en `thoughts/shared/research/`.

Es la primera fase del ciclo Research → Plan → Implement → Validate. Separa deliberadamente la comprensión del sistema de las propuestas de cambio: salvo petición explícita, la skill no debe criticar, recomendar mejoras ni diseñar una solución.

## Detailed Findings

### Contrato de la skill

El frontmatter registra el nombre, la descripción, el argumento esperado y el modelo, y desactiva la invocación implícita. La entrada debe ser una pregunta o tema de investigación suficientemente específico. Si falta o es ambiguo, el agente debe pedir concreción antes de continuar.

### Comportamiento de investigación

La skill ordena:

1. Leer primero y por completo cualquier fichero mencionado por el usuario.
2. Investigar directamente o mediante agentes especializados en localización, análisis, patrones e historial de `thoughts/`.
3. Usar investigación web solamente cuando el usuario la solicite explícitamente.
4. Dar prioridad al código vivo frente a documentos históricos y citar rutas y líneas.

Los subagentes son un mecanismo disponible, especialmente para preguntas que abarcan varios componentes; no son el producto final de la skill.

### Salida persistente

La skill inicializa `thoughts/` si hace falta, recopila metadata Git y prescribe un documento Markdown con frontmatter, resumen, hallazgos, referencias, arquitectura, contexto histórico, investigaciones relacionadas y preguntas abiertas. Las preguntas posteriores se anexan al mismo documento, actualizando su metadata.

### Papel en el flujo del proyecto

El README presenta `research-codebase` como el comando principal de la fase de investigación. El conocimiento se guarda en `thoughts/` para sobrevivir a la limpieza del contexto entre fases. Después, una investigación puede servir como entrada factual para `create-plan`, pero esta skill no crea ese plan.

## Code References

- `core/skills/research-codebase/SKILL.md:2-6` — identidad, argumento, modelo e invocación explícita.
- `core/skills/research-codebase/SKILL.md:15-23` — alcance descriptivo y validación de la pregunta.
- `core/skills/research-codebase/SKILL.md:27-39` — proceso, agentes disponibles y prioridad del código actual.
- `core/skills/research-codebase/SKILL.md:41-81` — persistencia, metadata y estructura del informe.
- `core/skills/research-codebase/SKILL.md:83-85` — tratamiento de seguimientos.
- `README.md:176-196` — lugar de la skill en el flujo y comportamiento resumido.
- `README.md:232-248` — ejemplo del ciclo completo desde investigación hasta validación.

## Architecture Documentation

```text
Pregunta concreta del usuario
          |
          v
  research-codebase
    |     |      |
    |     |      +--> historial en thoughts/
    |     +---------> lectura/análisis del repositorio
    +---------------> agentes especializados cuando procede
          |
          v
thoughts/shared/research/YYYY-MM-DD-*.md
          |
          v
 posible entrada factual para create-plan
```

## Historical Context (from thoughts/)

El plan de compatibilidad con Codex conserva `$ARGUMENTS` deliberadamente. En Claude Code, la invocación normal usa `/stepwise-core:research-codebase <pregunta>`; en Codex, `$ARGUMENTS` no se expande y la pregunta debe incluirse en el propio mensaje. El mismo plan considera importante validar manualmente la delegación paralela cuando la investigación lo requiere.

Referencia: `thoughts/shared/plans/2026-08-19-codex-compatibility.md:24-30,169-180`.

## Related Research

No se encontró otro documento de investigación dedicado al propósito de esta skill. El contexto relacionado disponible es el plan de compatibilidad con Codex citado arriba.

## Open Questions

Ninguna para explicar el propósito actual del documento.
