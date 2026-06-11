---
id: 022
area: dev
type: GUIDE
module: lifecycle-framework
version: 1.0
status: DRAFT
tags:
  - guide
  - framework
  - lifecycle
  - methodology
  - project-management
  - software-engineering
  - iso-12207
  - pmbok
  - agile
  - devops
summary: "Marco generico de ciclo de vida para proyectos de desarrollo de software. Define 8 fases estandar (Inicio, Planificacion, Diseno, Configuracion, Codificacion, Verificacion, Despliegue, Operacion) con entradas, actividades, salidas y criterios de aceptacion. Incluye la documentacion como actividad transversal obligatoria en todas las fases. Mapeo concreto usando el tutorial de Django+GraphQL como caso de estudio."
keywords:
  - guia
  - marco
  - ciclo-de-vida
  - framework
  - proyecto
  - desarrollo
  - software
  - fases
  - estandar
  - iso-12207
  - pmbok
  - metodologia
  - tutorial
  - plantilla
  - hitos
  - entregables
  - verificacion
  - documentacion
  - transversal
changelog:
  - version: 1.0
    date: 2026-06-08
    author: workflow-agent
    description: Creacion del marco generico de ciclo de vida para proyectos de software
---

# Marco Generico de Ciclo de Vida para Proyectos de Software

> **Referencias:** ISO/IEC 12207 (procesos de ciclo de vida del software),
> PMBOK Guide 7th ed. (principios de gestion de proyectos),
> Agile Manifesto, DevOps Handbook.
>
> **Caso de estudio:** Tutorial de GraphQL con Django y Graphene
> (`template/tutorial.md`).
>
> **Integracion con RECPL:** State machine pattern de AGENTS.md
> (analyze → propose → approve → plan → approve → execute → verify).

---

## 1. Introduccion

### 1.1 Proposito

Este documento define un **marco generico** para iniciar, planificar, disenar,
configurar, codificar, verificar, desplegar y operar cualquier proyecto de
desarrollo de software. El marco es **agnostico en tecnologia, metodologia
y tamano de equipo**. Se presenta como un wrapper o envoltura que transforma
cualquier tutorial o especificacion tecnica en un proyecto ejecutable y
trazable.

### 1.2 Por que un Marco Generico

Los tutoriales tipicos (como el de Django+GraphQL) ensenan **pasos secuenciales**
pero omiten las fases anteriores (decisiones de diseno, analisis de riesgo) y
posteriores (operacion, mantenimiento). Un marco generico:

| Problema del tutorial aislado | Solucion del marco |
|------------------------------|-------------------|
| Empieza directamente con instalacion | Incluye fase de analisis y decision previa |
| No explica alternativas descartadas | Documenta decisiones de diseno |
| No define criterios de exito | Cada fase tiene verificacion explicita |
| Termina cuando el codigo funciona | Incluye despliegue y operacion |
| Asume un contexto especifico | Parametrizable a cualquier stack |

### 1.3 Relacion con RECPL

Este marco es la **capa de proceso** que envuelve al pipeline RECPL:

```
[ MARCO DE CICLO DE VIDA ]
  ├── Fase 1: Inicio      →  RECPL: analyze intent
  ├── Fase 2: Plan         →  RECPL: classify_intent + fill_slots
  ├── Fase 3: Diseno       →  RECPL: semantic analysis + IR
  ├── Fase 4: Configuracion → RECPL: preprocess + setup
  ├── Fase 5: Codificacion  → RECPL: synthesis + scaffold
  ├── Fase 6: Verificacion  → RECPL: test suite
  ├── Fase 7: Despliegue    → RECPL: build + package
  └── Fase 8: Operacion     → RECPL: monitor + iterate

Donde RECPL actua como el **motor de ejecucion** de cada fase.
```

---

## 2. Las 8 Fases del Ciclo de Vida

Cada fase tiene:
- **Entrada:** Que se necesita antes de empezar
- **Actividades:** Que se hace en la fase
- **Salida:** Que se produce al terminar
- **Verificacion:** Como se valida que la fase esta completa
- **Artefactos:** Documentos o archivos generados
- **Caso concreto:** Mapeo al tutorial Django+GraphQL

```
Vista general del pipeline:

[INICIO] → [PLAN] → [DISENO] → [CONFIG] → [CODIGO] → [VERIF] → [DESPL] → [OPERA]
    │         │         │          │          │         │         │         │
    ▼         ▼         ▼          ▼          ▼         ▼         ▼         ▼
[Req]    [Plan]    [Arq]     [Env]      [Feat]    [Test]    [Release] [Run]
┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐
│Acta  │ │Plan  │ │Doc   │ │Repo    │ │Sprin │ │Suite │ │Tag   │ │Monitor │
│proy. │ │proy. │ │arq.  │ │+ deps  │ │t N   │ │tests │ │v1.0  │ │+ logs  │
└──────┘ └──────┘ └──────┘ └────────┘ └──────┘ └──────┘ └──────┘ └────────┘
                                                                             
         Retroalimentacion (ciclo de refinamiento) ←──────────────────────
```

