from agentic_pipeline.config import config, PipelineConfig


def test_config_defaults():
    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4o-mini"
    assert config.llm_temperature == 0.3
    assert config.log_level == "info"
    assert config.max_retries == 3
    assert config.cache_enabled is True


def test_config_is_pipeline_config():
    assert isinstance(config, PipelineConfig)
