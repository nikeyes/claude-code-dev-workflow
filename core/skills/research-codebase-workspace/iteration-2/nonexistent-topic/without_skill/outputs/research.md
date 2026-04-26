# Research: Sistema de Base de Datos y Migraciones SQL

## Resumen Ejecutivo

El proyecto **stepwise-dev** es una herramienta de workflow para Claude Code. No contiene ningún sistema de base de datos propio, ni migraciones SQL reales. No existe ninguna base de datos operativa, ORM, driver de BD, ni fichero `.sql`, `.db`, o `.sqlite` en el repositorio (excluyendo `node_modules`).

---

## Hallazgos Detallados

### 1. Ausencia de Base de Datos Real

Tras una búsqueda exhaustiva en el repositorio:

- No existen ficheros `.sql`, `.db`, `.sqlite`, `.sqlite3`
- No existen directorios `migrations/` con contenido real
- No existen dependencias de base de datos en ningún `package.json`, `requirements.txt`, `go.mod` o fichero equivalente del proyecto principal
- No hay ORM (SQLAlchemy, ActiveRecord, Prisma, etc.) ni drivers de BD (psycopg2, mysql-connector, pg, etc.)

### 2. Estructura de Directorio Vacía (Fixture de Test)

El único lugar donde aparece una estructura relacionada con base de datos es como un **esqueleto vacío** dentro de los fixtures de test:

**Ruta:** `/Users/jorge.castro/mordor/personal/stepwise-dev/test/fixtures/sample-project/src/database/`

```
test/fixtures/sample-project/src/
├── api/           (vacío)
├── auth/          (vacío)
├── database/
│   ├── migrations/ (vacío - 0 ficheros)
│   └── models/     (vacío - 0 ficheros)
└── utils/          (vacío)
```

Esta estructura fue creada el 28 de diciembre de 2024 como un proyecto de muestra para los smoke tests. Los directorios están completamente vacíos; no contienen ningún fichero de migración ni modelo.

**Ficheros de test relacionados:**
- `/Users/jorge.castro/mordor/personal/stepwise-dev/test/plugin-structure-test.sh`
- `/Users/jorge.castro/mordor/personal/stepwise-dev/test/thoughts-structure-test.sh`
- `/Users/jorge.castro/mordor/personal/stepwise-dev/test/test-helpers.sh`

### 3. Referencias Documentales a Migraciones SQL (Ejemplos Pedagógicos)

El proyecto sí contiene **documentación de referencia** que usa migraciones SQL y cambios de esquema como ejemplos ilustrativos dentro de la skill `small-safe-steps`.

**Fichero:** `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/small-safe-steps/references/small-safe-steps.md`

Este documento describe el patrón **Expand-Contract** aplicado a cambios de base de datos. Los fragmentos SQL presentes son puramente ejemplos pedagógicos, no migraciones reales del proyecto:

#### Ejemplo 1: Renombrar columna (`email` → `email_address`)

```sql
-- Fase EXPAND: añadir nueva columna
ALTER TABLE users ADD COLUMN email_address VARCHAR(255);

-- Backfill de datos existentes
UPDATE users SET email_address = email WHERE email_address IS NULL;

-- Fase CONTRACT: eliminar columna antigua
ALTER TABLE users DROP COLUMN email;
```

#### Ejemplo 2: Cambio de tipo de dato (String → JSONB)

```sql
-- Fase EXPAND: añadir columna estructurada
ALTER TABLE users ADD COLUMN address_structured JSONB;

-- Fase CONTRACT: eliminar columna antigua
ALTER TABLE users DROP COLUMN address;
```

Estos ejemplos cubren:
- Renombrado de columnas con dual-write
- Cambio de tipo de dato (VARCHAR → JSONB en PostgreSQL)
- Patrones de backfill en batches para tablas grandes
- Verificaciones SQL de integridad durante la migración

**Fichero SKILL.md relacionado:** `/Users/jorge.castro/mordor/personal/stepwise-dev/core/skills/small-safe-steps/SKILL.md`

La skill menciona explícitamente casos de uso de migraciones de base de datos:
- "Renaming database columns, tables, or fields"
- "Database migrations"
- "Applies expand-contract pattern for migrations, refactorings, schema changes"

---

## Conclusión

**El proyecto stepwise-dev no tiene sistema de base de datos ni migraciones SQL reales.** Es un proyecto de tooling (skills/agents para Claude Code) que persiste su estado en el sistema de ficheros (directorio `thoughts/`) en lugar de en una base de datos.

Las únicas referencias a SQL y migraciones en el repositorio son:
1. **Directorios vacíos** en `test/fixtures/sample-project/src/database/` (sin contenido)
2. **Ejemplos pedagógicos** en `core/skills/small-safe-steps/references/small-safe-steps.md` que ilustran el patrón Expand-Contract para guiar al usuario cuando trabaje con migraciones en sus propios proyectos

El tema "sistema de base de datos y migraciones SQL" no existe como funcionalidad implementada en este proyecto.
