---
id: 029
area: doc
type: PROP
module: documentation
version: 1.0
status: ACTIVE
tags:
  - prop
  - documentation
  - organization
  - index
  - area
  - knowledge-base
summary: "Propuesta de organizacion de la base de conocimiento en docs/ por AREA_SEMANTICA del frontmatter, preservando la secuencia de creacion (NNN). Plantea mantener la estructura plana con NNN como identificador unico y agregar un INDEX.md maestro categorizado por area como unico mecanismo de navegacion. Alternativas evaluadas: subdirectorios, symlinks, y vistas virtuales."
keywords:
  - documentacion
  - organizacion
  - area
  - index
  - knowledge-base
  - frontmatter
  - navegacion
  - propuesta
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Propuesta de organizacion de docs/ por AREA_SEMANTICA
---

# Propuesta de Organizacion de docs/ por AREA_SEMANTICA

> **Problema:** El directorio `docs/` contiene 30 archivos planos. No hay
> forma de navegar por area tematica (dev, mgt, doc, prompts, etc.) sin
> leer cada nombre de archivo.
>
> **Restriccion:** La secuencia de creacion (prefijo NNN) debe preservarse.

---

## 0. Estado Actual

### 0.1 Estructura actual

```
docs/
├── NNN_TIPO_AREA_MODULO_VERSION_ESTADO.md  (25 archivos con frontmatter)
├── NNN_AREA_TIPO_MODULO_VERSION_ESTADO.md  (3 archivos legacy, area+tipo invertidos)
├── xxx_DOC_GUIDE_*_1.0_DRAFT.md           (2 sin frontmatter)
└── ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md  (1 con area=algorithms)
```

### 0.2 Areas existentes

| Area | Cantidad | Archivos |
|------|----------|----------|
| `dev` | 21 | 000, 004, 006-018, 020, 022, 024-028 |
| `mgt` | 3 | 019, 021, 023 |
| `doc` | 1 | 003 |
| `prompts` | 1 | 008 |
| `algorithms` | 1 | ALGP003 |
| (sin frontmatter) | 3 | 001, 002, 005 |

### 0.3 Problemas

1. No se puede listar solo documentos de gestion (`area: mgt`) sin grep
2. Los 3 archivos legacy sin frontmatter no tienen area asignada
3. La convencion de nombrado no es uniforme (algunos usan `AREA_TIPO`,
   otros `TIPO_AREA`)
4. ALGP003 tiene un formato de ID diferente

---

## 1. Alternativas Evaluadas

### Alternativa A: Subdirectorios por area (DESCARTADA)

```
docs/
├── dev/
│   ├── 000_GUIDE_SHELL_STYLE_1_0_DRAFT.md
│   ├── 004_SPEC_DOC_PROCESSOR_1_0_DRAFT.md
│   └── ...
├── mgt/
│   ├── 019_REP_FRAMEMAKER_1_0_DRAFT.md
│   └── 021_REP_FRAMEMAKER_MARKET_1_0_DRAFT.md
├── legacy/
│   ├── 001_DOC_GUIDE_MASTERINDEX_1.0_DRAFT.md
│   └── 002_DOC_GUIDE_SPELLCHECK_1.0_DRAFT.md
└── ...
```

| Pro | Contra |
|-----|--------|
| Navegacion limpia por area | La secuencia NNN deja de ser visible en una sola lista |
| Agrupa logicamente | grep `docs/` ya no encuentra todo |
| Estandar en muchos proyectos | El AREA en el nombre del archivo se vuelve redundante |
| | Mover archivos rompe enlaces en referencias cruzadas |
| | Los archivos legacy sin area no tienen un lugar claro |

**Veredicto:** Descarta. La perdida de la secuencia plana y el costo de
mantener referencias cruzadas supera los beneficios.

### Alternativa B: Symlinks por area (DESCARTADA)

```
docs/
├── 000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md  (archivo real)
├── dev/
│   └── 000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md → ../ (symlink)
└── ...
```

| Pro | Contra |
|-----|--------|
| Los archivos reales quedan intactos | Los symlinks no se traducen bien en web (GitHub, GitLab) |
| Se puede navegar por area | Mantener symlinks al crear/renombrar archivos es tedioso |
| | `git status` muestra ruido de symlinks |
| | Dificil de automatizar sin un script de mantenimiento |

**Veredicto:** Descarta. Los symlinks son fragiles y no funcionan bien en
interfaces web de git.

### Alternativa C: INDEX.md por area (SELECCIONADA)

