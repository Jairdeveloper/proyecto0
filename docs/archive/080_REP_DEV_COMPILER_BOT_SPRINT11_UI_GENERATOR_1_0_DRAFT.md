---
id: 080
area: DEV
type: REP
module: COMPILER_BOT
version: 1.0
status: DRAFT
tags:
  - sprint
  - ui-generator
  - builder-pattern
  - design-tokens
  - responsive-engine
  - accessibility-injector
  - animation-injector
  - component-factory
summary: >-
  Reporte Sprint 11 — UI Generator. Implementacion de UIComponentBuilder
  (Builder pattern 5 pasos), DesignTokens (paleta SaaS), ResponsiveEngine
  (mobile-first), AccessibilityInjector (ARIA), AnimationInjector (CSS),
  ComponentFactory (Form, Table), y UIGenerator como PipelineStage.
keywords:
  - sprint-11
  - ui-generator
  - builder-pattern
  - design-tokens
  - responsive-engine
  - accessibility
  - animations
  - component-factory
  - fluent-interface
  - mobile-first
changelog:
  - version: '1.0'
    date: 2026-06-14
    description: Documento inicial del Sprint 11
---

# 080_REP_DEV_COMPILER_BOT_SPRINT11_UI_GENERATOR_1_0_DRAFT

## Resumen

Sprint 11 completado siguiendo las especificaciones del plan maestro en
`docs/068_PLAN_DEV_COMPILER_BOT_SCALE_EXECUTION_1_0_DRAFT.md`.

Se implemento el UI Generator con Builder pattern, DesignTokens, Responsive
Engine, Accessibility, y Animations. El UIGenerator se integro como
PipelineStage (etapa 10 del pipeline RECPL v2.0).

Pipeline completo: `input -> preprocessor -> lexer -> parser -> semantic_analyzer
-> ir_generator -> planner -> synthesis -> ui_generator -> validator -> output`

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `generators/design_tokens.py` | DesignTokens: colores, fuentes, spacing, breakpoints, CSS vars, Tailwind config |
| `generators/ui_component_builder.py` | UIComponentBuilder (5-step fluent), ComponentFactory (Form, Table) |
| `generators/responsive_engine.py` | ResponsiveEngine, AccessibilityInjector, AnimationInjector |
| `nodes/ui_generator.py` | UIGenerator PipelineStage (10 etapas en pipeline) |
| `tests/test_ui_builder.py` | 17 tests para builder y factory |
| `tests/test_responsive_engine.py` | 8 tests para responsive classes |
| `tests/test_accessibility_injector.py` | 11 tests para a11y y animaciones |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `generators/__init__.py` | Re-export de DesignTokens, ResponsiveEngine, AccessibilityInjector, AnimationInjector, UIComponentBuilder, ComponentFactory |
| `orchestrator.py` | Conectado ui_generator node entre synthesis y validator |

## Detalle de implementacion

### DesignTokens

Clase con estilo SaaS moderno (Indigo + Emerald):

```python
COLORS = {
    "primary": "#6366F1",      # Indigo
    "secondary": "#10B981",    # Emerald
    "background": "#FFFFFF",
    "surface": "#F9FAFB",
    "text": "#111827",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "error": "#EF4444",
}
FONTS = {"sans": "'Inter', sans-serif", "mono": "'JetBrains Mono', monospace"}
BORDER_RADIUS = "8px"
SPACING = {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "48px"}
BREAKPOINTS = {"sm": "640px", "md": "768px", "lg": "1024px", "xl": "1280px"}
```

Metodos:
- `as_css_vars()` — genera `:root { --color-primary: #6366F1; ... }`
- `tailwind_config()` — dict para configuracion de Tailwind
- `css()` — alias de as_css_vars()

### UIComponentBuilder

Builder pattern con interfaz fluida de 5 pasos:

```
build_structure(name, props)
    -> apply_styles(styles)
        -> add_behavior(events)
            -> add_accessibility(aria)
                -> add_animations(animations)
                    -> build() -> dict
```

Cada metodo retorna `self` para encadenamiento. `build()` produce un dict
contype, name, props, styles, events, aria, animations, children.

### ComponentFactory

Fabrica de componentes pre-construidos:

- `ComponentFactory.form(name, fields)`:
  - Inputs con placeholder, estilos, aria labels, animaciones
  - Boton submit con color primario, border radius, evento onClick
  - Form con layout flex column, gap, surface background, animacion fadeIn
  - Campos email/password por defecto, personalizables

