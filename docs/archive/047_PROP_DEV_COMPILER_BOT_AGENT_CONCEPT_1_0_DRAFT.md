---
id: 047
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - prop
  - concept
  - agent
  - ai-coding-agent
  - rebranding
  - architecture
  - open-source
  - recpl
summary: "Analisis y propuesta de nuevo concepto para Proyecto0: de un compilador de lenguaje natural a codigo IR a un agente de IA de codigo abierto multi-proposito para desarrollo de software. Define alcance, analisis de viabilidad, mapeo contra el codigo existente, arquitectura de agentes, y plan de migracion."
keywords:
  - propuesta
  - concepto
  - agente-ia
  - recpl
  - rebranding
  - open-source
  - coding-agent
  - arquitectura-agentes
  - migracion
  - analisis
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Analisis de nuevo concepto para Proyecto0 como agente de IA open-source para desarrollo de software
---

# Propuesta de Nuevo Concepto: Proyecto0(RECPL) como Agente de IA Open-Source

> **Documento de analisis.** Evalua el cambio de paradigma de Proyecto0: de un
> "compilador de lenguaje natural a codigo IR" a un
> "agente de IA de codigo abierto para escribir y ejecutar codigo con
> cualquier modelo de IA".

---

## 0. Resumen Ejecutivo

**Concepto actual:** RECPL Compiler Bot — un pipeline compilador (preprocessor →
lexer → parser → semantic → IR → synthesis) que traduce lenguaje natural a
scaffolding de modulos NestJS/Prisma.

**Concepto propuesto:** Proyecto0(RECPL) — un agente de codigo abierto que ayuda
a escribir y ejecutar codigo con cualquier modelo de IA. Disponible como interfaz
de terminal, aplicacion de escritorio y extension de IDE.

**Naturaleza del cambio:** Mas que una reescritura, es un **cambio de narrativa y
posicionamiento** que expande el alcance del proyecto existente. El pipeline
compilador actual se convierte en el **nucleo deterministico** de un sistema de
agentes mas grande.

| Aspecto | Concepto Actual | Nuevo Concepto |
|---------|-----------------|----------------|
| Que es | Compilador NL → NestJS/Prisma | Agente de IA open-source para codigo |
| Output | Modulos NestJS, modelos Prisma | Cualquier tarea de desarrollo |
| Usuarios | Desarrolladores NestJS/Prisma | Cualquier desarrollador |
| Modelo de IA | Solo Claude/OpenAI via API key | Cualquier modelo (gratis, pago, local) |
| Interfaz | Terminal (CLI) | Terminal, Desktop, IDE extension |
| Licencia | MIT | MIT (sin cambios) |
| Monetizacion | — | 100% gratuito, modelos gratuitos incluidos |

---

## 1. Analisis del Concepto Propuesto

### 1.1 Definicion

Proyecto0(RECPL) se define como:

> **Un agente de codigo abierto que te ayuda a escribir y ejecutar codigo con
> cualquier modelo de IA. Esta disponible como interfaz de terminal, aplicacion
> de escritorio o extension de IDE.**

### 1.2 Modelo de uso

```
$ recpl "crea un modulo de pagos en NestJS"
✅ Modulo Payments creado en modules/payments/

$ recpl "explica como funciona este pipeline"
El pipeline RECPL procesa lenguaje natural como un compilador...

$ recpl --tui
[Interfaz grafica en terminal]

$ recpl --model local "refactoriza este controlador"
...
```

### 1.3 Pilares del concepto

| Pilar | Descripcion |
|-------|-------------|
| **Open-source (MIT)** | Codigo publico en GitHub. Cualquiera puede usarlo, modificarlo, contribuir. |
| **Multi-modelo** | Soporta OpenAI, Anthropic, xAI, Google, y modelos locales. Viene con modelos gratuitos integrados. |
| **Sin suscripcion forzada** | No requiere cuenta. Los modelos gratuitos funcionan out-of-the-box. |
| **Multi-interfaz** | Terminal, desktop app, IDE extension (VS Code, JetBrains). |
| **Multi-proposito** | No limitado a scaffolding — cualquier tarea de desarrollo. |
| **Autonomo** | Orientado a objetivos, proactivo, reactivo, con capacidad de usar herramientas. |

---

## 2. Contexto: El Estado Actual del Proyecto

### 2.1 Lo que ya existe (y se preserva)

El pipeline RECPL actual proporciona una base solida para el nuevo concepto:

