import requests

response = requests.post(
    "https://markdowntoimage.com/api/v1/images/generate",
    headers={
        "Authorization": "Bearer mti_3baa4d1a78aca15c6b8b8f96891904426e3ce217651d56f9",
        "Content-Type": "application/json"
    },
    json={
        "markdown": """%%{init:{
"theme":"base",
"themeVariables":{
    "primaryColor":"#1f2937",
    "primaryBorderColor":"#60a5fa",
    "primaryTextColor":"#ffffff",
    "lineColor":"#94a3b8"
}
}}%%

```mermaid
classDiagram

%% =========================================================================
%% 1. PIPELINE STAGE HIERARCHY (Template Method + Chain of Responsibility)
%% =========================================================================

class PipelineStage {
    <<abstract>>
    +name: str
    +subject: StageSubject$
    #context: StageContext
    +receive_mission(input_data) None*
    +analyze() AnalysisResult
    +reflect_and_plan(analysis) ActionPlan
    +act(plan) StageOutput*
    +learn_and_improve(feedback) None
    +execute(input_data) StageOutput
}

PipelineStage <|-- PerceptionUnit : intent
PipelineStage <|-- Preprocessor : preprocessor
PipelineStage <|-- Lexer : lexer
PipelineStage <|-- ParserGLR : parser
PipelineStage <|-- SemanticAnalyzer : semantic_analyzer
PipelineStage <|-- IRGenerator : ir_generator
PipelineStage <|-- ReasoningEngine : planner
PipelineStage <|-- ActionExecutor : synthesis
PipelineStage <|-- UIGenerator : ui_generator
PipelineStage <|-- ValidatorPipeline : validator

PerceptionUnit --> NLP
Preprocessor --> PreprocessorContract
Lexer --> SubDFA
Lexer --> Trie
ParserGLR --> ASTNode
SemanticAnalyzer --> SymbolTable
IRGenerator --> IRNode
ActionExecutor --> GeneratorFactory
UIGenerator --> UIComponentBuilder
ValidatorPipeline --> ErrorGuard

class StageContext {
    +mission_id: str
    +stage: Stage
    +input_data: Any
    +previous_output: Optional[Any]
    +config_overrides: dict
    +last_error: Optional[str]
}

class Stage {
    <<enum>>
    INTENT
    PREPROCESSOR
    LEXER
    PARSER
    SEMANTIC_ANALYZER
    IR_GENERATOR
    PLANNER
    SYNTHESIS
    UI_GENERATOR
    VALIDATOR
}

class StageOutput {
    +stage: Stage
    +output_data: dict
    +metrics: dict
    +feedback: Any
    +success: bool
    +error: Optional[str]
}

class AnalysisResult {
    +observations: list
    +detected_patterns: list
    +risks: list
    +complexity_score: float
}

class ActionPlan {
    +steps: list
    +strategy: str
    +fallback_strategy: Optional[str]
    +estimated_cost: float
}

%% =========================================================================
%% 2. AGENT HIERARCHY
%% =========================================================================

class Agent {
    <<abstract>>
    +name: str
    +role: str
    +process(task) TaskResult*
}

Agent <|-- PerceptionAgent : perception_agent
Agent <|-- ReasoningAgent : reasoning_agent
Agent <|-- ExecutionAgent : execution_agent
Agent <|-- ValidatorAgent : validator_agent
Agent <|-- SupervisorAgent : supervisor

SupervisorAgent o--> Agent : delegates to

class Task {
    +id: str
    +description: str
    +agent: str
    +params: dict
    +dependencies: list[str]
    +status: str
}

class TaskResult {
    +task_id: str
    +success: bool
    +data: Any
    +error: Optional[str]
}

class SharedContext {
    -data: dict
    -event_bus: EventBus
    +publish(topic, data) None
    +subscribe(topic, callback) Any
    +get_snapshot() dict
}

class AsyncSharedContext {
    -channels: dict
    +publish(topic, data) None*
}

SharedContext <|-- AsyncSharedContext
SharedContext --> EventBus

class EventBus {
    -subscribers: dict
    +subscribe(topic, callback) None
    +unsubscribe(topic, callback) None
    +publish(topic, data) None
    +publish_async(topic, data) None
    +has_subscribers(topic) bool
    +subscriber_count(topic) int
    +clear() None
}

%% =========================================================================
%% 3. PROMPT HANDLER HIERARCHY (Chain of Responsibility)
%% =========================================================================

class PromptHandler {
    <<abstract>>
    +name: str
    +output_contract: type[BaseModel]
    +input_fields: list[str]
    -next_handler: PromptHandler
    -llm: LLMBackend
    -debug_callback: Callable
    -subject: StageSubject
    +set_next(handler) PromptHandler
    +handle(request, ctx) PromptResponse
    +_build_prompt_kwargs(request, ctx_data) dict*
    +_notify_observers(output, duration, success, error) None
    +_get_ctx_data(ctx) dict
}

PromptHandler <|-- PreprocessHandler : preprocess
PromptHandler <|-- IntentHandler : intent
PromptHandler <|-- PlanHandler : plan
PromptHandler <|-- GenerateHandler : generate
PromptHandler <|-- VerifyHandler : verify
PromptHandler <|-- FormatHandler : format

class ChainOrchestrator {
    -llm: LLMBackend
    -subject: StageSubject
    -chain: PromptHandler
    -max_retries: int
    +run(raw_input) dict
}

ChainOrchestrator --> PromptHandler : builds chain
ChainOrchestrator --> ChainContext

class ChainContext {
    -data: dict
    -history: list[ChainStep]
    +set_output(stage, data, contract) None
    +get_fields(stage, fields) dict
    +render_template(template, stage, fields) str
    +get_history(limit) list
    +get_all_outputs() dict
}

class PromptRequest {
    +raw_input: str
    +debug_callback: Optional[Callable]
}

class PromptResponse {
    +success: bool
    +output: dict
    +error: Optional[str]
}

%% =========================================================================
%% 4. COMMAND HIERARCHY (Command Pattern)
%% =========================================================================

class Command {
    <<abstract>>
    +name: str
    +execute() CommandResult*
}

Command <|-- MacroCommand : macro
Command <|-- PreprocessCommand : preprocess
Command <|-- IntentCommand : intent
Command <|-- PlanCommand : plan
Command <|-- GenerateCommand : generate
Command <|-- VerifyCommand : verify
Command <|-- FormatCommand : format
Command <|-- ToolCommand : tool:{name}
Command <|-- PipelineMacroCommand : pipeline

MacroCommand o--> Command : commands

class CommandResult {
    +success: bool
    +data: Any
    +error: Optional[str]
    +fallback_used: bool
    +duration: float
    +command_name: str
}

class CommandHistory {
    -entries: list[CommandEntry]
    +record(cmd, result) None
    +get_all() list
    +get_failures() list
    +get_successes() list
    +get_by_name(name) list
    +replay_failures(factory) None
    +get_success_rate() float
}

CommandHistory --> CommandEntry

class ToolCommand {
    +name: str
    +execute() CommandResult
}

ToolCommand --> ToolRegistry

%% =========================================================================
%% 5. OBSERVER HIERARCHY (Observer Pattern)
%% =========================================================================

class StageSubject {
    -observers: list[StageObserver]
    +attach(observer) None
    +detach(observer) None
    +notify(event) None
    +observer_count: int
}

class StageObserver {
    <<interface>>
    +on_event(event)* None
}

class StageEvent {
    +stage: str
    +duration: float
    +success: bool
    +output: dict
    +error: Optional[str]
    +metadata: dict
    +timestamp: str
}

StageSubject o--> StageObserver

StageObserver <|.. MetricsObserver
StageObserver <|.. DebugObserver
StageObserver <|.. PromptOptimizerObserver
StageObserver <|.. DashboardObserver
StageObserver <|.. PlanObserver

class MetricsObserver {
    -feedback: GlobalFeedbackLoop
    +on_event(event) None
}

class DebugObserver {
    -callback: Callable
    +on_event(event) None
}

class DashboardObserver {
    -recent_events: deque
    -ws_clients: list
    +on_event(event) None
    +get_recent(limit) list
    +event_count: int
}

%% =========================================================================
%% 6. GENERATOR HIERARCHY (Strategy + Factory)
%% =========================================================================

class BaseGenerator {
    <<abstract>>
    +generate(ir_node, output_dir) list[Path]*
}

BaseGenerator <|-- ReactGenerator : react
BaseGenerator <|-- NextJSGenerator : nextjs
BaseGenerator <|-- NestJSGenerator : nestjs
BaseGenerator <|-- PrismaGenerator : prisma
BaseGenerator <|-- DockerGenerator : docker
BaseGenerator <|-- TailwindGenerator : tailwind

class GeneratorFactory {
    +get_generator(target)$ BaseGenerator
}

class UIComponentBuilder {
    +build_structure(spec)
    +apply_styles(theme)
    +add_behavior(events)
    +add_accessibility(aria)
    +add_animations(anim)
    +build() ComponentSpec
}

%% =========================================================================
%% 7. IR NODE HIERARCHY (Composite)
%% =========================================================================

class IRNode {
    <<abstract>>
    +name: str
    +children: list[IRNode]
    +validate() list
    +to_code(target) str
    +add_child(node) None
}

IRNode <|-- IRProject : project
IRNode <|-- IRPage : page
IRNode <|-- IRComponent : component
IRNode <|-- IREntity : entity
IRNode <|-- IRAPI : api
IRNode <|-- IRConfig : config
IRNode <|-- IRInfra : infra

IRNode o--> IRNode : children

class IRBuilder {
    +build(semantic_dict) IRProject
    +validate(project) list
    +get_dependency_order() list
}

IRBuilder --> DependencyGraph

class IRSerializer {
    <<interface>>
    +serialize(node, path) None*
    +mime_type() str*
}

IRSerializer <|.. JSONSerializer
IRSerializer <|.. YAMLSerializer
IRSerializer <|.. DOTSerializer

%% =========================================================================
%% 8. AST NODE HIERARCHY (Parser output)
%% =========================================================================

class ASTNode {
    <<abstract>>
    +validate() list
    +evaluate(ctx) Any
    +to_ir() IRNode
}

ASTNode <|-- ProjectNode
ASTNode <|-- PageNode
ASTNode <|-- ComponentNode
ASTNode <|-- EntityNode
ASTNode <|-- InfraNode

%% =========================================================================
%% 9. NLP PIPELINE
%% =========================================================================

class IntentClassifier {
    +classify(text) IntentResult
}

class NERExtractor {
    +extract(text, intent) Entities
}

class SlotFiller {
    +fill(text, intent, entities) Slots
}

class AmbiguityDetector {
    +detect(text, intent, slots) AmbiguityResult
}

class EnrichedInput {
    +raw: str
    +intent: IntentResult
    +entities: Entities
    +slots: Slots
    +ambiguity: AmbiguityResult
    +context: ContextState
}

%% =========================================================================
%% 10. SUPPORTING CLASSES
%% =========================================================================

class SymbolTable {
    -scopes: list
    +enter_scope() None
    +exit_scope() None
    +define(name, info) None
    +resolve(name) Any
    +snapshot() dict
    +save_memento() Memento
    +restore(memento) None
}

class SubDFA {
    +build(words) DFA
    +scan(text) list[Token]
}

class Trie {
    +insert(phrase, token_type) None
    +lookup(text) list[Token]
}

class LLMBackend {
    <<interface>>
    +generate(prompt) LLMResult*
    +generate_structured(prompt, schema) LLMResult*
}

LLMBackend <|.. FailoverLLMBackend
LLMBackend <|.. OpenAIBackend

class ToolRegistry {
    -tools: dict[str, Tool]
    +register(tool) None
    +execute(name, params) ToolResult
    +list_tools() list
}

class Tool {
    <<interface>>
    +name: str
    +execute(params) ToolResult*
}

Tool <|.. ReadFileTool
Tool <|.. WriteFileTool
Tool <|.. RunCommandTool
Tool <|.. SearchCodeTool
Tool <|.. GenerateCodeTool
Tool <|.. AskUserTool
Tool <|.. ExplainTool

class ErrorGuard {
    +should_continue(ctx)$ str
}

class GlobalFeedbackLoop {
    -store: MetricsStore
    -legacy: FeedbackLoop
    +record_stage(stage, metrics) None
    +record_prompt(name, metrics) None
    +get_prompt_success_rate(name, n) float
    +summary() dict
}

class MetricsStore {
    +record(stage, metrics) None
    +get_recent(stage, limit) list
    +summary() dict
    +record_prompt(name, metrics) None
    +record_token(token, weight) None
}

class WorldModel {
    +snapshot() dict
}

%% =========================================================================
%% RELATIONSHIPS
%% =========================================================================

PipelineStage --> StageContext
PipelineStage --> StageSubject : publishes to
PipelineStage --> StageOutput

Agent --> SharedContext
Agent --> Task
Agent --> TaskResult

StageSubject --> StageEvent
StageSubject --> StageObserver

MacroCommand --> CommandResult
CommandHistory --> CommandResult

GeneratorFactory --> BaseGenerator
ActionExecutor --> GeneratorFactory

PromptHandler --> LLMBackend
PromptHandler --> PromptRegistry
PromptHandler --> ChainContext

SemanticAnalyzer --> SymbolTable
Lexer --> SubDFA
Lexer --> Trie

IRBuilder --> IRNode
IRGenerator --> IRBuilder

PerceptionUnit --> IntentClassifier
PerceptionUnit --> NERExtractor
PerceptionUnit --> SlotFiller
PerceptionUnit --> AmbiguityDetector

AgentOrchestrator --> PipelineStage : NODE_MAP
AgentOrchestrator --> StateGraph
AgentOrchestrator --> ErrorGuard

SupervisorAgent --> ChainOrchestrator
SupervisorAgent --> Agent : sub-agents

GlobalFeedbackLoop --> MetricsStore
GlobalFeedbackLoop --> FeedbackLoop 
""",
"format": "png",
"width": 800
}
)

data = response.json()
print(data["data"]["imageUrl"])