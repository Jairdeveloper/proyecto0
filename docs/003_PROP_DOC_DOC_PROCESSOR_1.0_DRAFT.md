---
id: 003
area: doc
type: PROP
module: doc-processor
version: 1.0
status: DRAFT
tags:
  - proposal
  - document-processor
  - masterindex
  - spellcheck
  - compiler-compiler
summary: "Propuesta de implementacion para un procesador-compilador de documentos que compila instrucciones .md en documentacion estructurada. Inicia con la creacion de masterindex.sh y spellcheck.sh como herramientas base del ecosistema de documentacion de desarrollo."
keywords:
  - document-processor
  - compiler-compiler
  - masterindex
  - spellcheck
  - proposal
  - architecture
  - tasks
  - phases
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion inicial de la propuesta de implementacion
---

# Compilador-Compilador de Documentos

## 1. Ingenieria Inversa: Analisis de herramientas existentes

### 1.1 masterindex.sh (indexador de documentos legacy)

**Que hace:** Genera un indice formateado a partir de entradas de indice estructuradas
provenientes de documentos troff.

**Pipeline de procesamiento:**
```
[Archivos fuente] → input.idx → sort → pagenums.idx → combine.idx → format.idx → [Indice final]
```

**Patrones de arquitectura extraidos:**
- **Pipeline modular**: cada etapa es un programa independiente (`input.idx`, `pagenums.idx`, `combine.idx`, `format.idx`). Se pueden reemplazar o extender individualmente.
- **Estado como archivo**: usa archivos temporales (`/tmp/index$$`) como paso entre fases.
- **Multi-volumen**: soporta compilacion de indices de multiples volumenes, usando numeros romanos como prefijo.
- **Flags de modo**: `-m` (master/ multi-volumen), `-p` (page/ prueba), `-s` (screen/ sin troff).
- **Soporte de 3 niveles**: entrada primaria, secundaria y terciaria, con delimitadores `:`, `;` y `~`.
- **Rotacion automatica**: el delimitador `~` genera dos entradas (rotacion primaria↔secundaria).

**Para adaptar a @tienda/api:**
- En vez de troff, leer archivos `.md` con frontmatter YAML.
- Cada archivo `.md` es un "volumen" de documentacion.
- Generar indice maestro de documentacion (archivos, secciones, tags, estado).
- Pipeline: `scan_md → parse_frontmatter → sort → generate_index`.

### 1.2 spellcheck.sh (corrector ortografico interactivo legacy)

**Que hace:** Corrector ortografico interactivo escrito en awk. Ejecuta `spell`, muestra cada
palabra mal escrita y permite: cambiar cada ocurrencia, cambio global, anadir al diccionario,
ayuda o salir.

**Arquitectura del programa:**
```
BEGIN → Main loop (por palabra) → END
         ├── Change each occurrence (make_change recursivo)
         ├── Global change (make_global_change)
         ├── Add to dict (dict[])
         ├── Help (muestra respuestas)
         └── Quit (exit → END)
```

**Patrones de extraidos:**
- **Archivos temporales**: `sp_wordlist`, `sp_input`, `sp_out` — nunca trabaja sobre el original hasta confirmacion.
- **Confirmacion en dos pasos**: primero muestra cambios, luego pregunta "Save changes? (y/n)".
- **Backup automatico**: copia `.orig` antes de sobrescribir.
- **Loop de interaccion**: `while` con regex flexible para validar input del usuario.
- **Funcion recursiva**: `make_change()` se llama a si misma para multiples ocurrencias en una linea.
- **Gestion de diccionario**: anade palabras, ordena con `sort`, mantiene archivo plano.

**Para adaptar a @tienda/api:**
- Usar `aspell` o `hunspell` en vez de `spell` (obsoleto).
- Operar solo sobre archivos `.md`.
- Integrar con el flujo de aprobacion del state machine.
- Usar directorio `docs/` como raiz de documentacion.

---

## 2. Arquitectura Final del Procesador-Compilador

### 2.1 Concepto General

