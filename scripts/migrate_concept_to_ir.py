#!/usr/bin/env python3
"""Migrate project concept from 'Compilador NL a codigo [tech]' to 'Compilador NL a codigo IR'.

Updates all files to reflect the new concept.
Handles both manual contextual edits and bulk pattern replacements.
"""

import os
import re
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# === Manual contextual replacements (file-specific) ===

MANUAL_EDITS = {}

# AGENTS.md — Objetivo implicito block
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'AGENTS.md')] = [
    (
        '''> Construir un RECPL Compiler Bot — un compilador de lenguaje natural a
> codigo. Toma instrucciones en espanol ("crea un modulo de pagos en NestJS")
> y genera scaffolding de modulos NestJS, entidades y modelos Prisma.
> >
> El pipeline compilador (preprocess → lexer → parser → semantic → IR →
> synthesis) es el producto. NestJS/Prisma es el formato de salida, no un
> proyecto separado.''',
        '''> Construir un RECPL Compiler Bot — un compilador de lenguaje natural a
> codigo IR (Intermediate Representation). Toma instrucciones en lenguaje
> natural y produce una representacion intermedia canonica que describe la
> intencion del usuario en terminos de acciones, entidades y relaciones.
> >
> El pipeline compilador (preprocess → lexer → parser → semantic → IR →
> synthesis) es el producto. El IR es el formato de salida central; los
> generadores a codigo especifico (NestJS, Prisma, React, etc.) son
> plugins opcionales intercambiables.'''
    ),
]

# README.md — Title + description + pipeline
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'README.md')] = [
    (
        '# RECPL — Natural Language to NestJS/Prisma Scaffolding\n',
        '# RECPL — Natural Language to IR Compiler\n'
    ),
    (
        '**RECPL** (READ-EVAL-PRINT Compiler Loop) es un compilador de lenguaje\n'
        'natural a codigo. Toma instrucciones en espanol y genera scaffolding de\n'
        'modulos NestJS, entidades Prisma, componentes React, y mas.\n',
        '**RECPL** (READ-EVAL-PRINT Compiler Loop) es un compilador de lenguaje\n'
        'natural a codigo IR (Intermediate Representation). Toma instrucciones en\n'
        'lenguaje natural y produce una representacion intermedia canonica.\n'
        'Generadores opcionales traducen el IR a codigo especifico (NestJS, Prisma,\n'
        'React, etc.).\n'
    ),
    (
        '[ Synthesis ]       → generacion de codigo (NestJS/Prisma/React/...)',
        '[ Synthesis ]       → generacion de codigo IR (plugins opcionales)'
    ),
    (
        'OUTPUT: modules/pagos/pagos.controller.ts, schema.prisma, ...',
        'OUTPUT: IR canonico (JSON) → [opcional] codigo especifico'
    ),
]

# docs/index.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', 'index.md')] = [
    (
        'Compilador de lenguaje natural a codigo NestJS/Prisma/React.',
        'Compilador de lenguaje natural a codigo IR (Intermediate Representation).'
    ),
]

# docs/architecture/001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', 'architecture', '001_ARCH_REPORT_RECPL_V2_1_0_DRAFT.md')] = [
    (
        'RECPL Compiler Bot v2.0+ es un **compilador de lenguaje natural a código**. Toma instrucciones en español (ej. *"crea un módulo de pagos en NestJS"*) y genera scaffolding completo de módulos NestJS, entidades Prisma, componentes React, y configuraciones Docker/Next.js/Tailwind.',
        'RECPL Compiler Bot v2.0+ es un **compilador de lenguaje natural a código IR** (Intermediate Representation). Toma instrucciones en lenguaje natural y produce una representación intermedia canónica que describe la intención del usuario. Generadores opcionales traducen el IR a código específico (NestJS, Prisma, React, Docker, Next.js, Tailwind, etc.).'
    ),
]

# docs/136_GUIDE_DEV_PROJECT0_RUNBOOK_1_0_ACTIVE.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '136_GUIDE_DEV_PROJECT0_RUNBOOK_1_0_ACTIVE.md')] = [
    (
        'Proyecto0 implementa RECPL, un compilador de lenguaje natural a codigo. El',
        'Proyecto0 implementa RECPL, un compilador de lenguaje natural a codigo IR. El'
    ),
]

# compiler-bot/agent-robot/prompts/system_agent.txt
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'compiler-bot', 'agent-robot', 'prompts', 'system_agent.txt')] = [
    (
        'el pipeline RECPL (un compilador de lenguaje natural a codigo) y un conjunto',
        'el pipeline RECPL (un compilador de lenguaje natural a codigo IR) y un conjunto'
    ),
]

