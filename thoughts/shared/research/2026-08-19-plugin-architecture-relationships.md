---
date: 2026-08-19T10:15:45+0000
researcher: Jorge Castro
git_commit: 0ef62fc9f7e23c9a979b109ffcd61fc423c445aa
branch: feat/codex
repository: stepwise-dev
topic: "Investiga cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research. ¿Comparten código? ¿Hay dependencias cruzadas?"
tags: [research, codebase, plugin-architecture, stepwise-core, stepwise-git, stepwise-web, stepwise-research, cross-plugin]
status: complete
last_updated: 2026-08-19
last_updated_by: Jorge Castro
---

# Research: Relaciones entre los 4 plugins de stepwise-dev

## Research Question

¿Cómo se relacionan los 4 plugins entre sí: stepwise-core, stepwise-git, stepwise-web, stepwise-research? ¿Comparten código? ¿Hay dependencias cruzadas?

## Summary

Los cuatro plugins son unidades **independientes** sin declaraciones formales de dependencia entre ellos. Sus `plugin.json` no declaran `dependencies`, `requires` ni `peerDependencies`. Las relaciones existentes son exclusivamente de dos tipos:

1. **Referencias en prosa** dentro de archivos SKILL.md: un skill puede mencionar un agente de otro plugin como paso opcional o sugerencia de siguiente paso.
2. **Agregación en la capa Codex** (`codex/`): scripts de build e instalación que referencian los cuatro plugins juntos para el entorno OpenAI Codex.

No existe ningún archivo, script ni código compartido entre plugins distintos. La convención `${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}` se usa de forma independiente dentro de cada plugin que tiene scripts.

## Detailed Findings

### 1. Plugin manifests — sin dependencias formales

Los cuatro archivos `plugin.json` contienen únicamente campos de metadatos (`name`, `version`, `description`, `author`, `keywords`). Ninguno declara dependencia sobre otro:

- `core/.claude-plugin/plugin.json`
- `git/.claude-plugin/plugin.json`
- `web/.claude-plugin/plugin.json`
- `research/.claude-plugin/plugin.json`

El `marketplace.json` en `/.claude-plugin/marketplace.json` lista los cuatro plugins como pares, sin relaciones de dependencia entre ellos.

### 2. Única referencia de agente cross-plugin en runtime

La única referencia en runtime de un skill a un agente de otro plugin está en:

**`core/skills/research-codebase/SKILL.md:37`**
```
- **web-search-researcher** (Claude Code: `stepwise-web:web-search-researcher`) — external web research; only *spawn* it if the user explicitly asked...
```

Esta referencia es **opcional y condicional**: el skill `research-codebase` (stepwise-core) solo invoca al agente `web-search-researcher` (stepwise-web) si el usuario lo pide explícitamente.

### 3. Referencias de sugerencia de siguiente paso (no runtime)

**`core/skills/implement-plan/SKILL.md:163`**
```
- Use the `commit` skill (Claude Code: `/stepwise-git:commit`) to create git commits for the changes
```

Esta referencia aparece en la sección de "Completion" como sugerencia, no como dependencia de ejecución.

### 4. Scripts compartidos — solo dentro de stepwise-core

Los scripts de `thoughts-management` viven en `core/skills/thoughts-management/scripts/` y son llamados por otros skills **del mismo plugin** (stepwise-core):

| Skill que llama | Script | Archivo:línea |
|---|---|---|
| `thoughts-management` | `thoughts-init`, `thoughts-metadata` | `core/skills/thoughts-management/SKILL.md:30,49,77` |
| `research-codebase` | `thoughts-init`, `thoughts-metadata` | `core/skills/research-codebase/SKILL.md:45,50` |
| `create-plan` | `thoughts-init` | `core/skills/create-plan/SKILL.md:182` |
| `iterate-plan` | `thoughts-init` | `core/skills/iterate-plan/SKILL.md:131` |

Ningún skill de `stepwise-git`, `stepwise-web` ni `stepwise-research` llama a estos scripts.

### 5. Convención `${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}` por plugin

Cada plugin que tiene scripts usa esta convención de forma independiente:

- **stepwise-core**: para `thoughts-management/scripts/thoughts-init` y `thoughts-metadata`
- **stepwise-research**: para `deep-research/scripts/generate-report`
- **stepwise-git**: sin scripts, sin uso de `${CLAUDE_PLUGIN_ROOT}`
- **stepwise-web**: sin scripts, sin uso de `${CLAUDE_PLUGIN_ROOT}`

El `Makefile` (líneas 102–112) valida con `check-codex` que todas las referencias a `${CLAUDE_PLUGIN_ROOT}` incluyan el fallback `:-$HOME/.agents`.