El "compilador-compilador de documentos" es un meta-sistema que:

1. **Lee** instrucciones en formato `.md` (especificaciones, prompts, documentacion tecnica)
2. **Compila** esas instrucciones en artefactos de documentacion estructurada
3. **Genera** indices maestros, tablas de contenido, validacion ortografica y reportes de estado

```
                          ┌─────────────────────┐
  [Instrucciones .md] ──▶│  Doc Compiler        │──▶ [Documentacion compilada]
                          │                      │──▶ [Indice maestro (masterindex)]
                          │  (compiler-compiler) │──▶ [Reporte de errores (spellcheck)]
                          └─────────────────────┘
```

### 2.2 Componentes del Sistema

```
docs/
├── masterindex.sh       # Genera indice maestro de documentacion
├── spellcheck.sh        # Corrector ortografico para archivos .md
├── doc_compiler.sh      # Orquestador: pipeline completo
├── lib/
│   ├── scan_md.sh       # Escanea archivos .md en busca de frontmatter
│   ├── parse_yaml.sh    # Extrae campos de frontmatter YAML
│   ├── generate_index.sh# Genera indice formateado
│   └── dict_manager.sh  # Gestion de diccionarios locales
└── templates/
    ├── index_template   # Plantilla de salida para el indice
    └── report_template  # Plantilla de reporte de spellcheck
```

### 2.3 Flujo de Compilacion

```
Fase 1: SCAN
  masterindex.sh --scan docs/  →  lista todos los .md con frontmatter

Fase 2: PARSE
  masterindex.sh --parse       →  extrae id, area, type, module, status, tags

Fase 3: SORT & INDEX
  masterindex.sh --index       →  genera indice maestro (por area, modulo, estado)

Fase 4: VALIDATE
  spellcheck.sh docs/          →  revisa ortografia en todos los .md

Fase 5: REPORT
  doc_compiler.sh --report     →  genera reporte consolidado
```

### 2.4 masterindex.sh (nueva implementacion)

```
Propósito: Escanear todos los archivos .md en docs/ y generar un
           indice maestro navegable de la documentacion del proyecto.

Uso:  ./masterindex.sh [--scan|--parse|--index|--help]
      ./masterindex.sh --scan [directorio]
      ./masterindex.sh --parse <file.md>
      ./masterindex.sh --index [--format {table,markdown,json}]

Salida: STDOUT (o archivo con --output)

Pipeline:
  scan_md.sh → parse_yaml.sh → sort → generate_index.sh

Formato de salida (markdown por defecto):

  # Indice Maestro de Documentacion
  ## Area: DEV
  | ID | Archivo | Modulo | Estado | Tags |
  |----|---------|--------|--------|------|
  ...
  ## Area: DOC
  | ID | Archivo | Modulo | Estado | Tags |
  ...
```

### 2.5 spellcheck.sh (nueva implementacion)

```
Propósito: Revisar ortografia en archivos .md usando aspell/hunspell,
           con modo interactivo y modo batch.

Uso:  ./spellcheck.sh [--check|--list|--add|--help] <file.md>
      ./spellcheck.sh --check <file.md>           # modo interactivo
      ./spellcheck.sh --list <file.md>             # solo lista errores
      ./spellcheck.sh --add <palabra>              # anade a diccionario local

Diccionario local: docs/.dict
Modo batch:        --list (sin interaccion, util para CI)

Salida:
  --list: lista de palabras mal escritas (una por linea)
  --check: interaccion por terminal (hereda de spellcheck.awk legacy)
```

---

## 3. Implementacion Esperada

### 3.1 masterindex.sh

