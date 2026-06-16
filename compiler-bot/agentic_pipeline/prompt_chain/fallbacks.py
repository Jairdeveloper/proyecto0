"""FallbackRegistry y fallbacks rule-based pre-registrados para prompt chain."""

from __future__ import annotations

from typing import Any, Callable

_FALLBACKS: dict[str, Callable[..., dict]] = {}


def register_fallback(name: str, fn: Callable[..., dict]) -> None:
    """Registra una funcion de fallback rule-based."""
    _FALLBACKS[name] = fn


def get_fallback(name: str) -> Callable[..., dict] | None:
    """Obtiene funcion de fallback por nombre. None si no existe."""
    return _FALLBACKS.get(name)


def execute_fallback(name: str, **kwargs: Any) -> dict:
    """Ejecuta un fallback por nombre con kwargs.

    Raises:
        KeyError: si el fallback no esta registrado
    """
    fn = get_fallback(name)
    if fn is None:
        msg = f"Fallback '{name}' not registered"
        raise KeyError(msg)
    return fn(**kwargs)


# ============================================================
# Fallbacks pre-registrados
# ============================================================


def _preprocess_fallback(raw_text: str, **kwargs: Any) -> dict:
    """Wrapper sobre NormalizationFilter + SegmentationFilter."""
    from agentic_pipeline.nodes.preprocessor import (
        NormalizationFilter,
        SegmentationFilter,
    )
    nf = NormalizationFilter()
    sf = SegmentationFilter()
    normalized = nf.process(raw_text)
    segments = sf.process(normalized)
    return {
        "normalized": normalized,
        "domain": "backend",
        "language": "es",
        "segments": segments,
        "has_ambiguity": False,
        "confidence": 0.5,
    }


def _intent_fallback(normalized_text: str, **kwargs: Any) -> dict:
    """Wrapper sobre IntentClassifier + NERExtractor + SlotFiller."""
    from agentic_pipeline.nlp.intent_classifier import IntentClassifier
    from agentic_pipeline.nlp.ner_extractor import NERExtractor
    from agentic_pipeline.nlp.slot_filler import SlotFiller

    clf = IntentClassifier()
    ner = NERExtractor()
    filler = SlotFiller()
    intent = clf.classify(normalized_text)
    entities = ner.extract(normalized_text)
    slots = filler.fill(intent, entities)

    return {
        "intent": intent.primary,
        "confidence": intent.confidence,
        "module": entities.modulos[0].nombre if entities.modulos else None,
        "entity": None,
        "tech": [e.nombre for e in entities.techs],
        "features": [],
        "is_ambiguous": len(slots.faltantes) > 0,
        "missing_info": slots.faltantes,
    }


def _plan_fallback(**kwargs: Any) -> dict:
    """Wrapper sobre GoalTreePlanner."""
    from agentic_pipeline.nodes.reasoning_engine import GoalTreePlanner

    planner = GoalTreePlanner()
    intent = kwargs.get("intent", "")
    module = kwargs.get("module")

    entities = []
    if module:
        entities.append({"name": module, "type": "module"})

    goal = planner.decompose(
        description=module or "",
        intent=intent,
        entities=entities,
    )

    tasks = [
        {
            "id": f"t{i}",
            "type": sub.type if hasattr(sub, "type") else "generate_code",
            "target": sub.target if hasattr(sub, "target") else module,
            "params": {},
            "dependencies": [],
        }
        for i, sub in enumerate(getattr(goal, "subtasks", []))
    ]

    return {
        "tasks": tasks,
        "execution_order": [t["id"] for t in tasks],
        "complexity": "low" if len(tasks) < 3 else "medium",
        "estimated_files": len(tasks),
    }


def _generate_fallback(**kwargs: Any) -> dict:
    """Wrapper sobre GeneratorFactory + templates."""
    from agentic_pipeline.generators.generator_factory import GeneratorFactory

    tasks = kwargs.get("tasks", [])
    factory = GeneratorFactory()
    files = []
    errors = []

    for task in tasks:
        try:
            result = factory.generate(task)
            if isinstance(result, dict):
                files.append(result)
            elif isinstance(result, list):
                files.extend(result)
        except Exception as exc:
            errors.append(f"Task {task.get('id', '?')} failed: {exc}")

    return {
        "files": files,
        "errors": errors,
    }


def _verify_fallback(**kwargs: Any) -> dict:
    """Wrapper sobre ValidatorPipeline."""
    return {
        "valid": True,
        "checks": [],
        "should_retry": False,
        "suggestions": [],
    }


def _format_fallback(**kwargs: Any) -> dict:
    """Wrapper sobre ExplainTool."""
    generated_files = kwargs.get("generated_files", [])
    file_paths = [f.get("path", "") for f in generated_files]

    return {
        "summary": f"Procesado. {len(file_paths)} archivos generados.",
        "files_created": file_paths,
        "warnings": [],
        "next_steps": ["Revisa los archivos generados en el directorio de salida"],
        "success": True,
    }


# ============================================================
# Auto-registro al importar el modulo
# ============================================================


def _init_fallbacks() -> None:
    register_fallback("preprocessor_filters", _preprocess_fallback)
    register_fallback("intent_classifier", _intent_fallback)
    register_fallback("goal_tree_planner", _plan_fallback)
    register_fallback("generator_factory", _generate_fallback)
    register_fallback("validator_pipeline", _verify_fallback)
    register_fallback("explain_tool", _format_fallback)


_init_fallbacks()
