---
date: 2026-04-26T01:05:10+0000
researcher: Jorge Castro
git_commit: a1cdcbb9417f75144272adc1ba45ff14376102d1
branch: main
repository: stepwise-dev
topic: "¿Cómo fluyen los datos desde que un usuario invoca /research-codebase hasta que se genera el documento final en thoughts/?"
tags: [research, codebase, research-codebase, data-flow, skill, agents, thoughts, workflow, plugin-architecture]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Flujo de datos en /research-codebase → thoughts/

## Research Question

¿Cómo fluyen los datos desde que un usuario invoca /research-codebase hasta que se genera el documento final en thoughts/? Quiero entender todos los componentes que intervienen.

## Summary

Cuando un usuario invoca `/stepwise-core:research-codebase [query]`, Claude Code localiza y carga `core/skills/research-codebase/SKILL.md` desde el plugin cache (`~/.claude/plugins/cache/stepwise-dev/stepwise-core/1.0.1/`), interpretando su contenido como instrucciones de comportamiento del modelo. El flujo atraviesa 10 pasos: validación de la query, lectura de archivos mencionados, descomposición del problema, lanzamiento paralelo de hasta 5 sub-agentes especializados (codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer), síntesis de resultados en el contexto principal, inicialización opcional de `thoughts/` via el script `thoughts-init`, obtención de metadatos git via `thoughts-metadata`, generación del documento con frontmatter YAML, enriquecimiento opcional con GitHub permalinks, y presentación al usuario. El documento final se escribe en `thoughts/shared/research/YYYY-MM-DD-descripcion.md` en el directorio de trabajo actual del proyecto del usuario.

## Detailed Findings

### 1. Punto de Entrada: Invocación del Skill

**Archivo**: `core/skills/research-codebase/SKILL.md` (86 líneas en source, mismo contenido en plugin cache)
**Plugin cache**: `/Users/jorge.castro/.claude/plugins/cache/stepwise-dev/stepwise-core/1.0.1/skills/research-codebase/SKILL.md`

El skill se instala como parte del plugin `stepwise-core` desde el marketplace `stepwise-dev`. El `plugin.json` en `core/.claude-plugin/plugin.json` define el plugin con `name: "stepwise-core"`, lo que crea el namespace para la invocación `/stepwise-core:research-codebase`.

El frontmatter YAML del skill (`SKILL.md:1-7`) define el comportamiento del runtime:

```yaml
name: research-codebase
description: Document codebase as-is with thoughts directory for historical context
argument-hint: [research question or topic]
model: sonnet
disable-model-invocation: true
```

- `model: sonnet` — el skill se ejecuta usando Claude Sonnet
- `disable-model-invocation: true` — Claude Code no invoca el modelo directamente por la invocación del slash command; el archivo SKILL.md actúa como el prompt de sistema que guía el comportamiento del modelo actual
- `argument-hint` — documenta que la query del usuario se pasa como `$ARGUMENTS` al texto del skill

La query que el usuario escribe al invocar `/stepwise-core:research-codebase [query]` llega disponible como la variable `$ARGUMENTS` dentro del contenido del SKILL.md.

---

### 2. Validación de la Query (SKILL.md:21-26)

El primer procesamiento que ocurre es la evaluación de `$ARGUMENTS`:

- Si `$ARGUMENTS` está **vacío** → responde al usuario pidiendo su pregunta de investigación y espera
- Si `$ARGUMENTS` es **vago o ambiguo** (ej. "investigate tests", "look at the code") → pide al usuario que clarifique el alcance antes de proceder. Una buena pregunta de investigación nombra un componente específico, flujo o concepto
- Si `$ARGUMENTS` es **claro** → procede directamente sin interrupciones

---

### 3. Lectura Previa de Archivos Mencionados (SKILL.md:29-31)

Si el usuario menciona archivos específicos en la query (por nombre, ruta, o referencia a tickets), Claude los lee completamente en el contexto principal **antes** de hacer cualquier otra cosa. La instrucción explícita es leerlos sin parámetros `limit/offset`, garantizando lectura completa. Este paso ancla el contexto principal con información de archivos clave antes de delegar a sub-agentes.

---

### 4. Investigación con Sub-Agentes (SKILL.md:29-39)

Este es el núcleo del sistema de recolección de datos. El skill instruye a Claude a usar "whatever approach makes sense — read files directly, spawn sub-agents for parallel research, or both". Los sub-agentes disponibles son:

