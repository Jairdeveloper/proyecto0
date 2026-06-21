---
id: 027
area: dev
type: prop
module: compiler-bot
version: 1.0
status: IMPLEMENTED
tags:
  - prop
  - improvement
  - recpl
  - cli
  - batch
  - command-mode
  - file-mode
  - implemented
summary: "Propuesta de mejora para agregar las banderas -c/--command y -f/--file al bucle RECPL. Estas banderas permiten ejecutar instrucciones desde la linea de comandos o desde un archivo, extendiendo los modos de operacion del bot sin romper la compatibilidad hacia atras."
keywords:
  - recpl
  - mejora
  - cli
  - banderas
  - command
  - file
  - batch
  - shell
  - usabilidad
  - recpl.sh
changelog:
  - version: 1.0
    date: 2026-06-11
    author: workflow-agent
    description: Documentacion de la mejora -c/-f en recpl.sh
---

# Mejora: Banderas -c/--command y -f/--file para recpl.sh

> **Archivo modificado:** `compiler-bot/recpl.sh`
> **Version:** 1.0.0 → 1.2.0
> **Tests:** 72/72 pasan

---

## 0. Resumen

Se agregaron dos nuevas banderas al bucle principal RECPL:

| Bandera | Forma larga | Funcion |
|---------|-------------|---------|
| `-c` | `--command` | Ejecuta una instruccion desde el argumento y termina |
| `-f` | `--file` | Ejecuta las instrucciones de un archivo y termina |

Esto completa los 4 modos de operacion del bot:

```
recpl.sh
  ├── modo interactivo  (sin args, stdin terminal)
  ├── modo batch        (sin args, stdin pipe)
  ├── modo comando      (-c "instruccion")
  └── modo archivo      (-f instrucciones.txt)
```

---

## 1. Motivacion

### 1.1 Problema original

Antes de esta mejora, `recpl.sh` tenia solo dos modos de operacion,
determinados por la deteccion de terminal en stdin (`[ -t 0 ]`):

| Modo | Como se activa | Limitacion |
|------|----------------|------------|
| Interactivo | Ejecutar sin pipe | Requiere terminal |
| Batch | Pipe desde stdin | No permite instruccion inline ni archivo |

No habia forma de:

- Ejecutar una sola instruccion desde un script o Makefile sin usar `echo |`
- Procesar un archivo de instrucciones sin redireccion manual
- Integrar el bot en pipelines de CI/CD de forma limpia

### 1.2 Soluciones anteriores (workarounds)

Los usuarios tenian que recurrir a:

```sh
# Inchado: echo + pipe para una sola instruccion
echo "crea modulo pagos en nestjs" | ./recpl.sh

# Redireccion para archivo
./recpl.sh < instrucciones.txt
```

Ambos funcionan pero son menos explicitos y dificultan la integracion
en scripts donde se mezclan argumentos y pipes.

---

## 2. Decision de Diseno

### 2.1 Convencion seguida

Se siguio la convencion POSIX/UNIX de herramientas establecidas:

| Herramienta | Comando | Archivo |
|-------------|---------|---------|
| `bash` | `bash -c "comando"` | `bash archivo.sh` |
| `psql` | `psql -c "SELECT 1"` | `psql -f script.sql` |
| `redis-cli` | `redis-cli GET key` | `redis-cli < script.txt` |
| `python` | `python -c "print(1)"` | `python script.py` |
| `awk` | `awk -v x=1` | `awk -f programa.awk` |
| **RECPL** | **`recpl.sh -c "instruccion"`** | **`recpl.sh -f archivo.txt`** |

### 2.2 Decisiones especificas

| Decision | Opcion elegida | Alternativa descartada |
|----------|---------------|----------------------|
| Flag corto | `-c` (command), `-f` (file) | Usar `-e` como `bash -e` (conflictivo con `set -e`) |
| Flag largo | `--command`, `--file` | `--exec`, `--run`, `--source` (menos estandar) |
| Separacion de argumento | Espacio: `-c "texto"` | `-c"texto"` (menos legible, dificil de parsear en shell) |
| Archivo no encontrado | Error a stderr + exit 1 | Fallo silencioso (peligroso) |
| Estado | init + process + cleanup por invocacion | Estado compartido entre multiples `-c` (innecesario) |

### 2.3 Compatibilidad hacia atras

La mejora es **100% compatible**:

- Los modos existentes (interactivo y batch) no se modificaron
- Las banderas se parsean **antes** que la logica de deteccion de terminal
- Sin banderas, el comportamiento es identico a v1.0.0

---

## 3. Implementacion

### 3.1 Funciones nuevas

Dos funciones envolventes que orquestan init → process → cleanup:

**`command_mode(instruction)`:**
```sh
command_mode() {
    instruction="$1"
    init_state
    process_instruction "$instruction"
    cleanup
}
```

