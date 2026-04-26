---
date: 2026-04-26T00:00:00+00:00
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "¿Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research? ¿Comparten código? ¿Hay dependencias cruzadas?"
tags: [research, codebase, plugins, architecture, stepwise-core, stepwise-git, stepwise-web, stepwise-research]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Relaciones entre los 4 plugins de stepwise-dev

**Date**: 2026-04-26
**Researcher**: Jorge Castro
**Git Commit**: a1cdcbb
**Branch**: main
**Repository**: stepwise-dev

## Research Question

¿Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research? ¿Comparten código? ¿Hay dependencias cruzadas?

## Summary

Los 4 plugins son **arquitectónicamente independientes** en términos de código: no comparten ficheros, no tienen dependencias de paquetes entre sí y cada uno tiene su propio `plugin.json`. Sin embargo, están diseñados para trabajar juntos en un workflow (Research → Plan → Implement → Validate → Commit) y existen **referencias cruzadas explícitas** de nomenclatura (por ej. `stepwise-web:web-search-researcher`) y **un contrato de datos compartido** basado en el directorio `thoughts/` que todos leen y escriben.

La única "dependencia real en tiempo de ejecución" es que `stepwise-core:research-codebase` puede invocar opcionalmente al agente `stepwise-web:web-search-researcher` si el usuario necesita información externa. El resto de dependencias son solo recomendaciones de workflow documentadas en los READMEs.

## Detailed Findings

### 1. Estructura del Marketplace y de Plugins

El fichero raíz del marketplace registra los 4 plugins como entidades independientes dentro del mismo repositorio:

- `/Users/jorge.castro/mordor/personal/stepwise-dev/.claude-plugin/marketplace.json`

Cada plugin tiene su propio `plugin.json` sin campo `dependencies`:

| Plugin | Ubicación | Versión |
|--------|-----------|---------|
| stepwise-core | `core/.claude-plugin/plugin.json` | 1.0.1 |
| stepwise-git | `git/.claude-plugin/plugin.json` | 1.0.0 |
| stepwise-web | `web/.claude-plugin/plugin.json` | 1.0.0 |
| stepwise-research | `research/.claude-plugin/plugin.json` | 1.0.0 |

Ninguno de los `plugin.json` declara dependencias hacia los demás plugins. Son instalables de forma completamente independiente.

### 2. Código compartido: NO existe

No hay ningún fichero de código (script bash, utilidad, librería) que sea compartido o reutilizado entre plugins. Cada plugin contiene su propio conjunto de ficheros en su directorio:

- `core/` → skills (SKILL.md) + agents (.md) + scripts bash
- `git/` → skills (SKILL.md)
- `web/` → agents (.md)
- `research/` → skills (SKILL.md) + agents (.md) + scripts bash

El único patrón cercano a "código compartido" son los **scripts bash**, pero cada plugin tiene los suyos propios:
- `core/skills/thoughts-management/scripts/thoughts-init` y `thoughts-metadata` - solo pertenecen a stepwise-core
- `research/skills/research-reports/scripts/generate-report` - solo pertenece a stepwise-research

No existe ningún directorio `shared/`, `lib/` o `common/` entre plugins.

### 3. Dependencia cruzada explícita: stepwise-core → stepwise-web (opcional)

La única dependencia cruzada **funcional en tiempo de ejecución** está en:

- `core/skills/research-codebase/SKILL.md`, línea 70:
  > "For web research (only if user explicitly asks): Use the **stepwise-web:web-search-researcher** agent for external documentation and resources"

`research-codebase` puede invocar al agente `stepwise-web:web-search-researcher` como sub-tarea opcional. Esta referencia es **opcional** (requiere que el usuario lo pida explícitamente) y se manifiesta como una invocación del `Task` tool con `subagent_type: "stepwise-web:web-search-researcher"`.

Si `stepwise-web` no está instalado, `research-codebase` simplemente no podrá usar esa funcionalidad de búsqueda web, pero el skill funcionará correctamente para la investigación del codebase local.

### 4. Referencias cruzadas de workflow (documentadas)

Los READMEs y los SKILL.md contienen múltiples referencias cruzadas que representan el **flujo de trabajo recomendado**, no dependencias técnicas:

**En `core/skills/implement-plan/SKILL.md` (líneas 123-124):**
```
- Use `/stepwise-core:validate-plan` to verify completeness
- Use `/stepwise-git:commit` to create git commits for the changes
```

