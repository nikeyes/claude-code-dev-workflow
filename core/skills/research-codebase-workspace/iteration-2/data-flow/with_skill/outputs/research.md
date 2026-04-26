---
date: 2026-04-26T00:00:00+0000
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "¿Cómo fluyen los datos desde que un usuario invoca /research-codebase hasta que se genera el documento final en thoughts/?"
tags: [research, research-codebase, data-flow, skill, agents, thoughts, workflow, architecture]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Flujo de datos en /research-codebase → thoughts/

**Date**: 2026-04-26T00:00:00+0000
**Researcher**: Jorge Castro
**Git Commit**: a1cdcbb
**Branch**: main
**Repository**: stepwise-dev

## Research Question

¿Cómo fluyen los datos desde que un usuario invoca /research-codebase hasta que se genera el documento final en thoughts/? Quiero entender todos los componentes que intervienen.

## Summary

Cuando un usuario invoca `/stepwise-core:research-codebase [pregunta]`, Claude Code carga el archivo `core/skills/research-codebase/SKILL.md` y lo interpreta como instrucciones de comportamiento. El skill ejecuta 10 pasos secuenciales: recibe la query del usuario, descompone la pregunta, lanza sub-agentes paralelos (locator, analyzer, pattern-finder, thoughts-locator, thoughts-analyzer), espera sus resultados, verifica la existencia de `thoughts/`, ejecuta el script `thoughts-metadata` para obtener metadatos git, sintetiza los hallazgos en un documento Markdown con frontmatter YAML, y lo escribe en `thoughts/shared/research/YYYY-MM-DD-descripcion.md`. Los cinco agentes especializados viven en `core/agents/` y operan con herramientas restringidas (solo Grep/Glob/LS para locators, Read adicional para analyzers). El sistema `thoughts/` es un directorio en disco persistente creado por el script `thoughts-init` con una estructura fija de subdirectorios.

---

## Detailed Findings

### 1. Punto de Entrada: El Skill SKILL.md

**Archivo**: `core/skills/research-codebase/SKILL.md` (233 líneas)

El skill es un archivo Markdown con frontmatter YAML que Claude Code interpreta como un conjunto de instrucciones de comportamiento. El frontmatter define:

```yaml
name: research-codebase
description: Document codebase as-is with thoughts directory for historical context
argument-hint: [research question or topic]
model: opus
disable-model-invocation: true
```

- `model: opus` — el skill se ejecuta en el modelo Claude Opus
- `disable-model-invocation: true` — Claude Code no invoca el modelo directamente por la invocación del skill; Claude interpreta el archivo SKILL.md como prompt de sistema
- `argument-hint` — la query que escribe el usuario al invocar `/research-codebase [query]` llega como `$ARGUMENTS`

**Flujo de control inicial** (`SKILL.md:29-37`):
- Si `$ARGUMENTS` tiene contenido → procede directamente al workflow de 10 pasos
- Si `$ARGUMENTS` está vacío → responde pidiendo la query y espera

---

### 2. Paso 1: Lectura Previa de Archivos Mencionados

**`SKILL.md:41-47`**

Si el usuario menciona archivos específicos (tickets, JSON, docs), Claude los lee con la herramienta `Read` **sin parámetros limit/offset** (lectura completa). Esta lectura ocurre en el contexto principal antes de lanzar sub-agentes. Es obligatoria para garantizar que el contexto principal tenga información completa antes de descomponer la investigación.

---

### 3. Paso 2: Descomposición de la Pregunta

**`SKILL.md:49-55`**

Claude analiza la query y la descompone en áreas de investigación composables:
- Identifica componentes, patrones y conceptos a investigar
- Considera qué directorios, archivos o patrones arquitectónicos son relevantes
- Crea un plan de investigación usando `TodoWrite` para rastrear las subtareas

---

### 4. Paso 3: Los Sub-Agentes Paralelos

**`SKILL.md:57-83`**

Este es el núcleo del sistema. Claude lanza múltiples agentes `Task` en paralelo para investigar aspectos distintos concurrentemente. Los agentes se dividen en dos familias:

#### 4a. Agentes de Codebase (en `core/agents/`)

