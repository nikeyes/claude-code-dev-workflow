---
date: 2026-04-26T00:00:00+00:00
researcher: Jorge Castro
git_commit: a1cdcbb
branch: main
repository: stepwise-dev
topic: "Flujo de datos desde /research-codebase hasta la generación del documento en thoughts/"
tags: [research, data-flow, research-codebase, agents, thoughts-management, skills]
status: complete
last_updated: 2026-04-26
last_updated_by: Jorge Castro
---

# Research: Flujo de datos desde /research-codebase hasta la generación del documento en thoughts/

**Date**: 2026-04-26T00:00:00+00:00
**Researcher**: Jorge Castro
**Git Commit**: a1cdcbb
**Branch**: main
**Repository**: stepwise-dev

## Research Question

¿Cómo fluyen los datos desde que un usuario invoca `/research-codebase` hasta que se genera el documento final en `thoughts/`? ¿Qué componentes intervienen?

## Summary

Cuando el usuario invoca `/stepwise-core:research-codebase [pregunta]`, Claude Code carga el archivo `core/skills/research-codebase/SKILL.md` y lo ejecuta como skill principal (con `disable-model-invocation: true`, lo que significa que Claude Code orquesta la ejecución sin re-invocar un modelo separado). El skill descompone la pregunta en áreas de investigación y lanza múltiples sub-agentes en paralelo usando el tool `Task`: hasta 5 agentes especializados (codebase-locator, codebase-analyzer, codebase-pattern-finder, thoughts-locator, thoughts-analyzer). El skill principal espera a que todos los agentes completen, sintetiza sus resultados, opcionalmente inicializa el directorio `thoughts/` con el script `thoughts-init`, recopila metadatos git con el script `thoughts-metadata`, y genera el documento final como archivo Markdown en `thoughts/shared/research/YYYY-MM-DD-descripcion.md`.

---

## Detailed Findings

### 1. Punto de entrada: el Skill `research-codebase`

**Archivo**: `core/skills/research-codebase/SKILL.md`

El skill es la pieza central de la arquitectura. Se define con frontmatter YAML:

```yaml
name: research-codebase
description: Document codebase as-is with thoughts directory for historical context
argument-hint: [research question or topic]
model: opus
disable-model-invocation: true
```

- `model: opus` indica que Claude usa el modelo Opus para la ejecución.
- `disable-model-invocation: true` hace que Claude Code ejecute el skill directamente sin relanzar una nueva invocación de modelo; el skill actúa como una capa de orquestación.
- `argument-hint` permite pasar la pregunta de investigación directamente: `/stepwise-core:research-codebase [pregunta]`.

La secuencia de pasos definida en el SKILL.md es:

1. Leer archivos mencionados directamente (si los hay) antes de lanzar sub-agentes.
2. Analizar y descomponer la pregunta en áreas de investigación; crear plan con `TodoWrite`.
3. Lanzar sub-agentes en paralelo.
4. Esperar que todos los sub-agentes completen y sintetizar resultados.
5. Verificar/inicializar el directorio `thoughts/` si no existe.
6. Recopilar metadatos para el documento.
7. Generar el documento de investigación.
8. Añadir GitHub permalinks (si aplica).
9. Presentar resumen al usuario.
10. Gestionar preguntas de seguimiento.

---

### 2. Capa de orquestación: sub-agentes especializados

El skill lanza hasta 5 agentes especializados mediante el tool `Task`. Todos están bajo `core/agents/`:

#### 2.1 `codebase-locator` — Localizador de archivos
**Archivo**: `core/agents/codebase-locator.md`

```yaml
name: codebase-locator
tools: Grep, Glob, LS
color: blue
model: haiku
```

- Responsabilidad: encontrar **dónde** vive el código (archivos, directorios, naming conventions).
- Herramientas: solo `Grep`, `Glob`, `LS` — no lee el contenido de los archivos.
- Modelo: `haiku` (más rápido/económico para búsquedas estructurales).
- Salida: lista de rutas agrupadas por categoría (implementación, tests, config, docs).

#### 2.2 `codebase-analyzer` — Analizador de implementación
**Archivo**: `core/agents/codebase-analyzer.md`

