import os


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret")
    ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"

    PORT: int = int(os.getenv("PORT", "8000"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_chatrooms"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "qwen")

    QWEN_API_KEY: str | None = os.getenv("QWEN_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    AZURE_OPENAI_API_KEY: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")

    AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-1")

    @staticmethod
    def from_env() -> "Config":
        return Config()