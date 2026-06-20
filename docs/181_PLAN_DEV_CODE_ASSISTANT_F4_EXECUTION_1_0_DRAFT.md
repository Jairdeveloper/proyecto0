---
id: 181
area: DEV
type: PLAN
module: CODE_ASSISTANT_AGENTIC_PLATFORM
version: 1.0
status: DRAFT
tags:
  - plan
  - execution
  - f4
  - foundation
  - repository-intelligence
  - tools
  - world-model
  - memory
  - agentic-ir
  - goal-manager
summary: "Plan de ejecucion para Fase 4 de la Code Assistant Agentic Platform — RepositoryIntelligenceAgent, ToolRegistry + 16 herramientas, WorldModelAgent, MemorySystem 3 niveles, IntentRouter, GoalManager, AgenticIR y AgentGraphBuilder."
keywords:
  - f4
  - execution-plan
  - repository-graph
  - treesitter
  - tools
  - world-model
  - memory
  - intent-router
  - goal-manager
  - agentic-ir
changelog:
  - version: 1.0
    date: 2026-06-20
    author: system
    changes:
      - "Plan de ejecucion F4 — Foundation, basado en las propuestas 179 y 180"
---

# Plan de Ejecucion — F4: Foundation

> **Propuesta base:** `docs/179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md`  
> **Extension cognitiva:** `docs/180_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md`  
> **Pre-requisito:** F3 completado (`docs/160_PLAN_DEV_PDCA_SDLC_F3_EXECUTION_1_0_DRAFT.md`)  
> **Siguiente:** F5 — Agent Expansion (documento por definir)

---

## Resumen

**Objetivo:** Construir la base del nuevo sistema agentic: Repository Graph, 16 herramientas explicitas, World Model inicial, memoria de 3 niveles, enrutamiento inteligente, y el contrato AgenticIR.

```
F4 Scope:
  ┌─────────────────────────────────────────────────────┐
  │                    F4: Foundation                    │
  │                                                      │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Sprint 1: Repository Intelligence Core       │   │
  │  │  (LanguageDetector → TreeSitter → AST)       │   │
  │  └──────────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Sprint 2: Repository Intelligence Graphs    │   │
  │  │  (SymbolGraph → DependencyGraph → ArchDetect)│   │
  │  └──────────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Sprint 3: ToolRegistry + 8 tools (batch 1)  │   │
  │  │  (Read, Write, Search, Ripgrep, Glob, Git,   │   │
  │  │   Docker, Diff)                               │   │
  │  └──────────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Sprint 4: Tools batch 2 + WorldModel start  │   │
  │  │  (TestRunner, Terminal, Browser, AST, LSP,   │   │
  │  │   DepGraph, EmbeddingSearch, SymbolLookup    │   │
  │  │   + WorldModelAgent + ServiceMap)            │   │
  │  └──────────────────────────────────────────────┘   │
  │  ┌──────────────────────────────────────────────┐   │
  │  │  Sprint 5: Routing + Memory + Integration    │   │
  │  │  (IntentRouter, Memory 3 niveles,            │   │
  │  │   AgentGraphBuilder, GoalManager, AgenticIR) │   │
  │  └──────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────┘
```

**Duracion:** 5 sprints (~50 dias habiles)
**Archivos nuevos:** ~23
**LOC estimado:** ~3,450
**Tests nuevos:** ~140
**Dependencias externas nuevas:** `tree-sitter`, `watchdog`

---

## Arquitectura F4

```
                          compiler-bot/
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
   repository_agent/     tools/               core/
   (S1-S2)              (S3-S4)              (S5)
         │                    │                    │
         ▼                    ▼                    ▼
   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
   │Language      │    │ToolRegistry  │    │IntentRouter  │
   │Detector      │    │- ReadFile    │    │GoalManager   │
   │TreeSitter    │    │- WriteFile   │    │AgenticIR     │
   │ASTBuilder    │    │- Search      │    │Memory(3 niv) │
   │SymbolGraph   │    │- Ripgrep     │    │AgentGraphBldr│
   │DepGraph      │    │- Glob        │    └──────────────┘
   │ArchDetect    │    │- Git         │
   │RepoGraphBldr │    │- Docker      │
   └──────┬───────┘    │- Diff        │
          │            │- TestRunner  │
          ▼            │- Terminal    │
   ┌──────────────┐    │- Browser     │
   │  WorldModel  │◄───│- AST         │
   │  Agent       │    │- DepGraph    │
   │  (S4)        │    │- LSP         │
   └──────┬───────┘    │- EmbedSearch │
          │            │- SymbolLookup│
          ▼            └──────────────┘
   ┌──────────────────────────────────────────┐
   │           Knowledge Graph                │
   │  (+ Repository Graph types)              │
   └──────────────────────────────────────────┘
```

---

## Sprint 1: Repository Intelligence Core (10 dias)

**Objetivo:** Construir el pipeline de parsing que convierte codigo fuente en ASTs semanticos mult-lenguaje.

**Archivos del sprint:** 5
**LOC estimado:** ~700
**Tests:** ~30

### Dia 1 — Estructura del modulo + base classes

`repository_agent/__init__.py`
`repository_agent/base_parser.py`
`repository_agent/repository_intelligence_agent.py` (esqueleto)

**Logica:**

```python
class BaseParser(ABC):
    """Parser base para todos los lenguajes soportados."""
    
    @abstractmethod
    def language(self) -> str: ...
    
    @abstractmethod
    def parse(self, source: str) -> SyntaxTree: ...
    
    @abstractmethod
    def extract_symbols(self, tree: SyntaxTree) -> list[Symbol]: ...

class RepositoryIntelligenceAgent(Agent):
    """Agente principal de inteligencia de repositorio.
    
    Orquesta: LanguageDetector → TreeSitterParser → ASTBuilder → ...
    """
    
    manifest = CapabilityManifest(
        agent_id="repository-intelligence-agent",
        triggers=["repository.scan.requested", "repository.file.changed"],
        output_events=["repository.scan.completed", "repository.graph.updated"]
    )
```

**Tests:** `test_base_parser.py` (2 tests)
- `test_base_parser_abc`: no se puede instanciar BaseParser directamente
- `test_agent_manifest`: manifest tiene agent_id y triggers correctos

**Criterio:** `ruff check . && ruff format .`

### Dia 2 — LanguageDetector

`repository_agent/language_detector.py`

**Logica:**

```python
class LanguageDetector:
    """Detecta lenguajes de programacion en un repositorio.
    
    Soporta: Python, TypeScript, JavaScript, Go, Rust, Java, 
    Kotlin, Ruby, PHP, C, C++, C#, Swift, Scala, Shell, YAML, 
    JSON, Markdown, Dockerfile, Prisma, SQL.
    """
    
    # Map: extension → language
    EXTENSION_MAP = {
        ".py": "python", ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript", ".go": "go",
        ".rs": "rust", ".java": "java", ".kt": "kotlin",
        ".rb": "ruby", ".php": "php", ".c": "c", ".h": "c",
        ".cpp": "cpp", ".hpp": "cpp", ".cs": "csharp",
        ".swift": "swift", ".scala": "scala", ".sh": "shell",
        ".yaml": "yaml", ".yml": "yaml", ".json": "json",
        ".md": "markdown", "Dockerfile": "dockerfile",
        ".prisma": "prisma", ".sql": "sql",
    }
    
    # Map: shebang → language
    SHEBANG_MAP = {
        "python": "python", "bash": "shell", "sh": "shell",
        "node": "javascript", "deno": "typescript",
        "ruby": "ruby", "perl": "perl",
    }
    
    def detect(self, file_path: str) -> str | None:
        """Detecta lenguaje por extension o shebang."""
        # 1. Extension
        ext = os.path.splitext(file_path)[1]
        if ext in self.EXTENSION_MAP:
            return self.EXTENSION_MAP[ext]
        
        # 2. Dockerfile (sin extension)
        if os.path.basename(file_path) == "Dockerfile":
            return "dockerfile"
        
        # 3. Shebang
        if self._has_shebang(file_path):
            return self._shebang_language(file_path)
        
        return None
    
    def scan_repository(self, root: str) -> dict[str, list[str]]:
        """Escanea el repositorio y agrupa archivos por lenguaje."""
        result: dict[str, list[str]] = {}
        for file_path in self._walk_files(root):
            lang = self.detect(file_path)
            if lang:
                result.setdefault(lang, []).append(file_path)
        return result
```

**Tests:** `test_language_detector.py` (5 tests)
- `test_detect_by_extension`: `.py` → `python`, `.ts` → `typescript`, `.rs` → `rust`
- `test_detect_by_shebang`: `#!/usr/bin/python` → `python`
- `test_detect_dockerfile`: `path/to/Dockerfile` → `dockerfile`
- `test_unknown_extension`: `.xyz` → `None`
- `test_scan_repository`: directorio con 3 lenguajes → dict con 3 entries

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_language_detector.py -v`

### Dia 3 — TreeSitterParser (single language)

`repository_agent/treesitter_parser.py`

**Logica:**

```python
class TreeSitterParser(BaseParser):
    """Parser que usa TreeSitter para construir ASTs.
    
    Soporta multi-lenguaje via tree-sitter grammars.
    """
    
    # Gramaticas disponibles
    LANGUAGES = {
        "python": Language.python(),
        "typescript": Language.typescript(),
        "javascript": Language.javascript(),
        "go": Language.go(),
        "rust": Language.rust(),
        "java": Language.java(),
        # ... mas lenguajes bajo demanda
    }
    
    def __init__(self):
        self._parsers: dict[str, Parser] = {}
    
    def _get_parser(self, language: str) -> Parser:
        """Lazy initialization del parser para un lenguaje."""
        if language not in self._parsers:
            lang = self.LANGUAGES.get(language)
            if not lang:
                raise ValueError(f"Unsupported language: {language}")
            self._parsers[language] = Parser(lang)
        return self._parsers[language]
    
    def parse(self, source: str, language: str) -> SyntaxTree:
        """Parsea codigo fuente a AST."""
        parser = self._get_parser(language)
        tree = parser.parse(bytes(source, "utf8"))
        return SyntaxTree(
            language=language,
            root=self._convert_node(tree.root_node),
            source=source
        )
    
    def extract_symbols(self, tree: SyntaxTree) -> list[Symbol]:
        """Extrae simbolos del AST usando queries TreeSitter."""
        # Queries especificas por lenguaje
        if tree.language == "python":
            return self._extract_python(tree)
        elif tree.language in ("typescript", "javascript"):
            return self._extract_typescript(tree)
        # ... pattern for each language
    
    def _extract_python(self, tree: SyntaxTree) -> list[Symbol]:
        """Extrae: class definitions, function definitions, imports."""
        query = """
        (class_definition
          name: (identifier) @class.name) @class.def
          
        (function_definition
          name: (identifier) @function.name) @function.def
          
        (import_statement
          name: (dotted_name) @import.name) @import.stmt
          
        (import_from_statement
          module_name: (dotted_name) @import.from
          name: (dotted_name) @import.name) @import.from_stmt
        """
        return self._query_symbols(tree, query)
    
    def _extract_typescript(self, tree: SyntaxTree) -> list[Symbol]:
        """Extrae: class, interface, function, method, import, export."""
        query = """
        (class_declaration
          name: (type_identifier) @class.name) @class.def
          
        (interface_declaration
          name: (type_identifier) @interface.name) @interface.def
          
        (function_declaration
          name: (identifier) @function.name) @function.def
          
        (method_definition
          name: (property_identifier) @method.name) @method.def
          
        (import_statement) @import.stmt
        """
        return self._query_symbols(tree, query)
```

**Tests:** `test_treesitter_parser.py` (6 tests)
- `test_parse_python`: codigo Python → SyntaxTree con root node
- `test_parse_typescript`: codigo TS → SyntaxTree valido
- `test_extract_symbols_python`: funcion + clase → 2 symbols
- `test_extract_symbols_typescript`: class + interface + method → 3 symbols
- `test_unsupported_language`: lenguaje no soportado → ValueError
- `test_lazy_parser_init`: parser no se inicializa hasta primer uso

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_treesitter_parser.py -v`

