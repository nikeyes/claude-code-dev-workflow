# Research: Arquitectura de Agentes Especializados

## Research Question
¿Qué agentes hay, qué tools tiene cada uno, y cómo se diferencian los locators de los analyzers?

## Summary

El proyecto stepwise-dev define 9 agentes especializados distribuidos en 4 plugins. Los agentes siguen un patrón de especialización claro: los **locators** son agentes ligeros de navegación (solo usan herramientas de búsqueda de archivos, modelo Haiku) mientras que los **analyzers** son agentes de lectura y comprensión profunda (incluyen la herramienta Read, modelo Sonnet). Esta diferencia no es cosmética: refleja una separación intencional entre encontrar *dónde* vive el código y entender *cómo* funciona.

---

## Detailed Findings

### Plugin: stepwise-core (`/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/`)

Contiene 5 agentes orientados a la exploración de un codebase local.

#### 1. codebase-locator
- **Archivo**: `core/agents/codebase-locator.md`
- **Tools**: `Grep, Glob, LS`
- **Model**: `haiku`
- **Color**: `blue`
- **Propósito**: Encuentra *dónde* viven archivos, directorios y componentes. Es un "Super Grep/Glob/LS tool". Explícitamente **no lee contenidos de ficheros**.
- **Responsabilidades**: Buscar ficheros por topic/feature, categorizarlos (implementación, tests, configuración, tipos, docs), devolver rutas agrupadas por propósito.
- **Output típico**: Listado de rutas con agrupación por categoría. No analiza lo que hay dentro.

#### 2. codebase-analyzer
- **Archivo**: `core/agents/codebase-analyzer.md`
- **Tools**: `Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `green`
- **Propósito**: Entiende *cómo* funciona el código. Lee ficheros en profundidad, traza el flujo de datos, documenta patrones con referencias `file:line`.
- **Responsabilidades**: Analizar detalles de implementación, trazar llamadas a funciones, identificar patrones arquitectónicos.
- **Output típico**: Análisis con referencias exactas tipo `handlers/webhook.js:15-32`, secciones de Entry Points, Core Implementation, Data Flow, Key Patterns.

#### 3. codebase-pattern-finder
- **Archivo**: `core/agents/codebase-pattern-finder.md`
- **Tools**: `Grep, Glob, Read, LS`
- **Model**: `sonnet`
- **Color**: `purple`
- **Propósito**: Encuentra implementaciones similares y patrones existentes que puedan servir de plantilla. Diferencia respecto a codebase-locator: no solo indica la localización, sino que **extrae fragmentos de código concretos**.
- **Responsabilidades**: Localizar implementaciones comparables, extraer snippets, mostrar múltiples variaciones del mismo patrón.
- **Output típico**: Ejemplos de código con contexto, referencias `file:line`, categorías de patrones (API, Data, Component, Testing).

#### 4. thoughts-locator
- **Archivo**: `core/agents/thoughts-locator.md`
- **Tools**: `Grep, Glob, LS`
- **Model**: `haiku`
- **Color**: `cyan`
- **Propósito**: Descubre documentos relevantes en el directorio `thoughts/`. Equivalente a `codebase-locator` pero para el espacio de documentación interna.
- **Responsabilidades**: Buscar en `thoughts/shared/`, `thoughts/{username}/`, `thoughts/global/`; categorizar por tipo (tickets, research, plans, prs, notes).
- **Output típico**: Listado de documentos agrupados por tipo, con descripción de una línea a partir del título.

#### 5. thoughts-analyzer
- **Archivo**: `core/agents/thoughts-analyzer.md`
- **Tools**: `Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `yellow`
- **Propósito**: Extrae insights de alto valor de documentos de `thoughts/`. Descrito como "the research equivalent of codebase-analyzer". A diferencia del locator, lee en profundidad y filtra agresivamente contenido irrelevante.
- **Responsabilidades**: Extraer decisiones clave, filtrar información obsoleta, identificar constraints y especificaciones técnicas concretas.
- **Output típico**: Key Decisions, Critical Constraints, Technical Specifications, Actionable Insights, Still Open/Unclear, Relevance Assessment.

---

### Plugin: stepwise-research (`/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/`)

Contiene 3 agentes orientados a investigación web con síntesis multi-agente.

#### 6. research-lead
- **Archivo**: `research/agents/research-lead.md`
- **Tools**: `Task, Read, Write, TodoWrite`
- **Model**: `opus`
- **Color**: `blue`
- **Propósito**: Orquestador del workflow de investigación multi-agente. Planifica, delega a research-workers en paralelo, sintetiza hallazgos y genera el informe final.
- **Responsabilidades**: Descomponer queries en sub-preguntas, lanzar workers en paralelo (en un único mensaje), detectar gaps, escribir el informe a `thoughts/shared/research/`.
- **Nota**: Es el único agente que usa la herramienta `Task` para crear sub-agentes.

#### 7. research-worker
- **Archivo**: `research/agents/research-worker.md`
- **Tools**: `WebSearch, WebFetch, Read, Grep, Glob`
- **Model**: `sonnet`
- **Color**: `green`
- **Propósito**: Ejecuta búsquedas web focalizadas en una sub-pregunta concreta. Sigue una estrategia Broad → Narrow: primero queries cortas (1-6 palabras), luego refinamiento.
- **Responsabilidades**: Ejecutar 3-5 búsquedas, obtener contenido de 5-10 fuentes de calidad, comprimir hallazgos en 3-6 insights con citas.
- **Output**: Structured findings con Bibliography y Research Metadata.

