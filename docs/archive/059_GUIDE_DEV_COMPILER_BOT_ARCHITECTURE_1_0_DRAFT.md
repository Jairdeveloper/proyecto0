---
id: 059
area: dev
type: guide
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - guide
  - architecture
  - overview
  - components
  - data-flow
summary: "Guia de arquitectura de Proyecto0(RECPL). Explica de forma sencilla como funciona el compilador de lenguaje natural a codigo IR, sus componentes principales, el flujo de datos, y como conviven el pipeline deterministico, el agente inteligente y los generadores de codigo."
keywords:
  - arquitectura
  - pipeline
  - agente
  - recpl
  - componentes
  - flujo
  - shell
changelog:
  - version: 1.0
    date: 2026-06-13
    author: workflow-agent
    description: Guia de arquitectura de Proyecto0 — pipeline compilador, agente, generacion de codigo
---

# Guia de Arquitectura de Proyecto0(RECPL)

> **Que es Proyecto0:** Un asistente que funciona en la terminal. Le escribes
> instrucciones en espanol ("crea un modulo de pagos en NestJS") y el genera
> el codigo por ti.

---

## 1. La idea central

Proyecto0 funciona como un **compilador de lenguaje natural a codigo IR**: toma texto
escrito por una persona y lo convierte en codigo. Para lograrlo, imita el
diseno de los compiladores clasicos (como los que usan C, Java o Python),
pero adaptado para entender espanol y generar archivos NestJS/Prisma.

El proceso completo es:

```
Tu escribes:  "crea un modulo de usuarios en NestJS"
     ↓
El sistema:   analiza → entiende → planifica → genera codigo
     ↓
Resultado:    archivos .ts, .module, .service creados automaticamente
```

---

## 2. Los dos caminos para entender instrucciones

Proyecto0 tiene dos formas de entender lo que le pides:

### Camino deterministico (rapido, sin internet)

Usa reglas fijas escritas en codigo. Reconoce palabras clave como "crea",
"modulo", "nestjs" y las traduce a acciones. Es rapido, no necesita internet,
pero solo entiende frases con esas palabras clave.

### Camino con inteligencia artificial (flexible, necesita internet)

Usa modelos de IA como Claude (de Anthropic) u OpenAI. Entiende frases mas
naturales y variadas. Por ejemplo, entiende tanto "crea un modulo de pagos"
como "necesito un modulo para procesar pagos, por favor". Pero necesita una
clave de API y conexion a internet.

El sistema decide automaticamente que camino usar: primero intenta con el
rapido (deterministico), y si no entiende la instruccion, recurre a la IA.

---

## 3. El pipeline (la cadena de montaje)

El proceso de convertir tu instruccion en codigo pasa por varias etapas,
como una fabrica:

```
Entrada
   ↓
1. PREPROCESADOR  — limpia el texto (quita mayusculas, signos repetidos)
   ↓
2. ANALIZADOR LEXICO — separa en palabras clave (tokens)
   ↓
3. ANALIZADOR SINTACTICO — identifica la estructura: accion + objeto + tecnologia
   ↓
4. ANALIZADOR SEMANTICO — verifica que tenga sentido y guarda el contexto
   ↓
5. GENERADOR IR — crea un "plano" intermedio con las instrucciones claras
   ↓
6. SINTESIS — convierte el plano en una respuesta o en codigo
   ↓
Salida
```

### 3.1 Preprocesador

Toma tu texto y lo estandariza: pasa todo a minusculas, quita espacios de
mas, coloca puntos donde faltan. Esto asegura que las etapas siguientes
reciban texto limpio sin importar como escribas.

### 3.2 Analizador lexico (el que separa palabras)

Divide tu frase en piezas reconocibles llamadas "tokens". Por ejemplo:

```
"crea modulo usuarios en nestjs"
  → [ACCION: crea] [MODULO] [NOMBRE: usuarios] [TECNOLOGIA: nestjs]
```

Es como cuando separas una oracion en sujeto, verbo y predicado, pero
adaptado a instrucciones de programacion.

### 3.3 Analizador sintactico (el que entiende la estructura)

Toma los tokens y arma un arbol con la estructura de la instruccion.
Verifica que la frase tenga sentido: "crea modulo X en Y" es valida,
pero "en nestjs modulo crea" no lo es.

### 3.4 Analizador semantico (el que da significado)

Verifica que lo que pides sea factible. Mantiene una "tabla de simbolos"
que recuerda modulos creados anteriormente. Si pides eliminar algo que no
existe, te avisa.

