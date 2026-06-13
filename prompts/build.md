---

You are building un compilador-compilador, un generador de compilador, para un procesador de texto para archivos markdown

# Marco Integral de Proyecto

1. Información General del Proyecto
1.1 Nombre del Proyecto

Nombre provisional: __________________________________________

1.2 Descripción General

Describir el objetivo principal del sistema, visión del producto y propuesta de valor.

Resumen Ejecutivo
Problema que resuelve
Público objetivo
Diferenciadores del sistema
Alcance general
Objetivos de negocio
Objetivos técnicos
2. Visión del Producto
2.1 Objetivos Estratégicos
Objetivo	Descripción	Prioridad
2.2 Público Objetivo
Segmentos de usuarios
Cliente Final
Edad:
Intereses:
Comportamiento:
Necesidades:
Administrador
Responsabilidades:
Necesidades:
Vendedor / Operador
Responsabilidades:
Necesidades:
3. Toma de Requerimientos
3.1 Requerimientos Funcionales
3.2 Requerimientos No Funcionales

4. Análisis del Sistema

4.1 Problema actual


5. Architecture rules

4.2 Solución propuesta

4.3 Factibilidad

5. Arquitectura del Sistema

5.1 Arquitectura general
> Diagrama general: (insertar diagrama ASCII)

5.2 Componentes

Diseño de Base de Datos

6.1 Modelo de base de datos (...)


6.3 Relaciones clave

7. Modelado de Procesos

7.1 Flujo del bot inteligente

7.1 Sistema de diseño

7.2 Formularios clave (Diseño de Entrada)

7.3 Pantallas principales (Diseño de Salida)

8. Elaboración de Prototipos

8.1 Wireframes

8.2 Prototipos funcionales

9. Diseño UX / UI

9.1 Experiencia de usuario

9.2 Diseño de interfaz

- Mobile first, responsive, soporte dark mode, animaciones suaves

10. Stack Tecnológico

10.1 Frontend

10.2 Backend

| Tecnología | Uso |
|---|---|
| Node.js / NestJS | API |
| Python | IA / NLP |
| FastAPI | Servicios IA |

10.3 Base de datos


10.4 DevOps


11. API y Comunicación

11.1 Arquitectura API

- REST API, GraphQL y WebSockets según caso de uso

11.2 Endpoints principales (ejemplos)

13. Jest	Unit Testing
Cypress	E2E
Postman	APIs
14. DevOps y Despliegue
14.1 Infraestructura
Ambientes
Desarrollo
Staging
Producción
Hosting
AWS
DigitalOcean
Google Cloud
Azure
16.2 Pipeline CI/CD
Push código
Ejecutar tests
Build
Deploy automático
Verificación
15. Gestión del Proyecto
15.1 Metodología
Scrum
Kanban
Agile
15.2 Roles
Rol	Responsabilidades
Project Manager	Gestión general
Backend Developer	APIs y lógica
Frontend Developer	UI/UX
AI Engineer	Bot inteligente
DevOps Engineer	Infraestructura
15.3 Roadmap
Fase 1 — Investigación y Diseño
Requerimientos
Arquitectura
Prototipos
Fase 2 — MVP
Autenticación
Catálogo
Carrito
Pedidos
Fase 3 — Bot Inteligente
NLP
Integración IA
Automatización
Fase 4 — Escalabilidad
Optimización
Analytics
Recomendaciones IA
16. Gestión de Riesgos
Riesgo	Impacto	Mitigación
Caída del sistema	Alto	Redundancia
Problemas de pago	Alto	Pasarelas múltiples
Escalabilidad	Medio	Arquitectura modular
17. Métricas y KPIs
KPIs Técni
---

