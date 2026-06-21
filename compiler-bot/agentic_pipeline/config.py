from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AGENTIC_")

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    log_level: str = "info"
    memory_dir: str = "/tmp/agentic_memory"
    max_retries: int = 3
    cache_enabled: bool = True
    offline: bool = False
    ir_only: bool = False
    stage_models: dict[str, str] = {
        "preprocess": "gpt-4o-mini",
        "intent": "gpt-4o",
        "plan": "gpt-4o",
        "reasoning": "gpt-4o",
        "generate": "gpt-4o",
        "verify": "gpt-4o",
        "format": "gpt-4o-mini",
    }


config = PipelineConfig()
