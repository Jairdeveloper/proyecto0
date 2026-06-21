---
id: 014
area: dev
type: prop
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - proposal
  - compiler-bot
  - recpl
  - nlp
  - intent
  - natural-language
  - dialog-manager
  - contexto
  - ambiguedad
  - clasificador
  - comprension
  - mejora
summary: "Propuesta de sistema NLP y clasificador de intenciones (Intent) para el bot RECPL. Anade una capa de comprension de lenguaje natural antes del pipeline existente: clasifica la intencion del usuario, extrae entidades y relaciones, resuelve ambiguedades, gestiona contexto multi-turno y maneja dialogos de clarificacion."
keywords:
  - propuesta
  - nlp
  - intent
  - clasificador
  - lenguaje-natural
  - comprension
  - contexto
  - dialogo
  - ambiguedad
  - entidades-nombradas
  - slot-filling
  - requerimientos
  - recpl
  - compiler-bot
changelog:
  - version: 1.0
    date: 2026-06-07
    author: workflow-agent
    description: Creacion de la propuesta de sistema NLP e Intent para el bot RECPL
---

# Propuesta: Sistema NLP y Clasificador de Intenciones (Intent) para RECPL

> **Referencias:** `003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md` (patrones de pipeline modular),
> `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` (especificacion con requerimientos y fases),
> `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` (arquitectura original del bot),
> `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` (multi-tech-stack + UI web),
> `012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md` (flujo de datos + refinamiento),
> `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` (nucleo C nativo)
>
> **Continuacion de:** 011 (multi-stack), 012 (contratos/grafo), 013 (C core)
>
> Mientras 011-013 definen *que* construimos y *como ejecutamos*, esta propuesta
> define **como entendemos** al usuario: una capa de comprension de lenguaje natural
> que transforma requerimientos vagos en instrucciones precisas para el pipeline.

---

## 1. Resumen Ejecutivo

### 1.1 Problema

El bot RECPL actual procesa instrucciones en lenguaje natural mediante un pipeline
de compilador clasico (lexer → parser → semantico → IR → synthesis). Sin embargo,
su comprension del lenguaje es limitada:

| Limitacion | Ejemplo | Impacto |
|------------|---------|---------|
| **Solo comandos directos** | "crea modulo X en Y" | No entiende preguntas, descripciones vagas, ni requerimientos complejos |
| **Sin entendimiento de intencion** | "necesito gestionar usuarios" | No deduce que es un CRUD, no sugiere tecnologias |
| **Sin contexto multi-turno** | "crea modulo payments" → "agregale autenticacion" | No relaciona "agregale" con "payments" |
| **Sin manejo de ambiguedad** | "haz un modulo" (cual?) | No pregunta, falla silenciosamente |
| **Sin extraccion de requisitos** | "con base de datos y cache" | No extrae restricciones adicionales |
| **Sin deteccion de dominios** | "como configuro nestjs?" | Trata una pregunta como comando y falla |

### 1.2 Solucion Propuesta

Una **capa NLP + Intent** que se situa **antes del pipeline existente** y lo enriquece:

```
INPUT: "necesito un sistema de pagos con stripe en nestjs, que tenga autenticacion JWT"
  ↓
[ CAPA NLP + INTENT ]
  ├── Intent Classifier:  SCAFFOLD (0.92), QUERY (0.08)
  ├── NER Extractor:      entidades=[pagos], techs=[nestjs, stripe], reqs=[autenticacion JWT]
  ├── Ambiguity Detector: ninguna
  ├── Context Manager:    [turno 1] → historial=[]
  └── Dialog Manager:    → pasa directamente al pipeline
  ↓
[ PIPELINE EXISTENTE ] (preprocess → lexer → parser → semantic → IR → synthesis)
  ↓
OUTPUT: "Generando modulo Pagos con NestJS, integrando Stripe y JWT..."
```

Si la intencion es ambigua, el Dialog Manager toma control:

```
INPUT: "haz algo con usuarios"
  ↓
[ CAPA NLP + INTENT ]
  ├── Intent Classifier:  SCAFFOLD (0.45), QUERY (0.40), UNKNOWN (0.15)
  ├── Ambiguity Detector: intencion baja, entidad "usuarios" sin accion clara
  └── Dialog Manager:    → "¿Que quieres hacer con usuarios? Crear, modificar, eliminar, o listar?"
  ↓
INPUT2: "crearlos"
  ├── Context Manager:   entidad=usuarios (del turno anterior)
  ├── Intent Classifier: SCAFFOLD (0.95)
  └── Dialog Manager:    → pasa al pipeline con entidad completada
  ↓
OUTPUT: "Generando modulo Usuarios..."
```

### 1.3 Beneficios Esperados

| Escenario | Sin NLP | Con NLP | Mejora |
|-----------|---------|---------|--------|
| Comando directo ("crea modulo X") | OK | OK (igual) | — |
| Descripcion vaga ("necesito gestion de pagos") | Falla (error lexico) | Clasifica SCAFFOLD, extrae "pagos" | **De error a exito** |
| Pregunta ("como se configura nestjs?") | Falla (error sintactico) | Clasifica QUERY, responde guia | **De error a exito** |
| Multi-turno ("crea X" → "agregale Y") | Falla (referencia sin contexto) | Context Manager resuelve "le"→"X" | **De error a exito** |
| Requisitos complejos ("con auth y cache") | Ignora requisitos extra | Los extrae y pasa al IR | **Enriquecimiento** |
| Ambiguedad ("haz un modulo") | Falla o crea "un_modulo" | Pregunta "cual?" | **Claridad** |
| Prompt mal escrito ("crear... este... modulo") | Error lexico | Normaliza y deduce | **Resiliencia** |

---

## 2. Arquitectura de la Capa NLP + Intent

### 2.1 Vision General

