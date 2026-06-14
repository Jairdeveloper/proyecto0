import logging

from langgraph.graph import StateGraph

from .nodes.ir_generator import IRGenerator
from .nodes.lexer import Lexer
from .nodes.parser import ParserGLR
from .nodes.planner import HybridPlanner
from .nodes.preprocessor import Preprocessor
from .nodes.semantic_analyzer import SemanticAnalyzer
from .state_models import StageContext, Stage

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    def __init__(self):
        self.graph = StateGraph(StageContext)
        self._build()

    def _build(self):
        self.graph.set_entry_point("input")
        self.graph.add_node("input", lambda x: x)
        self.graph.add_node(
            "preprocessor",
            lambda ctx: Preprocessor(ctx).execute(ctx.input_data),
        )
        self.graph.add_node(
            "lexer",
            lambda ctx: Lexer(ctx).execute(ctx.input_data),
        )
        self.graph.add_node(
            "parser",
            lambda ctx: ParserGLR(ctx).execute(ctx.input_data),
        )
        self.graph.add_node(
            "semantic_analyzer",
            lambda ctx: SemanticAnalyzer(ctx).execute(ctx.input_data),
        )
        self.graph.add_node(
            "ir_generator",
            lambda ctx: IRGenerator(ctx).execute(ctx.input_data),
        )
        self.graph.add_node(
            "planner",
            lambda ctx: HybridPlanner(ctx).execute(ctx.input_data),
        )
        self.graph.add_edge("input", "preprocessor")
        self.graph.add_edge("preprocessor", "lexer")
        self.graph.add_edge("lexer", "parser")
        self.graph.add_edge("parser", "semantic_analyzer")
        self.graph.add_edge("semantic_analyzer", "ir_generator")
        self.graph.add_edge("ir_generator", "planner")
        self.graph.add_node("output", lambda x: x)
        self.graph.add_edge("planner", "output")
        self.graph.set_finish_point("output")
        self.compiled = self.graph.compile()

    async def run(self, user_input: str) -> dict:
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data=user_input)
        logger.info("PipelineOrchestrator running with input: %.100s", user_input)
        return await self.compiled.ainvoke(ctx)
