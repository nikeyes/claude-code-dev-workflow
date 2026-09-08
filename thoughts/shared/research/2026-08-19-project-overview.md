---
date: 2026-08-19T09:26:39+0000
researcher: Jorge Castro
git_commit: 0ef62fc9f7e23c9a979b109ffcd61fc423c445aa
branch: feat/codex
repository: stepwise-dev
topic: "¿Qué hace este proyecto?"
tags: [research, codebase, workflow, plugins, thoughts, codex]
status: complete
last_updated: 2026-08-19
last_updated_by: Jorge Castro
---

# Research: Visión general del proyecto

## Research Question

¿Qué hace el proyecto contenido en este repositorio?

## Summary

`stepwise-dev` es una suite local de herramientas para organizar el desarrollo asistido por IA. No es una aplicación de usuario final: empaqueta skills, agentes especializados y scripts que guían un ciclo **Research → Plan → Implement → Validate**, conservando investigación, planes y decisiones en `thoughts/` para que sobrevivan entre sesiones y limpiezas de contexto.

Se distribuye como cuatro plugins independientes para Claude Code y ofrece una capa de compatibilidad con OpenAI Codex. El código fuente de las skills es compartido entre ambos entornos; las definiciones de agentes para Codex se generan como TOML.

## Detailed Findings

### Flujo de trabajo principal

El plugin `stepwise-core` contiene las skills que investigan el código existente, crean e iteran planes, implementan el plan por fases y validan el resultado. También incorpora prácticas auxiliares como TDD, bug discovery, división de historias y migraciones en pasos pequeños (`core/README.md:7-25`).

La fase de investigación documenta el repositorio tal como existe, delega localización, análisis, búsqueda de patrones e historial a agentes especializados y guarda el informe en `thoughts/shared/research/` (`core/skills/research-codebase/SKILL.md:13-81`). La creación de planes consume investigación previa (`core/skills/create-plan/SKILL.md:46-93`); la implementación orquesta trabajo por fases y técnicas de prueba (`core/skills/implement-plan/SKILL.md:29-119`); la validación compara el plan con archivos y pruebas reales (`core/skills/validate-plan/SKILL.md:11-57`).

### Arquitectura de plugins

El marketplace declara cuatro paquetes (`.claude-plugin/marketplace.json:10-38`):

- `stepwise-core`: workflow principal, gestión de `thoughts/` y prácticas de desarrollo.
- `stepwise-git`: creación de commits y revisión de comentarios de pull requests.
- `stepwise-web`: agente especializado en búsqueda web.
- `stepwise-research`: investigación profunda multiagente con workers y verificación de citas.

Las skills son directorios con un `SKILL.md` declarativo; los agentes son archivos Markdown con frontmatter y responsabilidades estrechas. Por ejemplo, `codebase-locator` solo localiza y clasifica archivos, mientras otros agentes explican funcionamiento, encuentran patrones o examinan el historial (`core/agents/codebase-locator.md:1-41`).

### Memoria persistente en thoughts

`thoughts-management` administra una estructura con notas y tickets personales, además de documentos compartidos de investigación, planes y PRs (`core/skills/thoughts-management/SKILL.md:82-109`). `thoughts-init` crea esas carpetas y su README (`core/skills/thoughts-management/scripts/thoughts-init:29-79`); `thoughts-metadata` obtiene fecha, autor y estado Git para el frontmatter de los documentos (`core/skills/thoughts-management/scripts/thoughts-metadata:19-50`).

Este almacenamiento permite limpiar el contexto entre fases sin perder el conocimiento acumulado.

### Compatibilidad con Claude Code y Codex

Claude Code consume los cuatro plugins desde el marketplace. Para Codex, `codex/install.sh` enlaza las skills en `~/.agents/skills/` y copia agentes generados a `~/.codex/agents/` (`codex/install.sh:7-37`). `codex/transpile-agents.sh` transforma las definiciones Markdown de agentes a TOML, incluyendo equivalencias de modelos y sandbox (`codex/transpile-agents.sh:25-75`).

Así, las skills mantienen una única fuente de verdad y solo los nueve agentes Codex son artefactos generados.

### Pruebas y automatización

El `Makefile` ofrece pruebas funcionales, comprobaciones estáticas, validación de compatibilidad Codex e instalación local (`Makefile:42-70`, `Makefile:85-140`). Los tests Bash verifican:

