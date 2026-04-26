---
date: 2026-04-26T00:00:00+0000
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research. ¿Comparten código? ¿Hay dependencias cruzadas?"
tags: [research, codebase, plugin-architecture, cross-plugin-dependencies]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Relaciones entre los 4 plugins de stepwise-dev

## Research Question

¿Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research? ¿Comparten código? ¿Hay dependencias cruzadas?

## Summary

Los 4 plugins están diseñados como unidades independientes dentro de un marketplace compartido. No comparten código fuente ejecutable directamente entre sí, pero sí existen **dependencias conceptuales y de convención de datos** (el sistema `thoughts/`). La única dependencia funcional explícita en código es la referencia de `stepwise-core:research-codebase` al agente `stepwise-web:web-search-researcher`. Las demás referencias cruzadas son de tipo informativo (menciones en READMEs y sugerencias de workflow al usuario).

## Detailed Findings

### 1. Estructura de marketplace (sin dependencias declaradas)

El marketplace se define en `/.claude-plugin/marketplace.json`. Los 4 plugins aparecen listados como entradas independientes, cada uno apuntando a su propio directorio (`./core`, `./git`, `./web`, `./research`). No existe ningún campo `dependencies` ni `requires` en ninguno de los `plugin.json`:

- `/Users/jorge.castro/mordor/personal/stepwise-dev/.claude-plugin/marketplace.json` — lista los 4 plugins
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/.claude-plugin/plugin.json`
- `/Users/jorge.castro/mordor/personal/stepwise-dev/git/.claude-plugin/plugin.json`
- `/Users/jorge.castro/mordor/personal/stepwise-dev/web/.claude-plugin/plugin.json`
- `/Users/jorge.castro/mordor/personal/stepwise-dev/research/.claude-plugin/plugin.json`

Todos comparten la misma estructura de metadatos (`name`, `version`, `description`, `author`, `license`) pero no declaran ninguna dependencia entre sí.

### 2. La única dependencia de código entre plugins: core → web

En `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/research-codebase/SKILL.md` (línea 35), el skill `research-codebase` menciona explícitamente al agente de otro plugin como una herramienta disponible:

```
- **stepwise-web:web-search-researcher** — web research (only if user explicitly asks)
```

Esta es la única referencia cruzada de código funcional entre plugins. Si `stepwise-web` no está instalado, `research-codebase` continúa funcionando normalmente pero sin capacidad de búsqueda web bajo demanda.

### 3. stepwise-research es funcionalmente independiente de stepwise-web

Aunque ambos plugins realizan búsqueda web, implementan la funcionalidad de forma completamente separada y sin reutilizar código:

- `stepwise-web` (`/Users/jorge.castro/mordor/personal/stepwise-dev/web/agents/web-search-researcher.md`): Agente único de 108 líneas, usa `WebSearch + WebFetch + TodoWrite + Read + Grep + Glob + LS`, modelo `sonnet`. Un solo investigador que hace búsquedas iterativas.
- `stepwise-research` (`/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/research-worker.md`): Agente trabajador de 286 líneas, usa `WebSearch + WebFetch + Read + Grep + Glob`, modelo `sonnet`. Diseñado para ser lanzado en paralelo por un orquestador.

El plan de implementación del plugin de investigación (en `thoughts/shared/plans/2026-02-19-deep-research-plugin.md`) indica que `stepwise-research` fue creado específicamente porque el agente de `stepwise-web` era "single-agent y limitado". Son implementaciones paralelas, no reutilizadas.

### 4. Dependencia de datos compartida: el sistema thoughts/

El único elemento compartido de forma transversal entre todos los plugins es **el directorio `thoughts/`** como convención de almacenamiento. Cada plugin que genera documentos (research, planes, reportes) los escribe en `thoughts/shared/research/` o `thoughts/shared/plans/`.

La infraestructura del sistema `thoughts/` (inicialización y metadatos) es propiedad exclusiva de `stepwise-core` mediante los scripts:
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/thoughts-management/scripts/thoughts-init`
- `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/thoughts-management/scripts/thoughts-metadata`

El plugin `stepwise-research` escribe reportes en `thoughts/shared/research/` (mencionado en `research/skills/deep-research/SKILL.md` y `research/README.md`), y en su README declara explícitamente: "Reports integrate with the `stepwise-core` thoughts management system". Sin embargo, no llama a los scripts de `stepwise-core`; simplemente sigue la misma convención de directorio. `stepwise-research` tiene su propio script de generación de reportes: `/Users/jorge.castro/mordor/personal/stepwise-dev/research/skills/research-reports/scripts/generate-report`, que crea el directorio `thoughts/shared/research/` con `mkdir -p` si no existe.

### 5. Dependencias de tipo "workflow suggestion" (no funcionales)