### 3.5 Generador de IR (representacion intermedia)

Toma toda la informacion validada y produce un JSON estandarizado. Este
JSON es como un "plano" que describe exactamente que hay que hacer, sin
importar si la instruccion vino del camino deterministico o de la IA.

Ejemplo del plano:
```json
{
  "accion": "scaffold",
  "tipo": "module",
  "nombre": "usuarios",
  "tech": "nestjs"
}
```

### 3.6 Sintesis (el que genera codigo)

Toma el plano JSON y lo convierte en una respuesta para el usuario. Si el
plano pide crear codigo, llama al generador de plantillas (scaffold) que
copia archivos desde `templates/` y reemplaza los nombres genericos por
los que pediste.

---

## 4. El agente inteligente

Sobre el pipeline compilador hay una capa adicional llamada **agente**.
El agente es como un recepcionista: recibe tu instruccion, decide que hacer
con ella, y si es necesario, la descompone en pasos mas pequenos.

### 4.1 Clasificador de intenciones

Cuando escribes algo, el agente primero clasifica que tipo de cosa es:

| Si dices... | El agente piensa... |
|-------------|---------------------|
| "hola", "quien eres" | Es un saludo → responde amablemente |
| "crea modulo auth en nestjs" | Es una instruccion RECPL → la envia al pipeline |
| "crea modulo auth y modulo payments" | Tiene varias partes → necesita un plan |
| "lee el archivo config.js" | Quiere leer un archivo → usa la herramienta de lectura |
| "ejecuta npm install" | Quiere ejecutar un comando → usa la terminal |

### 4.2 Planificador

Si la instruccion tiene varias partes ("crea modulo X y modulo Y"), el
planificador las separa en pasos individuales y los ejecuta uno por uno.

Existen dos planificadores:
- **Planificador rapido**: usa reglas fijas para detectar "y" y separar
  las partes. Funciona siempre.
- **Planificador con IA**: usa inteligencia artificial para descomponer
  instrucciones mas complejas. Solo funciona si hay conexion a internet.

Si el planificador con IA no esta disponible, el rapido toma el control
automaticamente.

### 4.3 Herramientas del agente

El agente tiene varias herramientas a su disposicion:

| Herramienta | Que hace |
|-------------|----------|
| RECPL | Envia la instruccion al pipeline compilador |
| Responder | Da una respuesta textual (saludos, ayuda) |
| Leer archivo | Muestra el contenido de un archivo |
| Escribir archivo | Crea o modifica un archivo |
| Ejecutar comando | Corre un comando en la terminal |
| Buscar codigo | Encuentra texto dentro de los archivos del proyecto |

### 4.4 Memoria

El agente tiene memoria: guarda un historial de las instrucciones que le
diste y las respuestas que dio. Esta memoria persiste entre sesiones,
asi que si cierras y abres la terminal, el agente recuerda lo que hicieron
juntos.

### 4.5 Interfaz grafica en terminal (TUI)

Ademas de escribir comandos directamente, el agente puede mostrar un menu
interactivo usando `whiptail` (ventanas de texto en la terminal). Esto
permite usar el programa con menus y botones, sin tener que recordar
comandos.

Para activarlo: `./agent-robot/agent.sh --tui`

---

## 5. El puente (bridge)

El agente y el pipeline compilador son dos sistemas separados. Para
comunicarse usan un "puente" (bridge):

```
Agente ──→ Puente ──→ Pipeline RECPL
```

El puente se encarga de:
1. Llamar al pipeline con la instruccion correcta
2. Capturar la respuesta (que viene en JSON)
3. Traducir la respuesta a un formato que el agente entienda
4. Devolverle el resultado al agente

Esto mantiene a ambos sistemas independientes: se puede modificar el
pipeline sin tener que cambiar el agente, y viceversa.

---

## 6. Los proveedores de IA

Para el camino con inteligencia artificial, el sistema soporta varios
"proveedores":

- **Claude** (de Anthropic) — el principal
- **OpenAI** (ChatGPT) — alternativa

Cada proveedor tiene su propio adaptador, pero todos se usan de la misma
forma. Si en el futuro aparece otro proveedor, solo hace falta escribir
un adaptador nuevo.

La seleccion del proveedor se hace con la variable de entorno:

```sh
export AGENT_LLM_PROVIDER=claude    # o "openai"
```

---

## 7. Las plantillas de codigo