```yaml
name: codebase-analyzer
tools: Read, Grep, Glob, LS
color: green
model: sonnet
```

- Responsabilidad: entender **cómo** funciona el código — traza flujos de datos, identifica funciones clave, documenta lógica.
- Herramientas: tiene acceso a `Read` (puede leer contenido de archivos) además de `Grep`, `Glob`, `LS`.
- Modelo: `sonnet` (más capaz para análisis de código).
- Salida: análisis con referencias `file:línea` precisas, incluyendo Entry Points, Core Implementation, Data Flow y Key Patterns.

#### 2.3 `codebase-pattern-finder` — Buscador de patrones
**Archivo**: `core/agents/codebase-pattern-finder.md`

```yaml
name: codebase-pattern-finder
tools: Grep, Glob, Read, LS
color: purple
model: sonnet
```

- Responsabilidad: encontrar ejemplos de patrones existentes en el codebase.
- Herramientas: `Grep`, `Glob`, `Read`, `LS` — busca y extrae fragmentos de código concretos.
- Modelo: `sonnet`.
- Salida: catálogo de patrones con extractos de código y referencias `file:línea`.

#### 2.4 `thoughts-locator` — Localizador en thoughts/
**Archivo**: `core/agents/thoughts-locator.md`

```yaml
name: thoughts-locator
tools: Grep, Glob, LS
color: cyan
model: haiku
```

- Responsabilidad: descubrir documentos relevantes en el directorio `thoughts/` (tickets, research, planes, notas).
- Herramientas: solo `Grep`, `Glob`, `LS` — no lee en profundidad.
- Modelo: `haiku`.
- Estructura de búsqueda:
  ```
  thoughts/shared/research/   → documentos de investigación
  thoughts/shared/plans/      → planes de implementación
  thoughts/shared/prs/        → descripciones de PRs
  thoughts/{username}/tickets/ → tickets personales
  thoughts/{username}/notes/   → notas personales
  ```

#### 2.5 `thoughts-analyzer` — Analizador de thoughts/
**Archivo**: `core/agents/thoughts-analyzer.md`

```yaml
name: thoughts-analyzer
tools: Read, Grep, Glob, LS
color: yellow
model: sonnet
```

- Responsabilidad: extraer insights de alto valor de los documentos encontrados por `thoughts-locator`.
- Herramientas: `Read`, `Grep`, `Glob`, `LS` — lee el contenido completo de los documentos más relevantes.
- Modelo: `sonnet`.
- Salida: análisis filtrado con Key Decisions, Technical Specifications, Constraints, y Relevance Assessment.

---

### 3. Gestión de `thoughts/`: el Skill `thoughts-management`

**Archivo**: `core/skills/thoughts-management/SKILL.md`

El skill `research-codebase` delega dos operaciones críticas al skill `thoughts-management`:

#### 3.1 Inicialización del directorio (`thoughts-init`)
**Script**: `core/skills/thoughts-management/scripts/thoughts-init`

```bash
# Ruta de invocación desde research-codebase:
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-init
```

El script:
- Lee la variable de entorno `THOUGHTS_USER` (default: `nikey_es`).
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
- Genera `thoughts/README.md` (solo si no existe).
- Es idempotente: si `thoughts/` ya existe, emite una advertencia pero continúa sin destruir archivos.

#### 3.2 Generación de metadatos (`thoughts-metadata`)
**Script**: `core/skills/thoughts-management/scripts/thoughts-metadata`

```bash
# Ruta de invocación desde research-codebase:
bash ${CLAUDE_PLUGIN_ROOT}/skills/thoughts-management/scripts/thoughts-metadata
```

El script recopila:
- Fecha/hora con timezone (varios formatos: `DATETIME_TZ`, `DATE_ISO`, `DATE_SHORT`, `FILENAME_TS`).
- Metadatos git: commit hash, branch name, repository name, user name, user email.
- Fallbacks para entornos sin git: valores `no-repo`, `no-branch`, `no-commit`, `unknown`.

