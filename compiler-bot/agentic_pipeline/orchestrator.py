from langgraph.graph import StateGraph

from .state_models import StageContext, Stage


class PipelineOrchestrator:
    def __init__(self):
        self.graph = StateGraph(StageContext)
        self._build()

    def _build(self):
        self.graph.set_entry_point("input")
        self.graph.add_node("input", lambda x: x)
        self.graph.add_node("output", lambda x: x)
        self.graph.add_edge("input", "output")
        self.graph.set_finish_point("output")
        self.compiled = self.graph.compile()

    async def run(self, user_input: str) -> dict:
        ctx = StageContext(stage=Stage.PREPROCESSOR, input_data=user_input)
        return await self.compiled.ainvoke(ctx)
