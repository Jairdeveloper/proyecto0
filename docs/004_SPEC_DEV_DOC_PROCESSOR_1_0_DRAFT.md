---
id: 004
area: dev
type: SPEC
module: doc-processor
version: 1.0
status: DRAFT
tags:
  - specification
  - doc-processor
  - compiler-compiler
  - masterindex
  - spellcheck
  - shell
summary: "Especificacion completa del Sistema Compilador-Compilador de Documentacion para @Procesador de texto. Define alcance, arquitectura, componentes, requerimientos, stack, fases y metricas del proyecto."
keywords:
  - compilador-compilador
  - document-processor
  - masterindex
  - spellcheck
  - especificacion
  - arquitectura
  - requerimientos
  - shell
  - markdown
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion inicial de la especificacion del proyecto
---

# Sistema Compilador-Compilador de Documentacion — @PProcesador de texto

## 1. Informacion General

### 1.1 Nombre del Proyecto

**Compilador-Compilador de Documentacion (Doc Processor)**

### 1.2 Descripcion General

Sistema que compila instrucciones en formato `.md` en documentacion estructurada,
indexada y validada. Funciona como un "compilador-compilador": toma especificaciones
en markdown y produce artefactos de documentacion mediante herramientas modulares shell.

**Problema que resuelve**: La documentacion de desarrollo tiende a dispersarse, desactualizarse
y carecer de estructura consistente. Este sistema automatiza la generacion de indices maestros,
la validacion ortografica y el rastreo de estado de la documentacion.

**Publico objetivo**: Desarrolladores del ecosistema @Procesador de texto que crean y mantienen
documentacion tecnica en formato markdown.

**Diferenciadores**:
- Pipeline modular: cada fase es un script independiente y reemplazable
- Orientado a RAG: estructura pensada para recuperacion por agentes IA
- Convencion de nombres y frontmatter estricta y automatizable
- Tooling shell ligero, sin dependencias externas pesadas

**Alcance general**: Herramientas de linea de comandos para escanear, parsear, indexar
y validar archivos `.md` en el directorio `docs/`. No incluye UI web ni servicio backend.

### 1.3 Objetivos

| Tipo | Objetivo | Prioridad |
|------|----------|-----------|
| Negocio | Reducir el esfuerzo manual de mantener documentacion | Alta |
| Negocio | Unificar criterios de documentacion en todo el equipo | Alta |
| Tecnico | Generar indice maestro automatico de toda la documentacion | Alta |
| Tecnico | Validar ortografia en documentacion .md | Media |
| Tecnico | Proveer pipeline extensible para futuras herramientas doc | Media |

---

## 2. Vision del Producto

### 2.1 Publico Objetivo

| Segmento | Necesidad |
|----------|-----------|
| Desarrollador backend | Documentar APIs, modulos, esquemas de BD |
| Desarrollador frontend | Documentar componentes, flujos UI |
| Technical writer | Mantener documentacion coherente y actualizada |
| Agente IA (OpenCode) | Leer y procesar documentacion estructurada para RAG |

### 2.2 Casos de Uso

1. **Escaneo**: `./masterindex.sh --scan docs/` — lista todos los .md con frontmatter valido
2. **Indexado**: `./masterindex.sh --index --format table` — genera tabla de documentacion
3. **Validacion**: `./spellcheck.sh --list docs/*.md` — lista errores ortograficos en batch
4. **Correccion**: `./spellcheck.sh --check docs/001_GUIDE_DOC_MASTERINDEX_1_0_DRAFT.md` — interactivo

---

## 3. Requerimientos

### 3.1 Funcionales

| ID | Requerimiento | Modulo | Prioridad |
|----|---------------|--------|-----------|
| RF-01 | Escanear directorio buscando archivos .md con frontmatter YAML | masterindex | Alta |
| RF-02 | Extraer campos id, area, type, module, version, status, tags del frontmatter | masterindex | Alta |
| RF-03 | Generar indice maestro en formatos table, markdown y json | masterindex | Alta |
| RF-04 | Detectar archivos .md sin frontmatter o con frontmatter invalido | masterindex | Media |
| RF-05 | Ejecutar aspell/hunspell sobre archivos .md y listar errores | spellcheck | Alta |
| RF-06 | Modo interactivo: mostrar palabra erronea, ofrecer C/G/A/H/Q | spellcheck | Media |
| RF-07 | Anadir palabra a diccionario local (`docs/.dict`) | spellcheck | Media |
| RF-08 | Modo batch: solo listar errores sin interaccion (para CI) | spellcheck | Alta |
| RF-09 | Generar backup .orig antes de sobrescribir archivos | spellcheck | Alta |
| RF-10 | Confirmar cambios antes de guardar (patron heredado de legacy) | spellcheck | Alta |
| RF-11 | Pipeline completo: scan → index → validate → report | doc-compiler | Baja |