# docs/127_PROP_DEV_PIPELINE_HTTP_WRAPPER_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '127_PROP_DEV_PIPELINE_HTTP_WRAPPER_1_0_DRAFT.md')] = [
    (
        'El pipeline `agentic_pipeline` (RECPL v2.0) está diseñado como un **compilador de lenguaje natural a código** que ejecuta un StateGraph con 10+ PipelineStages conectados secuencialmente',
        'El pipeline `agentic_pipeline` (RECPL v2.0) está diseñado como un **compilador de lenguaje natural a código IR** que ejecuta un StateGraph con 10+ PipelineStages conectados secuencialmente'
    ),
]

# docs/082_REP_DEV_PROJECT0_COMPREHENSIVE_ANALYSIS_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '082_REP_DEV_PROJECT0_COMPREHENSIVE_ANALYSIS_1_0_DRAFT.md')] = [
    (
        'Proyecto0 es un **RECPL Compiler Bot** — un compilador de lenguaje natural a código que toma instrucciones en español (e.g., "crea un módulo de pagos en NestJS") y genera scaffolding de módulos NestJS/Prisma.',
        'Proyecto0 es un **RECPL Compiler Bot** — un compilador de lenguaje natural a código IR que toma instrucciones en lenguaje natural y produce una representación intermedia canónica. Generadores opcionales traducen el IR a código específico (NestJS, Prisma, React, etc.).'
    ),
]

# docs/178_ANALYSIS_DEV_COMPREHENSIVE_TECHNICAL_REPORT_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '178_ANALYSIS_DEV_COMPREHENSIVE_TECHNICAL_REPORT_1_0_DRAFT.md')] = [
    (
        'RECPL (READ-EVAL-PRINT Compiler Loop) es un **compilador de lenguaje natural a codigo**. Toma instrucciones en espanol como *"crea un modulo de pagos en NestJS"* y genera scaffolding de modulos NestJS, entidades Prisma, componentes React, configuracion Docker, y mas.',
        'RECPL (READ-EVAL-PRINT Compiler Loop) es un **compilador de lenguaje natural a codigo IR**. Toma instrucciones en lenguaje natural y produce una representacion intermedia canonica. Generadores opcionales traducen el IR a codigo especifico (NestJS, Prisma, React, Docker, etc.).'
    ),
]

# docs/091_REP_MGT_MULTI_PERSPECTIVE_ANALYSIS_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '091_REP_MGT_MULTI_PERSPECTIVE_ANALYSIS_1_0_DRAFT.md')] = [
    (
        'Proyecto0 (RECPL Compiler Bot v2.0) es un compilador de lenguaje natural',
        'Proyecto0 (RECPL Compiler Bot v2.0) es un compilador de lenguaje natural a codigo IR'
    ),
]

# docs/114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md — line 30
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '114_REP_DEV_ARCHITECTURAL_REVIEW_ISO12207_1_0_DRAFT.md')] = [
    (
        '**Proyecto0** se redefine de "compilador de lenguaje natural a codigo NestJS/Prisma"',
        '**Proyecto0** se redefine de "compilador de lenguaje natural a codigo NestJS/Prisma" a "compilador de lenguaje natural a codigo IR"'
    ),
    (
        '**Problema:** El pipeline RECPL actual es un compilador de lenguaje natural',
        '**Problema:** El pipeline RECPL actual es un compilador de lenguaje natural a codigo IR'
    ),
]

# docs/024_REP_DEV_PROJECT_DIAGNOSTIC_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '024_REP_DEV_PROJECT_DIAGNOSTIC_1_0_DRAFT.md')] = [
    (
        '> Construir un **RECPL Compiler Bot** — un compilador de lenguaje natural a codigo.',
        '> Construir un **RECPL Compiler Bot** — un compilador de lenguaje natural a codigo IR.'
    ),
    (
        '**Que es @Proyecto0:** Un compilador de lenguaje natural a codigo (RECPL).',
        '**Que es @Proyecto0:** Un compilador de lenguaje natural a codigo IR (RECPL).'
    ),
]

# docs/061_GUIDE_DEV_COMPILER_BOT_TUI_BEHAVIOR_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '061_GUIDE_DEV_COMPILER_BOT_TUI_BEHAVIOR_1_0_DRAFT.md')] = [
    (
        'Un compilador de lenguaje natural a codigo NestJS/Prisma.',
        'Un compilador de lenguaje natural a codigo IR.'
    ),
]

# docs/023_REP_MGT_PROJECT_ANALYSIS_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '023_REP_MGT_PROJECT_ANALYSIS_1_0_DRAFT.md')] = [
    (
        'La semilla del proyecto (compilador de lenguaje natural → codigo) esta operativa.',
        'La semilla del proyecto (compilador de lenguaje natural → codigo IR) esta operativa.'
    ),
]

# docs/049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '049_PLAN_DEV_COMPILER_BOT_AGENT_EXECUTION_1_0_DRAFT.md')] = [
    (
        'el pipeline RECPL (un compilador de lenguaje natural a codigo) y un conjunto',
        'el pipeline RECPL (un compilador de lenguaje natural a codigo IR) y un conjunto'
    ),
]