```
┌──────────────────────────────────────────────────────────────────┐
│                    CAPA NLP + INTENT                              │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │   RAW INPUT   │───▶│   INTENT    │───▶│  NLP ENHANCER    │   │
│  │  (texto)      │    │ CLASSIFIER  │    │  (NER + slots)   │   │
│  └──────────────┘    └──────┬───────┘    └────────┬─────────┘   │
│                             │                      │             │
│                             ▼                      ▼             │
│                    ┌────────────────────────────────────┐        │
│                    │      AMBIGUITY & REQUIREMENT       │        │
│                    │          DETECTOR                 │        │
│                    └────────────────┬───────────────────┘        │
│                                     │                           │
│                    ┌────────────────▼───────────────────┐        │
│                    │         DIALOG MANAGER             │        │
│                    │  ┌────────────────────────────┐   │        │
│                    │  │  CLARIFICATION / SLOT       │   │        │
│                    │  │  FILLING / CONFIRMATION     │   │        │
│                    │  └────────────────────────────┘   │        │
│                    └────────────────┬───────────────────┘        │
│                                     │                           │
│                    ┌────────────────▼───────────────────┐        │
│                    │         CONTEXT MANAGER            │        │
│                    │  (historial, anáfora, defaults)    │        │
│                    └────────────────┬───────────────────┘        │
│                                     │                           │
└─────────────────────────────────────┼───────────────────────────┘
                                      │
                                      ▼
              ┌───────────────────────────────────────────┐
              │       PIPELINE EXISTENTE (recpl-core)      │
              │  preprocess → lexer → parser → semantic    │
              │  → IR → synthesis                          │
              └───────────────────────────────────────────┘
                                      │
                                      ▼
              ┌───────────────────────────────────────────┐
              │         ENRICHED IR + CONTEXT              │
              │  {accion, tipo, nombre, tech, requisitos,  │
              │   historial, confianza, dominio, ...}      │
              └───────────────────────────────────────────┘
```

### 2.2 Integracion con Pipeline Existente

La capa NLP + Intent no reemplaza el pipeline existente, sino que lo **antecede**
y lo **enriquece**:

```
FLUJO ACTUAL:
  INPUT → preprocess → lexer → parser → semantic → IR → synthesis → OUTPUT

FLUJO PROPUESTO (modo directo):
  INPUT → [NLP LAYER] → enriched_input.json → preprocess → lexer → parser → semantic
          → enriched_IR → synthesis → OUTPUT + contexto_actualizado

FLUJO PROPUESTO (modo dialogo):
  INPUT → [NLP LAYER] → [ambigüedad?] → [DIALOG MANAGER] → pregunta al usuario
          → [respuesta del usuario] → [CONTEXT MANAGER] resuelve
          → enriched_input.json → pipeline existente
```

La capa NLP produce un **`enriched_input.json`** que el pipeline existente consume:

```json
{
  "raw": "necesito un sistema de pagos con stripe en nestjs",
  "intent": {
    "primary": "scaffold",
    "secondary": null,
    "confidence": 0.92,
    "domain": "backend"
  },
  "entities": {
    "modulos": ["pagos"],
    "techs": ["nestjs", "stripe"],
    "requisitos": [
      {"tipo": "integracion", "valor": "stripe"},
      {"tipo": "autenticacion", "valor": null}
    ]
  },
  "slots": {
    "accion": "create",
    "tipo": "module",
    "nombre": "pagos",
    "tech": "nestjs",
    "completado": true
  },
  "ambiguity": {
    "detected": false,
    "elementos": []
  },
  "context": {
    "turno": 1,
    "historial": [],
    "defaults": {"tech": "nestjs"}
  },
  "dominio": "scaffolding"
}
```

### 2.3 Modos de Operacion

La capa NLP opera en tres modos:

| Modo | Descripcion | Activacion |
|------|-------------|------------|
| **Directo** | Intencion clara, pasa directamente al pipeline | confidence >= 0.8 |
| **Dialogo** | Intencion baja o slots incompletos → pregunta al usuario | 0.4 < confidence < 0.8 |
| **Derivacion** | No es comando → responde con informacion | confidence <= 0.4 (QUERY) |

---

## 3. Componentes Detallados

### 3.1 Intent Classifier

Clasificador de intenciones basado en reglas + patrones + scoring.
Determina **que** quiere hacer el usuario.

#### Taxonomia de Intenciones

| Intencion | Descripcion | Ejemplos | Accion derivada |
|-----------|-------------|----------|-----------------|
| `SCAFFOLD` | Crear/Generar algo nuevo | "crea modulo", "necesito un crud", "haz un servicio de auth" | CREATE |
| `QUERY` | Preguntar/Consultar informacion | "como se configura?", "que es un modulo?", "muestra los existentes" | READ / INFO |
| `MODIFY` | Cambiar/Actualizar existente | "agrega auth a payments", "cambia la DB a postgres" | UPDATE |
| `DELETE` | Eliminar algo | "borra modulo X", "elimina la entidad Y" | DELETE |
| `EXPLORE` | Navegar/Listar estructura | "que modulos tengo?", "listame los proyectos" | READ (lista) |
| `CONFIGURE` | Cambiar configuracion del bot | "usa prisma por defecto", "cambia a ingles" | CONFIG |
| `META` | Comandos del sistema | "help", "version", "status", "salir" | META |
| `CLARIFY` | Respuesta a pregunta del bot | "si", "no", "el de usuarios", "con postgres" | (completa slot) |
| `UNKNOWN` | No se puede determinar | "hola", "que tal", texto irrelevante | Dialogo / Ignorar |

#### Algoritmo de Clasificacion

