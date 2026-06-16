# Release Process

## Version Policy

RECPL sigue [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR**: Cambios incompatibles en el pipeline (nuevos stages, cambios
  en contratos, eliminacion de features publicas)
- **MINOR**: Nuevas features compatibles (nuevos generadores, gramaticas,
  flags CLI)
- **PATCH**: Bugfixes, optimizaciones, docs, tests

El numero de version se lee de `VERSION` en la raiz del proyecto.

## Pre-release Checklist

- [ ] `ruff check .` = 0 errores
- [ ] `pytest tests/ -q` = 100% pasando
- [ ] `bash -n ci.sh && shellcheck ci.sh` (si aplica)
- [ ] `CHANGELOG.md` actualizado con cambios de la release
- [ ] `VERSION` actualizado al nuevo numero
- [ ] README.md actualizado (badges, quick start, roadmap)

## Release Steps

```bash
# 1. Actualizar VERSION (si no se hizo)
echo "MAJOR.MINOR.PATCH" > VERSION

# 2. Actualizar CHANGELOG.md con fecha y cambios

# 3. Commit y tag
git add VERSION CHANGELOG.md
git commit -m "release: vMAJOR.MINOR.PATCH"
git tag -a vMAJOR.MINOR.PATCH -m "vMAJOR.MINOR.PATCH"

# 4. Verificar tag
git describe --tags --exact-match HEAD

# 5. Push (cuando corresponda)
git push origin main --tags
```

## Version History

| Version | Fecha | Descripcion |
|---------|-------|-------------|
| v2.0.0  | 2026-06-14 | NLP pipeline completo, 10 stages, 516 tests |
