---
id: ONB-002
area: DEV
type: GUIDE
module: ONBOARDING
version: 1.0
status: ACTIVE
tags:
  - onboarding
  - new-stage
  - pipeline-stage
summary: "Tutorial 2: como crear un nuevo PipelineStage y conectarlo al StateGraph."
---

# Tutorial 2: Anadir un Nuevo Stage

## Paso 1: Crear la clase

Crea `nodes/mi_stage.py`:

```python
from ..base_stage import PipelineStage
from ..state_models import StageContext, StageOutput, AnalysisResult, ActionPlan


class MiStage(PipelineStage):
    name = "mi_stage"

    def __init__(self, context: StageContext) -> None:
        super().__init__(context)
        self._input_data: dict | None = None

    def receive_mission(self, input_data: object) -> None:
        self._input_data = input_data if isinstance(input_data, dict) else {}

    def analyze(self) -> AnalysisResult:
        return AnalysisResult(observations=[], detected_patterns=[], risks=[], complexity_score=0.1)

    def reflect_and_plan(self, analysis: AnalysisResult) -> ActionPlan:
        return ActionPlan(steps=[], strategy="deterministic")

    def act(self, plan: ActionPlan) -> StageOutput:
        return StageOutput(
            stage=self.context.stage,
            output_data={**self._input_data, "mi_campo": "valor"},
        )

    def learn_and_improve(self, feedback: object) -> None:
        pass
```

## Paso 2: Registrar en el enum `Stage`

En `state_models.py`, anade el nuevo stage al enum:

```python
class Stage(str, Enum):
    ...
    MI_STAGE = "mi_stage"
```

## Paso 3: Conectar en el orchestrator

En `orchestrator.py`, importa tu stage y anadelo al `NODE_MAP` en la
posicion deseada:

```python
from .nodes.mi_stage import MiStage

NODE_MAP: dict[Stage, type[PipelineStage]] = {
    ...
    Stage.MI_STAGE: MiStage,
    ...
}
```

El `_build()` del orchestrator conecta automaticamente los stages en
orden secuencial con `ErrorGuard.should_continue`.

## Paso 4: Verificar

```bash
python -m pytest tests/ -q  # 524+ tests deben seguir pasando
```