```
docs/
├── 000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md  (plano, sin cambios)
├── ...
├── INDEX.md                                  (maestro, categorizado por area)
├── dev/
│   └── INDEX.md                              (vista parcial, opcional)
└── mgt/
    └── INDEX.md                              (vista parcial, opcional)
```

| Pro | Contra |
|-----|--------|
| Los archivos NO se mueven | INDEX.md requiere mantenimiento manual o generacion |
| La secuencia NNN se preserva | Dos lugares de verdad si se usan sub-INDEX |
| Cualquier herramienta (grep, ls, find) sigue funcionando | |
| GitHub renderiza INDEX.md como landing page del directorio | |
| Se puede automatizar con un script que lea frontmatter | |

**Veredicto:** Seleccionada. Es la que da mejor equilibrio entre orden
y mantenibilidad.

---

## 2. Propuesta: Estructura Plana + INDEX.md Maestro

### 2.1 Reglas

1. **No mover ningun archivo existente.** La estructura plana se mantiene.
2. **Agregar `docs/INDEX.md`** como tabla de contenido categorizada por area.
3. **Opcional: agregar `docs/<area>/INDEX.md`** como vistas parciales.
4. **El prefijo NNN sigue siendo el identificador unico** de secuencia.
5. **Los archivos legacy sin frontmatter (001, 002, 005)** se categorizan
   manualmente en el INDEX.md segun su contenido.

### 2.2 INDEX.md propuesto

```markdown
# Indice de Documentacion

> Secuencia de creacion: NNN ascendente.
> Navegacion por area: usar las secciones siguientes.
> 30 documentos, 5 areas tematicas.

---

## Area: dev (Desarrollo)

Documentos tecnicos del pipeline RECPL, guias de estilo, y propuestas de implementacion.
21 documentos.

| NNN | Tipo | Modulo | Descripcion |
|-----|------|--------|-------------|
| 000 | GUIDE | shell-style | Guia de estilo para scripts shell |
| 004 | SPEC | doc-processor | Especificacion del procesador de documentos |
| 006 | PROP | compiler-bot | Propuesta del bot RECPL |
| ... | ... | ... | ... |

---

## Area: mgt (Gestion)

Analisis de negocio, mercado, y diagnostico del proyecto.
3 documentos.

| NNN | Tipo | Modulo | Descripcion |
|-----|------|--------|-------------|
| 019 | REP | framemaker | Analisis de negocio de FrameMaker |
| 021 | REP | framemaker | Analisis de mercado (TAM/SAM/SOM) |
| 023 | REP | project-analysis | Analisis integral del proyecto |

---

## Area: doc (Documentacion)

Convenciones y herramientas de documentacion.
1 documento.

| NNN | Tipo | Modulo | Descripcion |
|-----|------|--------|-------------|
| 003 | PROP | doc-processor | Propuesta de implementacion del procesador de documentos |

---

## Area: prompts (Prompts)

Plantillas y especificaciones de prompts para agentes.
1 documento.

| NNN | Tipo | Modulo | Descripcion |
|-----|------|--------|-------------|
| 008 | PRM | build-agent | Convenciones de prompts para construir agentes |

---

## Area: algorithms (Algoritmos)

Convenciones de nomenclatura y algoritmos.
1 documento.

| NNN | Tipo | Modulo | Descripcion |
|-----|------|--------|-------------|
| ALGP003 | ALGP | documentation | Convencion de nombrado de documentos |

---

## Sin area (Legacy)

Documentos heredados que no tienen frontmatter YAML.
3 documentos.

| Archivo | Descripcion |
|---------|-------------|
| 001_DOC_GUIDE_MASTERINDEX_1.0_DRAFT.md | Documentacion original de masterindex (Dale Dougherty) |
| 002_DOC_GUIDE_SPELLCHECK_1.0_DRAFT.md | Documentacion original de spellcheck.awk (O'Reilly) |
| 005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md | Teoria de compiladores (Godel, Turing, automatas) |

---

## Secuencia completa (por NNN)

| NNN | Archivo | Area |
|-----|---------|------|
| 000 | `000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md` | dev |
| 001 | `001_DOC_GUIDE_MASTERINDEX_1.0_DRAFT.md` | (legacy) |
| 002 | `002_DOC_GUIDE_SPELLCHECK_1.0_DRAFT.md` | (legacy) |
| ... | ... | ... |
```

### 2.3 Script de generacion automatica (opcional)