### Dia 4 — TreeSitterParser (multi-language, edge cases)

**Logica adicional:**
- Parseo de archivos con errores sintacticos (TreeSitter es tolerante)
- Archivos vacios → SyntaxTree vacio
- Archivos binarios → skip
- Archivos muy grandes (>1MB) → parseo parcial

**Tests adicionales:** (3 tests)
- `test_parse_syntax_error`: codigo con error sintactico → SyntaxTree con error nodes
- `test_parse_empty_file`: archivo vacio → SyntaxTree vacio
- `test_parse_large_file`: truncamiento seguro

**Criterio:** `ruff check . && ruff format .`

### Dia 5 — ASTBuilder (single file)

`repository_agent/ast_builder.py`

**Logica:**

```python
class ASTBuilder:
    """Construye un AST semantico (no sintactico) desde el output de TreeSitter.
    
    Diferencia con TreeSitter:
    - TreeSitter produce AST sintactico (concreto, con toda la sintaxis)
    - ASTBuilder produce AST semantico (abstracto, solo lo relevante)
    """
    
    def build(self, file_path: str, source: str, 
              language: str, syntax_tree: SyntaxTree) -> SemanticAST:
        """Construye AST semantico para un archivo."""
        
        symbols = self._extract_symbols(syntax_tree, language)
        imports = self._extract_imports(syntax_tree, language)
        exports = self._extract_exports(syntax_tree, language)
        
        return SemanticAST(
            file_path=file_path,
            language=language,
            symbols=symbols,      # class, function, method, interface definitions
            imports=imports,      # what this file imports
            exports=exports,      # what this file exports
            metrics=self._compute_metrics(syntax_tree, source)
        )
    
    def _compute_metrics(self, tree: SyntaxTree, source: str) -> CodeMetrics:
        """Metricas basicas del codigo."""
        lines = source.count("\n") + 1
        return CodeMetrics(
            lines=lines,
            code_lines=self._count_code_lines(source),
            comment_lines=self._count_comment_lines(tree),
            blank_lines=lines - self._count_code_lines(source) 
                        - self._count_comment_lines(tree),
            functions=len([s for s in self._extract_symbols(tree, tree.language) 
                          if s.type in ("function", "method")]),
            classes=len([s for s in self._extract_symbols(tree, tree.language)
                        if s.type == "class"])
        )
```

**Tests:** `test_ast_builder.py` (4 tests)
- `test_build_semantic_ast`: archivo TS con clase → AST semantico con symbols, imports, exports
- `test_metrics_computed`: archivo de 10 lineas → metrics.lines = 10
- `test_empty_file_metrics`: archivo vacio → metrics.lines = 0, functions = 0
- `test_import_extraction`: archivo con imports → lista de imports extraida

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_ast_builder.py -v`

### Dia 6 — ASTBuilder (cross-file references)

**Logica adicional:**
- Identificar referencias cruzadas entre archivos
- Resolver imports relativos y absolutos
- Detectar archivos que importan simbolos no exportados

**Tests adicionales:** (3 tests)
- `test_cross_file_reference`: archivo A importa de B → referencia detectada
- `test_relative_import_resolution`: `import ./sub/module` → path resuelto
- `test_missing_export_detection`: import de simbolo no exportado → warning

**Criterio:** `ruff check . && ruff format .`

### Dia 7 — RepositoryIntelligenceAgent (scan workflow)

`repository_agent/repository_intelligence_agent.py` (completar)

**Logica:**

```python
class RepositoryIntelligenceAgent(Agent):
    """Agente de inteligencia de repositorio. Completado."""
    
    async def handle_event(self, event: Event):
        if event.topic == "repository.scan.requested":
            await self._scan_repository(event.data.get("path"))
        elif event.topic == "repository.file.changed":
            await self._update_file(event.data)
    
    async def _scan_repository(self, root_path: str):
        """Escanea el repositorio completo y construye Repository Graph."""
        # 1. Detectar lenguajes
        lang_map = self.language_detector.scan_repository(root_path)
        
        # 2. Parsear cada archivo
        all_asts = {}
        for lang, files in lang_map.items():
            for file_path in files:
                source = await self._read_file(file_path)
                syntax_tree = self.parser.parse(source, lang)
                ast = self.ast_builder.build(file_path, source, lang, syntax_tree)
                all_asts[file_path] = ast
        
        # 3. Construir SymbolGraph
        symbol_graph = self.symbol_graph_builder.build(all_asts)
        
        # 4. Construir DependencyGraph
        dep_graph = self.dependency_graph_builder.build(all_asts)
        
        # 5. Detectar arquitectura
        arch = self.architecture_detector.detect(all_asts, dep_graph)
        
        # 6. Escribir al Knowledge Graph
        await self._write_to_kg(all_asts, symbol_graph, dep_graph, arch)
        
        # 7. Publicar evento
        await self.event_bus.publish(Event(
            topic="repository.scan.completed",
            source=self.agent_id,
            data={
                "path": root_path,
                "files_scanned": len(all_asts),
                "languages": list(lang_map.keys()),
                "errors": self._scan_errors
            }
        ))
```

**Tests:** `test_repository_intelligence_agent.py` (4 tests)
- `test_scan_workflow`: scan de directorio pequeño → repository.scan.completed emitido
- `test_file_change_triggers_update`: evento repository.file.changed → re-parseo
- `test_scan_empty_directory`: directorio vacio → scan completed con files_scanned=0
- `test_scan_error_handling`: archivo corrupto → error registrado, scan continua

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_repository_intelligence_agent.py -v`

### Dia 8 — RepositoryIntelligenceAgent (Knowledge Graph writing)

`repository_agent/repository_graph_builder.py` (schema + KG mapping)

**Logica:**

```python
class RepositoryGraphBuilder:
    """Escribe los datos del repositorio en el Knowledge Graph."""
    
    NODE_TYPES_MAP = {
        "class": NodeType.CLASS,
        "function": NodeType.FUNCTION,
        "method": NodeType.METHOD,
        "interface": NodeType.INTERFACE,
        "entity": NodeType.ENTITY,
        "endpoint": NodeType.ENDPOINT,
        "source_file": NodeType.SOURCE_FILE,
    }
    
    async def write_scan_results(self, kg: KnowledgeGraph,
                                  all_asts: dict, symbol_graph: dict,
                                  dep_graph: dict, arch: ArchitectureModel):
        """Escribe todo el resultado del scan al Knowledge Graph."""
        
        # 1. Nodo REPOSITORY (raiz)
        repo_id = f"repo-{uuid4().hex[:8]}"
        await kg.add_node(Node(
            id=repo_id, node_type=NodeType.REPOSITORY,
            properties={"path": "...", "scanned_at": time.time()}
        ))
        
        # 2. Por cada archivo: nodo SOURCE_FILE
        for file_path, ast in all_asts.items():
            file_id = self._file_to_id(file_path)
            await kg.add_node(Node(
                id=file_id, node_type=NodeType.SOURCE_FILE,
                properties={
                    "path": file_path, "language": ast.language,
                    "lines": ast.metrics.lines, "functions": ast.metrics.functions,
                    "classes": ast.metrics.classes
                }
            ))
            await kg.add_edge(Edge(repo_id, file_id, EdgeType.CONTAINS))
            
            # 2a. Por cada simbolo: nodo CLASS, FUNCTION, etc.
            for symbol in ast.symbols:
                symbol_id = f"{file_id}:{symbol.name}"
                node_type = self.NODE_TYPES_MAP.get(symbol.type, NodeType.CLASS)
                await kg.add_node(Node(
                    id=symbol_id, node_type=node_type,
                    properties={
                        "name": symbol.name, "line": symbol.line,
                        "docstring": symbol.docstring
                    }
                ))
                await kg.add_edge(Edge(file_id, symbol_id, EdgeType.DEFINES))
        
        # 3. Dependencias entre archivos
        for file_from, deps in dep_graph.items():
            from_id = self._file_to_id(file_from)
            for dep in deps:
                to_id = self._file_to_id(dep.target_path)
                await kg.add_edge(Edge(from_id, to_id, EdgeType.IMPORTS))
        
        # 4. Arquitectura detectada
        arch_id = f"arch-{uuid4().hex[:8]}"
        await kg.add_node(Node(
            id=arch_id, node_type="architecture_pattern",
            properties={"pattern": arch.pattern, "confidence": arch.confidence}
        ))
        await kg.add_edge(Edge(repo_id, arch_id, EdgeType.DEFINES))
```

**Tests:** `test_repository_graph_builder.py` (3 tests)
- `test_write_scan_results`: 2 archivos → 2 SOURCE_FILE + symbols + imports en KG
- `test_empty_scan`: 0 archivos → solo nodo REPOSITORY
- `test_edge_creation`: archivo A importa B → arista IMPORTS creada

**Criterio:** `ruff check . && ruff format .`

### Dia 9 — Tests de integracion S1

**Tests de integracion (`test_integration_s1.py` ~4 tests):**
- `test_full_scan_pipeline`: LanguageDetector → TreeSitter → ASTBuilder → KG (3 archivos Python)
- `test_full_scan_typescript`: 2 archivos TS con imports cruzados → grafo con aristas
- `test_scan_idempotent`: mismo directorio escaneado 2 veces → mismo resultado
- `test_agent_handle_event_scan_requested`: evento dispara scan completo

### Dia 10 — Buffer / Ruff cleanup / Documentacion

- Docstrings en todas las clases y metodos publicos de S1
- `ruff check . --no-fix` → 0 errors
- `ruff format . --check` → sin cambios
- `python -m pytest tests/test_language_detector.py tests/test_treesitter_parser.py tests/test_ast_builder.py tests/test_repository_intelligence_agent.py tests/test_repository_graph_builder.py tests/test_integration_s1.py -v` → ~30 tests PASS

---

## Sprint 2: Repository Intelligence Graphs (10 dias)

**Objetivo:** Construir SymbolGraph, DependencyGraph, ArchitectureDetector y completar el RepositoryGraphBuilder.

**Archivos del sprint:** 5
**LOC estimado:** ~700
**Tests:** ~30

### Dia 11 — SymbolGraph (extraction)

`repository_agent/symbol_graph.py`

**Logica:**

```python
class SymbolGraph:
    """Grafo de simbolos del repositorio.
    
    Nodos: Symbol (class, function, method, interface, variable)
    Aristas: defines, extends, implements, calls, references
    """
    
    def build(self, all_asts: dict[str, SemanticAST]) -> nx.DiGraph:
        """Construye grafo de simbolos desde ASTs."""
        graph = nx.DiGraph()
        
        # 1. Agregar todos los simbolos como nodos
        for file_path, ast in all_asts.items():
            for symbol in ast.symbols:
                graph.add_node(
                    symbol.id,
                    name=symbol.name,
                    type=symbol.type,
                    file=file_path,
                    line=symbol.line,
                    docstring=symbol.docstring
                )
        
        # 2. Detectar herencia (extends, implements)
        for file_path, ast in all_asts.items():
            for symbol in ast.symbols:
                if symbol.extends:
                    parent = self._find_symbol(symbol.extends, all_asts)
                    if parent:
                        graph.add_edge(symbol.id, parent.id, type="extends")
                if symbol.implements:
                    for iface in symbol.implements:
                        iface_node = self._find_symbol(iface, all_asts)
                        if iface_node:
                            graph.add_edge(symbol.id, iface_node.id, 
                                          type="implements")
        
        return graph
```

