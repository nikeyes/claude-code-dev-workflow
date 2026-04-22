# Plan de pruebas: Eliminación de searchable/

## Setup

```bash
# Desactivar plugins instalados
claude plugin disable stepwise-core@stepwise-dev
claude plugin disable stepwise-git@stepwise-dev
claude plugin disable stepwise-web@stepwise-dev
claude plugin disable stepwise-research@stepwise-dev

# Lanzar con plugins locales
claude --plugin-dir /Users/jorge.castro/mordor/personal/stepwise-dev/core \
       --plugin-dir /Users/jorge.castro/mordor/personal/stepwise-dev/git \
       --plugin-dir /Users/jorge.castro/mordor/personal/stepwise-dev/web \
       --plugin-dir /Users/jorge.castro/mordor/personal/stepwise-dev/research
```

Usar un proyecto de prueba (e.g. [stepwise-todo-api-test](https://github.com/nikeyes/stepwise-todo-api-test)).
Si ya tiene `thoughts/`, borrarlo antes: `rm -rf thoughts/`

---

## Test 1: Inicialización desde research

```bash
/stepwise-core:research_codebase How does the API handle requests?
```

- [x] Crea `thoughts/` sin subdirectorio `searchable/`
- [x] No hay `.gitignore` dentro de `thoughts/`
- [x] Genera documento en `thoughts/shared/research/YYYY-MM-DD-*.md`
- [x] No aparece ningún error ni warning sobre `thoughts-sync`
- [x] El documento tiene frontmatter con metadata real (no placeholders)

## Test 2: Crear plan

```bash
/clear
/stepwise-core:create_plan Add a health check endpoint
```

- [x] No intenta ejecutar `thoughts-sync`
- [x] Genera plan en `thoughts/shared/plans/YYYY-MM-DD-*.md`
- [x] El plan tiene fases con success criteria

## Test 3: Iterar plan

```bash
/clear
/stepwise-core:iterate_plan thoughts/shared/plans/[el-plan-del-test-2].md Add error handling phase
```

- [x] Modifica el plan existente in-place
- [x] No hay referencia a sync ni searchable en la salida

## Test 4: Implementar plan

```bash
/clear
/stepwise-core:implement_plan thoughts/shared/plans/[el-plan-del-test-2].md
```

- [x] Ejecuta las fases
- [x] Al completar, NO ejecuta `thoughts-sync` ni `thoughts-init` (ya existe)
- [x] El mensaje final sugiere `/stepwise-core:validate_plan`

## Test 5: Buscar en thoughts

```bash
grep -r "health" thoughts/
```

- [x] Encuentra resultados en `shared/research/` y `shared/plans/`
- [x] No hay resultados duplicados (antes los duplicaba searchable/)

## Test 6: thoughts-locator como sub-agente

Se dispara indirectamente durante Test 1 o Test 2 si ya hay documentos previos en `thoughts/`.

- [x] En la salida de los sub-agentes no aparece `searchable/` en ninguna ruta
- [x] Las rutas reportadas son directas: `thoughts/shared/research/...`, no `thoughts/searchable/shared/...`

---

## Criterio de éxito

Los 6 tests pasan sin que aparezca `searchable`, `hardlink` o `thoughts-sync` en ningún output.

## Cleanup

```bash
# Reactivar plugins del marketplace tras las pruebas
claude plugin enable stepwise-core@stepwise-dev
claude plugin enable stepwise-git@stepwise-dev
claude plugin enable stepwise-web@stepwise-dev
claude plugin enable stepwise-research@stepwise-dev
```
