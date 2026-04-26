---
date: 2026-04-26T01:05:40Z
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "Arquitectura de agentes especializados: qué agentes hay, qué tools tiene cada uno, y cómo se diferencian los locators de los analyzers"
tags: [research, codebase, agents, architecture, locators, analyzers, stepwise-core, stepwise-research, stepwise-web]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Arquitectura de Agentes Especializados

## Research Question

Investiga la arquitectura de agentes especializados: qué agentes hay, qué tools tiene cada uno, y cómo se diferencian los locators de los analyzers.

## Summary

El proyecto stepwise-dev distribuye **9 agentes especializados** en 3 plugins: `stepwise-core` (5 agentes), `stepwise-research` (3 agentes) y `stepwise-web` (1 agente). Todos los agentes son ficheros markdown ubicados en directorios `agents/` dentro de cada plugin.

La distinción fundamental entre locators y analyzers reside en el acceso a la herramienta `Read` y en el modelo LLM utilizado:
- Los **locators** (`codebase-locator`, `thoughts-locator`) usan solo `Grep, Glob, LS` — herramientas de navegación de sistema de ficheros. Su mandato explícito es encontrar **dónde** viven los ficheros sin leer su contenido. Usan el modelo `haiku` (más rápido y económico).
- Los **analyzers** (`codebase-analyzer`, `thoughts-analyzer`) añaden `Read` a su toolset, lo que les permite leer el contenido completo de los ficheros y documentar **cómo** funciona el código. Usan `sonnet`.

El agente `codebase-pattern-finder` es un híbrido: comparte tools con el analyzer (`Grep, Glob, Read, LS`) pero su especialización es encontrar patrones y ejemplos de código reutilizables a lo largo del codebase, no analizar un componente concreto.

## Detailed Findings

### Plugin stepwise-core — 5 agentes en `core/agents/`

#### codebase-locator
- **Archivo**: `core/agents/codebase-locator.md`
- **Tools**: `Grep, Glob, LS`
- **Model**: `haiku`
- **Color**: `blue`
- **Descripción (frontmatter)**: "Super Grep/Glob/LS tool — Use it if you find yourself desiring to use one of these tools more than once."
- **Rol**: Localiza ficheros y directorios relevantes a un feature o tarea. Devuelve listas estructuradas de ficheros agrupadas por propósito (implementation, test, config, type definitions, examples).
- **Mandato explícito** (`codebase-locator.md:103`): "Don't read file contents – Just report locations."
- **Invocado por**: `research-codebase` (SKILL.md:30), `create-plan` (SKILL.md:62), `iterate-plan` (SKILL.md:84).