**`file_mode(filepath)`:**
```sh
file_mode() {
    filepath="$1"
    # validar que existe y es legible
    init_state
    while read -r line; do
        process_instruction "$line"
    done < "$filepath"
    cleanup
}
```

Ambas son "wrappers del wrapper": envuelven el pipeline completo
(init → process → cleanup) en una sola invocacion, a diferencia del
modo interactivo que mantiene el estado vivo entre iteraciones.

### 3.2 Parseo de argumentos

El parseo ocurre al inicio de `main()`, antes de cualquier otra logica:

```sh
main() {
    case "${1:-}" in
        -c|--command) command_mode "$2"; exit $? ;;
        -f|--file)    file_mode "$2";    exit $? ;;
    esac
    # ... resto de la logica (help, version, interactivo, batch)
}
```

El caso especial `"${1:-}"` evita errores si no hay argumentos
(devuelve string vacio en lugar de error).

### 3.3 Validacion de argumentos

Ambas banderas validan que el argumento requerido exista:

```sh
if [ -z "${2:-}" ]; then
    echo "Error: -c/--command requiere un argumento" >&2
    exit 1
fi
```

`file_mode()` ademas valida que el archivo exista y sea legible.

### 3.4 Manejo de errores

- Si el archivo no existe: error a stderr + exit 1
- Si el archivo no es legible: error a stderr + exit 1
- Si la instruccion falla en el pipeline: se produce JSON de error
  (igual que en modo batch/interactivo)
- El `exit $?` en main propaga el codigo de salida de `command_mode`
  o `file_mode` (aunque actualmente siempre es 0)

---

## 4. Modos de Operacion Comparativos

| Aspecto | Interactivo | Batch (pipe) | Comando (-c) | Archivo (-f) |
|---------|-------------|--------------|--------------|--------------|
| Invocacion | `./recpl.sh` | `echo "x" \| ./recpl.sh` | `./recpl.sh -c "x"` | `./recpl.sh -f archivo` |
| Input | Terminal (stdin) | Pipe (stdin) | Argumento `$2` | Archivo en disco |
| Estado | Persiste entre instrucciones | Persiste entre instrucciones | Init → cleanup por llamada | Init → cleanup por archivo |
| Prompt | Si (`>`) | No | No | No |
| Banner | Si | No | No | No |
| Comandos especiales | quit, help, version | quit, help | Ninguno | quit |
| Uso tipico | Exploracion, debugging | Scripts simples | CI/CD, Makefile, scripts | Procesamiento por lotes |
| stdout | JSON respuesta | JSON respuesta | JSON respuesta | JSON respuesta (una por linea) |
| stderr | Solo logs | Solo logs | Errores de validacion | Errores de validacion |

---

## 5. Ejemplos de Uso

### 5.1 Modo comando (-c)

```sh
# Una instruccion, una respuesta
./recpl.sh -c "crea un modulo de pagos en NestJS"

# Con estado: CREATE + READ en la misma sesion NO es posible con -c
# (cada -c crea un estado nuevo)
```

### 5.2 Modo archivo (-f)

```sh
# archivo instrucciones.txt:
#   crea un modulo de pagos en NestJS
#   mostrar pagos
#   quit

./recpl.sh -f instrucciones.txt
```

### 5.3 Integracion en scripts

```sh
#!/bin/sh
# generate_module.sh - Genera un modulo NestJS desde un script

MODULE_NAME="$1"
TECH="${2:-NestJS}"

./recpl.sh -c "crea un modulo de ${MODULE_NAME} en ${TECH}"
```

### 5.4 Integracion en Makefile

```makefile
.PHONY: generate

generate:
	./compiler-bot/recpl.sh -c "crea un modulo de $(MODULE) en $(TECH)"
```

### 5.5 Integracion en CI/CD

```yaml
# .github/workflows/generate.yml
jobs:
  generate:
    steps:
      - run: ./compiler-bot/recpl.sh -c "crea un modulo de payments en NestJS"
      - run: ls modules/payments/
```

---

## 6. Impacto en Tests

Los 72 tests existentes pasan sin modificaciones porque:

| Test | Como se afecta |
|------|---------------|
| Syntax (bash -n) | `recpl.sh` sigue pasando bash -n |
| LOOP batch mode | No se modifico el modo batch |
| Pipeline completo | No se modifico el pipeline interno |
| Scaffolding | No se modifico scaffold.sh |

No se agregaron tests especificos para las nuevas banderas porque
el proyecto no tiene un framework de tests para flags de CLI
(las pruebas manuales confirman el funcionamiento).

---

## 7. Riesgos y Limitaciones

