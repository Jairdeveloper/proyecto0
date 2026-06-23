---
id: 001
area: dev
type: guide
module: doc-indexer
version: 1.0
status: ACTIVE
tags:
  - indexing
  - documentation
  - frontmatter
  - masterindex
  - legacy
  - adaptation
  - generate-docs-index
summary: "Guia del sistema de indexacion de documentacion de Proyecto0. Adaptacion del clasico masterindex de Dale Dougherty (troff, 1990) al ecosistema de documentacion markdown con frontmatter YAML del proyecto. Describe el patron de filtros modulares, el script generate_docs_index.sh, y como se conecta con la documentacion ISO 12207."
keywords:
  - masterindex
  - indexing
  - documentation-index
  - frontmatter
  - yaml
  - awk
  - modular-filters
  - reference
  - dougherty
  - adaptacion
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Reescritura completa. Migrado de docs/archive/ a docs/. Actualizado de legacy troff a indexador markdown moderno. Documentacion en espanol.
---

# Guia del Sistema de Indexacion de Documentacion

> **Documento original:** `masterindex` por Dale Dougherty (O'Reilly, 1990)
> **Archivo historico:** `docs/archive/001_GUIDE_DOC_MASTERINDEX_1.0_DRAFT.md`
> **Script original:** `masterindex.sh` (raiz del proyecto)
> **Adaptacion moderna:** `scripts/generate_docs_index.sh`

---

## 1. Proposito en Proyecto0

Proyecto0 mantiene aproximadamente **180 documentos** de documentacion en `docs/`,
organizados por area tematica (dev, mgt, doc, ops, etc.) y numerados con un
identificador unico de 3 digitos (`NNN`).

Para navegar esta documentacion de manera eficiente, el proyecto utiliza un
**sistema de indexacion automatico** que escanea los archivos markdown, extrae
su frontmatter YAML, y genera indices estructurados.

Este sistema es la **adaptacion moderna** del clasico `masterindex` de Dale
Dougherty, que originalmente procesaba macros troff (`.XX`, `.XN`, `.XB`) para
generar indices de libros. El patron de filtros modulares se ha preservado;
el formato de entrada ha cambiado de troff a YAML.

---

## 2. Arquitectura del Indexador

### 2.1 Patron de Filtros Modulares (heredado de masterindex)

El `masterindex` original usaba un pipeline de filtros conectados via tuberias
Unix:

```
input.idx → sort → pagenums.idx → combine.idx → format.idx
```

Cada filtro era un programa independiente (`nawk`/`sed`) con una responsabilidad
unica:

| Filtro original | Responsabilidad | Adaptacion en Proyecto0 |
|----------------|----------------|------------------------|
| `input.idx` | Lectura de entradas estructuradas | `extract_fm()` — extrae frontmatter YAML con awk |
| `sort` | Ordenacion alfabetica | `sort -t'|' -k1,1 -k2,2` — ordena por area y NNN |
| `pagenums.idx` | Agrupacion de numeros de pagina | `wc -l + agrupacion por area` — conteo de documentos |
| `combine.idx` | Combinacion de entradas duplicadas | `sort \| uniq` — deduplicacion por NNN |
| `format.idx` | Formateo de salida (troff/screen/page) | Markdown table + links — salida INDEX.md |

### 2.2 Componentes Actuales

```
docs/*.md (frontmatter YAML)
    │
    ▼
scripts/generate_docs_index.sh
    │
    ├── extract_fm()       ← awk: extrae id, area, type, module, summary
    ├── extract_nnn()      ← sed: extrae prefijo numerico del nombre
    ├── write_master_index()  ← genera docs/INDEX.md (indice maestro)
    └── write_partial_views() ← genera docs/<area>/INDEX.md (vistas parciales)
    │
    ▼
docs/INDEX.md (indice maestro)
docs/<area>/INDEX.md (vistas por area)
```

### 2.3 Formato de Entrada (Frontmatter YAML)

Cada documento markdown en `docs/` debe contener frontmatter YAML con la
siguiente estructura:

```yaml
---
id: NNN              # Identificador unico de 3 digitos (o ALGP003)
area: dev            # Area tematica: dev, mgt, doc, ops, legacy
type: rep            # Tipo: plan, prop, rep, guide, spec, analysis
module: pdca-sdlc    # Modulo del proyecto
version: 1.0         # Version del documento
status: DRAFT        # Estado: DRAFT, ACTIVE, IMPLEMENTED
tags:                # Etiquetas para busqueda
  - report
  - development
summary: "Descripcion breve del contenido (max 120 chars)"
keywords:            # Palabras clave para busqueda
  - pdca-sdlc
  - arquitectura
changelog:
  - version: 1.0
    date: 2026-06-22
    author: sisyphus
    description: Descripcion del cambio
---
```

### 2.4 Formato de Salida (INDEX.md)

El indice maestro (`docs/INDEX.md`) se organiza en dos secciones:

1. **Por area tematica** — tabla con NNN, Tipo, Modulo, Resumen
2. **Secuencia completa por NNN** — lista plana de todos los documentos

Las vistas parciales (`docs/<area>/INDEX.md`) muestran solo los documentos
de un area especifica.

---

## 3. Uso

### 3.1 Regenerar el indice completo

```bash
./scripts/generate_docs_index.sh
```

Esto escanea `docs/*.md`, extrae el frontmatter de cada archivo, y genera:

| Archivo | Contenido |
|---------|-----------|
| `docs/INDEX.md` | Indice maestro con todos los documentos |
| `docs/<area>/INDEX.md` | Vista parcial por area (dev/, mgt/, etc.) |

### 3.2 Convencion de Nombrado

Los documentos siguen el formato:

```
[NNN]_[TIPOSEMANTICO]_[AREASEMANTICA]_[MODULO]_[VERSION]_[ESTADO].md
```

Ejemplo: `206_REP_DEV_REVERSE_ENGINEERING_1_0_DRAFT.md`

| Componente | Descripcion |
|-----------|-------------|
| `NNN` | Identificador unico de 3 digitos (001-999) |
| `TIPO` | Tipo semantico: GUIDE, PROP, PLAN, REP, SPEC, ANALYSIS |
| `AREA` | Area semantica: DEV, DOC, MGT, OPS, LEGACY |
| `MODULO` | Modulo del proyecto |
| `VERSION` | Version del documento (1_0, 2_0, etc.) |
| `ESTADO` | Estado: DRAFT, ACTIVE, IMPLEMENTED |

Caso especial: `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` usa prefijo
alfabetico en vez de numerico.

### 3.3 Integracion con el Flujo de Trabajo

Se recomienda regenerar el indice **despues de cada cambio significativo**
en la documentacion:

- Al anadir un nuevo documento
- Al modificar el frontmatter de un documento existente
- Al cambiar el estado de un documento (DRAFT → ACTIVE)
- Antes de cada commit que incluya cambios en `docs/`

No esta integrado en pre-commit hooks ni CI actualmente (ver seccion 6).

---

## 4. El Legado de masterindex

### 4.1 Que era masterindex (original)

Programa de indexacion escrito por Dale Dougherty para O'Reilly & Associates
(~1990). Procesaba archivos troff con macros especiales (`.XX`, `.XN`, `.XB`)
para generar indices formateados en tres modos:

- **troff** (default): salida con macros para formateo tipografico
- **screen** (`-s`): salida ASCII para visualizacion en pantalla
- **page** (`-p`): listado pagina por pagina para correccion

Su innovacion principal era el **pipeline modular**: una serie de pequenos
programas (input.idx, pagenums.idx, combine.idx, format.idx) conectados via
tuberias Unix, cada uno con una responsabilidad unica. Esto permitia aislar
y corregir problemas, y conectar nuevos modulos para implementar nuevas
funcionalidades.

### 4.2 Por que estaba en el proyecto

El archivo `masterindex.sh` y su documentacion se incluyeron en el bootstrap
inicial del proyecto como **codigo de referencia** (ver `AGENTS.md`). Ambos
(`masterindex.sh` y `spellscheck.sh`) son programas clasicos de O'Reilly que
demuestran el estilo de programacion Unix con tuberias y filtros. No forman
parte del pipeline de compilacion NL→IR ni de la orquestacion SDLC.

### 4.3 Que se adapto

| Concepto original | Adaptacion |
|------------------|-----------|
| Macros `.XX`/`.XN`/`.XB` en archivos troff | Frontmatter YAML en archivos markdown |
| Filtros nawk independientes | Funciones awk embebidas en shell script |
| Salida troff con macros `.Se`/`.XC`/`.XF` | Salida markdown con tablas y enlaces |
| Indice multivolumen (`-m`) | Indice multiarea (dev, mgt, doc, ops, etc.) |
| Paginacion (`-p`, `-s`) | Vistas parciales por area |
| `romanum` para numeros de volumen | `extract_nnn()` para identificadores |

### 4.4 Archivo historico

El documento original de Dale Dougherty se conserva en:

```
docs/archive/001_GUIDE_DOC_MASTERINDEX_1.0_DRAFT.md
```

Se mantiene como referencia historica y tributo al diseno de software Unix
de los anos 90. No se modificara.

---

## 5. Referencia Rapida de Funciones

### `extract_fm(file, key)`

Extrae un campo del frontmatter YAML de un archivo markdown.

```bash
extract_fm "docs/206_REP_DEV_REVERSE_ENGINEERING_1_0_DRAFT.md" "area"
# → dev
```

**Implementacion:** awk con estados (1=dentro de frontmatter, 2=fuera).
Busca `key:` y retorna el valor limpiando comillas.

### `extract_nnn(name)`

Extrae el prefijo numerico del nombre del archivo.

```bash
extract_nnn "206_REP_DEV_REVERSE_ENGINEERING_1_0_DRAFT.md"
# → 206
extract_nnn "ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md"
# → ALGP003
```

### `write_master_index()`

Genera `docs/INDEX.md` con:

1. Contador total de documentos
2. Tabla por area tematica
3. Secuencia completa por NNN

### `write_partial_views(tmpfile)`

Para cada area unica, genera `docs/<area>/INDEX.md` con los documentos
de esa area.

---

## 6. Limitaciones y Mejoras Potenciales

| Limitacion | Descripcion | Mejora propuesta |
|-----------|-------------|-----------------|
| Sin integracion CI | El indice no se regenera automaticamente en CI | Anadir paso en `.github/workflows/ci.yml` |
| Sin validacion de frontmatter | No detecta campos faltantes o mal formateados | Anadir validador YAML antes de generar indice |
| Sin busqueda por tags | Las tags existen en frontmatter pero no se indexan | Anadir seccion de indices por tag |
| Sin ordenacion por estado | No hay vista de documentos por estado (DRAFT/ACTIVE) | Anadir filtro por estado en vistas parciales |
| Sin deteccion de roturas | No verifica que los enlaces en los indices sean validos | Anadir `check_links()` al script |
| Sin soporte para docs en subdirectorios | Solo escanea `docs/*.md`, no `docs/**/*.md` | Extender con `find` recursivo |

---

## 7. Referencias

- Documento original (archivo): `docs/archive/001_GUIDE_DOC_MASTERINDEX_1.0_DRAFT.md`
- Script original: `masterindex.sh` (raiz del proyecto)
- Script adaptado: `scripts/generate_docs_index.sh`
- Indice maestro: `docs/INDEX.md`
- Guia de convencion de documentacion: `docs/ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md`
- Documentacion de referencia: `AGENTS.md` (seccion "Existing shell scripts")
- Guia de estilo shell: `docs/000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md`
