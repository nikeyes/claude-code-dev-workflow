---
date: 2026-04-26T12:00:00+00:00
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

**Date**: 2026-04-26T12:00:00+00:00
**Researcher**: Jorge Castro
**Git Commit**: a1cdcbb
**Branch**: main
**Repository**: stepwise-dev

## Research Question

Investiga la arquitectura de agentes especializados: qué agentes hay, qué tools tiene cada uno, y cómo se diferencian los locators de los analyzers.

## Summary

El proyecto stepwise-dev distribuye **9 agentes especializados** distribuidos en 3 plugins: `stepwise-core` (5 agentes), `stepwise-research` (3 agentes) y `stepwise-web` (1 agente). Todos los agentes son markdown files en directorios `agents/` de cada plugin.

La distinción fundamental entre locators y analyzers es de **profundidad y herramientas disponibles**:
- Los **locators** (codebase-locator, thoughts-locator) usan exclusivamente `Grep, Glob, LS` — herramientas de búsqueda y navegación de sistema de ficheros. Su mandato es encontrar **dónde** viven los ficheros sin leer su contenido.
- Los **analyzers** (codebase-analyzer, thoughts-analyzer) tienen acceso adicional a `Read`, lo que les permite leer el contenido completo de los ficheros y documentar **cómo** funciona el código.

El agente `codebase-pattern-finder` ocupa un espacio intermedio: tiene las mismas tools que el analyzer (`Grep, Glob, Read, LS`) pero su especialización es encontrar patrones y ejemplos de código existentes, no analizar un componente específico.

## Detailed Findings

### Plugin stepwise-core — 5 agentes en `core/agents/`

#### codebase-locator
- **Archivo**: `core/agents/codebase-locator.md`
- **Tools**: `Grep, Glob, LS`
- **Model**: `haiku`
- **Color**: `blue`
- **Descripción**: "Super Grep/Glob/LS tool" — localiza ficheros y directorios relevantes sin leer su contenido. Devuelve listas estructuradas de ficheros agrupadas por propósito (implementation, test, config, type definitions, examples).
- **Mandato**: Documentar dónde vive el código, NO analizar qué hace. No usa `Read`.
- **Uso**: Se llama cuando se necesita navegar la estructura del codebase, identificar dónde están clusters de ficheros relacionados.

#### codebase-analyzer
- **Archivo**: `core/agents/codebase-analyzer.md`
- **Tools**: `Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `green`
- **Descripción**: Analiza detalles de implementación. Lee ficheros específicos para entender lógica, trazar data flow, y explicar funcionamiento técnico con referencias precisas `file:line`.
- **Mandato**: Documentar HOW funciona el código con precisión quirúrgica. Incluye entry points, data flow, key patterns, configuration, error handling.
- **Diferencia clave vs locator**: Tiene `Read` y usa `sonnet` (más capaz). Su output incluye números de línea específicos y código.

#### codebase-pattern-finder
- **Archivo**: `core/agents/codebase-pattern-finder.md`
- **Tools**: `Grep, Glob, Read, LS`
- **Model**: `sonnet`
- **Color**: `purple`
- **Descripción**: Encuentra implementaciones similares, ejemplos de uso, y patrones existentes que sirven como plantillas. Combina localización con extracción de código.
- **Mandato**: Catalogar patrones existentes mostrando código real con contexto. Similar al locator pero incluye snippets de código.
- **Diferencia vs analyzer**: El analyzer entiende HOW funciona un componente específico; el pattern-finder muestra QUÉ patrones existen y dónde se usan a lo largo del codebase.

#### thoughts-locator
- **Archivo**: `core/agents/thoughts-locator.md`
- **Tools**: `Grep, Glob, LS`
- **Model**: `haiku`
- **Color**: `cyan`
- **Descripción**: Especialista en encontrar documentos en el directorio `thoughts/`. Localiza research, planes, notas, y tickets relacionados con un tema.
- **Mandato**: Categorizar findings por tipo (tickets, research, plans, prs, notes) sin analizar en profundidad el contenido.
- **Paralelo con codebase-locator**: Mismas tools (`Grep, Glob, LS`), mismo modelo (`haiku`), mismo rol de "finder" pero para el dominio `thoughts/` en lugar del codebase.

#### thoughts-analyzer
- **Archivo**: `core/agents/thoughts-analyzer.md`
- **Tools**: `Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `yellow`
- **Descripción**: Extrae insights de alto valor de documentos en `thoughts/`. Analiza en profundidad, filtra agresivamente, y devuelve solo información accionable.
- **Mandato**: Ser curador de insights, no resumidor de documentos. Identifica decisiones tomadas, trade-offs, constraints, especificaciones técnicas.
- **Paralelo con codebase-analyzer**: Mismas tools (`Read, Grep, Glob, LS`), mismo modelo (`sonnet`), pero dominio `thoughts/`.

