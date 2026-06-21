---
area: dev
type: guide
module: offline_mode
version: 1.0
status: ACTIVE
---
# Modo Offline RECPL v2.0+

## ¿Qué funciona sin LLM?

| Stage | Con LLM | Sin LLM (offline) |
|-------|---------|-------------------|
| Intent classification | PerceptionUnit (LLM) | Reglas DFA (heurístico) |
| Planning | ReasoningEngine (LLM) | GoalTreePlanner (heurístico) |
| Preprocesador | — | Siempre determinista |
| Lexer | — | Siempre DFA |
| Parser | — | Siempre Lark |
| Semantic | — | Siempre Visitor |
| IR Generator | — | Siempre determinista |
| Synthesis | — | Siempre scaffold |
| UI Generator | — | Siempre con guarda |
| Validator | — | Siempre Chain of Responsibility |

## ¿Cómo usarlo?

```bash
python compiler-bot/agentic -p "crea modulo pagos" --offline
```

## ¿Qué cambia internamente?

- `PipelineConfig.offline` se setea a `True`
- `PerceptionUnit` salta el enriquecimiento con SentenceTransformers
- `ReasoningEngine` fuerza estrategia `"heuristic"` en lugar de `"llm"` incluso para planes complejos
- Los stages puramente sintácticos (preprocessor, lexer, parser, semantic, IR, synthesis, UI, validator) no se ven afectados
