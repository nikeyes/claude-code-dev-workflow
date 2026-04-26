---
date: 2026-04-26
researcher: Jorge Castro
topic: "Arquitectura de agentes especializados: qué agentes hay, qué tools tiene cada uno, y cómo se diferencian los locators de los analyzers"
tags: [research, agents, architecture, locators, analyzers, multi-agent]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Arquitectura de Agentes Especializados

**Date**: 2026-04-26
**Researcher**: Jorge Castro
**Repository**: stepwise-dev

## Research Question

Investiga la arquitectura de agentes especializados: qué agentes hay, qué tools tiene cada uno, y cómo se diferencian los locators de los analyzers.

---

## Summary

El proyecto stepwise-dev implementa una arquitectura multi-agente distribuida en 4 plugins (stepwise-core, stepwise-git, stepwise-web, stepwise-research). Hay un total de **9 agentes especializados**, cada uno con un conjunto de tools acotado y una responsabilidad única. La separación fundamental entre locators y analyzers es: los **locators** usan solo herramientas de búsqueda (`Grep`, `Glob`, `LS`) y devuelven ubicaciones de archivos **sin leer su contenido**, mientras que los **analyzers** añaden la herramienta `Read` a su toolset y profundizan en el contenido para extraer significado, flujo de datos o insights de alto valor. Esta distinción reduce el consumo de tokens y mantiene cada agente enfocado en una sola responsabilidad.

---

## Detailed Findings

### Plugin stepwise-core — 5 agentes

Todos residen en `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/`.

#### 1. codebase-locator
**Archivo**: `core/agents/codebase-locator.md`
**Model**: `haiku` (el más ligero/barato del grupo)
**Color**: blue
**Tools**: `Grep`, `Glob`, `LS`

Especialista en **encontrar dónde vive el código**. Actúa como un "Super Grep/Glob/LS". Su mandato explícito es localizar ficheros y directorios relacionados con una feature o tarea, categorizarlos por propósito (implementation files, test files, config files, type definitions, documentation) y devolver rutas completas agrupadas lógicamente.

Restricción crítica: **no lee el contenido de los ficheros**. Solo reporta ubicaciones. El agente es literalmente un cartógrafo del repositorio, no un lector.

Output esperado: estructura con secciones `Implementation Files`, `Test Files`, `Configuration`, `Type Definitions`, `Related Directories`, `Entry Points`.

#### 2. codebase-analyzer
**Archivo**: `core/agents/codebase-analyzer.md`
**Model**: `sonnet`
**Color**: green
**Tools**: `Read`, `Grep`, `Glob`, `LS`

Especialista en entender **cómo funciona el código**. La diferencia clave con el locator es la presencia de `Read`, que le permite leer archivos completos. Su trabajo es analizar detalles de implementación, trazar el flujo de datos, identificar patrones arquitectónicos, y documentar contratos entre componentes con referencias exactas `file:line`.

Estrategia en 3 pasos: leer entry points → seguir el código paso a paso → documentar la lógica clave.

Output esperado: secciones `Overview`, `Entry Points`, `Core Implementation` (con líneas exactas), `Data Flow`, `Key Patterns`, `Configuration`, `Error Handling`.

#### 3. codebase-pattern-finder
**Archivo**: `core/agents/codebase-pattern-finder.md`
**Model**: `sonnet`
**Color**: purple
**Tools**: `Grep`, `Glob`, `Read`, `LS`

Especialista en **encontrar implementaciones similares y ejemplos de patrones existentes**. Funciona como una biblioteca de patrones vivos del codebase. A diferencia del locator (que solo dice dónde están los ficheros), el pattern-finder también lee esos ficheros para mostrar fragmentos de código concretos. A diferencia del analyzer (que analiza cómo funciona un componente dado), el pattern-finder busca variantes y ejemplos múltiples para que el desarrollador pueda modelar nuevo código.

Aunque comparte el mismo toolset que el analyzer (`Read`, `Grep`, `Glob`, `LS`), su enfoque es distinto: busca patrones repetibles y muestra variaciones, no analiza un único componente en profundidad.

Output esperado: secciones `Pattern 1`, `Pattern 2`, `Testing Patterns`, `Pattern Usage in Codebase`, `Related Utilities` — siempre con snippets de código reales.

#### 4. thoughts-locator
**Archivo**: `core/agents/thoughts-locator.md`
**Model**: `haiku`
**Color**: cyan
**Tools**: `Grep`, `Glob`, `LS`

Especialista en **descubrir documentos en el directorio `thoughts/`**. Es el equivalente exacto de `codebase-locator` pero para el sistema de documentación persistente del proyecto (thoughts/). Mapea la estructura de directorios `thoughts/shared/`, `thoughts/{username}/`, `thoughts/global/` y categoriza los documentos encontrados por tipo (tickets, research, plans, PRs, notes).

Al igual que codebase-locator, **no lee el contenido completo de los archivos**, solo escanea para determinar relevancia a partir de títulos y nombres de fichero.

