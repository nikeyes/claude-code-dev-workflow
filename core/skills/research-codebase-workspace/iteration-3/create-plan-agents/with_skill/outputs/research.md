---
date: 2026-04-26T01:05:20+0000
researcher: Jorge Castro
git_commit: a1cdcbb9417f75144272adc1ba45ff14376102d1
branch: main
repository: stepwise-dev
topic: "¿Qué agentes usa la skill create-plan, en qué orden se ejecutan, y cuáles se lanzan en paralelo?"
tags: [research, codebase, create-plan, agents, skills, stepwise-core]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Agentes usados por la skill create-plan

## Research Question

¿Qué agentes usa la skill `create-plan`, en qué orden se ejecutan, y cuáles se lanzan en paralelo?

## Summary

La skill `create-plan` usa hasta 5 agentes especializados distribuidos en dos fases del proceso. En la **Fase 1 (Step 1)**, lanza 3 agentes en paralelo antes de hacer preguntas al usuario. En la **Fase 2 (Step 2)**, lanza hasta 5 agentes en paralelo para investigación más profunda. El orden y paralelismo están explícitamente definidos en el SKILL.md.

## Detailed Findings

### Agentes disponibles en create-plan

La skill `create-plan` referencia los siguientes agentes, todos definidos en `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/`:

| Agente | Archivo | Modelo | Color | Herramientas |
|--------|---------|--------|-------|-------------|
| `stepwise-core:codebase-locator` | `codebase-locator.md` | haiku | blue | Grep, Glob, LS |
| `stepwise-core:codebase-analyzer` | `codebase-analyzer.md` | sonnet | green | Read, Grep, Glob, LS |
| `stepwise-core:codebase-pattern-finder` | `codebase-pattern-finder.md` | sonnet | purple | Grep, Glob, Read, LS |
| `stepwise-core:thoughts-locator` | `thoughts-locator.md` | haiku | cyan | Grep, Glob, LS |
| `stepwise-core:thoughts-analyzer` | `thoughts-analyzer.md` | sonnet | yellow | Read, Grep, Glob, LS |

### Orden de ejecución y paralelismo

#### FASE 1 — Step 1: Context Gathering & Initial Analysis (líneas 59-64)

Se lanzan **3 agentes en paralelo** antes de hacer preguntas al usuario:

1. **`stepwise-core:codebase-locator`** — Encuentra todos los archivos relacionados con el ticket/tarea
2. **`stepwise-core:codebase-analyzer`** — Entiende cómo funciona la implementación actual
3. **`stepwise-core:thoughts-locator`** _(condicional, "If relevant")_ — Busca documentos existentes en `thoughts/` sobre la feature

Estos 3 se invocan en paralelo. El SKILL.md dice explícitamente: _"use specialized agents to research in parallel"_ (línea 60).

#### FASE 2 — Step 2: Research & Discovery (líneas 112-132)

Después de las clarificaciones iniciales del usuario, se lanza una segunda ronda de investigación paralela con hasta **5 agentes en paralelo**:

**Para investigación profunda:**
1. **`stepwise-core:codebase-locator`** — Encuentra archivos más específicos
2. **`stepwise-core:codebase-analyzer`** — Entiende detalles de implementación
3. **`stepwise-core:codebase-pattern-finder`** — Encuentra features similares para modelar

**Para contexto histórico:**
4. **`stepwise-core:thoughts-locator`** — Busca research, planes o decisiones en el área
5. **`stepwise-core:thoughts-analyzer`** — Extrae insights clave de los documentos más relevantes

El SKILL.md indica explícitamente: _"Create multiple Task agents to research different aspects concurrently"_ (línea 113) y _"Wait for ALL sub-tasks to complete before proceeding"_ (línea 132).

### Resumen del flujo completo de agentes

```
Step 1 (paralelo, antes de preguntar al usuario):
  ├── codebase-locator   [SIEMPRE]
  ├── codebase-analyzer  [SIEMPRE]
  └── thoughts-locator   [CONDICIONAL: "If relevant"]

  → Usuario responde preguntas

Step 2 (paralelo, tras clarificaciones):
  ├── codebase-locator       [para archivos más específicos]
  ├── codebase-analyzer      [para detalles de implementación]
  ├── codebase-pattern-finder [para patrones similares]
  ├── thoughts-locator        [para contexto histórico]
  └── thoughts-analyzer       [para insights de documentos encontrados]

  → Se espera a que TODOS completen antes de continuar
```

