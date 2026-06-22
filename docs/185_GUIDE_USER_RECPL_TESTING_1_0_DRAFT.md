---
id: 185
area: user
type: guide
module: recpl_testing
version: 1.0
status: DRAFT
tags:
  - user
  - guide
  - testing
  - tutorial
  - recpl
  - cli
summary: "Guia de prueba del sistema RECPL para usuario final. Recorre todos los modos de operacion: CLI directo, --ir-only, modo debug, dashboard, metricas, prompt chain y prompts de ejemplo."
keywords:
  - guia
  - testing
  - usuario
  - recpl
  - cli
  - ir-only
  - dashboard
  - debug
  - metricas
  - prompt
changelog:
  - version: 1.0
    date: 2026-06-21
    author: workflow-agent
    description: Creacion de la guia de testing para usuario final
---

# Guia de Prueba: RECPL Compiler Bot v2.0

> **Sistema:** RECPL (READ-EVAL-PRINT Compiler Loop)
> **Version:** 2.9.0+
> **Proposito:** Compilador de lenguaje natural a codigo IR (Intermediate Representation) con
> generadores opcionales a NestJS, Prisma, React, NextJS, Tailwind y Docker.

---

## 1. Requisitos

- Python 3.11+
- pip

### Instalacion

```bash
# Desde la raiz del proyecto
pip install -e compiler-bot/agentic_pipeline/

# Verificar instalacion
compiler-bot/agentic --help
```

### Dependencias opcionales

| Funcionalidad | Dependencia | Instalacion |
|---|---|---|
| Clasificacion semantica | sentence-transformers | `pip install sentence-transformers` |
| Modo LLM | openai / anthropic | `pip install openai anthropic` |
| Pipeline prompt chain | langchain | `pip install langchain>=0.3.0` |
| Dashboard (SQLite) | _sqlite3 | incluido en stdlib |

---

## 2. Primeros pasos

### 2.1 Prompt directo

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos en NestJS"
```

**Salida esperada:** JSON con el resultado del pipeline completo (`output` + `success: true`).
El sistema genera los archivos NestJS del modulo en `modules/pagos/`.

### 2.2 Prompt desde archivo

```bash
echo "crea una entidad Usuario con nombre:string email:string" > prompt.txt
./compiler-bot/agentic --file prompt.txt
```

### 2.3 Directorio de salida personalizado

```bash
./compiler-bot/agentic -p "crea un modulo de pagos" -o ./mi_salida
```

### 2.4 Streaming de progreso

```bash
./compiler-bot/agentic -p "crea un modulo de pagos" --stream
```

Muestra en stderr cada etapa que se completa:

```
[intent_stage] completed
[preprocessor] completed
[lexer] completed
[parser] completed
[semantic_analyzer] completed
[ir_generator] completed
[planner] completed
[synthesis] completed
```

---

## 3. Modo solo IR (--ir-only)

Obtiene el IR canonico sin ejecutar generadores de codigo. Util para inspeccionar
como el sistema interpreta una instruccion.

```bash
./compiler-bot/agentic --prompt "crea un modulo de pagos" --ir-only
```

**Salida tipica:**

```json
{
  "output": {
    ...
    "ast": {
      "node_type": "project",
      "children": [
        {
          "node_type": "module",
          "name": "pagos",
          "type": "nestjs",
          "entities": [
            {
              "name": "Pago",
              "attributes": []
            }
          ]
        }
      ]
    },
    "commands": [
      {
        "task_id": "pagos",
        "type": "scaffold",
        "path": "modules/pagos"
      }
    ]
  },
  "success": true
}
```

**Caso de prueba:** Probar con distintos niveles de detalle:

```bash
# Basico
./compiler-bot/agentic -p "modulo usuarios" --ir-only

# Con entidades
./compiler-bot/agentic -p "crea entidad Producto con nombre:string precio:float" --ir-only

# Multiples modulos
./compiler-bot/agentic -p "crea un CRUD de facturas con NestJS y Postgres" --ir-only
```

---

## 4. Tipos de instrucciones

### 4.1 CREATE

```bash
# Modulo NestJS
./compiler-bot/agentic -p "crea un modulo de autenticacion en NestJS" --ir-only