**Tests:** `test_symbol_graph.py` (4 tests)
- `test_build_from_asts`: 2 archivos con clases → grafo con 2+ nodos
- `test_extends_edge`: clase B extends A → arista extends
- `test_implements_edge`: clase implements Interface → arista implements
- `test_empty_asts`: dict vacio → grafo vacio

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_symbol_graph.py -v`

### Dia 12 — SymbolGraph (resolution + cycles)

**Logica adicional:**
- Resolver referencias entre archivos
- Detectar ciclos de dependencia entre simbolos
- Detectar simbolos definidos pero no usados
- Detectar simbolos usados pero no definidos

**Tests adicionales:** (3 tests)
- `test_reference_resolution`: simbolo referenciado desde otro archivo → resuelto
- `test_cycle_detection`: A→B→C→A → ciclo detectado
- `test_unused_symbol`: simbolo definido pero no referenciado → reportado

**Criterio:** `ruff check . && ruff format .`

### Dia 13 — DependencyGraph

`repository_agent/dependency_graph.py`

**Logica:**

```python
class DependencyGraph:
    """Grafo de dependencias entre archivos/modulos del repositorio.
    
    Niveles:
    - external: dependencias de terceros (npm, pip, maven)
    - internal: otros modulos del proyecto
    - same_module: archivos dentro del mismo modulo
    """
    
    def build(self, all_asts: dict[str, SemanticAST]) -> nx.DiGraph:
        """Construye grafo de dependencias entre archivos."""
        graph = nx.DiGraph()
        
        for file_path, ast in all_asts.items():
            graph.add_node(file_path, language=ast.language)
            
            for imp in ast.imports:
                target = self._resolve_import(file_path, imp)
                if target:
                    level = self._classify_dependency(target, all_asts)
                    graph.add_edge(file_path, target, 
                                  level=level, symbol=imp.symbol)
        
        return graph
    
    def _classify_dependency(self, target: str, 
                              all_asts: dict) -> str:
        """Clasifica nivel de dependencia."""
        if target in all_asts:
            return "same_module"  # Mismo proyecto
        if any(target.startswith(p) for p in self._project_prefixes):
            return "internal"     # Otro modulo del proyecto
        return "external"         # Terceros
    
    def find_cycles(self, graph: nx.DiGraph) -> list[list[str]]:
        """Encuentra ciclos en el grafo de dependencias."""
        cycles = []
        for cycle in nx.simple_cycles(graph):
            cycles.append(list(cycle))
        return cycles
    
    def find_unused_dependencies(self, graph: nx.DiGraph) -> list[str]:
        """Encuentra dependencias declaradas pero no usadas."""
        unused = []
        for node in graph.nodes():
            if graph.out_degree(node) == 0 and graph.in_degree(node) == 0:
                unused.append(node)
        return unused
```

**Tests:** `test_dependency_graph.py` (4 tests)
- `test_build_with_imports`: 2 archivos, A importa B → arista A→B
- `test_external_dependency`: import de libreria externa → level="external"
- `test_cycle_detection`: A→B→C→A → 1 ciclo detectado
- `test_no_dependencies`: archivo sin imports → nodo aislado

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_dependency_graph.py -v`

### Dia 14 — ArchitectureDetector (NestJS patterns)

`repository_agent/architecture_detector.py`

**Logica:**

```python
class ArchitectureDetector:
    """Detecta patrones arquitectonicos en el codigo.
    
    Usa heuristics basadas en estructura de directorios,
    nombres de archivos, decoradores/annotaciones, y 
    convenciones del framework.
    """
    
    PATTERNS = {
        "nestjs": {
            "indicators": [
                {"type": "file_pattern", "pattern": "*.module.ts"},
                {"type": "file_pattern", "pattern": "*.controller.ts"},
                {"type": "file_pattern", "pattern": "*.service.ts"},
                {"type": "decorator", "name": "@Module"},
                {"type": "decorator", "name": "@Controller"},
                {"type": "decorator", "name": "@Injectable"},
            ],
            "min_score": 3  # minimo 3 indicadores para detectar
        },
        "ddd": {
            "indicators": [
                {"type": "directory", "pattern": "domain/"},
                {"type": "directory", "pattern": "application/"},
                {"type": "directory", "pattern": "infrastructure/"},
                {"type": "directory", "pattern": "interfaces/"},
                {"type": "class_pattern", "pattern": "*Repository"},
                {"type": "class_pattern", "pattern": "*Service"},
                {"type": "class_pattern", "pattern": "*Entity"},
            ],
            "min_score": 4
        },
        "clean_architecture": {
            "indicators": [
                {"type": "directory", "pattern": "usecases/"},
                {"type": "directory", "pattern": "entities/"},
                {"type": "directory", "pattern": "gateways/"},
                {"type": "class_pattern", "pattern": "*UseCase"},
                {"type": "class_pattern", "pattern": "*Gateway"},
            ],
            "min_score": 3
        },
        "mvc": {
            "indicators": [
                {"type": "directory", "pattern": "models/"},
                {"type": "directory", "pattern": "views/"},
                {"type": "directory", "pattern": "controllers/"},
            ],
            "min_score": 2
        }
    }
    
    def detect(self, all_asts: dict[str, SemanticAST],
               dep_graph: nx.DiGraph) -> ArchitectureModel:
        """Detecta patrones arquitectonicos."""
        scores = {}
        violations = []
        
        for pattern_name, pattern_def in self.PATTERNS.items():
            score = 0
            for indicator in pattern_def["indicators"]:
                if self._check_indicator(indicator, all_asts, dep_graph):
                    score += 1
            scores[pattern_name] = score
        
        # Mejor patron
        best_pattern = max(scores, key=scores.get)
        best_score = scores[best_pattern]
        
        if best_score >= self.PATTERNS[best_pattern]["min_score"]:
            # Detectar violaciones
            violations = self._detect_violations(best_pattern, all_asts, dep_graph)
            
            return ArchitectureModel(
                pattern=best_pattern,
                confidence=best_score / len(self.PATTERNS[best_pattern]["indicators"]),
                violations=violations
            )
        
        return ArchitectureModel(
            pattern="unknown",
            confidence=0.0,
            violations=[]
        )
```

**Tests:** `test_architecture_detector.py` (4 tests)
- `test_detect_nestjs`: proyecto con @Module, @Controller, *.module.ts → pattern=nestjs
- `test_detect_ddd`: proyecto con domain/, application/, interfaces/ → pattern=ddd
- `test_unknown_architecture`: proyecto sin patron claro → pattern=unknown
- `test_violation_detection`: proyecto DDD con controller en domain/ → violation

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_architecture_detector.py -v`

### Dia 15 — ArchitectureDetector (multi-pattern, edge cases)

**Logica adicional:**
- Proyectos que combinan patrones (ej: NestJS + DDD)
- Deteccion por framework (Next.js pages router vs app router)
- Deteccion de Prisma como ORM
- Violaciones de capas

**Tests adicionales:** (3 tests)
- `test_mixed_patterns`: NestJS + DDD → ambos detectados con score
- `test_nextjs_app_router`: directorio app/ con layout.tsx → nextjs-app detectado
- `test_prisma_detection`: schema.prisma presente → prisma detectado

**Criterio:** `ruff check . && ruff format .`

### Dia 16 — RepositoryGraphBuilder (completar)

`repository_agent/repository_graph_builder.py` (finalizar metodos faltantes)

```python
class RepositoryGraphBuilder:
    """Constructor completo del Repository Graph."""
    
    async def build_and_store(self, kg: KnowledgeGraph, event_bus: AsyncEventBus,
                               scan_result: ScanResult):
        """Construye el grafo completo y lo almacena."""
        
        # 1. Nodo repositorio
        # 2. Nodos SOURCE_FILE + aristas CONTAINS
        # 3. Nodos de simbolos (CLASS, FUNCTION, etc.) + aristas DEFINES
        # 4. Aristas IMPORTS entre SOURCE_FILE
        # 5. Aristas EXTENDS / IMPLEMENTS entre simbolos
        # 6. Nodo de patron arquitectonico
        # 7. Violaciones de arquitectura
        # 8. Publicar evento repository.graph.updated
        
    async def query(self, kg: KnowledgeGraph, query_type: str, 
                     params: dict) -> QueryResult:
        """Consultas predefinidas sobre el grafo.
        
        Tipos:
        - file_dependencies: dependencias de un archivo
        - symbol_location: donde esta definido un simbolo
        - callers: quienes llaman a una funcion
        - architecture_layer: que capa arquitectonica es un archivo
        - endpoints: todos los endpoints HTTP detectados
        """
```

**Tests:** `test_repository_graph_builder_full.py` (3 tests)
- `test_build_and_store`: scan → todos los nodos y aristas en KG
- `test_query_file_dependencies`: query de dependencias de archivo → lista de dependencias
- `test_query_symbol_location`: query de ubicacion de simbolo → archivo + linea

**Criterio:** `ruff check . && ruff format .`

### Dia 17 — Repository Graph queries + deteccion de endpoints

**Logica adicional:**
- Detectar endpoints HTTP desde decoradores (@Get, @Post, @app.get, etc.)
- Construir aristas ENDPOINT → SOURCE_FILE
- Query: "dame todos los endpoints de este modulo"

**Tests:** (3 tests)
- `test_endpoint_detection_nestjs`: @Get('/users') → ENDPOINT con method=GET, path=/users
- `test_endpoint_detection_fastapi`: @app.get('/users') → ENDPOINT detectado
- `test_query_endpoints_by_module`: query por modulo → lista de endpoints

**Criterio:** `ruff check . && ruff format .`

### Dia 18 — Integracion con el Knowledge Graph existente

**Logica:**
- Los nuevos tipos de nodo (SOURCE_FILE, CLASS, FUNCTION, etc.) deben coexistir con los existentes (GOAL, REQUIREMENT, COMPONENT, etc.)
- Unir SDLC Layer con Repository Layer:
  - Un nodo CODE_MODULE existente → varios nodos SOURCE_FILE
  - Un nodo COMPONENT → un grupo de nodos CLASS
- Validar que las queries del dashboard existente no se rompan

**Tests de integracion:** (3 tests)
- `test_sdlc_repo_integration`: nodo CODE_MODLE vinculado a SOURCE_FILEs
- `test_component_to_class_traceability`: COMPONENT traza a CLASSes que lo implementan
- `test_existing_queries_unbroken`: query de proyectos del dashboard → mismo resultado que antes

**Criterio:** `ruff check . && ruff format .`

### Dia 19 — Tests de integracion S2

**Tests de integracion (`test_integration_s2.py` ~4 tests):**
- `test_full_repo_graph_pipeline`: escanear repo → SymbolGraph + DependencyGraph + ArchitectureDetector → KG completo
- `test_cycle_warning`: repo con ciclo de dependencias → warning en evento repository.scan.completed
- `test_architecture_violation_detected`: repo con violacion → violation almacenada en KG
- `test_query_chain_from_file_to_architecture`: archivo → simbolo → dependencia → arquitectura

### Dia 20 — Buffer / Ruff cleanup

- Docstrings en todas las clases y metodos publicos de S2
- `ruff check . --no-fix` → 0 errors
- `ruff format . --check` → sin cambios
- `python -m pytest tests/test_symbol_graph.py tests/test_dependency_graph.py tests/test_architecture_detector.py tests/test_repository_graph_builder_full.py tests/test_integration_s2.py -v` → ~30 tests PASS

---

## Sprint 3: ToolRegistry + 8 Tools (batch 1) (10 dias)

**Objetivo:** Implementar ToolRegistry y las primeras 8 herramientas.

**Archivos del sprint:** ~6
**LOC estimado:** ~700
**Tests:** ~30

### Dia 21 — ToolRegistry + BaseTool

`core/tool_registry.py`
`core/base_tool.py`

**Logica:**

```python
class ToolResult:
    success: bool
    data: Any
    error: str | None
    duration: float
    tool_name: str

class BaseTool(ABC):
    """Clase base para todas las herramientas del sistema."""
    
    name: str
    description: str
    allowed_agents: list[str]  # "*" = todos
    estimated_latency: float = 0.1  # segundos
    
    @abstractmethod
    async def execute(self, params: dict) -> ToolResult: ...
    
    @abstractmethod
    def get_schema(self) -> dict:
        """Retorna JSON schema de parametros (para validacion y LLM)."""
        ...