### 3.2 No Funcionales

| ID | Requerimiento | Detalle |
|----|---------------|---------|
| RNF-01 | Portabilidad | Scripts puramente POSIX shell, sin bashismos |
| RNF-02 | Seguridad | No usar `eval`. No `set -e`. Errores explicitos |
| RNF-03 | Rendimiento | Indice de 100+ archivos en < 1s |
| RNF-04 | Mantenibilidad | Funciones modulares < 50 lineas cada una |
| RNF-05 | Validacion | Pasar `bash -n` y `shellcheck` sin warnings |
| RNF-06 | Auditoria | Logs estructurados con timestamp ISO |

---

## 4. Analisis del Sistema

### 4.1 Problema Actual

- Documentacion sin indice central — dificil saber que existe
- Sin validacion ortografica automatica — errores en docs publicos
- Sin convencion de nombres unificada — archivos con criterios diferentes
- Sin integracion con agentes IA — documentacion no es facilmente procesable

### 4.2 Solucion Propuesta

| Problema | Solucion |
|----------|----------|
| Sin indice central | `masterindex.sh --scan --index` genera indice maestro automatico |
| Sin validacion ortografica | `spellcheck.sh --list --check` revisa y corrige |
| Convencion inconsistente | Frontmatter YAML obligatorio + naming estandar |
| No RAG-friendly | Frontmatter estructurado, tags controlados, summary para embeddings |

### 4.3 Factibilidad

- Shell POSIX disponible en cualquier entorno Unix/Linux
- `aspell`/`hunspell` disponibles en los gestores de paquetes principales
- Scripts heredados (`masterindex.sh`, `spellscheck.sh`) demuestran patrones validos
- Estilo shell ya definido en `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`

---

## 5. Arquitectura del Sistema

### 5.1 Arquitectura General

```
                          ┌──────────────────┐
  [docs/*.md] ───────────▶│  masterindex.sh  │──▶ Indice maestro
                          │  --scan --index   │    (table/markdown/json)
                          └──────────────────┘

                          ┌──────────────────┐
  [docs/*.md] ───────────▶│  spellcheck.sh   │──▶ Lista errores / Archivos corregidos
                          │  --list --check   │    + backup .orig
                          └──────────────────┘

                          ┌──────────────────┐
  [masterindex + spell]──▶│  doc_compiler.sh  │──▶ Reporte consolidado
                          │  (orquestador)    │
                          └──────────────────┘
```

### 5.2 Componentes

```
docs/
├── masterindex.sh       # Genera indice maestro de documentacion
├── spellcheck.sh        # Corrector ortografico para archivos .md
├── doc_compiler.sh      # Orquestador: pipeline completo (futuro)
├── lib/
│   ├── scan_md.sh       # Escanea archivos .md en busca de frontmatter
│   ├── parse_yaml.sh    # Extrae campos de frontmatter YAML
│   ├── generate_index.sh# Genera indice formateado
│   └── dict_manager.sh  # Gestion de diccionarios locales
├── templates/
│   ├── index_template   # Plantilla de salida para indice
│   └── report_template  # Plantilla de reporte de spellcheck
└── .dict                # Diccionario local de palabras permitidas
```

### 5.3 Diseno de masterindex.sh

```
$ ./masterindex.sh --help
USO: ./masterindex.sh <comando> [opciones]

COMANDOS:
  scan    Escanea directorio buscando archivos .md con frontmatter
  index   Genera indice maestro a partir del scan
  help    Muestra esta ayuda

OPCIONES:
  --dir PATH    Directorio a escanear (defecto: ./docs)
  --out FILE    Archivo de salida (defecto: STDOUT)
  --format FMT  Formato: table, markdown, json (defecto: markdown)

FLUJO INTERNO:
  scan_directory() → lista archivos .md
  parse_frontmatter() → extrae id, area, type, module, status, tags
  generate_index() → combina y ordena
  format_as_table() | format_as_markdown() | format_as_json() → produce salida
```

### 5.4 Diseno de spellcheck.sh

```
$ ./spellcheck.sh --help
USO: ./spellcheck.sh <comando> <archivo> [opciones]

COMANDOS:
  check   Modo interactivo (hereda de spellcheck.awk legacy)
  list    Modo batch: lista errores sin interaccion
  add     Anade palabra al diccionario local
  help    Muestra esta ayuda

OPCIONES:
  --dict FILE   Diccionario personalizado (defecto: docs/.dict)
  --lang LANG   Idioma (defecto: en)

FLUJO INTERNO:
  Verificar dependencia (aspell/hunspell)
  Si --list: ejecuta aspell --list, muestra errores en stdout
  Si --check: por cada error, loop interactivo C/G/A/H/Q
  Si --add: anade palabra a .dict
  Backup .orig antes de escribir
  Confirmacion en 2 pasos (hereda de legacy)
```

