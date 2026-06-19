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


config = PipelineConfig()