Output esperado: secciones `Tickets`, `Research Documents`, `Implementation Plans`, `Related Discussions`, `PR Descriptions` con un conteo total de documentos.

#### 5. thoughts-analyzer
**Archivo**: `core/agents/thoughts-analyzer.md`
**Model**: `sonnet`
**Color**: yellow
**Tools**: `Read`, `Grep`, `Glob`, `LS`

Equivalente de `codebase-analyzer` pero para documentos del sistema `thoughts/`. Extrae **insights de alto valor** de los documentos, filtrando el ruido (divagaciones exploratorias, opciones rechazadas, workarounds temporales, información supersedida). Va más allá de resumir: evalúa la relevancia temporal de la información.

Estrategia: leer el documento completo → extraer decisiones, trade-offs, constraints, lecciones aprendidas, action items → filtrar todo lo que no sea accionable hoy.

Output esperado: secciones `Document Context` (con fecha y status de relevancia), `Key Decisions`, `Critical Constraints`, `Technical Specifications`, `Actionable Insights`, `Still Open/Unclear`, `Relevance Assessment`.

---

### Plugin stepwise-research — 3 agentes

Todos residen en `/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/`.

#### 6. research-lead
**Archivo**: `research/agents/research-lead.md`
**Model**: `opus` (el más potente)
**Color**: blue
**Tools**: `Task`, `Read`, `Write`, `TodoWrite`

Agente **orquestador** de investigación web multi-agente. No hace búsquedas directamente: su herramienta principal es `Task`, con la que spawna múltiples `research-worker` en paralelo. Sigue un ciclo OODA (Observe, Orient, Decide, Act) para planificar la investigación, delegar sub-preguntas, detectar gaps, sintetizar hallazgos y generar un informe final en `thoughts/shared/research/`.

Es el único agente de toda la arquitectura con la herramienta `TodoWrite` (para gestión de tareas de investigación) y `Write` (para generar el informe final).

#### 7. research-worker
**Archivo**: `research/agents/research-worker.md`
**Model**: `sonnet`
**Color**: green
**Tools**: `WebSearch`, `WebFetch`, `Read`, `Grep`, `Glob`

Agente **trabajador** de investigación web. Ejecuta una sub-pregunta asignada por `research-lead`. Aplica una estrategia búsqueda broad-to-narrow (3 rondas: descubrimiento amplio → exploración dirigida → deep dive), evalúa la calidad de las fuentes (jerarquía de 4 tiers: .gov/.edu > major tech blogs > community content > evitar), y devuelve hallazgos comprimidos en 3-6 insights con bibliografía numerada. Máximo 10-15 tool calls por ejecución.

#### 8. citation-analyst
**Archivo**: `research/agents/citation-analyst.md`
**Model**: `sonnet`
**Color**: yellow
**Tools**: `Read`, `WebFetch`, `Grep`

Agente **auditor de calidad** de informes de investigación. Verifica que las afirmaciones del informe estén respaldadas por fuentes adecuadas, que las URLs sean accesibles, y que la distribución de fuentes sea mayoritariamente Tier 1-2. Produce un informe de análisis con un score de calidad (Excellent/Good/Fair/Poor) y un veredicto final (`Ready to publish?`). No reescribe el informe, solo señala issues.

---

### Plugin stepwise-web — 1 agente

Reside en `/Users/jorge.castro/mordor/personal/stepwise-dev/web/agents/`.

#### 9. web-search-researcher
**Archivo**: `web/agents/web-search-researcher.md`
**Model**: `sonnet`
**Color**: orange
**Tools**: `WebSearch`, `WebFetch`, `TodoWrite`, `Read`, `Grep`, `Glob`, `LS`

Agente generalista de **investigación web** para uso directo desde skills (principalmente `research-codebase`). A diferencia de `research-worker` (que es un worker especializado dentro del pipeline de `research-lead`), este agente opera de forma autónoma: recibe una query, ejecuta múltiples búsquedas estratégicas, y produce un informe estructurado con fuentes citadas. Tiene el toolset más amplio de todos los agentes (incluye `TodoWrite`, `LS`, `Glob` además de las herramientas web).

---

## Architecture Documentation

### Tabla resumen de todos los agentes

| Agente | Plugin | Model | Tools | Rol |
|--------|--------|-------|-------|-----|
| codebase-locator | stepwise-core | haiku | Grep, Glob, LS | Localizar ficheros del codebase |
| codebase-analyzer | stepwise-core | sonnet | Read, Grep, Glob, LS | Analizar implementación del codebase |
| codebase-pattern-finder | stepwise-core | sonnet | Grep, Glob, Read, LS | Encontrar patrones y ejemplos |
| thoughts-locator | stepwise-core | haiku | Grep, Glob, LS | Localizar documentos en thoughts/ |
| thoughts-analyzer | stepwise-core | sonnet | Read, Grep, Glob, LS | Analizar documentos de thoughts/ |
| research-lead | stepwise-research | opus | Task, Read, Write, TodoWrite | Orquestar investigación web multi-agente |
| research-worker | stepwise-research | sonnet | WebSearch, WebFetch, Read, Grep, Glob | Ejecutar búsquedas web focalizadas |
| citation-analyst | stepwise-research | sonnet | Read, WebFetch, Grep | Auditar calidad de citas |
| web-search-researcher | stepwise-web | sonnet | WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS | Investigación web autónoma generalista |

