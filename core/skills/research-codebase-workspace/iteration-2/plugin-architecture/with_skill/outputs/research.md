---
date: 2026-04-26T00:00:00+00:00
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research. ¿Comparten código? ¿Hay dependencias cruzadas?"
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

Investiga cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research. ¿Comparten código? ¿Hay dependencias cruzadas?

## Summary

Los 4 plugins son **arquitectónicamente independientes**: cada uno tiene su propio directorio, su propio `plugin.json`, y no comparten código fuente. No existe ningún mecanismo de dependencia declarada entre ellos (no hay `dependencies` en los `plugin.json`). Sin embargo, existen **referencias semánticas cruzadas** en el contenido de los skills: `stepwise-core` (en `research-codebase`) hace referencia al agente `stepwise-web:web-search-researcher`; `stepwise-core` (en `implement-plan`) hace referencia al comando `/stepwise-git:commit`; y `stepwise-research` (en `deep-research` y `research-lead`) hace referencia internamente a sus propios agentes (`stepwise-research:research-worker`, `stepwise-research:citation-analyst`). El único sistema de estado compartido entre todos los plugins es el directorio `thoughts/` en el proyecto del usuario, al que todos escriben y leen de forma convencional.

## Detailed Findings

### 1. Independencia estructural de los plugins

Cada plugin es una unidad completamente independiente con la siguiente estructura:

- `core/` → `stepwise-core` (`core/.claude-plugin/plugin.json`)
- `git/` → `stepwise-git` (`git/.claude-plugin/plugin.json`)
- `web/` → `stepwise-web` (`web/.claude-plugin/plugin.json`)
- `research/` → `stepwise-research` (`research/.claude-plugin/plugin.json`)

Todos los `plugin.json` tienen la misma estructura mínima: `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`. **Ninguno de los cuatro contiene un campo `dependencies`**. No existe ningún mecanismo declarativo de dependencia inter-plugin.

El marketplace (`/.claude-plugin/marketplace.json`) lista los 4 plugins con sus rutas locales (`./core`, `./git`, `./web`, `./research`) pero no establece ninguna relación de dependencia entre ellos.

### 2. No hay código fuente compartido

No existe ningún directorio `shared/`, `common/`, `lib/` ni `utils/` a nivel raíz que sea importado por múltiples plugins. Cada plugin contiene exclusivamente sus propios archivos:

- **stepwise-core**: 10 skills SKILL.md + 5 agents .md + 2 scripts bash
- **stepwise-git**: 1 skill SKILL.md
- **stepwise-web**: 1 agent .md
- **stepwise-research**: 2 skills SKILL.md + 3 agents .md + 1 script bash

Los dos scripts bash existentes son completamente independientes entre sí:
- `core/skills/thoughts-management/scripts/thoughts-init` — inicializa el directorio `thoughts/`
- `core/skills/thoughts-management/scripts/thoughts-metadata` — genera metadatos git
- `research/skills/research-reports/scripts/generate-report` — genera informes con frontmatter YAML

### 3. Dependencias cruzadas semánticas (referencias en skills)

Las referencias cruzadas entre plugins existen únicamente como texto instruccional en los archivos SKILL.md/agent.md. Son invocaciones que Claude Code resuelve en tiempo de ejecución, no dependencias de código compilado.

#### stepwise-core → stepwise-web

En `core/skills/research-codebase/SKILL.md:70`:
```
- Use the **stepwise-web:web-search-researcher** agent for external documentation and resources
- IF you use web-research agents, instruct them to return LINKS with their findings...
```
Esta es la **única referencia cruzada de stepwise-core a stepwise-web**. Es opcional: la instrucción dice "only if user explicitly asks".

#### stepwise-core → stepwise-git

En `core/skills/implement-plan/SKILL.md:124`:
```
- Use `/stepwise-git:commit` to create git commits for the changes
```
Esta es la **única referencia cruzada de stepwise-core a stepwise-git**. Aparece en el mensaje de finalización del skill `implement-plan` como sugerencia de siguiente paso en el workflow.

#### stepwise-research → stepwise-research (interna)

