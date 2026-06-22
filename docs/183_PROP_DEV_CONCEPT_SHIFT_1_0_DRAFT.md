---
id: 183
area: dev
type: prop
module: concept_shift
version: 1.0
status: DRAFT
tags:
  - proposal
  - concept
  - IR
  - refactor
  - documentation
  - architecture
summary: "Propuesta para cambiar el concepto central del proyecto de 'Compilador de lenguaje natural a codigo NestJS/Prisma/React' a 'Compilador de lenguaje natural a codigo IR'. Busca alinear la concepcion del sistema con su idea original y ampliar la utilidad a cualquier tecnologia de salida."
keywords:
  - proposal
  - concept-shift
  - IR-first
  - documentation
  - code-generation
changelog:
  - version: 1.0
    date: 2026-06-21
    author: system
---

# Propuesta de Cambio de Concepto: Compilador NL → IR

## 1. Estado Actual

El proyecto esta definido conceptualmente como:

> **Compilador de lenguaje natural a codigo NestJS, Prisma, React...**

Esta definicion aparece en:
- `AGENTS.md`
- `README.md`
- `prompts/build.txt`
- `docs/INDEX.md`
- Varios reportes y planes en `docs/`

El codigo realmente hace lo que el concepto dice: toma instrucciones en
lenguaje natural y genera scaffolding concreto de modulos NestJS, entidades
Prisma, componentes React, etc. a traves de generadores especificos
(`nestjs_generator.py`, `prisma_generator.py`, `react_generator.py`,
`docker_generator.py`, `nextjs_generator.py`).

## 2. Problema

El concepto actual tiene tres limitaciones fundamentales:

### 2.1 Utilidad restringida

El sistema solo es util para proyectos que usen NestJS, Prisma, React o
NextJS. Cualquier persona que trabaje con Django, Rails, Spring Boot,
Go, Rust, o cualquier otro stack no puede aprovechar el compilador.

### 2.2 Esfuerzo desproporcionado

Se invierte esfuerzo significativo en mantener y extender generadores para
tecnologias especificas. Cada nuevo generador requiere:
- Template scaffolding por tecnologia
- Pruebas de integracion por tecnologia
- Mantenimiento ante cambios de versiones de la tecnologia destino

### 2.3 Desalineacion con la idea original

El sistema fue concebido como un **compilador** en el sentido clasico
(Aho, Dragon Book): pipeline que transforma lenguaje natural → AST → IR →
codigo. El Middle End (IR) es el corazon del compilador, no los generadores
del Back End. La definicion actual pone el foco en el Back End cuando el
valor diferencial esta en el pipeline completo.

## 3. Propuesta

Cambiar el concepto central a:

> **Compilador de lenguaje natural a codigo IR**

Donde **IR** (Intermediate Representation) es una representacion canonica
e independiente de tecnologia que describe la intencion del usuario en
terminos de:
- Accion a realizar (CREAR, LEER, ACTUALIZAR, ELIMINAR)
- Entidades involucradas (modulos, modelos, componentes)
- Relaciones entre entidades
- Atributos y configuracion
- Dependencias

### 3.1 Que implica

| Aspecto | Antes | Despues |
|---------|-------|---------|
| Concepto | "Compilador NL a NestJS/Prisma" | "Compilador NL a IR" |
| Output primario | Codigo NestJS, Prisma, React | IR JSON canonico |
| Generadores | Obligatorios para funcionar | Plugins intercambiables |
| Usuario target | Desarrolladores NestJS/Prisma | Cualquier desarrollador |
| Valor diferencial | Scaffolding por tecnologia | Pipeline de compilacion NL→IR |

### 3.2 Que NO cambia

- El pipeline compilador (preprocess → lexer → parser → semantic → IR →
  synthesis) se mantiene intacto
- Los generadores existentes no se eliminan — pasan a ser **plugins
  opcionales**
- El codigo existente sigue funcionando
- La arquitectura del sistema no se modifica

## 4. Impacto en Documentacion

### 4.1 Documentos a actualizar (prioridad alta)