- `ComponentFactory.table(name, columns)`:
  - Header (`thead`) con celdas (`th`) ordenables via onClick sortBy()
  - Estilos: width 100%, border-collapse, fuente sans
  - ARIA: role columnheader en cada th, role table en table
  - Animacion fadeIn

### ResponsiveEngine

Clases utilitarias mobile-first:

| Metodo | Proposito |
|--------|-----------|
| `responsive_class(base, sm, md, lg, xl)` | Genera clases responsive Tailwind |
| `grid_columns({default: 1, md: 2})` | Columnas de grid responsivas |
| `hide_at(breakpoint)` | `hidden md:block` |
| `show_at(breakpoint)` | `block md:hidden` |
| `container()` | Contenedor responsivo completo |
| `responsive_font({default: "base", lg: "lg"})` | Tamaños de fuente responsivos |

### AccessibilityInjector

Inyecta atributos ARIA en componentes:
- `inject(component)` — agrega `aria-label` (default nombre) y `role` (default
segun tipo: button, form, input, table, nav, header, footer, main, aside)
- `label(component, text)` — actualiza aria-label
- Mapa de roles por defecto para tipos comunes

### AnimationInjector

Inyecta animaciones CSS en componentes:
- `inject(component, animations)` — agrega config de animacion
- `to_css(animations)` — genera CSS con @keyframes (fadeIn, slideUp, slideIn)
- `to_tailwind(animations)` — genera clases Tailwind (animate-fadeIn, duration-300)

### UIGenerator

PipelineStage de 5 pasos:
1. `receive_mission`: recibe output de synthesis (tasks + ir_tree)
2. `analyze`: cuenta UI tasks
3. `reflect_and_plan`: planifica 5 acciones (inject tokens, build components,
   responsive, accessibility, animations)
4. `act`: genera archivos:
   - `design-tokens.css` — CSS variables
   - `responsive.css` — grid y container queries
   - `animations.css` — keyframes y clases de animacion
   - `design-tokens.json` — config para Tailwind
   - Componentes TSX (Form, Table, etc.) detectados desde IR tree y tasks
5. `learn_and_improve`: no implementado

## Tests

444 tests pasando, 0 fallos, ruff check 0 errores.

Nuevos tests (Sprint 11):
- UIComponentBuilder: 7 tests (structure, styles, behavior, a11y, animations, fluent, build)
- ComponentFactory: 10 tests (form structure, inputs, submit, tokens, a11y, animations, table structure, header, cells, sort, responsive, custom fields)
- ResponsiveEngine: 8 tests (all breakpoints, base only, grid, responsive grid, hide, show, container, font)
- AccessibilityInjector: 4 tests (inject, preserve, default roles, label)
- AnimationInjector: 6 tests (default, custom, to_css, to_tailwind, duration mapping)

## Pipeline actual

```
input -> preprocessor -> lexer -> parser -> semantic_analyzer
    -> ir_generator -> planner -> synthesis -> ui_generator
    -> validator -> output
```

11 etapas conectadas via LangGraph StateGraph.

## Riesgos

- UIGenerator depende de ReactGenerator en Synthesis para componentes base
  (los componentes UI se generan en paralelo, no como reemplazo)
- ComponentFactory solo produce Form y Table — mas componentes (Navbar,
  Sidebar, Modal, Card, etc.) requieren extension
- DesignTokens esta hardcodeado en Python — no hay sobrecarga desde IRConfig
- `to_tailwind()` usa mapeo de duraciones fijo (200/300/400/500ms) —
  duraciones no estandar requieren extension
- El CSS generado no esta minificado — recomendable pasar por CodeFormatter
- AccessibilityInjector asigna roles genericos — proyectos especificos
  pueden necesitar roles WAI-ARIA personalizados

## Proximos pasos

- Sprint 12: Feedback Loop + Refinamiento (SQLite metrics, AST cache, weight tuning)
- Agregar mas componentes: Navbar, Sidebar, Card, Modal, Toast, Spinner
- Soportar sobrecarga de DesignTokens desde IRConfig en el IR tree
- Integrar animaciones con Framer Motion (opcional via target detection)
- Agregar variantes de componentes (primary, secondary, outline, ghost)
- Minificar CSS generado (postcss-clean o similar)
