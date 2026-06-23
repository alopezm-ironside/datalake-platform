# Agregar un módulo (job) nuevo

Un módulo es un job desplegable que sincroniza una entidad desde un origen hacia
un destino. Agregar uno consiste en proveer los adaptadores concretos de los
cuatro ports y cablearlos; la orquestación (`SyncPipeline`) ya existe en
`etl-common` y no se reescribe.

## 1. Crear el paquete del job

```
jobs/<modulo>/
├── pyproject.toml          # name = "etl-<modulo>", dep: etl-common
├── Dockerfile
└── src/<modulo>/
    ├── __main__.py         # entry point: cablea adaptadores e invoca el pipeline
    ├── domain/             # entidades de dominio (stdlib dataclass)
    └── persistence/
        ├── models/         # ORM SQLAlchemy (esquema del sink)
        └── repositories/   # mapea entidad ↔ ORM, persiste
```

El `pyproject.toml` declara `etl-common` como dependencia de workspace y expone
un console script como entry point:

```toml
[project]
name = "etl-<modulo>"
dependencies = ["etl-common"]

[project.scripts]
<modulo>-job = "<modulo>.__main__:main"

[tool.uv.sources]
etl-common = { workspace = true }
```

`members = ["packages/*", "jobs/*"]` en la raíz ya incluye el job nuevo; basta
con `uv lock` para incorporarlo al workspace.

## 2. Definir la entidad de dominio

Pura, sin frameworks. El aggregate root contiene sus entidades relacionadas.

```python
# domain/<entidad>.py
from dataclasses import dataclass, field

@dataclass
class MiEntidad:
    id: int
    # ... campos del dominio
    lineas: list["MiLinea"] = field(default_factory=list)
```

La entidad no conoce SQLAlchemy ni el destino. Esa es la condición de la
agnosticidad.

## 3. Implementar los adaptadores

Cada uno cumple un contrato de `etl_common.interfaces`. Los detalles internos van
en métodos privados del adaptador.

| Adaptador | Contrato | Responsabilidad |
|---|---|---|
| Extractor | `ExtractorInterface` | Leer IDs nuevos y lotes desde el origen |
| Transformer | `TransformerInterface` | Mapear el registro crudo a la entidad de dominio |
| Repository | `RepositoryInterface[T]` | Persistir entidades (append) en el sink |
| Sync state | `SyncStateInterface` | Watermark + metadata de la corrida |

Para `Odoo → BigQuery` se reutilizan los adaptadores de infraestructura de
`etl-common` (`OdooManager`, `BigQueryConnection`). Para un origen o destino
nuevo, se implementa el adaptador correspondiente una sola vez.

Cualquier adaptador o servicio que necesite logging importa desde el paquete raíz
de observabilidad:

```python
from etl_common.observability import get_logger

logger = get_logger(__name__)
```

Nunca desde módulos de backend específicos (`GcpLogBackend`, `ConsoleLogBackend`).
El backend se configura en el composition root; los adaptadores solo consumen el
punto de acceso genérico.

## 4. Cablear el entry point

`__main__.py` configura la observabilidad, construye los adaptadores y se los pasa
al pipeline. No contiene lógica de orquestación.

```python
from etl_common.observability import configure_logging, resolve_backend

def main() -> None:
    settings = Settings()
    configure_logging(resolve_backend(settings.LOG_BACKEND))
    # construir conexiones y adaptadores concretos...
    SyncPipeline(
        module_name="<modulo>",
        extractor=...,
        transformer=...,
        repository=...,
        sync_state=...,
    ).run()
```

`configure_logging` debe llamarse antes de construir cualquier adaptador, para
garantizar que todos los loggers del proceso usen el mismo backend desde el inicio.

Cambiar de destino (por ejemplo a Snowflake) se reduce a construir aquí otro
`repository` y otro `sync_state`; `run()` no cambia.

## 5. Dockerfile

Reutilizar el patrón distroless del job `account` (builder `python:3.11-slim` +
`uv`, runtime `gcr.io/distroless/cc-debian12`). El build se ejecuta desde la raíz
del repositorio:

```bash
docker build -f jobs/<modulo>/Dockerfile -t <registry>/<modulo>:<sha> .
```

## 6. Verificación local

Instalar los hooks de git una vez por clon (prerequisito antes de que disparen):

```bash
uv run lefthook install
```

Luego, verificar el nuevo módulo completo:

```bash
uv lock
uv sync --package etl-<modulo>
uv run ruff check .
uv run mypy
uv run pytest
uv run --package etl-<modulo> <modulo>-job   # requiere variables de entorno
```

## 7. Tests

El workspace usa **pytest** con **pytest-randomly**: el orden de ejecución de los
tests es aleatorio por defecto. Esto detecta dependencias de estado entre tests
que un orden fijo ocultaría.

El `conftest.py` en la raíz del repositorio reinicia el estado global entre cada
test (singleton de `BigQueryConnection` y sentinel de observabilidad). No se
requiere ninguna acción adicional en los tests del módulo nuevo.

Para reproducir una falla con el mismo orden de ejecución:

```bash
uv run pytest -p randomly --randomly-seed=last
```

`--randomly-seed=last` reutiliza la semilla del último run. Para un seed
específico (que pytest imprime al inicio del run):

```bash
uv run pytest -p randomly --randomly-seed=<numero>
```
