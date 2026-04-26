---
date: 2026-04-26T01:05:10+0000
researcher: Jorge Castro
git_commit: a1cdcbb9417f75144272adc1ba45ff14376102d1
branch: main
repository: stepwise-dev
topic: "Investiga cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research. ¿Comparten código? ¿Hay dependencias cruzadas?"
tags: [research, codebase, plugin-architecture, stepwise-core, stepwise-git, stepwise-web, stepwise-research]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Relación entre los 4 plugins de stepwise-dev

## Research Question

¿Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research? ¿Comparten código? ¿Hay dependencias cruzadas?

## Summary

Los 4 plugins son **independientes en términos de código** — no comparten código fuente ni ficheros. Sin embargo, existen **dependencias de ejecución en tiempo de runtime** documentadas explícitamente en los SKILL.md: skills de stepwise-core referencian agentes de stepwise-web, y el ciclo de trabajo completo asume que todos los plugins están disponibles. La integración ocurre a través de un **contrato implícito**: el directorio `thoughts/` como almacenamiento compartido, y las referencias a agentes por nombre con prefijo de plugin (`stepwise-web:web-search-researcher`, `stepwise-git:commit`).

## Detailed Findings

### 1. Estructura física — sin código compartido

Cada plugin reside en un directorio propio con su `plugin.json` independiente:

- `core/.claude-plugin/plugin.json` — stepwise-core v1.0.1
- `git/.claude-plugin/plugin.json` — stepwise-git v1.0.0
- `web/.claude-plugin/plugin.json` — stepwise-web v1.0.0
- `research/.claude-plugin/plugin.json` — stepwise-research v1.0.0

El fichero `marketplace.json` en `.claude-plugin/` los lista como plugins autónomos con `source` apuntando a su directorio. **No existe ningún fichero compartido** entre plugins (no hay `lib/`, `shared/`, ni symlinks entre los cuatro directorios).

No hay declaraciones `dependencies`, `requires` ni `extends` en ninguno de los `plugin.json`.

### 2. Dependencias en tiempo de ejecución (runtime)

Aunque no hay dependencias formales declaradas, los skills referencian componentes de otros plugins en sus instrucciones de uso:

#### stepwise-core → stepwise-web

En `core/skills/research-codebase/SKILL.md` (línea 35):
```
- **stepwise-web:web-search-researcher** — web research (only if user explicitly asks)
```
El skill `research-codebase` declara que puede invocar el agente `web-search-researcher` del plugin stepwise-web si el usuario lo pide explícitamente. Es una dependencia **opcional** en runtime.

#### stepwise-core → stepwise-git

En `core/skills/implement-plan/SKILL.md` (línea 124):
```
- Use `/stepwise-git:commit` to create git commits for the changes
```
El skill `implement-plan` sugiere usar el skill `commit` de stepwise-git como siguiente paso del workflow. Es una referencia de **recomendación workflow**, no una invocación directa.

#### stepwise-research → stepwise-core (thoughts/)

En `research/README.md` (línea 183):
```
Reports integrate with the `stepwise-core` thoughts management system
```
El plugin stepwise-research graba sus reports en `thoughts/shared/research/`, el directorio gestionado por stepwise-core. Esta es la **integración de datos más concreta**: stepwise-research produce documentos en la estructura de directorios que stepwise-core inicializa y gestiona.

### 3. Dependencias de agentes dentro del mismo plugin

Existen referencias cruzadas de agentes **dentro de stepwise-core** (self-references):

Los skills `research-codebase`, `create-plan` e `iterate-plan` referencian los 5 agentes del propio stepwise-core:
- `stepwise-core:codebase-locator`
- `stepwise-core:codebase-analyzer`
- `stepwise-core:codebase-pattern-finder`
- `stepwise-core:thoughts-locator`
- `stepwise-core:thoughts-analyzer`

Esto es dependencia intra-plugin, no inter-plugin.

