import os


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-for-ai-chatrooms-2024")
    ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"

    PORT: int = int(os.getenv("PORT", "8000"))

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/ai_chatrooms"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # LLM 配置
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "qwen")

    # 千问（百炼）配置
    QWEN_API_KEY: str = os.getenv("QWEN_API_KEY", "sk-c8c8799f8fdd4fa7a1ba0d4a7360060a")
    QWEN_API_BASE: str = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/api/v1")

    # OpenAI 配置
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

    # Azure OpenAI 配置
    AZURE_OPENAI_API_KEY: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_ENDPOINT: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")

    # AWS 配置
    AWS_REGION: str = os.getenv("AWS_REGION", "ap-southeast-1")
    AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")

    # JWT 配置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-for-ai-chatrooms-2024")
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "2592000"))

    @staticmethod
    def from_env() -> "Config":
        return Config()