# Entidad con atributos
./compiler-bot/agentic -p "crea entidad Usuario con nombre:string email:string edad:int" --ir-only

# Multiples modulos
./compiler-bot/agentic -p "crea modulos de pagos y usuarios con Prisma" --ir-only

# Full proyecto
./compiler-bot/agentic -p "crea un sistema de facturacion con NestJS, Prisma y Docker" --ir-only
```

### 4.2 READ (consulta)

```bash
# Solo se activa en modo agente completo con LLM
# El pipeline deterministico interpreta "muestra" como CREATE
./compiler-bot/agentic -p "muestra el contenido del modulo pagos" --ir-only
```

### 4.3 UPDATE (modificacion)

```bash
./compiler-bot/agentic -p "agrega un campo telefono a la entidad Usuario" --ir-only
```

### 4.4 DELETE (eliminacion)

```bash
./compiler-bot/agentic -p "elimina el modulo de pagos" --ir-only
```

### 4.5 EXPLAIN

```bash
./compiler-bot/agentic -p "explica como funciona el pipeline" --ir-only
```

---

## 5. Generacion de codigo (sin --ir-only)

Sin `--ir-only`, el sistema ejecuta los generadores y produce archivos reales.

### 5.1 NestJS

```bash
./compiler-bot/agentic -p "crea un modulo de pagos en NestJS"
ls modules/pagos/
# controller/  service/  module/  entity/
```

### 5.2 Prisma

```bash
./compiler-bot/agentic -p "crea un modelo Usuario y Factura con Prisma"
cat modules/prisma/schema.prisma
```

### 5.3 React

```bash
./compiler-bot/agentic -p "crea una pagina de login en React"
ls modules/login/
```

### 5.4 NextJS

```bash
./compiler-bot/agentic -p "crea un dashboard en NextJS"
ls modules/dashboard/
```

### 5.5 Docker

```bash
./compiler-bot/agentic -p "crea configuracion Docker para postgresql"
cat modules/docker/docker-compose.yml
```

### 5.6 Combinaciones

```bash
# NestJS + Prisma
./compiler-bot/agentic -p "crea un CRUD de productos con NestJS y Prisma"

# React + Tailwind
./compiler-bot/agentic -p "crea una pagina de inicio con React y Tailwind"

# Todo incluido
./compiler-bot/agentic -p "crea un sistema completo con NestJS, Prisma, React, Docker"
```

---

## 6. Modo debug

### 6.1 Trace

Muestra cada etapa del pipeline en detalle:

```bash
./compiler-bot/agentic -p "crea un modulo" --debug trace
```

### 6.2 Step

Pausa entre etapas (presiona Enter para continuar):

```bash
./compiler-bot/agentic -p "crea un modulo" --debug step
```

### 6.3 Timing

Muestra tiempo de ejecucion por etapa:

```bash
./compiler-bot/agentic -p "crea un modulo" --debug timing
```

**Salida tipica:**

```
=== Timing Report ===
intent: 0.023s
preprocessor: 0.015s
lexer: 0.008s
parser: 0.031s
semantic: 0.012s
ir_generator: 0.045s
planner: 0.009s
synthesis: 0.112s
Total: 0.255s
```

### 6.4 Inspect

Inspecciona datos intermedios entre etapas:

```bash
./compiler-bot/agentic -p "crea un modulo" --debug inspect --show-output
```

---

## 7. Modo prompt chain (--chain)

Ejecuta el pipeline via Chain of Responsibility con 6 handlers
(preprocess, intent, plan, generate, verify, format) y reintentos automaticos.

```bash
./compiler-bot/agentic -p "crea un modulo de pagos" --chain
```

El modo chain incluye verificacion y reintenta hasta 3 veces si falla.

---

## 8. Modo offline

Ejecuta sin llamadas LLM, solo heuristicas deterministicas:

```bash
./compiler-bot/agentic -p "crea un modulo de pagos" --offline
```

---

## 9. Dashboard de metricas

### 9.1 Iniciar servidor

```bash
./compiler-bot/agentic --dashboard
# Escuchando en http://127.0.0.1:8765
```

### 9.2 Opciones del servidor

```bash
# Puerto personalizado
./compiler-bot/agentic --dashboard --port 8080