Para generar codigo, el sistema usa plantillas. Son archivos con partes
variables que se reemplazan segun lo que pediste.

Por ejemplo, una plantilla para un modulo de NestJS:

```
templates/module-nestjs/
├── __LOWERNAME__.controller.ts
├── __LOWERNAME__.module.ts
└── __LOWERNAME__.service.ts
```

Cuando pides "crea modulo usuarios en nestjs", el sistema:
1. Copia los archivos de la plantilla
2. Reemplaza `__LOWERNAME__` por "usuarios"
3. Reemplaza `__NAME__` por "Usuarios"
4. Guarda los archivos en `modules/usuarios/`

---

## 8. Como se organiza el codigo

El proyecto esta en la carpeta `compiler-bot/` y tiene esta estructura:

| Carpeta | Contenido |
|---------|-----------|
| `compiler-bot/recpl.sh` | El bucle principal del compilador |
| `compiler-bot/agent-robot/` | El agente inteligente y sus herramientas |
| `compiler-bot/frontend/` | Analisis del lenguaje (lexico, sintactico, semantico) |
| `compiler-bot/middleend/` | Generacion del plano intermedio (IR) |
| `compiler-bot/backend/` | Generacion de codigo y respuestas |
| `compiler-bot/providers/` | Adaptadores para Claude y OpenAI |
| `compiler-bot/templates/` | Plantillas para generar codigo NestJS/Prisma |
| `compiler-bot/tests/` | Pruebas del sistema (72 + 19 = 91 pruebas) |
| `docs/` | Documentacion del proyecto (60+ archivos) |

---

## 9. Modos de uso

Puedes usar Proyecto0 de varias formas:

### Modo directo (una instruccion)

```sh
echo "crea modulo pagos en nestjs" | ./agent-robot/agent.sh
```

### Modo interactivo (conversacion)

```sh
./agent-robot/agent.sh --tui
# Se abre un menu con opciones
```

### Forzar uso de IA

```sh
./agent-robot/agent.sh --llm "explica que es este proyecto"
```

### Modo solo deterministico (sin IA)

```sh
./agent-robot/agent.sh --deterministic "crea modulo auth en nestjs"
```

---

## 10. Resumen visual

```
                    ┌──────────────────────────────────────┐
                    │          TU INSTRUCCION               │
                    │  "crea modulo usuarios en nestjs"     │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │         AGENTE (agent.sh)             │
                    │                                      │
                    │   1. Clasifica: es una instruccion    │
                    │      de creacion? un saludo? un       │
                    │      comando?                         │
                    │                                      │
                    │   2. Si tiene varias partes, la       │
                    │      descompone en pasos (planner)    │
                    │                                      │
                    │   3. Ejecuta cada paso                │
                    └──────────────┬───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │       PIPELINE COMPILADOR             │
                    │                                      │
                    │   ┌─────────┐                        │
                    │   │ Router  │──→ IA (si es necesario) │
                    │   └────┬────┘                        │
                    │        │                              │
                    │   ┌────▼────────────────────┐        │
                    │   │ Pipeline deterministico  │        │
                    │   │                          │        │
                    │   │ preprocess → lexer →     │        │
                    │   │ parser → semantic → IR   │        │
                    │   └──────────────────────────┘        │
                    │              │                         │
                    │         ┌────▼────┐                   │
                    │         │Sintesis │                   │
                    │         └────┬────┘                   │
                    └──────────────┼───────────────────────┘
                                   │
                    ┌──────────────▼───────────────────────┐
                    │       GENERACION DE CODIGO            │
                    │                                      │
                    │   Plantillas → modules/usuarios/      │
                    │   ├── usuarios.controller.ts          │
                    │   ├── usuarios.module.ts              │
                    │   └── usuarios.service.ts             │
                    └──────────────────────────────────────┘
```

---

## 11. Para empezar a usarlo

1. Entra a la carpeta del proyecto: `cd compiler-bot`
2. Prueba una instruccion simple:

```sh
echo "hola" | ./agent-robot/agent.sh
```

3. Prueba crear un modulo:

```sh
echo "crea modulo demo en nestjs" | ./agent-robot/agent.sh
```

4. Si tienes una clave de API, activa la IA:

```sh
export ANTHROPIC_API_KEY="tu-clave-aqui"
./agent-robot/agent.sh --llm "crea un microservicio de pagos con nodejs"
```

5. Para el menu interactivo:

```sh
./agent-robot/agent.sh --tui
```