---

### Plugin stepwise-web — 1 agente en `web/agents/`

#### web-search-researcher
- **Archivo**: `web/agents/web-search-researcher.md`
- **Tools**: `WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `orange`
- **Descripción**: Especialista en investigación web. Busca información moderna en la web cuando el codebase no tiene la respuesta.
- **Mandato**: Buscar estratégicamente (broad → narrow), evaluar calidad de fuentes, extraer información relevante con citas y links.
- **Uso**: Solo se llama cuando el usuario lo pide explícitamente. La skill `research-codebase` lo menciona como opción condicionada.
- **Diferencia fundamental**: Es el único agente orientado a fuentes externas. Tiene `WebSearch` y `WebFetch` que ningún otro agente en `stepwise-core` tiene.

---

### Plugin stepwise-research — 3 agentes en `research/agents/`

#### research-lead
- **Archivo**: `research/agents/research-lead.md`
- **Tools**: `Task, Read, Write, TodoWrite`
- **Model**: `opus`
- **Color**: `blue`
- **Descripción**: Lead researcher que orquesta workflows de multi-agent research. Sigue el ciclo OODA (Observe, Orient, Decide, Act).
- **Mandato**: Planificar investigación, delegar sub-preguntas a research-worker agents en paralelo, sintetizar hallazgos, generar reporte estructurado.
- **Uso**: Es el orchestrator del plugin `stepwise-research`. Spawna múltiples research-worker agents simultáneamente.
- **Tool clave**: `Task` — puede spawnar otros agentes. Es el único agente de research con esta capacidad.

#### research-worker
- **Archivo**: `research/agents/research-worker.md`
- **Tools**: `WebSearch, WebFetch, Read, Grep, Glob`
- **Model**: `sonnet`
- **Color**: `green`
- **Descripción**: Worker agent que ejecuta research focalizado con búsquedas web. Operado en paralelo por el research-lead.
- **Mandato**: Ejecutar búsquedas web (broad → narrow), evaluar calidad de fuentes (Tier 1-4), comprimir hallazgos en 3-6 key insights con citas.
- **Límite**: Max 10-15 tool calls combinados (WebSearch + WebFetch).

#### citation-analyst
- **Archivo**: `research/agents/citation-analyst.md`
- **Tools**: `Read, WebFetch, Grep`
- **Model**: `sonnet`
- **Color**: `yellow`
- **Descripción**: Verifica la exactitud, completitud y calidad de citas en research reports.
- **Mandato**: Auditor de calidad de citas, no editor. Mapea claims a fuentes, verifica accesibilidad de URLs, evalúa distribución de calidad de fuentes.
- **Output**: Citation quality report con score (Excellent/Good/Fair/Poor) y recomendaciones.

---

## Code References

- `core/agents/codebase-locator.md:1-7` — Frontmatter con tools, model, color
- `core/agents/codebase-analyzer.md:1-7` — Frontmatter con tools, model, color
- `core/agents/codebase-pattern-finder.md:1-7` — Frontmatter con tools, model, color
- `core/agents/thoughts-locator.md:1-7` — Frontmatter con tools, model, color
- `core/agents/thoughts-analyzer.md:1-7` — Frontmatter con tools, model, color
- `web/agents/web-search-researcher.md:1-7` — Frontmatter con tools, model, color
- `research/agents/research-lead.md:1-11` — Frontmatter con tools (incluye Task), model opus
- `research/agents/research-worker.md:1-11` — Frontmatter con tools WebSearch/WebFetch
- `research/agents/citation-analyst.md:1-10` — Frontmatter con tools

## Architecture Documentation

### Distribución por Plugin

| Plugin | Agentes | Propósito |
|--------|---------|-----------|
| `stepwise-core` | codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer | Investigación del codebase y directorio thoughts/ |
| `stepwise-web` | web-search-researcher | Investigación de fuentes externas web |
| `stepwise-research` | research-lead, research-worker, citation-analyst | Pipeline de deep research multi-agente |

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

La distinción es sistemática y consistente en ambos pares (codebase y thoughts):

**Locators** (`codebase-locator`, `thoughts-locator`):
- **Tools**: Solo `Grep, Glob, LS` — sin `Read`
- **Model**: `haiku` (más rápido, más económico)
- **Rol**: Encontrar dónde está el código/documento, sin leer su contenido
- **Output**: Listas de ficheros agrupadas por propósito con rutas completas
- **Mandato explícito**: "Don't read file contents – Just report locations"

**Analyzers** (`codebase-analyzer`, `thoughts-analyzer`):
- **Tools**: `Read, Grep, Glob, LS` — incluye `Read`
- **Model**: `sonnet` (más capaz)
- **Rol**: Leer y entender el contenido en profundidad
- **Output**: Análisis con referencias `file:line`, data flow, decisiones clave
- **Mandato explícito**: "Read files thoroughly before making statements"

El flujo de uso habitual en `research-codebase` es: primero locators para encontrar ficheros candidatos, luego analyzers sobre los más prometedores.

### Patrón de specialización por dominio

Existe un paralelismo exacto entre el par `codebase-*` y el par `thoughts-*`:

```
codebase-locator   ←→  thoughts-locator   (mismas tools: Grep, Glob, LS; mismo model: haiku)
codebase-analyzer  ←→  thoughts-analyzer  (mismas tools: Read, Grep, Glob, LS; mismo model: sonnet)
```

La única diferencia es el dominio sobre el que operan:
- `codebase-*` opera sobre el código fuente del proyecto
- `thoughts-*` opera sobre el directorio `thoughts/` (documentación, planes, investigaciones históricas)

### Model selection pattern

El patrón de selección de modelo es consistente:
- `haiku`: Para tareas ligeras de búsqueda/navegación (locators)
- `sonnet`: Para tareas de análisis y comprensión profunda (analyzers, pattern-finder, research workers)
- `opus`: Solo para orchestration de alto nivel (research-lead, y la propia skill research-codebase)

### Principio documentarian

Todos los agentes de `stepwise-core` y el `web-search-researcher` comparten una instrucción crítica idéntica en su frontmatter de instrucciones:

> "CRITICAL: YOUR ONLY JOB IS TO DOCUMENT AND EXPLAIN THE CODEBASE AS IT EXISTS TODAY — DO NOT suggest improvements or changes"

Este principio aparece en los 5 agentes de stepwise-core y en el web-search-researcher. Los agentes de `stepwise-research` tienen un enfoque diferente (síntesis con citas y verificación de calidad).

## Historical Context (from thoughts/)

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Referencia a los 6 agentes especializados de stepwise-core como parte del análisis de context management. Confirma que todos usan `model: sonnet` (ahora actualizado: locators usan `haiku`, según los ficheros actuales).

## Related Research

- `thoughts/shared/research/2025-12-28-humanlayer-comparison-improvement-opportunities.md` — Contexto comparativo sobre la arquitectura multi-agente de stepwise vs HumanLayer.

## Open Questions

1. El fichero `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md:209` indica "All agents use `model: sonnet`" pero los ficheros actuales muestran que los locators usan `haiku`. No se puede determinar si es un cambio posterior o un error en el research histórico.
2. No se encontró documentación explícita sobre el criterio para elegir el color de cada agente (blue, green, purple, cyan, yellow, orange).
3. El agente `web-search-researcher` tiene `TodoWrite` entre sus tools, mientras que el resto de agentes de `stepwise-core` no lo tienen — no hay documentación explicando este diseño.