---
Crea un bucle o funcion recursiva de tipo bot con los siguientes requerimientos:
- Establecer reglas de respuestas deterministas para un bot que tenga los siguientes metodos :
read, eval, print, loop.
- Establece Reglas Semanticas, Reglas Sintacticas y Reglas Lexicas basicas de acuerdo a estandares y patrones probados para bots conversaciona Para estos metodos.
Algoritmo:
Input/Lenguaje fuente
preproceso de la entrada <- utilities
lexer -> Tokeniza [READ(scan)][EVAL(act)][PRINT(print)][LOOP(loop)]
tokenizacion <- lexema <- Analizador lexico(reglas sintacticas)
Se captura la entrada mediante un linker o algo parecido ![alt text](image.png)

La finalidad es crear un sistema de procesamiento "(Aho:chap1) Un sistema de procesamiento de lenguaje consiste en varios componentes que funcionan en una cola de procesamiento. Esta cola normalmente se inicia con un preprocesador y finaliza con el link editor o linker:
"
![alt text](image-1.png)

Flujo completo ideal (compilador):
Usuario: "Crea un módulo de pagos en NestJS"
  ↓
compilador compile "Crea un módulo de pagos..."
  ↓ LEX: tokeniza → [READ(scan)][EVAL(act)][PRINT(print)][LOOP(loop)]
  ↓ PARSE: construye AST
  ↓ SEMANTIC: resuelve con perfil + tabla de símbolos
  ↓ (OPCIONAL)SCORE: busca acciones similares en training
  ↓ IR.json: representación intermedia canónica
  ↓ (opcional[ESTABLECER])TRACE: three-address code (trazabilidad)
  ↓ SYNTHESIS: [READ(scan)][EVAL(act)][PRINT(print)][LOOP(loop)] o todas
  ↓ BOT: responde por chat
---

--- 
Escribe 3 agentes en la siguiente ruta /home/john/proyects/proyect0/.opencode/agents. Los agentes seran de tipo orquestador, sigue la siguiente especificación/prompt para crear los agentes : /home/john/proyects/proyect0/docs/008_PRM_BUILD_AGENT_1_0_DRAFT.md. 
# instruciones/descripcion:
## Orquestador1: delega
Contexto: -
1. Dónde(En que proyecto estamos trabajando leer) ubicacion/ruta, ruta de entrada, ruta de salida
2. Tareas : ¿Qué hacer? leer archivo : /home/john/proyects/proyect0/docs/006_PROP_DEV_COMPILER_BOT_1_0_DRAFT.md y /home/john/proyects/proyect0/docs/007_GUIDE_DEV_COMPILER_BOT_1_0_DRAFT.md crear ruta/mapa de ejecucion de lectura para que el agente/programador pueda saber que tareas ejecutar de acuerdo a las especificaciones y su mutua referencia.
3. Orden (Cuando): Evaluar en que orden realizar las las tareas.
4. Quien: (generador de prompt -> Generador de prompt)->Itera 
5. Cómo : Generador de promp : Delega a generador de prompt para saber qué, cómo, cuándo y dónde.
## orquestardor2: delega 
Contexto: Investigacion 
1. Problema:
2. Causa
Instrucciones : Fases delegadas por orquestador 1
Restricciones: -
- Sigue protocolo de AGENT.md
- Devuelveme : 
Resultado de build, 
resutado de test
Resultado de verificaion de endpoints
Resultado de deploy si aplica...
---
## Orquestador 3 : Generador de prompt
Contexto : Generador de prompt
Recibe cómo de orquestador 1
devuelve prompt


Analiza el proyecto y escribe un archivo .md para proponer funcionalidad/mejoras y hacerlo mas completo de acuerdo a las siguientes especificaciones. :/home/john/proyects/proyect0/docs/003_DOC_PROP_DOC_PROCESSOR_1.0_DRAFT.md, /home/john/proyects/proyect0/docs/004_SPEC_DEV_DOC_PROCESSOR_1_0_DRAFT.md evalua la propuesta como una continuacion de /home/john/proyects/proyect0/docs/014_PROP_DEV_COMPILER_BOT_NLP_INTENT_1_0_DRAFT.md
Se espera la siguiente propuesta :
- El bot debera ser capaz de entender y realizar tareas como seguir el siguiente tutorial y realizar las acciones que estan descritas en el, leer archivo: /home/john/proyects/proyect0/misc/tutorial.md.

