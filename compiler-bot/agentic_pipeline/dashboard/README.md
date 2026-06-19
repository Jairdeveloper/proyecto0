# RECPL Dashboard

Dashboard local de metricas del pipeline RECPL. Sin dependencias externas,
sin build step.

## Uso rapido

```sh
./compiler-bot/agentic --dashboard
# Abrir http://127.0.0.1:8765
```

## Flags

| Flag | Default | Descripcion |
|------|---------|-------------|
| `--dashboard` | — | Arranca servidor dashboard |
| `--host` | `127.0.0.1` | Host del servidor |
| `--port` | `8765` | Puerto del servidor |

## Endpoints

| Metodo | Ruta | Respuesta |
|--------|------|-----------|
| `GET` | `/` | HTML del dashboard |
| `GET` | `/api/health` | JSON backend + timestamp |
| `GET` | `/api/summary` | JSON resumen global |
| `GET` | `/api/stages` | JSON lista de stages |
| `GET` | `/api/stages/<stage>/recent?limit=20` | JSON registros recientes |
| `GET` | `/api/prompt-chain` | JSON resumen prompt chain |

## Componentes

| Archivo | Proposito |
|---------|-----------|
| `__init__.py` | Init del paquete, exporta DashboardService |
| `service.py` | View model layer sobre MetricsStore |
| `app.py` | Servidor HTTP stdlib con routing |
| `static/index.html` | UI del dashboard |
| `static/dashboard.css` | Estilos responsive |
| `static/dashboard.js` | Logica frontend |

## Notas

- Las metricas son acumuladas.
- El dashboard usa `MetricsStore`.
- Si `_sqlite3` no existe, se usa JSON fallback en `/tmp/agentic_metrics_json_fallback/`.
- Tests: `python -m pytest tests/test_dashboard_service.py tests/test_dashboard_app.py -q -o addopts=`
