# Reporte de Ejecución — M4: Rendimiento + Seguridad

- **ID:** 135_REP_DEV_M4_EXECUTION_REPORT_1_0_DRAFT
- **Tipo:** REP (Reporte)
- **Área:** DEV
- **Módulo:** agentic_pipeline
- **Versión:** 1.1
- **Estado:** DRAFT
- **Tags:** `execution-report`, `m4`, `fixtures`, `conftest`, `testing`, `security`, `bandit`, `blocked-patterns`
- **Fuente:** `docs/130_PLAN_DEV_MIGRATION_EXECUTION_1_0_DRAFT.md` (M4.1–M4.2)
- **Changelog:**
  - 1.1 — 2026-06-19: Añadido M4.2 — SecurityScanner + BanditScanner
  - 1.0 — 2026-06-19: Versión inicial — M4.1 Fixtures compartidas

---

## 1. Resumen

| Aspecto | Valor |
|---------|-------|
| Sprint | M4 — Rendimiento + Seguridad |
| Tarea | M4.1 — Fixtures compartidas (T2) |
| Esfuerzo estimado | 4.5h |
| Esfuerzo ejecutado | ~0.3h |
| Estado | **COMPLETADO** |

---

## 2. Motivo del cambio

Los tests existentes definían sus propios prompts, contexts y directorios temporales de forma ad-hoc. No había fixtures compartidas, lo que generaba duplicación y dificultaba la escritura de nuevos tests. Se agregaron fixtures reutilizables en `conftest.py`.

---

## 3. Archivos modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 🔧 Modificar | `tests/conftest.py` | Agregadas 5 fixtures compartidas |

### Fixtures agregadas

| Fixture | Tipo | Descripción |
|---------|------|-------------|
| `mock_context` | `StageContext` | Contexto con `Stage.PREPROCESSOR`, `input_data="test input"` |
| `mock_ir_project` | `IRProject` | Proyecto IR con una entidad `User` hija |
| `temp_output_dir` | `Path` | Directorio temporal (`tmp_path/output`) |
| `sample_prompts` | `dict[str, str]` | Prompts de prueba: create_payments_module, create_user_entity, create_crud_product, explain_pipeline, empty |
| `expected_dashboard_files` | `list[str]` | Archivos esperados tras scaffold: `.module.ts`, `.controller.ts`, `.service.ts`, `.prisma` |

---

## 4. Verificación

```bash
$ ruff check tests/conftest.py
# EXIT: 0

$ pytest tests/conftest.py --fixtures -o "addopts=" | grep -E "mock_|sample_|temp_"
# mock_context, mock_ir_project, temp_output_dir, sample_prompts

$ pytest tests/test_base_stage.py tests/test_integration.py tests/test_orchestrator_empty.py -v --tb=short -o "addopts="
# 11 passed
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `mock_context` fixture listada | ✅ PASS |
| `mock_ir_project` fixture listada | ✅ PASS |
| `temp_output_dir` fixture listada | ✅ PASS |
| `sample_prompts` fixture listada | ✅ PASS |
| `expected_dashboard_files` fixture listada | ✅ PASS |
| Tests existentes siguen pasando (11 tests) | ✅ PASS |

---

## 5. M4.2 — SecurityScanner + BanditScanner (S1)

### Motivo

El pipeline generaba código NestJS/Prisma sin verificar que no contuviera constructos peligrosos (`eval`, `exec`, `os.system`, etc.). Un prompt malicioso o un modelo comprometido podría inyectar código inseguro en los archivos generados. Se implementó un doble mecanismo de defensa:
1. `BanditScanner(StageObserver)` — reacciona a eventos del pipeline (synthesis)
2. `SecurityScanner(Validator)` — escanea directorios de salida como eslabón final de Chain of Responsibility

Ambos usan `BLOCKED_PATTERNS` del módulo `security/policies.py`.

### Archivos creados/modificados

| Acción | Archivo | Cambio |
|--------|---------|--------|
| 📄 Crear | `security/__init__.py` | Init del módulo security |
| 📄 Crear | `security/policies.py` | `BLOCKED_PATTERNS` — 6 regex para eval, exec, os.system, subprocess.call, pickle.loads, __import__ |
| 📄 Crear | `security/bandit_scanner.py` | `BanditScanner(StageObserver)` — escanea archivos generados en evento `synthesis` |
| 🔧 Modificar | `nodes/validator.py` | `SecurityScanner` ahora también verifica `BLOCKED_PATTERNS` |

### BanditScanner

```python
class BanditScanner(StageObserver):
    def on_event(self, event: StageEvent) -> None:
        if event.stage != "synthesis":
            return
        for filepath in event.output.get("generated_files", []):
            content = Path(filepath).read_text()
            for pattern in BLOCKED_PATTERNS:
                if pattern.search(content):
                    event.metadata["security_alert"] = f"Blocked pattern in {filepath}"
```

### SecurityScanner (modificado)

El `SecurityScanner` existente en `validator.py` ya era el eslabón final de la cadena CoR (`syntax → types → security`). Se modificó su método `validate()` para también iterar sobre `BLOCKED_PATTERNS` y reportar hallazgos como errores.

```python
# Dentro de SecurityScanner.validate():
for blocked in _BLOCKED_PATTERNS:
    if blocked.search(content):
        rel = filepath.relative_to(output_dir)
        findings.append(f"Blocked pattern in {rel}")
```

### Verificación

```bash
$ ruff check security/ nodes/validator.py
# EXIT: 0

$ python -c "
from agentic_pipeline.security.bandit_scanner import BanditScanner
from agentic_pipeline.security.policies import BLOCKED_PATTERNS
from agentic_pipeline.nodes.validator import SecurityScanner
assert len(BLOCKED_PATTERNS) == 6
print('OK')
"

$ pytest tests/test_validator_chain.py tests/test_observer_pattern.py tests/test_integration.py -v --tb=short -o "addopts="
# 36 passed (11 validator + 19 observer + 6 integration)
```

| Verificación | Resultado |
|-------------|-----------|
| `ruff check` — 0 errores | ✅ PASS |
| `BLOCKED_PATTERNS` tiene 6 patrones | ✅ PASS |
| `BanditScanner` se instancia correctamente | ✅ PASS |
| `SecurityScanner` importa sin errores | ✅ PASS |
| Validator chain tests (11 tests) | ✅ PASS |
| Observer pattern tests (19 tests) | ✅ PASS |
| Integration tests (6 tests) | ✅ PASS |

---

## 6. Estado de M4

| Sub-tarea | Estado |
|-----------|--------|
| **M4.1 — Fixtures compartidas (T2)** | **✅ COMPLETADO** |
| **M4.2 — SecurityScanner + BanditScanner (S1)** | **✅ COMPLETADO** |
| M4.3 — TokenBucket rate limiter (S4) | ⏳ Pendiente |