---

### Fase 1: Inicio (Initiation)

**Objetivo:** Definir el proyecto, su alcance y viabilidad antes de escribir
una linea de codigo.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Idea, necesidad, problema a resolver, tutorial o especificacion |
| **Objetivo** | Decidir si el proyecto se hace y cual es su alcance inicial |
| **Duracion tipica** | 1-3 dias |
| **Metodologia** | Analisis de viabilidad tecnica y de negocio |

#### Actividades

1. **Definir el problema:** ?Que problema resuelve el proyecto? ?Para quien?
2. **Identificar stakeholders:** ?Quien usa, financia, mantiene el resultado?
3. **Definir alcance (bounded context):** ?Que incluye? ?Que NO incluye?
4. **Evaluar viabilidad:** ?Tenemos las herramientas, tiempo y conocimiento?
5. **Seleccionar stack tecnologico:** ?Lenguaje, framework, base de datos?
6. **Definir criterios de exito:** ?Como sabemos que el proyecto esta completo?
7. **Crear acta de proyecto (project charter):** Documento fundacional.

#### Salida

- Acta de proyecto (project charter) con alcance, objetivos, stakeholders, stack
- Repositorio de codigo inicializado (git init)
- Directorio docs/ con README.md basico

#### Verificacion

- [ ] Acta firmada o aprobada por stakeholders
- [ ] Stack tecnologico seleccionado con justificacion
- [ ] Criterios de exito definidos y medibles
- [ ] Repositorio creado con .gitignore adecuado

#### Caso concreto (Django+GraphQL)

```yaml
Proyecto: shorty — Acortador de URL con GraphQL
Problema: Crear un backend que acorte URLs largas usando GraphQL
Stack: Python 3.5+, Django 2.1.7, Graphene-Django 2.2.0
Stakeholders: Desarrollador backend, usuario final del API
Criterios de exito:
  - Endpoint GraphQL funcional en /graphql
  - Mutation createUrl acepta URL y devuelve hash
  - Query urls lista todas las URLs
  - Redireccion de URL corta a URL original
  - Validacion de URLs invalidas
  - Filtro por nombre de URL
  - Paginacion con first/skip
No incluye: Autenticacion de usuarios, UI web, base de datos no relacional
```

---

### Fase 2: Planificacion (Planning)

**Objetivo:** Descomponer el trabajo en tareas, estimar esfuerzo, y definir
el orden de ejecucion.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Acta de proyecto (de Fase 1) |
| **Objetivo** | Tener un plan accionable con tareas, dependencias y tiempos |
| **Duracion tipica** | 1-5 dias |
| **Metodologia** | WBS (Work Breakdown Structure), grafo de dependencias |

#### Actividades

1. **Descomponer el proyecto en tareas atomicas** (WBS):
   - Cada tarea debe ser: una accion concreta, verificable, < 1 dia de esfuerzo
   - Formato: `[verbo] [objeto] [contexto]` (ej: "Instalar dependencias en venv")
2. **Identificar dependencias entre tareas** (grafo):
   - ?Que tarea debe completarse antes de empezar otra?
   - ?Que tareas son independientes y pueden ejecutarse en paralelo?
3. **Estimar esfuerzo por tarea**:
   - Usar tallas: S (< 2h), M (2-4h), L (4-8h), XL (8h+)
4. **Definir hitos (milestones):** Puntos de verificacion intermedios
5. **Asignar prioridad:** MoSCoW (Must, Should, Could, Wont)

#### Salida

- WBS (lista de tareas con ID, nombre, esfuerzo, dependencias)
- Grafo de dependencias (DAG)
- Cronograma (orden de ejecucion)
- Hitos definidos

#### Verificacion

- [ ] Toda tarea tiene esfuerzo estimado
- [ ] Dependencias explicitas identificadas
- [ ] Orden topologico del grafo es correcto
- [ ] Hitos alineados con criterios de exito de Fase 1

#### Caso concreto (Django+GraphQL)

