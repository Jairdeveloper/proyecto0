---
id: 002
area: dev
type: GUIDE
module: spellcheck
version: 1.0
status: ACTIVE
tags:
  - spellcheck
  - aspell
  - documentation
  - guide
  - adaptation
  - legacy
summary: "Guia del corrector ortografico interactivo para documentacion en docs/. Adaptacion del clasico spellcheck.awk de Dale Dougherty (O'Reilly, 1990) usando aspell como motor moderno."
keywords:
  - spellcheck
  - aspell
  - spelling
  - interactive
  - documentation
  - o-reilly
  - dougherty
  - legacy
  - adaptation
changelog:
  - version: 1.0
    date: 2026-06-23
    description: Creacion inicial. Documentacion de la adaptacion del spellcheck.awk clasico a scripts/spellcheck_docs.sh con aspell
---

# Corrector Ortografico Interactivo para Documentacion

## 1. Proposito

El corrector ortografico interactivo permite revisar y corregir errores
ortograficos en archivos de documentacion markdown (`docs/`). Es la
adaptacion moderna del clasico `spellcheck.awk` de Dale Dougherty
(O'Reilly, "UNIX Text Processing", 1990).

A diferencia de un corrector batch (como `codespell` en CI), este
script preserva el flujo interactivo original: muestra cada palabra
desconocida en contexto, ofrece sugerencias, y permite decidir que
hacer con ella (corregir, ignorar, agregar a diccionario).

## 2. Original: spellcheck.awk (Dale Dougherty, 1990)

### 2.1. Diseno original

El `spellcheck.awk` original era un script awk que:

1. Invocaba el programa UNIX `spell` sobre un archivo de texto
2. Generaba una lista de palabras desconocidas
3. Para cada palabra, presentaba un prompt interactivo con 5 opciones
4. Permitia correccion por ocurrencia (funcion recursiva
   `make_change()`) o cambio global (`make_global_change()`)
5. Usaba archivos temporales con prefijo `sp_` (`sp_wordlist`,
   `sp_input`, `sp_out`)
6. Creaba copias `.orig` antes de modificar
7. Confirmaba con el usuario antes de guardar cambios
8. Soportaba diccionarios locales (`+dict`)

### 2.2. Arquitectura del original

```
spellscheck.sh (shell wrapper)
  └── nawk -f spellcheck.awk [+dict] archivo
        ├── BEGIN: procesar args, ejecutar spell, crear wordlist
        ├── MAIN:  por cada palabra en wordlist → prompt C/G/A/H/Q
        │     ├── make_change()       → recursiva, ocurrencia por ocurrencia
        │     ├── make_global_change() → gsub global, todas a la vez
        │     └── confirm_changes()    → confirmar antes de guardar
        └── END: guardar cambios, limpiar temporales
```

### 2.3. Codigo de referencia

El codigo original completo esta preservado en:
- [`docs/archive/002_GUIDE_DOC_SPELLCHECK_1.0_DRAFT.md`](../archive/002_GUIDE_DOC_SPELLCHECK_1.0_DRAFT.md)
  (documentacion original del libro de O'Reilly, 604 lineas)
- [`spellscheck.sh`](../spellscheck.sh) (script awk original, 333 lineas,
  preservado como referencia pero reescrito como wrapper delegante)

## 3. Adaptacion a Proyecto0

### 3.1. Cambios respecto al original

| Aspecto | Original (1990) | Adaptacion (actual) |
|---------|----------------|---------------------|
| Motor de revision | UNIX `spell` | GNU `aspell` |
| Formato de entrada | Texto plano | Markdown (`.md`) |
| Saltar bloques de codigo | No aplica | Filtro sed elimina ```...``` |
| Idioma | Ingles (`en`) | Espanol (`es`) por defecto |
| Diccionario personal | `+dict` en argumento | `-d <archivo>` |
| Lenguaje de implementacion | awk puro | Shell POSIX (`/bin/sh`) |
| Output de errores | Lista plana | Contexto con numero de linea |
| Ubicacion | `spellscheck.sh` (raiz) | `scripts/spellcheck_docs.sh` |
| Wrapper | `spellscheck.sh` invocaba awk | `spellscheck.sh` delega en el script moderno |

### 3.2. Patrones preservados

Del original se conservan los siguientes patrones de diseno:

1. **make_change() recursivo** — permite al usuario corregir cada
   ocurrencia individualmente, confirmando una por una. Conserva la
   recursion conceptual (aunque implementada con bucle en shell).

2. **make_global_change()** — reemplaza todas las ocurrencias de una
   vez, mostrando las lineas modificadas y solicitando confirmacion
   antes de guardar.

3. **confirm_changes()** — doble confirmacion: por palabra y al final
   del archivo. Ningun cambio se persiste sin aprobacion explicita.

4. **Archivos temporales** — uso de `/tmp/spellcheck_*_$$.tmp` con
   `trap` para limpieza automatica, equivalente al patron `sp_*`
   original.

5. **Copia .orig** — respaldo del archivo original antes de cualquier
   modificacion, como hacia el `spellscheck.sh` clasico.

6. **Diccionario local** — soporte para archivo de palabras
   personalizado, equivalente al `+dict` original.

### 3.3. Nuevas capacidades

Ademas de preservar el flujo clasico, la adaptacion anade:

- **Modo dry-run** (`-n`): lista errores sin modificar archivos
- **Sugerencias contextuales**: muestra las sugerencias de aspell para
  cada palabra desconocida
- **Multi-archivo**: procesa multiples archivos en una sola invocacion
- **Filtro markdown**: omite bloques de codigo y enlaces automaticamente
- **Idioma configurable**: soporta cualquier idioma que tenga diccionario
  aspell instalado

## 4. Herramienta Moderna: scripts/spellcheck_docs.sh

### 4.1. Instalacion de dependencias

```bash
# Debian/Ubuntu
apt-get install aspell aspell-es

# macOS
brew install aspell

# RHEL/Fedora
dnf install aspell aspell-es
```

### 4.2. Uso basico

```bash
# Revisar un archivo
scripts/spellcheck_docs.sh docs/INDEX.md

# Revisar varios archivos
scripts/spellcheck_docs.sh docs/*.md

# Usando el wrapper clasico
spellscheck.sh docs/INDEX.md
```

### 4.3. Opciones

| Opcion | Descripcion |
|--------|-------------|
| `-d <dict>` | Diccionario personalizado (archivo con una palabra por linea) |
| `-l <lang>` | Idioma aspell (default: `es`) |
| `-n` | Modo dry-run: lista errores sin interactuar |
| `-h`, `--help` | Muestra ayuda detallada |

### 4.4. Modo interactivo

Al ejecutar el script, por cada palabra desconocida se muestra:

```
[1/5] Palabra: 'lenguage'
  Sugerencias: lenguaje, lenguaje, lenguajes
  Contexto:
    42: un lenguage de programacion moderno

  lenguage (C/G/A/H/Q/ENTER):
```

Opciones de respuesta:
- **C** — Cambiar cada ocurrencia (prompt por cada una, como el
  `make_change()` original)
- **G** — Cambio global (todas las ocurrencias a la vez, como el
  `make_global_change()` original)
- **A** — Agregar al diccionario personal (como el `+dict` original)
- **H** — Ayuda
- **Q** — Salir
- **ENTER** — Ignorar esta palabra

### 4.5. Modo dry-run

```bash
scripts/spellcheck_docs.sh -n docs/*.md
```

Lista todas las palabras desconocidas con su conteo de ocurrencias y
sugerencias, sin modificar ningun archivo:

```
==================================================
  INDEX.md:
==================================================
  ORM                  (2 ocurrencias) sugerencias: orm
  Scaffolding          (1 ocurrencias) sugerencias: scaffolding
  autogenerados        (1 ocurrencias) sugerencias: autogenerados
  backend              (3 ocurrencias) sugerencias: backend
```

### 4.6. Diccionario personalizado

Para evitar falsos positivos con terminologia tecnica, se puede crear un
archivo de diccionario con palabras propias del proyecto:

```bash
# Crear diccionario del proyecto
cat > docs/.aspell.pws <<'DICT'
personal_ws_v1.1 es 4
NestJS
Prisma
RECPL
LangGraph
DICT

# Usarlo en las revisiones
scripts/spellcheck_docs.sh -d docs/.aspell.pws docs/*.md
```

### 4.7. Arquitectura del script moderno

```
scripts/spellcheck_docs.sh [opciones] [archivo...]
  │
  ├── check_deps()          → verifica que aspell este instalado
  ├── extract_text()        → filtra markdown (elimina bloques de codigo)
  ├── get_misspellings()    → aspell list → palabras unicas
  ├── get_suggestions()     → aspell pipe → sugerencias
  ├── find_occurrences()    → grep -n → contexto con lineas
  │
  └── process_file()        → por cada archivo:
        ├── backup .orig
        ├── para cada palabra:
        │     ├── make_change()        → cambio por ocurrencia
        │     ├── make_global_change() → cambio global
        │     ├── add to dict          → agrega a diccionario
        │     └── ignore/quit          → salta o termina
        └── confirmar guardado
```

## 5. Integracion con pre-commit

Para integrar el spellcheck en el flujo de CI/CD, anadir a
`.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: spellcheck
      name: spellcheck docs
      entry: scripts/spellcheck_docs.sh
      language: script
      files: ^docs/.*\.md$
      args: [-n]
```

El modo `-n` (dry-run) permite que el hook solo liste errores sin
intentar correcciones automaticas.

## 6. Referencias

### Archivos del proyecto

- [`scripts/spellcheck_docs.sh`](../scripts/spellcheck_docs.sh) —
  Script moderno de corrector ortografico (implementacion activa)
- [`spellscheck.sh`](../spellscheck.sh) — Wrapper adaptado que
  preserva la interfaz original y delega en el script moderno
- [`docs/archive/002_GUIDE_DOC_SPELLCHECK_1.0_DRAFT.md`](../archive/002_GUIDE_DOC_SPELLCHECK_1.0_DRAFT.md)
  — Documentacion original de O'Reilly (604 lineas, valor historico)

### Documentacion relacionada

- [`docs/001_GUIDE_DEV_DOC_INDEXER_1_0_ACTIVE.md`](001_GUIDE_DEV_DOC_INDEXER_1_0_ACTIVE.md)
  — Guia del indexador de documentacion (adaptacion paralela del
  masterindex clasico)
- [`docs/archive/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`](../archive/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md)
  — Convenciones de estilo shell usadas en el proyecto

### Fuente original

- Dougherty, Dale. "UNIX Text Processing" (O'Reilly & Associates, 1987).
 Capitulo 12: "Spellcheck, an Interactive Spell Checker".
  Codigo original: `spellcheck.awk`