#### 4a. Agentes de Codebase (definidos en `core/agents/`)

**codebase-locator** (`core/agents/codebase-locator.md`):
```yaml
tools: Grep, Glob, LS
color: blue
model: haiku
```
Especializado en encontrar DÓNDE viven los archivos. Usa solo herramientas de búsqueda y localización, no lee contenidos. Devuelve listados de archivos agrupados por propósito: implementación, tests, configuración, tipos, ejemplos. Usa `haiku` (rápido, económico) porque solo hace búsquedas superficiales.

**codebase-analyzer** (`core/agents/codebase-analyzer.md`):
```yaml
tools: Read, Grep, Glob, LS
color: green
model: sonnet
```
Especializado en entender CÓMO funciona el código específico. Lee archivos completos para trazar el flujo de datos, identificar patrones arquitectónicos y documentar contratos entre componentes. Devuelve análisis con referencias `archivo:línea` precisas. Usa `sonnet` porque requiere razonamiento profundo.

**codebase-pattern-finder** (`core/agents/codebase-pattern-finder.md`):
```yaml
tools: Grep, Glob, Read, LS
color: purple
model: sonnet
```
Especializado en encontrar ejemplos de patrones existentes con código concreto. Combina búsqueda (como locator) con lectura y extracción de código (como analyzer). Devuelve snippets de código con contexto y referencias `archivo:línea`.

#### 4b. Agentes de Thoughts (definidos en `core/agents/`)

**thoughts-locator** (`core/agents/thoughts-locator.md`):
```yaml
tools: Grep, Glob, LS
color: cyan
model: haiku
```
Especializado en descubrir documentos existentes en `thoughts/` relacionados con el tema. Busca en `thoughts/shared/`, `thoughts/{username}/`, `thoughts/global/`. Categoriza hallazgos sin leer contenidos en profundidad. Usa `haiku` para velocidad.

**thoughts-analyzer** (`core/agents/thoughts-analyzer.md`):
```yaml
tools: Read, Grep, Glob, LS
color: yellow
model: sonnet
```
Especializado en extraer insights de alto valor de documentos específicos en `thoughts/`. Lee documentos completos y filtra agresivamente, devolviendo solo decisiones clave, restricciones críticas y especificaciones técnicas. Usa `sonnet` para síntesis de calidad.

#### 4c. Agente Web (opcional)

**web-search-researcher** (`web/agents/web-search-researcher.md` en el plugin `stepwise-web`):
Solo se invoca si el usuario explícitamente pide investigación web. Cuando se usa, retorna links que se incluyen en el documento final.

El skill instruye: "When the question spans multiple components, spawn agents in parallel for efficiency." Los agentes se lanzan concurrentemente via la herramienta `Task`, reduciendo el tiempo total de investigación y manteniendo el contexto principal ligero (los agentes consumen tokens en sus propios contextos aislados; el agente padre recibe solo los resultados sintetizados).

---

### 5. Síntesis de Resultados (SKILL.md:39-41)

Después de que todos los sub-agentes completan, el skill sintetiza los hallazgos en el contexto principal:
- Prioriza hallazgos del codebase en vivo sobre documentos históricos de `thoughts/`
- Incluye rutas de archivo y números de línea específicos
- Los hallazgos de `thoughts/` sirven como contexto histórico suplementario

---

### 6. Inicialización del Directorio thoughts/ (SKILL.md:43-46)

Antes de escribir el documento, el skill verifica si existe `thoughts/`. Si no existe:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init
```

La variable `${CLAUDE_PLUGIN_ROOT}` es resuelta por Claude Code a la ruta de instalación del plugin en el cache: `/Users/jorge.castro/.claude/plugins/cache/stepwise-dev/stepwise-core/1.0.1/`. El script `thoughts-init` (`core/skills/thoughts-management/scripts/thoughts-init`):

- Lee `THOUGHTS_USER` del entorno (default: `nikey_es`)
- Crea la estructura de directorios con `mkdir -p`:
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
- Si `thoughts/README.md` no existe, lo crea con documentación de uso de los slash commands
- Usa `set -euo pipefail` para fallo rápido ante errores

Si `thoughts/` ya existe, el script emite un warning pero continúa sin destruir archivos existentes.

---

### 7. Generación de Metadatos (SKILL.md:47-49)

El skill ejecuta:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
```