```
WBS del tutorial (8 pasos → 18 tareas atomicas):

FASE 2: PLANIFICACION
│
├── 2.1 Descomponer tutorial
│   ├── T-001  Instalar Python 3.5+ y pip (prerequisito)
│   ├── T-002  Crear entorno virtual y directorio shorty
│   ├── T-003  Instalar django==2.1.7 y graphene-django>=2.2.0
│   ├── T-004  Crear proyecto Django (django-admin startproject)
│   ├── T-005  Ejecutar migraciones iniciales
│   ├── T-006  Configurar graphene_django en INSTALLED_APPS
│   ├── T-007  Configurar GRAPHENE schema en settings.py
│   ├── T-008  Crear app shortener (startapp)
│   ├── T-009  Registrar shortener en INSTALLED_APPS
│   ├── T-010  Crear modelo URL con full_url, url_hash, clicks
│   ├── T-011  Crear migraciones y migrar
│   ├── T-012  Crear URLType y Query en shortener/schema.py
│   ├── T-013  Crear schema.py principal en shorty/
│   ├── T-014  Configurar URL endpoint GraphQL + GraphiQL
│   ├── T-015  Crear Mutation CreateURL
│   ├── T-016  Crear vista root de redireccion
│   ├── T-017  Implementar validacion de URL (GraphQLError)
│   ├── T-018  Implementar filtro por nombre
│   └── T-019  Implementar paginacion (first/skip)

Grafo de dependencias:
T-001 ← T-002 ← T-003 ← T-004 ← T-005 ← T-006 ← T-007
                                                      │
                                                      ▼
                                               T-008 ← T-009 ← T-010 ← T-011
                                                                          │
                                                          T-012 ←─────────┤
                                                          │               │
                                                          ▼               │
                                                     T-013 ←──────────────┘
                                                      │
                                                      ▼
                                                     T-014
                                                      │
                                          T-015 ←─────┘
                                                      │
                                          T-016 ←─────┘
                                                      │
                                          T-017 ←─────┘
                                                      │
                                          T-018 ←─────┘
                                                      │
                                          T-019 ←─────┘
```

---

### Fase 3: Diseno (Design / Architecture)

**Objetivo:** Definir la arquitectura del sistema: componentes, datos, flujos,
y decisiones tecnicas.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Acta de proyecto (Fase 1) + WBS (Fase 2) |
| **Objetivo** | Tener un plano arquitectonico que guie la implementacion |
| **Duracion tipica** | 1-5 dias |
| **Metodologia** | C4 model, diagramas de componentes, ADRs |

#### Actividades

1. **Definir arquitectura de alto nivel (contexto):**
   - ?Que componentes conforman el sistema?
   - ?Como se comunican entre si?
   - ?Con que sistemas externos interactuan?
2. **Definir modelo de datos:**
   - Entidades, atributos, relaciones
   - Formato de los datos en cada interfaz
3. **Definir flujo de datos:**
   - ?Que camino sigue una peticion desde que entra hasta que responde?
   - ?Donde se ejecuta cada logica (validacion, transformacion, persistencia)?
4. **Documentar decisiones de diseno (ADR):**
   - Cada decision importante con: contexto, opciones, decision, consecuencias
5. **Definir contratos de API:**
   - Formato de peticion/respuesta para cada endpoint
   - Schemas de datos

#### Salida

- Diagrama de contexto (C4 Level 1)
- Diagrama de contenedores (C4 Level 2)
- Modelo de datos (ERD)
- ADRs (Architecture Decision Records)
- Contratos de API (schemas)

#### Verificacion

- [ ] Diagrama de contexto completo con todos los actores externos
- [ ] Modelo de datos normalizado (3FN o justificacion de desnormalizacion)
- [ ] ADRs creados para decisiones no triviales
- [ ] Contratos de API especificados antes de codificar

#### Caso concreto (Django+GraphQL)

```
Arquitectura de shorty:

Contexto:
  [Cliente HTTP] ←→ [Shorty API (Django + GraphQL)] ←→ [SQLite DB]

Contenedores:
  ┌─────────────────────────────────────────────────┐
  │  shorty/ (proyecto Django)                       │
  │  ├── shorty/ (configuracion)                     │
  │  │   ├── settings.py   (INSTALLED_APPS, GRAPHENE)│
  │  │   ├── urls.py       (/graphql, /<url_hash>)   │
  │  │   └── schema.py     (Query + Mutation root)   │
  │  └── shortener/ (app)                            │
  │      ├── models.py     (URL)                     │
  │      ├── schema.py     (URLType, Query, Mutation)│
  │      └── views.py      (root redirect)           │
  └─────────────────────────────────────────────────┘

Modelo de datos:
  URL {
    full_url:  URLField (unique, validated)
    url_hash:  URLField (unique, MD5[:10])
    clicks:    IntegerField (default=0)
    created_at: DateTimeField (auto_now_add)
  }

Flujo de una mutation createUrl:
  POST /graphql → GraphQLView → validate schema → resolve CreateURL
    → URL.save() → validate() → md5 hash → INSERT → return URLType

Flujo de redireccion:
  GET /<url_hash> → root() → get_object_or_404 → clicked() → redirect()

ADR-001: Usar SQLite en desarrollo
  Contexto: Tutorial local, sin multiples usuarios concurrentes
  Opciones: SQLite (integrado), PostgreSQL (requiere servidor)
  Decision: SQLite por simplicidad del tutorial
  Consecuencias: Migrar a PostgreSQL en produccion

ADR-002: Hash MD5 truncado a 10 caracteres
  Contexto: URL corta debe ser legible y unica
  Opciones: MD5[:10], Base62, UUID4
  Decision: MD5[:10] por simplicidad (el tutorial lo especifica)
  Consecuencias: Riesgo de colision teorica; monitorear en produccion
```