```
#! /bin/sh
# ============================================================================
# masterindex.sh - Genera indice maestro de documentacion .md
# ============================================================================
#
# USO: ./masterindex.sh <comando> [opciones]
#
# COMANDOS:
#   scan    Escanea directorio buscando archivos .md con frontmatter
#   index   Genera indice maestro a partir del scan
#   help    Muestra esta ayuda
#
# OPCIONES:
#   --dir PATH    Directorio a escanear (defecto: ./docs)
#   --out FILE    Archivo de salida (defecto: STDOUT)
#   --format FMT  Formato de salida: table, markdown, json
# ============================================================================

PROJECT_ROOT="$(dirname "$(realpath "$0")")"
DOCS_DIR="${DOCS_DIR:-$PROJECT_ROOT/docs}"
INDEX_FILE=""

# Funciones (snake_case)
scan_directory() { ... }
parse_frontmatter() { ... }
generate_index() { ... }
format_as_table() { ... }
format_as_markdown() { ... }
format_as_json() { ... }

main() { ... }
main "$@"
```

### 3.2 spellcheck.sh

```
#! /bin/sh
# ============================================================================
# spellcheck.sh - Corrector ortografico para documentacion .md
# ============================================================================
#
# USO: ./spellcheck.sh <comando> <archivo> [opciones]
#
# COMANDOS:
#   check   Modo interactivo (hereda de spellcheck.awk legacy)
#   list    Modo batch: lista errores sin interaccion
#   add     Anade palabra al diccionario local
#   help    Muestra esta ayuda
#
# OPCIONES:
#   --dict FILE   Diccionario personalizado
#   --lang LANG   Idioma (defecto: en)
# ============================================================================

PROJECT_ROOT="$(dirname "$(realpath "$0")")"
DICT_FILE="$PROJECT_ROOT/docs/.dict"
SPELL_CMD="aspell"

# Funciones (snake_case)
check_spelling() { ... }
list_errors() { ... }
add_to_dict() { ... }
interactive_loop() { ... }    # hereda de spellcheck.awk legacy
confirm_changes() { ... }     # patron de confirmacion heredado
```

---

## 4. Tabla de Tareas (Formato)

Cada tarea sigue esta estructura:

```
| ID | Tarea | Modulo | Depende de | Esfuerzo | Estado |
|----|-------|--------|------------|----------|--------|
```

Campos:
- **ID**: `TASK-NNN` (numeracion secuencial)
- **Tarea**: Descripcion breve (verbo al inicio)
- **Modulo**: `masterindex` | `spellcheck` | `doc-compiler` | `docs`
- **Depende de**: ID de tarea(s) previas requeridas, o `--`
- **Esfuerzo**: `S` (small, < 2h) | `M` (medium, 2-4h) | `L` (large, 4-8h) | `XL` (extra-large, > 8h)
- **Estado**: `pending` | `in_progress` | `completed` | `blocked`

### Lista de Tareas

| ID | Tarea | Modulo | Depende de | Esfuerzo | Estado |
|----|-------|--------|------------|----------|--------|
| TASK-001 | Crear esqueleto de masterindex.sh | masterindex | -- | M | pending |
| TASK-002 | Implementar `scan_directory()` en masterindex.sh | masterindex | TASK-001 | M | pending |
| TASK-003 | Implementar `parse_frontmatter()` en masterindex.sh | masterindex | TASK-001 | L | pending |
| TASK-004 | Implementar `generate_index()` en masterindex.sh | masterindex | TASK-002, TASK-003 | M | pending |
| TASK-005 | Implementar formatos de salida (table, markdown, json) | masterindex | TASK-004 | M | pending |
| TASK-006 | Anadir manejo de errores y validacion a masterindex.sh | masterindex | TASK-005 | S | pending |
| TASK-007 | Crear esqueleto de spellcheck.sh | spellcheck | -- | M | pending |
| TASK-008 | Implementar `check_spelling()` con aspell/hunspell | spellcheck | TASK-007 | M | pending |
| TASK-009 | Implementar `list_errors()` modo batch | spellcheck | TASK-007 | S | pending |
| TASK-010 | Implementar `interactive_loop()` (hereda de legacy) | spellcheck | TASK-008 | L | pending |
| TASK-011 | Implementar `add_to_dict()` y diccionario local | spellcheck | TASK-007 | S | pending |
| TASK-012 | Implementar `confirm_changes()` con backup (.orig) | spellcheck | TASK-010 | S | pending |
| TASK-013 | Validar con `bash -n` y `shellcheck` todos los scripts | ambos | TASK-006, TASK-011 | S | pending |
| TASK-014 | Crear archivo de documentacion de masterindex.sh | docs | TASK-006 | M | pending |
| TASK-015 | Crear archivo de documentacion de spellcheck.sh | docs | TASK-011 | M | pending |