| Componente | Archivo | Proposito en el nuevo concepto |
|------------|---------|-------------------------------|
| Pipeline deterministico | `preprocessor.sh` → `lexer.sh` → `parser.sh` → `semantic.sh` → `ir_generator.sh` → `synthesis.sh` | Nucleo determinista del agente. Procesa ~80% de instrucciones sin costo. |
| Loop principal | `recpl.sh` (352 lineas, 4 modos) | Entrypoint del agente. Modos interactivo, batch, comando, archivo. |
| Proveedores LLM | `providers/claude.sh`, `providers/openai.sh` | Adapters para modelos de pago. |
| Provider registry | `providers/provider_registry.sh` (propuesto en 046) | Catalogo centralizado de modelos. |
| Fachada LLM | `frontend/llm_classifier.sh` | Dispatcher inteligente que elige que modelo usar. |
| Router | `frontend/router.sh` | Decide entre pipeline deterministico o LLM segun complejidad. |
| Pipeline debugger | `pipeline_debugger.sh` (784 lineas, 5 modos) | Herramienta de diagnostics y trazabilidad del agente. |
| Arquitectura tier | `docs/046` — free/paid layers | Base para el modelo gratuito + BYOK (bring-your-own-key). |
| Provider gratuito | `docs/045` — apifreellm.com | Modelos 200B+ params sin costo. |
| TUI wrapper | `docs/039` — whiptail TUI | Semilla para la interfaz de escritorio. |
| Sistema de templates | `templates/` (NestJS, Prisma) | Mecanismo de scaffolding extensible. |
| Comandos compuestos | `frontend/router.sh` — source, exec | Capacidad de ejecutar scripts y archivos. |
| 72 tests | `tests/run_tests.sh` | Suite de regresion. |

### 2.2 Lo que NO existe (y hay que construir)

| Componente | Prioridad | Depende de |
|------------|-----------|------------|
| IDE extension (VS Code) | Futuro | API del agente |
| Desktop app | Futuro | TUI o framework nativo |
| Modelos gratuitos integrados (no requieren API key) | **ALTA** | apifreellm.sh, o modelos locales |
| API HTTP del agente | Media | router.sh, recpl.sh |
| Memoria persistente del agente | Media | semantic.sh (tabla de simbolos actual es efimera) |
| Multi-agente / comunicacion entre agentes | Baja | Arquitectura de agentes |
| Herramientas del agente (tool use) | **ALTA** | Ya existe en providers (tool calling) |
| Instalador / package manager | Media | Scripts de distribucion |
| Documentacion de usuario (README, sitio web) | Media | — |

---

## 3. Analisis de Viabilidad Tecnica

### 3.1 El pipeline compilador como nucleo deterministico del agente

El pipeline RECPL actual implementa un **compilador de lenguaje natural a codigo IR** que
transforma una instruccion en una accion estructurada (IR.json). En el nuevo
concepto, este pipeline se convierte en el **modo deterministico** del agente:
rapido, sin costo, y predecible.

```
Instruccion: "crea modulo payments en nestjs"

Pipeline deterministico (50ms, $0):
  preprocess → lexer → parser → semantic → IR → synthesis → archivos

Pipeline con LLM (1-3s, ~$0.004):
  preprocess → router → llm_classifier → provider → IR mapper → synthesis → archivos
```

**Ventaja competitiva:** El modo deterministico permite que el agente sea util
**sin conexion a internet y sin costo**, algo que ningun "AI coding agent"
comercial ofrece. Incluso sin LLM, RECPL entiende un lenguaje natural
estructurado y produce codigo real.

### 3.2 La arquitectura de agentes ya existe parcialmente

El concepto de "agente" se define por:

| Caracteristica | Estado en RECPL |
|----------------|-----------------|
| **Autonomia** | PARCIAL — El pipeline procesa sin intervencion humana, pero no inicia acciones por si mismo |
| **Proactividad** | NO — RECPL solo reacciona a input del usuario |
| **Reactividad** | SI — Responde a instrucciones, errores, y cambios de estado |
| **Orientado a objetivos** | PARCIAL — Cada instruccion es un objetivo, pero no hay planificacion multi-paso |
| **Uso de herramientas (tool calling)** | SI — Los LLM llaman a herramientas (scaffold, delete, read, update) via function calling |
| **Memoria** | PARCIAL — Tabla de simbolos persistente en disco, pero sin memoria de largo plazo |
| **Comunicacion multi-agente** | NO — No hay protocolo de comunicacion entre agentes |