class ToolRegistry:
    """Registro central de herramientas."""
    
    def __init__(self, event_bus: AsyncEventBus):
        self._tools: dict[str, BaseTool] = {}
        self.event_bus = event_bus
    
    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise KeyError(f"Tool not found: {name}")
        return self._tools[name]
    
    def list_for_agent(self, agent_id: str) -> list[BaseTool]:
        return [t for t in self._tools.values()
                if agent_id in t.allowed_agents or "*" in t.allowed_agents]
    
    async def execute(self, tool_name: str, params: dict,
                       agent_id: str) -> ToolResult:
        """Ejecuta una herramienta con auditoria."""
        tool = self.get(tool_name)
        
        if agent_id not in tool.allowed_agents and "*" not in tool.allowed_agents:
            return ToolResult(False, None, f"Agent {agent_id} not allowed", 0, tool_name)
        
        start = time.time()
        try:
            result = await tool.execute(params)
            duration = time.time() - start
            
            await self.event_bus.publish(Event(
                topic="tool.executed",
                source=agent_id,
                data={
                    "tool": tool_name,
                    "params": params,
                    "success": result.success,
                    "duration": duration
                }
            ))
            
            return ToolResult(result.success, result.data, result.error, 
                            duration, tool_name)
        except Exception as e:
            duration = time.time() - start
            await self.event_bus.publish(Event(
                topic="tool.error",
                source=agent_id,
                data={"tool": tool_name, "error": str(e)}
            ))
            return ToolResult(False, None, str(e), duration, tool_name)
```

**Tests:** `test_tool_registry.py` (4 tests)
- `test_register_and_get`: tool registrada → recuperable por nombre
- `test_execute_success`: tool ejecutada → ToolResult con success=True
- `test_execute_permission_denied`: agente no autorizado → error
- `test_execute_unregistered_tool`: tool no registrada → KeyError

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_tool_registry.py -v`

### Dia 22 — ReadFileTool + WriteFileTool

`tools/read_file_tool.py`
`tools/write_file_tool.py`

**Logica:**

```python
class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read content of a file"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        path = params.get("path")
        if not path:
            return ToolResult(False, None, "path required", 0, self.name)
        
        # Security: prevent directory traversal
        safe_path = self._sanitize_path(path)
        if not safe_path:
            return ToolResult(False, None, "invalid path", 0, self.name)
        
        try:
            with open(safe_path, "r") as f:
                content = f.read()
            return ToolResult(True, {
                "path": safe_path,
                "content": content,
                "size": len(content),
                "lines": content.count("\n") + 1
            }, None, 0, self.name)
        except FileNotFoundError:
            return ToolResult(False, None, f"File not found: {safe_path}", 0, self.name)
        except Exception as e:
            return ToolResult(False, None, str(e), 0, self.name)
    
    def _sanitize_path(self, path: str) -> str | None:
        """Previene directory traversal."""
        # Normalizar path
        normalized = os.path.normpath(path)
        # Rechazar si contiene '..'
        if ".." in normalized.split(os.sep):
            return None
        return normalized

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write content to a file (creates backup)"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        path = params.get("path")
        content = params.get("content")
        if not path or content is None:
            return ToolResult(False, None, "path and content required", 0, self.name)
        
        safe_path = self._sanitize_path(path)
        if not safe_path:
            return ToolResult(False, None, "invalid path", 0, self.name)
        
        # Backup existente
        if os.path.exists(safe_path):
            backup_path = safe_path + ".bak"
            shutil.copy2(safe_path, backup_path)
        
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, "w") as f:
            f.write(content)
        
        return ToolResult(True, {
            "path": safe_path,
            "size": len(content),
            "backup_created": os.path.exists(safe_path + ".bak")
        }, None, 0, self.name)
```

**Tests:** `test_read_file_tool.py` + `test_write_file_tool.py` (5 tests)
- `test_read_existing_file`: leer archivo existente → contenido + metadata
- `test_read_nonexistent_file`: leer archivo inexistente → FileNotFound error
- `test_read_directory_traversal`: path con "../" → invalid path
- `test_write_new_file`: escribir archivo nuevo → archivo creado con contenido
- `test_write_existing_file_with_backup`: escribir archivo existente → backup creado

**Criterio:** `ruff check . && ruff format .`

### Dia 23 — SearchTool + RipgrepTool

`tools/search_tool.py`
`tools/ripgrep_tool.py`

**Logica:**

```python
class SearchTool(BaseTool):
    """Busqueda textual simple (re sobre archivos)."""
    name = "search"
    description = "Search text in files using regex"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        pattern = params.get("pattern")
        path = params.get("path", ".")
        include = params.get("include")  # "*.ts"
        max_results = params.get("max_results", 100)
        
        matches = []
        for file_path in self._walk_files(path, include):
            try:
                with open(file_path, "r") as f:
                    for i, line in enumerate(f, 1):
                        if re.search(pattern, line):
                            matches.append({
                                "file": file_path,
                                "line": i,
                                "content": line.rstrip()[:200]
                            })
                            if len(matches) >= max_results:
                                return ToolResult(True, {
                                    "matches": matches, "total": len(matches),
                                    "truncated": True
                                }, None, 0, self.name)
            except (UnicodeDecodeError, IsADirectoryError):
                continue
        
        return ToolResult(True, {
            "matches": matches, "total": len(matches), "truncated": False
        }, None, 0, self.name)

class RipgrepTool(BaseTool):
    """Busqueda rapida via ripgrep (rg)."""
    name = "ripgrep"
    description = "Fast regex search using ripgrep"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        pattern = params.get("pattern")
        path = params.get("path", ".")
        
        cmd = ["rg", "--json", "--line-number", pattern, path]
        if params.get("include"):
            cmd.extend(["--glob", params["include"]])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        
        matches = []
        for line in stdout.decode().split("\n"):
            if line:
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        matches.append({
                            "file": data["data"]["path"]["text"],
                            "line": data["data"]["line_number"],
                            "content": data["data"]["lines"]["text"]
                        })
                except json.JSONDecodeError:
                    continue
        
        return ToolResult(True, {
            "matches": matches, "total": len(matches)
        }, None, 0, self.name)
```

**Tests:** `test_search_tool.py` + `test_ripgrep_tool.py` (4 tests)
- `test_search_find_pattern`: patron existente → matches encontrados
- `test_search_no_matches`: patron inexistente → 0 matches
- `test_search_max_results`: limite de resultados respetado
- `test_ripgrep_basic`: ripgrep encuentra patron en archivo

**Criterio:** `ruff check . && ruff format .`

### Dia 24 — GlobTool + DiffTool

`tools/glob_tool.py`
`tools/diff_tool.py`

**Logica:**

```python
class GlobTool(BaseTool):
    name = "glob"
    description = "List files by glob pattern"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        pattern = params.get("pattern")
        path = params.get("path", ".")
        
        matches = glob.glob(os.path.join(path, pattern), recursive=True)
        matches = sorted(matches)
        
        # Clasificar por tipo
        files = [m for m in matches if os.path.isfile(m)]
        dirs = [m for m in matches if os.path.isdir(m)]
        
        return ToolResult(True, {
            "matches": matches, "total": len(matches),
            "files": files, "directories": dirs
        }, None, 0, self.name)

class DiffTool(BaseTool):
    name = "diff"
    description = "Generate diff between file versions or strings"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        text_a = params.get("text_a") or self._read_file(params.get("path_a"))
        text_b = params.get("text_b") or self._read_file(params.get("path_b"))
        context = params.get("context", 3)
        
        diff = difflib.unified_diff(
            text_a.splitlines(keepends=True),
            text_b.splitlines(keepends=True),
            fromfile=params.get("fromfile", "a"),
            tofile=params.get("tofile", "b"),
            n=context
        )
        diff_text = "".join(diff)
        
        return ToolResult(True, {
            "diff": diff_text,
            "additions": sum(1 for l in diff_text.split("\n") if l.startswith("+") and not l.startswith("+++")),
            "deletions": sum(1 for l in diff_text.split("\n") if l.startswith("-") and not l.startswith("---")),
            "has_changes": len(diff_text.strip()) > 0
        }, None, 0, self.name)
```

**Tests:** `test_glob_tool.py` + `test_diff_tool.py` (4 tests)
- `test_glob_find_files`: pattern "*.py" → archivos .py
- `test_glob_no_matches`: pattern sin matches → total=0
- `test_diff_strings`: dos strings diferentes → diff con cambios
- `test_diff_identical`: dos strings iguales → has_changes=False

**Criterio:** `ruff check . && ruff format .`

### Dia 25 — GitTool + DockerTool

`tools/git_tool.py`
`tools/docker_tool.py`

**Logica:**

```python
class GitTool(BaseTool):
    name = "git"
    description = "Execute git operations (status, diff, log, commit)"
    allowed_agents = ["*"]
    
    OPERATIONS = {
        "status": ["git", "status", "--short"],
        "diff": ["git", "diff"],
        "diff_staged": ["git", "diff", "--cached"],
        "log": ["git", "log", "--oneline", "-20"],
        "log_full": ["git", "log", "-5"],
        "branches": ["git", "branch", "-a"],
        "blame": ["git", "blame"],
    }
    
    async def execute(self, params: dict) -> ToolResult:
        operation = params.get("operation")
        path = params.get("path", ".")
        
        if operation not in self.OPERATIONS and operation != "commit":
            return ToolResult(False, None, f"Unknown operation: {operation}", 0, self.name)
        
        if operation == "commit":
            message = params.get("message", "Auto-commit")
            return await self._run(["git", "commit", "-am", message], path)
        
        return await self._run(self.OPERATIONS[operation], path)
    
    async def _run(self, cmd: list[str], path: str) -> ToolResult:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=path
        )
        stdout, stderr = await proc.communicate()
        return ToolResult(
            proc.returncode == 0,
            {"stdout": stdout.decode(), "stderr": stderr.decode(), "returncode": proc.returncode},
            stderr.decode() if proc.returncode != 0 else None,
            0, self.name
        )

class DockerTool(BaseTool):
    name = "docker"
    description = "Execute docker operations (build, run, ps)"
    allowed_agents = ["coding-agent", "test-agent", "*"]
    
    ALLOWED_COMMANDS = ["build", "run", "ps", "images", "stop", "logs"]
    
    async def execute(self, params: dict) -> ToolResult:
        command = params.get("command")
        if command not in self.ALLOWED_COMMANDS:
            return ToolResult(False, None, f"Command not allowed: {command}", 0, self.name)
        
        cmd = ["docker", command]
        if params.get("args"):
            cmd.extend(params["args"])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return ToolResult(
            proc.returncode == 0,
            {"stdout": stdout.decode(), "stderr": stderr.decode()},
            stderr.decode() if proc.returncode != 0 else None,
            0, self.name
        )
```

**Tests:** `test_git_tool.py` + `test_docker_tool.py` (4 tests)
- `test_git_status`: git status en repo valido → stdout con estado
- `test_git_log`: git log → commits recientes
- `test_git_invalid_operation`: operacion desconocida → error
- `test_docker_allowed_commands`: solo comandos permitidos

**Criterio:** `ruff check . && ruff format .`

### Dia 26 — Tool security + audit

**Logica:**
- Implementar auditoria de herramientas en el EventBus
- Rate limiting por agente (max N llamadas/minuto)
- Validacion de parametros contra schema
- Logging de todas las ejecuciones

**Tests:** `test_tool_security.py` (4 tests)
- `test_audit_event_emitted`: cada ejecucion → tool.executed en EventBus
- `test_rate_limiting`: N+1 llamadas en 1 minuto → ultima bloqueada
- `test_parameter_validation`: parametros invalidos contra schema → error
- `test_tool_error_audit`: error en herramienta → tool.error en EventBus

**Criterio:** `ruff check . && ruff format .`

### Dia 27 — Integracion con agentes

**Logica:**
- Inyectar ToolRegistry en los agentes via AgentContext
- Agentes existentes (SDLC F1-F3) pueden usar herramientas
- Test: un agente puede invocar ReadFileTool y recibir resultado

**Tests:** `test_tool_agent_integration.py` (2 tests)
- `test_agent_calls_tool`: AdaptationAgent invoca ReadFileTool → resultado valido
- `test_agent_calls_unauthorized_tool`: agente sin permiso → error de permiso