```sh
# classify_intent.sh - Clasificador de intenciones basado en patrones
#
# Entrada: texto normalizado (stdin)
# Salida: JSON con intencion primaria, secundaria y confianza
#
# ALGORITMO:
#   1. Match contra patrones de cada intencion
#   2. Cada patron produce un score parcial
#   3. Normalizar scores a [0.0, 1.0]
#   4. Si hay empate (< 0.1 diferencia): marcar como ambigüo
#   5. Si score maximo < 0.3: UNKNOWN
#   6. Devolver top-2 intenciones

PATRONES_SCAFFOLD="crea|genera|nuev[oa]|necesit[ao]|quier[eo]|haz|construye|implementa|anade"
PATRONES_QUERY="como|que.e|que.s|explica|configura|ayuda|help|que.es|muestra|listame"
PATRONES_MODIFY="actualiza|cambia|modifica|agrega|aniade|edita|update"
PATRONES_DELETE="borra|elimina|remove|delete|saca|quita"
PATRONES_EXPLORE="que.modulos|listame|que.tengo|estado|status"
PATRONES_CONFIGURE="configura|usa|por.defecto|cambia.idioma|set"
PATRONES_META="^(help|version|salir|quit|status|estado)$"
PATRONES_CLARIFY="^(si|no|sí|ok|vale)$|el.de|con."
```

#### Salida del Clasificador

```json
{
  "intent": {
    "primary": "scaffold",
    "secondary": null,
    "confidence": 0.92,
    "scores": {
      "scaffold": 0.92,
      "query": 0.05,
      "modify": 0.02,
      "unknown": 0.01
    }
  },
  "dominio": "backend"
}
```

### 3.2 NLP Enhancer — Reconocimiento de Entidades (NER)

Extrae entidades nombradas, tecnologias, requisitos y relaciones del texto.

#### Tipos de Entidades

| Tipo | Descripcion | Ejemplos |
|------|-------------|----------|
| `MODULO` | Nombre de modulo/entidad a crear | "pagos", "usuarios", "auth", "inventory" |
| `TECH` | Stack tecnologico | "nestjs", "prisma", "react", "postgres", "stripe" |
| `REQUISITO` | Requisito funcional o tecnico | "autenticacion JWT", "cache", "logging", "tests" |
| `ATRIBUTO` | Caracteristica de entidad | "crud", "rest", "graphql", "microservicio" |
| `RELACION` | Relacion entre entidades | "depende de", "hereda de", "se conecta a" |
| `CANTIDAD` | Numero o cardinalidad | "tres tablas", "5 endpoints", "varios modulos" |
| `NEGACION` | Negacion explicita | "sin auth", "no uses redis" |

#### Algoritmo de Extraccion

```sh
# extract_entities.sh - Extractor de entidades nombradas
#
# Fases:
#   1. Detectar multi-word entities (bigramas/trigramas conocidos)
#      "gestor de pagos" → entidad compuesta "gestor_pagos"
#      "autenticacion JWT" → requisito "autenticacion_jwt"
#
#   2. Extraer TECH de lista blanca (extendida de 011 + 013)
#      Techs conocidas: NestJS, Prisma, Express, FastAPI, React, Vue,
#      Postgres, MongoDB, Docker, K8s, GraphQL, NextJS, Django, Flask,
#      Spring, Gin, Svelte, Redis, Stripe, JWT, TypeORM, Sequelize
#
#   3. Extraer entidades no tech
#      Palabras con mayuscula, o en posicion de entidad (tras accion+modulo)
#      Bigramas: "gestion de inventarios" → "gestion_inventarios"
#
#   4. Extraer requisitos con patrones
#      "con <requisito>" → requisito
#      "que tenga <requisito>" → requisito
#      "usando <requisito>" → requisito
#      "sin <requisito>" → requisito (negado)
#
#   5. Detectar relaciones entre entidades
#      "<entidad> depende de <entidad>" → relacion
#      "<entidad> usa <entidad>" → relacion
```

#### Salida del NER

```json
{
  "entities": {
    "modulos": [
      {"nombre": "pagos", "tipo": "module", "multi_word": false}
    ],
    "techs": [
      {"nombre": "nestjs", "rol": "framework"},
      {"nombre": "stripe", "rol": "integracion"}
    ],
    "requisitos": [
      {"tipo": "integracion", "valor": "stripe", "negado": false},
      {"tipo": "autenticacion", "valor": "jwt", "negado": false}
    ],
    "atributos": [],
    "relaciones": [],
    "negaciones": []
  }
}
```

### 3.3 Slot Filler — Completitud de Comandos

Determina si la instruccion tiene todos los campos necesarios para ejecutarse.
Si faltan slots, pasa al Dialog Manager.

#### Slots Requeridos por Intencion

| Intencion | Slots requeridos | Slots opcionales |
|-----------|-----------------|------------------|
| SCAFFOLD | accion, tipo, nombre | tech, requisitos, atributos |
| MODIFY | accion, nombre | tech, requisitos |
| DELETE | accion, nombre | — |
| QUERY | dominio | entidad, aspecto |
| EXPLORE | — | tipo, dominio |
| CONFIGURE | parametro, valor | — |
| META | comando | — |

#### Algoritmo de Slot Filling

```sh
# fill_slots.sh - Completador de slots
#
# Entrada: JSON del Intent Classifier + NER
# Salida: JSON con slots completados o incompletos
#
# Para SCAFFOLD:
#   slot_accion    = inferir de intencion primaria (si no hay accion en texto)
#   slot_tipo      = entity | module (inferir de patrones como "modulo", "entidad")
#   slot_nombre    = primera entidad extraida (o pedir en dialogo)
#   slot_tech      = primera tech encontrada (o default de contexto)
#   slot_req       = lista de requisitos extraidos
#   completado     = true si tiene accion + tipo + nombre
#
# Si !completado:
#   determinar que slot falta
#   preparar pregunta para Dialog Manager
```

#### Salida del Slot Filler

```json
{
  "slots": {
    "accion": "create",
    "tipo": "module",
    "nombre": "pagos",
    "tech": "nestjs",
    "requisitos": ["stripe", "jwt"],
    "completado": true,
    "faltantes": []
  }
}
```

Si faltan slots:

```json
{
  "slots": {
    "accion": "create",
    "tipo": "module",
    "nombre": null,
    "tech": "nestjs",
    "requisitos": [],
    "completado": false,
    "faltantes": ["nombre"]
  }
}
```

### 3.4 Ambiguity Detector

Detecta situaciones donde la intencion o las entidades no estan claras.

#### Casos de Ambiguedad