El script `thoughts-metadata` (`core/skills/thoughts-management/scripts/thoughts-metadata`) genera metadatos de contexto para el frontmatter del documento:

**Metadatos de tiempo:**
- `DATETIME_TZ` = `date '+%Y-%m-%d %H:%M:%S %Z'`
- `DATE_ISO` = `date -u '+%Y-%m-%dT%H:%M:%S%z'`
- `DATE_SHORT` = `date '+%Y-%m-%d'`
- `FILENAME_TS` = `date '+%Y-%m-%d_%H-%M-%S'`

**Metadatos de git** (con fallbacks si no hay repositorio):
- `REPO_ROOT` = `git rev-parse --show-toplevel`
- `REPO_NAME` = `basename "$REPO_ROOT"`
- `GIT_BRANCH` = `git branch --show-current` (o `git rev-parse --abbrev-ref HEAD`)
- `GIT_COMMIT` = `git rev-parse HEAD`
- `GIT_USER` = `git config user.name`
- `GIT_EMAIL` = `git config user.email`

La salida es en formato `Clave: Valor` por stdout (legible por Claude). Los warnings van a stderr con `>&2`, no contaminando la salida principal.

---

### 8. Generación del Documento de Investigación (SKILL.md:53-79)

Claude escribe el documento final en disco usando la herramienta `Write`. La ruta sigue el patrón:

```
thoughts/shared/research/YYYY-MM-DD-descripcion.md          # sin ticket
thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-descripcion.md # con número de ticket
```

El documento tiene esta estructura fija:

```markdown
---
date: [ISO datetime from metadata]
researcher: [name from metadata]
git_commit: [commit hash from metadata]
branch: [branch from metadata]
repository: [repo name from metadata]
topic: "[user's question]"
tags: [research, codebase, relevant-component-names]
status: complete
last_updated: [YYYY-MM-DD]
last_updated_by: [researcher name]
---

# Research: [Topic]

## Research Question
## Summary
## Detailed Findings
## Code References
## Architecture Documentation
## Historical Context (from thoughts/)
## Related Research
## Open Questions
```

La instrucción explícita del skill es **nunca escribir valores placeholder**; todos los campos del frontmatter deben tener valores reales obtenidos de la ejecución del script `thoughts-metadata`.

---

### 9. Presentación al Usuario (SKILL.md:81)

Una vez escrito el documento, el skill presenta al usuario:
- Ruta del documento generado
- Resumen conciso de los hallazgos
- Siguiente paso sugerido: `/stepwise-core:create-plan` si aplica

---

### 10. Preguntas de Seguimiento (SKILL.md:83-86)

Para preguntas de seguimiento del mismo usuario:
- Se **agrega al mismo documento** (no se crea uno nuevo)
- Se actualiza `last_updated` y `last_updated_by` en el frontmatter
- Se agrega una sección `## Follow-up Research [timestamp]`

---

## Code References

| Archivo | Líneas | Propósito |
|---|---|---|
| `core/skills/research-codebase/SKILL.md` | 1-7 | Frontmatter del skill (model, disable-model-invocation, argument-hint) |
| `core/skills/research-codebase/SKILL.md` | 21-26 | Validación de $ARGUMENTS (vacío, ambiguo, claro) |
| `core/skills/research-codebase/SKILL.md` | 29-31 | Lectura previa de archivos mencionados (sin limit/offset) |
| `core/skills/research-codebase/SKILL.md` | 29-39 | Definición y uso de los 5 agentes especializados |
| `core/skills/research-codebase/SKILL.md` | 39-41 | Síntesis: priorizar codebase sobre thoughts/ |
| `core/skills/research-codebase/SKILL.md` | 43-46 | Inicialización de thoughts/ con thoughts-init |
| `core/skills/research-codebase/SKILL.md` | 47-49 | Generación de metadatos con thoughts-metadata |
| `core/skills/research-codebase/SKILL.md` | 53-79 | Template completo del documento de investigación |
| `core/skills/research-codebase/SKILL.md` | 81 | Presentación al usuario y sugerencia de create-plan |
| `core/skills/research-codebase/SKILL.md` | 83-86 | Manejo de preguntas de seguimiento |
| `core/agents/codebase-locator.md` | 1-7 | Frontmatter: haiku, tools: Grep/Glob/LS |
| `core/agents/codebase-analyzer.md` | 1-7 | Frontmatter: sonnet, tools: Read+Grep+Glob+LS |
| `core/agents/codebase-pattern-finder.md` | 1-7 | Frontmatter: sonnet, tools: Grep+Glob+Read+LS |
| `core/agents/thoughts-locator.md` | 1-7 | Frontmatter: haiku, tools: Grep+Glob+LS |
| `core/agents/thoughts-analyzer.md` | 1-7 | Frontmatter: sonnet, tools: Read+Grep+Glob+LS |
| `core/skills/thoughts-management/scripts/thoughts-init` | 1-82 | Script bash: crea estructura thoughts/ |
| `core/skills/thoughts-management/scripts/thoughts-metadata` | 1-52 | Script bash: genera metadatos git |
| `core/.claude-plugin/plugin.json` | 1-22 | Metadatos del plugin stepwise-core v1.0.1 |
| `.claude-plugin/marketplace.json` | 1-38 | Definición del marketplace con 4 plugins |

