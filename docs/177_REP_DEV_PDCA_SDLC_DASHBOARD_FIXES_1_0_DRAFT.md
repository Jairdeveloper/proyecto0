---
id: 177
area: dev
type: rep
module: pdca_sdlc_eventbus_dashboard
version: 1.0
status: IMPLEMENTED
tags:
  - report
  - fix
  - pdca-sdlc
  - dashboard
  - event-bus
  - static-files
  - async-handlers
summary: "Reporte de 2 fixes aplicados al dashboard PDCA-sdlc: resolucion de rutas de archivos estaticos y manejo correcto de handlers async en wildcards del EventBus."
keywords:
  - fix
  - dashboard
  - static
  - event-bus
  - async
  - wildcard
  - 404
  - pagina-en-blanco
changelog:
  - version: 1.0
    date: 2026-06-20
    author: system
    changes:
      - "Fix 1: resolucion de ruta doble en _send_static() para archivos bajo /static/"
      - "Fix 2: await de coroutines en wildcard_handlers del EventBus"
      - "224 tests PASS, ruff 0 errores"
---

# Reporte de Fixes: PDCA-sdlc Dashboard

## Resumen

Se corrigieron 2 bugs en el modulo `pdca_sdlc` que causaban que el
dashboard web se mostrara en blanco (sin CSS/JS) y que los handlers
async de wildcards en el EventBus no se ejecutaran.

## Fix 1 — Ruta de archivos estaticos mal resuelta

**Archivo:** `compiler-bot/pdca_sdlc/dashboard/app.py`
**Sintoma:** La pagina HTML cargaba pero sin estilos ni JavaScript.
El navegador recibia 404 para `/static/dashboard.css` y
`/static/dashboard.js`. KPIs mostraban `--` y la tabla de proyectos
quedaba en `Cargando...` porque `loadDashboard()` nunca se ejecutaba.

**Causa raiz:** `_send_static()` concatenaba `static_dir` con el path
crudo. Cuando el path inclua el prefijo `/static/` (ej:
`/static/dashboard.js`), `path.lstrip("/")` producia
`static/dashboard.js`, y al unir con `static_dir` (que ya es
`.../dashboard/static/`) resultaba en la ruta inexistente
`.../dashboard/static/static/dashboard.js`.

**Cambio:** Se limpia el prefijo `/static/` antes de resolver la ruta:

```python
# Antes:
requested = (static_dir / path.lstrip("/")).resolve()

# Despues:
clean = path[len("/static/"):] if path.startswith("/static/") else path
requested = (static_dir / clean.lstrip("/")).resolve()
```

Para paths como `/` (index.html), `clean` queda igual a `""` y
`clean.lstrip("/")` queda como `""`, resultando en
`static_dir / "index.html"` — correcto.

## Fix 2 — Handlers async de wildcards no se ejecutaban

**Archivo:** `compiler-bot/pdca_sdlc/core/event_bus.py`
**Sintoma:** Los handlers registrados con wildcard (`*`, `>`) no se
ejecutaban. Si el handler era `async def`, la llamada sin `await` solo
creaba un objeto coroutine que nunca se consumia.

**Causa raiz:** En `AsyncEventBus.publish()`, el bucle de
`_wildcard_handlers` llamaba `handler(event.topic, event)` directamente
sin verificar si era una coroutine. El codigo tenia un `if` con `pass`
que no hacia nada.

**Cambio:** Se importa `asyncio` y se usa
`asyncio.iscoroutinefunction()` para bifurcar entre `await` y llamada
directa:

```python
# Antes:
if hasattr(handler, "_async") or hasattr(handler, "__call__"):
    pass
handler(event.topic, event)

# Despues:
if asyncio.iscoroutinefunction(handler):
    await handler(event.topic, event)
else:
    handler(event.topic, event)
```

**Nota:** Los agentes actuales (`adaptation`, `requirements_analyst`,
`coder`) usan subscripciones exactas (sin wildcard), por lo que su ruta
pasa por `publish_async()` del bus interno que ya hace `await`
correctamente de coroutines. Este fix previene el bug para futuros
agentes que usen wildcards.

## Verificacion

| Comando | Resultado |
|---------|-----------|
| `ruff check .` | All checks passed |
| `ruff format .` | 1 file reformatted (app.py) |
| `pytest tests/ -v` | 224 passed in 29.20s |

## Smoke test manual

```sh
python -m pdca_sdlc.main "crear modulo de pagos" --dashboard --port 9876
# Abrir http://127.0.0.1:9876
# Debe mostrar KPIs con datos, proyectos, distribucion, timeline
```

## Archivos modificados

| Archivo | Lineas | Cambio |
|---------|--------|--------|
| `compiler-bot/pdca_sdlc/dashboard/app.py` | 57-60 | Strip `/static/` prefix en `_send_static()` |
| `compiler-bot/pdca_sdlc/core/event_bus.py` | 10, 148-151 | `await` para async handlers en wildcards |
| `docs/177_REP_DEV_PDCA_SDLC_DASHBOARD_FIXES_1_0_DRAFT.md` | nuevo | Este reporte |