Let me write the market analysis report following the naming convention.

publico objetivo :
Manufactura electronica
de esos usarian una herramienta tipo compiler-compiler = 15,000
sinergia
como envolverias el "tutorial" proyecto descrito en el siguiente archivo /home/john/proyects/proyect0/template/tutorial.md en un marco generico para inicializar, configurar, planeara, codificar, etc..., un proyecto de desarrollo de software. Escribe un archivo .md con tu respuesta. Utiliza tu conocimiento y estadares de la industria para escribir tu respuesta.
lifecycle
So the user wants:
- From interactive mode, being able to run -c "instruccion" or -f archivo.txt as internal commands
- The batch/composite mode runs within the interactive session, sharing state
- Then returns to interactive mode

The key architectural change would be:
1. Make process_instruction() the central dispatch for ALL instruction processing
2. Add source and command as interactive commands
3. The file mode in interactive context reads and processes each instruction through the same process_instruction() pipeline
4. State persists because they share the same RECPL_STATE_DIR
So the composite pattern would look like:
recpl.sh
  └── main()
       └── interactive_mode()    ← COMPOSITE (outer loop)
            ├── process_instruction()  ← procesa instruccion individual
            ├── [source archivo]       ← delega a modo archivo (mismo estado)
            ├── [exec instruccion]     ← delega a modo comando (mismo estado)
            └── [pipe | filter]        ← modo batch dinamico desde dentr


Quiero implementar mi bot-compiler en contra de las apis de claude, openai etc... cómo podria hacerlo, escribe un archivo .md con una propuesta implementacion,la intencion de esta feature es que mi compiler-bot tambien pueda traducir la intencion del usuario y porqué no que este pueda tambien taducir esa intencion y en una respuesta/mutacion, etc, depende de la solicitud del usuario, una  respuesta a su solicitud. Escribe archivo .md con la propuesta con el sigiente formato :
-- frontmatter --
# Reporte de Gerencia: Ingenieria Inversa
## prompt 
Hacer ingenieria inversa a claude y openai de acuerdo a su informacion publica para replicar su comportamiento en la forma en que se comunican sus agentes y sus procesos principales. 
Generar reporte. 
Escribe un archivo .md con un plan de ejecucion describiendo, mejoras (y explicacion detallada del funcionamiento de esta ingracion con LLMs y el bot-compiler) detalladas para que esta propuesta sea realmente realizable y documentable de manera que se pueda explicar su uso sin tanta complejidad. Utiliza patrones de diseño y las guias de estilo/convencion que estamos usando en el proyecto para escribir tu propuesta detallada. 

 RECPL Compiler Bot. Shell-based bot que procesa lenguaje natural y genera/procesa respuesta via pipeline compilador (preprocess → lexer → parser → semantic → IR → synthesis).

 Analiza el archivo :/home/john/proyects/proyect0/docs/027_PROP_DEV_COMPILER_BOT_CLI_FLAGS_1_0_DRAFT.md. Dime el estado actual del archivo, encuanto a la implementacion sugerida. Escribe una nueva seccion con el estado actual del archivo.



Escribe una propuesta de implementacion en un archivo .md para un debugger para proyecto0 (El proyecto actual), La idea nace de la necesidad de aprender el funcionamiento interno del pipeline, La La finalidad del debugger es proporcionar al equipo de ingenieria inversa una herramienta para que puedan encontrar bugs, latencias, entre otros "fallos", inconsistencia del sistema.la propuesta debe tener en cuenta la conversacion y la propuestas hechas en la conversacion siguiente:


 The user is asking how to debug the RECPL pipeline. Let me think about what tools and approaches are available based on the project structure I've seen.
