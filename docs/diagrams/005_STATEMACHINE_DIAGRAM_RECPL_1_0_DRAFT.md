---
id: "D05"
area: "DEV"
type: "DIAGRAM"
module: "RECPL_STATEMACHINE"
version: "1.0"
status: "DRAFT"
tags: ["uml", "state-machine-diagram", "lifecycle"]
summary: "Diagrama de maquina de estados mostrando el ciclo de vida de PipelineStage, Task, y los modos de operacion del compilador"
---

# Diagrama de Máquina de Estados — RECPL Compiler Bot v2.0+

## 1. Ciclo de Vida de PipelineStage

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> ReceivingMission : execute(input_data)
    ReceivingMission --> Analyzing : receive_mission()
    Analyzing --> Planning : analyze()
    Planning --> Acting : reflect_and_plan()
    Acting --> Validating : act()
    Validating --> Publishing : contract.model_validate()
    Publishing --> Notifying : create StageEvent
    Notifying --> Learning : subject.notify(event)
    Learning --> Complete : learn_and_improve()

    Acting --> Failure : exception raised
    Validating --> Failure : contract validation error

    Failure --> ErrorNotify : create StageEvent (success=false)
    ErrorNotify --> Rethrow : subject.notify(failure_event)
    Rethrow --> [*] : re-raise exception

    Complete --> [*] : return StageOutput

    state Idle {
        [*] --> Ready
    }

    note right of Acting
        Etapa especifica del stage:
        - Lexer: DFA scan
        - Parser: GLR parse
        - Synthesis: file I/O
    end note

    note right of Failure
        ErrorGuard captura el error
        en StageContext.last_error
        y decide abort vs continue
    end note
```

## 2. Ciclo de Vida de Task (Multi-Agent System)

```mermaid
stateDiagram-v2
    [*] --> Pending

    Pending --> Ready : dependencies completed
    Ready --> Running : agent.process(task)

    Running --> Done : success=true
    Running --> Failed : success=false

    Failed --> Ready : attempt < max_retries\n(replan)
    Failed --> Blocked : attempt >= max_retries\nor no replan

    Blocked --> [*]
    Done --> [*]

    state Pending {
        [*] --> Waiting
        Waiting --> Available : check_dependencies()
    }

    note right of Failed
        SupervisorAgent._replan_failed()
        crea un nuevo Task con
        sufijo _retry
    end note
```

## 3. Estados del Prompt Chain (ChainOrchestrator)

```mermaid
stateDiagram-v2
    [*] --> MainChain

    MainChain --> Preprocess : run()
    Preprocess --> Intent : handle() success
    Intent --> Plan : handle() success
    Plan --> Generate : handle() success
    Generate --> Verify : handle() success

    Verify --> RetryDecision : handle() success
    RetryDecision --> Generate : should_retry=true\n& attempt < max_retries
    RetryDecision --> Format : should_retry=false\nor attempt >= max_retries
    Format --> Complete : handle() success

    MainChain --> Failure : any handler raises

    Failure --> [*]
    Complete --> [*]

    note right of RetryDecision
        ChainOrchestrator.run()
        cicla Generate→Verify
        hasta N=max_retries
    end note
```

## 4. Estados del StageSubject/Observer

```mermaid
stateDiagram-v2
    [*] --> Active

    Active --> Notifying : notify(event)
    Notifying --> Iterating : for each observer
    Iterating --> CallingObserver : observer.on_event(event)

    CallingObserver --> Iterating : next observer
    CallingObserver --> ObserverError : exception in on_event

    ObserverError --> Iterating : continue with\nnext observer

    Iterating --> Active : all observers notified

    Active --> Attaching : attach(observer)
    Attaching --> Active : observer added to list

    Active --> Detaching : detach(observer)
    Detaching --> Active : observer removed from list

    note right of CallingObserver
        Observers registrados:
        - MetricsObserver (siempre)
        - DebugObserver (si debug_callback)
        - PromptOptimizerObserver
        - DashboardObserver
    end note
```

## 5. Estados del Modo de Operacion (CLI)

```mermaid
stateDiagram-v2
    [*] --> ParseArgs

    ParseArgs --> ClassicPipeline : no --chain flag
    ParseArgs --> PromptChain : --chain flag
    ParseArgs --> Error : invalid args

    ClassicPipeline --> BuildingGraph : AgentOrchestrator
    BuildingGraph --> ExecutingStages : StateGraph compiled
    ExecutingStages --> Streaming : stream_callback set
    ExecutingStages --> Collecting : no callback
    Streaming --> Collecting : all stages done
    Collecting --> OutputResult : dict {output, success}

    PromptChain --> BuildingChain : ChainOrchestrator
    BuildingChain --> RunningHandlers : handler chain ready
    RunningHandlers --> OutputResult : dict {summary, files}

    OutputResult --> [*]
    Error --> [*]
    OutputResult --> Monitor : --monitor flag
    Monitor --> [*]
```