---

### Fase 4: Configuracion (Setup / Environment)

**Objetivo:** Preparar el entorno de desarrollo con todas las herramientas,
dependencias y configuraciones necesarias.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | WBS (Fase 2) + diseno (Fase 3) |
| **Objetivo** | Entorno reproducible donde cualquier desarrollador pueda empezar a codificar |
| **Duracion tipica** | 0.5-2 dias |
| **Metodologia** | Infrastructure as Code, entornos virtuales, Docker |

#### Actividades

1. **Preparar entorno de desarrollo:**
   - Instalar lenguajes y runtimes (Python, Node, etc.)
   - Configurar gestor de paquetes (pip, npm, cargo)
   - Crear entorno virtual o contenedor (venv, Docker)
2. **Inicializar proyecto base:**
   - Ejecutar scaffold inicial (django-admin startproject, npm init, cargo init)
   - Configurar archivo de dependencias (requirements.txt, package.json, Cargo.toml)
3. **Configurar herramientas de calidad:**
   - Linter (flake8, eslint, clippy)
   - Formateador (black, prettier, rustfmt)
   - Testing framework (pytest, jest, cargo test)
4. **Verificar que el entorno funciona:**
   - Ejecutar comando basico del framework (python manage.py runserver, npm start)
   - Confirmar que los tests pasan (si existen tests de template)

#### Salida

- Entorno de desarrollo funcional y documentado
- Archivo de dependencias (requirements.txt, etc.)
- Proyecto base inicializado
- Herramientas de calidad configuradas

#### Verificacion

- [ ] Comando `python --version` / `node --version` funciona
- [ ] `pip install -r requirements.txt` se completa sin errores
- [ ] Proyecto base arranca (runserver, dev server)
- [ ] Linter pasa sin errores en codigo generado
- [ ] README.md documenta como replicar el setup

#### Caso concreto (Django+GraphQL)

```sh
# Fase 4 del tutorial (Paso 1):
python3 -m venv .venv
source .venv/bin/activate
pip install "django==2.1.7" "graphene-django>=2.2.0"
django-admin startproject shorty .
python manage.py migrate
python manage.py runserver
# Verificar: http://localhost:8000 responde
```

---

### Fase 5: Codificacion (Implementation / Coding)

**Objetivo:** Implementar las funcionalidades del proyecto siguiendo el plan
y las decisiones de diseno. Esta fase se repite por cada feature/historia.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Diseno (Fase 3) + entorno (Fase 4) + plan (Fase 2) |
| **Objetivo** | Codigo funcionando que cumple los criterios de exito |
| **Duracion tipica** | Por feature: 0.5-3 dias |
| **Metodologia** | TDD/BDD, pair programming, Git Flow |

#### Actividades (por cada iteracion/feature)

1. **Seleccionar siguiente tarea** del WBS priorizado
2. **Escribir test** (si aplica TDD: test primero, codigo despues)
3. **Implementar la funcionalidad** siguiendo el diseno acordado
4. **Documentar la implementacion** (docstrings, comentarios de API, README si aplica)
5. **Ejecutar pruebas** unitarias y de integracion locales
6. **Commit + push** con mensaje descriptivo
7. **Marcar tarea como completada** en el WBS

#### Salida

- Codigo fuente funcional para cada tarea del WBS
- Commits en el repositorio (uno por tarea o por feature)
- Tests que validan la implementacion

#### Verificacion

- [ ] Cada tarea tiene al menos un commit asociado
- [ ] Tests pasan antes de marcar tarea como completada
- [ ] Codigo sigue las guias de estilo del proyecto
- [ ] No hay regresiones en funcionalidades previas

#### Caso concreto (Django+GraphQL)

Cada paso del tutorial (Paso 2 a Paso 8) corresponde a una iteracion:

```
Iteracion 1 (T-008 a T-011): App + Modelo
  → Crear app, definir modelo URL, migrar
  → Verificar: python manage.py showmigrations | grep shortener

Iteracion 2 (T-012 a T-014): Query + GraphiQL
  → Crear URLType, Query, schema principal, endpoint
  → Verificar: Query urls en GraphiQL devuelve []

Iteracion 3 (T-015): Mutation
  → Crear CreateURL, Mutation root
  → Verificar: createUrl devuelve URL con hash

Iteracion 4 (T-016): Redireccion
  → Crear vista root, anadir URL pattern
  → Verificar: GET /<hash> redirige a URL original

Iteracion 5 (T-017): Validacion de errores
  → Anadir URLValidator, GraphQLError
  → Verificar: URL invalida devuelve error

Iteracion 6 (T-018): Filtros
  → Anadir argumento url a Query.urls
  → Verificar: urls(url:"community") filtra

Iteracion 7 (T-019): Paginacion
  → Anadir first, skip a Query.urls
  → Verificar: urls(first:2, skip:1) pagina
```

---

### Fase 6: Verificacion (Testing / Verification)

**Objetivo:** Validar que el sistema completo cumple los criterios de exito
definidos y no tiene regresiones.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Codigo implementado (Fase 5) + criterios de exito (Fase 1) |
| **Objetivo** | Sistema verificado y listo para desplegar |
| **Duracion tipica** | 1-3 dias |
| **Metodologia** | Piramide de tests (unitarios, integracion, e2e) |

#### Actividades

1. **Ejecutar suite completa de tests unitarios**
2. **Ejecutar tests de integracion** (componentes conectados)
3. **Ejecutar tests end-to-end** (flujo completo del usuario)
4. **Ejecutar linter y analisis estatico** (flake8, mypy, bandit)
5. **Verificar criterios de exito** uno por uno
6. **Verificar documentacion:** README actualizado, API docs generadas, cambios documentados
7. **Prueba de regresion:** Las features anteriores siguen funcionando?
8. **Prueba de limites:** Que pasa con inputs vacios, muy grandes, invalidos?

#### Salida

- Informe de tests (pasaron/fallaron)
- Cobertura de codigo
- Lista de criterios de exito verificados

#### Verificacion

- [ ] 100% de tests unitarios pasan
- [ ] Cobertura > 80% (o threshold definido)
- [ ] Linter sin errores
- [ ] Todos los criterios de exito de Fase 1 se cumplen
- [ ] Documentacion tecnica actualizada (README, API docs, changelog)
- [ ] Pruebas de regresion pasan

#### Caso concreto (Django+GraphQL)

```python
# tests/test_shortener.py
import pytest
from graphene_django.utils import GraphQLTestCase
from shortener.models import URL

class URLTestCase(GraphQLTestCase):
    def test_create_url_mutation(self):
        response = self.query(
            '''
            mutation {
                createUrl(fullUrl:"https://example.com") {
                    url { id fullUrl urlHash clicks }
                }
            }
            ''')
        content = response.json()
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["createUrl"]["url"]["fullUrl"],
                         "https://example.com")

    def test_urls_query_empty(self):
        response = self.query('''query { urls { id fullUrl } }''')
        content = response.json()
        self.assertResponseNoErrors(response)
        self.assertEqual(content["data"]["urls"], [])

    def test_invalid_url_returns_error(self):
        response = self.query(
            '''mutation { createUrl(fullUrl:"not_valid") { url { id } } }''')
        content = response.json()
        self.assertIn("errors", content)
        self.assertEqual(content["errors"][0]["message"], "invalid url")

    def test_url_redirect(self):
        url = URL.objects.create(full_url="https://example.com")
        response = self.client.get(f"/{url.url_hash}/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://example.com")

    def test_filter_urls(self):
        URL.objects.create(full_url="https://example.com/community")
        URL.objects.create(full_url="https://example.com/blog")
        response = self.query(
            '''query { urls(url:"community") { fullUrl } }''')
        content = response.json()
        self.assertEqual(len(content["data"]["urls"]), 1)

    def test_pagination(self):
        for i in range(5):
            URL.objects.create(full_url=f"https://example.com/{i}")
        response = self.query(
            '''query { urls(first:2, skip:1) { fullUrl } }''')
        content = response.json()
        self.assertEqual(len(content["data"]["urls"]), 2)
```

---

### Fase 7: Despliegue (Deployment / Release)

**Objetivo:** Publicar el software en el entorno destino (produccion,
staging, o ambiente del cliente).

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Codigo verificado (Fase 6) |
| **Objetivo** | Software accesible por los usuarios finales |
| **Duracion tipica** | 0.5-2 dias |
| **Metodologia** | CI/CD, releases semver, Git tags |

#### Actividades

