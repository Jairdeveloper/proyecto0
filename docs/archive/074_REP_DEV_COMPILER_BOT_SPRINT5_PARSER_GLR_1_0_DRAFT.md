---
id: 074
area: dev
type: rep
module: compiler_bot
version: 1.0
status: IMPLEMENTED
tags:
  - sprint
  - parser
  - lark
  - glr
  - ast
summary: Reporte Sprint 5 — Parser GLR con Lark Earley, AST Composite y 4 gramáticas de dominio
keywords:
  - parser
  - lark
  - earley
  - ast
  - glr
  - gramatica
  - proyecto
  - ui
  - datos
  - infraestructura
changelog:
  - version: 1.0
    date: 2026-06-14
    description: Documento inicial del Sprint 5
---

# 074_REP_DEV_COMPILER_BOT_SPRINT5_PARSER_GLR_1_0_DRAFT

## Resumen

Sprint 5 completado. Implementación del Parser GLR (etapa 4 del pipeline RECPL v2.0) usando Lark con parser Earley y 4 gramáticas de dominio. Se crearon nodos AST con patrón Composite, un selector de gramática por palabras clave, y filtro de stop words. El parser se integró en el orquestador como nodo entre lexer y output.

## Logros

- **4 gramáticas Lark**: `project_grammar.lark`, `ui_grammar.lark`, `data_grammar.lark`, `infra_grammar.lark`
  - Project: páginas, módulos, componentes UI
  - UI: layouts, secciones, componentes específicos
  - Data: entidades, atributos con tipos
  - Infra: bases de datos, servicios, recursos con valores numéricos
- **AST Composite**: `nodes/ast_nodes.py` — `ProjectNode`, `PageNode`, `ComponentNode`, `EntityNode`, `InfraNode` con métodos `evaluate()`, `validate()`, `to_ir()`
- **ParserGLR stage**: `nodes/parser.py`
  - Receptor de tokens (dict) o texto plano
  - Limpieza de stop words vía regex
  - Selector de gramática por dominio
  - AST builder por gramática
  - Manejo de errores con mensajes descriptivos
  - Pipeline de 5 pasos: receive_mission → analyze → reflect_and_plan → act → learn_and_improve
- **Integración en orquestador**: `orchestrator.py` — pipeline `input → preprocessor → lexer → parser → output`
- **37 tests**: todos pasando (AST, gramática, edge cases, integración)

## Problemas encontrados y soluciones

| Problema | Solución |
|----------|----------|
| AST builder no manejaba nodos `section` intermedios del árbol Lark | Se agregó iteración recursiva sobre `section` → `page_def`/`module_def` |
| CNAME es Token en Lark, no Tree — los builders usaban `isinstance(child, Tree)` | Se cambió a `isinstance(child, Token) and child.type == "CNAME"` |
| Gramática infra no aceptaba números (`"cpu 4"`) | Se agregó `NUMBER` a `resource_item` y se hizo CONNECTOR opcional |
| Test usaba fixture `parser` de otra clase sin herencia | Se creó fixture local en cada clase de test |
| Stop words causaban ambigüedad en Lark | Se filtraron con regex antes de parsear |

## Archivos creados/modificados

| Archivo | Cambio |
|---------|--------|
| `nodes/ast_nodes.py` | Creado — AST Composite nodes |
| `nodes/parser.py` | Creado — ParserGLR stage (317 líneas) |
| `grammars/project_grammar.lark` | Creado — Gramática proyecto |
| `grammars/ui_grammar.lark` | Creado — Gramática UI |
| `grammars/data_grammar.lark` | Creado — Gramática datos |
| `grammars/infra_grammar.lark` | Creado — Gramática infra |
| `tests/test_parser_project.py` | Creado — 223 líneas, 25 tests |
| `tests/test_parser_ui.py` | Creado — 73 líneas, 12 tests |
| `orchestrator.py` | Modificado — conectado parser node |
| `pyproject.toml` | Modificado — dependencia `lark>=1.3.0` |

## Tests

```
155 passed in 1.80s
```

- **AST nodes**: 12 tests (ProjectNode, PageNode, ComponentNode, EntityNode, InfraNode)
- **Grammar selection**: 4 tests (project, data, infra, ui)
- **ParserGLR stage**: 12 tests (receive_mission, analyze, act, execute, edge cases, multi-grammar)
- **UI grammar**: 7 tests (page, section, infra, integration)
- **Orquestador**: 2 tests (compile, run)
- **Otros**: 118 tests de sprints anteriores

## Riesgos

- Las gramáticas Lark son específicas del dominio y pueden no cubrir todos los casos del lenguaje natural
- El filtro de stop words puede eliminar palabras significativas en algunos contextos
- El AST builder para infra no extrae nombres CNAME correctamente (usa `scan_values` para INFRA_KEYWORD)
- No hay manejo de ambigüedad entre gramáticas cuando el input podría pertenecer a múltiples dominios

## Próximos pasos

- Sprint 6: Semantic Analyzer — validación semántica del AST, resolución de símbolos, chequeo de tipos
- Mejorar los AST builders para extraer nombres y relaciones con más precisión
- Agregar gramática `mobile` para dominio mobile
- Implementar desambiguación cuando el selector de gramática tiene baja confianza