Dentro del plugin `stepwise-research`, los skills y agentes se referencian entre sí:
- `research/skills/deep-research/SKILL.md:70,78,247`: referencia a `stepwise-research:research-worker` y `stepwise-research:citation-analyst`
- `research/agents/research-lead.md:82`: referencia a `stepwise-research:research-worker`

Estas son dependencias internas al plugin, no cruzadas.

#### stepwise-research — ausencia de referencia a stepwise-web

El plan de implementación en `thoughts/shared/plans/2026-02-19-deep-research-plugin.md` documenta la decisión explícita de **no depender de stepwise-web**: el plugin `stepwise-research` implementó sus propios agentes `research-worker` con acceso a `WebSearch` y `WebFetch` en lugar de reutilizar el agente `web-search-researcher` de `stepwise-web`. Esto se hizo para evitar dependencias entre plugins.

### 4. Sistema de estado compartido: el directorio thoughts/

El único elemento compartido entre los plugins es el directorio `thoughts/` del proyecto del usuario. Todos los plugins escriben y leen de él con la misma convención de rutas:

| Plugin | Escribe en | Lee de |
|--------|-----------|--------|
| stepwise-core (research-codebase) | `thoughts/shared/research/` | `thoughts/` (búsqueda) |
| stepwise-core (create-plan) | `thoughts/shared/plans/` | `thoughts/` (búsqueda) |
| stepwise-core (iterate-plan) | `thoughts/shared/plans/` | `thoughts/shared/plans/` |
| stepwise-core (implement-plan) | `thoughts/shared/plans/` (checkboxes) | `thoughts/shared/plans/` |
| stepwise-core (validate-plan) | — | `thoughts/shared/plans/` |
| stepwise-research (deep-research) | `thoughts/shared/research/` | — |
| stepwise-research (research-reports) | `thoughts/shared/research/` | — |

Esta convención compartida está definida por `core/skills/thoughts-management/SKILL.md` y los scripts en `core/skills/thoughts-management/scripts/`. El plugin `stepwise-research` **no usa** los scripts de `thoughts-management` para inicializar la estructura; en cambio, su SKILL.md indica: "If `thoughts/shared/research/` directory doesn't exist: Create it before saving the report."

### 5. Roles en el workflow general

Los 4 plugins implementan un workflow secuencial que el usuario puede invocar de forma independiente:

```
Research  →  Plan       →  Implement    →  Validate  →  Commit
[core]        [core]        [core]          [core]       [git]
   ↑
[web, optional]

Deep web research:
[research]
```

- `stepwise-core` es el hub central con el ciclo Research → Plan → Implement → Validate
- `stepwise-git` es invocado como paso final sugerido después de implement-plan
- `stepwise-web` es invocado opcionalmente desde research-codebase para búsqueda web externa
- `stepwise-research` es un plugin separado para investigación web profunda multi-agente, alternativo/complementario a la investigación de codebase de stepwise-core

### 6. Modelos de LLM utilizados

Cada plugin especifica modelos en sus skills:

| Plugin | Skill/Agent | Model |
|--------|-------------|-------|
| stepwise-core | research-codebase | opus |
| stepwise-core | create-plan | opus |
| stepwise-core | iterate-plan | opus |
| stepwise-core | implement-plan | sonnet |
| stepwise-core | validate-plan | sonnet |
| stepwise-core | thoughts-management | (no especificado) |
| stepwise-core | hamburger-method | (no especificado) |
| stepwise-core | codebase-locator | haiku |
| stepwise-core | codebase-analyzer | sonnet |
| stepwise-core | codebase-pattern-finder | sonnet |
| stepwise-core | thoughts-locator | haiku |
| stepwise-core | thoughts-analyzer | sonnet |
| stepwise-git | commit | haiku |
| stepwise-web | web-search-researcher | sonnet |
| stepwise-research | deep-research | opus |
| stepwise-research | research-lead | opus |
| stepwise-research | research-worker | sonnet |
| stepwise-research | citation-analyst | sonnet |

No hay coordinación de modelos entre plugins; cada uno define los suyos de forma independiente.

### 7. Agentes disponibles por plugin

Los agentes son invocables via `Task` tool con la sintaxis `subagent_type: "plugin:agent-name"`:

