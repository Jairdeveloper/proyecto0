---
id: ONB-004
area: DEV
type: GUIDE
module: ONBOARDING
version: 1.0
status: ACTIVE
tags:
  - onboarding
  - debugging
  - debugger
summary: "Tutorial 4: como depurar el pipeline con --debug en sus 4 modos."
---

# Tutorial 4: Depurar el Pipeline con --debug

## Modos de depuracion

El CLI `compiler-bot/agentic` soporta 4 modos de debug:

```bash
./compiler-bot/agentic --prompt "crea un modulo" --debug trace    # (default-like)
./compiler-bot/agentic --prompt "crea un modulo" --debug timing   # tiempo por stage
./compiler-bot/agentic --prompt "crea un modulo" --debug inspect  # snapshots JSON
./compiler-bot/agentic --prompt "crea un modulo" --debug step     # pausa entre stages
```

## Modo trace

Muestra cada stage, su estado (OK/FAIL), tamano del output y metricas:

```
  [intent] OK  (1.2KB)  ← nodes/intent_stage.py:36
    metrics: intent=create confidence=0.95 domain=web entities=2
  [preprocessor] OK  (0.8KB)  ← nodes/preprocessor.py:120
```

## Modo timing

Muestra tiempo por stage mas grafico de barras al final:

```
  [intent] OK  0.045s  ← nodes/intent_stage.py:36
  [parser] OK  0.032s  ← nodes/parser.py:295
  ...
  === Timing Summary ===
  intent           0.045s ████████████████░░░░ 15.2%
  parser           0.032s ███████████░░░░░░░░░ 10.8%
  TOTAL            0.296s
```

## Modo inspect

Guarda snapshots JSON de cada stage en `debug_output/<session>/`:

```bash
./compiler-bot/agentic --prompt "crea un modulo" --debug inspect
ls debug_output/
# → 20260615_143000/intent.json, preprocessor.json, lexer.json, ...
```

## Modo step

Como trace pero pausa entre stages (pide Enter para continuar).

## Ver output_data

```bash
./compiler-bot/agentic --prompt "crea un modulo" --debug trace --show-output
```

Esto muestra el contenido completo del `output_data` de cada stage.