**codebase-locator** (`core/agents/codebase-locator.md`)
```yaml
tools: Grep, Glob, LS
color: blue
model: haiku
```
- Propósito: Encontrar DÓNDE viven los archivos y componentes
- Solo usa herramientas de búsqueda, no lee contenidos
- Devuelve listados de archivos agrupados por propósito (implementación, tests, config, tipos, ejemplos)
- No analiza ni critica, solo mapea ubicaciones

**codebase-analyzer** (`core/agents/codebase-analyzer.md`)
```yaml
tools: Read, Grep, Glob, LS
color: green
model: sonnet
```
- Propósito: Entender CÓMO funciona el código específico
- Lee archivos para trazar el flujo de datos
- Devuelve análisis con referencias `archivo:línea` precisas
- Documenta puntos de entrada, flujo de datos, patrones arquitectónicos, manejo de errores

**codebase-pattern-finder** (`core/agents/codebase-pattern-finder.md`)
```yaml
tools: Grep, Glob, Read, LS
color: purple
model: sonnet
```
- Propósito: Encontrar ejemplos de patrones existentes con código concreto
- Similar a codebase-locator pero incluye extractos de código
- Devuelve code snippets con contexto y referencias `archivo:línea`

#### 4b. Agentes de Thoughts (en `core/agents/`)

**thoughts-locator** (`core/agents/thoughts-locator.md`)
```yaml
tools: Grep, Glob, LS
color: cyan
model: haiku
```
- Propósito: Descubrir documentos existentes en `thoughts/` relacionados con el tema
- Busca en `thoughts/shared/`, `thoughts/{username}/`, `thoughts/global/`
- Categoriza hallazgos: tickets, research, plans, prs, notas generales
- No lee contenidos en profundidad

**thoughts-analyzer** (`core/agents/thoughts-analyzer.md`)
```yaml
tools: Read, Grep, Glob, LS
color: yellow
model: sonnet
```
- Propósito: Extraer insights de alto valor de documentos específicos en `thoughts/`
- Lee documentos completos y filtra agresivamente el ruido
- Devuelve solo decisiones clave, restricciones críticas, especificaciones técnicas

#### 4c. Agente Web (en `web/agents/`)

**web-search-researcher** (`web/agents/web-search-researcher.md`)
- Solo se usa si el usuario explícitamente pide investigación web
- Si se usa, debe retornar LINKS que se incluyen en el documento final

---

### 5. Paso 4: Síntesis de Resultados

**`SKILL.md:85-93`**

Claude espera a que **TODOS** los sub-agentes completen antes de proceder. Luego:
- Compila todos los resultados (codebase + thoughts)
- Prioriza hallazgos del codebase en vivo como fuente primaria de verdad
- Usa `thoughts/` como contexto histórico suplementario
- Conecta hallazgos entre diferentes componentes
- Incluye rutas de archivo y números de línea concretos
- Destaca patrones, conexiones y decisiones arquitectónicas
- Responde la pregunta del usuario con evidencia concreta

---

### 6. Paso 5: Inicialización del Directorio thoughts/ (si no existe)

**`SKILL.md:95-99`**

Claude verifica si existe `thoughts/`. Si no existe, ejecuta:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init
```

**Script `thoughts-init`** (`core/skills/thoughts-management/scripts/thoughts-init`):
- Usa la variable de entorno `THOUGHTS_USER` (default: `nikey_es`)
- Crea la estructura de directorios:
  ```
  thoughts/
  ├── {username}/
  │   ├── tickets/
  │   └── notes/
  └── shared/
      ├── research/
      ├── plans/
      └── prs/
  ```
- Si `thoughts/README.md` no existe, lo crea con documentación de uso
- Usa `set -euo pipefail` para fallo rápido ante errores

---

### 7. Paso 6: Generación de Metadatos

**`SKILL.md:101-109`**

Claude usa el skill `thoughts-management` para generar metadatos:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
```

**Script `thoughts-metadata`** (`core/skills/thoughts-management/scripts/thoughts-metadata`):
- Genera fecha/hora en múltiples formatos: `DATETIME_TZ`, `DATE_ISO`, `DATE_SHORT`, `FILENAME_TS`
- Ejecuta comandos git con fallbacks si no hay repositorio:
  - `git rev-parse --show-toplevel` → `REPO_ROOT`
  - `basename "$REPO_ROOT"` → `REPO_NAME`
  - `git branch --show-current` → `GIT_BRANCH`
  - `git rev-parse HEAD` → `GIT_COMMIT`
  - `git config user.name` → `GIT_USER`
  - `git config user.email` → `GIT_EMAIL`