Output de ejemplo:
```
Current Date/Time (TZ): 2025-01-12 14:30:45 PST
ISO DateTime: 2025-01-12T14:30:45-0800
Date Short: 2025-01-12
Current Git Commit Hash: abc123def456
Current Branch Name: main
Repository Name: my-project
Git User: John Doe
Git Email: john@example.com
Timestamp For Filename: 2025-01-12_14-30-45
```

---

### 4. Generación del documento final

Con los resultados de todos los agentes y los metadatos recopilados, el skill principal genera el documento de investigación en:

```
thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-descripcion.md
```

Ejemplos de nombres de archivo:
- Con ticket: `2025-01-08-ENG-1478-parent-child-tracking.md`
- Sin ticket: `2025-01-08-authentication-flow.md`

**Estructura del documento**:

```markdown
---
date: [ISO DateTime]
researcher: [Git User]
git_commit: [commit hash]
branch: [branch name]
repository: [repo name]
topic: "[pregunta original del usuario]"
tags: [research, codebase, componentes-relevantes]
status: complete
last_updated: [Date Short]
last_updated_by: [Git User]
---

# Research: [Pregunta/Tema]

**Date**: ...
**Researcher**: ...
**Git Commit**: ...
**Branch**: ...
**Repository**: ...

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

---

### 5. Flujo de datos completo (diagrama)

```
Usuario invoca:
/stepwise-core:research-codebase [pregunta]
        │
        ▼
Claude Code carga:
core/skills/research-codebase/SKILL.md
(model: opus, disable-model-invocation: true)
        │
        ▼
Skill analiza la pregunta y crea plan (TodoWrite)
        │
        ▼
        ┌─────────────────────────────────────────────────────────┐
        │           Lanza en PARALELO (Tool: Task)                │
        ├─────────────┬──────────────┬──────────────┬────────────┤
        │             │              │              │            │
        ▼             ▼              ▼              ▼            ▼
codebase-      codebase-      codebase-      thoughts-   thoughts-
locator        analyzer       pattern-       locator     analyzer
(haiku)        (sonnet)       finder         (haiku)     (sonnet)
               (sonnet)
Grep/Glob/LS  Read/Grep/     Grep/Glob/    Grep/Glob/  Read/Grep/
              Glob/LS        Read/LS       LS          Glob/LS
        │             │              │              │            │
        └─────────────┴──────────────┴──────────────┴────────────┘
                                     │
                                     ▼
              Skill principal espera y sintetiza resultados
                                     │
                          ┌──────────┴──────────┐
                          │                     │
                          ▼                     ▼
              Verifica/inicializa       Recopila metadatos git
              thoughts/ directory       via thoughts-metadata
              via thoughts-init         (fecha, branch, commit,
              (si no existe)            user, repo)
                          │                     │
                          └──────────┬──────────┘
                                     │
                                     ▼
              Genera documento final:
              thoughts/shared/research/YYYY-MM-DD-descripcion.md
              (con YAML frontmatter + contenido estructurado)
                                     │
                                     ▼
              Añade GitHub permalinks (si en main/pushed)
                                     │
                                     ▼
              Presenta resumen al usuario
