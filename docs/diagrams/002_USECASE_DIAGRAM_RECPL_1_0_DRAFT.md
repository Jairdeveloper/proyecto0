---
id: "D02"
area: dev
type: diagram
module: recpl_usecase
version: "1.0"
status: ACTIVE
tags: ["uml", "usecase-diagram", "requirements"]
summary: "Diagrama de casos de uso del pipeline RECPL mostrando actores, funcionalidades y limites del sistema"
---

# Diagrama de Casos de Uso — RECPL Compiler Bot v2.0+

```mermaid
graph TB
    %% =========================================================================
    %% ACTORS
    %% =========================================================================
    User(("Usuario"))
    Developer(("Desarrollador"))
    SystemAdmin(("Admin Sistema"))
    LLM_Service("LLM API\n(externo)")
    FileSystem("Sistema Archivos\n(externo)")

    %% =========================================================================
    %% SYSTEM BOUNDARY
    %% =========================================================================
    subgraph "RECPL Compiler Bot v2.0+"
        direction TB

        %% --- Prompt Chain Subsystem ---
        subgraph "Prompt Chain\n(prompt_chain/)"
            PC_Process["Interpretar Lenguaje Natural"]
            PC_Preprocess["Normalizar Texto"]
            PC_Intent["Clasificar Intencion"]
            PC_Plan["Descomponer en Tareas"]
            PC_Generate["Generar Codigo"]
            PC_Verify["Validar Resultado"]
            PC_Format["Formatear Respuesta"]
        end

        %% --- Pipeline Stages ---
        subgraph "Pipeline RECPL\n(nodes/)"
            PL_Perception["Analizar Entrada"]
            PL_Preprocess["Preprocesar Texto"]
            PL_Lexer["Tokenizar con DFA"]
            PL_Parser["Construir AST con GLR"]
            PL_Semantic["Validar Semantica"]
            PL_IR["Generar IR Canónico"]
            PL_Planner["Planificar Ejecucion"]
            PL_Synthesis["Sintetizar Codigo"]
            PL_UI["Generar UI"]
            PL_Validate["Validar Salida"]
        end

        %% --- Multi-Agent System ---
        subgraph "Sistema Multi-Agente\n(agents/)"
            MA_Supervise["Supervisar Flujo"]
            MA_Perceive["Percibir Entrada"]
            MA_Reason["Razonar Objetivo"]
            MA_Execute["Ejecutar Acciones"]
            MA_Validate["Validar Resultados"]
        end

        %% --- Supporting ---
        subgraph "Soporte"
            S_Command["Ejecutar Commandos"]
            S_Metrics["Registrar Metricas"]
            S_Fallback["Ejecutar Fallback"]
            S_Cache["Cachear LLM"]
            S_SymbolTable["Gestionar Tabla Simbolos"]
            S_Observer["Publicar Eventos"]
        end
    end

    %% =========================================================================
    %% CONNECT ACTORS TO USE CASES
    %% =========================================================================
    User --> PC_Process
    User --> PL_Perception
    User --> MA_Perceive

    Developer --> PL_Synthesis
    Developer --> PL_UI
    Developer --> S_Command
    Developer --> S_Fallback
    Developer --> S_SymbolTable

    SystemAdmin --> S_Metrics
    SystemAdmin --> PL_Validate
    SystemAdmin --> S_Observer
    SystemAdmin --> MA_Supervise

    LLM_Service <--> PC_Process
    LLM_Service <--> PL_Perception
    LLM_Service <--> MA_Reason
    LLM_Service <--> MA_Execute
    LLM_Service <--> S_Cache

    FileSystem <--> PL_Synthesis
    FileSystem <--> PL_UI
    FileSystem <--> S_Command

    %% =========================================================================
    %% INCLUDE/EXTEND RELATIONSHIPS
    %% =========================================================================
    PC_Process --> PC_Preprocess
    PC_Process --> PC_Intent
    PC_Process --> PC_Plan
    PC_Process --> PC_Generate
    PC_Process --> PC_Verify
    PC_Process --> PC_Format

    PL_Perception --> PL_Preprocess
    PL_Preprocess --> PL_Lexer
    PL_Lexer --> PL_Parser
    PL_Parser --> PL_Semantic
    PL_Semantic --> PL_IR
    PL_IR --> PL_Planner
    PL_Planner --> PL_Synthesis
    PL_Planner --> PL_UI
    PL_Planner --> PL_Validate

    PC_Verify --> PC_Generate : <<extend>>\n(retry loop)

    PL_Validate --> S_Fallback : <<extend>>\non failure
    PC_Verify --> S_Fallback : <<extend>>\non failure

    S_Metrics -.-> PL_Perception : <<extend>>\nvia Observer
    S_Metrics -.-> PL_Lexer : <<extend>>\nvia Observer
    S_Metrics -.-> PL_Synthesis : <<extend>>\nvia Observer

    S_Observer -.-> PL_Perception : <<include>>
    S_Observer -.-> PL_Lexer : <<include>>
    S_Observer -.-> PL_Parser : <<include>>
    S_Observer -.-> PL_Synthesis : <<include>>
    S_Observer -.-> PL_Validate : <<include>>

    MA_Supervise --> MA_Perceive
    MA_Supervise --> MA_Reason
    MA_Supervise --> MA_Execute
    MA_Supervise --> MA_Validate
```
