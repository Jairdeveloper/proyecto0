# RECPL Pipeline v2.0

Compilador de lenguaje natural a codigo IR (Intermediate Representation).

```mermaid
graph LR
    A[INPUT] --> B[Intent Stage]
    B --> C[Preprocessor]
    C --> D[Lexer]
    D --> E[Parser]
    E --> F[Semantic Analyzer]
    F --> G[IR Generator]
    G --> H[Planner]
    H --> I[Synthesis]
    I --> J[UI Generator]
    J --> K[Validator]
    K --> L[OUTPUT]
```

## Quick Start

```bash
pip install -e compiler-bot/agentic_pipeline/
./compiler-bot/agentic --prompt "crea un modulo de pagos con NestJS"
```

## Documentacion

- [Onboarding: entender el pipeline](onboarding/01_pipeline.md)
- [API Reference](api/base_stage.md)
- [Indice completo](INDEX.md)