### Dia 28 — Tests de integracion S3

**Tests (`test_integration_s3.py` ~4 tests):**
- `test_tool_registry_full_flow`: registrar 8 tools → ejecutar cada una → resultados correctos
- `test_concurrent_tool_execution`: 5 herramientas en paralelo → todas completan
- `test_tool_error_propagation`: tool que falla → error propagado al agente
- `test_tool_registry_audit_chain`: 10 ejecuciones → 10 eventos tool.executed en el bus

### Dia 29 — Buffer / Ruff cleanup

- `ruff check . --no-fix` → 0 errors
- `ruff format . --check` → sin cambios

### Dia 30 — Buffer

---

## Sprint 4: Tools batch 2 + WorldModel start (10 dias)

**Objetivo:** Completar las 8 herramientas restantes e iniciar el World Model.

**Archivos del sprint:** 7
**LOC estimado:** ~700
**Tests:** ~28

### Dia 31 — TestRunnerTool + TerminalTool

`tools/test_runner_tool.py`
`tools/terminal_tool.py`

**Logica:**

```python
class TestRunnerTool(BaseTool):
    name = "test_runner"
    description = "Run tests and parse results"
    allowed_agents = ["test-agent", "coding-agent"]
    
    # Frameworks detectables
    FRAMEWORKS = {
        "pytest": {"cmd": ["pytest"], "parser": "pytest"},
        "jest": {"cmd": ["npx", "jest"], "parser": "jest"},
        "go_test": {"cmd": ["go", "test"], "parser": "go"},
    }
    
    async def execute(self, params: dict) -> ToolResult:
        path = params.get("path", ".")
        framework = params.get("framework") or self._detect_framework(path)
        args = params.get("args", ["-v", "--tb=short"])
        timeout = params.get("timeout", 60)
        
        cmd = self.FRAMEWORKS[framework]["cmd"] + args + [path]
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=path
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            
            # Parsear resultados segun framework
            results = self._parse_results(
                stdout.decode(), framework
            )
            
            return ToolResult(True, {
                "framework": framework,
                "passed": results["passed"],
                "failed": results["failed"],
                "errors": results["errors"],
                "skipped": results.get("skipped", 0),
                "coverage": results.get("coverage"),
                "output": stdout.decode()[:5000]
            }, None, 0, self.name)
            
        except asyncio.TimeoutError:
            return ToolResult(False, None, "Test timeout exceeded", 0, self.name)

class TerminalTool(BaseTool):
    """Ejecuta comandos en sandbox. Solo comandos en lista blanca."""
    name = "terminal"
    description = "Execute shell commands (whitelist only)"
    allowed_agents = ["*"]
    
    WHITELIST = [
        "ls", "cat", "head", "tail", "wc", "sort", "uniq",
        "echo", "pwd", "which", "type", "file", "stat",
        "date", "cal", "df", "du", "env", "printenv",
        "npm", "npx", "pip", "python", "node", "tsc",
        "prisma", "docker-compose",
    ]
    
    async def execute(self, params: dict) -> ToolResult:
        command = params.get("command", "")
        args = params.get("args", [])
        timeout = params.get("timeout", 30)
        
        # Validar whitelist
        base = command.split()[0] if isinstance(command, str) else command
        if base not in self.WHITELIST:
            return ToolResult(False, None, 
                            f"Command not in whitelist: {base}", 0, self.name)
        
        cmd = [command] + args if isinstance(command, str) else [command] + args
        
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            return ToolResult(proc.returncode == 0, {
                "stdout": stdout.decode()[:10000],
                "stderr": stderr.decode()[:5000],
                "returncode": proc.returncode
            }, stderr.decode() if proc.returncode else None, 0, self.name)
        except asyncio.TimeoutError:
            return ToolResult(False, None, "Command timeout", 0, self.name)
```

**Tests:** `test_test_runner_tool.py` + `test_terminal_tool.py` (4 tests)
- `test_detect_pytest_framework`: directorio con test_*.py → pytest detectado
- `test_parse_pytest_results`: output pytest parseado → passed, failed contados
- `test_terminal_whitelist_allow`: comando en whitelist → ejecutado
- `test_terminal_whitelist_block`: comando no whitelist → bloqueado

**Criterio:** `ruff check . && ruff format .`

### Dia 32 — ASTTool + DependencyGraphTool

`tools/ast_tool.py`
`tools/dependency_graph_tool.py`

**Logica:**

```python
class ASTTool(BaseTool):
    """Wrapper sobre TreeSitterParser + ASTBuilder para consulta de AST."""
    name = "ast"
    description = "Build and query AST of source files"
    allowed_agents = ["*"]
    
    def __init__(self, parser: TreeSitterParser, ast_builder: ASTBuilder,
                 language_detector: LanguageDetector):
        self.parser = parser
        self.ast_builder = ast_builder
        self.language_detector = language_detector
    
    async def execute(self, params: dict) -> ToolResult:
        action = params.get("action")  # parse | get_symbols | get_metrics | get_imports
        path = params.get("path")
        
        lang = self.language_detector.detect(path)
        if not lang:
            return ToolResult(False, None, f"Cannot detect language: {path}", 0, self.name)
        
        with open(path, "r") as f:
            source = f.read()
        
        syntax_tree = self.parser.parse(source, lang)
        ast = self.ast_builder.build(path, source, lang, syntax_tree)
        
        if action == "get_symbols":
            return ToolResult(True, {"symbols": [s.dict() for s in ast.symbols]}, None, 0, self.name)
        elif action == "get_metrics":
            return ToolResult(True, ast.metrics.dict(), None, 0, self.name)
        elif action == "get_imports":
            return ToolResult(True, {"imports": ast.imports}, None, 0, self.name)
        else:
            return ToolResult(True, {
                "language": ast.language,
                "symbols": [s.dict() for s in ast.symbols],
                "imports": ast.imports,
                "metrics": ast.metrics.dict()
            }, None, 0, self.name)

class DependencyGraphTool(BaseTool):
    """Wrapper sobre DependencyGraph para consulta."""
    name = "dependency_graph"
    description = "Query the dependency graph"
    allowed_agents = ["*"]
    
    def __init__(self, dep_graph: DependencyGraph, kg: KnowledgeGraph):
        self.dep_graph = dep_graph
        self.kg = kg
    
    async def execute(self, params: dict) -> ToolResult:
        action = params.get("action")  # dependencies | dependents | cycles | unused
        path = params.get("path")
        
        if action == "dependencies":
            deps = await self.kg.get_outgoing(path, EdgeType.IMPORTS)
            return ToolResult(True, {"dependencies": [d.target_id for d in deps]}, None, 0, self.name)
        elif action == "dependents":
            deps = await self.kg.get_incoming(path, EdgeType.IMPORTS)
            return ToolResult(True, {"dependents": [d.source_id for d in deps]}, None, 0, self.name)
        elif action == "cycles":
            graph = await self._load_graph()
            cycles = self.dep_graph.find_cycles(graph)
            return ToolResult(True, {"cycles": cycles, "count": len(cycles)}, None, 0, self.name)
        elif action == "unused":
            graph = await self._load_graph()
            unused = self.dep_graph.find_unused_dependencies(graph)
            return ToolResult(True, {"unused": unused, "count": len(unused)}, None, 0, self.name)
```

**Tests:** `test_ast_tool.py` + `test_dependency_graph_tool.py` (4 tests)
- `test_ast_parse_file`: archivo Python parseado → symbols + metrics
- `test_ast_get_imports`: archivo con imports → imports extraidos
- `test_dep_graph_dependencies`: query dependencies de archivo → lista
- `test_dep_graph_cycles`: grafo con ciclo → ciclos detectados

**Criterio:** `ruff check . && ruff format .`

### Dia 33 — LSPTool + EmbeddingSearchTool

`tools/lsp_tool.py`
`tools/embedding_search_tool.py`

**Logica:**

```python
class LSPTool(BaseTool):
    """Code intelligence via LSP protocol.
    
    Funcionalidad basica (sin servidor LSP completo):
    - goto_definition: regex-based (fallback hasta tener LSP server)
    - find_references: regex-based
    - hover: no implementado en v1 (requiere servidor LSP activo)
    """
    name = "lsp"
    description = "Code intelligence: goto definition, find references"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        action = params.get("action")
        symbol = params.get("symbol")
        path = params.get("path")
        
        if action == "goto_definition":
            return await self._goto_definition(symbol, path)
        elif action == "find_references":
            return await self._find_references(symbol, path)
        
        return ToolResult(False, None, f"Unknown action: {action}", 0, self.name)
    
    async def _goto_definition(self, symbol: str, path: str) -> ToolResult:
        """Find definition of a symbol using the SymbolGraph in KG."""
        results = await self.kg.query(
            node_type=NodeType.CLASS, # busqueda mas amplia
            filter={"name": symbol}
        )
        # Tambien buscar en FUNCTION, METHOD, INTERFACE
        more = await self.kg.query(node_type=NodeType.FUNCTION, filter={"name": symbol})
        results.extend(more)
        
        if results:
            return ToolResult(True, {
                "definitions": [{
                    "name": r.properties["name"],
                    "file": r.properties["file"],
                    "line": r.properties.get("line"),
                    "id": r.id
                } for r in results]
            }, None, 0, self.name)
        
        return ToolResult(True, {"definitions": []}, None, 0, self.name)

class EmbeddingSearchTool(BaseTool):
    """Busqueda semantica en el codigo usando sentence-transformers."""
    name = "embedding_search"
    description = "Semantic code search using embeddings"
    allowed_agents = ["*"]
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None  # Lazy load
        self.model_name = model_name
        self.index: dict[str, list[float]] = {}  # file_path → embedding
    
    async def execute(self, params: dict) -> ToolResult:
        query = params.get("query")
        path = params.get("path", ".")
        top_k = params.get("top_k", 10)
        
        if not self.model:
            self.model = SentenceTransformer(self.model_name)
        
        # Codificar query
        query_emb = self.model.encode(query)
        
        # indexar si no existe
        if not self.index:
            await self._index_path(path)
        
        # Busqueda coseno
        scores = []
        for file_path, emb in self.index.items():
            score = np.dot(query_emb, emb) / (np.linalg.norm(query_emb) * np.linalg.norm(emb))
            scores.append((score, file_path))
        
        scores.sort(reverse=True)
        top_results = [{"file": f, "score": round(s, 4)} for s, f in scores[:top_k]]
        
        return ToolResult(True, {
            "results": top_results,
            "total_indexed": len(self.index)
        }, None, 0, self.name)
```

**Tests:** `test_lsp_tool.py` + `test_embedding_search_tool.py` (4 tests)
- `test_goto_definition`: simbolo definido en clase → definicion encontrada
- `test_find_references`: simbolo referenciado → referencias encontradas
- `test_embedding_search_semantic`: busqueda semantica → resultados relevantes
- `test_embedding_search_no_results`: busqueda sin matches → resultados vacios

**Criterio:** `ruff check . && ruff format .`

### Dia 34 — SymbolLookupTool + BrowserTool + Integracion tools batch 2

`tools/symbol_lookup_tool.py`
`tools/browser_tool.py`

**Logica:**

