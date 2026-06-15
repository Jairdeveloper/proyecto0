from typing import Literal
from .state_models import StageContext


class ErrorGuard:
    @staticmethod
    def should_continue(state: StageContext) -> Literal["continue", "abort"]:
        if state.last_error:
            return "abort"
        return "continue"