#### codebase-analyzer
- **Archivo**: `core/agents/codebase-analyzer.md`
- **Tools**: `Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `green`
- **Descripción (frontmatter)**: "Analyzes codebase implementation details. The more detailed your request prompt, the better!"
- **Rol**: Analiza detalles de implementación leyendo ficheros específicos para entender lógica, trazar data flow, y explicar funcionamiento técnico con referencias precisas `file:line`.
- **Mandato explícito** (`codebase-analyzer.md:144`): "Your sole purpose is to explain HOW the code currently works, with surgical precision and exact references."
- **Invocado por**: `research-codebase` (SKILL.md:30), `create-plan` (SKILL.md:63), `iterate-plan` (SKILL.md:85).

#### codebase-pattern-finder
- **Archivo**: `core/agents/codebase-pattern-finder.md`
- **Tools**: `Grep, Glob, Read, LS`
- **Model**: `sonnet`
- **Color**: `purple`
- **Descripción (frontmatter)**: "Finds similar implementations, usage examples, or existing patterns that can be modeled after. It will give you concrete code examples."
- **Rol**: Encuentra implementaciones similares que sirven como plantilla. Combina localización con extracción de snippets de código reales.
- **Diferencia vs analyzer**: El analyzer entiende HOW funciona un componente específico; el pattern-finder cataloga QUÉ patrones existen en el codebase y dónde se usan. El mandato del pattern-finder es "show what patterns exist and where they are used" sin analizar en profundidad ni un componente específico.
- **Invocado por**: `research-codebase` (SKILL.md:30), `create-plan` (SKILL.md:119), `iterate-plan` (SKILL.md:86).

#### thoughts-locator
- **Archivo**: `core/agents/thoughts-locator.md`
- **Tools**: `Grep, Glob, LS`
- **Model**: `haiku`
- **Color**: `cyan`
- **Descripción (frontmatter)**: "Discovers relevant documents in the thoughts/ directory. Use when you need to find research, plans, notes, or tickets related to a topic."
- **Rol**: Localiza documentos en el directorio `thoughts/` (tickets, research, plans, prs, notes). Categoriza findings por tipo sin analizar el contenido en profundidad.
- **Paralelo con codebase-locator**: Mismas tools (`Grep, Glob, LS`), mismo modelo (`haiku`), mismo rol de "finder" pero para el dominio `thoughts/`.
- **Invocado por**: `research-codebase` (SKILL.md:30), `create-plan` (SKILL.md:122), `iterate-plan` (SKILL.md:89).

#### thoughts-analyzer
- **Archivo**: `core/agents/thoughts-analyzer.md`
- **Tools**: `Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `yellow`
- **Descripción (frontmatter)**: "The research equivalent of codebase-analyzer. Use when wanting to deep dive on a research topic."
- **Rol**: Extrae insights de alto valor de documentos en `thoughts/`. Filtra agresivamente para devolver solo información accionable (decisiones tomadas, trade-offs, constraints, especificaciones técnicas).
- **Mandato** (`thoughts-analyzer.md:150`): "You're a curator of insights, not a document summarizer."
- **Paralelo con codebase-analyzer**: Mismas tools (`Read, Grep, Glob, LS`), mismo modelo (`sonnet`), pero dominio `thoughts/`.
- **Invocado por**: `research-codebase` (SKILL.md:30), `create-plan` (SKILL.md:123), `iterate-plan` (SKILL.md:90).

---

### Plugin stepwise-web — 1 agente en `web/agents/`

#### web-search-researcher
- **Archivo**: `web/agents/web-search-researcher.md`
- **Tools**: `WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `orange`
- **Descripción (frontmatter)**: "Do you find yourself desiring information you don't feel well-trained on? Use web-search-researcher to find any answers to your questions!"
- **Rol**: Especialista en investigación web. Busca y extrae información de fuentes externas con estrategia broad → narrow.
- **Diferencia fundamental**: Es el único agente con `WebSearch` y `WebFetch`, lo que le permite acceder a fuentes externas. También es el único agente de stepwise-core/stepwise-web que tiene `TodoWrite`.
- **Uso**: Solo se invoca cuando el usuario lo solicita explícitamente. La skill `research-codebase` lo menciona condicionado (`SKILL.md:35`: "web research — only if user explicitly asks").
- **Invocado por**: `research-codebase` (SKILL.md:35, condicional).

---

### Plugin stepwise-research — 3 agentes en `research/agents/`

#### research-lead
- **Archivo**: `research/agents/research-lead.md`
- **Tools**: `Task, Read, Write, TodoWrite`
- **Model**: `opus`
- **Color**: `blue`
- **Rol**: Orchestrator del pipeline de deep research. Sigue el ciclo OODA (Observe, Orient, Decide, Act). Planifica investigación, delega sub-preguntas a research-worker agents **en paralelo** vía `Task`, sintetiza hallazgos, y genera el reporte final.
- **Tool clave**: `Task` — es el único agente de research con esta capacidad. También es el único agente de todo el proyecto que usa el modelo `opus`.
- **Invocado por**: `deep-research` (SKILL.md del plugin stepwise-research).

#### research-worker
- **Archivo**: `research/agents/research-worker.md`
- **Tools**: `WebSearch, WebFetch, Read, Grep, Glob`
- **Model**: `sonnet`
- **Color**: `green`
- **Rol**: Ejecuta research focalizado sobre una sub-pregunta asignada por research-lead. Estrategia de búsqueda broad → narrow, evaluación de calidad de fuentes (Tier 1-4), compresión de hallazgos en 3-6 key insights con citas.
- **Límite**: Max 10-15 tool calls combinados (WebSearch + WebFetch).
- **Invocado por**: `research-lead` (vía `Task`).

#### citation-analyst
- **Archivo**: `research/agents/citation-analyst.md`
- **Tools**: `Read, WebFetch, Grep`
- **Model**: `sonnet`
- **Color**: `yellow`
- **Rol**: Auditor de calidad de citas en research reports. Mapea claims a fuentes, verifica accesibilidad de URLs vía WebFetch, evalúa distribución de calidad de fuentes, genera citation quality report con score (Excellent/Good/Fair/Poor).
- **Mandato** (`citation-analyst.md:284`): "You are a quality auditor, not an editor: Flag issues, don't fix them."
- **Invocado por**: `deep-research` (SKILL.md:243, tras generar el reporte).

---

## Code References

- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-locator.md:1-7` — Frontmatter: tools: Grep, Glob, LS; model: haiku; color: blue
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-locator.md:103` — Mandato "Don't read file contents"
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-analyzer.md:1-7` — Frontmatter: tools: Read, Grep, Glob, LS; model: sonnet; color: green
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-analyzer.md:144` — Mandato "explain HOW the code currently works, with surgical precision"
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/codebase-pattern-finder.md:1-7` — Frontmatter: tools: Grep, Glob, Read, LS; model: sonnet; color: purple
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/thoughts-locator.md:1-7` — Frontmatter: tools: Grep, Glob, LS; model: haiku; color: cyan
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/thoughts-locator.md:105` — Mandato "Don't read full file contents – Just scan for relevance"
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/thoughts-analyzer.md:1-7` — Frontmatter: tools: Read, Grep, Glob, LS; model: sonnet; color: yellow
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/thoughts-analyzer.md:150` — Mandato "curator of insights, not a document summarizer"
- `/Users/jorge.castro/mordor/personal/stepwise-dev/web/agents/web-search-researcher.md:1-7` — Frontmatter: tools: WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS; model: sonnet; color: orange
- `/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/research-lead.md:1-11` — Frontmatter: tools: Task, Read, Write, TodoWrite; model: opus; color: blue
- `/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/research-worker.md:1-11` — Frontmatter: tools: WebSearch, WebFetch, Read, Grep, Glob; model: sonnet; color: green
- `/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/citation-analyst.md:1-10` — Frontmatter: tools: Read, WebFetch, Grep; model: sonnet; color: yellow
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/research-codebase/SKILL.md:29-35` — Lista de agentes disponibles y cuándo invocarlos
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/create-plan/SKILL.md:62-63,117-123` — Referencias a uso de agentes en create-plan