#### 8. citation-analyst
- **Archivo**: `research/agents/citation-analyst.md`
- **Tools**: `Read, WebFetch, Grep`
- **Model**: `sonnet`
- **Color**: `yellow`
- **Propósito**: Verifica la calidad de las citas en informes de investigación. Es un auditor de calidad, no un editor.
- **Responsabilidades**: Mapear claims a fuentes, verificar accesibilidad de URLs, categorizar fuentes por nivel (Tier 1-4), emitir veredicto (ready/needs revision).

---

### Plugin: stepwise-web (`/Users/jorge.castro/mordor/personal/stepwise-dev/web/agents/`)

#### 9. web-search-researcher
- **Archivo**: `web/agents/web-search-researcher.md`
- **Tools**: `WebSearch, WebFetch, TodoWrite, Read, Grep, Glob, LS`
- **Model**: `sonnet`
- **Color**: `orange`
- **Propósito**: Investigación web generalista. Alternativa más simple a research-lead/worker para consultas únicas que no requieren workflow multi-agente.
- **Responsabilidades**: Búsquedas estratégicas, obtención de contenido de fuentes autorizadas, síntesis con citas y links directos.
- **Nota**: Solo se invoca desde `research-codebase` cuando el usuario explícitamente pide búsqueda web.

---

## Architecture Documentation

### La diferencia clave: Locators vs Analyzers

| Característica | Locators | Analyzers |
|---|---|---|
| **Ejemplos** | codebase-locator, thoughts-locator | codebase-analyzer, thoughts-analyzer |
| **Tools** | Grep, Glob, LS (sin Read) | Read + Grep, Glob, LS |
| **Modelo** | Haiku (más rápido/económico) | Sonnet (más capaz) |
| **¿Lee ficheros?** | No. Solo rutas. | Sí. Lee contenido completo. |
| **Output** | Lista de paths agrupados | Análisis con referencias file:line |
| **Propósito** | Encontrar DÓNDE vive el código | Entender CÓMO funciona el código |
| **Restricción** | No analiza contenidos | No busca rutas, analiza lo que recibe |

### codebase-pattern-finder: un híbrido

`codebase-pattern-finder` ocupa un espacio intermedio: usa `Read` (como los analyzers) pero su misión es encontrar ejemplos copiables, no trazar flujos de datos. Usa Sonnet. Se describe explícitamente como "sorta like codebase-locator, but it will also give you code details".

### Uso coordinado en research-codebase (`core/skills/research-codebase/SKILL.md`)

El skill `research-codebase` orquesta los 5 agentes de `stepwise-core` con esta lógica de coordinación:
- Cuando la pregunta abarca múltiples componentes → lanza agentes en paralelo
- Primero: `codebase-locator` encuentra los ficheros relevantes
- Luego: `codebase-analyzer` entiende cómo funcionan esos ficheros
- Opcionalmente: `codebase-pattern-finder` extrae ejemplos de código existentes
- Para contexto histórico: `thoughts-locator` localiza documentos + `thoughts-analyzer` extrae insights

### Uso coordinado en deep-research (`research/skills/deep-research/SKILL.md`)

El skill `deep-research` orquesta los agentes de `stepwise-research`:
1. El skill mismo actúa como `research-lead` (modelo Opus)
2. Lanza múltiples `research-worker` en paralelo (un único mensaje con múltiples Task calls)
3. Sintetiza los hallazgos
4. Lanza `citation-analyst` para verificar calidad
5. Revisa y finaliza el informe

### Principio compartido: documentarians, not critics

Todos los agentes de `stepwise-core` comparten una restricción crítica en su sistema prompt:
> "YOUR ONLY JOB IS TO DOCUMENT AND EXPLAIN THE CODEBASE AS IT EXISTS TODAY"

No sugieren mejoras, no critican, no realizan análisis de causa raíz a menos que se les pida explícitamente.

---

## Code References

- Todos los agentes de core: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/agents/`
- Todos los agentes de research: `/Users/jorge.castro/mordor/personal/stepwise-dev/research/agents/`
- Agente web: `/Users/jorge.castro/mordor/personal/stepwise-dev/web/agents/web-search-researcher.md`
- Skill que orquesta agentes de core: `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/research-codebase/SKILL.md` (líneas 29-37: lista de agentes disponibles)
- Skill que orquesta agentes de research: `/Users/jorge.castro/mordor/personal/stepwise-dev/research/skills/deep-research/SKILL.md` (líneas 70-115: delegación a workers)

---

## Open Questions

- No existe un `web-search-locator` ni `web-search-analyzer` — la web solo tiene un agente generalista. ¿Es intencional o pendiente de especializar?
- `research-lead` en `research/agents/research-lead.md` y el skill `deep-research` tienen responsabilidades muy solapadas (ambos planifican sub-preguntas, delegan workers, sintetizan). La diferencia entre ambos no es completamente clara desde la documentación del código.