---

## Architecture Documentation

### Flujo de Datos Completo

```
Usuario invoca /stepwise-core:research-codebase [query]
        │
        ▼
[Claude Code localiza SKILL.md en plugin cache]
[~/.claude/plugins/cache/stepwise-dev/stepwise-core/1.0.1/skills/research-codebase/SKILL.md]
        │
        ▼
[Validación de $ARGUMENTS]
   ├── Vacío → pide query, espera
   ├── Ambiguo → pide clarificación, espera
   └── Claro → continúa
        │
        ▼
[Lectura previa de archivos mencionados por el usuario]
        │
        ▼
[Investigación: sub-agentes paralelos via Task]
    ┌───┬──────────────────┬──────────────────┬─────────────────┐
    │   │                  │                  │                 │
    ▼   ▼                  ▼                  ▼                 ▼
codebase  codebase    codebase-       thoughts-    thoughts-
locator   analyzer    pattern-finder  locator      analyzer
(haiku)   (sonnet)    (sonnet)        (haiku)      (sonnet)
Grep/     Read+Grep+  Grep+Glob+      Grep/         Read+Grep+
Glob/LS   Glob+LS     Read+LS         Glob/LS       Glob+LS
    │         │            │               │             │
    └────┬────┴────────────┘               └──────┬──────┘
         │                                        │
         ▼                                        ▼
  [Hallazgos del codebase]             [Contexto histórico de thoughts/]
         │                                        │
         └──────────────────┬─────────────────────┘
                            │
                            ▼
[Síntesis en contexto principal del skill]
[Prioridad: codebase en vivo > documentos históricos]
                            │
                            ▼
[¿Existe thoughts/?]
   ├── No → bash thoughts-init → crea estructura de directorios
   └── Sí → continúa
                            │
                            ▼
[bash thoughts-metadata → stdout: fecha + git metadata]
                            │
                            ▼
[Genera documento Markdown con frontmatter YAML]
[Escribe en thoughts/shared/research/YYYY-MM-DD-descripcion.md]
                            │
                            ▼
[Presenta resumen al usuario]
[Sugiere /stepwise-core:create-plan como siguiente paso]
```

### Estructura de Archivos del Sistema

```
core/                                   # Plugin stepwise-core (source)
├── .claude-plugin/
│   └── plugin.json                     # Metadatos del plugin v1.0.1
├── agents/
│   ├── codebase-locator.md             # haiku, Grep/Glob/LS
│   ├── codebase-analyzer.md            # sonnet, Read+Grep+Glob+LS
│   ├── codebase-pattern-finder.md      # sonnet, Grep+Glob+Read+LS
│   ├── thoughts-locator.md             # haiku, Grep/Glob/LS
│   └── thoughts-analyzer.md            # sonnet, Read+Grep+Glob+LS
└── skills/
    ├── research-codebase/
    │   └── SKILL.md                    # Skill principal (86 líneas)
    └── thoughts-management/
        ├── SKILL.md                    # Skill de gestión de thoughts/
        └── scripts/
            ├── thoughts-init           # bash: crea estructura thoughts/
            └── thoughts-metadata       # bash: genera metadatos git

~/.claude/plugins/cache/stepwise-dev/stepwise-core/1.0.1/
                                        # Copia del plugin para seguridad/verificación
                                        # Ruta resuelta por ${CLAUDE_PLUGIN_ROOT}

thoughts/                               # Directorio en el proyecto del usuario
├── README.md
├── {username}/
│   ├── tickets/
│   └── notes/
├── shared/
│   ├── research/                       # ← Destino del documento de investigación
│   ├── plans/
│   └── prs/
└── searchable/                         # Hardlinks para grep eficiente
    ├── {username}/
    └── shared/
```

