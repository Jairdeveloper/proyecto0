---
id: "D04"
area: dev
type: diagram
module: recpl_activity
version: "1.0"
status: ACTIVE
tags: ["uml", "activity-diagram", "pipeline-flow"]
summary: "Diagrama de actividad del pipeline RECPL completo mostrando el flujo de control, decisiones y caminos alternativos"
---

# Diagrama de Actividad — Pipeline RECPL v2.0+

```mermaid
stateDiagram-v2
    state "Input Usuario" : raw_input
    state "Interpretar Intencion" : PerceptionUnit\n(LLM o reglas)
    state "Preprocesar Texto" : Preprocessor\n(normalizar + filtrar)
    state "Tokenizar con DFA" : Lexer\n(sub-DFAs + Trie)
    state "Construir AST (GLR)" : ParserGLR\n(gramatica multiple)
    state "Analisis Semantico" : SemanticAnalyzer\n(symbol table + types)
    state "Generar IR" : IRGenerator\n(Composite tree)
    state "Planificar Ejecucion" : ReasoningEngine\n(task graph + layers)
    state "Sintetizar Codigo" : ActionExecutor\n(GeneratorFactory)
    state "Generar UI" : UIGenerator\n(UIComponentBuilder)
    state "Validar Salida" : ValidatorPipeline\n(Chain of Responsibility)
    state "Output Final" : generated_files,\nerrors, warnings

    state fork_pipeline <<fork>>
    state join_validator <<join>>
    state decision_error <<choice>>
    state decision_retry <<choice>>

    [*] --> Input
    Input --> InterpretarIntencion

    InterpretarIntencion --> Preprocesar
    Preprocesar --> Tokenizar
    Tokenizar --> ConstruirAST
    ConstruirAST --> AnalisisSemantico
    AnalisisSemantico --> GenerarIR
    GenerarIR --> Planificar
    Planificar --> fork_pipeline

    fork_pipeline --> Sintetizar
    fork_pipeline --> GenerarUI

    Sintetizar --> join_validator
    GenerarUI --> join_validator

    join_validator --> Validar

    Validar --> decision_error
    decision_error --> decision_retry : success=false
    decision_retry --> fork_pipeline : should_retry=true\n& attempt < max
    decision_retry --> Output : should_retry=false\nor attempt >= max
    decision_error --> Output : success=true

    Output --> [*]

    %% --- Prompt Chain Alternative ---
    state "Prompt Chain Alternativo" {
        state "Preprocess" : PreprocessHandler
        state "Intent" : IntentHandler
        state "Plan" : PlanHandler
        state "Generate" : GenerateHandler
        state "Verify" : VerifyHandler
        state "Format" : FormatHandler

        state chain_decision <<choice>>

        Preprocess --> Intent
        Intent --> Plan
        Plan --> Generate
        Generate --> Verify
        Verify --> chain_decision
        chain_decision --> Generate : should_retry=true\n& attempt < max
        chain_decision --> Format : should_retry=false\nor attempt >= max
        Format --> [*]
    }

    %% --- Multi-Agent Alternative ---
    state "Flujo Multi-Agente" {
        state "PerceptionAgent" : analizar entrada\n(LLM o NLP)
        state "ReasoningAgent" : descomponer objetivo\n(LLM o GoalTree)
        state "ExecutionAgent" : ejecutar acciones\n(LLM o ToolRegistry)
        state "ValidatorAgent" : verificar resultados\n(LLM o WorldModel)

        PerceptionAgent --> ReasoningAgent
        ReasoningAgent --> ExecutionAgent
        ExecutionAgent --> ValidatorAgent
        ValidatorAgent --> [*]
    }

    note right of decision_error
        ErrorGuard.should_continue()
        revisa last_error del
        StageContext
    end note

    note right of decision_retry
        Solo en ValidatorPipeline
        cuando results.any()
        contiene should_retry=true
    end note
```