Dentro de stepwise-research, los agentes se referencian entre sí:
- `deep-research` (skill) invoca `stepwise-research:research-worker` y `stepwise-research:citation-analyst`
- `research-lead` (agente) invoca `stepwise-research:research-worker`

### 4. El directorio thoughts/ como contrato implícito de integración

El único punto de integración real entre plugins es el directorio `thoughts/` del proyecto usuario:

| Plugin | Rol respecto a thoughts/ |
|--------|--------------------------|
| stepwise-core | Inicializa la estructura (`thoughts-init`) y genera metadata (`thoughts-metadata`) |
| stepwise-core | Skills graban en `thoughts/shared/research/` y `thoughts/shared/plans/` |
| stepwise-research | Graba reports en `thoughts/shared/research/` (misma ruta que stepwise-core) |
| stepwise-git | No interactúa con thoughts/ |
| stepwise-web | No interactúa con thoughts/ |

`stepwise-research` asume que el directorio `thoughts/shared/research/` existe, y en su manejo de errores indica crearlo manualmente (`mkdir -p thoughts/shared/research`) si no existe — lo que normalmente hace stepwise-core.

### 5. Scripts ejecutables — sin compartición

Existen dos directorios de scripts:
- `core/skills/thoughts-management/scripts/` — `thoughts-init`, `thoughts-metadata`
- `research/skills/research-reports/scripts/` — `generate-report`

Ninguno de los scripts de un plugin es usado por otro plugin. Los scripts de `thoughts-management` son invocados solo desde skills dentro de stepwise-core mediante la variable `${CLAUDE_PLUGIN_ROOT}`, que resuelve al directorio del plugin instalado.

### 6. Modelos de lenguaje — sin coordinación

Cada skill y agente declara su modelo independientemente:

| Componente | Plugin | Modelo |
|---|---|---|
| research-codebase | stepwise-core | sonnet |
| create-plan | stepwise-core | opus |
| iterate-plan | stepwise-core | opus |
| implement-plan | stepwise-core | sonnet |
| validate-plan | stepwise-core | sonnet |
| commit | stepwise-git | haiku |
| web-search-researcher | stepwise-web | sonnet |
| deep-research | stepwise-research | opus |
| research-lead | stepwise-research | opus |
| research-worker | stepwise-research | sonnet |
| citation-analyst | stepwise-research | sonnet |

No hay coordinación de modelos entre plugins.

### 7. El workflow de desarrollo como integración conceptual

Los plugins están diseñados para funcionar juntos en un ciclo explícito, referenciado en la completion message de cada skill:

```
Research → Plan → Implement → Validate → Commit
```

- `research-codebase` (stepwise-core) → sugiere `/stepwise-core:create-plan`
- `create-plan` (stepwise-core) → sugiere `/stepwise-core:implement-plan` o `/stepwise-core:iterate-plan`
- `implement-plan` (stepwise-core) → sugiere `/stepwise-core:validate-plan` y `/stepwise-git:commit`

stepwise-web y stepwise-research son extensiones opcionales para búsqueda externa, no parte del ciclo principal.

## Code References

- `core/.claude-plugin/plugin.json` — definición del plugin stepwise-core
- `git/.claude-plugin/plugin.json` — definición del plugin stepwise-git
- `web/.claude-plugin/plugin.json` — definición del plugin stepwise-web
- `research/.claude-plugin/plugin.json` — definición del plugin stepwise-research
- `.claude-plugin/marketplace.json` — marketplace listing los 4 plugins
- `core/skills/research-codebase/SKILL.md:35` — referencia a `stepwise-web:web-search-researcher`
- `core/skills/implement-plan/SKILL.md:124` — referencia a `/stepwise-git:commit`
- `research/README.md:183` — integración declarada con el thoughts system de stepwise-core
- `research/skills/deep-research/SKILL.md:70-78` — spawn de agentes `stepwise-research:research-worker`
- `research/skills/deep-research/SKILL.md:243-247` — spawn de `stepwise-research:citation-analyst`
- `core/skills/thoughts-management/SKILL.md:139-141` — lista de skills que usan thoughts-init y thoughts-metadata

