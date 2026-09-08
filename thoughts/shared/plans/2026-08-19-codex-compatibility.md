# stepwise-dev compatible con Codex

## Contexto

`stepwise-dev` es hoy un marketplace de 4 plugins de Claude Code (16 skills, 9 agentes, 3 scripts bash). El objetivo es que el mismo workflow Research → Plan → Implement → Validate funcione en OpenAI Codex, **manteniendo una sola fuente de verdad**: cada línea de contenido duplicada o transpilada es superficie que se rompe con cada versión de las herramientas.

La auditoría del repo desmiente buena parte del riesgo asumido: **no hay ni una sola inyección `` !`cmd` ``, ni referencias `@fichero`, ni `${CLAUDE_SKILL_DIR}`/`${CLAUDE_PROJECT_DIR}`**. Y como Claude Code acepta frontmatter desconocido y Codex lo ignora, **el frontmatter de las 16 skills no se toca**. El trabajo real está en cuatro sitios concretos: la resolución de rutas de scripts, las referencias con namespace de plugin, el vocabulario de delegación, y los 9 agentes.

Alcance: **solo Codex**. OpenCode queda fuera.

### Verificado contra documentación oficial

| Afirmación | Estado |
|---|---|
| Codex descubre skills en `.agents/skills` y `$HOME/.agents/skills` (**no** `~/.codex/skills`) | ✅ [build-skills](https://learn.chatgpt.com/docs/build-skills) |
| *"Codex supports symlinked skill folders and follows the symlink target when scanning these locations"* | ✅ ídem |
| Presupuesto de listado: 2 % de la ventana u 8.000 caracteres | ✅ ídem — **medido: 2.956 chars. Al 37 %. No hay que acortar nada** |
| Agente Codex = TOML con `name`, `description`, `developer_instructions` obligatorios; en `~/.codex/agents/` o `.codex/agents/` | ✅ [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) |
| *"A plugin is an installable package that can include skills, an MCP server, or both"* → **los plugins de Codex no empaquetan agentes** | ✅ [build-plugins](https://learn.chatgpt.com/docs/build-plugins) |
| Codex delega *"after a direct request or applicable project or skill instruction"* → no delega proactivamente | ✅ [subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) |
| `bin/` de un plugin de Claude Code se añade al PATH | ✅ [plugins-reference](https://code.claude.com/docs/en/plugins-reference) (no lo usamos, pero descarta esa vía) |
| "Codex lee `.claude-plugin/marketplace.json`" | ❌ **No lo sostiene la doc oficial.** Descartado |

### Decisiones tomadas

1. Fuente única: los mismos `skills/` sirven a los dos harnesses. Lo único generado son los 9 `.toml`.
2. **No prefijar** nombres de skills. Riesgo de colisión en el espacio plano de Codex, aceptado y reversible.
3. **`$ARGUMENTS` se queda como está** (14 usos en `research-codebase`, `create-plan`, `iterate-plan`). Trade-off aceptado explícitamente: en Codex esas 3 skills verán la cadena literal `$ARGUMENTS`.
4. Agentes → TOML generados y commiteados, instalados en `~/.codex/agents/`.
5. Instalación por symlinks. **No** se crean `.codex-plugin/plugin.json` (nadie los usaría).

---

## Cambios

### 1. [x] Resolución de scripts — `${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}`

Las dos rutas tienen la misma forma (`<raíz>/skills/<nombre>/scripts/<script>`), así que un default de shell cubre ambos harnesses sin mover ficheros, sin variables nuevas y sin tocar `make test`.

```bash
bash "${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/thoughts-management/scripts/thoughts-init"
```

- `core/skills/research-codebase/SKILL.md:45,50`
- `core/skills/create-plan/SKILL.md:182`
- `core/skills/iterate-plan/SKILL.md:131`
- `core/skills/thoughts-management/SKILL.md:30,49,77,123,128`

**Además, arreglar un bug preexistente:** `research/skills/deep-research/SKILL.md:188` invoca `generate-report` con ruta relativa al repo (`research/skills/deep-research/scripts/generate-report`), que ya está roto hoy con el plugin instalado en Claude Code. Pasa al mismo idioma:

```bash
"${CLAUDE_PLUGIN_ROOT:-$HOME/.agents}/skills/deep-research/scripts/generate-report" --title ...
```

> ⚠️ Esto **ata `install.sh` a `$HOME/.agents/skills/`**. Es una convención codificada en 5 skills, no una detección. Documentarlo en `AGENTS.md`.

### 2. [x] Referencias a agentes y skills — nombre pelado + prefijo entre paréntesis

39 puntos usan el namespace de plugin de Claude Code (`stepwise-core:codebase-locator`, `/stepwise-core:tdd`), que en Codex no existe. Se nombran **los dos**, para no apostar a que Claude Code resuelva el nombre sin prefijo:

```markdown
- **codebase-locator** (Claude Code: `stepwise-core:codebase-locator`) — finds WHERE files and components live
```

Ficheros y líneas: `research-codebase/SKILL.md:30-35,81` · `create-plan/SKILL.md:40,41,62-64,112-114,117,118,145,313,314` · `iterate-plan/SKILL.md:35,36,84-86,89,90,182,183,261,267,275` · `implement-plan/SKILL.md:33,34,55,66,82,160,161` · `thoughts-management/SKILL.md:139-141` · `deep-research/SKILL.md:15,70,78,213,217,285,291,297` · `research/agents/research-lead.md:82`

Caso más crítico: `implement-plan/SKILL.md:55` es el **Paso 1** de la skill (`Invoke /stepwise-core:tdd using the Skill tool`) — en Codex falla en la primera instrucción.

### 3. [x] Vocabulario de delegación → prosa imperativa

Codex no delega solo. Donde hoy hay pseudo-API, poner una instrucción explícita que nombre los agentes, el paralelismo y la espera:

```markdown
Spawn these agents in parallel, in a single message, one per area,
and wait for all of them to finish before synthesizing:
  - codebase-locator: find WHERE the relevant code lives
  - codebase-analyzer: explain HOW it works
```

- `core/skills/create-plan/SKILL.md:451-458` — eliminar el bloque ```` ```python ```` con `Task(...)`, que no es una API real ni en Claude Code
- `research/skills/deep-research/SKILL.md:70,78,217,258` — `Use the \`Task\` tool` y los bloques `subagent_type:`
- `research/agents/research-lead.md:81,296`

Esto mejora también Claude Code: prosa explícita es más fiable que un bloque de Python falso.

### 4. [x] `agents/openai.yaml` en las 8 skills user-only

Preserva el `disable-model-invocation: true` que ya existe. Especialmente relevante en `commit`, que sin esto puede autoinvocarse en Codex.

```yaml
# <skill>/agents/openai.yaml
policy:
  allow_implicit_invocation: false
```

En: `create-plan`, `implement-plan`, `iterate-plan`, `research-codebase`, `validate-plan`, `commit`, `review-pr-comments`, `deep-research`.

> ⚠️ La doc describe `openai.yaml` como metadatos *"for the ChatGPT desktop app"*. **No está confirmado que el CLI de Codex respete `allow_implicit_invocation`.** Verificar empíricamente (ver Verificación, paso 4) antes de darlo por bueno.

### 5. [x] Nueva carpeta `codex/`

```
codex/
├── agents/*.toml          # 9, GENERADOS — no editar a mano
├── transpile-agents.sh    # *.md -> *.toml
└── install.sh             # symlinks de skills + copia de agentes
```

**`transpile-agents.sh`** — mapeo mecánico de los 9 `.md` (fuente sigue siendo `core/agents/`, `research/agents/`, `web/agents/`):

| Origen (frontmatter Claude Code) | Destino TOML |
|---|---|
| `name` | `name` |
| `description` | `description` |
| cuerpo markdown | `developer_instructions` |
| `tools:` sin `Write`/`Edit` | `sandbox_mode = "read-only"` |
| `tools:` con `Write` (solo `research-lead`) | `sandbox_mode = "workspace-write"` |
| `model: haiku` | `model = "gpt-5.6-luna"`, `model_reasoning_effort = "low"` |
| `model: sonnet` | `model = "gpt-5.6-terra"`, `model_reasoning_effort = "medium"` |
| `model: opus` | `model = "gpt-5.6"`, `model_reasoning_effort = "high"` |
| `color:` | descartado |

Resultado: 8 agentes `read-only`, solo `research-lead` con `workspace-write`.

> Detalle de implementación: usar cadena literal TOML `'''…'''` para `developer_instructions` (sin secuencias de escape, y los cuerpos contienen backslashes y comillas). El script debe **abortar** si algún cuerpo contiene `'''`.

**`install.sh`** — idempotente, sin sudo:

```bash
mkdir -p "$HOME/.agents/skills" "$HOME/.codex/agents"
for s in core/skills/*/ git/skills/*/ research/skills/*/; do
  case "$s" in *-workspace/*) continue;; esac        # excluir evals
  [ -f "$s/SKILL.md" ] || continue
  ln -sfn "$PWD/${s%/}" "$HOME/.agents/skills/$(basename "$s")"
done
cp codex/agents/*.toml "$HOME/.codex/agents/"
```

> ⚠️ La exclusión de `*-workspace/` es obligatoria: `core/skills/small-safe-steps-workspace/skill-snapshot/SKILL.md` es un duplicado byte a byte de la skill real y un `find -name SKILL.md` ingenuo lo instalaría como skill duplicada.

Skills instaladas: 13 de core + 2 de git + 1 de research = **16**.

### 6. [x] `AGENTS.md` + `CLAUDE.md`

- `AGENTS.md` pasa a ser la fuente de verdad: el contenido actual de `CLAUDE.md` más una sección nueva de arquitectura Codex (carpeta `codex/`, artefactos generados, la convención `$HOME/.agents`, cómo instalar).
- `CLAUDE.md` queda reducido a una línea: `@AGENTS.md`.

### 7. [x] `README.md`

Sección "Uso con Codex": `make install-codex`, qué instala y dónde (`~/.agents/skills/`, `~/.codex/agents/`), y las limitaciones conocidas — en particular que `research-codebase`, `create-plan` e `iterate-plan` muestran `$ARGUMENTS` literal y hay que dar el input en el propio mensaje.

### 8. [x] Makefile y tests

Targets nuevos:
- `install-codex` → `codex/install.sh`
- `transpile-codex` → regenera `codex/agents/*.toml`
- `check-codex` → enganchado a `ci`:
  1. Regenera los 9 TOML en un tmpdir y `diff` contra los commiteados → falla si alguien editó un `.md` sin regenerar
  2. Valida sintaxis TOML de los 9
  3. Grep que falla si aparece `${CLAUDE_PLUGIN_ROOT}` sin `:-`
  4. Grep que falla si aparece `stepwise-[a-z]*:` sin su nombre pelado en la misma línea

Y **actualizar `test/plugin-structure-test.sh`**, que lleva desfasado varias versiones: hoy no comprueba `git/skills/review-pr-comments`, ni nada del plugin `research`, ni las skills nuevas de core (`tdd`, `grill-me`, `bugmagnet`, `hamburger-method`, `small-safe-steps`, `story-splitting`, `test-desiderata`). Añadir además asserts de `codex/`.

> `web/` no tiene skills, solo el agente `web-search-researcher`. En Codex existe únicamente como `.toml`; no es un plugin.

---

## Verificación

Los pasos 3-5 son manuales por naturaleza (skills y agentes solo se validan ejecutándolos), en línea con `test/E2E_CHECKLIST.md`.

1. **Automático:** `make ci` → `test` + `check` (shellcheck) + `check-codex`. Debe pasar en verde.
2. **No regresión en Claude Code** (lo más importante — es el harness en uso hoy):
   - Reinstalar el plugin local y ejecutar `/stepwise-core:research-codebase` sobre una pregunta real. Confirmar que **siguen lanzándose los subagentes en paralelo** tras reescribir las referencias del apartado 2.
   - `/stepwise-git:commit` sobre un cambio de prueba.
   - `/stepwise-core:thoughts-management` → confirmar que `thoughts-init` se resuelve con el nuevo default de shell.
3. **Instalación en Codex:** `make install-codex`; abrir Codex; `/skills` debe listar las 16 sin avisos de truncado, y los 9 agentes deben estar disponibles.
4. **Confirmar `openai.yaml`** (afirmación no verificada): comprobar si Codex se autoinvoca `commit`. Si el CLI ignora `allow_implicit_invocation`, dejar constancia en el README como limitación conocida.
5. **Ciclo completo en Codex:** `research-codebase` → `create-plan` → `implement-plan` sobre un repo pequeño. El criterio de éxito es que **`research-codebase` abra subagentes en paralelo en vez de investigar en su contexto principal** — es lo que valida el apartado 3, y el fallo más probable de todo el plan.
6. **Drift:** editar un `core/agents/*.md`, ejecutar `make check-codex` sin regenerar y confirmar que **falla**.

---

## Estado de implementación (2026-08-19)

Los 8 apartados están implementados. `make ci` en verde: 14 + 91 + 41 = 146 asserts.

### Verificación completada (automática)

- [x] 1. `make ci` → `test` + `check` (shellcheck) + `check-codex`, todo en verde
- [x] 6. Drift: añadir contenido a `core/agents/thoughts-locator.md` sin regenerar hace fallar `make check-codex` (comprobado y revertido)
- [x] `codex/install.sh` verificado con `HOME` en un tmpdir: 16 skills, 9 agentes, idempotente, sin `-workspace`

### Pendiente (manual, requiere ejecutar los harnesses)

- [ ] 2. No regresión en Claude Code — reinstalar el plugin local y ejecutar `research-codebase`, `commit`, `thoughts-management`
- [ ] 3. `make install-codex` real + `/skills` lista las 16 en Codex
- [ ] 4. Confirmar empíricamente si el CLI de Codex respeta `allow_implicit_invocation`
- [ ] 5. Ciclo completo en Codex; criterio de éxito: `research-codebase` abre subagentes en paralelo

### Desviaciones respecto al plan

1. **Ejemplos ilustrativos sin prefijo (apartado 2).** El plan pedía nombrar los dos nombres en los 39 puntos. En las líneas que son *transcripciones de ejemplo* (`iterate-plan/SKILL.md:261,267,275`, `deep-research/SKILL.md:285,291,297`) se dejó solo el nombre pelado: repetir `(Claude Code: …)` en cada línea de un bloque de ejemplo añadía ruido sin información. La forma dual se mantiene en todas las líneas instructivas (listas de agentes, invocaciones, next steps). El grep de `check-codex` exige `Claude Code:` en la misma línea, así que la convención queda cubierta.

2. **`generate-report` fuera de shellcheck.** Añadirlo al target `check` destapó ~10 avisos SC2129 preexistentes, ajenos a este plan. Se dejó fuera para no mezclar. `codex/*.sh` sí está cubierto.

3. **Dos bugs encontrados y corregidos en los scripts nuevos** (BugMagnet), ninguno previsto en el plan:
   - `install.sh`: `ln -sfn` enlazaba *dentro* de un directorio real preexistente (`~/.agents/skills/commit/commit`), dejando una instalación rota que reportaba éxito. Ahora aborta con un mensaje claro.
   - `transpile-agents.sh`: no limpiaba `OUT_DIR`, así que un agente renombrado o borrado dejaba su `.toml` para siempre. Ahora hace `rm -f` previo y cuenta lo realmente escrito.

4. **Nuevo `test/codex-test.sh` (41 asserts), no contemplado en el plan.** El apartado 8 solo pedía actualizar `plugin-structure-test.sh`, que es puramente de existencia de ficheros — ninguno de los dos bugs anteriores habría sido detectado por él. El fichero nuevo ejecuta de verdad los dos scripts contra un `HOME` temporal. Ambas regresiones están verificadas por mutación: reintroduciendo cada bug, fallan 2 asserts.

5. **Helpers nuevos** en `test/test-helpers.sh`: `assert_equals` y `assert_fails`.
