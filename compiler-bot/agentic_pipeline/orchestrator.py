import logging

from langgraph.graph import StateGraph

from .nodes.preprocessor import Preprocessor
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
        self.graph.add_edge("input", "preprocessor")
        self.graph.add_node("output", lambda x: x)
        self.graph.add_edge("preprocessor", "output")
        self.graph.set_finish_point("output")
        self.compiled = self.graph.compile()

    async def run(self, user_input: str) -> dict:
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data=user_input)
        logger.info("PipelineOrchestrator running with input: %.100s", user_input)
        return await self.compiled.ainvoke(ctx)
