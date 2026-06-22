"""NLP modules for intent classification, entity extraction, and slot filling.

.. deprecated::
    This module is transitional. Import from ``user_request`` instead.
    New code should use ``from user_request.nlu import ...`` or
    ``from user_request.contracts import ...``.
"""

import warnings

from user_request.contracts.enums import IntentType, RequestChannel
from user_request.contracts.request import (
    AmbiguityResult,
    Entities,
    Entity,
    IntentResult,
    RequestObject,
    Slots,
)
from user_request.contracts.response import ResponseObject
from user_request.nlu.slot_filler import SlotFiller

# Legacy re-exports — maintained for backward compatibility.
from agentic_pipeline.nlp.ambiguity_detector import AmbiguityDetector
from agentic_pipeline.nlp.enriched_input import ContextState, EnrichedInput
from agentic_pipeline.nlp.intent_classifier import IntentClassifier
from agentic_pipeline.nlp.ner_extractor import NERExtractor

__all__ = [
    "AmbiguityDetector",
    "AmbiguityResult",
    "ContextState",
    "Entities",
    "Entity",
    "EnrichedInput",
    "IntentClassifier",
    "IntentResult",
    "IntentType",
    "NERExtractor",
    "RequestChannel",
    "RequestObject",
    "ResponseObject",
    "SlotFiller",
    "Slots",
]

warnings.warn(
    "agentic_pipeline.nlp is deprecated. Use user_request.contracts and user_request.nlu instead.",
    DeprecationWarning,
    stacklevel=2,
)