```python
class SymbolLookupTool(BaseTool):
    """Busqueda de simbolos en el Repository Graph."""
    name = "symbol_lookup"
    description = "Look up symbols in the Repository Graph"
    allowed_agents = ["*"]
    
    async def execute(self, params: dict) -> ToolResult:
        name = params.get("name")
        symbol_type = params.get("type")  # class, function, method, interface, all
        file_path = params.get("file_path")
        
        # Query al Knowledge Graph
        filter_dict = {"name": name}
        if file_path:
            filter_dict["file"] = file_path
        
        results = await self.kg.query(
            node_type=symbol_type if symbol_type != "all" else None,
            filter=filter_dict
        )
        
        return ToolResult(True, {
            "symbols": [{
                "id": r.id, "name": r.properties.get("name"),
                "type": r.node_type, "file": r.properties.get("file"),
                "line": r.properties.get("line")
            } for r in results],
            "total": len(results)
        }, None, 0, self.name)

class BrowserTool(BaseTool):
    """Navegacion web para documentacion / busqueda."""
    name = "browser"
    description = "Fetch web content (documentation, APIs)"
    allowed_agents = ["documentation-agent"]
    
    async def execute(self, params: dict) -> ToolResult:
        url = params.get("url")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, headers={
                    "User-Agent": "RECPL-Assistant/1.0"
                })
                resp.raise_for_status()
                
                # Extraer texto (sin HTML tags)
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(strip=True)[:10000]
                
                return ToolResult(True, {
                    "url": url, "status": resp.status_code,
                    "content": text, "title": soup.title.string if soup.title else ""
                }, None, 0, self.name)
        except httpx.HTTPError as e:
            return ToolResult(False, None, f"HTTP error: {e}", 0, self.name)
```

**Tests:** (4 tests)
- `test_symbol_lookup_by_name`: buscar "UserService" → simbolo encontrado
- `test_symbol_lookup_nonexistent`: simbolo inexistente → total=0
- `test_browser_fetch_url`: fetch URL valida → contenido obtenido
- `test_browser_timeout`: URL timeout → error graceful

**Criterio:** `ruff check . && ruff format .`

### Dia 35 — WorldModelAgent (clase base + ciclo)

`agents/world_model_agent.py`

**Logica:**

```python
class WorldModelAgent(Agent):
    """Agente de World Model: mantiene estado global del proyecto.
    
    NO es el World Model en si. Es el agente que actualiza
    el Knowledge Graph con datos del mundo exterior.
    """
    
    manifest = CapabilityManifest(
        agent_id="world-model-agent",
        description="Maintains project-level global state",
        triggers=[
            "repository.scan.completed",
            "schedule.hourly",
        ],
        output_events=["world.model.updated"]
    )
    
    async def handle_event(self, event: Event):
        if event.topic == "repository.scan.completed":
            await self._update_from_scan(event.data)
        elif event.topic == "schedule.hourly":
            await self._refresh_state()
    
    async def _update_from_scan(self, data: dict):
        """Actualiza World Model desde un scan del repositorio."""
        # 1. Detectar microservicios
        services = await self._detect_services(data["path"])
        
        # 2. Detectar dependencias externas
        deps = await self._detect_dependencies(data["path"])
        
        # 3. Detectar base de datos
        db = await self._detect_database(data["path"])
        
        # 4. Escribir al KG
        for svc in services:
            await self.kg.add_node(Node(
                id=svc.id, node_type=NodeType.MICROSERVICE,
                properties=svc.dict()
            ))
        
        for dep in deps:
            await self.kg.add_node(Node(
                id=f"dep-{dep['name']}", node_type=NodeType.DEPENDENCY,
                properties=dep
            ))
        
        if db:
            await self.kg.add_node(Node(
                id=f"db-{db['type']}", node_type=NodeType.DATABASE,
                properties=db
            ))
        
        await self.event_bus.publish(Event(
            topic="world.model.updated",
            source=self.agent_id,
            data={"services": len(services), "deps": len(deps)}
        ))
```

**Tests:** `test_world_model_agent.py` (3 tests)
- `test_update_from_scan`: scan completado → servicios + dependencias en KG
- `test_hourly_refresh`: evento hourly → refresh ejecutado sin error
- `test_no_services_detected`: repo sin microservicios → world.model.updated con services=0

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_world_model_agent.py -v`

### Dia 36 — ServiceMap + DependencyTracker

`world_model/service_map.py`
`world_model/dependency_tracker.py`

**Logica:**

```python
class ServiceMap:
    """Topologia de microservicios detectada desde el codigo."""
    
    async def detect(self, root_path: str) -> list[Service]:
        """Detecta microservicios en el repositorio.
        
        Heuristics:
        - Directorios con package.json/pyproject.toml independientes
        - Dockerfiles por directorio
        - docker-compose con multiples servicios
        """
        services = []
        
        # Buscar docker-compose
        compose_path = os.path.join(root_path, "docker-compose.yml")
        if os.path.exists(compose_path):
            services = await self._from_docker_compose(compose_path)
        
        # Buscar package.json independientes
        for pkg in glob.glob(os.path.join(root_path, "**/package.json"), recursive=True):
            if self._is_independent_service(pkg):
                services.append(self._service_from_package(pkg))
        
        return services
    
    async def detect_connections(self, services: list[Service]) -> list[Connection]:
        """Detecta conexiones entre servicios (HTTP, message queue, DB)."""
        connections = []
        for svc in services:
            for dep in svc.dependencies:
                target = self._find_service_by_name(services, dep)
                if target:
                    connections.append(Connection(svc.id, target.id, "depends_on"))
        return connections

class DependencyTracker:
    """Rastrea dependencias externas del proyecto."""
    
    async def detect(self, root_path: str) -> list[dict]:
        """Detecta dependencias desde package.json / pyproject.toml."""
        deps = []
        
        pkg_json = os.path.join(root_path, "package.json")
        if os.path.exists(pkg_json):
            with open(pkg_json) as f:
                data = json.load(f)
                for name, version in (data.get("dependencies") or {}).items():
                    deps.append({"name": name, "version": version, "type": "runtime"})
                for name, version in (data.get("devDependencies") or {}).items():
                    deps.append({"name": name, "version": version, "type": "dev"})
        
        pyproject = os.path.join(root_path, "pyproject.toml")
        if os.path.exists(pyproject):
            # Parsear TOML
            ...
        
        return deps
```

**Tests:** `test_service_map.py` + `test_dependency_tracker.py` (4 tests)
- `test_detect_services_from_compose`: docker-compose con 2 servicios → 2 servicios
- `test_detect_connections`: servicio A depende de B → conexion detectada
- `test_detect_package_deps`: package.json con dependencias → deps extraidas
- `test_empty_project`: sin archivos → listas vacias

**Criterio:** `ruff check . && ruff format .`

### Dia 37 — Integracion World Model ↔ Knowledge Graph

**Logica:**
- ServiceMap escribe nodos MICROSERVICE al KG
- DependencyTracker escribe nodos DEPENDENCY
- Conexiones entre servicios → aristas DEPENDS_ON_SERVICE
- WorldModelAgent se suscribe a repository.scan.completed

**Tests:** (2 tests)
- `test_world_model_kg_integration`: scan → servicios + dependencias en KG
- `test_world_model_event_chain`: scan → world.model.updated → dashboard actualizado

### Dia 38 — Tests de integracion S4

**Tests (`test_integration_s4.py` ~4 tests):**
- `test_full_tool_registry_16_tools`: 16 tools registradas → cada una ejecutable
- `test_tool_ast_integration`: ASTTool consulta un archivo → resultado valido
- `test_world_model_from_repo_graph`: scan de repo → ServiceMap ejecutado → servicios en KG
- `test_concurrent_tools_and_world_model`: tools + world model operan simultaneamente

### Dia 39 — Buffer / Ruff cleanup

- `ruff check . --no-fix` → 0 errors
- `ruff format . --check` → sin cambios

### Dia 40 — Buffer

---

## Sprint 5: Routing + Memory + Integration (10 dias)

**Objetivo:** Construir IntentRouter, GoalManager, AgenticIR, MemorySystem 3 niveles, AgentGraphBuilder e integrar todo F4.

**Archivos del sprint:** 5
**LOC estimado:** ~650
**Tests:** ~25

### Dia 41 — IntentRouter

`core/intent_router.py`

**Logica:**

```python
class IntentRouter:
    """Router de intenciones. Clasifica el request y decide la ruta."""
    
    INTENTS = {
        "new_feature": {
            "agents": ["repository", "planning", "coding", "review", "test"],
            "requires_goal_manager": True
        },
        "refactor": {
            "agents": ["repository", "refactor", "review", "test"],
            "requires_goal_manager": False
        },
        "bugfix": {
            "agents": ["repository", "coding", "test"],
            "requires_goal_manager": False
        },
        "documentation": {
            "agents": ["repository", "documentation"],
            "requires_goal_manager": False
        },
        "test": {
            "agents": ["repository", "test"],
            "requires_goal_manager": False
        },
        "analysis": {
            "agents": ["repository"],
            "requires_goal_manager": False
        },
        "add_code": {
            "agents": ["repository", "coding"],
            "requires_goal_manager": False
        },
        "security_audit": {
            "agents": ["repository", "security"],
            "requires_goal_manager": False
        },
        "performance_audit": {
            "agents": ["repository", "performance"],
            "requires_goal_manager": False
        }
    }
    
    async def route(self, request: str) -> IntentRoute:
        """Clasifica request y retorna ruta."""
        
        # LLM ligero para clasificacion
        intent = await self._classify(request)
        
        route = self.INTENTS.get(intent, self.INTENTS["new_feature"])
        
        await self.event_bus.publish(Event(
            topic="intent.routed",
            source="intent-router",
            data={
                "intent": intent,
                "agents": route["agents"],
                "requires_goal_manager": route["requires_goal_manager"],
                "raw_request": request
            }
        ))
        
        return IntentRoute(
            intent=intent,
            agents=route["agents"],
            requires_goal_manager=route["requires_goal_manager"]
        )
    
    async def _classify(self, request: str) -> str:
        """Clasifica usando LLM o heuristicas."""
        # Heuristicas simples primero
        request_lower = request.lower()
        
        if any(w in request_lower for w in ["refactor", "reestructura", "mejora"]):
            return "refactor"
        if any(w in request_lower for w in ["bug", "error", "fallo", "arregla"]):
            return "bugfix"
        if any(w in request_lower for w in ["documenta", "doc", "readme", "explica"]):
            return "documentation"
        if any(w in request_lower for w in ["test", "prueba", "cobertura"]):
            return "test"
        if any(w in request_lower for w in ["analiza", "describe", "que hace"]):
            return "analysis"
        if any(w in request_lower for w in ["seguridad", "vulnerabilidad", "owasp"]):
            return "security_audit"
        if any(w in request_lower for w in ["rendimiento", "performance", "lento"]):
            return "performance_audit"
        
        # Si no hay match: asumir new_feature
        return "new_feature"
```

**Tests:** `test_intent_router.py` (4 tests)
- `test_route_new_feature`: "crea modulo de pagos" → intent=new_feature
- `test_route_refactor`: "refactoriza auth.service" → intent=refactor
- `test_route_bugfix`: "arregla error en login" → intent=bugfix
- `test_route_unknown`: "que hace esta funcion?" → intent=analysis

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_intent_router.py -v`

### Dia 42 — EpisodicMemory + SemanticMemory (basico)

`memory/base_memory.py`
`memory/episodic_memory.py`
`memory/semantic_memory.py`

**Logica:**

```python
class MemoryBase(ABC):
    """Base para los 3 niveles de memoria."""
    
    @abstractmethod
    async def store(self, data: MemoryData): ...
    
    @abstractmethod
    async def recall(self, query: MemoryQuery) -> list[MemoryData]: ...

class EpisodicMemory(MemoryBase):
    """Memoria episodica: sobre el EventBus log."""
    
    def __init__(self, event_bus: AsyncEventBus):
        self.event_bus = event_bus
    
    async def store(self, data: MemoryData):
        # Los eventos ya se almacenan en el EventBus
        # EpisodicMemory es una capa de consulta
        pass
    
    async def recall(self, query: MemoryQuery) -> list[MemoryData]:
        events = await self.event_bus.query_events(
            project=query.project_id,
            topic=query.topic_filter,
            since_time=query.since,
            limit=query.limit
        )
        return [MemoryData(
            type="episodic",
            key=event.id,
            content=event.data,
            timestamp=event.timestamp,
            metadata={"topic": event.topic, "source": event.source}
        ) for event in events]
    
    async def replay_session(self, session_id: str):
        """Replay de eventos de una sesion."""
        return await self.event_bus.replay(session_id)

class SemanticMemory(MemoryBase):
    """Memoria semantica: patrones y conocimiento del proyecto.
    
    Se construye desde el Repository Graph + Architecture Detector.
    """
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    async def store(self, data: MemoryData):
        await self.kg.add_node(Node(
            node_type="semantic_fact",
            properties={
                "fact": data.content,
                "context": data.metadata,
                "timestamp": data.timestamp
            }
        ))
    
    async def recall(self, query: MemoryQuery) -> list[MemoryData]:
        results = await self.kg.query(
            node_type="semantic_fact",
            filter=query.filters
        )
        return [MemoryData(
            type="semantic",
            key=r.id,
            content=r.properties["fact"],
            timestamp=r.properties.get("timestamp"),
            metadata=r.properties.get("context", {})
        ) for r in results]
    
    async def get_architecture_pattern(self) -> str | None:
        """Recupera el patron arquitectonico del proyecto."""
        patterns = await self.kg.query(node_type="architecture_pattern")
        if patterns:
            return patterns[0].properties.get("pattern")
        return None
```