# Host personalizado
./compiler-bot/agentic --dashboard --host 0.0.0.0
```

### 9.3 Metricas por CLI

```bash
# Resumen en JSON
./compiler-bot/agentic --metrics json

# Resumen en tabla
./compiler-bot/agentic --metrics table
```

**Salida tabla tipica:**

```
=== Pipeline Metrics Summary ===
Total records: 15
Total errors:  1
Success rate:  93.3%
Per-stage:
  intent_stage: 2 records
  preprocessor: 2 records
  lexer: 2 records
  parser: 2 records
  semantic_analyzer: 2 records
  ir_generator: 2 records
  planner: 2 records
  synthesis: 1 records

Prompt Chain per-stage:
  preprocess: 5 calls, 100% success, avg 0.5s
  intent: 5 calls, 100% success, avg 0.3s
  plan: 5 calls, 80% success, avg 1.2s
  generate: 5 calls, 100% success, avg 2.1s
  verify: 5 calls, 100% success, avg 0.8s
  format: 5 calls, 100% success, avg 0.1s

Overall success rate: 97%
Fallback rate: 5%
```

---

## 10. Pruebas de lenguaje

### 10.1 Variantes terminologicas

El sistema normaliza sinonimos comunes:

| Entrada | Interpretacion |
|---|---|
| `crea modulo X` | CREATE modulo X |
| `haz un modulo X` | CREATE modulo X |
| `genera X` | CREATE modulo X |
| `quiero un X` | CREATE modulo X |
| `necesito X` | CREATE modulo X |
| `construye X` | CREATE modulo X |

### 10.2 Articulos

Los articulos (un, una, el, la) se eliminan durante el preprocesado:

```bash
# Todas producen el mismo resultado
./compiler-bot/agentic -p "crea modulo pagos" --ir-only
./compiler-bot/agentic -p "crea un modulo de pagos" --ir-only
./compiler-bot/agentic -p "crea el modulo de pagos" --ir-only
```

### 10.3 Mayusculas/minusculas

El preprocesador convierte todo a minusculas:

```bash
# Equivalentes
./compiler-bot/agentic -p "CREA MODULO PAGOS" --ir-only
./compiler-bot/agentic -p "Crea Modulo Pagos" --ir-only
```

---

## 11. Escenarios de prueba completos

### 11.1 CRUD completo

```bash
# 1. Crear entidad
./compiler-bot/agentic -p "crea entidad Producto con nombre:string precio:float stock:int"

# 2. Crear modulo NestJS
./compiler-bot/agentic -p "crea un modulo NestJS para Producto"

# 3. Schema Prisma
./compiler-bot/agentic -p "crea modelo Prisma para Producto con nombre:string precio:float"

# 4. Frontend React
./compiler-bot/agentic -p "crea pagina de listado de productos en React"

# 5. Infra Docker
./compiler-bot/agentic -p "crea docker-compose con postgresql"
```

### 11.2 Proyecto completo

```bash
./compiler-bot/agentic -p "
  crea un sistema de gestion de tareas con:
  - modulo NestJS para tareas
  - entidades Tarea y Usuario con Prisma
  - frontend React con Tailwind
  - docker-compose con postgresql
"
```

### 11.3 Prueba de reintentos con --chain

```bash
# Ejecutar varias veces para ver metricas acumuladas
for i in 1 2 3; do
  ./compiler-bot/agentic -p "crea modulo test$i" --chain
done

