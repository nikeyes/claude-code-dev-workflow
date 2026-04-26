---
date: 2026-04-26T00:35:52+0000
researcher: Jorge Castro
git_commit: a1cdcbb9417f75144272adc1ba45ff14376102d1
branch: main
repository: stepwise-dev
topic: "¿Qué agentes usa la skill create-plan, en qué orden se ejecutan, y cuáles se lanzan en paralelo?"
tags: [research, codebase, create-plan, agents, codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: ¿Qué agentes usa la skill create-plan, en qué orden se ejecutan, y cuáles se lanzan en paralelo?

**Date**: 2026-04-26 02:35:52 CEST
**Researcher**: Jorge Castro
**Git Commit**: a1cdcbb9417f75144272adc1ba45ff14376102d1
**Branch**: main
**Repository**: stepwise-dev

## Research Question

¿Qué agentes usa la skill create-plan, en qué orden se ejecutan, y cuáles se lanzan en paralelo?

## Summary

La skill `create-plan` usa hasta 5 agentes especializados del plugin `stepwise-core`. Estos agentes se organizan en dos rondas de ejecución:

1. **Primera ronda (paralela, en Step 1)**: Se lanzan 3 agentes en paralelo antes de hacerle preguntas al usuario: `codebase-locator`, `codebase-analyzer`, y (condicionalmente) `thoughts-locator`.

2. **Segunda ronda (paralela, en Step 2)**: Se lanzan hasta 5 agentes en paralelo para investigación más profunda: `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, `thoughts-locator`, y `thoughts-analyzer`.

La skill también usa el Skill `thoughts-management` (no un agente Task) para inicializar el directorio `thoughts/` y generar metadata del documento de plan.

## Detailed Findings

### Agentes utilizados

La skill `create-plan` usa 5 agentes especializados, todos del plugin `stepwise-core`:

| Agente | Herramientas | Modelo | Color | Propósito en create-plan |
|--------|-------------|--------|-------|--------------------------|
| `stepwise-core:codebase-locator` | Grep, Glob, LS | haiku | blue | Encontrar ficheros relacionados con el ticket/tarea |
| `stepwise-core:codebase-analyzer` | Read, Grep, Glob, LS | sonnet | green | Entender cómo funciona la implementación actual |
| `stepwise-core:codebase-pattern-finder` | Grep, Glob, Read, LS | sonnet | purple | Encontrar features similares como referencia |
| `stepwise-core:thoughts-locator` | Grep, Glob, LS | haiku | cyan | Encontrar documentos thoughts/ sobre el tema |
| `stepwise-core:thoughts-analyzer` | Read, Grep, Glob, LS | sonnet | yellow | Extraer insights clave de documentos relevantes |

Ficheros de definición: `core/agents/codebase-locator.md`, `core/agents/codebase-analyzer.md`, `core/agents/codebase-pattern-finder.md`, `core/agents/thoughts-locator.md`, `core/agents/thoughts-analyzer.md`.

### Orden de ejecución y paralelismo

#### Step 1: Context Gathering & Initial Analysis (líneas 59-64 de SKILL.md)

Antes de hacer cualquier pregunta al usuario, se lanzan **3 agentes en paralelo**:

- `stepwise-core:codebase-locator` — encuentra todos los ficheros relacionados con el ticket/tarea
- `stepwise-core:codebase-analyzer` — entiende cómo funciona la implementación actual
- `stepwise-core:thoughts-locator` — (condicional: "If relevant") encuentra documentos thoughts/ existentes sobre el feature

```
[Step 1 - PARALELO]
├── codebase-locator   (obligatorio)
├── codebase-analyzer  (obligatorio)
└── thoughts-locator   (condicional, si es relevante)
```

Después de que completan, la skill lee TODOS los ficheros identificados en el contexto principal y presenta al usuario un resumen informado con preguntas focalizadas.

#### Step 2: Research & Discovery (líneas 112-132 de SKILL.md)

Tras recibir clarificaciones del usuario, se lanza una segunda ronda de investigación con **hasta 5 agentes en paralelo**:

- `stepwise-core:codebase-locator` — para encontrar ficheros más específicos
- `stepwise-core:codebase-analyzer` — para entender detalles de implementación
- `stepwise-core:codebase-pattern-finder` — para encontrar features similares que sirvan de modelo
- `stepwise-core:thoughts-locator` — para encontrar research, planes o decisiones sobre el área
- `stepwise-core:thoughts-analyzer` — para extraer insights clave de los documentos más relevantes

```
[Step 2 - PARALELO]
├── codebase-locator        (para ficheros más específicos)
├── codebase-analyzer       (para detalles de implementación)
├── codebase-pattern-finder (para patterns similares)
├── thoughts-locator        (para histórico en thoughts/)
└── thoughts-analyzer       (para insights de documentos clave)
```

La skill espera explícitamente a que **TODOS** los sub-tasks completen antes de proceder (`core/skills/create-plan/SKILL.md:132`).

#### Steps 3-5: Plan Structure Development, Plan Writing, Review

En los pasos restantes no se lanzan agentes Task. La skill:
- Crea el outline del plan y obtiene feedback del usuario (Step 3)
- Usa el Skill `thoughts-management` para inicializar `thoughts/` si no existe y generar metadata (Step 4)
- Escribe el plan a `thoughts/shared/plans/YYYY-MM-DD-[ENG-XXXX-]description.md` (Step 4)
- Presenta el borrador y itera con el usuario (Step 5)

### Diagrama de flujo completo

```
create-plan invocada
        │
        ▼
Step 1: Leer ficheros mencionados en $ARGUMENTS (main context)
        │
        ▼
Step 1: LANZAR EN PARALELO ─────────────────────────┐
        │  codebase-locator (obligatorio)            │
        │  codebase-analyzer (obligatorio)           │
        │  thoughts-locator (si es relevante)        │
        └────────────── ESPERAR A TODOS ─────────────┘
        │
        ▼
Step 1: Leer TODOS los ficheros identificados (main context)
        │
        ▼
Step 1: Presentar al usuario resumen + preguntas focalizadas
        │
        ▼
        [Usuario responde / aclara]
        │
        ▼
Step 2: Si el usuario corrige, verificar con nuevos sub-tasks
        │
        ▼
Step 2: LANZAR EN PARALELO ─────────────────────────┐
        │  codebase-locator                          │
        │  codebase-analyzer                         │
        │  codebase-pattern-finder                   │
        │  thoughts-locator                          │
        │  thoughts-analyzer                         │
        └────────────── ESPERAR A TODOS ─────────────┘
        │
        ▼
Step 2: Presentar findings y opciones de diseño
        │
        ▼
        [Usuario elige enfoque]
        │
        ▼
Step 3: Crear outline del plan → obtener feedback
        │
        ▼
Step 4: Inicializar thoughts/ si no existe (thoughts-management Skill)
        │
        ▼
Step 4: Generar metadata (thoughts-management Skill)
        │
        ▼
Step 4: Escribir plan a thoughts/shared/plans/...
        │
        ▼
Step 5: Revisar e iterar con el usuario
```

### Descripción de cada agente

#### codebase-locator (`core/agents/codebase-locator.md`)

Especialista en encontrar DONDE vive el código. Usa solo Grep, Glob y LS (no lee contenido de ficheros). Devuelve rutas organizadas por propósito: ficheros de implementación, tests, configuración, tipos, documentación. Usa modelo `haiku` por su velocidad y bajo coste en búsquedas simples.

#### codebase-analyzer (`core/agents/codebase-analyzer.md`)

Especialista en entender CÓMO funciona el código. Lee ficheros para trazar flujo de datos, identificar patrones arquitecturales y documentar lógica con referencias `fichero:línea`. Usa modelo `sonnet` por la complejidad de análisis requerida.

#### codebase-pattern-finder (`core/agents/codebase-pattern-finder.md`)

Especialista en encontrar ejemplos de patterns existentes. A diferencia de `codebase-locator`, no solo da rutas sino también extractos de código. Útil para modelar nuevas implementaciones en features similares ya existentes. Usa modelo `sonnet`.

#### thoughts-locator (`core/agents/thoughts-locator.md`)

Especialista en encontrar documentos en el directorio `thoughts/`. Busca en `thoughts/shared/` (equipo) y `thoughts/{username}/` (personal). Categoriza por tipo: tickets, research, planes, PRs, notas. Usa modelo `haiku` (solo localización, sin análisis profundo).

#### thoughts-analyzer (`core/agents/thoughts-analyzer.md`)

Especialista en extraer insights de alto valor de documentos thoughts/. Filtra agresivamente para devolver solo información accionable: decisiones tomadas, trade-offs, constraints técnicos, lecciones aprendidas. Usa modelo `sonnet` para análisis profundo.

### Notas sobre condicionalidad

- `thoughts-locator` en Step 1 tiene la nota "If relevant" (`SKILL.md:64`), lo que indica que su lanzamiento es opcional según el contexto.
- En Step 2, todos los agentes se listan como opciones disponibles, pero la skill los usa "según el tipo de investigación requerida" (`SKILL.md:113-114`). En la práctica, el patrón de sub-task spawning best practices (`SKILL.md:431`) indica lanzar múltiples tasks en paralelo.
- El Skill `thoughts-management` NO es un agente Task sino un Skill separado que se invoca directamente en el contexto principal.

## Code References

- `core/skills/create-plan/SKILL.md:59-64` — Primera ronda de agentes paralelos (Step 1)
- `core/skills/create-plan/SKILL.md:112-132` — Segunda ronda de agentes paralelos (Step 2)
- `core/skills/create-plan/SKILL.md:178-184` — Uso del Skill thoughts-management
- `core/skills/create-plan/SKILL.md:431-459` — Sub-task Spawning Best Practices con ejemplo de paralelismo
- `core/agents/codebase-locator.md` — Definición del agente localizador de código
- `core/agents/codebase-analyzer.md` — Definición del agente analizador de código
- `core/agents/codebase-pattern-finder.md` — Definición del agente buscador de patterns
- `core/agents/thoughts-locator.md` — Definición del agente localizador de thoughts
- `core/agents/thoughts-analyzer.md` — Definición del agente analizador de thoughts

## Architecture Documentation

La skill `create-plan` sigue el patrón arquitectural del proyecto: un agente orquestador principal (la skill) que delega investigación a agentes especializados y sintetiza los resultados. Los agentes están diseñados como "documentaristas" que describen el estado actual sin sugerir mejoras.

Los agentes se clasifican en dos dimensiones:
- **Por dominio**: `codebase-*` (código fuente) vs `thoughts-*` (documentación histórica)
- **Por profundidad**: `*-locator` (solo localización, haiku) vs `*-analyzer`/`*-pattern-finder` (análisis profundo, sonnet)

Este patrón permite optimizar el uso de tokens usando modelos más ligeros para búsquedas y modelos más potentes solo para análisis profundo.

## Historical Context (from thoughts/)

- `thoughts/searchable/shared/plans/2025-12-31-enhance-create-plan-vertical-slicing.md` — Plan para mejorar create-plan con vertical slicing. Documenta el flujo de planificación existente de 5 pasos: Context gathering → Research (spawn agents) → Plan structure → Plan writing → Sync and review. Confirma que el spawn de agentes ocurre en el Step 2 (Research & Discovery) del flujo.

## Related Research

No se encontraron otros documentos de research directamente relacionados con la arquitectura de agentes de create-plan en `thoughts/shared/research/`.

## Open Questions

Ninguna. La pregunta queda completamente respondida con la información encontrada en el código fuente.
