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

| Tipo | Cuándo usarlo |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de un bug |
| `docs` | Solo documentación |
| `style` | Formato sin cambio de lógica (espacios, comas, imports) |
| `refactor` | Cambio de código que no corrige un bug ni agrega funcionalidad |
| `perf` | Mejora de rendimiento |
| `test` | Agregar o corregir tests |
| `build` | Sistema de build o dependencias (uv, Docker) |
| `ci` | Configuración de CI/CD |
| `chore` | Mantenimiento que no encaja en los anteriores |
| `revert` | Revierte un commit previo |

Para breaking changes, usar `!` después del tipo (`feat!:`) o el footer
`BREAKING CHANGE:`.