- Salida stdout en formato `Clave: Valor` (legible por Claude)
- Usa `>&2` para warnings, no contamina stdout con información de debug

**Naming del archivo** (`SKILL.md:102-109`):
```
thoughts/shared/research/YYYY-MM-DD-descripcion.md          # sin ticket
thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-descripcion.md # con ticket
```

---

### 8. Paso 7: Generación del Documento de Investigación

**`SKILL.md:111-169`**

Claude genera el documento Markdown con estructura fija:

```markdown
---
date: [ISO datetime con timezone]
researcher: [nombre del usuario git]
git_commit: [hash del commit actual]
branch: [rama actual]
repository: [nombre del repositorio]
topic: "[Query del usuario]"
tags: [research, codebase, nombres-de-componentes-relevantes]
status: complete
last_updated: [YYYY-MM-DD]
last_updated_by: [nombre del investigador]
---

# Research: [Query del usuario]

## Research Question
## Summary
## Detailed Findings
  ### [Componente/Área 1]
  ### [Componente/Área 2]
## Code References
## Architecture Documentation
## Historical Context (from thoughts/)
## Related Research
## Open Questions
```

**Regla crítica**: Nunca escribir el documento con valores placeholder. Todos los campos del frontmatter deben tener valores reales obtenidos en el paso 6.

---

### 9. Paso 8: GitHub Permalinks (Opcional)

**`SKILL.md:171-177`**

Si el repositorio está en rama `main`/`master` o el commit está pusheado:
1. `gh repo view --json owner,name` → obtiene `owner` y `name`
2. Genera permalinks: `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`
3. Reemplaza referencias locales de archivos con permalinks en el documento

---

### 10. Paso 9: Presentación al Usuario

**`SKILL.md:179-195`**

Claude presenta un resumen conciso al usuario con:
- Ruta del documento generado: `thoughts/shared/research/[filename].md`
- Hallazgos clave con referencias de archivos
- Próximos pasos del workflow: revisión → `/stepwise-core:create-plan` → preguntas de seguimiento
- Consejo de usar `/clear` para liberar contexto antes de planificar

---

### 11. Paso 10: Preguntas de Seguimiento

**`SKILL.md:197-204`**

Para preguntas de seguimiento del usuario:
- Agrega al mismo documento sin crear uno nuevo
- Actualiza `last_updated` y `last_updated_by` en el frontmatter
- Agrega `last_updated_note: "Added follow-up research for [descripción]"`
- Crea una nueva sección: `## Follow-up Research [timestamp]`
- Lanza nuevos sub-agentes según sea necesario

---

## Architecture Documentation

### Modelo de Plugins

El sistema opera como un plugin de Claude Code (`stepwise-core`). La configuración del plugin está en `core/.claude-plugin/plugin.json`:
```json
{
  "name": "stepwise-core",
  "version": "1.0.1"
}
```

El plugin forma parte de un marketplace de 4 plugins definido en `.claude-plugin/marketplace.json`. Claude Code resuelve `${CLAUDE_PLUGIN_ROOT}` a la ruta de instalación del plugin, permitiendo que los scripts se ubiquen de forma relativa al plugin.

### Estructura de Archivos del Sistema

```
core/
├── .claude-plugin/
│   └── plugin.json               # Metadatos del plugin stepwise-core
├── agents/
│   ├── codebase-locator.md       # Agente: encuentra archivos (haiku, Grep/Glob/LS)
│   ├── codebase-analyzer.md      # Agente: analiza implementación (sonnet, Read+Grep+Glob+LS)
│   ├── codebase-pattern-finder.md# Agente: encuentra patrones con código (sonnet, Grep+Glob+Read+LS)
│   ├── thoughts-locator.md       # Agente: localiza docs en thoughts/ (haiku, Grep/Glob/LS)
│   └── thoughts-analyzer.md      # Agente: extrae insights de thoughts/ (sonnet, Read+Grep+Glob+LS)
└── skills/
    ├── research-codebase/
    │   └── SKILL.md              # Skill principal: 233 líneas, 10 pasos
    └── thoughts-management/
        ├── SKILL.md              # Skill de gestión de thoughts/
        └── scripts/
            ├── thoughts-init     # Script bash: crea estructura thoughts/
            └── thoughts-metadata # Script bash: genera metadatos git
```