From what I know about the project:
1. The pipeline is: preprocess → lexer → parser → semantic → IR → synthesis
2. Each stage passes JSON via stdin/stdout pipes
3. There's a LOG_FILE variable for logging
4. The test suite runs individual stages
5. There are individual scripts in frontend/, middleend/, backend/
Let me provide practical debugging approaches based on the actual codebase.
El pipeline trabaja con JSON puro via stdin/stdout. Hay varias formas segun que necesites ver:
1. Etapa por etapa (la mas util)
Ejecuta cada etapa individualmente con una instruccion conocida:
cd compiler-bot
# 1. Ver que sale del preprocesador
./frontend/preprocessor.sh "crea modulo pagos en nestjs"
# 2. Ver tokens del lexer
./frontend/lexer.sh "$(./frontend/preprocessor.sh "crea modulo pagos en nestjs")"
# 3. Pipeline completo paso a paso con pipes
./frontend/preprocessor.sh "crea modulo pagos en nestjs" | \
  ./frontend/lexer.sh | \
  ./frontend/parser.sh | \
  RECPL_STATE_DIR=/tmp/recpl_debug ./frontend/semantic.sh | \
  ./middleend/ir_generator.sh | \
  ./backend/synthesis.sh
2. Ver errores de una etapa
Si una etapa falla, el stderr tiene la causa. El pipeline oficial lo silencia (2>/dev/null), pero en debug quitalo:
./frontend/lexer.sh "crea modulo test_module en nestjs" 2>&1
#                ↑ muestra "Error lexico: token no reconocido en col 17: '_'"
3. Router
Si el problema esta en el ruteo (deterministico vs LLM):
# Forzar pipeline deterministico
RECPL_LLM_MODE=deterministic ./frontend/router.sh "crea modulo pagos en nestjs"
# Ver que decision toma
RECPL_LLM_MODE=auto ./frontend/router.sh "instruccion larga que no reconoce"
4. Log del bucle
recpl.sh escribe un log operable via LOG_FILE:
LOG_FILE=/tmp/recpl_debug.log ./recpl.sh -c "crea modulo pagos en nestjs"
cat /tmp/recpl_debug.log
5. Modo batch para aislar
Usa -c para probar una instruccion sin entrar al modo interactivo:
./recpl.sh -c "crea modulo pagos en nestjs"
Si el problema es solo en interactivo, prueba exactamente el mismo texto en batch:
echo "crea modulo pagos en nestjs" | ./recpl.sh


¿Existe algun debugguer para archivos .sh's ? 
The user is asking about debuggers for shell scripts (.sh files).
bash tiene modo debug nativo. No necesitas herramienta externa:
bash -x (trace de ejecucion)
Muestra cada linea ANTES de ejecutarla, con + anidados por profundidad:
bash -x recpl.sh -c "crea modulo pagos en nestjs"
Para una sola funcion del script sin ejecutar todo:
bash -x -c '
source compiler-bot/recpl.sh
init_state
process_instruction "crea modulo pagos en nestjs"
cleanup
'
bash -v (verbose)
Muestra cada linea mientras se lee, sin expandir variables:
bash -v recpl.sh -c "crea modulo pagos en nestjs"
Combinar -xv
bash -xv recpl.sh -c "crea modulo pagos en nestjs"
Debug parcial con set -x / set +x
Envuelve solo la seccion que te interesa:
set -x       # activa trace
process_instruction "crea modulo pagos en nestjs"
set +x       # desactiva trace
PS4 para contexto extra
La variable PS4 controla el prefijo del trace (+  por defecto). Cambialo para mostrar linea y funcion:
PS4='+[$LINENO] ' bash -x recpl.sh -c "crea modulo pagos en nestjs"
O con funcion anidada:
PS4='+${BASH_SOURCE}:${LINENO}:${FUNCNAME[0]:-main}() ' bash -x recpl.sh
Resumen
Herramienta	Que muestra	Cuando usarla
bash -x	Cada linea con variables expandidas	Flujo general, bugs de control
bash -v	Cada linea sin expandir	Problemas de parsing/sintaxis
set -x/set +x	Solo una seccion	Pipeline, funcion especifica
PS4	Linea, archivo, funcion	Scripts con multiples archivos