**En `core/skills/research-codebase/SKILL.md` (línea 191):**
```
- Use `/stepwise-core:create-plan [task description]` to plan implementation
```

**En `core/README.md`:**
```
Related Plugins:
- stepwise-git: Git commit workflow without Claude attribution
- stepwise-web: Web search and research capabilities
- stepwise-research: Multi-agent deep research with parallel web searches
```

**En `git/README.md`:**
```
Related Plugins:
- stepwise-core: Core workflow for Research → Plan → Implement → Validate
- stepwise-web: Web search and research capabilities
```

**En `web/README.md`:**
```
Related Plugins:
- stepwise-core: Core workflow for Research → Plan → Implement → Validate
- stepwise-git: Git commit workflow without Claude attribution
```

Estas referencias son documentación de integración de alto nivel, no dependencias de código.

### 5. Contrato de datos compartido: directorio `thoughts/`

El contrato más importante entre plugins es **el directorio `thoughts/`** como almacenamiento persistente compartido. Tanto `stepwise-core` como `stepwise-research` escriben en la misma estructura:

```
thoughts/
├── {username}/
│   ├── tickets/
│   └── notes/
└── shared/
    ├── research/   ← stepwise-core:research-codebase y stepwise-research:deep-research escriben aquí
    ├── plans/      ← stepwise-core:create-plan escribe aquí
    └── prs/
```

**stepwise-core** (via `thoughts-management/scripts/thoughts-init`):
- Inicializa el directorio `thoughts/`
- Los skills `research-codebase`, `create-plan`, `implement-plan` usan `${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init`

**stepwise-research** (`deep-research/SKILL.md`, línea 159):
- Guarda reportes en `thoughts/shared/research/[topic]-[date].md`
- Crea el directorio si no existe: `mkdir -p thoughts/shared/research`
- **No llama** a `thoughts-init` de stepwise-core; lo crea directamente si falta

Este es el punto donde los dos plugins "compiten" funcionalmente: ambos pueden crear/usar `thoughts/shared/research/`, pero sin coordinación técnica (no hay llamada a un API o script compartido).

### 6. Convenciones de nomenclatura compartidas (sin código compartido)

Los dos plugins con scripts (`stepwise-core` y `stepwise-research`) producen documentos con **YAML frontmatter idéntico en estructura**, pero cada uno lo genera de forma independiente:

**stepwise-core** (via `thoughts-metadata` bash script):
```yaml
date: [ISO datetime]
researcher: [git user]
git_commit: [hash]
branch: [branch name]
repository: [repo name]
topic: "[question]"
tags: [list]
status: complete
```

**stepwise-research** (via `generate-report` bash script):
```yaml
title: Research on [Topic]
date: YYYY-MM-DD
query: [original question]
keywords: [5-8 terms]
status: complete
agent_count: N
source_count: M
```

Las estructuras son similares en concepto pero distintas en campos concretos, ya que cada plugin tiene su propio script que genera el frontmatter de forma independiente.

### 7. Modelo de Claude asignado por plugin

Cada plugin asigna modelos de Claude diferentes según el rol:

| Componente | Plugin | Modelo |
|------------|--------|--------|
| research-codebase, create-plan, iterate-plan | stepwise-core | opus |
| implement-plan, validate-plan | stepwise-core | sonnet |
| codebase-locator, thoughts-locator | stepwise-core | haiku |
| codebase-analyzer, codebase-pattern-finder, thoughts-analyzer | stepwise-core | sonnet |
| commit | stepwise-git | haiku |
| web-search-researcher | stepwise-web | sonnet |
| deep-research, research-lead | stepwise-research | opus |
| research-worker, citation-analyst | stepwise-research | sonnet |

Esta asignación es independiente por plugin y no existe un fichero de configuración centralizado para los modelos.

### 8. Licencia compartida (Apache 2.0)

Todos los plugins comparten la misma licencia Apache 2.0 y el mismo autor (Jorge Castro). Varios ficheros en `stepwise-core` y `stepwise-git` tienen doble atribución indicando origen en el proyecto HumanLayer:

```
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2024 humanlayer Authors (original)
SPDX-FileCopyrightText: 2025 Jorge Castro (modifications)
```

Los ficheros de `stepwise-research` y `stepwise-web` no tienen este encabezado SPDX, lo que sugiere que son creaciones originales (no derivadas de HumanLayer).

### 9. Relación entre stepwise-research y stepwise-web

`stepwise-research` y `stepwise-web` resuelven necesidades similares (búsqueda web) pero con niveles de orquestación distintos:

- `stepwise-web`: Un único agente `web-search-researcher` que hace búsquedas web simples. Es invocado directamente como sub-agente opcional por `stepwise-core:research-codebase`.

- `stepwise-research`: Sistema multi-agente completo (`deep-research` → `research-lead` → N × `research-workers` + `citation-analyst`). Diseñado para investigación profunda con síntesis y verificación de citas.

Los dos plugins no se referencian entre sí en ningún fichero.

## Code References

- `.claude-plugin/marketplace.json` - Registro de los 4 plugins independientes
- `core/.claude-plugin/plugin.json` - Plugin config de stepwise-core (sin dependencies)
- `git/.claude-plugin/plugin.json` - Plugin config de stepwise-git (sin dependencies)
- `web/.claude-plugin/plugin.json` - Plugin config de stepwise-web (sin dependencies)
- `research/.claude-plugin/plugin.json` - Plugin config de stepwise-research (sin dependencies)
- `core/skills/research-codebase/SKILL.md:70` - Única referencia cruzada funcional (stepwise-web:web-search-researcher)
- `core/skills/implement-plan/SKILL.md:124` - Referencia workflow a stepwise-git:commit
- `core/skills/thoughts-management/scripts/thoughts-init` - Script bash que inicializa thoughts/ (solo stepwise-core)
- `research/skills/research-reports/scripts/generate-report` - Script bash para reportes (solo stepwise-research)
- `research/skills/deep-research/SKILL.md:70-115` - Orquestación de research-workers dentro de stepwise-research
- `core/agents/codebase-locator.md:6` - model: haiku (asignación por agente)
- `research/agents/research-lead.md:9` - model: opus (asignación por agente)

## Architecture Documentation

### Diagrama de relaciones

```
stepwise-core
├── Agents propios: codebase-locator, codebase-analyzer, codebase-pattern-finder,
│                   thoughts-locator, thoughts-analyzer
├── Scripts propios: thoughts-init, thoughts-metadata
├── Invoca OPCIONALMENTE: stepwise-web:web-search-researcher (via Task tool)
├── Recomienda en workflow: stepwise-git:commit (solo documentación)
└── Escribe en: thoughts/shared/research/, thoughts/shared/plans/

stepwise-git
├── Sin dependencias hacia otros plugins
└── Referenciado por: stepwise-core (solo documentación de workflow)

stepwise-web
├── Sin dependencias hacia otros plugins
├── Referenciado por: stepwise-core (invocación funcional opcional)
└── Agente: web-search-researcher (herramientas: WebSearch, WebFetch)

stepwise-research
├── Agents propios: research-lead, research-worker, citation-analyst
├── Scripts propios: generate-report
├── Sin dependencias hacia otros plugins
└── Escribe en: thoughts/shared/research/ (misma ruta que stepwise-core)
```

### Tipos de relación

| Relación | Tipo | Técnica |
|----------|------|---------|
| core → web | Funcional opcional | Invocación de agente via Task tool |
| core → git | Workflow recommendation | Solo documentación/texto |
| core → research | Workflow recommendation | Solo documentación/texto |
| research → web | Sin relación | (no existe) |
| git → web | Sin relación | (no existe) |
| research → core | Shared storage convention | Mismo directorio thoughts/ |
| Todos | Shared license | Apache 2.0, mismo repo |

## Historical Context (from thoughts/)

No se encontraron documentos en `thoughts/shared/research/` directamente relevantes sobre la arquitectura multi-plugin actual. Los planes en `thoughts/shared/plans/` muestran la evolución histórica:

- `thoughts/shared/plans/2025-11-11-convert-to-plugin.md` - Plan de conversión al sistema de plugins
- `thoughts/shared/plans/2026-02-19-deep-research-plugin.md` - Plan de creación del plugin stepwise-research (el más reciente de los 4)

Esto confirma que `stepwise-research` fue el último plugin creado (según su número de versión 1.0.0 frente a stepwise-core 1.0.1 y la fecha del plan).

## Open Questions

- No está documentado si existe algún mecanismo de coordinación cuando tanto `stepwise-core:research-codebase` como `stepwise-research:deep-research` intentan crear `thoughts/shared/research/` simultáneamente.
- El `research-lead` agent dentro de stepwise-research tiene la misma funcionalidad orquestadora que el skill `deep-research` del mismo plugin — no está documentada la distinción de cuándo usar uno u otro.