## Architecture Documentation

### Distribución por plugin

| Plugin | Agentes | Propósito |
|--------|---------|-----------|
| `stepwise-core` | codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer | Investigación del codebase y del directorio thoughts/ |
| `stepwise-web` | web-search-researcher | Investigación de fuentes externas web |
| `stepwise-research` | research-lead, research-worker, citation-analyst | Pipeline de deep research multi-agente con web |

### Tabla completa de agentes

| Agente | Plugin | Tools | Model | Color |
|--------|--------|-------|-------|-------|
| codebase-locator | stepwise-core | Grep, Glob, LS | haiku | blue |
| codebase-analyzer | stepwise-core | Read, Grep, Glob, LS | sonnet | green |
| codebase-pattern-finder | stepwise-core | Grep, Glob, Read, LS | sonnet | purple |
| thoughts-locator | stepwise-core | Grep, Glob, LS | haiku | cyan |
| thoughts-analyzer | stepwise-core | Read, Grep, Glob, LS | sonnet | yellow |
| web-search-researcher | stepwise-web | WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS | sonnet | orange |
| research-lead | stepwise-research | Task, Read, Write, TodoWrite | opus | blue |
| research-worker | stepwise-research | WebSearch, WebFetch, Read, Grep, Glob | sonnet | green |
| citation-analyst | stepwise-research | Read, WebFetch, Grep | sonnet | yellow |

### Diferencia entre Locators y Analyzers

La distinción es sistemática y consistente en ambos pares de dominio (codebase y thoughts):

**Locators** (`codebase-locator`, `thoughts-locator`):
- **Tools**: Solo `Grep, Glob, LS` — sin `Read`
- **Model**: `haiku` (más rápido y económico)
- **Rol**: Encontrar **dónde** está el código o el documento, sin leer su contenido
- **Output**: Listas de ficheros agrupadas por propósito con rutas completas y recuento
- **Mandato explícito en ambos**: "Don't read file contents – Just report locations" / "Don't read full file contents – Just scan for relevance"

