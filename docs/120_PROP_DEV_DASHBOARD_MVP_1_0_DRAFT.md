---
id: "P01"
area: "DEV"
type: "PROP"
module: "RECPL_ADAPTIVE"
version: "2.0"
status: "DRAFT"
tags: ["proposal", "adaptive", "requirement-decomposer", "pipeline"]
summary: "Propuesta de implementacion adaptativa — el pipeline RECPL procesa cualquier entrada de lenguaje natural generando codigo util, sin extender DFA/gramatica/IR por cada nuevo tipo de output. El RequirementDecomposer es el componente central adaptativo."
changelog:
  - version: "2.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Revision completa — enfoque adaptativo centrado en RequirementDecomposer, elimina extension prescriptiva de DFA/gramatica/IR"
  - version: "1.0"
    date: "2026-06-18"
    author: "Arquitecto Senior"
    description: "Version inicial — enfoque prescriptivo (extender DFA, gramatica, IR para charts)"
---

# Propuesta de Implementacion: Pipeline Adaptativo

> **Pipeline:** `INTENT → PREPROCESSOR → LEXER → PARSER → REQUIREMENT_DECOMPOSER → SEMANTIC → IR → PLANNER → SYNTHESIS → UI → VALIDATOR`  
> **Principio:** El sistema debe adaptarse a **cualquier entrada**, no solo a aquellas para las que explicitamente extendemos DFA/gramatica/IR.  
> **Componente clave:** `RequirementDecomposer` (hoy dead code) como capa adaptativa central.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Problema del Enfoque Prescriptivo](#2-problema-del-enfoque-prescriptivo)
3. [Enfoque Adaptativo](#3-enfoque-adaptativo)
4. [Flujo del Pipeline — Stage por Stage](#4-flujo-del-pipeline--stage-por-stage)
5. [Requisito 0: Cablear RequirementDecomposer](#5-requisito-0-cablear-requirementdecomposer)
6. [El RequirementDecomposer como Capa Adaptativa](#6-el-requirementdecomposer-como-capa-adaptativa)
7. [El Generador Adaptativo](#7-el-generador-adaptativo)
8. [Plan de Implementacion](#8-plan-de-implementacion)
9. [Ejemplos de Entrada y Salida](#9-ejemplos-de-entrada-y-salida)
10. [Riesgos y Mitigacion](#10-riesgos-y-mitigacion)
11. [Criterios de Aceptacion](#11-criterios-de-aceptacion)
12. [Estimacion de Esfuerzo](#12-estimacion-de-esfuerzo)

---

## 1. Resumen Ejecutivo

El pipeline RECPL de 10 etapas tiene un componente olvidado: `RequirementDecomposer` (`nodes/requirement_decomposer.py`). Existe como archivo, tiene su `Stage.REQUIREMENT_DECOMPOSER` en el enum, usa LLM tools (`DomainClassifier`, `EntityExtractor`, `FeatureIdentifier`, `ConstraintDetector`, `StoryGenerator`) para producir un `RequirementGraph` rico en semantica, pero **nunca se cableo en el `NODE_MAP` del orquestador**.

La propuesta original (v1.0) planeaba extender DFA, gramatica Lark, IR nodes y generadores especificamente para "graficos de dashboard". Eso es **prescriptivo**: cada nuevo tipo de output requiere modificar 10+ archivos del pipeline. Este sistema no escala.

La propuesta revisada (v2.0) es **adaptativa**: cablear `RequirementDecomposer` en el pipeline (tras el parser, antes del semantico) para que capture semanticamente lo que el parser formal no pudo resolver, y usar esa salida para guiar al planner y al generador. El sistema asi funciona para **cualquier entrada**, no solo para las que conocemos de antemano.

### Cambio Fundamental

| Aspecto | v1.0 (Prescriptivo) | v2.0 (Adaptativo) |
|---------|--------------------|--------------------|
| **Dashboard** | Extender DFA/tokens, gramatica, IR, generador | `RequirementDecomposer` infiere features desde el texto |
| **Costos por nuevo tipo** | 10-17 archivos modificados | 0-1 archivo (template) |
| **Limite superior** | Solo lo que programamos explicitamente | Cualquier input razonable |
| **RequirementDecomposer** | Dead code (se propuso eliminar) | Componente central del pipeline |
| **LLM** | Opcional, solo en prompt chain | Integrado en pipeline como fallback semantico |

---

## 2. Problema del Enfoque Prescriptivo

### 2.1 Que proponia v1.0

Para que el sistema genere un dashboard con graficos desde el prompt "Crea dashboard web para graficos", v1.0 proponia:

| Componente | Cambio | Archivos |
|-----------|--------|----------|
| Lexer | Agregar tokens CHART, BAR_CHART, LINE_CHART, PIE_CHART, KPI, WIDGET | 2 |
| Gramatica | Reglas `chart_def`, `dashboard_def`, 9 nuevos terminales | 2 |
| AST | Nuevo `ChartNode` | 2 |
| Parser | `_build_chart_def()`, `_build_dashboard_def()` | 1 |
| IR | Nuevos `IRChart`, `IRDashboard` | 2 |
| Semantico | Validador chart types | 2 |
| Planner | Template dashboard, target chart | 1 |
| Synthesis | Target chart, ChartGenerator | 2 |
| Generators | ChartGenerator, DashboardGenerator, 5 templates | 7 |

**Total: ~29 archivos para un solo tipo de output.**

### 2.2 Por que no escala

Cada nuevo tipo de output (formularios, tablas, graficos, mapas, calendarios, etc.) requiere repetir el mismo proceso:

1. Definir tokens en DFA
2. Extender gramatica Lark
3. Crear AST node
4. Agregar builders al parser
5. Crear IR node
6. Extender validador semantico
7. Crear generador
8. Escribir templates
9. Escribir tests

**Esto es insostenible.** El sistema solo puede generar lo que explicitamente programamos. Peor aun: el pipeline ya tiene un componente diseñado exactamente para evitar esto — `RequirementDecomposer` — pero nunca se conecto.

---

## 3. Enfoque Adaptativo

### 3.1 Principio

> El pipeline formal (lexer → parser → semantic) produce lo que puede.  
> El `RequirementDecomposer` completa lo que el pipeline formal no pudo resolver.  
> El planner y synthesis usan la informacion combinada para generar codigo util.

### 3.2 Pipeline Modificado

```
INPUT → INTENT → PREPROCESSOR → LEXER → PARSER → REQUIREMENT_DECOMPOSER → SEMANTIC → IR → PLANNER → SYNTHESIS → UI → VALIDATOR
                                                     ↑
                                  Recibe: AST parcial + tokens + raw text
                                  Produce: RequirementGraph (features, entities, constraints, stories)
                                  Usa: LLM tools + reglas heuristicas
                                  Efecto: SEMANTIC recibe AST + RequirementGraph
                                         PLANNER usa RequirementGraph.features para crear tareas
                                         SYNTHESIS usa RequirementGraph para seleccionar generador
```

### 3.3 Flujo de Decision

```
INPUT: "Crea dashboard web para graficos para Proyecto0"

INTENT ──► CREATE, domain=DASHBOARD, entities=[dashboard, graficos, proyecto0]

PREPROCESSOR ──► texto normalizado

LEXER ──► Tokens: [ACTION_CREATE, DASHBOARD, WEB, PREP, ...]
              ↑
        No existe token CHART, ni BAR_CHART, etc.
        El lexer produce tokens genericos para "graficos"
        (lo reconoce como ENTITY o COMP_KEYWORD segun gramatica)

PARSER ──► AST PARCIAL:
             ProjectNode("proyecto0")
               └── PageNode("dashboard")        ← se reconoce "dashboard"
                     └── ComponentNode("graficos", component_type="grafico")
                           ↑                    ← se reconoce "graficos" como
                         Sin estructura interna    COMP_KEYWORD pero no hay
                         (options, series, etc.)  reglas de produccion para chart

       ┌─────────────────────────────────────────────────────────────────────
       │  AQUI OCURRE LA ADAPTACION:
       │  RequirementDecomposer recibe el AST parcial + raw text + tokens
       │  y usa LLM tools para expandir:
       │    features: ["dashboard", "charts", "bar chart", "line chart", "kpi"]
       │    entities: [{name: "Ventas", type: "metric"}, ...]
       │    constraints: ["responsive", "real-time"]
       │    user_stories: ["Como admin quiero ver metricas clave"]
       │
       │  Este RequirementGraph se adjunta al AST como metadata
       └─────────────────────────────────────────────────────────────────────

SEMANTIC ──► AST validado + SymbolTable poblada
             El RequirementGraph enriquece la tabla de simbolos:
               $features → ["dashboard", "charts", "kpi"]
               $domain → "dashboard"

IR ──► IRProject con IRPage("dashboard") + metadata features en IRConfig

PLANNER ──► Usa RequirementGraph.features para crear tareas:
              - ui: dashboard/page.tsx
              - ui: components/BarChart.tsx (porque features contiene "bar chart")
              - ui: components/KPICard.tsx   (porque features contiene "kpi")
              - ui: components/ChartWidget.tsx
              - infra: package.json (+ recharts)

SYNTHESIS ──► Genera archivos. Para componentes UI sin generador dedicado,
              usa AdaptiveGenerator que produce codigo React generico
              con Recharts si features contiene "chart".

UI ──► Renderiza componentes con datos mock
```

### 3.4 Comparacion Prescriptivo vs Adaptativo

| Aspecto | Prescriptivo (v1.0) | Adaptativo (v2.0) |
|---------|--------------------|--------------------|
| **Archivos por nuevo output** | 10-29 | 1-3 (solo templates si se desea output especifico) |
| **RequirementDecomposer** | Dead code, se elimina | Se cablea, es central |
| **Cobertura de inputs** | Solo los explicitamente tokenizados | Cualquier input razonable |
| **Uso de LLM** | Solo en prompt chain | Integrado en pipeline como fallback semantico |
| **Parser falla?** | Pipeline produce AST vacio o error | RequirementDecomposer rescata con LLM |
| **Nuevo tipo de UI** | Modificar 10+ archivos | No tocar pipeline, solo template (opcional) |
| **Costo por iteracion** | Alto (cambios en pipeline compilado) | Bajo (solo cambiar prompt LLM) |

---

## 4. Flujo del Pipeline — Stage por Stage

### Stage 1: INTENT (PerceptionUnit)

**Input:** Raw text  
**Output:** `EnrichedInput` con intent, entidades, slots

```
intent: CREATE
domain: DASHBOARD
entities:
  - type: TECH
    value: dashboard
  - type: COMPONENT
    value: graficos
slots:
  - target: Proyecto0
  - action: crear
  - feature: dashboard_web
```

**Estado actual:** Ya funciona. No requiere cambios.

### Stage 2: PREPROCESSOR

**Input:** Raw text  
**Output:** Texto normalizado

**Estado actual:** Ya funciona. No requiere cambios.

### Stage 3: LEXER

**Input:** Texto normalizado  
**Output:** `list[Token]`

```
[ACTION_CREATE, DASHBOARD, WEB, PREP_PARA, COMPONENT("graficos"), ...]
```

**Estado actual:** El lexer reconoce `DASHBOARD` via DomainDFA y `graficos` como keyword.  
**Cambio necesario:** **Ninguno.** El lexer produce tokens genericos. No necesitamos `CHART`, `BAR_CHART`, etc. El RequirementDecomposer interpreta semanticamente lo que el lexer dejo como generico.

### Stage 4: PARSER

**Input:** Tokens  
**Output:** AST (puede ser parcial)

```
ProjectNode("proyecto0")
  └── PageNode("dashboard")
        └── ComponentNode("graficos", component_type="grafico")
```

**Estado actual:** El parser reconoce `dashboard` como COMP_KEYWORD y `graficos` como componente. No produce estructura interna de chart (options, series, etc.).  
**Cambio necesario:** **Ninguno.** El AST parcial es suficiente. El RequirementDecomposer completara la semantica faltante.

### Stage 5: REQUIREMENT_DECOMPOSER (NUEVO — cableado)

**Input:** `AST parcial + raw text + tokens + enriched context`  
**Output:** `RequirementGraph` con features, entidades, constraints, user_stories

```python
RequirementGraph(
    domain="dashboard",
    entities=[
        {"name": "Ventas", "type": "metric", "values": ["Ene", "Feb", "Mar"]},
        {"name": "Usuarios", "type": "metric"},
    ],
    features=[
        "dashboard",
        "charts",
        "bar chart for monthly sales",
        "line chart for user trends",
        "kpi cards for key metrics",
        "responsive layout",
    ],
    constraints=["responsive", "read-only"],
    user_stories=[
        "Como admin quiero ver metricas clave del proyecto",
    ],
    raw_text="Crea dashboard web para graficos para el proyecto actual Proyecto0",
)
```

**Estado actual:** El archivo existe pero no esta en `NODE_MAP`. Ya usa `LLMOrchestrator`, `DomainClassifier`, `EntityExtractor`, `FeatureIdentifier`, `ConstraintDetector`, `StoryGenerator`.  
**Cambio necesario:** Cablearlo en `NODE_MAP` y pasarle el AST parcial + raw text + tokens.

### Stage 6: SEMANTIC ANALYZER

**Input:** AST + RequirementGraph  
**Output:** AST validado + SymbolTable enriquecida con RequirementGraph

**Cambio necesario:** El semantic analyzer debe leer el `RequirementGraph` del contexto y poblarlo en la symbol table como `$features`, `$domain`, `$entities`. No requiere validacion de chart types.

### Stage 7: IR GENERATOR

**Input:** AST + SymbolTable (con RequirementGraph)  
**Output:** IRProject con metadata de features en `IRConfig`

**Cambio necesario:** `IRConfig` debe incluir `features`, `domain`, `entities` del RequirementGraph. No requiere `IRChart` ni `IRDashboard`.

### Stage 8: PLANNER (ReasoningEngine)

**Input:** IRProject + RequirementGraph.features  
**Output:** Task list

```
Tasks generadas adaptativamente segun features:
  1. [ui] dashboard/page.tsx
  2. [ui] components/ChartWidget.tsx
  3. [ui] components/KPICard.tsx
  4. [infra] package.json (+ recharts si features contiene "chart")
```

**Cambio necesario:** El planner debe leer `features` del RequirementGraph para determinar las tareas. En lugar de templates fijos, usa un prompt LLM o rules heuristicas: si features contiene "chart", genera tareas de chart.

### Stage 9: SYNTHESIS (ActionExecutor)

**Input:** Tasks + IR + RequirementGraph  
**Output:** Archivos generados

**Cambio necesario:** Agregar `AdaptiveGenerator` que recibe `features` y genera codigo React generico. Si features contiene "chart", usa Recharts. Si features contiene "table", genera tabla. Si features contiene "form", genera formulario. Esto se hace con templates condicionales, no con generadores separados.

### Stage 10: UI GENERATOR

**Input:** IR + RequirementGraph.features  
**Output:** Pagina dashboard con componentes

**Cambio necesario:** En lugar de detectar solo `"form"` y `"table"`, usar `features` del RequirementGraph para determinar que componentes renderizar.

### Stage 11: VALIDATOR

**Input:** Archivos generados  
**Output:** Reporte de validacion

**Cambio necesario:** Validar que los archivos generados corresponden a las features detectadas. No requiere `ChartValidator` especifico.

---

## 5. Requisito 0: Cablear RequirementDecomposer

### 5.1 Cambio en Orchestrator

```python
# En orchestrator.py, NODE_MAP:
Stage.REQUIREMENT_DECOMPOSER: RequirementDecomposer,

# Pipeline queda:
# INTENT → PREPROCESSOR → LEXER → PARSER → REQUIREMENT_DECOMPOSER → SEMANTIC → IR → PLANNER → SYNTHESIS → UI → VALIDATOR
```

### 5.2 RequirementDecomposer debe recibir AST parcial

Actualmente `receive_mission()` recibe `input_data` como string. Debe cambiar para recibir un dict con:

```python
def receive_mission(self, input_data: object) -> None:
    if isinstance(input_data, dict):
        self._raw_text = input_data.get("raw_text", str(input_data))
        self._partial_ast = input_data.get("ast", {})
        self._tokens = input_data.get("tokens", [])
        self._enriched = input_data.get("enriched", {})
    else:
        self._raw_text = str(input_data)
        self._partial_ast = {}
        self._tokens = []
        self._enriched = {}
```

El pipeline debe pasar los datos del parser al RequirementDecomposer:

```python
# En orchestrator._make_node(), para REQUIREMENT_DECOMPOSER:
ctx.input_data = {
    "raw_text": ctx.input_data.get("raw_text", ""),
    "ast": output.output_data.get("ast", {}),
    "tokens": output.output_data.get("tokens", []),
    "enriched": output.output_data.get("enriched", {}),
}
```

**Nota:** Esto requiere que `raw_text` original se preserve a traves de los stages. Actualmente el pipeline muta `input_data`. Con el refactor a `StageContext` frozen (plan 121), se agregaria un campo `original_input` o se preservaria via metadata.

### 5.3 Archivos a Modificar (Cableado)

| Archivo | Cambio |
|---------|--------|
| `orchestrator.py` | Agregar `Stage.REQUIREMENT_DECOMPOSER` a `NODE_MAP` en la posicion correcta |
| `orchestrator.py` | `build_context()` debe incluir raw text preservation para REQUIREMENT_DECOMPOSER |
| `nodes/requirement_decomposer.py` | `receive_mission()` acepta dict con raw_text + ast + tokens |
| `state_models.py` | Si es necesario, agregar `raw_text` field a `StageContext` (opcional, depende de frozen refactor) |

**Total cableado:** ~3 archivos modificados, ~2h

---

## 6. El RequirementDecomposer como Capa Adaptativa

### 6.1 Lo que ya hace (sin modificar)

El `RequirementDecomposer` actual ya tiene:

| Componente | Funcion | Usa LLM? |
|-----------|---------|----------|
| `DomainClassifier` | Clasifica dominio (web, mobile, api, data, infra, cli) | Si, fallback |
| `EntityExtractor` | Extrae entidades con regex + LLM | Si, fallback |
| `FeatureIdentifier` | Identifica features por keyword matching + LLM | Si, fallback |
| `ConstraintDetector` | Detecta constraints (performance, security, etc.) | No, solo keywords |
| `StoryGenerator` | Genera user stories desde features + entities | Si |
| `ASTCache` | Cache LRU para RequirementGraph repetidos | No |

### 6.2 Lo que necesita para ser adaptativo

```python
# Enfoque actual (ya existe):
features = self._feature_identifier.identify(self._raw_text)
# → ["dashboard", "charts"]  (por keyword matching)

# Enfoque adaptativo (extender):
features = self._feature_identifier.identify_adaptive(
    raw_text=self._raw_text,
    partial_ast=self._partial_ast,
    tokens=self._tokens,
)
# → ["dashboard", "bar chart for sales", "line chart for users",
#    "kpi cards", "responsive layout", "data from existing entities"]
# Usa LLM para expandir lo que el keyword matching no capturo
```

El `FeatureIdentifier` debe extenderse para:
1. Tomar el AST parcial y tokens como contexto
2. Usar LLM para inferir features que el keyword matching no detecto
3. Usar el AST parcial para extraer entidades conocidas (como "graficos")

### 6.3 RequirementGraph Enriquecido

El `RequirementGraph` actual solo tiene strings. Para ser util al planner y synthesis, necesita mas estructura:

```python
# state_models.py — extender RequirementGraph:

class Feature(BaseModel):
    name: str                         # "bar chart"
    category: str = "ui"              # "ui" | "data" | "api" | "infra"
    target_library: str | None = None # "recharts" | "chart.js" | None
    priority: int = 1                 # 1 = alta, 2 = media, 3 = baja
    llm_generated: bool = False       # True si lo infirio el LLM

class RequirementGraph(BaseModel):
    domain: str
    entities: list[dict] = []
    features: list[Feature] = []       # Antes: list[str]
    constraints: list[str] = []
    user_stories: list[str] = []
    raw_text: str = ""
    # Nuevo:
    ast_summary: dict = {}             # Resumen del AST parcial
    tokens_summary: list[str] = []     # Tipos de tokens encontrados
    detected_libraries: list[str] = [] # Librerias inferidas (recharts, chart.js, etc.)
    missing_info: list[str] = []       # Que informacion falta para generar
```

### 6.4 Archivos a Modificar

| Archivo | Cambio |
|---------|--------|
| `state_models.py` | Extender `RequirementGraph` con `Feature` tipado, `ast_summary`, `detected_libraries`, `missing_info` |
| `nodes/requirement_decomposer.py` | `receive_mission()` accepta dict, `_build_graph()` usa AST parcial + tokens |
| `tools/llm_tools.py` (FeatureIdentifier) | `identify_adaptive()` que usa LLM con AST parcial como contexto |
| `tests/test_requirement_decomposer.py` | Tests con AST parcial simulado |

**Total:** ~4 archivos, ~8h

---

## 7. El Generador Adaptativo

### 7.1 Problema

Hoy `GeneratorFactory.get_generator(target)` solo conoce targets fijos: `react`, `nextjs`, `prisma`, `nestjs`, `docker`, `tailwind`. Si el RequirementDecomposer detecta que el input requiere "dashboard con graficos", no hay un generador para eso.

### 7.2 Solucion: AdaptiveGenerator

En lugar de crear `ChartGenerator`, `DashboardGenerator`, `FormGenerator`, etc., creamos **un solo generador adaptativo** que recibe las features del RequirementGraph y genera codigo en consecuencia:

```python
# generators/adaptive_generator.py — NUEVO

class AdaptiveGenerator(BaseGenerator):
    """Generador adaptativo: produce codigo React basado en features del RequirementGraph.
    
    No conoce tipos de UI especificos. En su lugar, recibe una lista de features
    y genera componentes condicionalmente:
    - Si features contiene "chart" → genera <BarChart> con Recharts mock data
    - Si features contiene "kpi" → genera <KPICard>
    - Si features contiene "table" → genera <DataTable>
    - Si features contiene "form" → genera <Form>
    
    Cada condicion es un template string simple, no un generador separado.
    Agregar nuevo tipo de UI = agregar condicion en este archivo.
    """

    def generate(self, features: list[Feature], output_dir: Path) -> list[Path]:
        created = []
        for feature in features:
            if "chart" in feature.name.lower():
                created.append(self._generate_chart(feature, output_dir))
            if "kpi" in feature.name.lower() or "metric" in feature.name.lower():
                created.append(self._generate_kpi_card(feature, output_dir))
            if "table" in feature.name.lower() or "list" in feature.name.lower():
                created.append(self._generate_table(feature, output_dir))
            if "form" in feature.name.lower():
                created.append(self._generate_form(feature, output_dir))
        return created
    
    def _generate_chart(self, feature: Feature, output_dir: Path) -> Path:
        # Template inline — no requiere archivo separado
        return self._write_template(output_dir, "Chart.tsx", CHART_TEMPLATE)
```

### 7.3 Ventajas

1. **Un solo archivo** para todos los tipos de UI (vs. un generador por tipo)
2. **Nuevo tipo de UI** = agregar un `if` y un template string, no un generador completo
3. **Template inline** — los templates estan en el codigo, no en archivos .j2 separados
4. **Basado en features** — el RequirementDecomposer decide que generar, no el usuario del generador

### 7.4 Adaptive Page Generator

El `AdaptiveGenerator` tambien genera la pagina principal del dashboard:

```python
def generate_main_page(self, features: list[Feature], domain: str) -> str:
    """Genera page.tsx basado en features detectadas."""
    imports = []
    components = []
    
    for f in features:
        if "chart" in f.name.lower():
            imports.append('import Chart from "../components/Chart";')
            components.append('<Chart title="{f.name}" />')
        if "kpi" in f.name.lower():
            imports.append('import KPICard from "../components/KPICard";')
            components.append('<KPICard label="..." value="..." />')
    
    return f"""
import {{ DashboardGrid }} from "../components/DashboardGrid";
{chr(10).join(imports)}

export default function {domain.title()}Page() {{
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">{{"{domain.title()}"}}</h1>
      <DashboardGrid>
        {chr(10).join(components)}
      </DashboardGrid>
    </div>
  );
}}
"""
```

### 7.5 Archivos

| Archivo | Cambio |
|---------|--------|
| `generators/adaptive_generator.py` | **NUEVO** — `AdaptiveGenerator` con templates inline condicionales |
| `generators/base_generator.py` | **MODIFICAR** — agregar `AdaptiveGenerator` al `GeneratorFactory` |
| `nodes/action_executor.py` | **MODIFICAR** — `_detect_target()` puede retornar `"adaptive"` si features lo requieren |

**Total:** ~3 archivos, ~10h

---

## 8. Plan de Implementacion

### Fase 1: Cablear RequirementDecomposer (2h)

| # | Tarea | Archivos | Esfuerzo |
|---|-------|----------|----------|
| 1.1 | Agregar `REQUIREMENT_DECOMPOSER` a `NODE_MAP` en orden correcto (tras parser) | `orchestrator.py` | 0.5h |
| 1.2 | `receive_mission()` accepta dict con raw_text + ast + tokens | `nodes/requirement_decomposer.py` | 1h |
| 1.3 | Preservar `raw_text` a traves del pipeline para que RequirementDecomposer lo reciba | `orchestrator.py` (`_make_node`) | 0.5h |

### Fase 2: Extender RequirementDecomposer (8h)

| # | Tarea | Archivos | Esfuerzo |
|---|-------|----------|----------|
| 2.1 | Extender `RequirementGraph` con `Feature` tipado, `ast_summary`, `detected_libraries` | `state_models.py` | 1h |
| 2.2 | `FeatureIdentifier.identify_adaptive()` que usa AST parcial + LLM | `tools/llm_tools.py` | 3h |
| 2.3 | `_build_graph()` incorpora AST parcial y tokens para enriquecer features | `nodes/requirement_decomposer.py` | 2h |
| 2.4 | Tests de RequirementDecomposer con AST parcial simulado | `tests/test_requirement_decomposer.py` | 2h |

### Fase 3: Generador Adaptativo (10h)

| # | Tarea | Archivos | Esfuerzo |
|---|-------|----------|----------|
| 3.1 | Crear `AdaptiveGenerator` con templates condicionales (chart, kpi, table, form) | `generators/adaptive_generator.py` | 5h |
| 3.2 | Registrar `AdaptiveGenerator` en `GeneratorFactory` | `generators/base_generator.py` | 0.5h |
| 3.3 | `_detect_target()` retorna "adaptive" si hay features UI | `nodes/action_executor.py` | 0.5h |
| 3.4 | `GoalTreePlanner` lee features del RequirementGraph para crear tareas | `nodes/reasoning_engine.py` | 2h |
| 3.5 | Tests del AdaptiveGenerator con distintas combinaciones de features | `tests/test_adaptive_generator.py` | 2h |

### Fase 4: Integracion y CI (4h)

| # | Tarea | Esfuerzo |
|---|-------|----------|
| 4.1 | Verificar pipeline end-to-end con prompt de dashboard | 1h |
| 4.2 | Verificar pipeline con prompt de formulario (sin modificar nada) | 1h |
| 4.3 | Verificar pipeline con prompt de API (sin modificar nada) | 1h |
| 4.4 | `ruff check .` + `pytest tests/ -v --cov` | 1h |

**Total:** ~24h

### Resumen de Archivos

| Archivos Nuevos | Archivos Modificados |
|----------------|---------------------|
| `generators/adaptive_generator.py` | `orchestrator.py` |
| `tests/test_adaptive_generator.py` | `nodes/requirement_decomposer.py` |
| `tests/test_requirement_decomposer.py` | `state_models.py` |
| | `tools/llm_tools.py` (FeatureIdentifier) |
| | `generators/base_generator.py` |
| | `nodes/action_executor.py` |
| | `nodes/reasoning_engine.py` |

**Total: 3 nuevos + 7 modificados = 10 archivos (vs. 29 de v1.0)**

---

## 9. Ejemplos de Entrada y Salida

### 9.1 Dashboard con graficos

```
INPUT:  "Crea dashboard web para graficos para el proyecto actual Proyecto0"
OUTPUT: modules/dashboard/page.tsx        ← layout con grid
        modules/components/Chart.tsx      ← grafico Recharts (barras + lineas)
        modules/components/KPICard.tsx    ← tarjetas de metrica
        modules/components/DashboardGrid.tsx  ← grid wrapper
        modules/package.json              ← + recharts
```

### 9.2 Formulario de registro

```
INPUT:  "Crea un formulario de registro de usuarios con validacion"
OUTPUT: modules/auth/RegisterPage.tsx     ← pagina con formulario
        modules/components/FormField.tsx  ← campo reutilizable
        modules/components/ValidationSummary.tsx ← errores de validacion
```

### 9.3 API REST (sin cambiar nada)

```
INPUT:  "Crea una API REST para gestion de productos"
OUTPUT: modules/products/product.service.ts  ← NestJS service
        modules/products/product.controller.ts ← endpoints CRUD
        modules/products/product.entity.ts    ← Prisma entity
        modules/prisma/schema.prisma          ← modelo de datos
```

### 9.4 Landing page

```
INPUT:  "Crea una landing page moderna con hero, features y footer"
OUTPUT: modules/landing/HeroSection.tsx
        modules/landing/FeaturesSection.tsx
        modules/landing/FooterSection.tsx
        modules/landing/page.tsx
```

**Todos estos ejemplos funcionan sin modificar el pipeline. Solo cambia lo que el `RequirementDecomposer` detecta como features y lo que el `AdaptiveGenerator` genera condicionalmente.**

---

## 10. Riesgos y Mitigacion

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|-----------|
| **LLM falla o es lento** en RequirementDecomposer | Media | Alto | Cache LRU (ya existe) + fallback heuristico (keyword matching) |
| **RequirementGraph muy generico** — features poco precisas | Alta | Medio | El `AdaptiveGenerator` debe tener valores por defecto razonables (mock data generica) |
| **Raw text se pierde** entre stages del pipeline | Baja | Alto | Preservar raw_text en `StageContext` (plan 121: frozen context refactor) |
| **Over-engineering del AdaptiveGenerator** — demasiados if condicionales | Media | Bajo | Empezar con 3-4 tipos (chart, kpi, table, form). Iterar. |
| **Dependencia LLM aumenta costo por request** | Alta | Medio | Cache + fallback heuristico + modelo mini para RequirementDecomposer |

---

## 11. Criterios de Aceptacion

### 11.1 Funcionales

| # | Criterio | Verify |
|---|----------|--------|
| F1 | Pipeline completo ejecuta con RequirementDecomposer cableado | ✅ |
| F2 | Prompt de dashboard produce archivo `page.tsx` + componentes React | ✅ |
| F3 | Prompt de formulario produce archivo de formulario (sin modificar pipeline) | ✅ |
| F4 | Prompt de API produce archivos NestJS/Prisma (sin modificar pipeline) | ✅ |
| F5 | RequirementDecomposer produce RequirementGraph con features detectadas | ✅ |
| F6 | AdaptiveGenerator genera codigo condicional segun features | ✅ |
| F7 | Sin LLM, el sistema sigue funcionando con fallback heuristico | ✅ |

### 11.2 Tecnicos

| # | Criterio | Verify |
|---|----------|--------|
| T1 | `ruff check .` = 0 errores | ✅ |
| T2 | `pytest tests/ -v` = todos pasan | ✅ |
| T3 | No se introducen dependencias Python nuevas | ✅ |
| T4 | El sistema funciona para prompts que nunca antes vio | ✅ |
| T5 | RequirementDecomposer ya no es dead code (esta en NODE_MAP) | ✅ |

---

## 12. Estimacion de Esfuerzo

| Fase | Horas | % |
|------|-------|---|
| F1: Cablear RequirementDecomposer | 2h | 8% |
| F2: Extender RequirementDecomposer | 8h | 33% |
| F3: Generador Adaptativo | 10h | 42% |
| F4: Integracion + CI | 4h | 17% |
| **Total** | **24h (3 dias)** | **100%** |

### Comparacion con v1.0

| Aspecto | v1.0 (Prescriptivo) | v2.0 (Adaptativo) |
|---------|--------------------|--------------------|
| Archivos nuevos | 12 | 3 |
| Archivos modificados | 17 | 7 |
| Esfuerzo total | **67h** | **24h** |
| Cobertura de inputs | Solo dashboard | Cualquier input |
| Costo por nuevo tipo UI | 10-29 archivos | 0-1 archivo (template) |
| RequirementDecomposer | Eliminado | Componente central |

---

*Documento generado a partir del analisis del pipeline RECPL v2.0+. Fecha: 2026-06-18. v2.0 — Enfoque adaptativo.*