| Documento | Cambio |
|-----------|--------|
| `AGENTS.md` | Reescribir seccion "Objetivo implicito del proyecto" |
| `README.md` | Actualizar descripcion, tagline, ejemplos |
| `prompts/build.txt` | Reescribir prompt de especificacion |
| `docs/INDEX.md` | Actualizar descripcion del proyecto |
| `docs/001_CLASS_DIAGRAM_RECPL_1_0_DRAFT.md` | Revisar notas conceptuales |
| `docs/architecture/001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md` | Actualizar seccion de proposito |
| `docs/archive/070_GUIDE_DEV_PYTHON_STYLE_1_0_DRAFT.md` | Sin cambio (estilo, no concepto) |

### 4.2 Documentos a crear

| Documento | Proposito |
|-----------|-----------|
| Guia del IR canonico | Especificacion formal del formato IR, sus nodos, validacion |
| Guia de generadores como plugins | Como escribir un generador para cualquier tecnologia |
| Tutorial: usar el compilador sin generadores | Obtener IR y consumirlo externamente |

### 4.3 Documentos sin cambio

- Guias de estilo (`000_GUIDE_DEV_SHELL_STYLE`, `070_GUIDE_DEV_PYTHON_STYLE`)
- Planes de ejecucion especificos (planes de fase, sprints)
- Reportes historicos (quedan como registro del estado anterior)
- Documentacion de componentes internos (nodes/, agents/, etc.)

## 5. Impacto en Codigo

### 5.1 Cambios semánticos (bajo esfuerzo)

| Archivo | Cambio |
|---------|--------|
| `pyproject.toml` | Actualizar `description` |
| `synthesis.py` / `action_executor.py` | Documentar que el output IR es el producto primario |
| `generator_factory.py` | Documentar que los generadores son plugins, no el core |
| CLI entrypoint | Mensaje de bienvenida/ayuda alineado al nuevo concepto |

### 5.2 Cambios estructurales (esfuerzo medio, opcional)

| Componente | Cambio propuesto |
|------------|------------------|
| `generators/` | Reorganizar como directorio de plugins con registro explicito |
| Interfaz de generador | Definir protocolo formal (ABC o Protocol) para generadores externos |
| Output por defecto | En modo `--ir-only`, emitir IR JSON y terminar sin generar codigo |

## 6. Estrategia de Migracion

### Fase 1 — Documentacion (1 sesion)

Actualizar todos los documentos listados en 4.1 para reflejar el nuevo
concepto. No tocar codigo.

**Criterio de exito:** `grep -r "Compilador de lenguaje natural a codigo" docs/`
ya no muestra la definicion antigua (excepto en documentos historicos
donde sea apropiado conservarla).(**Obviar excepcion**)

### Fase 2 — Codigo (1-2 sesiones)

- Actualizar metadata en pyproject.toml
- Agregar flag `--ir-only` al CLI
- Documentar IR como primer ciudadano en docstrings
- Si aplica, reorganizar generadores como plugins

### Fase 3 — Comunicacion

- Actualizar canales de comunicacion del proyecto
- README.md con ejemplos que muestren IR como output
- CHANGELOG.md con entrada del cambio conceptual

## 7. Riesgos

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| Confusion en usuarios existentes | Alta | Documentar que los generadores siguen funcionando |
| Percepcion de "menos funcionalidad" | Media | Enfatizar que IR + plugins = mas funcionalidad |
| Resistencia al cambio conceptual | Baja | El cambio alinea con la realidad arquitectonica |
| Generadores se vuelven ciudadanos de segunda | Media | Explicitamente documentarlos como plugins mantenidos |

## 8. Veredicto

**Recomendado.** El cambio de concepto no requiere reescribir codigo ni
cambiar la arquitectura. Es principalmente un cambio de **encuadre**
(framing) que:

1. Refleja con mayor precision el valor real del sistema (el pipeline
   compilador)
2. Abre la puerta a usuarios de cualquier tecnologia
3. Reduce presion de mantener generadores para cada tecnologia existente
4. Prepara el terreno para la vision de Code Assistant Agentic Platform
   (donde el IR es el lenguaje de intercambio entre agentes)

El esfuerzo es bajo (~2-3 sesiones) y el riesgo es manejable con
comunicacion clara.