| Riesgo | Mitigacion |
|--------|------------|
| `-c` con instrucciones largas | Usar `-f` con archivo temporal |
| Archivos con BOM o encoding no-UTF8 | El preprocesador maneja NFKC |
| `-c` sin estado entre instrucciones | Usar modo interactivo o batch para sesiones multi-instruccion |
| Compatibilidad con shells no-bash | El script usa `#!/bin/sh` (POSIX), las nuevas funciones tambien |

---

## 8. Observaciones sobre el estado actual del proyecto

*Redactado al momento del commit `7cf8f86` (Junio 2026).*

### 8.1 Lo que ha cambiado desde esta propuesta

| Aspecto | Propuesta original (027) | Estado actual | Diferencia |
|---------|--------------------------|---------------|------------|
| Version de recpl.sh | 1.1.0 | 1.2.0 | Se agregaron flags `--llm`, `--provider` y comandos `source`/`exec` |
| Conteo de tests | 47 tests | 72 tests | +25 tests (LLM Fases L1-L4, composite Fase 1-3) |
| `file_mode()` | Loop inline propio | Delega en `composite_file()` | Refactorizado en composite Fase 1 para compartir logica con `source` |
| `batch_mode()` | Solo `quit`/`help`/`process_instruction` | Tambien `source` y `exec` | Mejora de Fase 2: se puede invocar archivos e instrucciones inline desde el pipe |
| `interactive_mode()` | Sin `source`/`exec` | Con `source` y `exec` como comandos internos | Mejora de Fase 2: estado compartido dentro de la sesion |
| `show_help()` | Sin mencion de source/exec | Muestra ambos comandos | Documentacion actualizada |
| Banderas disponibles | `-c`, `-f`, `--help`, `--version` | Ademas `--llm`, `--provider` | Extension LLM (Fases L1-L4 del plan 031) |
| Tests de CLI | "No se agregaron tests especificos" | Test 12 cubre source/exec via batch mode | Cobertura parcial (faltan tests directos de `-c` y `-f`) |

### 8.2 Implementacion efectiva vs. propuesta

La Seccion 3.1 muestra `file_mode()` con un loop inline:

```sh
# Como se propuso originalmente:
file_mode() {
    filepath="$1"
    init_state
    while read -r line; do
        process_instruction "$line"
    done < "$filepath"
    cleanup
}
```

En la implementacion actual, `file_mode()` delega en `composite_file()`
siguiendo el principio DRY y el patron composite:

```sh
# Como se implemento finalmente:
file_mode() {
    filepath="$1"
    init_state
    composite_file "$filepath"
    cleanup
}
```

La logica de lectura de archivo se movio a `composite_file()` para que
tanto `file_mode()` como el comando interno `source` compartan el mismo
codigo. Esto no estaba previsto en la propuesta original.

### 8.3 Limitaciones que persisten

- **Sin tests para `-c` y `-f` directos:** La suite de tests usa solo
  modo batch (pipe). Las banderas `-c` y `-f` no tienen tests
  automatizados; se verifican manualmente.
- **`-c` sin estado entre invocaciones:** Cada `-c` crea estado nuevo,
  igual que en la propuesta. Para sesiones multi-instruccion se debe
  usar modo interactivo, batch, o `source` con un archivo.
- **Sin validacion post-scaffold:** El pipeline genera archivos pero no
  verifica que el modulo resultante compile o pase tests de sintaxis.
- **Sin CI/CD:** Aunque la propuesta menciona integracion en CI/CD
  (Seccion 5.5), no hay pipelines automatizados configurados.

### 8.4 Lo que la propuesta predijo correctamente

| Prediccion | Se cumple | Nota |
|------------|-----------|------|
| 100% compatible hacia atras | Si | Todos los modos existentes funcionan igual |
| Estado init+process+cleanup por invocacion | Si | En `-c`, `-f` y `command_mode` |
| Error a stderr + exit 1 si archivo no existe | Si | En `file_mode()` y `composite_file()` |
| Parseo antes de deteccion de terminal | Si | Los flags se parsean antes de `[ -t 0 ]` |
| Formato `-c "texto"` con espacio | Si | `command_mode "$2"` |
| Sin modificacion al pipeline interno | Si | `process_instruction()` no se modifico |

---

## 9. Estado de Implementacion (Junio 2026)

*Seccion agregada post-implementacion al momento del commit `7cf8f86`.*

### 9.1 Resumen

| Aspecto | Estado |
|---------|--------|
| Estatus del documento | `DRAFT` — la implementacion existe pero el frontmatter no refleja el cambio |
| Banderas implementadas | `-c`/`--command` ✅, `-f`/`--file` ✅ |
| `command_mode()` | Implementado igual a la propuesta |
| `file_mode()` | Implementado con desviaciones (delega en `composite_file()`, no loop inline) |
| Parseo de argumentos | Implementado con validaciones explicitas (mas completo que la propuesta) |
| Banderas adicionales no previstas | `--llm`, `--provider`, `--help`, `--version` |
| Version actual de recpl.sh | 1.2.0 (la propuesta dice 1.1.0) |
| Tests | 72 pasan, 0 fallan (la propuesta dice 47) |