Los skill files de `stepwise-core` contienen sugerencias al usuario para invocar otros plugins, pero estas no son dependencias de ejecución:

- `core/skills/implement-plan/SKILL.md`: Sugiere `/stepwise-git:commit` como siguiente paso tras implementar
- `core/skills/research-codebase/SKILL.md`: Sugiere `/stepwise-core:create-plan` como siguiente paso

Estas referencias son texto instructivo para Claude, no llamadas de código.

### 6. Referencias cruzadas en READMEs (documentación, no código)

Cada plugin lista a los demás en su sección "Related Plugins" como mención informativa:

- `core/README.md` menciona stepwise-git, stepwise-web, stepwise-research
- `git/README.md` menciona stepwise-core, stepwise-web
- `web/README.md` menciona stepwise-core, stepwise-git
- `research/README.md` menciona la integración con el sistema thoughts de stepwise-core

### 7. Código compartido: origen HumanLayer

Los archivos con headers SPDX en `stepwise-core` (todos los agentes codebase-*, thoughts-*, y los skills del flujo Research→Plan→Implement→Validate) llevan:
```
SPDX-FileCopyrightText: 2024 humanlayer Authors (original)
SPDX-FileCopyrightText: 2025 Jorge Castro (modifications)
```

Los demás plugins (`stepwise-git`, `stepwise-web`, `stepwise-research`) no llevan estos headers SPDX en sus archivos principales, siendo creaciones originales de Jorge Castro.

El script `thoughts-metadata` también lleva el header SPDX y está basado en `hack/spec_metadata.sh` de HumanLayer.

### 8. No hay código ejecutable compartido entre plugins

No existe ningún directorio `lib/`, `shared/`, ni ningún archivo `.js`, `.py`, o `.ts` compartido entre los cuatro plugins. El único código ejecutable de los plugins son los scripts bash en `core/skills/thoughts-management/scripts/` y `research/skills/research-reports/scripts/generate-report`, que son completamente independientes entre sí.

Las pruebas estructurales en `/Users/jorge.castro/mordor/personal/stepwise-dev/test/plugin-structure-test.sh` validan a cada plugin de forma independiente.

## Architecture Documentation

### Mapa de dependencias entre plugins

```
stepwise-core
  ├── [usa como agente opcional] → stepwise-web:web-search-researcher
  ├── [sugiere al usuario] → /stepwise-git:commit
  └── [provee infraestructura thoughts/ que usa] → stepwise-research (convención)

stepwise-web
  └── [independiente, sin dependencias de código sobre otros plugins]

stepwise-git
  └── [independiente, sin dependencias de código sobre otros plugins]

stepwise-research
  └── [sigue convención thoughts/ de stepwise-core, pero sin llamar sus scripts]
```

### Tipos de relaciones identificadas

| Tipo de relación | Plugins involucrados | Archivo donde se declara |
|---|---|---|
| Dependencia de agente (funcional) | core → web | `core/skills/research-codebase/SKILL.md:35` |
| Convención de datos compartida | core + research | Directorio `thoughts/shared/research/` |
| Sugerencia de workflow (textual) | core → git | `core/skills/implement-plan/SKILL.md:123` |
| Documentación de ecosistema | todos → todos | READMEs de cada plugin |
| Código de origen común (HumanLayer) | Solo archivos de core | Headers SPDX en agentes y skills de core |

## Code References

- `/.claude-plugin/marketplace.json`: Definición del marketplace con los 4 plugins
- `/core/.claude-plugin/plugin.json`: Sin campo dependencies
- `/core/skills/research-codebase/SKILL.md:35`: Única referencia cruzada funcional (stepwise-web)
- `/core/skills/implement-plan/SKILL.md:123`: Sugerencia textual a stepwise-git:commit
- `/core/skills/thoughts-management/scripts/thoughts-init`: Script exclusivo de stepwise-core que inicializa el sistema thoughts/
- `/research/skills/research-reports/scripts/generate-report`: Script de stepwise-research que crea thoughts/shared/research/ de forma autónoma
- `/research/README.md:183`: Declara integración con thoughts management de stepwise-core
- `/web/agents/web-search-researcher.md`: Agente independiente (108 líneas, modelo sonnet)
- `/research/agents/research-worker.md`: Agente paralelo independiente (286 líneas, modelo sonnet)
- `/test/plugin-structure-test.sh`: Tests estructurales de los 4 plugins, validados independientemente

## Open Questions

- ¿Está previsto en el roadmap que `stepwise-research` llame explícitamente a los scripts de `thoughts-management` de `stepwise-core` para inicializar el directorio, en lugar de hacerlo con `mkdir -p`?
- Si `stepwise-web` no está instalado, ¿Claude Code muestra algún error cuando `research-codebase` intenta invocar `stepwise-web:web-search-researcher`, o simplemente no ofrece esa opción?
