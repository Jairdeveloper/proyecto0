---
id: "D01A"
area: "DEV"
type: "DIAGRAM"
module: "RECPL_CLASS_ASCII"
version: "1.0"
status: ACTIVE
tags: ["uml", "class-diagram", "ascii", "architecture"]
summary: "Diagrama de clases en ASCII del pipeline RECPL v2.0+ mostrando jerarquias, relaciones y patrones GoF"
---

# Diagrama de Clases (ASCII) — RECPL Compiler Bot v2.0+

```
================================================================================
 1. PIPELINE STAGE HIERARCHY — Template Method + Chain of Responsibility
================================================================================

 .-----------------------------------------.
 |           PipelineStage (ABC)           |
 |-----------------------------------------|
 | # name: str                             |
 | + subject: StageSubject         (class) |
 | # context: StageContext                 |
 |-----------------------------------------|
 | + receive_mission(input) None     [*]   |
 | + analyze() AnalysisResult              |
 | + reflect_and_plan(a) ActionPlan        |
 | + act(plan) StageOutput           [*]   |
 | + learn_and_improve(feedback) None      |
 | + execute(input) StageOutput            |-------.
 |       (Template Method)                 |       |
 '-----------------------------------------'       |
          ^           ^          ^                   |
          |           |          |                   |
          | inherits  |          |                   |
          |           |          |                   | publishes to
 .--------+----+------+--- . ---+--- . ---+--- . ----+----.
 |             |              |             |             |
 v             v              v             v             v
 .--------. .--------. .----------. .----------. .-------------.
 |Percept | |Prepro- | |  Lexer   | |ParserGLR | |SemanticAna- |
 | ionUnit| |cessor  | |          | |          | | lyzer       |
 |--------| |--------| |----------| |----------| |-------------|
 |name=   | |name=   | |name=     | |name=     | |name=       |
 |"intent"| |"prepro-| |"lexer"   | |"parser"  | |"semantic_  |
 |        | |cessor" | |          | |          | |analyzer"   |
 |--------| |--------| |----------| |----------| |-------------|
 | uses   | |valid.  | | uses     | | produces | | uses        |
 | NLP    | |Preproc | | SubDFA   | | ASTNode  | | SymbolTable |
 | Classes| |Contract| | Trie     | |          | |             |
 '--------' '--------' '----------' '----------' '-------------'

 .----------. .----------. .----------. .------------. .----------.
 |IRGenera- | |Reasoning | |ActionExe | |UIGenerator | |Validator |
 |tor       | |Engine    | |cutor     | |            | |Pipeline  |
 |----------| |----------| |----------| |------------| |----------|
 |name=     | |name=     | |name=     | |name=       | |name=     |
 |"ir_gener"| |"planner" | |"synthesis| |"ui_gener"  | |"validator|
 |          | |          | |          | |            | |          |
 |----------| |----------| |----------| |------------| |----------|
 |produces  | |LLM or    | |uses      | |uses        | |uses      |
 | IRNode   | |heuristic | |Generator | |UIComponent | |ErrorGuard|
 |          | |planner   | |Factory   | |Builder     | |          |
 '----------' '----------' '----------' '------------' '----------'

=== Supporting Models ===

 .------------------------------------.   .------------------------------------.
 |         StageContext               |   |          StageOutput                |
 |------------------------------------|   |------------------------------------|
 | + mission_id: str                  |   | + stage: Stage                     |
 | + stage: Stage                     |   | + output_data: dict                |
 | + input_data: Any                  |   | + metrics: dict                    |
 | + previous_output: Optional[Any]   |   | + feedback: Any                    |
 | + config_overrides: dict           |   | + success: bool                    |
 | + last_error: Optional[str]        |   | + error: Optional[str]             |
 '------------------------------------'   '------------------------------------'

 .------------------------------------.   .------------------------------------.
 |         AnalysisResult             |   |          ActionPlan                 |
 |------------------------------------|   |------------------------------------|
 | + observations: list               |   | + steps: list                      |
 | + detected_patterns: list          |   | + strategy: str                    |
 | + risks: list                      |   | + fallback_strategy: Optional[str] |
 | + complexity_score: float          |   | + estimated_cost: float            |
 '------------------------------------'   '------------------------------------'

 Stage (Enum): INTENT | PERCEPTION | PREPROCESSOR | LEXER | PARSER
               SEMANTIC_ANALYZER | IR_GENERATOR | PLANNER | REASONING
               SYNTHESIS | EXECUTION | UI_GENERATOR | VALIDATOR


================================================================================
 2. AGENT HIERARCHY
================================================================================

 .------------------------------------.
 |           Agent (ABC)              |
 |------------------------------------|
 | + name: str                        |
 | + role: str                        |
 |------------------------------------|
 | + process(task) TaskResult    [*]  |
 '------------------------------------'
          ^          ^          ^
          |          |          |          .-----------------------.
 .--------+----. .---+----. .--+-------.  |  SupervisorAgent      |
 | Perception  | |Reasoning| |Execution |  |-----------------------|
 | Agent       | |Agent    | |Agent     |  | + agents: dict[str,Ag]|
 |-------------| |---------| |----------|  | + llm: LLMBackend     |
 | name=       | | name=   | | name=    |  |-----------------------|
 | "percept_"  | |"reason_"| |"exec_"   |  | + process() TaskResult|
 | agent       | | agent   | | agent    |  | + _decompose() list   |
 '------------' '---------' '----------'  | + _replan() list      |
          ^                               '-----------------------'
          |                                     | delegates to
 .--------+----.                                v
 | Validator   |                        .----------------------.
 | Agent       |                        |   Agent (sub-agents) |
 |-------------|                        '----------------------'
 | name=       |
 | "valid_"    |                    SharedContext
 | agent       |                    .----------------------------.
 '------------'                    | - data: dict               |
                                   | - event_bus: EventBus      |
 Task (dataclass)                  |----------------------------|
 .----------------------------.    | + publish(topic, data)     |
 | + id: str                  |    | + subscribe(topic,cb) Any  |
 | + description: str         |    | + get_snapshot() dict      |
 | + agent: str               |    '----------------------------'
 | + params: dict             |               ^
 | + dependencies: list[str]  |               | extends
 | + status: str              |    .----------------------------.
 '----------------------------'    |    AsyncSharedContext       |
                                   |----------------------------|
 TaskResult (dataclass)            | + publish(topic, data) *   |
 .----------------------------.    '----------------------------'
 | + task_id: str             |
 | + success: bool            |    EventBus
 | + data: Any                |    .----------------------------.
 | + error: Optional[str]     |    | - subscribers: dict       |
 '----------------------------'    |----------------------------|
                                   | + subscribe(topic,cb)      |
                                   | + unsubscribe(topic,cb)    |
                                   | + publish(topic,data)      |
                                   | + publish_async(t,data)    |
                                   | + has_subscribers() bool   |
                                   | + subscriber_count() int   |
                                   | + clear()                  |
                                   '----------------------------'


================================================================================
 3. PROMPT HANDLER HIERARCHY — Chain of Responsibility
================================================================================

 .----------------------------------------------------------------.
 |                    PromptHandler (ABC)                          |
 |----------------------------------------------------------------|
 | + name: str                                                     |
 | + output_contract: type[BaseModel]                              |
 | + input_fields: list[str]                                       |
 | - next_handler: PromptHandler                                   |
 | - llm: LLMBackend                                               |
 | - debug_callback: Callable                                      |
 | - subject: StageSubject                                         |
 |----------------------------------------------------------------|
 | + set_next(handler) PromptHandler       (fluent)                |
 | + handle(request, ctx) PromptResponse   (Template Method)       |
 | + _build_prompt_kwargs(req, ctx) dict        [*]                |
 | + _notify_observers(out, dur, ok, err)                          |
 | + _get_ctx_data(ctx) dict                                       |
 '----------------------------------------------------------------'
          ^          ^          ^          ^          ^          ^
          |          |          |          |          |          |
 .--------+--. .---+---. .---+--. .---+--. .---+---. .---+------.
 |Preprocess | |Intent | |Plan | |Gener| |Verify| |Format      |
 |Handler    | |Handler| |Handl| |ate  | |Handl | |Handler     |
 |------------| |-------| |-----| |Han- | |------| |------------|
 |name=       | |name=  | |name=| |dler | |name= | |name=       |
 |"preprocess"| |"intent| |"plan| |-----| |"veri | |"format"    |
 |------------| |"      | |"    | |name=| |fy"   | |------------|
 |input_fields| |input_f| |input| |"gene| |input_| |input_fields|
 |= []        | |= [...| |= [...]| |rate"| |= [...]| |= [...]    |
 '------------' '------' '-----' '-----' '------' '------------'

 ChainOrchestrator                              ChainContext
 .----------------------------------------.     .----------------------------.
 | - llm: LLMBackend                      |     | - data: dict               |
 | - subject: StageSubject                |     | - history: list[ChainStep] |
 | - chain: PromptHandler                 |     |----------------------------|
 | - max_retries: int                     |     | + set_output(s,d,c)        |
 |----------------------------------------|     | + get_fields(s,f) dict     |
 | + run(raw_input) dict                  |     | + render_template(...) str |
 '----------------------------------------'     | + get_history(l) list      |
       |                                        | + get_all_outputs() dict   |
       | builds chain                           '----------------------------'
       v
 .----------------------------------------.     PromptRequest (Pydantic)
 | PromptHandler chain                    |     .----------------------------.
 | (fluent: set_next(a).set_next(b)...)   |     | + raw_input: str           |
 '----------------------------------------'     | + debug_callback: Callable |
                                                 '----------------------------'
 PromptResponse (Pydantic)
 .----------------------------.
 | + success: bool = True     |
 | + output: dict = {}        |
 | + error: Optional[str]     |
 '----------------------------'


================================================================================
 4. COMMAND HIERARCHY — Command Pattern
================================================================================

 .------------------------------------.
 |          Command (ABC)             |
 |------------------------------------|
 | + name: str                        |
 |------------------------------------|
 | + execute() CommandResult     [*]  |
 '------------------------------------'
          ^          ^          ^          ^
          |          |          |          |
 .--------+--. .---+---. .---+----. .----+-----------.
 |MacroCommand| |Prepro| |IntentC | | PlanCommand    |
 |------------| |cess  | |ommand  | | (name="plan")  |
 |name="macro"| |Comman| |(name=  | '----------------'
 |------------| |d     | |"intent"| .----------------.
 | commands:  | |(name=| |        | |GenerateCommand |
 | list[Comd] | |"pre" | '--------' | (name="gen")   |
 |------------| |      | .--------. '----------------'
 | + add(c)   | '------' |VerifyC | .----------------.
 | + execute()| .------. |ommand  | |FormatCommand   |
 '------------' |ToolC | |(name=  | | (name="format")|
       |        |ommand| |"verify"| '----------------'
       |        |------| '--------'
       |        |adapts| .--------------------.
       |        |ToolRe| |PipelineMacroCommand|
       |        |gistry| | (name="pipeline")  |
       |        '------' '--------------------'
       | composes
       v               CommandResult (dataclass)
 .--------.            .----------------------------.
 | Command |            | + success: bool            |
 | list    |            | + data: Any                |
 '--------'            | + error: Optional[str]     |
                       | + fallback_used: bool       |
 CommandHistory         | + duration: float           |
 .--------------------. | + command_name: str         |
 | - entries: list    | '----------------------------'
 |--------------------|
 | + record(cmd,res)  |     CommandEntry (dataclass)
 | + get_all() list   |     .----------------------------.
 | + get_failures()   |     | + command_name: str        |
 | + get_successes()  |     | + result: CommandResult    |
 | + replay_failures()|     | + timestamp: str           |
 | + get_success_rate |     | + params: dict             |
 '--------------------'     '----------------------------'


================================================================================
 5. OBSERVER HIERARCHY — Observer Pattern
================================================================================

 StageSubject                           StageEvent (dataclass)
 .----------------------------.         .----------------------------.
 | - observers: list[Obs]    |         | + stage: str               |
 |----------------------------|         | + duration: float           |
 | + attach(observer)        | notify  | + success: bool             |
 | + detach(observer)        |-------->| + output: dict              |
 | + notify(event)           |         | + error: Optional[str]      |
 | + observer_count: int     |         | + metadata: dict            |
 '----------------------------'         | + timestamp: str            |
       |                               '----------------------------'
       | holds list of
       v
 .------------------------------------.
 |         StageObserver (interface)  |
 |------------------------------------|
 | + on_event(event) None        [*]  |
 '------------------------------------'
          ^          ^          ^          ^           ^
          |          |          |          |           |
 .--------+--. .---+---. .---+----. .----+------. .---+------.
 |MetricsObs | |DebugOb| |PromptOp| |DashboardObs | |PlanObser|
 |erver      | |server | |timizer | |erver        | |ver      |
 |-----------| |-------| |Observer| |-------------| |---------|
 |feedback:  | |call-  | |--------| |recent_events| | logs    |
 |GlobalFeed | |back   | |store:  | |: deque[1000]| |task     |
 |backLoop   | |       | |Metrics | |ws_clients[] | | state   |
 |-----------| |-------| |Store   | |-------------| |changes  |
 |on_event() | |on_eve | |--------| |on_event()   | '---------'
 | records to| |nt()   | |on_even | |broadcast()  |
 | GlobalFee | |calls  | |t() rec | |get_recent() |
 |dbackLoop  | |call-  | |ords in | '------------'
 '-----------' '------' '--------'


================================================================================
 6. GENERATOR HIERARCHY — Strategy + Factory
================================================================================

 .------------------------------------.
 |        BaseGenerator (ABC)         |
 |------------------------------------|
 | + generate(ir_node, output_dir)    |
 |       -> list[Path]           [*]  |
 '------------------------------------'
          ^          ^          ^          ^          ^          ^
          |          |          |          |          |          |
 .--------+--. .---+---. .---+--. .---+--. .---+---. .---+------.
 |ReactG| |Next| |Nest| |Pri| |Dock| |Tail| .--------.
 |enerat| |JS  | |JS  | |sma| |erGe| |wind| |UICompo |
 |or    | |Gen | |Gen | |Gen| |ner | |Gen | |nentBui |
 |      | |erat| |erat| |era| |ato | |erat| |lder    |
 |      | |or  | |or  | |tor| |r   | |or  | |--------|
 '------' '----' '----' '---' '----' '----' |Builder |
                                             |pattern |
 GeneratorFactory                             |--------|
 .-------------------------.                 |build_  |
 | + get_generator(target) |                 |struct()|
 |       -> BaseGenerator  |                 |apply_  |
 '-------------------------'                 |styles()|
                                             |add_Beh |
 ActionExecutor --> GeneratorFactory         |avior() |
                                             '--------'


================================================================================
 7. IR NODE HIERARCHY — Composite Pattern
================================================================================

 .------------------------------------.
 |          IRNode (ABC)              |
 |------------------------------------|
 | + name: str                        |
 | + children: list[IRNode]           |
 |------------------------------------|
 | + validate() list                  |
 | + to_code(target) str              |
 | + add_child(node) None             |
 '------------------------------------'
          ^          ^          ^          ^          ^          ^          ^
          |          |          |          |          |          |          |
 .--------+--. .---+---. .---+--. .---+--. .---+---. .---+----. .---+------.
 |IRProje| |IRPage| |IRComp| |IREnt| |IRAPI| |IRConf| |IRInfra |
 |ct     | |      | |onent | |ity  | |     | |ig    | |        |
 |-------| |------| |------| |-----| |-----| |------| |--------|
 |name=  | |compo | |valida| |attr | |route| |setti | |type   |
 |proj   | |nents | |te    | |ibute| |     | |ngs   | |(db/svc)|
 '-------' '------' '------' '-----' '-----' '------' '--------'
      ^
      | children
      |
 .------------------------------------.
 |      IRNode (composite tree)       |
 '------------------------------------'

 IRBuilder                                    IRSerializer (interface)
 .--------------------------------.          .---------------------------.
 | + build(semantic_dict) IRProj |          | + serialize(node,path) *  |
 | + validate(project) list      |          | + mime_type() str *       |
 | + get_dependency_order() list |          '---------------------------'
 '--------------------------------'                    ^
       |                                                |
       v                                                |
 .--------------------------------.          .----------+---------.
 |        DependencyGraph         |          |          |          |
 |--------------------------------|          v          v          v
 | + topological_sort() list      |    .---------. .--------. .-------.
 | + detect_cycle() bool          |    |JSONSeri | |YAMLSer | |DOTSer |
 '--------------------------------'    |alizer   | |ializer | |ializer|
                                        '---------' '--------' '-------'


================================================================================
 8. AST NODE HIERARCHY — Parser Output
================================================================================

 .------------------------------------.
 |         ASTNode (ABC)              |
 |------------------------------------|
 | + validate() list                  |
 | + evaluate(ctx) Any                |
 | + to_ir() IRNode                   |
 '------------------------------------'
          ^          ^          ^          ^          ^
          |          |          |          |          |
 .--------+--. .---+---. .---+--. .---+--. .---+------.
 |ProjectNode| |PageNo  | |Compo| |Entity| |InfraNod |
 |           | |de      | |nent | |Node  | |e        |
 |-----------| |--------| |Node | |------| |---------|
 | pages: [] | |compo-  | |-----| |attri | |resource |
 |           | |nents[] | |vali-| |butes | |s: []    |
 '-----------' '--------' |date | '------' '--------'
                          '-----'


================================================================================
 9. NLP PIPELINE CLASSES
================================================================================

 .------------------.   .------------------.   .------------------.
 | IntentClassifier |   |  NERExtractor    |   |   SlotFiller     |
 |------------------|   |------------------|   |------------------|
 | + classify(text) |   | + extract(text,  |   | + fill(text,     |
 |   -> IntentRes   |   |   intent) Entity |   |   intent, ent)   |
 '------------------'   '------------------'   |   -> Slots       |
                                               '------------------'
 .------------------.   .------------------.
 |AmbiguityDetector |   |  EnrichedInput   |
 |------------------|   |------------------|
 | + detect(text,   |   | + raw: str       |
 |   intent, slots) |   | + intent: Intent |
 |   -> AmbiguityRes|   | + entities: Ents |
 '------------------'   | + slots: Slots   |
                        | + ambiguity: Amb |
                        | + context: CtxSt |
                        '------------------'


================================================================================
 10. SUPPORTING CLASSES
================================================================================

 SymbolTable (Memento)               LLMBackend (interface)
 .-------------------------------.   .-------------------------------.
 | - scopes: list                |   | + generate(prompt) LLMResult* |
 |-------------------------------|   | + generate_structured(p,s)    |
 | + enter_scope()               |   |       -> LLMResult*           |
 | + exit_scope()                |   '-------------------------------'
 | + define(name, info)          |              ^            ^
 | + resolve(name) Any           |              |            |
 | + snapshot() dict             |              |            |
 | + save_memento() Memento      |    .---------+--.  .------+------.
 | + restore(memento)            |    |FailoverLLM  |  |OpenAIBacken|
 '-------------------------------'    |Backend      |  |d           |
                                      |-------------|  |------------|
 SubDFA                               | backends[]  |  | api_key    |
 .-------------------------------.   | (primary +  |  |------------|
 | + build(words) DFA            |   |  failover)  |  | + generate |
 | + scan(text) list[Token]      |   '-------------'  | + generate_|
 '-------------------------------'                     | structured|
                                                        '----------'
 Trie
 .-------------------------------.   ToolRegistry
 | + insert(phrase, tok_type)    |   .-------------------------------.
 | + lookup(text) list[Token]    |   | - tools: dict[str, Tool]      |
 '-------------------------------'   |-------------------------------|
                                     | + register(tool)              |
 Tool (interface)                    | + execute(name, params) Tool  |
 .-------------------------------.   | + list_tools() list           |
 | + name: str                   |   '-------------------------------'
 | + execute(params) ToolResult* |
 '-------------------------------'             ^
          ^          ^          ^          ^   | registers
          |          |          |          |   |
 .--------+--. .---+---. .---+--. .---+---+-+  |
 |ReadFileTo | |WriteFi | |RunCom | |SearchCod|--'
 |ol         | |leTool  | |mandTo | |eTool    |
 '-----------' '--------' |ol      | '---------'
 .-----------. .--------. '--------' .-----------.
 |GenerateCod| |AskUser | .--------. |ExplainTool|
 |eTool      | |Tool    | |ErrorGua| |           |
 '-----------' '--------' |rd      | '-----------'
                          |--------|
 MetricsStore             | + shoul|
 .----------------------. |d_contin|   WorldModel
 | + record(s,m)        | |ue(ctx)$|   .---------------.
 | + get_recent(s,l)    | '--------'   | + snapshot()  |
 | + summary() dict     |               '---------------'
 | + record_prompt(n,m) |
 | + record_token(t,w)  |   GlobalFeedbackLoop
 '----------------------'   .-------------------------------.
                            | - store: MetricsStore          |
 FeedbackLoop (legacy)      | - legacy: FeedbackLoop         |
 .----------------------.   | - adjustments: dict            |
 | + record(s,m)        |   |-------------------------------|
 | + get_recent(s,l)    |   | + record_stage(s, m)          |
 '----------------------'   | + record_prompt(n, m)         |
                            | + get_prompt_success_rate()   |
 PromptOptimizer            | + summary() dict              |
 .----------------------.   '-------------------------------'
 | + optimize(name) dict|
 '----------------------'


================================================================================
 CROSS-CUTTING RELATIONSHIPS (dependency / association summary)
================================================================================

 ActorOrchestrator --> PipelineStage         (via NODE_MAP dict)
 ActorOrchestrator --> StateGraph            (compiles LangGraph)
 ActorOrchestrator --> ErrorGuard            (conditional edges)

 PipelineStage ----> StageContext            (composition)
 PipelineStage ----> StageSubject            (publishes StageEvent)
 PipelineStage ----> StageOutput             (produces)
 PipelineStage ----> AnalysisResult          (returns from analyze)
 PipelineStage ----> ActionPlan              (returns from reflect_and_plan)

 StageSubject  ----> StageObserver           (holds list)
 StageSubject  ----> StageEvent              (notifies with)

 StageObserver ----> GlobalFeedbackLoop      (MetricsObserver)
 StageObserver ----> Callable                (DebugObserver)
 StageObserver ----> deque                   (DashboardObserver)

 PromptHandler ----> LLMBackend              (delegates LLM call)
 PromptHandler ----> PromptRegistry          (template lookup)
 PromptHandler ----> ChainContext            (publishes output)
 PromptHandler ----> StageSubject            (publishes StageEvent)

 ChainOrchestrator -> PromptHandler          (builds chain)
 ChainOrchestrator -> ChainContext           (creates per run)
 ChainOrchestrator -> StageSubject           (with DebugObserver)

 SupervisorAgent ---> Agent                  (holds sub-agents)
 SupervisorAgent ---> SharedContext          (pub/sub bus)
 SupervisorAgent ---> ChainOrchestrator      (optional LLM mode)

 Agent ------------> SharedContext           (composition)
 Agent ------------> Task                    (processes)
 Agent ------------> TaskResult              (returns)

 SharedContext ----> EventBus                (delegates pub/sub)

 Command ----------> CommandResult           (returns from execute)
 MacroCommand -----> Command                 (composes list)
 CommandHistory ---> CommandResult           (records)

 GeneratorFactory -> BaseGenerator           (creates strategy)
 ActionExecutor ---> GeneratorFactory        (uses)

 IRBuilder --------> IRNode                  (builds composite tree)
 IRBuilder --------> DependencyGraph         (topological sort)
 IRGenerator ------> IRBuilder               (uses)

 SemanticAnalyzer -> SymbolTable             (manages scopes)
 Lexer ------------> SubDFA + Trie           (tokenizer components)

 PerceptionUnit ---> IntentClassifier        (uses)
 PerceptionUnit ---> NERExtractor             (uses)
 PerceptionUnit ---> SlotFiller              (uses)
 PerceptionUnit ---> AmbiguityDetector       (uses)

 GlobalFeedbackLoop -> MetricsStore          (delegates)
 GlobalFeedbackLoop -> FeedbackLoop          (legacy fallback)