**Conclusion:** El proyecto actual implementa ~50% de las caracteristicas de un
agente. Las brechas principales son: proactividad, planificacion multi-paso, y
memoria de largo plazo.

### 3.3 Viabilidad del modelo gratuito

La propuesta 045 (apifreellm.com) y 046 (tier architecture) ya disenan la capa
gratuita. El nuevo concepto explicita:

- **Free tier actual:** Pipeline deterministico (sin costo, sin API key, sin internet)
- **Free LLM tier:** apifreellm.com (sin costo monetario, requiere API key gratuita)
- **Premium LLM tier:** Claude, OpenAI, etc. (costo por token, BYOK)

El usuario puede usar RECPL **sin pagar un centavo** usando solo el pipeline
deterministico + apifreellm.

### 3.4 Viabilidad de las interfaces adicionales

| Interfaz | Viabilidad | Esfuerzo estimado |
|----------|------------|-------------------|
| Terminal (CLI) | **EXISTE** | 0 |
| TUI (whiptail) | Disenada en 039 | ~2 horas |
| Desktop app | Baja (requiere framework nativo o Electron) | ~2-4 semanas |
| IDE extension | Media (VS Code API + agente como servicio) | ~2-3 semanas |
| Web UI | Disenada en 011 | ~4-6 semanas |

**Recomendacion:** Implementar TUI primero (bajo riesgo), luego Web UI (mayor
alcance), dejar Desktop e IDE para fases futuras.

---

## 4. Arquitectura de Agentes Propuesta

### 4.1 Definicion de "Agente" en el contexto de RECPL

> Un agente es una entidad computacional disenada para percibir su entorno
> (digital y potencialmente fisico), tomar decisiones informadas basadas en esas
> percepciones y un conjunto de objetivos predefinidos o aprendidos, y ejecutar
> acciones para alcanzar esos objetivos de manera autonoma.

**Caracteristicas del agente RECPL:**

1. **Autonomia:** Opera sin intervencion humana una vez recibida una instruccion
2. **Proactividad:** Puede sugerir acciones, preguntar para clarificar, o
   proponer alternativas
3. **Reactividad:** Responde a cambios en el entorno (errores de compilacion,
   archivos modificados, etc.)

### 4.2 Capacidades del agente (herramientas)

Una "Capacidad" es el uso de herramientas que permite al agente interactuar con
APIs externas, bases de datos, o servicios, alcanzando mas alla de su lienzo
inmediato.

**Capacidades actuales de RECPL:**

| Herramienta | Descripcion | Implementada en |
|-------------|-------------|-----------------|
| `scaffold_module` | Genera modulo NestJS/Prisma | `synthesis.sh` + `scaffold.sh` |
| `scaffold_entity` | Genera entidad | `synthesis.sh` + `scaffold.sh` |
| `delete_module` | Elimina modulo | `synthesis.sh` |
| `read_module` | Muestra informacion | `synthesis.sh` |
| `update_module` | Modifica modulo | `synthesis.sh` |
| `clarify` | Pregunta al usuario | `llm_classifier.sh` |
| `respond` | Responde textual | `llm_classifier.sh` |

**Capacidades futuras (nuevo concepto):**

| Herramienta | Descripcion | Prioridad |
|-------------|-------------|-----------|
| `read_file` | Lee archivos del proyecto | Alta |
| `write_file` | Escribe/edita archivos | Alta |
| `run_command` | Ejecuta comandos del sistema | Alta |
| `search_code` | Busca en el codigo fuente | Media |
| `git_operation` | Opera sobre el repositorio git | Media |
| `install_dependency` | Instala paquetes | Baja |
| `run_tests` | Ejecuta tests y reporta resultados | Baja |

### 4.3 Memoria del agente

El agente necesita retener informacion a lo largo de las interacciones:

| Tipo de memoria | Estado actual | Estado deseado |
|-----------------|---------------|----------------|
| Sesion (conversacion) | Parcial (via RECPL_STATE_DIR) | Completa (historial de instrucciones y respuestas) |
| Proyecto (tabla de simbolos) | Si (modulos creados, tech stack) | Expandido (archivos, dependencias, configuracion) |
| Largo plazo (entre sesiones) | No | Base de datos ligera (SQLite o JSON) |
| Contexto (archivos del proyecto) | No | Indice de archivos y su contenido |

### 4.4 Comunicacion entre agentes

> Los agentes pueden establecer conversaciones con usuarios, otros sistemas,
> incluso otros agentes que operan en el mismo lienzo conectados.