**Tests:** `test_episodic_memory.py` + `test_semantic_memory.py` (4 tests)
- `test_episodic_recall_recent`: eventos recientes recuperados
- `test_episodic_recall_filtered`: eventos filtrados por topic
- `test_semantic_store_and_recall`: hecho almacenado → recuperado
- `test_semantic_architecture_pattern`: patron arquitectonico recuperado

**Criterio:** `ruff check . && ruff format .`

### Dia 43 — ProceduralMemory

`memory/procedural_memory.py`

**Logica:**

```python
class ProceduralMemory(MemoryBase):
    """Memoria procedural: recetas y workflows.
    
    Almacena secuencias de acciones probadas para tipos de tarea.
    """
    
    # Recetas base (hardcodeadas inicialmente, aprendidas despues via ExperienceEngine)
    BASE_RECIPES = {
        "create_nestjs_endpoint": [
            {"step": "create_dto", "tool": "write_file", 
             "description": "Crear DTO con validacion"},
            {"step": "create_service", "tool": "write_file",
             "description": "Crear service con logica de negocio"},
            {"step": "create_controller", "tool": "write_file",
             "description": "Crear controller con endpoints"},
            {"step": "update_module", "tool": "write_file",
             "description": "Actualizar module con nuevos providers"},
            {"step": "create_test", "tool": "write_file",
             "description": "Crear test del endpoint"},
            {"step": "run_tests", "tool": "test_runner",
             "description": "Ejecutar tests"},
        ],
        "add_prisma_model": [
            {"step": "update_schema", "tool": "read_file",
             "description": "Leer schema.prisma actual"},
            {"step": "add_model", "tool": "write_file",
             "description": "Agregar modelo al schema"},
            {"step": "generate_migration", "tool": "terminal",
             "description": "Generar migracion"},
            {"step": "apply_migration", "tool": "terminal",
             "description": "Aplicar migracion"},
        ],
        "create_test_file": [
            {"step": "analyze_source", "tool": "ast",
             "description": "Analizar codigo fuente"},
            {"step": "create_test", "tool": "write_file",
             "description": "Crear archivo de test"},
            {"step": "run_tests", "tool": "test_runner",
             "description": "Ejecutar tests y verificar"},
        ],
        "add_react_component": [
            {"step": "create_component", "tool": "write_file",
             "description": "Crear componente TSX"},
            {"step": "create_styles", "tool": "write_file",
             "description": "Crear estilos CSS/Tailwind"},
            {"step": "create_test", "tool": "write_file",
             "description": "Crear test del componente"},
            {"step": "update_exports", "tool": "write_file",
             "description": "Actualizar barrel exports"},
        ],
    }
    
    async def get_recipe(self, task_type: str) -> list[Step]:
        """Recupera receta para un tipo de tarea."""
        # Primero buscar recetas aprendidas (KG)
        learned = await self.kg.query(
            node_type="procedure",
            filter={"task_type": task_type}
        )
        if learned:
            return learned[0].properties["steps"]
        
        # Fallback a recetas base
        return self.BASE_RECIPES.get(task_type, [])
    
    async def learn_recipe(self, task_type: str, steps: list[dict], 
                            success_rate: float):
        """Aprende o actualiza una receta basada en experiencia."""
        await self.kg.add_node(Node(
            node_type="procedure",
            properties={
                "task_type": task_type,
                "steps": steps,
                "success_rate": success_rate,
                "learned_at": time.time()
            }
        ))
    
    async def suggest_optimization(self, task_type: str, 
                                     execution_log: list[dict]) -> list[Step]:
        """Sugiere optimizacion de receta basada en ejecucion real."""
        recipe = await self.get_recipe(task_type)
        if not recipe:
            return []
        
        # Comparar pasos planeados vs reales
        optimizations = []
        for planned, actual in zip(recipe, execution_log):
            if planned["tool"] != actual.get("tool_used"):
                optimizations.append({
                    "step": planned["step"],
                    "suggestion": f"Use {actual.get('tool_used')} instead of {planned['tool']}"
                })
        
        return optimizations
```

**Tests:** `test_procedural_memory.py` (3 tests)
- `test_get_existing_recipe`: "create_nestjs_endpoint" → 6 pasos
- `test_get_nonexistent_recipe`: tipo desconocido → lista vacia
- `test_learn_new_recipe`: aprender receta → recuperable

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_procedural_memory.py -v`

### Dia 44 — AgentGraphBuilder + GoalManager (basico)

`core/agent_graph_builder.py`
`core/goal_manager.py`

**Logica:**

```python
class AgentGraphBuilder:
    """Construye StateGraph dinamico segun la ruta de agentes."""
    
    def build(self, route: IntentRoute, agents: dict[str, Agent]) -> StateGraph:
        """Construye grafo de agentes para una ruta."""
        graph = StateGraph(AgentContext)
        
        # Nodo inicial: planificador
        graph.add_node("planning", agents["planning"])
        graph.set_entry_point("planning")
        
        # Nodo final: git commit (si es necesario)
        if any(a in route.agents for a in ["coding", "refactor", "test"]):
            graph.add_node("git_commit", self._git_commit_node())
        
        # Conectar agentes en orden
        prev = "planning"
        for agent_name in route.agents:
            if agent_name == "planning":
                continue
            graph.add_node(agent_name, agents[agent_name])
            graph.add_edge(prev, agent_name)
            prev = agent_name
        
        # Arista final
        if prev != "planning":
            graph.add_edge(prev, "git_commit")
        
        return graph.compile()

class GoalManager:
    """Descompone una solicitud en objetivos atomicos."""
    
    async def decompose(self, request: str) -> list[Goal]:
        """Descompone request en objetivos atomicos."""
        
        # Heuristicas simples (sin LLM en F4 basico)
        goals = self._heuristic_decompose(request)
        
        # Almacenar en KG
        for goal in goals:
            await self.kg.add_node(Node(
                id=goal.id, node_type=NodeType.GOAL,
                properties={
                    "description": goal.description,
                    "type": goal.type,
                    "priority": goal.priority,
                    "status": "pending"
                }
            ))
        
        for goal in goals:
            for dep_id in goal.dependencies:
                await self.kg.add_edge(Edge(
                    source_id=goal.id, target_id=dep_id,
                    edge_type=EdgeType.DEPENDS_ON
                ))
        
        return goals
    
    def _heuristic_decompose(self, request: str) -> list[Goal]:
        """Descomposicion por heuristicas (conectores linguisticos)."""
        # Detectar conectores "y", "ademas", "tambien"
        parts = re.split(r'\b(y |ademas |tambien )', request)
        
        goals = []
        for i, part in enumerate(parts):
            part = part.strip()
            if len(part) > 10:  # minimo 10 chars
                goal_type = self._detect_type(part)
                goals.append(Goal(
                    id=f"g-{i+1:03d}",
                    description=part,
                    type=goal_type,
                    dependencies=[],
                    priority="medium"
                ))
        
        if not goals:
            goals.append(Goal(
                id="g-001", description=request,
                type=self._detect_type(request),
                dependencies=[], priority="high"
            ))
        
        return goals
```

**Tests:** `test_agent_graph_builder.py` + `test_goal_manager.py` (4 tests)
- `test_build_simple_route`: route con 2 agentes → grafo con 2 nodos + entry
- `test_build_with_git_commit`: route con coding → grafo incluye git_commit
- `test_decompose_single_goal`: "crear modulo auth" → 1 goal
- `test_decompose_multi_goal`: "crear auth y documentar API" → 2 goals

**Criterio:** `ruff check . && ruff format .`

### Dia 45 — AgenticIR (dataclass, builder, serializer, validator)

`core/agentic_ir.py`
`core/ir_registry.py`

**Logica:**

```python
@dataclass
class AgenticIR:
    """Representacion Intermedia Agentica.
    
    No describe codigo. Describe la INTENCION de una tarea.
    Sirve como contrato entre PlanningAgent y los agentes ejecutores.
    """
    ir_id: str
    goal: str
    entity: str | None
    framework: str | None
    constraints: list[str]
    parent_ir: str | None
    dependencies: list[str]
    acceptance_criteria: list[str]
    estimated_complexity: str  # simple | moderate | complex
    model_preference: str | None