# Ver metricas
./compiler-bot/agentic --metrics table
```

---

## 12. Comprobacion de estado del sistema

### 12.1 Verificar version

```bash
cat VERSION
# 2.9.0
```

### 12.2 Verificar metricas acumuladas

```bash
./compiler-bot/agentic --metrics json
```

### 12.3 Verificar dashboard

```bash
# En otra terminal:
./compiler-bot/agentic --dashboard
# Abrir en navegador: http://127.0.0.1:8765
```

El dashboard muestra:
- Total de registros procesados
- Tasa de exito/error
- Registros por stage (ordenable por columna)
- Detalle de cada registro

---

## 13. Solucion de problemas

### 13.1 Error: modulo no encontrado

```
ModuleNotFoundError: No module named 'agentic_pipeline'
```

**Solucion:** Reinstalar el paquete:

```bash
pip install -e compiler-bot/agentic_pipeline/
```

### 13.2 Error: _sqlite3 no disponible

```
_sqlite3 C module not available; falling back to JSON file store
```

**Solucion:** No es critico. El sistema usa JSON como fallback.
Para resolverlo, instalar sqlite3 en el sistema:

```bash
# Debian/Ubuntu
sudo apt install libsqlite3-dev
# Recompilar Python
```

### 13.3 Sin salida visible

Si el comando solo muestra `{"output": ..., "success": true}` y no ves
archivos generados, usa `--ir-only` para depurar primero:

```bash
./compiler-bot/agentic -p "<tu prompt>" --ir-only
```

Si el IR es correcto, ejecuta sin `--ir-only` y revisa `modules/`.

### 13.4 Prompt chain falla siempre

```bash
# Forzar modo deterministico
./compiler-bot/agentic -p "crea un modulo" --chain --offline
```

### 13.5 El dashboard no arranca

Verificar que el puerto no este ocupado:

```bash
lsof -i :8765
# Si ocupado, usar --port diferente
./compiler-bot/agentic --dashboard --port 9000
```

---

## 14. Referencia rapida de flags

| Flag | Descripcion | Ejemplo |
|---|---|---|
| `-p` / `--prompt` | Instruccion en lenguaje natural | `-p "crea modulo pagos"` |
| `-f` / `--file` | Leer prompt desde archivo | `-f prompt.txt` |
| `-o` / `--output` | Directorio de salida | `-o ./salida` |
| `--stream` | Mostrar progreso por etapa | `--stream` |
| `--ir-only` | Solo IR, sin generar codigo | `--ir-only` |
| `--debug` | Modo debug (trace/step/timing/inspect) | `--debug trace` |
| `--show-output` | Mostrar datos intermedios (con --debug) | `--debug inspect --show-output` |
| `--chain` | Pipeline Chain of Responsibility | `--chain` |
| `--offline` | Sin LLM, solo heuristicas | `--offline` |
| `--dialog` | Modo interactivo para prompts ambiguos | `--dialog` |
| `--metrics` | Resumen de metricas (json/table) | `--metrics table` |
| `--dashboard` | Iniciar servidor dashboard | `--dashboard` |
| `--host` | Host del dashboard | `--host 0.0.0.0` |
| `--port` | Puerto del dashboard | `--port 8080` |

---

## 15. Salida esperada del pipeline

El pipeline produce un JSON con esta estructura:

```json
{
  "output": {
    "normalized_text": "crea un modulo de pagos [SEG] ...",
    "tokens": [
      {"value": "crea", "type": "ACTION_CREATE", "category": "action", ...},
      {"value": "modulo", "type": "MODULE", "category": "module", ...},
      {"value": "pagos", "type": "ENTITY", "category": "entity", ...}
    ],
    "ast": {
      "node_type": "project",
      "children": [
        {"node_type": "module", "name": "pagos", ...}
      ]
    },
    "symbols": { ... },
    "ir": { ... },
    "plan": [
      {"task_id": "pagos", "type": "scaffold", "dependencies": [], ...}
    ],
    "commands": [
      {"task_id": "pagos", "type": "scaffold", "path": "modules/pagos"}
    ]
  },
  "success": true
}
```

Los campos concretos dependen del prompt y del modo de ejecucion.
Con `--ir-only`, el pipeline se detiene despues del IR generador.
Sin `--ir-only`, continua hasta los generadores de codigo y produce archivos
en el directorio de salida.