---

## 5. Tabla de Fases (Formato)

Cada fase sigue esta estructura:

```
| Fase | Nombre | Descripcion | Tareas | Depende de | Duracion est. |
|------|--------|-------------|--------|------------|---------------|
```

### Fases del Proyecto

| Fase | Nombre | Descripcion | Tareas | Depende de | Duracion est. |
|------|--------|-------------|--------|------------|---------------|
| FASE-1 | Fundacion masterindex | Crear esqueleto, scan, parse y generacion de indice | TASK-001 al TASK-006 | -- | 3-4 dias |
| FASE-2 | Fundacion spellcheck | Crear esqueleto, check batch, interactivo y diccionario | TASK-007 al TASK-012 | -- | 3-4 dias |
| FASE-3 | Validacion y hardening | shellcheck, bash -n, manejo de errores, edge cases | TASK-013 | FASE-1, FASE-2 | 1 dia |
| FASE-4 | Documentacion | Guias de uso para masterindex.sh y spellcheck.sh | TASK-014, TASK-015 | FASE-3 | 1-2 dias |
| FASE-5 | Integracion | Orquestador doc_compiler.sh + pipeline completo | (futuro) | FASE-4 | 2-3 dias |

### Desglose de Fase-1 (ejemplo completo)

| Fase | Tarea | Descripcion | Output | Criterio de aceptacion |
|------|-------|-------------|--------|------------------------|
| FASE-1 | TASK-001 | Crear esqueleto de masterindex.sh con header, constantes, funciones vacias y dispatch | `masterindex.sh` | `bash -n masterindex.sh` exitoso; `./masterindex.sh help` muestra uso |
| FASE-1 | TASK-002 | Implementar `scan_directory()` que lista archivos .md con frontmatter | Funcion scan_directory | Escanea `docs/` y devuelve lista de archivos con YAML |
| FASE-1 | TASK-003 | Implementar `parse_frontmatter()` que extrae id, area, type, module, status, tags | Funcion parse_frontmatter | Lee YAML de archivo .md y devuelve campos estructurados |
| FASE-1 | TASK-004 | Implementar `generate_index()` que combina scan + parse y produce indice | Funcion generate_index | Indice con todos los archivos de documentacion |
| FASE-1 | TASK-005 | Implementar formatos table, markdown y json | 3 funciones de formato | Cada formato produce salida correcta y parseable |
| FASE-1 | TASK-006 | Anadir validacion de errores, archivos sin frontmatter, directorios vacios | Validaciones en todas las funciones | Errores con mensaje descriptivo, codigo de salida no-zero |

---

## 6. Convenciones de Implementacion

### 6.1 Estilo Shell

Apegarse estrictamente a `000_DEV_GUIDE_SHELL_STYLE_1_0_DRAFT.md`:
- No `set -e`, no `eval`
- Doble comillas en todas las variables
- 4 espacios de indentacion, max 100 caracteres
- Funciones `snake_case` con `()`
- Constantes `SCREAMING_SNAKE_CASE`
- Logging estructurado con `log()` y `output()`
- Lock files con PID para evitar ejecucion concurrente

### 6.2 Validacion Obligatoria

Cada script debe pasar antes de darse por terminado:
```
bash -n script.sh
shellcheck script.sh
```

### 6.3 Pruebas

- Probar `masterindex.sh --scan docs/` en el directorio actual (debe encontrar los .md existentes)
- Probar `masterindex.sh --index --format json` (salida debe ser JSON valido)
- Probar `spellcheck.sh --list docs/` (debe listar errores sin modificar archivos)
- Probar `spellcheck.sh --add palabra` (debe anadir al diccionario local)