- **stepwise-core**: `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, `thoughts-locator`, `thoughts-analyzer`
- **stepwise-web**: `web-search-researcher`
- **stepwise-research**: `research-lead`, `research-worker`, `citation-analyst`
- **stepwise-git**: ningún agente, solo el skill `commit`

## Code References

- `core/.claude-plugin/plugin.json` — Metadata del plugin stepwise-core (sin campo dependencies)
- `git/.claude-plugin/plugin.json` — Metadata del plugin stepwise-git (sin campo dependencies)
- `web/.claude-plugin/plugin.json` — Metadata del plugin stepwise-web (sin campo dependencies)
- `research/.claude-plugin/plugin.json` — Metadata del plugin stepwise-research (sin campo dependencies)
- `.claude-plugin/marketplace.json` — Registro del marketplace con los 4 plugins
- `core/skills/research-codebase/SKILL.md:70` — Única referencia de stepwise-core a stepwise-web
- `core/skills/implement-plan/SKILL.md:124` — Única referencia de stepwise-core a stepwise-git
- `research/skills/deep-research/SKILL.md:70,78,247` — Referencias internas a agentes de stepwise-research
- `core/skills/thoughts-management/scripts/thoughts-init` — Script de inicialización del sistema thoughts/
- `research/skills/research-reports/scripts/generate-report` — Script independiente para generar informes
- `thoughts/shared/plans/2026-02-19-deep-research-plugin.md:249-253` — Documentación de la decisión de no depender de stepwise-web

## Architecture Documentation

### Patrón de diseño: plugins independientes con convenciones compartidas

Los 4 plugins siguen el patrón de **microservicios loosely-coupled**: no hay dependencias declaradas ni código compartido. La integración se realiza a través de:

1. **Convención de nombres de agentes**: La sintaxis `plugin:agent-name` permite que cualquier skill de cualquier plugin invoque agentes de otros plugins si el usuario los tiene instalados.

2. **Convención de directorio `thoughts/`**: Todos los plugins escriben outputs en la misma estructura de directorios, creando un "estado global" compartido basado en el sistema de archivos.

3. **Mensajes de workflow**: Los skills incluyen en sus mensajes de finalización sugerencias de siguiente paso que referencian skills de otros plugins (e.g., `implement-plan` sugiere usar `/stepwise-git:commit`).

### Acoplamiento opcional vs requerido

- **Acoplamiento requerido**: Ninguno. Todos los plugins funcionan de forma independiente.
- **Acoplamiento opcional**: 
  - `research-codebase` puede usar `web-search-researcher` si el usuario lo pide explícitamente y tiene stepwise-web instalado
  - El workflow completo sugiere usar `stepwise-git:commit` al finalizar, pero no es obligatorio

### Evolución documentada: stepwise-research vs stepwise-web

La decisión de arquitectura más relevante fue crear `stepwise-research` como plugin independiente en lugar de extender `stepwise-web`. El plan en `thoughts/shared/plans/2026-02-19-deep-research-plugin.md` documenta que esto se hizo deliberadamente para "avoid dependency on stepwise-web", manteniendo la independencia de los plugins.

## Historical Context (from thoughts/)

- `thoughts/shared/plans/2026-02-19-deep-research-plugin.md` — Plan de implementación del plugin stepwise-research. Documenta la decisión de no reutilizar `web-search-researcher` de stepwise-web (línea 249-253), la arquitectura multi-agente con research-lead, research-worker y citation-analyst, y la integración con el sistema thoughts/.

## Related Research

- `thoughts/shared/research/2025-11-12-testing-infrastructure.md`
- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md`
- `thoughts/shared/research/2025-12-28-humanlayer-comparison-improvement-opportunities.md`

## Open Questions

- No se ha investigado si el plugin system de Claude Code soporta declarar dependencias entre plugins en el `plugin.json`. Los archivos actuales no usan esa capacidad aunque pudiera existir.
- El directorio `thoughts/` es inicializado por `thoughts-management` (core) pero `stepwise-research` lo gestiona de forma autónoma. No está documentado si existe alguna garantía de que la estructura sea compatible cuando los plugins se instalan en distinto orden.
