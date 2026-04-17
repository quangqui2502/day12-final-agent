from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "QuangQui AI Agent"
    version: str = "1.0.0"
    environment: str = "development"
    port: int = 8000

    # Auth
    agent_api_key: str = "dev-key-please-change"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Cost guard (USD)
    monthly_budget_usd: float = 10.0
    cost_per_1k_input_tokens: float = 0.00015
    cost_per_1k_output_tokens: float = 0.0006

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