```

---

## Code References

- `core/skills/research-codebase/SKILL.md:1-7` — Frontmatter del skill (name, model, disable-model-invocation)
- `core/skills/research-codebase/SKILL.md:28-38` — Lógica de inicio: manejo de $ARGUMENTS
- `core/skills/research-codebase/SKILL.md:40-80` — Pasos 1-3: lectura inicial, decomposición, lanzamiento de agentes
- `core/skills/research-codebase/SKILL.md:81-98` — Paso 4: esperar y sintetizar resultados de todos los agentes
- `core/skills/research-codebase/SKILL.md:99-107` — Paso 5: inicialización de thoughts/ con thoughts-init
- `core/skills/research-codebase/SKILL.md:100-169` — Pasos 6-7: recopilar metadatos y generar documento con estructura completa
- `core/agents/codebase-locator.md:1-7` — Frontmatter: tools Grep/Glob/LS, model haiku
- `core/agents/codebase-analyzer.md:1-7` — Frontmatter: tools Read/Grep/Glob/LS, model sonnet
- `core/agents/codebase-pattern-finder.md:1-7` — Frontmatter: tools Grep/Glob/Read/LS, model sonnet
- `core/agents/thoughts-locator.md:1-7` — Frontmatter: tools Grep/Glob/LS, model haiku
- `core/agents/thoughts-analyzer.md:1-7` — Frontmatter: tools Read/Grep/Glob/LS, model sonnet
- `core/skills/thoughts-management/SKILL.md:29-32` — Invocación de thoughts-init
- `core/skills/thoughts-management/SKILL.md:48-51` — Invocación de thoughts-metadata
- `core/skills/thoughts-management/scripts/thoughts-init:7` — Variable de entorno THOUGHTS_USER (default: nikey_es)
- `core/skills/thoughts-management/scripts/thoughts-init:37-41` — Creación de estructura de directorios
- `core/skills/thoughts-management/scripts/thoughts-metadata:20-23` — Recopilación de timestamps
- `core/skills/thoughts-management/scripts/thoughts-metadata:26-40` — Recopilación de metadatos git con fallbacks

---

## Architecture Documentation

### Patrón de orquestación paralela
El skill principal actúa como orquestador: lanza múltiples agentes en paralelo y sintetiza sus resultados. Cada agente tiene un scope estrecho (locate, analyze, find patterns, locate thoughts, analyze thoughts). El paralelismo maximiza la eficiencia y minimiza el contexto en el agente principal.

### División de herramientas por responsabilidad
Los agentes "locators" (codebase-locator, thoughts-locator) solo tienen herramientas de búsqueda de estructura (`Grep`, `Glob`, `LS`) y usan modelo haiku (rápido). Los agentes "analyzers" (codebase-analyzer, thoughts-analyzer, codebase-pattern-finder) tienen acceso a `Read` y usan modelo sonnet (más capaz para comprensión).

### Separación de concerns
- `research-codebase`: orquestación y síntesis.
- `codebase-*` agents: investigación del código fuente.
- `thoughts-*` agents: investigación del historial en thoughts/.
- `thoughts-management` skill + scripts: gestión del sistema de archivos (creación de directorios, metadatos).

### Convención de naming del documento final
`YYYY-MM-DD[-ENG-XXXX]-descripcion-kebab-case.md` en `thoughts/shared/research/`. La fecha proviene del script `thoughts-metadata`, no del reloj del modelo.

### Frontmatter como contrato de datos
Todos los documentos generados usan YAML frontmatter con campos consistentes (`date`, `researcher`, `git_commit`, `branch`, `repository`, `topic`, `tags`, `status`, `last_updated`, `last_updated_by`). Los valores nunca son placeholders: provienen del script `thoughts-metadata`.

---

## Historical Context (from thoughts/)

- `thoughts/shared/research/2025-12-28-advanced-context-engineering-improvements.md` — Documenta la arquitectura de orquestación paralela de Stepwise, menciona el ciclo Research → Plan → Implement → Validate y el uso de skills con fases bien definidas.
- `thoughts/nikey_es/notes/claude-code-skills.md` — Notas sobre el estándar Agent Skills y cómo los skills se integran en Claude Code mediante el directorio `.claude/skills/` o plugins.
- `thoughts/nikey_es/notes/plugins-claude-code.md` — Documentación sobre el sistema de plugins de Claude Code que permite la distribución de skills y agentes como unidades instalables.

---

## Related Research

- `thoughts/shared/research/2025-12-28-humanlayer-comparison-improvement-opportunities.md` — Contexto de comparación con HumanLayer, del que proviene la arquitectura de agentes paralelos.
- `thoughts/shared/research/2025-11-12-testing-infrastructure.md` — Investigación sobre la infraestructura de tests del proyecto.

---

## Open Questions

- ¿Cómo se comporta el skill si uno de los sub-agentes falla o timeout durante la ejecución paralela? El SKILL.md no describe manejo explícito de errores a nivel de agente individual.
- ¿Cuántos agentes se lanzan concurrentemente como máximo? El skill dice "múltiples en paralelo" pero no define un límite explícito.
- El paso de GitHub permalinks (paso 8) depende de que el commit esté pushed; ¿cómo se documenta el caso en que no lo está?
