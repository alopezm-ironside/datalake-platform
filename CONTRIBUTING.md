# Contribuir

## Mensajes de commit

El repositorio usa [Conventional Commits](https://www.conventionalcommits.org/),
validados por commitizen en el hook `commit-msg` (lefthook).

Formato:

```
<tipo>(<alcance opcional>): <descripción>
```

Regla del proyecto: **elegir el tipo más específico que corresponda**. No usar
`feat` o `fix` por defecto cuando el cambio encaja en un tipo más preciso.

| Tipo       | Cuándo usarlo                                                  |
| ---------- | -------------------------------------------------------------- |
| `feat`     | Nueva funcionalidad                                            |
| `fix`      | Corrección de un bug                                           |
| `docs`     | Solo documentación                                             |
| `style`    | Formato sin cambio de lógica (espacios, comas, imports)        |
| `refactor` | Cambio de código que no corrige un bug ni agrega funcionalidad |
| `perf`     | Mejora de rendimiento                                          |
| `test`     | Agregar o corregir tests                                       |
| `build`    | Sistema de build o dependencias (uv, Docker)                   |
| `ci`       | Configuración de CI/CD                                         |
| `chore`    | Mantenimiento que no encaja en los anteriores                  |
| `revert`   | Revierte un commit previo                                      |

Para breaking changes, usar `!` después del tipo (`feat!:`) o el footer
`BREAKING CHANGE:`.

## Workflow de desarrollo

Ciclo estándar: `uv sync` → `uv run lefthook install` (una vez por clon) → editar
→ los hooks disparan automáticamente en cada commit y push.

| Gate | Cuándo | Comando manual equivalente |
| ---- | ------ | -------------------------- |
| Lint + formato | pre-commit | `uv run ruff check --fix . && uv run ruff format .` |
| Convención de commits | commit-msg | automático (`cz check`) |
| Type check + tests | pre-push | `uv run mypy && uv run pytest` |
| CI completo | push / PR | GitHub Actions (`ci.yml`) |

## Tests

- Framework: **pytest** + **pytest-randomly** (orden de ejecución aleatorio por
  defecto).
- El `conftest.py` en la raíz del workspace reinicia el estado global entre tests
  (singleton de `BigQueryConnection` y sentinel de observabilidad). No se requiere
  ninguna acción adicional en tests nuevos.
- Ejecutar la suite completa desde la raíz del workspace:

  ```bash
  uv run pytest
  ```

- Para reproducir una falla con el mismo orden de ejecución:

  ```bash
  uv run pytest -p randomly --randomly-seed=last
  ```

  `--randomly-seed=last` reutiliza la semilla del último run. pytest imprime la
  semilla activa al inicio de cada ejecución.

## Tipado estático

El proyecto usa tipado estricto con dos herramientas complementarias:

- **mypy** (con plugin `pydantic.mypy`, modo strict) — chequeo primario, corre en
  CI y en el hook pre-push.
- **pyright** — validación con paridad de IDE; detecta casos que mypy pasa por
  alto.

Correr ambas herramientas juntas:

```bash
uv run mypy && uv run pyright
```

Todo código nuevo debe pasar ambas herramientas con **0 errores** antes de abrir
un PR.