```sh
#!/bin/sh
# generate_docs_index.sh - Genera docs/INDEX.md desde frontmatter YAML

echo "# Indice de Documentacion"
echo

for area in dev mgt doc prompts algorithms; do
    echo "## Area: $area"
    echo
    echo "| NNN | Tipo | Modulo | Archivo |"
    echo "|-----|------|--------|---------|"
    for file in docs/*.md; do
        a=$(grep '^area: ' "$file" | sed 's/area: //')
        [ "$a" = "$area" ] || continue
        nnn=$(echo "$file" | sed 's/docs\///;s/_.*//')
        tipo=$(grep '^type: ' "$file" | sed 's/type: //')
        modulo=$(grep '^module: ' "$file" | sed 's/module: //')
        echo "| $nnn | $tipo | $modulo | \`$(basename $file)\` |"
    done
    echo
done
```

---

## 3. Plan de Implementacion

### Fase 1: Crear INDEX.md (estimacion: 30 min)

1. Crear `docs/INDEX.md` con la estructura categorizada por area
2. Incluir los 3 archivos legacy en seccion aparte
3. Verificar que todos los archivos existentes estan referenciados

### Fase 2: Normalizar frontmatter faltante (estimacion: 15 min)

1. Agregar frontmatter YAML a `001_DOC_GUIDE_MASTERINDEX_1.0_DRAFT.md`:
   ```yaml
   area: legacy
   type: GUIDE
   module: masterindex
   ```
2. Agregar frontmatter YAML a `002_DOC_GUIDE_SPELLCHECK_1.0_DRAFT.md`:
   ```yaml
   area: legacy
   type: GUIDE
   module: spellcheck
   ```
3. Agregar frontmatter YAML a `005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md`:
   ```yaml
   area: dev
   type: SPEC
   module: compiler-theory
   ```

### Fase 3: Unificar convencion de nombrado (estimacion: 10 min)

Cambiar los archivos que usan el orden antiguo (`AREA_TIPO`) al orden
nuevo (`TIPO_AREA`) para que coincidan con ALGP003:

| Actual | Propuesto |
|--------|-----------|
| `000_DEV_GUIDE_*` | `000_GUIDE_DEV_*` |
| `001_DOC_GUIDE_*` | `001_GUIDE_DOC_*` |
| `002_DOC_GUIDE_*` | `002_GUIDE_DOC_*` |
| `003_DOC_PROP_*` | `003_PROP_DOC_*` |
| `004_SPEC_DEV_*` | `004_SPEC_DEV_*` (ya correcto) |
| `005_SPEC_DOC_*` | `005_SPEC_DOC_*` (ya correcto) |

**Nota:** Renombrar archivos rompe referencias externas y enlaces en
documentos existentes. Evaluar si el beneficio justifica el costo.

### Fase 4: Script de generacion (opcional, estimacion: 20 min)

1. Crear `scripts/generate_docs_index.sh`
2. Agregar al Makefile o como hook de pre-commit
3. Documentar en el INDEX.md que es generado

---

## 4. Estado final propuesto

```
docs/
├── INDEX.md                               ← NUEVO: indice maestro por area
├── 000_GUIDE_DEV_SHELL_STYLE_1_0_DRAFT.md ← sin cambios
├── 001_DOC_GUIDE_MASTERINDEX_1.0_DRAFT.md ← (se agregara frontmatter)
├── 002_DOC_GUIDE_SPELLCHECK_1.0_DRAFT.md  ← (se agregara frontmatter)
├── 003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md
├── 004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md
├── 005_SPEC_DOC_COMPILADORTHEORY_1.0_ACTIVE.md ← (se agregara frontmatter)
├── ... (todos los demas, sin cambios)
└── ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md
```

**29 archivos planos + 1 INDEX.md = 30 archivos total.**

---

## 5. Criterios de decision

| Criterio | Alternativa A (subdirs) | Alternativa B (symlinks) | Alternativa C (INDEX.md) |
|----------|------------------------|--------------------------|-------------------------|
| Preserva secuencia NNN | NO | SI | SI |
| Navegacion por area | EXCELENTE | BUENA | BUENA |
| Mantenible sin scripting | NO | NO | SI |
| Funciona en GitHub web | SI | NO | SI |
| grep/docs/\* encuentra todo | NO | SI | SI |
| Riesgo de romper enlaces | ALTO | BAJO | NULO |
| Esfuerzo de implementacion | ALTO | ALTO | BAJO |

**Alternativa C gana en 6 de 7 criterios.**

---

## 6. Checklist de implementacion

- [ ] Crear `docs/INDEX.md` con todas las areas y sus documentos
- [ ] Categorizar los 3 archivos legacy en seccion separada del INDEX
- [ ] Agregar frontmatter a los 3 archivos legacy (opcional)
- [ ] Decidir si renombrar archivos al orden TIPO_AREA (opcional)
- [ ] Crear script de generacion automatica (opcional)
- [ ] Commit + push de los cambios