### Diferencia entre los dos grupos paralelos

| Aspecto | Step 1 | Step 2 |
|---------|--------|--------|
| Cuándo | Antes de preguntas al usuario | Después de clarificaciones del usuario |
| Agentes | 3 (codebase-locator, codebase-analyzer, thoughts-locator) | Hasta 5 (los 3 anteriores + codebase-pattern-finder + thoughts-analyzer) |
| Nuevo agente | — | `codebase-pattern-finder` y `thoughts-analyzer` |
| Propósito | Entendimiento inicial + preguntas informadas | Investigación profunda para diseñar el plan |

## Code References

- `core/skills/create-plan/SKILL.md` — Definición completa de la skill
  - Línea 60: _"use specialized agents to research in parallel"_ — parallelismo en Step 1
  - Líneas 62-64: Los 3 agentes del Step 1 (`codebase-locator`, `codebase-analyzer`, `thoughts-locator`)
  - Líneas 112-123: Step 2, lista completa de 5 agentes con descripción de su propósito
  - Línea 132: _"Wait for ALL sub-tasks to complete before proceeding"_ — barrera de sincronización
  - Líneas 431-459: Sección "Sub-task Spawning Best Practices" — guías generales de paralelismo
- `core/agents/codebase-locator.md` — Definición del agente localizador (model: haiku, tools: Grep, Glob, LS)
- `core/agents/codebase-analyzer.md` — Definición del agente analizador (model: sonnet, tools: Read, Grep, Glob, LS)
- `core/agents/codebase-pattern-finder.md` — Definición del agente de patrones (model: sonnet, tools: Grep, Glob, Read, LS)
- `core/agents/thoughts-locator.md` — Definición del agente localizador de thoughts (model: haiku, tools: Grep, Glob, LS)
- `core/agents/thoughts-analyzer.md` — Definición del agente analizador de thoughts (model: sonnet, tools: Read, Grep, Glob, LS)

## Architecture Documentation

### Propósito de cada agente

- **codebase-locator**: "Super Grep/Glob/LS tool" — Encuentra DÓNDE viven los archivos y componentes. Solo localiza, no lee contenidos. Usa model haiku (más ligero) porque solo hace búsquedas de texto/estructura.

- **codebase-analyzer**: Entiende CÓMO funciona el código. Lee archivos completos, traza flujos de datos, documenta detalles de implementación con referencias `file:line`. Usa sonnet (más potente) por la complejidad del análisis.

- **codebase-pattern-finder**: Encuentra ejemplos de implementaciones similares con fragmentos de código reales. Complementa al localizador mostrando no solo ubicaciones sino también el código en sí. Usa sonnet.

- **thoughts-locator**: Variante del codebase-locator pero para el directorio `thoughts/`. Encuentra documentos de research, planes, tickets y notas históricas. Usa haiku (solo busca, no analiza).

- **thoughts-analyzer**: Extrae insights de alto valor de los documentos de `thoughts/`. Filtra agresivamente para devolver solo la información más relevante y accionable. Usa sonnet.

### Patrón de sincronización

La skill sigue un patrón **fork-join**: lanza múltiples agentes en paralelo (fork), espera a que todos terminen (join), luego el skill principal sintetiza los resultados. Este patrón se aplica en ambas fases (Step 1 y Step 2).

## Historical Context (from thoughts/)

Los siguientes documentos en `thoughts/` mencionan estos agentes o la skill `create-plan`:

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Menciona codebase-locator/analyzer en contexto de mejoras
- `thoughts/shared/research/2025-12-28-humanlayer-comparison-improvement-opportunities.md` — Referencia a los agentes en comparación con HumanLayer
- `thoughts/shared/plans/2025-11-11-convert-to-plugin.md` — Plan de conversión a plugin que afecta la estructura de agentes
- `thoughts/shared/research/2025-11-12-testing-infrastructure.md` — Menciona codebase-locator/analyzer en contexto de testing
- `thoughts/shared/plans/2025-11-13-prevent-6000-token-limit-error.md` — Plan relacionado con límites de tokens en agentes
- `thoughts/shared/plans/2025-11-13-simplify-tests.md` — Simplificación de tests que menciona agentes

## Related Research

No existe un documento de research previo específicamente sobre los agentes de `create-plan`.

## Open Questions

Ninguna. La pregunta queda completamente respondida por el análisis directo del SKILL.md y los archivos de agentes.