### Separación de Responsabilidades por Modelo

| Componente | Modelo | Herramientas | Responsabilidad |
|---|---|---|---|
| research-codebase (skill) | opus | Todas | Orquestación, síntesis, generación del documento |
| codebase-locator | haiku | Grep, Glob, LS | Mapeo rápido de ubicaciones |
| thoughts-locator | haiku | Grep, Glob, LS | Descubrimiento en thoughts/ |
| codebase-analyzer | sonnet | Read, Grep, Glob, LS | Análisis profundo de implementación |
| codebase-pattern-finder | sonnet | Grep, Glob, Read, LS | Extracción de patrones con código |
| thoughts-analyzer | sonnet | Read, Grep, Glob, LS | Extracción de insights de documentos |

Los agentes más simples (locators) usan `haiku` (menor costo, mayor velocidad). Los más complejos (analyzers) usan `sonnet`. El skill orquestador usa `opus` para síntesis de alta calidad.

### Flujo de Datos Completo (Diagrama)

```
Usuario invoca /stepwise-core:research-codebase [query]
        │
        ▼
[Claude Code carga SKILL.md como prompt de sistema]
        │
        ▼
[Paso 1] ¿Hay archivos mencionados? → Read (sin limit/offset)
        │
        ▼
[Paso 2] Descomposición + TodoWrite
        │
        ▼
[Paso 3] Lanzamiento paralelo de sub-agentes
    ┌───┴──────────────────────────────────────────────┐
    │                    │                    │         │
    ▼                    ▼                    ▼         ▼
codebase-locator  codebase-analyzer  thoughts-locator  thoughts-analyzer
(haiku)           (sonnet)           (haiku)           (sonnet)
Grep/Glob/LS      Read+Grep+Glob+LS  Grep/Glob/LS      Read+Grep+Glob+LS
    │                    │                    │         │
    └───────┬────────────┘                    └───┬─────┘
            │                                    │
            ▼                                    ▼
    [Hallazgos de codebase]          [Contexto histórico de thoughts/]
            │                                    │
            └───────────────┬────────────────────┘
                            │
                            ▼
[Paso 4] Síntesis en contexto principal del skill
                            │
                            ▼
[Paso 5] ¿Existe thoughts/? → No → bash thoughts-init → crea estructura
                            │
                            ▼
[Paso 6] bash thoughts-metadata → obtiene fecha + git metadata
                            │
                            ▼
[Paso 7] Genera documento .md con frontmatter YAML
         → escribe en thoughts/shared/research/YYYY-MM-DD-descripcion.md
                            │
                            ▼
[Paso 8] ¿Rama main/commit pusheado? → gh repo view → genera permalinks
                            │
                            ▼
[Paso 9] Presenta resumen al usuario
```

### Directorio thoughts/ Como Almacenamiento Persistente

El directorio `thoughts/` funciona como una base de datos de documentos persistente en el sistema de archivos local. La estructura observada en el repositorio actual:

```
thoughts/
├── README.md
├── .gitignore
├── nikey_es/
│   └── notes/
│       ├── claude-code-skills.md
│       ├── create_deep_reasearch_plugin_research.md
│       ├── deep-research-claude-code-references.md
│       └── plugins-claude-code.md
├── shared/
│   ├── plans/
│   │   ├── 2025-11-11-convert-to-plugin.md
│   │   ├── 2025-11-13-prevent-6000-token-limit-error.md
│   │   ├── 2025-11-13-simplify-tests.md
│   │   └── 2026-02-19-deep-research-plugin.md
│   └── research/
│       ├── 2025-11-12-testing-infrastructure.md
│       ├── 2025-12-28-advanced-context-engineering-improvements.md
│       └── 2025-12-28-humanlayer-comparison-improvement-opportunities.md
└── searchable/              # Hardlinks para grep eficiente
    ├── nikey_es/
    └── shared/
```

Los documentos de investigación se almacenan en `thoughts/shared/research/`. El subdirectorio `searchable/` contiene hardlinks de los mismos archivos para búsqueda eficiente con `grep -r`.

---

## Code References