| Tipo | Descripcion | Ejemplo | Resolucion |
|------|-------------|---------|------------|
| **Intencion baja** | Ninguna intencion supera 0.6 | "haz algo" | Preguntar intencion |
| **Multi-intencion** | Dos intenciones con score similar | "crea y muestra" | Preguntar prioridad |
| **Entidad ambigua** | Entidad puede ser modulo o tech | "stripe" (modulo? tech?) | Preguntar tipo |
| **Referencia pendiente** | Pronombre sin antecedente | "agregale auth" (a que?) | Preguntar referencia |
| **Multi-entidad** | Muchas entidades sin relacion clara | "crea modulos de usuarios, pagos, auth con postgres y redis" | Confirmar relacion |
| **Inconsistencia** | Requisitos contradictorios | "con sql y mongodb" | Alertar inconsistencia |

#### Algoritmo de Deteccion

```sh
# detect_ambiguity.sh - Detector de ambiguedades
#
# Entrada: JSON del classifier + NER + slots
# Salida: JSON con elementos ambiguos
#
# 1. Revisar confidence del intent principal
#    Si < 0.6: marcar como "intencion_baja"
#    Si diferencia top2 < 0.1: marcar como "multi_intencion"
#
# 2. Revisar slots incompletos
#    Si hay faltantes: marcar como "slot_faltante"
#
# 3. Revisar referencias pronominales
#    Si hay "lo", "le", "la", "ello", "eso": buscar antecedente
#    Si no hay antecedente en historial: marcar "referencia_pendiente"
#
# 4. Revisar inconsistencias
#    Techs incompatibles: mongo + postgres juntos sin contexto
#    Atributos contradictorios
#
# 5. Generar mensaje de clarificacion
```

#### Salida del Detector

```json
{
  "ambiguity": {
    "detected": true,
    "severidad": "media",
    "elementos": [
      {
        "tipo": "intencion_baja",
        "descripcion": "No se puede determinar la intencion principal",
        "opciones": ["scaffold", "query", "modify"],
        "sugerencia": "¿Quieres crear, consultar o modificar algo?"
      }
    ]
  }
}
```

### 3.5 Dialog Manager

Gestiona la interaccion multi-turno cuando hay ambiguedad o slots faltantes.

#### Maquina de Estados del Dialogo

```
                   ┌───────────┐
                   │  INIT     │
                   └─────┬─────┘
                         │
                  ┌──────▼──────┐
                  │  ANALYZE    │ ← Intent Classifier + NER + Slots
                  └──────┬──────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │ DIRECT  │ │ DIALOG  │ │ DERIVE  │
        │ (conf   │ │ (ambig  │ │ (QUERY) │
        │  >= 0.8)│ │  o slots│ │         │
        └────┬────┘ │  vacios)│ └────┬────┘
             │      └────┬────┘      │
             │           │           │
             ▼           ▼           ▼
        ┌─────────┐ ┌─────────┐ ┌─────────┐
        │ EXECUTE │ │ CLARIFY │ │ RESPOND │
        │ (pipe   │ │ (pregun │ │ (info)  │
        │  normal)│ │  ta al  │ │         │
        │         │ │  user)  │ │         │
        └─────────┘ └────┬────┘ └─────────┘
                         │
                    ┌────▼────┐
                    │ AWAIT   │ ← espera input del usuario
                    │ INPUT   │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │ RESOLVE │ ← Context Manager resuelve
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │ EXECUTE │
                    └─────────┘
```

#### Estrategias de Clarificacion

| Situacion | Estrategia | Ejemplo |
|-----------|------------|---------|
| Intencion baja | Preguntar intencion general | "No entiendo bien que quieres hacer. ¿Quieres crear algo, consultar, modificar o eliminar?" |
| Slot nombre faltante | Preguntar nombre | "¿Como se llama el modulo que quieres crear?" |
| Slot tech faltante | Usar default o preguntar | "Usare NestJS por defecto. ¿Quieres otra tecnologia?" |
| Referencia ambigua | Preguntar antecedente | "¿A que modulo quieres agregarle autenticacion?" |
| Multi-entity sin relacion | Pedir aclarar relacion | "Detecte varias entidades: usuarios, pagos, auth. ¿Son modulos separados o partes de un mismo sistema?" |
| Confirmacion destructiva | Pedir confirmacion | "Vas a eliminar el modulo 'payments'. ¿Estas seguro?" |

### 3.6 Context Manager

Mantiene estado entre turnos de conversacion y resuelve referencias.

#### Estado del Contexto

```json
{
  "context": {
    "turno": 3,
    "session_id": "sess_abc123",
    "historial": [
      {
        "turno": 1,
        "input": "crea modulo pagos en nestjs",
        "intent": "scaffold",
        "slots": {"accion": "create", "tipo": "module", "nombre": "pagos", "tech": "nestjs"},
        "resultado": "ok",
        "timestamp": "..."
      },
      {
        "turno": 2,
        "input": "agregale autenticacion JWT",
        "intent": "modify",
        "slots": {"accion": "update", "nombre": "pagos", "requisitos": ["autenticacion JWT"]},
        "resolved_ref": true,
        "timestamp": "..."
      }
    ],
    "ultima_entidad": "pagos",
    "ultimo_intent": "modify",
    "defaults": {
      "tech": "nestjs",
      "tipo_modulo": "module"
    },
    "session_vars": {
      "modulos_creados": ["pagos"],
      "techs_usadas": ["nestjs"]
    }
  }
}
```

#### Resolucion de Anaforas

```sh
# resolve_anaphora.sh - Resuelve referencias pronominales
#
# Entrada: texto del turno actual + contexto historial
# Salida: texto con referencias resueltas
#
# Reglas:
#   "le", "lo", "la" → ultima entidad mencionada
#   "eso", "ello"    → ultimo comando/completo
#   "ahi", "allí"    → ultimo contexto mencionado
#   "igual", "tambien" → replicar ultima accion con nueva entidad
#
# Ejemplo:
#   Turno 1: "crea modulo pagos en nestjs"
#   Turno 2: "agregale auth" → "agrega auth a pagos"  (resuelto)
#   Turno 3: "haz lo mismo con usuarios" → "crea modulo usuarios en nestjs" (resuelto)
```