---

## 6. Stack Tecnologico

| Tecnologia | Uso | Version min |
|------------|-----|-------------|
| Shell POSIX (`/bin/sh`) | Scripts principales | Cualquier Unix |
| awk | Procesamiento de texto | nawk/gawk |
| aspell | Corrector ortografico (modo batch) | 0.60+ |
| hunspell | Corrector ortografico (alternativa) | 1.7+ |
| Markdown (GFM) | Formato de documentacion | — |
| YAML | Frontmatter de metadatos | — |
| `bash -n` | Validacion de sintaxis shell | Bash 3+ |
| shellcheck | Analisis estatico shell (lint) | 0.7+ |

---

## 7. Modelado de Procesos

### 7.1 Flujo de masterindex.sh

```
[Inicio] → [Validar argumentos]
         → [--scan]:   escanear directorio → listar .md → parsear frontmatter
         → [--index]:  leer scan previo → ordenar → formatear → imprimir
         → [--help]:   mostrar uso
         → [error]:    mostrar error + uso, exit 1
```

### 7.2 Flujo de spellcheck.sh --check

```
[Inicio] → [Validar argumentos y dependencias]
         → [Crear archivos temporales (sp_*)]
         → [Ejecutar aspell/hunspell → wordlist]
         → [Si wordlist vacia: "No errors found", limpiar y salir]
         → [Loop por cada palabra erronea]:
             → Mostrar palabra y numero
             → [C]hange: llamar a make_change() recursivo
             → [G]lobal: llamar a make_global_change()
             → [A]dd: agregar a dict[]
             → [H]elp: mostrar respuestas
             → [Q]uit: salir al END
             → [CR]: ignorar, siguiente palabra
         → [END]: confirmar guardado, backup .orig, limpiar temporales
```

### 7.3 Flujo de spellcheck.sh --list

```
[Inicio] → [Ejecutar: aspell --list < archivo.md]
         → [Mostrar lista de errores en stdout]
         → [exit 0 si sin errores, exit 1 si hay errores]
         → [Util para CI: si hay errores, pipeline falla]
```

---

## 8. Entregables y Prototipos

### 8.1 Entregables

| Fase | Entregable | Descripcion |
|------|------------|-------------|
| FASE-1 | masterindex.sh v1 | Script funcional con scan + index + formatos |
| FASE-2 | spellcheck.sh v1 | Script funcional con list + check + add |
| FASE-3 | Validacion | `shellcheck` limpio, edge cases cubiertos |
| FASE-4 | Documentacion | Guias de uso para ambos scripts |
| FASE-5 | doc_compiler.sh | Orquestador del pipeline completo |

---

## 9. API y Comunicacion

Los scripts se comunican exclusivamente mediante:

- **Argumentos CLI**: `./masterindex.sh --scan --dir docs/`
- **STDOUT**: salida principal del indice / lista de errores
- **STDERR**: logs y mensajes de error
- **Exit codes**: 0 = exito, 1 = error
- **Archivos temporales**: `/tmp/scriptname_$$.tmp` (con limpieza via trap)
- **Lock files**: para evitar ejecucion concurrente

No hay API REST, GraphQL ni WebSockets. El sistema es puramente tooling CLI.

---

## 10. DevOps y Despliegue

### 10.1 Infraestructura

| Ambiente | Proposito |
|----------|-----------|
| Desarrollo | `docs/` en el repo local, scripts ejecutables directamente |
| CI (futuro) | Ejecutar `spellcheck.sh --list` en cada PR |
| Produccion | Ninguna (no es un servicio, son herramientas de desarrollo) |

### 10.2 Pipeline CI Propuesto (futuro)

```
[Push a master] → [Ejecutar spellcheck.sh --list en docs/]
                → [Si errores: fallar CI, listar palabras en output]
                → [Ejecutar bash -n en todos los .sh]
                → [Ejecutar shellcheck en todos los .sh]
                → [Si todo OK: CI pasa]
```

---

## 11. Gestion del Proyecto

### 11.1 Metodologia

Kanban simple con tareas en `docs/004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md`.
Cada tarea tiene estado: `pending → in_progress → completed`.

### 11.2 Roles

| Rol | Responsabilidades |
|-----|------------------|
| Workflow agent | Implementar scripts, validar, documentar |

### 11.3 Roadmap

