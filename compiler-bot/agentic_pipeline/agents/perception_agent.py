"""PerceptionAgent — analiza entrada con intent_handler (F4) + fallback NLP (N3.2a)."""

from __future__ import annotations

from agentic_pipeline.agents.agent_mediator import AgentMessage, PerceptionResult
from agentic_pipeline.agents.base_agent import Agent, SharedContext, Task, TaskResult
from agentic_pipeline.prompt_chain.llm_backend import LLMBackend
from agentic_pipeline.world_model import WorldModel


class PerceptionAgent(Agent):
    """Agente especializado en percepcion y analisis semantico."""

    name = "perception_agent"
    role = "analizar entrada del usuario con NLP"
    subscriptions = ["task.assigned"]

    def __init__(
        self,
        context: SharedContext,
        world: WorldModel | None = None,
        llm: LLMBackend | None = None,
    ):
        super().__init__(context)
        self.world = world or WorldModel()
        self._llm = llm
        self._spacy = None
        self._classifier = None

    def _get_spacy(self):
        if self._spacy is None:
            try:
                from agentic_pipeline.nodes.preprocessor import SpacyProcessor

                self._spacy = SpacyProcessor()
            except Exception:
                self._spacy = False
        return self._spacy if self._spacy else None

    def _get_classifier(self):
        if self._classifier is None:
            try:
                from agentic_pipeline.nodes.perception_unit import (
                    SentenceTransformerClassifier,
                )

                self._classifier = SentenceTransformerClassifier()
            except Exception:
                self._classifier = False
        return self._classifier if self._classifier else None

    def _disambiguate(self, term: str, context: list[str]) -> dict | None:
        try:
            from agentic_pipeline.nodes.parser import disambiguate_term

            return disambiguate_term(term, context)
        except Exception:
            return None

    def on_message(self, msg: AgentMessage) -> None:
        if msg.topic == "task.assigned" and self.mediator:
            payload = msg.payload
            text = payload.get("text", payload.get("description", ""))
            result = self._process_sync(text)
            self.mediator.send(
                AgentMessage(
                    sender=self.name,
                    topic="perception.completed",
                    payload=PerceptionResult(
                        raw=text,
                        intent=result.get("intent", {}),
                        entities=result.get("entities", []),
                        slots=result.get("slots", {}),
                        confidence=result.get("confidence", 0.0),
                    ),
                    correlation_id=msg.correlation_id,
                )
            )

    def _process_sync(self, text: str) -> dict:
        analysis: dict = {
            "raw": text,
            "spacy": None,
            "intent": None,
            "disambiguation": None,
        }
        spacy_proc = self._get_spacy()
        if spacy_proc:
            spacy_result = spacy_proc.process(text)
            if spacy_result:
                analysis["spacy"] = spacy_result
                analysis["tokens"] = spacy_result["tokens"]
        clf = self._get_classifier()
        if clf:
            intent, score = clf.classify(text)
            analysis["intent"] = {"intent": intent, "score": score}
        terms = [
            t.get("text", "") for t in (analysis.get("tokens") or []) if not t.get("is_stop", False)
        ]
        ambiguous = [t for t in terms if t in ("modulo", "entidad", "servicio", "pagina")]
        for term in ambiguous:
            result = self._disambiguate(term, [text])
            if result:
                analysis["disambiguation"] = result
        return analysis

    async def process(self, task: Task) -> TaskResult:
        text = task.params.get("text", task.description)

        if self._llm is not None:
            result_data = await self._process_with_prompt(text)
            if result_data is not None:
                if self.mediator:
                    self.mediator.send(
                        AgentMessage(
                            sender=self.name,
                            topic="perception.completed",
                            payload=PerceptionResult(
                                raw=text,
                                intent=result_data.get("intent", {}),
                                entities=result_data.get("entities", []),
                                slots=result_data.get("slots", {}),
                                confidence=result_data.get("confidence", 0.0),
                            ),
                            correlation_id=task.id,
                        )
                    )
                else:
                    self.context.publish("perception_result", result_data)
                return TaskResult(task.id, True, data=result_data)

        return await self._process_rule_based(task, text)

    async def _process_with_prompt(self, text: str) -> dict | None:
        try:
            from agentic_pipeline.prompt_chain.orchestrator import (
                _ensure_prompts_registered,
            )

            _ensure_prompts_registered()

            from agentic_pipeline.prompt_chain.prompts.intent import (
                intent_handler,
            )

            output = await intent_handler(
                normalized_text=text,
                llm=self._llm,
            )
            return {
                "raw": text,
                "spacy": None,
                "intent": {
                    "intent": output.get("intent"),
                    "score": output.get("confidence", 0.0),
                },
                "disambiguation": None,
                "module": output.get("module"),
                "entity": output.get("entity"),
                "tech": output.get("tech", []),
                "features": output.get("features", []),
                "is_ambiguous": output.get("is_ambiguous", False),
                "missing_info": output.get("missing_info", []),
            }
        except Exception:
            return None

    async def _process_rule_based(self, task: Task, text: str) -> TaskResult:
        analysis = self._process_sync(text)

        if self.mediator:
            self.mediator.send(
                AgentMessage(
                    sender=self.name,
                    topic="perception.completed",
                    payload=PerceptionResult(
                        raw=text,
                        intent=analysis.get("intent", {}),
                        entities=analysis.get("entities", []),
                        slots=analysis.get("slots", {}),
                        confidence=analysis.get("confidence", 0.0),
                    ),
                    correlation_id=task.id,
                )
            )
        else:
            self.context.publish("perception_result", analysis)
        return TaskResult(task.id, True, data=analysis)