# docs/030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md — both occurrences
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '030_REP_MGT_COMPILER_BOT_LLM_INTEGRATION_1_0_DRAFT.md')] = [
    (
        '"system": "Eres un compilador de lenguaje natural..."',
        '"system": "Eres un compilador de lenguaje natural a codigo IR..."',
    ),
    (
        'Eres un compilador de lenguaje natural a codigo (RECPL).',
        'Eres un compilador de lenguaje natural a codigo IR (RECPL).',
    ),
]

# docs/031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md — 3 occurrences
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', '031_PLAN_DEV_COMPILER_BOT_LLM_EXECUTION_1_0_DRAFT.md')] = [
    (
        'Eres un compilador de lenguaje natural a codigo (RECPL).',
        'Eres un compilador de lenguaje natural a codigo IR (RECPL).',
    ),
]

# archive files

MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', 'archive', '033_REP_DEV_COMPILER_BOT_LLM_FASE_L2_1_0_DRAFT.md')] = [
    (
        'Eres un compilador de lenguaje natural a codigo (RECPL).',
        'Eres un compilador de lenguaje natural a codigo IR (RECPL).',
    ),
]

MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', 'archive', '059_GUIDE_DEV_COMPILER_BOT_ARCHITECTURE_1_0_DRAFT.md')] = [
    (
        'summary: "Guia de arquitectura de Proyecto0(RECPL). Explica de forma sencilla como funciona el compilador de lenguaje natural a codigo, sus componentes principales, el flujo de datos, y como conviven el pipeline deterministico, el agente inteligente y los generadores de codigo."',
        'summary: "Guia de arquitectura de Proyecto0(RECPL). Explica de forma sencilla como funciona el compilador de lenguaje natural a codigo IR, sus componentes principales, el flujo de datos, y como conviven el pipeline deterministico, el agente inteligente y los generadores de codigo."',
    ),
    (
        'Proyecto0 funciona como un **compilador de lenguaje natural**: toma texto',
        'Proyecto0 funciona como un **compilador de lenguaje natural a codigo IR**: toma texto',
    ),
]

MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', 'archive', '047_PROP_DEV_COMPILER_BOT_AGENT_CONCEPT_1_0_DRAFT.md')] = [
    (
        'summary: "Analisis y propuesta de nuevo concepto para Proyecto0: de un compilador de lenguaje natural que genera scaffolding NestJS/Prisma a un agente de IA de codigo abierto multi-proposito para desarrollo de software. Define alcance, analisis de viabilidad, mapeo contra el codigo existente, arquitectura de agentes, y plan de migracion."',
        'summary: "Analisis y propuesta de nuevo concepto para Proyecto0: de un compilador de lenguaje natural a codigo IR a un agente de IA de codigo abierto multi-proposito para desarrollo de software. Define alcance, analisis de viabilidad, mapeo contra el codigo existente, arquitectura de agentes, y plan de migracion."',
    ),
    (
        '> "compilador de lenguaje natural a scaffolding NestJS/Prisma" a un',
        '> "compilador de lenguaje natural a codigo IR" a un',
    ),
    (
        'El pipeline RECPL actual implementa un **compilador de lenguaje natural** que',
        'El pipeline RECPL actual implementa un **compilador de lenguaje natural a codigo IR** que',
    ),
]

# compiler-bot/frontend/llm_classifier.sh
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'compiler-bot', 'frontend', 'llm_classifier.sh')] = [
    (
        'Eres un compilador de lenguaje natural a codigo (RECPL).',
        'Eres un compilador de lenguaje natural a codigo IR (RECPL).',
    ),
]

# docs/archive/026_GUIDE_DEV_COMPILER_BOT_LOOP_1_0_DRAFT.md
MANUAL_EDITS[os.path.join(PROJECT_ROOT, 'docs', 'archive', '026_GUIDE_DEV_COMPILER_BOT_LOOP_1_0_DRAFT.md')] = [
    (
        'adaptado a un compilador de lenguaje natural:',
        'adaptado a un compilador de lenguaje natural a codigo IR:',
    ),
]


def apply_manual_edits():
    modified = []
    for filepath, edits in MANUAL_EDITS.items():
        if not os.path.exists(filepath):
            print(f"  SKIP (not found): {filepath}")
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        changed = False
        for old, new in edits:
            if old in content:
                content = content.replace(old, new)
                changed = True
            else:
                print(f"  WARN: pattern not found in {os.path.relpath(filepath, PROJECT_ROOT)}")
        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            modified.append(os.path.relpath(filepath, PROJECT_ROOT))
            print(f"  MODIFIED: {os.path.relpath(filepath, PROJECT_ROOT)}")
    return modified


def main():
    print("=== Fase 1 — Migracion de Concepto: Compilador NL -> IR ===\n")
    
    print("--- Manual contextual edits ---")
    modified = apply_manual_edits()
    
    print(f"\nTotal files modified: {len(modified)}")
    print("\nDone.")


if __name__ == '__main__':
    main()
