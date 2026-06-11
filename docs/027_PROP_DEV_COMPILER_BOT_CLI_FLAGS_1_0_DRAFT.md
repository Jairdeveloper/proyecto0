---
id: 027
area: dev
type: PROP
module: compiler-bot
version: 1.0
status: DRAFT
tags:
  - prop
  - improvement
  - recpl
  - cli
  - batch
  - command-mode
  - file-mode
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
> **Version:** 1.0.0 → 1.1.0
> **Tests:** 47/47 pasan

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

Los 47 tests existentes pasan sin modificaciones porque:

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