El nuevo concepto imagina un ecosistema donde multiples agentes RECPL colaboran:

- **Orquestador:** Recibe la instruccion de alto nivel, la descompone en subtareas
- **Especialistas:** Cada agente se encarga de un dominio (backend, frontend, DB, tests)
- **Memoria compartida:** Los agentes comparten estado via RECPL_STATE_DIR o un bus

**Estado actual:** No hay soporte multi-agente. El pipeline actual es monolitico
(un solo proceso, un solo hilo de ejecucion).

**Estado futuro deseado:** Arquitectura de micro-agentes donde cada uno expone
una interfaz estandar y se comunican via JSON/IPC.

---

## 5. Mapeo del Codigo Existente contra el Nuevo Concepto

### 5.1 Lo que se preserva (sin cambios)

| Archivo | Funcion actual | Funcion en nuevo concepto |
|---------|---------------|---------------------------|
| `frontend/preprocessor.sh` | Normaliza input | Normalizacion de instrucciones del agente |
| `frontend/lexer.sh` | Tokeniza | Analisis lexico de comandos deterministicos |
| `frontend/parser.sh` | Construye AST | Analisis sintactico de comandos deterministicos |
| `frontend/semantic.sh` | Valida tipos | Memoria del agente (tabla de simbolos) |
| `middleend/ir_generator.sh` | Genera IR.json | Representacion intermedia canonica |
| `backend/synthesis.sh` | Sintetiza respuesta | Ejecutor de acciones del agente |
| `backend/scaffold.sh` | Renderiza templates | Generador de archivos |
| `recpl.sh` | Bucle principal | Entrypoint y loop del agente |
| `tests/run_tests.sh` | Tests | Suite de regresion |

### 5.2 Lo que se modifica

| Archivo | Cambio | Razon |
|---------|--------|-------|
| `frontend/llm_classifier.sh` | Dispatcher multi-provider (ya disenado en 046) | Soporte de cualquier modelo |
| `frontend/router.sh` | Pasar RECPL_LLM_TIER (ya disenado en 046) | Routing por capa free/paid |
| `recpl.sh` | Flag `--tier`, `--model`, `--tui` | Nuevas interfaces y modos |
| `providers/provider_registry.sh` | Expandir registro (nuevo, propuesto en 046) | Catalogo de modelos |
| `pipeline_debugger.sh` | Bugfix --output | Correccion de bug conocido |

### 5.3 Lo que se crea

| Archivo | Proposito | Prioridad | Depende de |
|---------|-----------|-----------|------------|
| `providers/apifreellm.sh` | Provider gratuito | **ALTA** | 045_PROP |
| `providers/provider_registry.sh` | Registro de modelos | **ALTA** | 046_PROP |
| `tui.sh` | Interfaz TUI | Media | 039_PROP |
| `Makefile` o `recpl` | Instalador global | Media | — |
| `recpl --serve` | API HTTP del agente | Baja | router.sh |
| `.github/workflows/` | CI/CD | Media | — |

### 5.4 Lo que se archiva/desprioriza

| Componente | Motivo | Destino |
|------------|--------|---------|
| Core C (`recpl-core/`) | No alineado con el nuevo concepto (el valor esta en la flexibilidad del shell + LLM, no en la velocidad C) | Rama `experiment/c-core` |
| Docs 019-021 (FrameMaker) | Distraccion del nuevo concepto | Rama `archive/framemaker` |
| Docs 005 (teoria compiladores) | Referencia teorica, no bloqueante | Mantener en docs/ |
| Docs 013-017 (C core) | Especifico de C core archivado | Mantener referencias |

---

## 6. Analisis de Brechas (Gap Analysis)

### 6.1 Brechas tecnicas

| Brecha | Impacto en el nuevo concepto | Esfuerzo para cerrar |
|--------|------------------------------|----------------------|
| Sin modelos gratuitos integrados (sin API key) | El claim "viene con modelos gratuitos" no se cumple | **Alto** — requiere negociacion con proveedores o bundle de modelo local (Ollama) |
| Sin API HTTP | No se puede construir IDE extension o web UI sobre el agente | Medio (~1 semana) |
| Sin memoria de largo plazo | El agente olvida entre sesiones | Bajo (~1 dia, SQLite) |
| Sin planificacion multi-paso | El agente no puede ejecutar tareas complejas que requieren secuencias de acciones | **Alto** — requiere un planificador/orquestador |
| Sin instalador global (`recpl` command) | El usuario debe clonar el repo y ejecutar `./compiler-bot/recpl.sh` | Bajo (~1 hora, script de instalacion) |
| Sin CI/CD | No hay validacion automatica de contribuciones | Medio (~1 dia, GitHub Actions) |
| Sin empaquetado (npm, brew, etc.) | Dificil de distribuir | Medio (~2-3 dias por plataforma) |