### Separación de Responsabilidades por Modelo

| Componente | Modelo | Herramientas | Responsabilidad |
|---|---|---|---|
| research-codebase (skill) | sonnet | Todas | Orquestación, síntesis, escritura del documento |
| codebase-locator | haiku | Grep, Glob, LS | Mapeo rápido de ubicaciones de archivos |
| thoughts-locator | haiku | Grep, Glob, LS | Descubrimiento rápido en thoughts/ |
| codebase-analyzer | sonnet | Read, Grep, Glob, LS | Análisis profundo de implementación con referencias |
| codebase-pattern-finder | sonnet | Grep, Glob, Read, LS | Extracción de patrones con código concreto |
| thoughts-analyzer | sonnet | Read, Grep, Glob, LS | Extracción de insights de documentos históricos |

Los agentes de localización (locators) usan `haiku` para velocidad y economía. Los de análisis profundo (analyzers) usan `sonnet`. El skill orquestador también usa `sonnet` para síntesis de calidad.

### Mecanismo de ${CLAUDE_PLUGIN_ROOT}

Según la documentación del plugin system de Claude Code (referenciada en `thoughts/nikey_es/notes/plugins-claude-code.md`), `${CLAUDE_PLUGIN_ROOT}` es una variable de entorno que Claude Code inyecta en tiempo de ejecución y apunta al directorio raíz del plugin instalado. Para plugins instalados desde un marketplace, este directorio es la copia en el cache (`~/.claude/plugins/cache/{marketplace}/{plugin-name}/{version}/`). Esto permite que los scripts del plugin se referencien con rutas relativas al plugin independientemente de dónde esté instalado.

---

## Historical Context (from thoughts/)

**`thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md`**: Documenta que el patrón de sub-agentes paralelos en research-codebase implementa aislamiento de contexto (los sub-agentes exploran en sus propios contextos, el agente padre recibe solo resultados sintetizados). También confirma la existencia del directorio `thoughts/searchable/` con hardlinks para grep eficiente. Menciona un script `thoughts-sync` (147 líneas) para gestionar esos hardlinks, pero ese script ya no existe en la versión actual del plugin (solo existen `thoughts-init` y `thoughts-metadata`).

**`thoughts/shared/research/2025-11-12-testing-infrastructure.md`**: Confirma que la validación de skills y agents requiere prueba manual en Claude Code runtime. No hay tests automáticos para el comportamiento del skill; los tests automatizados en `test/smoke-test.sh` solo cubren los scripts bash (`thoughts-init`, `thoughts-metadata`).

---

## Related Research

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Análisis del patrón de aislamiento de contexto con sub-agentes
- `thoughts/shared/research/2025-11-12-testing-infrastructure.md` — Infraestructura de testing del proyecto
- `core/skills/research-codebase-workspace/iteration-2/data-flow/with_skill/outputs/research.md` — Investigación previa sobre el mismo flujo (iteración 2)

---

## Open Questions

1. **¿Cómo resuelve Claude Code `${CLAUDE_PLUGIN_ROOT}` exactamente en el contexto de un skill?** — La documentación del plugin reference (`thoughts/nikey_es/notes/plugins-claude-code.md`) documenta `${CLAUDE_PLUGIN_ROOT}` para hooks y MCP servers, pero no especifica explícitamente cómo se inyecta esta variable cuando el SKILL.md la referencia en comandos bash inline.

2. **¿Dónde fue el script `thoughts-sync`?** — La investigación histórica (`2025-12-28-advanced-context-engineering-improvements.md`) menciona `skills/thoughts-management/scripts/thoughts-sync` (147 líneas de bash) para gestionar hardlinks en `thoughts/searchable/`. Este script no existe en la versión actual del repositorio ni en el plugin cache, pero el directorio `thoughts/searchable/` sí existe en el repositorio.

3. **¿Cuándo se popula `thoughts/searchable/`?** — El directorio existe en el repositorio pero no hay ningún script activo que lo mantenga. Los subdirectorios `searchable/nikey_es/` y `searchable/shared/` existen pero su contenido no fue verificado.