### 3.7 Requirement Extractor

Extrae requisitos funcionales y tecnicos no estructurados del texto.

#### Patrones de Extraccion

| Patron | Tipo | Ejemplo |
|--------|------|---------|
| "con <algo>" | requisito positivo | "con autenticacion JWT" |
| "que tenga <algo>" | requisito positivo | "que tenga cache con redis" |
| "usando <algo>" | requisito tecnologico | "usando stripe para pagos" |
| "sin <algo>" | requisito negado | "sin base de datos" |
| "que soporte <algo>" | requisito funcional | "que soporte multi-idioma" |
| "que sea <algo>" | atributo | "que sea rest" |
| "integrado con <algo>" | integracion | "integrado con sendgrid" |

#### Salida del Extractor

```json
{
  "requisitos": [
    {"tipo": "integracion", "valor": "stripe", "negado": false, "confianza": 0.95},
    {"tipo": "autenticacion", "valor": "jwt", "negado": false, "confianza": 0.90},
    {"tipo": "cache", "valor": "redis", "negado": false, "confianza": 0.85},
    {"tipo": "db", "valor": "postgres", "negado": false, "confianza": 0.80}
  ],
  "atributos": [
    {"nombre": "arquitectura", "valor": "microservicio", "confianza": 0.70}
  ],
  "negaciones": []
}
```

---

## 4. Integracion con Propuestas Anteriores

### 4.1 Integracion con 011 (Multi-Tech-Stack)

El NER del NLP se beneficia directamente de los 18+ tech stacks definidos en 011:

| Componente 011 | Beneficio del NLP |
|----------------|-------------------|
| `stacks/registry.sh` | El NER usa registry.sh como lista blanca de techs conocidas |
| `stack.json` | Los requisitos extraidos se mapean a stacks disponibles |
| Resolucion de techs | El NLP puede sugerir techs basado en requisitos (ej: "con pagos" → sugiere Stripe) |

### 4.2 Integracion con 012 (Contratos y Grafo)

El Dialog Manager y Context Manager se integran con el ciclo de refinamiento:

| Componente 012 | Integracion |
|----------------|-------------|
| Ciclo de refinamiento | Dialog Manager propone refinamientos basados en slots faltantes |
| Grafo de dependencias | Context Manager mantiene estado del grafo entre turnos |
| Regeneracion parcial | NLP detecta que cambio y solo afecta a ese sub-grafo |
| Versionado | Context Manager asocia cada turno a una version del IR |

### 4.3 Integracion con 013 (C Core)

La capa NLP puede implementarse en dos niveles:

```
NIVEL 1 (shell, inmediato):
  Scripts shell que preceden a recpl-core
  classify_intent.sh → extract_entities.sh → fill_slots.sh → detect_ambiguity.sh
  → si OK: pipe a recpl-core --mode=full
  → si ambigüo: dialog_manager.sh (interactivo)

NIVEL 2 (C nativo, futuro):
  Modos nlp en recpl-core:
    recpl-core --mode=intent     → clasifica intencion
    recpl-core --mode=ner        → extrae entidades
    recpl-core --mode=slots      → completa slots
    recpl-core --mode=ambiguity  → detecta ambiguedad
    recpl-core --mode=nlp        → pipeline completo NLP
```

### 4.4 Diagrama de Flujo Integrado

```
INPUT: "necesito un crud de productos con auth y cache en nestjs"
  │
  ▼
[1. INTENT CLASSIFIER] ───────────── classifica_intent.sh
  │ SCAFFOLD (0.94)
  ▼
[2. NER EXTRACTOR] ───────────────── extract_entities.sh
  │ entidades: [productos]
  │ techs: [nestjs]
  │ requisitos: [auth, cache]
  ▼
[3. SLOT FILLER] ─────────────────── fill_slots.sh
  │ accion=create, tipo=entity, nombre=productos, tech=nestjs
  │ requisitos=[auth, cache], completado=true
  ▼
[4. AMBIGUITY DETECTOR] ──────────── detect_ambiguity.sh
  │ ninguna ambiguedad
  ▼
[5. ENRICHED INPUT] ──────────────── genera enriched_input.json
  │ pasa al pipeline
  ▼
[6. recpl-core --mode=full] ──────── pipeline existente (013)
  │ genera IR
  ▼
[7. SYNTHESIS + CONTEXT] ────────── synthesis.sh + context_manager.sh
  │ "Generando entidad Productos con NestJS,
  │  integrando autenticacion y cache..."
  │ contexto actualizado para siguiente turno
```

---

## 5. Flujo Detallado: Escenarios

### 5.1 Escenario Directo (Comando Completo)

```
USR> crea un modulo de pagos con stripe en nestjs

Intent Classifier:
  scaffold: 0.95
  query:    0.03
  unknown:  0.02

NER:
  modulo: "pagos"
  techs:  ["nestjs", "stripe"]
  reqs:   [stripe]

Slot Filler:
  accion=create, tipo=module, nombre=pagos
  tech=nestjs, reqs=[stripe]
  completado=true

Ambiguity: none

→ Pipeline: recpl-core --mode=full enriched_input.json
→ Respuesta: "Generando modulo Pagos con NestJS, integrando Stripe..."
→ Contexto: actualizado con entidad=pagos, tech=nestjs
```

### 5.2 Escenario Dialogo (Slots Incompletos)