class AgenticIRBuilder:
    """Construye AgenticIR desde un Goal."""
    
    async def build(self, goal: Goal, context: dict = None) -> AgenticIR:
        """Construye AgenticIR desde un Goal."""
        
        # Extraer entidad, framework y constraints del goal
        entity = self._extract_entity(goal.description)
        framework = self._extract_framework(goal.description)
        constraints = self._extract_constraints(goal.description)
        
        acceptance = await self._generate_acceptance(goal, entity)
        
        return AgenticIR(
            ir_id=f"air-{uuid4().hex[:8]}",
            goal=goal.description,
            entity=entity,
            framework=framework,
            constraints=constraints,
            parent_ir=None,
            dependencies=goal.dependencies,
            acceptance_criteria=acceptance,
            estimated_complexity=self._estimate_complexity(goal),
            model_preference=self._model_for_goal(goal.type)
        )
    
    def _extract_entity(self, text: str) -> str | None:
        """Extrae la entidad principal del texto."""
        # Heuristica simple: buscar palabras despues de "modulo", "entidad", "servicio"
        patterns = [
            r'(?:modulo|entidad|servicio|modelo)\s+(?:de\s+)?(\w+)',
            r'(?:para|del)\s+(\w+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).capitalize()
        return None

class AgenticIRSerializer:
    """Serializa/deserializa AgenticIR a JSON/YAML."""
    
    @staticmethod
    def to_json(ir: AgenticIR) -> str:
        return json.dumps({
            "ir_id": ir.ir_id,
            "goal": ir.goal,
            "entity": ir.entity,
            "framework": ir.framework,
            "constraints": ir.constraints,
            "parent_ir": ir.parent_ir,
            "dependencies": ir.dependencies,
            "acceptance_criteria": ir.acceptance_criteria,
            "estimated_complexity": ir.estimated_complexity,
            "model_preference": ir.model_preference
        }, indent=2)
    
    @staticmethod
    def from_json(data: str) -> AgenticIR:
        d = json.loads(data)
        return AgenticIR(**d)

class AgenticIRValidator:
    """Valida integridad de un AgenticIR."""
    
    def validate(self, ir: AgenticIR) -> list[str]:
        errors = []
        if not ir.ir_id:
            errors.append("ir_id is required")
        if not ir.goal:
            errors.append("goal is required")
        if ir.estimated_complexity not in ("simple", "moderate", "complex"):
            errors.append(f"invalid complexity: {ir.estimated_complexity}")
        if ir.dependencies and ir.parent_ir:
            # No puede tener parent y dependencies simultaneamente
            errors.append("cannot have both parent_ir and dependencies")
        return errors

class AgenticIRRegistry:
    """Registro de AgenticIRs activos."""
    
    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
    
    async def register(self, ir: AgenticIR):
        await self.kg.add_node(Node(
            id=ir.ir_id, node_type=NodeType.TASK_IR,
            properties=asdict(ir)
        ))
    
    async def get(self, ir_id: str) -> AgenticIR | None:
        node = await self.kg.get_node(ir_id)
        if node:
            return AgenticIR(**node.properties)
        return None
    
    async def get_chain(self, ir_id: str) -> list[AgenticIR]:
        """Recupera cadena completa: IR → sub-IRs → sub-sub-IRs."""
        chain = []
        current = await self.get(ir_id)
        while current:
            chain.append(current)
            # Buscar hijos
            children = await self.kg.query(
                node_type=NodeType.TASK_IR,
                filter={"parent_ir": current.ir_id}
            )
            if children:
                current = AgenticIR(**children[0].properties)
            else:
                break
        return chain
```

**Tests:** `test_agentic_ir.py` (5 tests)
- `test_ir_creation`: datos minimos → AgenticIR valido
- `test_ir_serialization_roundtrip`: JSON → AgenticIR → JSON → mismo contenido
- `test_ir_validation_valid`: IR completo → 0 errores
- `test_ir_validation_invalid`: IR sin goal → error
- `test_ir_registry_register_and_get`: registrar IR → recuperable por ID

**Criterio:** `ruff check . && ruff format . && python -m pytest tests/test_agentic_ir.py -v`

### Dia 46 — Integracion F4 (todos los componentes conectados)

`compiler-bot/agentic` (actualizar entrypoint)

**Logica:**
- Unificar los 5 sprints en un solo entrypoint
- CLI flags: `--mode pipeline|agentic` (elegir modo)
- Modo agentic: IntentRouter → GoalManager → AgenticIR → tools → Memory
- Modo pipeline: pipeline clasico (legacy)

```python
# compiler-bot/agentic (actualizado)
async def main_agentic_mode(prompt: str):
    """Nuevo modo agentic."""
    # 1. Clasificar intencion
    route = await intent_router.route(prompt)
    
    # 2. Descomponer objetivos
    if route.requires_goal_manager:
        goals = await goal_manager.decompose(prompt)
    else:
        goals = [Goal(id="g-001", description=prompt, type=route.intent)]
    
    # 3. Construir grafo de agentes
    graph = agent_graph_builder.build(route, agents)
    
    # 4. Para cada goal, generar AgenticIR y ejecutar
    for goal in goals:
        air = await agentic_ir_builder.build(goal)
        await ir_registry.register(air)
        
        # Ejecutar grafo
        result = await graph.ainvoke({
            "air": air,
            "tools": tool_registry,
            "memory": memory_system,
            "kg": knowledge_graph
        })
    
    return {"mode": "agentic", "goals": len(goals), "result": result}
```

**Tests:** `test_f4_integration.py` (3 tests)
- `test_agentic_mode_flow`: prompt → IntentRouter → GoalManager → AgenticIR → resultado
- `test_mode_selection`: flag `--mode agentic` → modo agentic, flag `--mode pipeline` → modo clasico
- `test_agentic_mode_simple_request`: "crea modulo users" → 1 goal, 1 AgenticIR, ejecucion

**Criterio:** `ruff check . && ruff format .`

### Dia 47 — Tests de integracion F4 completo

**Tests (`test_integration_f4.py` ~6 tests):**
- `test_end_to_end_simple`: prompt simple → intent.route → goal.decompose → agentic_ir.build → registry.store
- `test_end_to_end_with_repo_scan`: prompt + path → repo scan → world model → intent route → goal → IR
- `test_tool_execution_during_flow`: agente invoca ReadFileTool durante flujo → resultado valido
- `test_memory_recall_during_flow`: agente consulta memoria episodica durante flujo → eventos recuperados
- `test_goal_manager_multi_goal`: prompt con 2 objetivos → 2 goals, ambos procesados
- `test_f4_no_regression`: pipeline clasico (`--mode pipeline`) sigue funcionando igual que antes

### Dia 48 — Ruff cleanup + docstrings

- Docstrings en 100% de clases y metodos publicos de F4
- `ruff check . --no-fix` → 0 errors
- `ruff format . --check` → sin cambios

### Dia 49 — Buffer

### Dia 50 — Buffer + Demo

- Verificar ejemplos de uso:
  - `python -m compiler-bot.agentic "crea modulo users" --mode agentic`
  - `python -m compiler-bot.agentic "analiza este proyecto" --path ./test-project --mode agentic`
  - `python -m compiler-bot.agentic "crea auth y documenta API" --mode agentic`
- `python -m pytest tests/ -v -o "addopts="` → ~140 tests nuevos PASS
- Tests existentes (1,072) no afectados

---

## Resumen de Archivos F4

| Sprint | Archivo | LOC est. | Tests |
|--------|---------|----------|-------|
| **S1** | `repository_agent/__init__.py` | 10 | — |
| S1 | `repository_agent/base_parser.py` | 30 | 2 |
| S1 | `repository_agent/language_detector.py` | 80 | 5 |
| S1 | `repository_agent/treesitter_parser.py` | 150 | 9 |
| S1 | `repository_agent/ast_builder.py` | 120 | 7 |
| S1 | `repository_agent/repository_intelligence_agent.py` | 150 | 7 |
| S1 | `repository_agent/repository_graph_builder.py` | 160 | 6 |
| | *Subtotal S1* | *~700* | *~36* |
| **S2** | `repository_agent/symbol_graph.py` | 120 | 7 |
| S2 | `repository_agent/dependency_graph.py` | 120 | 7 |
| S2 | `repository_agent/architecture_detector.py` | 140 | 7 |
| S2 | Tests de endpoint detection | 60 | 3 |
| S2 | Tests de integracion SDLC-Repo | 60 | 3 |
| | *Subtotal S2* | *~500* | *~27* |
| **S3** | `core/tool_registry.py` | 80 | 4 |
| S3 | `core/base_tool.py` | 40 | 1 |
| S3 | `tools/read_file_tool.py` | 60 | 3 |
| S3 | `tools/write_file_tool.py` | 60 | 2 |
| S3 | `tools/search_tool.py` | 70 | 3 |
| S3 | `tools/ripgrep_tool.py` | 50 | 2 |
| S3 | `tools/glob_tool.py` | 40 | 2 |
| S3 | `tools/diff_tool.py` | 50 | 2 |
| S3 | `tools/git_tool.py` | 70 | 3 |
| S3 | `tools/docker_tool.py` | 60 | 1 |
| S3 | Tool security + audit | 50 | 4 |
| | *Subtotal S3* | *~630* | *~27* |
| **S4** | `tools/test_runner_tool.py` | 80 | 2 |
| S4 | `tools/terminal_tool.py` | 70 | 2 |
| S4 | `tools/ast_tool.py` | 60 | 2 |
| S4 | `tools/dependency_graph_tool.py` | 50 | 2 |
| S4 | `tools/lsp_tool.py` | 60 | 2 |
| S4 | `tools/embedding_search_tool.py` | 70 | 2 |
| S4 | `tools/symbol_lookup_tool.py` | 40 | 2 |
| S4 | `tools/browser_tool.py` | 40 | 2 |
| S4 | `agents/world_model_agent.py` | 80 | 3 |
| S4 | `world_model/service_map.py` | 80 | 2 |
| S4 | `world_model/dependency_tracker.py` | 60 | 2 |
| | *Subtotal S4* | *~690* | *~23* |
| **S5** | `core/intent_router.py` | 80 | 4 |
| S5 | `memory/base_memory.py` | 20 | — |
| S5 | `memory/episodic_memory.py` | 50 | 2 |
| S5 | `memory/semantic_memory.py` | 60 | 2 |
| S5 | `memory/procedural_memory.py` | 100 | 3 |
| S5 | `core/agent_graph_builder.py` | 70 | 2 |
| S5 | `core/goal_manager.py` | 80 | 2 |
| S5 | `core/agentic_ir.py` | 60 | 3 |
| S5 | `core/ir_registry.py` | 40 | 2 |
| S5 | Integracion F4 | 100 | 3 |
| | *Subtotal S5* | *~660* | *~23* |
| | **Total F4** | **~3,180** | **~136** |

---

## Criterio de Exito F4

```bash
# 1. Ruff check
ruff check . --no-fix          # 0 errors
ruff format . --check           # sin cambios

# 2. Tests nuevos
python -m pytest tests/test_language_detector.py \
  tests/test_treesitter_parser.py \
  tests/test_ast_builder.py \
  tests/test_repository_intelligence_agent.py \
  tests/test_repository_graph_builder.py \
  tests/test_symbol_graph.py \
  tests/test_dependency_graph.py \
  tests/test_architecture_detector.py \
  tests/test_tool_registry.py \
  tests/test_read_file_tool.py \
  tests/test_write_file_tool.py \
  tests/test_search_tool.py \
  tests/test_glob_tool.py \
  tests/test_diff_tool.py \
  tests/test_git_tool.py \
  tests/test_world_model_agent.py \
  tests/test_intent_router.py \
  tests/test_episodic_memory.py \
  tests/test_semantic_memory.py \
  tests/test_procedural_memory.py \
  tests/test_goal_manager.py \
  tests/test_agent_graph_builder.py \
  tests/test_agentic_ir.py \
  tests/test_integration_f4.py \
  -v -o "addopts="              # ~136 tests PASS

# 3. Tests legacy no rotos
python -m pytest compiler-bot/agentic_pipeline/tests/ -q -o "addopts="  # sigue pasando

# 4. Smoke tests
python -m compiler-bot.agentic "crea modulo users" --mode agentic
python -m compiler-bot.agentic "analiza este proyecto" --path ./ --mode agentic
python -m compiler-bot.agentic "crea auth y documenta API" --mode agentic

# 5. Backward compatibility
python -m compiler-bot.agentic "crea modulo payments en NestJS" --mode pipeline
# (debe producir el mismo resultado que antes de F4)
```

---

## Dependencias entre Sprints

```
S1 ──> S2 ──> S3 ──> S4 ──> S5
 │      │      │      │      │
 │      │      │      │      └── Depende de S1-S4 (integracion total)
 │      │      │      │
 │      │      │      └── Depende de S3 (ToolRegistry para tools batch 2)
 │      │      │           Depende de S1 (Repository Graph para WorldModel)
 │      │      │
 │      │      └── Depende de S1 (BaseTool + ToolRegistry)
 │      │
 │      └── Depende de S1 (ASTBuilder para SymbolGraph)
 │
 └── (ninguna dependencia externa, primer sprint)
```

**Sprints paralelizables:** S3 puede comenzar inmediatamente despues de S1 (no necesita S2). S1 y S2 son secuenciales.

---

## Riesgos Especificos F4

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **TreeSitter no disponible** en el entorno | Media | Alto | Fallback a regex-based parsing. TreeSitter tiene wheels precompilados para la mayoria de plataformas. |
| **LSPTool sin servidor LSP real** | Alta | Medio | F4 implementa LSPTool con busqueda regex-based + consultas al SymbolGraph. LSP real se difiere a F6. |
| **EmbeddingSearchTool lento en repos grandes** | Alta | Bajo | Indexacion lazy (solo archivos consultados). Limite de 10,000 archivos indexados. |
| **Repository Graph muy grande (>100K nodos)** con NetworkX | Media | Medio | NetworkX es in-memory pero el Knowledge Graph usa Neo4j (F3) para persistencia. El grafo en memoria es solo para la sesion actual. |
| **GoalManager heuristico muy simple** | Media | Bajo | El GoalManager en F4 es heuristico. Se mejora con LLM en F5. |
| **Tests de integracion lentos** por TreeSitter parsing | Alta | Bajo | Tests unitarios usan parsers mockeados. Solo tests de integracion usan TreeSitter real. |
| **WorldModelAgent sin fuentes externas reales** | Alta | Bajo | F4 implementa WorldModelAgent con deteccion local (docker-compose, package.json). Fuentes externas (GitHub API, CI) se agregan en F6. |

---

*Plan de ejecucion F4 basado en `docs/179_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md` y `docs/180_PROP_DEV_CODE_ASSISTANT_AGENTIC_PLATFORM_1_0_DRAFT.md`. Fecha: 2026-06-20.*
