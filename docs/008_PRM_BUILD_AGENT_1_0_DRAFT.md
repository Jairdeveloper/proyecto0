---
id: 018
area: prompts
type: PRM
module: build-agent
version: 1.0
status: DRAFT
author: system
created: 2026-05-23
last_updated: 2026-05-23
dependencies: []
tags:
  - prompt
  - build-agent
  - conventions
summary: "Convenciones para la creación de prompts de subagentes opencode: estructura, contenido, template y ejemplos de aplicación."
keywords:
  - prompts
  - agentes
  - convenciones
  - template
  - subagentes
  - opencode
changelog:
  - version: 1.0
    date: 2026-05-23
    author: system
    changes:
      - "Creación inicial del documento"
---

# Build Agent Prompt Conventions

## Reference Files

- **AGENTS.md** — Primary agent guide at project root
- **prompts/build.txt** — Concise build agent prompt
- **opencode.json** — Model and prompt configuration
- **docs/MASTER_INDEX.md** — Knowledge base system map

## Prompt File Location

All prompt files live in `/prompts/` at project root (NOT in `~/.opencode/`).

## opencode.json

```json
{
  "model": "opencode/big-pickle",
  "prompts": [
    "{file:./prompts/build.txt}"
  ]
}
```

## Prompt Conventions

### Structure
1. **Identity statement** — "You are building @tienda/api..."
2. **Tech stack** — Framework, language, key libraries
3. **Architecture rules** — Non-negotiable patterns (3 global guards, @Public(), etc.)
4. **Commands** — Build, test, run, DB management
5. **Key patterns** — Payment provider, order lifecycle, RBAC, idempotency
6. **CI info** — What CI does (so agent can replicate locally)

### Content Guidelines
- Be concise — reference AGENTS.md for detailed info
- List critical gotchas (deleteOutDir: true, PBKDF2 not bcrypt)
- Include all npm scripts with descriptions
- Document env var requirements

## Instrucciones

[Instrucciones específicas y detalladas]

## Ejemplos

### Ejemplo 1: [DESCRIPCIÓN]

**Entrada:**
```
[Ejemplo de entrada]
```

**Salida esperada:**
```
[Ejemplo de salida]
```

## Variables

| Variable | Descripción | Tipo | Ejemplo |
|----------|-------------|------|---------|
| {variable1} | Descripción | string | ejemplo |

## Restricciones

- [Restricción 1]
- [Restricción 2]

## Referencias
```
- [Enlace a documentación relevante]
```

## Template

```markdown
You are building [project], a [description].

Tech stack: [list]

## Architecture rules
- [rule 1]
- [rule 2]

## Commands
[command 1]  # description
[command 2]  # description

## Key patterns
- [pattern 1]
- [pattern 2]
```