```
USR> quiero un modulo

Intent Classifier:
  scaffold: 0.82
  query:    0.10
  unknown:  0.08

NER:
  (no entities, no techs)

Slot Filler:
  accion=create, tipo=module
  nombre=null, tech=null
  completado=false
  faltantes=["nombre", "tech"]

Ambiguity: slot_faltante

→ Dialog Manager: "¿Como se llama el modulo que quieres crear?"

USR> pagos

Context Manager:
  ← turno anterior: scaffold + module + null + null
  + turno actual: "pagos" → slot nombre=pagos (CLARIFY intent)

Slot Filler:
  completado=false (falta tech)
  faltantes=["tech"]

→ Dialog Manager: "Usare NestJS por defecto. ¿Quieres otra tecnologia?"

USR> no, esta bien

→ confirmado: tech=nestjs (default)
→ Pipeline: recpl-core --mode=full
→ Respuesta: "Generando modulo Pagos en NestJS..."
```

### 5.3 Escenario Derivacion (Pregunta)

```
USR> como se configura nestjs con prisma?

Intent Classifier:
  query:    0.91
  scaffold: 0.05
  unknown:  0.04

NER:
  techs: ["nestjs", "prisma"]
  dominio: "configuracion"

→ Dialog Manager: QUERY → no pasa a pipeline
→ Response: "Para configurar NestJS con Prisma:
   1. npm install @prisma/client
   2. npx prisma init
   3. Configurar schema.prisma
   4. npx prisma generate
   ¿Quieres que genere la configuracion por ti?"
```

### 5.4 Escenario Multi-Turno con Referencia

```
T1: USR> crea modulo payments en nestjs
    → scaffold modulo payments
    → "Generando modulo Payments en NestJS..."
    → contexto: ultima_entidad=payments, tech=nestjs

T2: USR> agregale autenticacion JWT
    Intent Classifier:
      modify: 0.88
    Context Manager:
      "le" → payments (resuelto)
    →
    → "Agregando autenticacion JWT al modulo Payments..."
    → contexto: ultima_entidad=payments, ultimo_intent=modify

T3: USR> haz lo mismo con usuarios
    Context Manager:
      "lo mismo" → scaffold + module + nestjs (del turno T1)
      "usuarios" → nueva entidad
    →
    → "Generando modulo Usuarios en NestJS..."
```

### 5.5 Escenario Ambiguedad Alta

```
USR> haz algo

Intent Classifier:
  scaffold: 0.35
  query:    0.30
  modify:   0.20
  unknown:  0.15

→ Ambiguity: intencion_baja (max < 0.6)
→ Dialog Manager: "No entiendo bien que quieres hacer.
   ¿Quieres crear algo nuevo, consultar informacion,
   modificar algo existente, o eliminar algo?"

USR> crear

→ CLARIFY: intent=scaffold confirmado
→ Dialog Manager: "¿Que quieres crear? ¿Un modulo, una entidad, o un proyecto completo?"

USR> un modulo de productos

→ SCAFFOLD + entidad=productos + tipo=module
→ Dialog Manager: "¿En que tecnologia? (NestJS, Prisma, Express, FastAPI...)"

USR> nestjs

→ Pipeline: recpl-core --mode=full
→ "Generando modulo Productos en NestJS..."
```

---

## 6. Tabla de Tareas

| ID | Tarea | Modulo | Depende de | Esfuerzo | Estado |
|----|-------|--------|------------|----------|--------|
| NLP-001 | Crear `classify_intent.sh` — clasificador de intenciones con patrones y scoring | intent | — | L | pending |
| NLP-002 | Definir taxonomia completa de intenciones y sus patrones | intent | NLP-001 | M | pending |
| NLP-003 | Implementar scoring normalizado y deteccion de multi-intencion | intent | NLP-001 | M | pending |
| NLP-004 | Implementar deteccion de dominio (backend/frontend/infra/consulta) | intent | NLP-001 | S | pending |
| NLP-005 | Crear `extract_entities.sh` — extractor NER basado en listas blancas y patrones | ner | — | L | pending |
| NLP-006 | Implementar deteccion de multi-word entities (bigramas/trigramas) | ner | NLP-005 | M | pending |
| NLP-007 | Implementar extraccion de techs desde registry.sh (lista blanca de 011) | ner | NLP-005, 011-FASE-E1 | M | pending |
| NLP-008 | Implementar extraccion de requisitos con patrones ("con", "que tenga", "usando") | ner | NLP-005 | L | pending |
| NLP-009 | Implementar deteccion de negacion ("sin", "no uses") | ner | NLP-005 | S | pending |
| NLP-010 | Crear `fill_slots.sh` — completador de slots por intencion | slots | NLP-001, NLP-005 | L | pending |
| NLP-011 | Definir slots requeridos/opcionales por tipo de intencion | slots | NLP-010 | M | pending |
| NLP-012 | Implementar inferencia de slots desde contexto (turnos anteriores) | slots | NLP-010 | M | pending |
| NLP-013 | Crear `detect_ambiguity.sh` — detector de ambiguedades | ambiguity | NLP-001, NLP-005, NLP-010 | L | pending |
| NLP-014 | Implementar deteccion de intencion baja (< 0.6) | ambiguity | NLP-013 | M | pending |
| NLP-015 | Implementar deteccion de referencias pronominales ("lo", "le", "la") | ambiguity | NLP-013 | M | pending |
| NLP-016 | Implementar deteccion de inconsistencias (techs incompatibles) | ambiguity | NLP-013 | S | pending |
| NLP-017 | Crear `dialog_manager.sh` — maquina de estados del dialogo | dialog | NLP-013 | XL | pending |
| NLP-018 | Implementar estado CLARIFY (preguntar al usuario) | dialog | NLP-017 | M | pending |
| NLP-019 | Implementar estrategias de clarificacion por tipo de ambiguedad | dialog | NLP-017 | L | pending |
| NLP-020 | Implementar confirmacion antes de acciones destructivas (DELETE) | dialog | NLP-017 | M | pending |
| NLP-021 | Crear `context_manager.sh` — gestor de contexto multi-turno | context | — | L | pending |
| NLP-022 | Implementar historial de turnos con persistencia (RECPL_STATE_DIR) | context | NLP-021 | M | pending |
| NLP-023 | Implementar resolucion de anaforas (referencias a entidades previas) | context | NLP-021 | L | pending |
| NLP-024 | Implementar defaults contextuales (ultima tech usada, ultimo tipo) | context | NLP-021 | M | pending |
| NLP-025 | Crear `requirement_extractor.sh` — extractor de requisitos no estructurados | reqs | NLP-005 | M | pending |
| NLP-026 | Implementar mapeo de requisitos a configuracion de stacks (011) | reqs | NLP-025, 011-FASE-E1 | M | pending |
| NLP-027 | Crear `enriched_input.json` — formato de entrada enriquecida para el pipeline | integration | NLP-001..NLP-026 | M | pending |
| NLP-028 | Modificar `recpl.sh` para integrar capa NLP antes del pipeline | integration | NLP-027 | L | pending |
| NLP-029 | Implementar modo directo (confidence >= 0.8 → pipeline inmediato) | integration | NLP-028 | M | pending |
| NLP-030 | Implementar modo dialogo (confidence < 0.8 → dialog manager) | integration | NLP-028 | M | pending |
| NLP-031 | Implementar modo derivacion (QUERY → responder sin pipeline) | integration | NLP-028 | M | pending |
| NLP-032 | Integrar con recpl-core (013) para que `--mode=full` acepte enriched_input | integration | NLP-028, 013-FASE-C6 | L | pending |
| NLP-033 | Tests unitarios: classify_intent (15 casos) | testing | NLP-003 | L | pending |
| NLP-034 | Tests unitarios: extract_entities (15 casos) | testing | NLP-008 | L | pending |
| NLP-035 | Tests unitarios: fill_slots (10 casos) | testing | NLP-010 | M | pending |
| NLP-036 | Tests unitarios: detect_ambiguity (10 casos) | testing | NLP-013 | M | pending |
| NLP-037 | Tests unitarios: dialog_manager (10 casos multi-turno) | testing | NLP-017 | L | pending |
| NLP-038 | Tests unitarios: context_manager (10 casos de anáfora) | testing | NLP-023 | L | pending |
| NLP-039 | Tests de integracion: pipeline completo NLP + RECPL (10 escenarios) | testing | NLP-028 | L | pending |
| NLP-040 | Validar con `bash -n` y `shellcheck` todos los scripts nuevos | quality | NLP-028 | S | pending |
| NLP-041 | Documentar API de la capa NLP (formatos, modos, ejemplos) | docs | NLP-028 | M | pending |
| NLP-042 | Actualizar runbook (010) con seccion de NLP e Intent | docs | NLP-041 | M | pending |