### 6. Relaciones internas por plugin

**stepwise-core** (intra-plugin):
- `create-plan/SKILL.md:145` invoca `grill-me` (mismo plugin)
- `implement-plan/SKILL.md:34` delega en `tdd`, `bugmagnet`, `test-desiderata` (mismo plugin)
- `research-codebase`, `create-plan`, `iterate-plan` usan los scripts de `thoughts-management` (mismo plugin)

**stepwise-research** (intra-plugin):
- `deep-research/SKILL.md:70,211` lanza agentes `research-worker` y `citation-analyst`
- `research-lead.md:78` lanza `research-worker`

**stepwise-git** y **stepwise-web**: sin referencias a otros plugins.

### 7. Capa Codex — agregación cross-plugin en build time

La capa de compatibilidad Codex en `codex/` agrega los cuatro plugins en tiempo de build/instalación:

**`codex/transpile-agents.sh:32`** — genera TOMLs a partir de agentes de 3 plugins:
```bash
for src in "$REPO_ROOT"/core/agents/*.md "$REPO_ROOT"/research/agents/*.md "$REPO_ROOT"/web/agents/*.md; do
```
(git/ ausente porque stepwise-git no tiene agentes)

**`codex/install.sh:14`** — instala skills de 3 plugins:
```bash
for skill in "$REPO_ROOT"/core/skills/*/ "$REPO_ROOT"/git/skills/*/ "$REPO_ROOT"/research/skills/*/; do
```
(web/ ausente porque stepwise-web no tiene skills, solo un agente)

Los 9 TOMLs generados en `codex/agents/` corresponden a:
- stepwise-core (5): `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, `thoughts-locator`, `thoughts-analyzer`
- stepwise-research (3): `research-lead`, `research-worker`, `citation-analyst`
- stepwise-web (1): `web-search-researcher`

## Code References

| Archivo | Línea | Tipo de referencia |
|---|---|---|
| `core/skills/research-codebase/SKILL.md` | 37 | Cross-plugin: stepwise-core → stepwise-web (opcional) |
| `core/skills/implement-plan/SKILL.md` | 163 | Cross-plugin: stepwise-core → stepwise-git (sugerencia) |
| `core/skills/research-codebase/SKILL.md` | 45, 50 | Intra-plugin: script thoughts-management |
| `core/skills/create-plan/SKILL.md` | 182 | Intra-plugin: script thoughts-management |
| `core/skills/iterate-plan/SKILL.md` | 131 | Intra-plugin: script thoughts-management |
| `research/skills/deep-research/SKILL.md` | 70, 211 | Intra-plugin: agentes research-worker, citation-analyst |
| `codex/transpile-agents.sh` | 32 | Build-time: agrega core + research + web |
| `codex/install.sh` | 14 | Install-time: agrega core + git + research |
| `Makefile` | 6, 44–49, 77–112 | CI/build: valida y opera sobre los 4 plugins |

## Architecture Documentation

```
stepwise-core ──(runtime, opcional)──▶ stepwise-web
stepwise-core ──(sugerencia)──────────▶ stepwise-git
stepwise-research ─────────────────────── (autónomo)
stepwise-git ──────────────────────────── (autónomo)
stepwise-web ──────────────────────────── (autónomo)

codex/ (build-time)
  transpile-agents.sh ──▶ core + research + web (agentes)
  install.sh ────────────▶ core + git + research (skills)
```

**Resumen por plugin:**
- **stepwise-core**: el más conectado; referencia opcionalmente a stepwise-web, sugiere stepwise-git, y sus scripts son usados internamente por varios de sus propios skills.
- **stepwise-research**: completamente autónomo; sus skills y agentes se comunican solo entre sí.
- **stepwise-git**: autónomo; no referencia ni es referenciado en runtime por ningún otro plugin.
- **stepwise-web**: autónomo; expone solo un agente que stepwise-core puede invocar opcionalmente.

**Dependencia compartida de filesystem:**
El directorio `thoughts/` es una convención de filesystem usada tanto por stepwise-core (research, plans) como por stepwise-research (deep-research reports). No es una dependencia de código sino una convención de paths en prosa.

## Historical Context (from thoughts/)

No se encontraron documentos previos en `thoughts/` sobre este tema.

## Related Research

- `AGENTS.md` — documentación de la arquitectura multi-plugin y convenciones Codex
- `README.md` — tabla de workflow cross-plugin (líneas 182–188)
- `Makefile` — targets que muestran las relaciones de build entre plugins
- `codex/transpile-agents.sh` y `codex/install.sh` — capa de compatibilidad Codex

## Open Questions

Ninguna. Todos los aspectos de la pregunta quedaron resueltos con el análisis del código fuente.