## Architecture Documentation

```
┌──────────────────────────────────────────────────────────────────┐
│                    Marketplace (marketplace.json)                │
│  stepwise-core │ stepwise-git │ stepwise-web │ stepwise-research │
└──────────────────────────────────────────────────────────────────┘

                   DEPENDENCIAS EN RUNTIME

┌─────────────────┐     references agent     ┌──────────────────┐
│  stepwise-core  │ ─────────────────────────▶│  stepwise-web    │
│  research-      │  (opcional, solo si       │  web-search-     │
│  codebase skill │   usuario lo pide)        │  researcher      │
└─────────────────┘                           └──────────────────┘

┌─────────────────┐   workflow suggestion     ┌──────────────────┐
│  stepwise-core  │ ─────────────────────────▶│  stepwise-git    │
│  implement-plan │  (en completion message)  │  commit skill    │
│  skill          │                           └──────────────────┘
└─────────────────┘

┌─────────────────┐   writes to thoughts/     ┌──────────────────┐
│ stepwise-       │ ─────────────────────────▶│  thoughts/       │
│ research        │  shared/research/         │  shared/         │
│                 │◀─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │  research/       │
│                 │  (assumes initialized     └──────────────────┘
│                 │   by stepwise-core)              ▲
└─────────────────┘                                  │ initializes
                                          ┌──────────┴───────────┐
                                          │   stepwise-core      │
                                          │   thoughts-          │
                                          │   management skill   │
                                          └──────────────────────┘

                   DEPENDENCIAS INTRA-PLUGIN (stepwise-core)

┌──────────────────────────────────────────────────────────────┐
│  stepwise-core                                               │
│  ┌────────────────┐    spawns    ┌─────────────────────────┐ │
│  │ research-      │ ────────────▶│ codebase-locator        │ │
│  │ codebase       │              │ codebase-analyzer       │ │
│  │ create-plan    │              │ codebase-pattern-finder │ │
│  │ iterate-plan   │              │ thoughts-locator        │ │
│  │ skills         │              │ thoughts-analyzer       │ │
│  └────────────────┘              └─────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

                   DEPENDENCIAS INTRA-PLUGIN (stepwise-research)

┌──────────────────────────────────────────────────────────────┐
│  stepwise-research                                           │
│  ┌────────────────┐    spawns    ┌─────────────────────────┐ │
│  │ deep-research  │ ────────────▶│ research-worker (1-8)   │ │
│  │ skill &        │              │ citation-analyst        │ │
│  │ research-lead  │              │ (via research-lead)     │ │
│  │ agent          │              └─────────────────────────┘ │
│  └────────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
```

## Historical Context (from thoughts/)

No se encontraron documentos previos en `thoughts/` que traten específicamente la arquitectura de relaciones entre plugins.

## Related Research

- `thoughts/shared/plans/2026-02-19-deep-research-plugin.md` — Plan de implementación del plugin stepwise-research, que documenta la decisión de arquitectura multi-agente
- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Contexto sobre el diseño del ciclo Research → Plan → Implement → Validate

## Open Questions

1. ¿Existe algún mecanismo formal de detección en runtime de si stepwise-web está instalado antes de que `research-codebase` intente invocar `web-search-researcher`? Los SKILL.md no documentan fallback en caso de que el plugin no esté disponible.

2. ¿Se garantiza que `thoughts/shared/research/` existe cuando stepwise-research intenta escribir? La guía de troubleshooting sugiere crearlo manualmente, lo que indica que no hay inicialización automática desde stepwise-research — se asume que stepwise-core ha sido ejecutado antes.