---

## 7. Fases de Implementacion

| Fase | Nombre | Descripcion | Tareas | Depende de | Duracion est. |
|------|--------|-------------|--------|------------|---------------|
| **FASE-N1** | Fundacion NLP | Intent Classifier + NER basico | NLP-001 al NLP-009 | — | 5-7 dias |
| **FASE-N2** | Slots y Ambiguedad | Slot Filler + Ambiguity Detector | NLP-010 al NLP-016 | FASE-N1 | 4-5 dias |
| **FASE-N3** | Dialogo y Contexto | Dialog Manager + Context Manager | NLP-017 al NLP-024 | FASE-N2 | 5-7 dias |
| **FASE-N4** | Requisitos y Enriquecimiento | Requirement Extractor + enriched_input | NLP-025 al NLP-027 | FASE-N1 | 3-4 dias |
| **FASE-N5** | Integracion con Pipeline | Modificar recpl.sh, modos directo/dialogo/derivacion | NLP-028 al NLP-032 | FASE-N3, FASE-N4 | 4-5 dias |
| **FASE-N6** | Tests y Hardening | Tests unitarios, integracion, shellcheck | NLP-033 al NLP-040 | FASE-N5 | 4-5 dias |
| **FASE-N7** | Documentacion | Documentacion de API y runbook | NLP-041, NLP-042 | FASE-N6 | 1-2 dias |

### Grafo de Dependencias entre Fases

```
FASE-N1 (Fundacion NLP)
  │
  ├──────────────────────┐
  ▼                      ▼
FASE-N2 (Slots y      FASE-N4 (Requisitos)
  Ambiguedad)
  │                      │
  ▼                      │
FASE-N3 (Dialogo y      │
  Contexto)              │
  │                      │
  └──────────┬───────────┘
             ▼
        FASE-N5 (Integracion)
             │
             ▼
        FASE-N6 (Tests)
             │
             ▼
        FASE-N7 (Docs)
```

### Relacion con Fases de 011, 012, 013

| Fase externa | Relacion | Tareas NLP |
|--------------|----------|------------|
| 011-FASE-E1 (Stack Registry) | NER usa registry.sh como lista blanca | NLP-007 |
| 011-FASE-E3 (Parser Multi-Stack) | enriched_input alimenta al parser extendido | NLP-027 |
| 012-FASE-F1 (Contratos) | Requisitos extraidos se mapean a contratos | NLP-026 |
| 012-FASE-F4 (API Refinamiento) | Dialog Manager maneja el ciclo de refinamiento | NLP-017..NLP-020 |
| 013-FASE-C6 (Modo Full) | recpl-core acepta enriched_input.json | NLP-032 |
| 013-FASE-C8 (Daemon Server) | Daemon sirve sesiones NLP con contexto persistente | NLP-021..NLP-024 |

---

## 8. Estructura de Directorios (Nuevos Archivos)

```
compiler-bot/
├── nlp/                              # NUEVO: capa NLP + Intent
│   ├── classify_intent.sh            # Clasificador de intenciones
│   ├── extract_entities.sh           # Extractor NER
│   ├── fill_slots.sh                 # Completador de slots
│   ├── detect_ambiguity.sh           # Detector de ambiguedades
│   ├── dialog_manager.sh             # Maquina de estados del dialogo
│   ├── context_manager.sh            # Gestor de contexto multi-turno
│   ├── requirement_extractor.sh      # Extractor de requisitos
│   ├── enrich_input.sh               # Genera enriched_input.json
│   ├── lib/
│   │   ├── patterns.sh               # Patrones de intenciones y entidades
│   │   ├── scoring.sh                # Funciones de scoring normalizado
│   │   ├── anaphora.sh               # Resolucion de anaforas
│   │   └── defaults.sh              # Valores por defecto y configuracion
│   └── tests/
│       ├── test_classify_intent.sh
│       ├── test_extract_entities.sh
│       ├── test_fill_slots.sh
│       ├── test_detect_ambiguity.sh
│       ├── test_dialog_manager.sh
│       ├── test_context_manager.sh
│       └── run_nlp_tests.sh
├── recpl.sh                           # MODIFICADO: integra capa NLP
└── core/                              # Existente (013)
    └── ... (futuros modos nlp en C)
```