| Fase | Duracion est. | Tareas | Dependencias |
|------|---------------|--------|-------------|
| FASE-1: masterindex | 3-4 dias | TASK-001 al TASK-006 | — |
| FASE-2: spellcheck | 3-4 dias | TASK-007 al TASK-012 | — |
| FASE-3: Validacion | 1 dia | TASK-013 | FASE-1, FASE-2 |
| FASE-4: Documentacion | 1-2 dias | TASK-014, TASK-015 | FASE-3 |
| FASE-5: Orquestador | 2-3 dias | doc_compiler.sh | FASE-4 |

---

## 12. Gestion de Riesgos

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| `aspell` no instalado | Medio | Baja | Detectar en runtime, fallar con mensaje claro |
| Archivos .md sin frontmatter | Bajo | Media | Reportar como warning, continuar |
| Scripts muy largos o complejos | Medio | Baja | Mantener funciones < 50 lineas cada una |
| Lock file stale por crash | Bajo | Baja | Verificar PID activo antes de bloquear |

---

## 13. Metricas y KPIs

| KPI | Descripcion | Target |
|-----|-------------|--------|
| Cobertura de scan | % de archivos .md detectados sobre total real | 100% |
| Tiempo de indexado | Tiempo para indexar 100 archivos | < 1s |
| Falsos positivos spellcheck | Palabras correctas marcadas como error | < 5% |
| Errores de lint shell | Warnings de shellcheck | 0 |
| Archivos documentados | % de scripts con pagina de ayuda completa | 100% |

---

## 14. Convenciones

### 14.1 Nomenclatura de archivos

`[NNN]_[TIPOSEMANTICO]_[AREASEMANTICA]_[MODULO]_[VERSION]_[ESTADO].md`

**Ejemplos**:
| Archivo | Descripcion |
|---------|-------------|
| `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` | Guia de estilo shell |
| `001_GUIDE_DOC_MASTERINDEX_1_0_DRAFT.md` | Guia de masterindex legacy |
| `002_GUIDE_DOC_SPELLCHECK_1_0_DRAFT.md` | Guia de spellcheck legacy |
| `003_PROP_DOC_DOC_PROCESSOR_1_0_DRAFT.md` | Propuesta de implementacion |
| `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` | Esta especificacion |

### 14.2 Frontmatter YAML

Campos obligatorios: `id, area, type, module, version, status, tags, summary, keywords, changelog`.

### 14.3 Tags controlados

Ver seccion 3 de `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md`.

---

## 15. Tabla de Tareas

| ID | Tarea | Modulo | Depende de | Esfuerzo | Estado |
|----|-------|--------|------------|----------|--------|
| TASK-001 | Crear esqueleto de masterindex.sh | masterindex | — | M | pending |
| TASK-002 | Implementar `scan_directory()` | masterindex | TASK-001 | M | pending |
| TASK-003 | Implementar `parse_frontmatter()` | masterindex | TASK-001 | L | pending |
| TASK-004 | Implementar `generate_index()` | masterindex | TASK-002, TASK-003 | M | pending |
| TASK-005 | Implementar formatos de salida (table, md, json) | masterindex | TASK-004 | M | pending |
| TASK-006 | Validacion de errores y edge cases en masterindex | masterindex | TASK-005 | S | pending |
| TASK-007 | Crear esqueleto de spellcheck.sh | spellcheck | — | M | pending |
| TASK-008 | Implementar dependencia aspell/hunspell + `list_errors()` | spellcheck | TASK-007 | M | pending |
| TASK-009 | Implementar `interactive_loop()` con C/G/A/H/Q | spellcheck | TASK-008 | L | pending |
| TASK-010 | Implementar `add_to_dict()` y diccionario local | spellcheck | TASK-007 | S | pending |
| TASK-011 | Implementar `confirm_changes()` con backup .orig | spellcheck | TASK-009 | S | pending |
| TASK-012 | Validar con `bash -n` y `shellcheck` todos los scripts | ambos | TASK-006, TASK-011 | S | pending |
| TASK-013 | Renombrar archivos existentes a nueva convencion de nombres | docs | — | S | pending |
| TASK-014 | Actualizar AGENTS.md con estado actual del proyecto | docs | TASK-013 | S | pending |

---

## 16. Referencias

- `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
- `001_GUIDE_DOC_MASTERINDEX_1_0_DRAFT.md` — Documentacion de masterindex legacy
- `002_GUIDE_DOC_SPELLCHECK_1_0_DRAFT.md` — Documentacion de spellcheck legacy
- `003_PROP_DOC_DOC_PROCESSOR_1_0_DRAFT.md` — Propuesta de implementacion
- `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` — Convencion de documentacion
- `AGENTS.md` — Instrucciones para sesiones OpenCode
- `prompts/build.md` — Template de especificacion original