1. **Versionar el release** (semver: v1.0.0, v1.1.0, etc.)
2. **Crear tag en Git** (`git tag v1.0.0`)
3. **Empaquetar el proyecto** (wheel, container, binary)
4. **Desplegar en entorno destino** (servidor, PaaS, SaaS)
5. **Ejecutar smoke tests** en produccion (endpoint responde, health check)
6. **Documentar el release** (changelog, notas de version)

#### Salida

- Tag de version en el repositorio
- Artefacto de release (archivo .whl, .tar.gz, imagen Docker)
- Entorno destino con el software funcionando
- Notas de version (changelog)

#### Verificacion

- [ ] Smoke tests en produccion pasan
- [ ] Version semver correctamente asignada
- [ ] Changelog actualizado
- [ ] Rollback plan documentado

#### Caso concreto (Django+GraphQL)

```yaml
Version: v1.0.0
Stack: Django 2.1.7 + Graphene-Django 2.2.0 + SQLite
Despliegue: localhost (desarrollo) / servidor PythonAnywhere (produccion)
Comandos:
  - pip install -r requirements.txt
  - python manage.py migrate
  - python manage.py runserver 0.0.0.0:8000
Smoke tests:
  - curl http://localhost:8000/graphql -H "Content-Type: application/json" \
    -d '{"query":"{ urls { id } }"}'
  - curl -I http://localhost:8000/077880af78
Rollback: git revert + redeploy version anterior
```

---

### Fase 8: Operacion (Operations / Maintenance)

**Objetivo:** Mantener el software funcionando, monitorizar su salud, y
gestionar cambios post-lanzamiento.

| Elemento | Descripcion |
|----------|-------------|
| **Entrada** | Software desplegado (Fase 7) |
| **Objetivo** | Sistema estable, monitorizado y mejorable |
| **Duracion tipica** | Continua |
| **Metodologia** | DevOps, monitorizacion, SLIs/SLOs/SLAs |

#### Actividades

1. **Monitorizar la salud del sistema** (logs, errores, metricas)
2. **Gestionar incidencias** (bugs reportados por usuarios)
3. **Aplicar parches de seguridad** (dependencias desactualizadas)
4. **Iterar** (nuevas features, mejoras, refactors)
5. **Gestionar el ciclo de vida de datos** (backups, limpieza)
6. **Documentar lecciones aprendidas** (retrospectiva)

#### Salida

- Logs y metricas del sistema en produccion
- Lista de incidencias gestionadas
- Plan de iteraciones futuras
- Documentacion post-mortem de incidencias

#### Verificacion

- [ ] Logs estructurados accesibles (stdout/stderr, no archivos locales)
- [ ] Health endpoint responde (GET /health → {"status": "ok"})
- [ ] Backup de datos configurado (si aplica)
- [ ] Proximo ciclo de iteracion planificado

#### Caso concreto (Django+GraphQL)

```python
# health/views.py (post-lanzamiento)
from django.http import JsonResponse
from django.db import connection

def health(request):
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception:
        db_ok = False
    return JsonResponse({
        "status": "ok" if db_ok else "degraded",
        "version": "1.0.0",
        "db_connected": db_ok
    })
```

---

## 3. Mapa: Tutorial → Fases del Ciclo de Vida

Aplicacion concreta del marco al tutorial de Django+GraphQL:

| Paso del tutorial | Fase | Actividad | Artefacto generado |
|------------------|------|-----------|-------------------|
| (n/a) | INICIO | Definir proyecto, stack, criterios | Acta de proyecto |
| (n/a) | PLAN | WBS de 19 tareas, grafo dependencias | Plan de proyecto |
| (n/a) | DISENO | Arquitectura, modelo datos, ADRs | Doc de arquitectura |
| Paso 1 (parte 1) | CONFIG | pip install, startproject, migrate | Entorno funcional |
| Paso 1 (parte 2) | CODIF | Configurar settings.py | Codigo de configuracion |
| Paso 2 | CODIF | Crear app, modelo, migrar | Modelo URL |
| Paso 3 | CODIF | URLType, Query, schema, endpoint | GraphQL Query |
| Paso 4 | CODIF | Mutation CreateURL | GraphQL Mutation |
| Paso 5 | CODIF | Vista root, URL pattern | Redireccion |
| Paso 6 | CODIF | Validacion de errores | Manejo de errores |
| Paso 7 | CODIF | Filtro por nombre | Filtrado |
| Paso 8 | CODIF | Paginacion first/skip | Paginacion |
| (n/a) | VERIF | Tests unitarios + integracion | Suite de tests |
| (n/a) | DESPL | Tag v1.0.0, deploy local | Release |
| (n/a) | OPERA | Health endpoint, monitorizacion | Sistema en operacion |

---

## 4. Artefactos por Fase (Checklist Generico)