---

## 9. Stack Tecnologico

| Tecnologia | Uso | Version | Nota |
|------------|-----|---------|------|
| Shell POSIX | Scripts de la capa NLP | Cualquier Unix | Misma convencion que el resto del proyecto |
| awk | Procesamiento de patrones, scoring, NER | nawk/gawk | Sin cambios respecto al pipeline actual |
| sed | Transformaciones de texto, normalizacion | POSIX sed | Sin cambios |
| RECPL_STATE_DIR | Persistencia de contexto multi-turno | — | Misma variable que semantic.sh |
| `bash -n` | Validacion de sintaxis | Bash 3+ | Convocion existente |
| shellcheck | Analisis estatico | 0.7+ | Convocion existente |

**Nota:** La capa NLP se implementa inicialmente en shell puro (sin dependencias externas)
para mantener la compatibilidad con el ecosistema existente. Futuras optimizaciones
pueden migrar componentes a C siguiendo el patron de 013.

---

## 10. Riesgos y Mitigaciones

| Riesgo | Impacto | Probabilidad | Mitigacion |
|--------|---------|--------------|------------|
| Falsos positivos en clasificacion de intencion | Alto (ejecuta accion equivocada) | Media | Threshold minimo de 0.8 para modo directo; modo dialogo siempre pide confirmacion |
| Falsos negativos (no detecta intencion valida) | Medio (frustracion de usuario) | Media | Modo derivacion para QUERY; Dialog Manager ofrece opciones en vez de fallar |
| Contexto corrupto entre turnos | Alto | Baja | Validacion de integridad del JSON de contexto; fallback a estado fresco |
| Ambiguedad no resuelta en dialogo | Medio | Baja | Si tras 3 rondas de clarificacion no se resuelve: "No puedo procesar esa solicitud. Intenta reformularla." |
| Crecimiento excesivo del historial | Bajo (rendimiento) | Alta | Limitar historial a ultimos 20 turnos; rotacion con `tail` |
| Bashisms en scripts (incompatibilidad POSIX) | Medio | Media | `shellcheck` con perfil POSIX; pruebas en `/bin/sh` |
| Dependencia de registry.sh (011) | Medio | Baja | Fallback si no existe: lista blanca interna en patterns.sh |

---

## 11. Metricas de Exito

| KPI | Target | Como se mide |
|-----|--------|-------------|
| Precision de clasificacion de intencion | > 90% | Tests con 50 casos etiquetados manualmente |
| Tasa de exito en modo directo | > 80% de inputs pasan sin dialogo | Logging de modo vs cantidad total de prompts |
| Reduccion de errores lexicos/sintacticos | > 50% menos que sin NLP | Comparar logs de error antes/despues |
| Tasa de resolucion de ambiguedad | > 85% en ≤ 2 rondas de clarificacion | Tests multi-turno |
| Precision de resolucion de anaforas | > 90% | Tests de contexto con 20 casos |
| Tiempo de procesamiento NLP | < 20ms (shell) / < 1ms (C futuro) | `time` en scripts; `hyperfine` en binario |
| Tests pasando | 100% (70+ tests) | `run_nlp_tests.sh` |
| shellcheck | 0 warnings | `shellcheck nlp/*.sh` |

---

## 12. Casos de Uso (Resumen)

| ID | Descripcion | Input | Output esperado |
|----|-------------|-------|-----------------|
| CU-01 | Comando directo completo | "crea modulo pagos en nestjs" | Pipeline directo, "Generando modulo Pagos..." |
| CU-02 | Descripcion vaga | "necesito gestion de usuarios" | Clasifica SCAFFOLD, pide detalles |
| CU-03 | Pregunta tecnica | "como configuro prisma?" | Responde guia, ofrece generar config |
| CU-04 | Multi-turno con referencia | "crea X" → "agregale Y" | Contexto resuelve "le", aplica MODIFY a X |
| CU-05 | Multi-turno con "lo mismo" | "crea X en T" → "haz lo mismo con Y" | Contexto replica accion con nueva entidad |
| CU-06 | Requisitos complejos | "crud de productos con auth y cache en nestjs" | Extrae requisitos, los pasa al IR |
| CU-07 | Intencion ambigua | "haz algo" | Dialog Manager pregunta "Que quieres hacer?" |
| CU-08 | Multi-entity | "crea modulos de users, posts, comments" | Detecta multiples entidades, pregunta relacion |
| CU-09 | Accion destructiva | "borra modulo payments" | Pide confirmacion antes de ejecutar |
| CU-10 | Sin tech especificada | "crea modulo test" | Usa default tech del contexto (o pregunta) |

---

## 13. Referencias

- `003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md` — Patrones de pipeline modular del procesador de documentos
- `004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md` — Especificacion con requerimientos, fases, metricas
- `006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md` — Arquitectura original del bot RECPL
- `011_PROP_DEV_COMPILER_BOT_EXTENDED_1_0_DRAFT.md` — Multi-tech-stack y UI web
- `012_PROP_DEV_COMPILER_BOT_FLOW_REFINE_1_0_DRAFT.md` — Flujo de datos y ciclo de refinamiento
- `013_PROP_DEV_COMPILER_BOT_C_CORE_1_0_DRAFT.md` — Nucleo C nativo (recpl-core)
- `000_DEV_GUIDE_SHELL_STYLE_1_0_DRAFT.md` — Guia de estilo shell
- `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md` — Convencion de documentacion