### 6.2 Brechas de concepto

| Brecha | Impacto | Mitigacion |
|--------|---------|------------|
| El nombre "RECPL" evoca un compilador, no un agente | Confusion de marca | Mantener RECPL como nombre del pipeline, "Proyecto0" como nombre del agente |
| El pipeline deterministico es muy limitado (solo NestJS/Prisma) | El agente solo sirve para scaffolding | El LLM expande las capacidades. El deterministico es el modo "sin conexion" |
| La TUI actual (whiptail) es muy basica | No compite con herramientas modernas como Cursor o Windsurf | Documentar que es un wrapper liviano. La desktop app completa es futura. |

### 6.3 Brechas de ecosistema

| Brecha | Impacto | Mitigacion |
|--------|---------|------------|
| Sin comunidad de usuarios | Sin feedback, sin contribuciones | Open-source desde el inicio. GitHub issues abierto. |
| Sin documentacion de API/contribucion | Dificil que otros contribuyan | README.md actualizado + docs existentes |
| Sin ejemplos/use cases | El developer no entiende para que sirve | El runbook (010) ya documenta casos de uso |
| Sin landing page / sitio web | No hay "cara publica" del proyecto | README.md como landing page inicial |

---

## 7. Estrategia de Migracion (De Compilador a Agente)

### 7.1 Fase 0: Fundacion (Semana 1) — SIN RIESGO

Cerrar las brechas inmediatas que ya estan disenadas:

1. **Provider gratuito**: Implementar `providers/apifreellm.sh` (045_PROP, ~45 min)
2. **Provider registry**: Implementar `providers/provider_registry.sh` (046_PROP, ~20 min)
3. **Dispatcher multi-tier**: Refactorizar `llm_classifier.sh` (046_PROP, ~40 min)
4. **Flag `--tier`**: Agregar a `recpl.sh` (046_PROP, ~15 min)
5. **Bugfix --output**: Corregir `pipeline_debugger.sh` (~10 min)
6. **Commit inicial**: `git add . && git commit` (~5 min)

**Resultado:** RECPL funcional con tier gratuito, sin cambios en la API publica.

### 7.2 Fase 1: Rebranding (Semana 2) — NARRATIVA

1. **Actualizar README.md**: Nuevo concepto, nuevo proposito, nuevos ejemplos
2. **Actualizar AGENTS.md**: Reflejar el nuevo alcance
3. **Crear script de instalacion**: `make install` o `curl ... | sh`
4. **Alias `recpl`**: Script que se instala en PATH
5. **Menu de ayuda**: `recpl --help` con el nuevo mensaje de bienvenida

### 7.3 Fase 2: Interfaces (Semana 3-4) — ALCANCE

1. **TUI wrapper**: Implementar `tui.sh` (039_PROP, ~2 horas)
2. **API HTTP minima**: `recpl --serve` con endpoint `/api/prompt`
3. **Memoria persistente**: Expandir tabla de simbolos con SQLite ligero

### 7.4 Fase 3: Ecosistema (Mes 2+) — CRECIMIENTO

1. **IDE extension (VS Code)**: Wrapper del API del agente
2. **Modelos locales**: Integracion con Ollama
3. **Multi-agente**: Orquestador que divide tareas complejas
4. **Plugin system**: Terceros pueden agregar herramientas/capacidades
5. **Despliegue**: GitHub Actions, publicacion en npm/brew

---

## 8. Riesgos y Mitigaciones

### 8.1 Riesgos del cambio de concepto

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| **El proyecto pierde su identidad** ("era un compilador, ahora que es?") | Media | Alto | La marca "RECPL" se preserva como nombre del pipeline. "Proyecto0" es el agente. |
| **Expectativas irreales** ("agente de IA" suena a Cursor, no a un script shell) | **Alta** | Alto | Documentacion honesta: "Es un agente minimalista que prioriza transparencia y bajo costo sobre pulido UX" |
| **El pipeline deterministico queda obsoleto** | Baja | Medio | Es la ventaja unica: sin internet, sin costo, sigue funcionando. Preservar y celebrar. |
| **Demasiado ambito** (terminal + desktop + IDE + multi-modelo) | Media | Alto | Principio YAGNI: entregar la terminal primero, iterar. |
| **El modelo gratuito (apifreellm) cambia o desaparece** | Media | Medio | El pipeline deterministico no depende de el. El registry permite cambiar de provider. |