### 9.2 Correspondencia propuesta vs. implementacion

| Elemento propuesto (Seccion 3) | Implementado en recpl.sh | Lineas | Coincide |
|--------------------------------|--------------------------|--------|----------|
| `command_mode()`: init + process + cleanup | Igual a la propuesta | 167-172 | ✅ |
| `file_mode()`: init + while-read + cleanup | Delega en `composite_file()`, no loop inline | 175-191 | ⚠ Parcial |
| Validacion de archivo (existencia/permisos) | Implementado con if blocks + exit 1 | 178-186 | ✅ (propuesta solo lo tenia como comentario) |
| Parseo en main() antes de deteccion de terminal | Implementado | 311-328 | ✅ |
| `[ -z "${2:-}" ]` en flags | Implementado | 313, 321 | ✅ |
| Exit 1 si archivo no encontrado | Implementado | 180, 185 | ✅ |

### 9.3 Desviaciones respecto a la propuesta original

1. **`file_mode()` usa `composite_file()` en vez de loop inline** — La propuesta (Seccion 3.1) mostraba `file_mode()` con un `while read -r line` inline. En la implementacion real, la logica de lectura de archivo se extrajo a `composite_file()` (creada en composite Fase 1, doc 028) para compartir codigo con el comando `source`. `file_mode()` ahora es un wrapper de 3 lineas: `init_state; composite_file "$filepath"; cleanup`.

2. **Validacion de archivo explicita** — La propuesta tenia un comentario `# validar que existe y es legible` sin codigo. La implementacion real agrega dos bloques `if` con `exit 1` y mensajes de error a stderr.

3. **Flags no previstos `--llm` y `--provider`** — La propuesta no contemplaba la integracion con LLMs. Actualmente `main()` parsea estos flags antes que `-c`/`-f`, permitiendo combinaciones como `./recpl.sh --llm -c "instruccion"`.

4. **`batch_mode()` ampliado** — La propuesta (Seccion 4, tabla de modos) dice que batch tiene solo `quit` y `help` como comandos especiales. Actualmente `batch_mode()` tambien soporta `source` y `exec` (agregado en composite Fase 2).

5. **`--help` y `--version` como flags en main()** — La propuesta no menciona estos flags en el parseo de argumentos, aunque estan implementados en `recpl.sh:330-338`.

### 9.4 Exactitud de las estimaciones

| Aspecto | Propuesto | Real | Nota |
|---------|-----------|------|------|
| Lineas de codigo nuevas | ~25 lineas (command_mode + file_mode + parseo) | ~30 lineas | Incluye validaciones adicionales |
| Tests | 47/47 pasan sin modificaciones | 72/72 pasan | +25 tests de LLM y composite |
| Banderas totales | 4 (`-c`, `-f`, `--help`, `--version`) | 6 (+`--llm`, `--provider`) | Extension no prevista |
| Complejidad del parseo | `case "${1:-}" in ... esac` | `while` loop + `case` anidado | Por compatibilidad con `--llm` antepuesto |

### 9.5 Salud actual del codigo

- **`bash -n recpl.sh`**: Sin errores de sintaxis
- **`command_mode()`**: 6 lineas, identica a la propuesta
- **`file_mode()`**: 17 lineas (vs ~8 propuestas), mas robusta por validaciones y delegacion
- **Parseo de `-c`/`-f`**: Con validacion explicita de argumento faltante
- **Tests directos de `-c`/`-f`**: No existen (igual que en la propuesta, Seccion 6). Se verifican manualmente.

### 9.6 Frontmatter — corregido durante esta revision

| Campo | Antes | Despues |
|-------|-------|---------|
| `status` | `DRAFT` | `IMPLEMENTED` |
| `version` en resumen (header) | `1.0.0 → 1.1.0` | `1.0.0 → 1.2.0` |
| Tests en resumen (header y Seccion 6) | `47/47 pasan` | `72/72 pasan` |

### 9.7 Referencias

- `recpl.sh:167-172` — `command_mode()`
- `recpl.sh:175-191` — `file_mode()` (con delegacion a `composite_file()`)
- `recpl.sh:289-328` — Parseo de flags en `main()` (incluye `--llm`/`--provider`)
- `028_PROP_DEV_COMPILER_BOT_COMPOSITE_1_0_DRAFT.md` — Propuesta composite que refactorizo `file_mode()`
- `036_REP_DEV_COMPILER_BOT_COMPOSITE_FASE1_1_0_DRAFT.md` — Creacion de `composite_file()`