### Diferencias clave entre Locators y Analyzers

La distinción es simple pero fundamental:

**Locators** (`codebase-locator`, `thoughts-locator`):
- Tools: solo `Grep`, `Glob`, `LS` — **sin `Read`**
- Modelo: `haiku` (más ligero, más barato)
- Propósito: encontrar **dónde** están las cosas, no leer su contenido
- Output: listas de rutas agrupadas por categoría
- No leen el contenido de los archivos encontrados
- Actúan como un índice o mapa del repositorio/thoughts/

**Analyzers** (`codebase-analyzer`, `thoughts-analyzer`):
- Tools: `Read` + `Grep` + `Glob` + `LS` — **añaden `Read`**
- Modelo: `sonnet` (más capaz)
- Propósito: entender **cómo** funciona el código o **qué valor** tiene un documento
- Output: análisis con referencias `file:line`, flujos de datos, decisiones clave
- Leen archivos en profundidad para extraer información semántica

**Pattern Finder** (`codebase-pattern-finder`):
- Tiene el mismo toolset que codebase-analyzer (`Read`, `Grep`, `Glob`, `LS`)
- Pero su foco es diferente: busca variantes y ejemplos reutilizables en lugar de analizar un componente específico en profundidad
- Es un híbrido entre locator (busca) y analyzer (lee), orientado a mostrar ejemplos concretos de código

### Flujo de invocación desde las Skills

La skill `research-codebase` (`core/skills/research-codebase/SKILL.md`) orquesta los agentes en dos fases:

1. **Fase de localización** (paralela): lanza `codebase-locator` y `thoughts-locator` simultáneamente para construir un mapa de qué existe y dónde
2. **Fase de análisis** (paralela, sobre los mejores hallazgos): lanza `codebase-analyzer` y/o `thoughts-analyzer` sobre los ficheros más prometedores

La skill `create-plan` sigue el mismo patrón pero puede añadir `codebase-pattern-finder` cuando necesita encontrar patrones similares para modelar la implementación.

El agente `web-search-researcher` se usa solo cuando el usuario pide explícitamente investigación web externa.

### Principio compartido entre todos los agentes core

Todos los agentes de stepwise-core comparten un mandato común explícito: son **documentaristas, no críticos ni consultores**. Solo describen lo que existe, sin sugerir mejoras, identificar problemas, o hacer recomendaciones. Este principio está repetido literalmente en todos sus ficheros de definición.

---

## Code References

- `core/agents/codebase-locator.md` — tools: Grep, Glob, LS; model: haiku; foco: WHERE
- `core/agents/codebase-analyzer.md` — tools: Read, Grep, Glob, LS; model: sonnet; foco: HOW
- `core/agents/codebase-pattern-finder.md` — tools: Grep, Glob, Read, LS; model: sonnet; foco: EXAMPLES
- `core/agents/thoughts-locator.md` — tools: Grep, Glob, LS; model: haiku; foco: WHERE in thoughts/
- `core/agents/thoughts-analyzer.md` — tools: Read, Grep, Glob, LS; model: sonnet; foco: HIGH-VALUE INSIGHTS
- `research/agents/research-lead.md` — tools: Task, Read, Write, TodoWrite; model: opus; foco: ORCHESTRATE
- `research/agents/research-worker.md` — tools: WebSearch, WebFetch, Read, Grep, Glob; model: sonnet; foco: SEARCH
- `research/agents/citation-analyst.md` — tools: Read, WebFetch, Grep; model: sonnet; foco: VERIFY QUALITY
- `web/agents/web-search-researcher.md` — tools: WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS; model: sonnet; foco: AUTONOMOUS WEB RESEARCH
- `core/skills/research-codebase/SKILL.md:58-79` — Describe cómo la skill orquesta los agentes en orden locator → analyzer
- `core/skills/create-plan/SKILL.md:59-70` — Describe cómo create-plan usa locator + analyzer + pattern-finder

---

## Open Questions

- No se encontraron agentes en los plugins `stepwise-git` (solo tiene la skill `commit`) ni confirmación de si hay agentes pendientes de implementar en el roadmap.
- El agente `codebase-pattern-finder` tiene el mismo toolset que `codebase-analyzer` pero con orden distinto en el frontmatter (`Grep, Glob, Read, LS` vs `Read, Grep, Glob, LS`); no queda claro si el orden tiene implicaciones de prioridad en el runtime.