**Analyzers** (`codebase-analyzer`, `thoughts-analyzer`):
- **Tools**: `Read, Grep, Glob, LS` — incluye `Read`
- **Model**: `sonnet` (más capaz)
- **Rol**: Leer y entender el contenido en profundidad
- **Output**: Análisis con referencias `file:line`, data flow, decisiones clave, patrones
- **Mandato explícito en ambos**: "Read files thoroughly before making statements" / "Read the entire document first"

El flujo de uso habitual en `research-codebase` es: **primero locators** para encontrar ficheros candidatos → **luego analyzers** sobre los más prometedores para entender su contenido.

### Paralelismo exacto entre pares de dominio

Existe una simetría arquitectónica perfecta entre el par `codebase-*` y el par `thoughts-*`:

```
codebase-locator   ←→  thoughts-locator   (tools: Grep, Glob, LS; model: haiku)
codebase-analyzer  ←→  thoughts-analyzer  (tools: Read, Grep, Glob, LS; model: sonnet)
```

La única diferencia es el dominio sobre el que operan:
- `codebase-*` opera sobre el código fuente del proyecto
- `thoughts-*` opera sobre el directorio `thoughts/` (documentación, planes, investigaciones históricas)

### Patrón de selección de modelo

| Modelo | Agentes que lo usan | Criterio |
|--------|---------------------|---------|
| `haiku` | codebase-locator, thoughts-locator | Tareas ligeras de búsqueda y navegación sin leer contenido |
| `sonnet` | codebase-analyzer, codebase-pattern-finder, thoughts-analyzer, web-search-researcher, research-worker, citation-analyst | Tareas de análisis y comprensión profunda |
| `opus` | research-lead | Orchestration de alto nivel con planificación compleja |

### Principio "documentarian" compartido

Todos los agentes de `stepwise-core` y el `web-search-researcher` comparten una instrucción crítica en su sección de instrucciones:

> "CRITICAL: YOUR ONLY JOB IS TO DOCUMENT AND EXPLAIN THE CODEBASE AS IT EXISTS TODAY — DO NOT suggest improvements or changes"

Este principio está presente en los 5 agentes de stepwise-core. Los agentes de `stepwise-research` tienen un enfoque diferente orientado a síntesis con citas y verificación de calidad, no a la descripción del estado actual sin juicio.

### Agentes con capacidades únicas

- **Solo `research-lead`** tiene la herramienta `Task` (para spawnar sub-agentes) y usa el modelo `opus`.
- **Solo `web-search-researcher` y `research-worker`** tienen `WebSearch` para búsquedas web.
- **Solo `research-lead`, `web-search-researcher`** tienen `TodoWrite` para gestión de tareas.
- **Solo `research-lead`** tiene `Write` para escritura directa de ficheros.

## Historical Context (from thoughts/)

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Referencia a los agentes especializados de stepwise-core. Un research histórico indica "All agents use model: sonnet" — esto difiere de los ficheros actuales donde los locators usan `haiku`. Esto sugiere que el cambio de modelo en locators se introdujo después de ese research.
- `thoughts/shared/research/2025-12-28-humanlayer-comparison-improvement-opportunities.md` — Contexto comparativo sobre la arquitectura multi-agente de stepwise vs HumanLayer.

## Related Research

- `core/skills/research-codebase-workspace/iteration-2/agent-architecture/with_skill/outputs/research.md` — Research de iteración anterior sobre el mismo tema. Contiene la misma arquitectura confirmada.
- `core/skills/create-plan/SKILL.md` — Contiene el catálogo más completo de cuándo usar cada agente en el contexto de planificación.

## Open Questions

1. Un research histórico en `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` indica "All agents use model: sonnet", pero los ficheros actuales muestran que los locators usan `haiku`. No hay documentación del cambio.
2. No hay documentación explícita sobre el criterio de asignación del `color` de cada agente (blue, green, purple, cyan, yellow, orange).
3. El agente `web-search-researcher` tiene `TodoWrite` entre sus tools, mientras que los agentes de `stepwise-core` no lo tienen — no hay documentación explicando este diseño diferenciado.
4. El agente `research-worker` tiene `Grep` y `Glob` además de las tools web — no hay documentación explícita de por qué los incluye dado que su foco es la investigación web.