### 8.2 Riesgos de ejecucion

| Riesgo | Mitigacion |
|--------|------------|
| **Paralisis por analisis** (mas docs, menos codigo) | Regla: cada semana debe terminar con codigo nuevo en main |
| **Dependencia de APIs externas** | El modo deterministico (sin LLM) es el pilar. LLM es valor agregado. |
| **El proyecto se vuelve demasiado complejo** | Separar en modulos: recpl-core (pipeline), recpl-agent (LLM), recpl-ui (interfaces) |
| **Falta de usuarios/feedback** | Publicar temprano, aunque sea solo CLI. Feedback real > diseno perfecto. |

---

## 9. Preguntas Abiertas para el Autor

1. **Modelos gratuitos:** Que significa "viene con modelos gratuitos sin crear una
   cuenta"? apifreellm es gratuito pero requiere API key. Hay que aclarar si se
   refiere a:
   - Pipeline deterministico (sin API key, sin internet, sin costo)?
   - Modelos via apifreellm (API key gratuita)?
   - Modelos locales via Ollama (sin internet, requiere instalacion)?

2. **Desktop app:** Es una prioridad real o un "nice to have"? La TUI whiptail
   puede ser un paso intermedio, pero una desktop app real requiere Electron,
   Tauri, o similar.

3. **IDE extension:** Similarmente, es para el roadmap o para ahora? Una
   extension VS Code minima es factible (~1 semana), pero requiere mantenerla.

4. **Multi-agente:** Es parte del concepto fundacional o aspiracion a futuro?
   La comunicacion entre agentes es un desafio de diseno significativo.

5. **Que hace unico a Proyecto0?** En un mercado con Cursor, Windsurf, Copilot,
   Codeium, la diferenciacion debe ser clara:
   - 100% open-source (MIT)
   - Funciona sin internet (pipeline deterministico)
   - Sin vendor lock-in (cualquier modelo)
   - Sin telemetria forzada
   - Extensible via shell scripting

---

## 10. Recomendacion

**El nuevo concepto es viable y deseable.** La base tecnica actual soporta ~70%
del concepto propuesto sin cambios mayores. Las piezas faltantes (provider
gratuito, registry, TUI) ya estan disenadas en documentos previos (045, 046,
039).

**Recomendacion de orden de implementacion:**

```
Prioridad 1 (Semana 1) — Cerrar lo disenado:
  Implementar 045 + 046 (provider gratuito, registry, dispatcher)
  Bugfix pipeline_debugger.sh
  Primer commit

Prioridad 2 (Semana 2) — Rebranding:
  README.md con nuevo concepto
  Script de instalacion (recpl global)
  AGENTS.md actualizado

Prioridad 3 (Semana 3) — Interfaces:
  TUI wrapper (039)
  API HTTP minima (--serve)

Prioridad 4 (Mes 2+) — Crecimiento:
  Memoria persistente (SQLite)
  IDE extension
  Modelos locales (Ollama)
  Multi-agente
```

**Lo que NO se debe hacer:**
- NO reescribir el pipeline existente (el valor actual esta en los 72 tests y la
  base funcional)
- NO prometer lo que no se puede entregar (desktop app pulida sin equipo)
- NO abandonar el pipeline deterministico (es la ventaja competitiva unica)
- NO agregar dependencias externas que rompan el "funciona sin internet"

---

## 11. Referencias

- `docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Propuesta original del compilador
- `docs/039_PROP_DEV_COMPILER_BOT_TUI_LAYER_1_0_DRAFT.md` — Propuesta de capa TUI
- `docs/045_PROP_DEV_COMPILER_BOT_PROVIDER_APIFREELLM_1_0_DRAFT.md` — Provider gratuito
- `docs/046_PROP_DEV_COMPILER_BOT_TIER_ARCHITECTURE_1_0_DRAFT.md` — Arquitectura free/paid
- `docs/030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md` — Integracion LLM
- `docs/023_REP_MGT_PROJECT_ANALYSIS_1_0_DRAFT.md` — Analisis integral del proyecto
- `docs/011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` — Extension multi-tech y web UI
- `compiler-bot/recpl.sh` — Loop principal (entrypoint actual)
- `compiler-bot/frontend/llm_classifier.sh` — Fachada LLM
- `compiler-bot/providers/` — Adapters de proveedores