- `core/skills/research-codebase/SKILL.md:1-7` — Frontmatter del skill (model, disable-model-invocation)
- `core/skills/research-codebase/SKILL.md:29-37` — Lógica de inicialización con $ARGUMENTS
- `core/skills/research-codebase/SKILL.md:41-47` — Lectura previa de archivos mencionados (sin limit/offset)
- `core/skills/research-codebase/SKILL.md:57-83` — Definición y uso de los 5 agentes especializados
- `core/skills/research-codebase/SKILL.md:85-93` — Síntesis de resultados (esperar TODOS los agentes)
- `core/skills/research-codebase/SKILL.md:95-99` — Inicialización de thoughts/ con thoughts-init
- `core/skills/research-codebase/SKILL.md:101-109` — Naming del archivo de salida (con/sin ticket)
- `core/skills/research-codebase/SKILL.md:111-169` — Template completo del documento de investigación
- `core/skills/research-codebase/SKILL.md:171-177` — Generación de GitHub permalinks
- `core/skills/research-codebase/SKILL.md:197-204` — Manejo de preguntas de seguimiento
- `core/agents/codebase-locator.md:1-7` — Frontmatter del agente (haiku, Grep/Glob/LS)
- `core/agents/codebase-analyzer.md:1-7` — Frontmatter del agente (sonnet, Read+Grep+Glob+LS)
- `core/agents/codebase-pattern-finder.md:1-7` — Frontmatter del agente (sonnet, Grep+Glob+Read+LS)
- `core/agents/thoughts-locator.md:1-7` — Frontmatter del agente (haiku, Grep/Glob/LS)
- `core/agents/thoughts-analyzer.md:1-7` — Frontmatter del agente (sonnet, Read+Grep+Glob+LS)
- `core/skills/thoughts-management/SKILL.md:29-49` — Comandos de init y metadata
- `core/skills/thoughts-management/SKILL.md:83-96` — Estructura del directorio thoughts/
- `core/skills/thoughts-management/scripts/thoughts-init:1-82` — Script completo de inicialización
- `core/skills/thoughts-management/scripts/thoughts-metadata:1-52` — Script completo de metadatos git
- `.claude-plugin/marketplace.json` — Definición del marketplace con 4 plugins
- `core/.claude-plugin/plugin.json` — Metadatos del plugin stepwise-core v1.0.1

---

## Historical Context (from thoughts/)

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Investigación profunda sobre la estrategia FIC. Confirma que el patrón de sub-agentes paralelos en research-codebase implementa aislamiento de contexto (agentes consumen 5,000-10,000 tokens en exploración, el agente padre recibe solo resultados sintetizados). También documenta el sistema `thoughts/searchable/` con hardlinks.
- `thoughts/shared/research/2025-11-12-testing-infrastructure.md` — Documenta la infraestructura de testing del proyecto. Relevante porque confirma que la validación de skills/agents requiere prueba manual en Claude Code runtime (no hay tests automáticos para el comportamiento del skill).
- `thoughts/shared/plans/2025-11-13-prevent-6000-token-limit-error.md` — Plan para manejar el límite de 6000 tokens de output. Indica que el skill fue modificado para escribir el documento incrementalmente durante la síntesis en lugar de un output masivo al final.

---

## Related Research

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Análisis de contexto FIC, confirma arquitectura del skill
- `thoughts/shared/research/2025-11-12-testing-infrastructure.md` — Infraestructura de testing

---

## Open Questions

1. **¿Cómo resuelve Claude Code `${CLAUDE_PLUGIN_ROOT}`?** — La variable se expande en tiempo de ejecución del skill. No hay documentación en el repositorio sobre cómo Claude Code inyecta esta variable.

2. **¿Cuándo exactamente se escribe el archivo en disco?** — El SKILL.md indica que el documento se genera en el paso 7, pero no especifica si Claude usa la herramienta `Write` directamente o si existe algún mecanismo de buffer. El plan `2025-11-13-prevent-6000-token-limit-error.md` sugiere escritura incremental.

3. **¿Cuál es el comportamiento exacto de `disable-model-invocation: true`?** — El frontmatter del skill lo establece pero el repositorio no contiene documentación sobre cómo Claude Code interpreta esta directiva.

4. **¿Existe algún mecanismo de sincronización del directorio `searchable/`?** — La investigación existente menciona un script `thoughts-sync` (147 líneas) que gestiona hardlinks, pero ese script no existe en la versión actual del repositorio (no encontrado en `core/skills/thoughts-management/scripts/`).