- creación de la estructura y metadatos de `thoughts/` (`test/thoughts-structure-test.sh:31-70`);
- manifiestos, plugins, skills, agentes y scripts (`test/plugin-structure-test.sh:60-160`);
- transpilación e instalación Codex en un entorno temporal (`test/codex-test.sh:31-161`).

Las skills y los agentes también requieren validación manual en sus respectivos entornos, porque gran parte de su comportamiento son instrucciones para el modelo.

## Code References

- `README.md:7-22` — propósito general y flujo por fases.
- `.claude-plugin/marketplace.json:10-38` — catálogo de los cuatro plugins.
- `core/README.md:7-25` — skills y agentes de `stepwise-core`.
- `core/skills/research-codebase/SKILL.md:13-81` — investigación y persistencia del informe.
- `core/skills/create-plan/SKILL.md:46-93` — preparación y exploración para planes.
- `core/skills/implement-plan/SKILL.md:29-119` — orquestación de implementación.
- `core/skills/validate-plan/SKILL.md:11-57` — validación contra código y pruebas.
- `core/skills/thoughts-management/scripts/thoughts-init:29-79` — inicialización de `thoughts/`.
- `codex/install.sh:7-37` — instalación para Codex.
- `codex/transpile-agents.sh:25-75` — generación de agentes TOML.
- `Makefile:42-140` — comandos de test, checks y CI.

## Architecture Documentation

```text
Marketplace
├── stepwise-core      Research → Plan → Implement → Validate
│   ├── skills
│   ├── agentes especializados
│   └── thoughts-management ──> thoughts/shared/{research,plans,prs}
├── stepwise-git       commits y comentarios de PR
├── stepwise-web       búsqueda web
└── stepwise-research  investigación profunda multiagente

Fuentes Markdown ──> Claude Code plugins
       └───────────> Codex: skills enlazadas + agentes TOML generados
```

## Historical Context (from thoughts/)

El proyecto nació como un workflow local y posteriormente se empaquetó como plugin distribuible para Claude Code, procurando conservar sus comandos, agentes y scripts (`thoughts/shared/plans/2025-11-11-convert-to-plugin.md:3-6`, `:71-90`).

La separación por fases y el uso de agentes especializados responden a una estrategia de gestión de contexto: cada fase consume el artefacto persistido por la anterior, mientras `/clear` reduce el contexto activo (`thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md:95-154`, `:171-192`).

Más tarde se añadió `stepwise-research` para investigación web profunda multiagente (`thoughts/shared/plans/2026-02-19-deep-research-plugin.md:61-127`) y una capa Codex que comparte las mismas skills y genera únicamente los agentes TOML (`thoughts/shared/plans/2026-08-19-codex-compatibility.md:24-55`, `:100-150`). Los planes históricos documentan intención y evolución; el código vivo descrito arriba es la fuente prioritaria del estado actual.

## Related Research

- `thoughts/shared/research/2026-08-19-research-codebase-skill-purpose.md`
- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md`
- `thoughts/shared/research/2025-11-12-testing-infrastructure.md`
- `thoughts/shared/plans/2025-11-11-convert-to-plugin.md`
- `thoughts/shared/plans/2026-02-19-deep-research-plugin.md`
- `thoughts/shared/plans/2026-08-19-codex-compatibility.md`

## Open Questions

Ninguna para esta visión general.

## Follow-up Research 2026-08-19 13:13 CEST

Se volvió a verificar la pregunta sobre el commit `0ef62fc9f7e23c9a979b109ffcd61fc423c445aa` mediante tres líneas de investigación en paralelo: localización de componentes, análisis del workflow y consulta del contexto histórico en `thoughts/`.

La verificación confirma la descripción anterior: este repositorio no implementa una aplicación de negocio, sino una suite de tooling para desarrollo asistido por IA. Sus cuatro plugins empaquetan skills, agentes y scripts para el ciclo **Research → Plan → Implement → Validate**, operaciones Git, búsqueda web e investigación profunda multiagente (`README.md:35-75`, `.claude-plugin/marketplace.json:10-38`). La memoria entre fases se conserva en `thoughts/`, y la capa `codex/` permite reutilizar las skills en Codex instalando enlaces y agentes TOML generados (`README.md:126-145`, `codex/install.sh:7-37`).

Las comprobaciones automatizadas del repositorio cubren la estructura de `thoughts/`, la integridad de los cuatro plugins y la compatibilidad de los artefactos Codex (`Makefile:42-140`). No aparecieron discrepancias entre el código vivo, los manifiestos y el contexto histórico consultado.