| Fase | Artefacto | Formato | Obligatorio? |
|------|-----------|---------|-------------|
| INICIO | Acta de proyecto | .md | Si |
| INICIO | README.md inicial | .md | Si |
| INICIO | .gitignore | archivo | Si |
| INICIO | Stack decision record | .md | Si |
| PLAN | WBS (Work Breakdown Structure) | .md / .csv | Si |
| PLAN | Grafo de dependencias | diagrama / lista | Si |
| PLAN | Estimaciones de esfuerzo | tabla | Recomendado |
| PLAN | Hitos (milestones) | lista | Si |
| DISENO | Diagrama de contexto (C4 L1) | diagrama | Si |
| DISENO | Diagrama de contenedores (C4 L2) | diagrama | Recomendado |
| DISENO | Modelo de datos (ERD) | diagrama / .md | Si |
| DISENO | ADRs (Architecture Decision Records) | .md | Recomendado |
| DISENO | Contratos de API | .md / schema | Si |
| CONFIG | requirements.txt / package.json | archivo | Si |
| CONFIG | Entorno virtual / Dockerfile | archivo | Si |
| CONFIG | Configuracion de linter (.flake8, etc.) | archivo | Recomendado |
| CODIF | Codigo fuente | archivos | Si |
| CODIF | Tests unitarios | archivos | Si |
| CODIF | Commits descriptivos | git log | Si |
| VERIF | Informe de tests | stdout / .md | Si |
| VERIF | Reporte de cobertura | .html / .xml | Recomendado |
| VERIF | Criterios de exito verificados | checklist | Si |
| DESPL | Tag de version (v1.0.0) | git tag | Si |
| DESPL | Notas de version (changelog) | .md | Si |
| DESPL | Artefacto de release | .whl / .tar.gz | Si |
| OPERA | Logs estructurados | stdout | Si |
| OPERA | Health endpoint | codigo | Recomendado |
| OPERA | Plan de iteraciones futuras | .md | Recomendado |

---

## 5. Integracion con State Machine de RECPL

El marco se alinea con el patron de maquina de estados definido en AGENTS.md:

```
AGENTS.md state machine:
  analyze → propose → approve → plan → approve → execute → verify

Marco de ciclo de vida (mapeo):
  INICIO      → analyze (analizar problema, stakeholders, viabilidad)
  INICIO      → propose (proponer stack, alcance, criterios)
  INICIO      → approve (aprobar acta de proyecto)
  PLAN        → plan (descomponer en tareas, estimar)
  PLAN        → approve (aprobar plan)
  DISENO      → analyze (analizar opciones arquitectonicas)
  DISENO      → propose (proponer arquitectura)
  DISENO      → approve (aprobar ADRs)
  CONFIG      → execute (ejecutar setup de entorno)
  CODIF       → execute (ejecutar implementacion)
  VERIF       → verify (verificar criterios de exito)
  DESPL       → execute (ejecutar despliegue)
  OPERA       → analyze (analizar metricas y feedback)
```

Cada transicion entre fases requiere una **verificacion explicita** antes de
avanzar. No se puede pasar a CODIF sin haber verificado CONFIG.

---

## 6. Principios del Marco

1. **Secuencial por fase, iterativo por feature:** Las fases 1-4 son
   secuenciales (no se puede planificar sin iniciar). Las fases 5-8 son
   iterativas (cada feature pasa por CODIF → VERIF → DESPL → OPERA).

2. **Verificacion en cada frontera:** No se avanza a la siguiente fase
   sin verificar que la actual esta completa. Esto previene el avance
   con deuda tecnica.

3. **Artefactos sobre procesos:** El marco valora los documentos y
   decisiones registradas sobre la adherencia ritualistica a una metodologia.
   Cada artefacto tiene un proposito: comunicar, decidir, o verificar.

4. **Adaptable al contexto:** Un proyecto de 1 persona en una tarde puede
   comprimir las 8 fases en 30 minutos. Un proyecto enterprise de 12 meses
   puede extender cada fase a semanas. El marco se escala, no se impone.

5. **Trazabilidad:** Cada decision, tarea y artefacto se conecta a traves
   del ciclo de vida. El WBS de Fase 2 se usa hasta Fase 8.

6. **El tutorial es un caso particular del marco:** Un tutorial tipico
   cubre CONFIG + CODIF + VERIF parcial. El marco anade INICIO, PLAN,
   DISENO, DESPL y OPERA para completar el ciclo.

---

## 7. Proyecto Minimo: Aplicacion Rapida del Marco

Para proyectos pequenos (como el tutorial de Django+GraphQL), el marco se
puede comprimir en una checklist de una pagina:

```yaml
# checklist.yaml — Marco rapido para proyectos pequenos
fase_1_inicio:
  - problema definido
  - stack elegido (Python, Django, Graphene, SQLite)
  - repo creado con .gitignore
  - criterios de exito: 7 items (ver Fase 1)

fase_2_plan:
  - WBS creado: 19 tareas
  - dependencias graficadas
  - esfuerzo estimado (~8h total)

fase_3_diseno:
  - diagrama de contexto
  - modelo de datos (URL)
  - contratos de API (GraphQL schema)
  - ADRs: 2 (SQLite, MD5)

fase_4_config:
  - entorno virtual creado
  - django/graphene instalados
  - proyecto base arranca

fase_5_codificacion:
  - 7 iteraciones completadas (Pasos 2-8)
  - commits: 7+
  - docstrings y README de modulo actualizados

fase_6_verificacion:
  - tests: 6 casos (ver Fase 6)
  - criterios de exito: 7/7 verificados
  - documentacion tecnica revisada y actualizada

fase_7_despliegue:
  - tag v1.0.0
  - runserver funcionando
  - smoke tests pasan
  - changelog actualizado con notas de version

fase_8_operacion:
  - health endpoint creado
  - logs estructurados
  - runbook de operacion documentado
```

---

## 8. Referencias

- ISO/IEC 12207:2017 — Systems and software engineering — Software life cycle processes
- PMBOK Guide 7th Edition — Project Management Institute
- Agile Manifesto (2001) — beck, beedle, van Bennekum, et al.
- DevOps Handbook — Kim, Humble, Debois, Willis
- C4 Model — Simon Brown (c4model.com)
- ADR — Michael Nygard (documenting architecture decisions)
- RECPL State Machine — `AGENTS.md` (analyze → propose → approve → plan → approve → execute → verify)
- Tutorial de referencia — `template/tutorial.md` (Django + GraphQL + Graphene)
- Marco de tutorial executor — `docs/018_PROP_DEV_COMPILER_BOT_TUTORIAL_EXEC_1_0_DRAFT.md`

---

## 9. Documentacion como Actividad Transversal

**Objetivo:** La documentacion no es una fase aislada sino una actividad
continua que atraviesa todo el ciclo de vida. Cada fase produce, consume
o actualiza documentacion.

### 9.1 Principios de Documentacion

1. **Documentacion sincronizada:** Todo cambio en codigo debe reflejarse
   en la documentacion correspondiente en el mismo ciclo de trabajo.
2. **Documentacion como requisito de verificacion:** Una fase no se
   considera completa si su documentacion asociada no esta actualizada.
3. **Formato estandar:** Toda documentacion del proyecto sigue el esquema
   YAML frontmatter definido en `ALGP003_CONVENCION_DOCUMENTACION_v1_0_DRAFT.md`.
4. **Documentacion en el repositorio:** La documentacion vive junto al
   codigo fuente en el mismo repositorio (`docs/`), no en sistemas externos.

### 9.2 Documentacion por Fase

| Fase | Que documentar | Formato | Donde |
|------|---------------|---------|-------|
| INICIO | Acta de proyecto, stack decision, stakeholders | YAML + Markdown | `docs/` |
| PLAN | WBS, dependencias, estimaciones, hitos | Markdown / CSV | `docs/` |
| DISENO | Diagramas, ADRs, contratos de API, modelo datos | Markdown + diagramas | `docs/` |
| CONFIG | Instrucciones de setup, dependencias, variables de entorno | README.md, `.env.example` | Raiz del repo |
| CODIF | Docstrings, comentarios de API, README de modulos | Codigo + Markdown | Inline + `docs/` |
| VERIF | Informe de tests, criterios verificados, cobertura | Markdown / salida CI | `docs/` o CI artifact |
| DESPL | Notas de version, changelog, guia de despliegue | Markdown | `docs/` + CHANGELOG.md |
| OPERA | Runbook, health check, backup plan, lecciones aprendidas | Markdown | `docs/` |

### 9.3 Verificacion de Documentacion

La verificacion de documentacion se integra en cada fase:

- [ ] Los artefactos de la fase estan documentados segun el formato estandar
- [ ] README.md refleja el estado actual del proyecto
- [ ] CHANGELOG.md registra los cambios de esta fase
- [ ] La documentacion es accesible desde el repositorio
- [ ] No hay documentacion huerfana (docs de features eliminadas o irrelevantes)

### 9.4 Relacion con RECPL

El pipeline RECPL puede generar documentacion automaticamente a partir de
templates y del IR:

```
IR (con metadatos de documentacion) → synthesis.sh
  → scaffold.sh renderiza templates de documentacion
  → docs/ con frontmatter YAML y contenido generado
```

Esto permite que cada instruccion en lenguaje natural procesada por RECPL
produzca tanto codigo como su documentacion asociada.