Quiero darle un nuevo concepto a Proyecto0. Escribe un analisis en un archivo .md para mi propuesta de nuevo concepto para Proyecto0. Lee todos los archivos dentro del directorio /home/john/proyects/proyect0/docs para que tengas una aproximación de lo que se esta creando. Mi propuesta se basa en lo siguiente:
Que es Proyecto0(RECPL):
un agente de código abierto que te ayuda a escribir y ejecutar código con cualquier modelo de IA. Está disponible como interfaz de terminal, aplicación de escritorio o extensión de IDE. 
Cómo usar recpl?
Acceso a una terminal
Claves de API de los proveedores de LLM que quiera usar.
```
leer /home/john/proyects/proyect0/docs/010_GUIDE_DEV_COMPILER_BOT_RUNBOOK_1_0_DRAFT.md

```
¿Necesito suscripciones extra de IA para usar RECPL?
No necesariamente, RECPL viene con un conjunto de modelos gratuitos que puedes usar sin crear una cuenta. Aparte de estos, puedes usar cualquiera de los modelos de codificación populares creando una cuenta de (feature de proveedores gratuitos, exponer api interna para ofrecerlos gratuitamente como opcion). Aunque animamos a los usuarios a usar (funcionalidad interna que provee modelos gratuitos), RECPL también funciona con todos los proveedores populares como OpenAI, Anthropic, xAI, etc. Incluso puedes conectar tus modelos locales.

¿Puedo usar mis suscripciones de IA existentes con OpenCode?
Sí, RECPL soporta planes de suscripción de los principales proveedores. Puedes usar tus suscripciones de Claude Pro/Max, ChatGPT Plus/Pro o GitHub Copilot.

¿Solo puedo usar RECPL en la terminal? *futuro*
¡Ya no! RECPL ahora está disponible como una aplicación para tu escritorio y web!

¿Cuánto cuesta RECPL?
RECPL es 100% gratuito de usar. También viene con un conjunto de modelos gratuitos. Puede haber costos adicionales si conectas cualquier otro proveedor.

¿Es RECPL de código abierto?
Sí, RECPL es totalmente de código abierto. El código fuente es público en GitHub bajo la Licencia MIT, lo que significa que cualquiera puede usar, modificar o contribuir a su desarrollo. Cualquiera de la comunidad puede abrir problemas, enviar solicitudes de extracción y extender la funcionalidad.



La idea nace de un estudio hecho de la tendencia actual/revolucion a la automatización del desarrollo de software, se proponer utilizar la base de codigo actual y extrapolarla a un sistema de agentes. Entiendase como agente, "una entidad computacional diseñada para percibir su entorno (ambos, digital y potencialmente fisica), tomar decisiones informadas basadas en esas percepciones y un conjunto de objetivos predefinidos o aprendidos, y ejecutar acciones para alcanzar esos objetivos de manera autonoma:
Caracteristicas:
- Autonomia
- Proactividad
- Reactividad
Son orientados al objetivo.
Una Capacidad es el uso de herramientas lo que les permite inractuar con apis externas, bases de datos o servicios, alcanzando mas alla de su liezo inmediato, poseen memoria, retienen informacion a lo largo de las interacciones y pueden establecer conversaciones con usuarios, otros sistemas, incluso otros agentes que operan en el mismo lienzo conectados..."
La finalidad de esta redireccion, Es que la herramienta creada le sea de utilidad a cualquier desarrollador de software para cualquier tarea de desarrollo de software de manera mas intuitiva.