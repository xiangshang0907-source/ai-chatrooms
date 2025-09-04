import os
import secrets


class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-for-ai-chatrooms-2024")
    ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "0") == "1"

    PORT: int = int(os.getenv("PORT", "8000"))

    # 数据库配置 - 支持自动构建 DATABASE_URL
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # 如果没有设置 DATABASE_URL，尝试从单独的参数构建
    if not DATABASE_URL:
        POSTGRES_USER = os.getenv("POSTGRES_USER")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")  
        POSTGRES_DB = os.getenv("POSTGRES_DB")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST")
        POSTGRES_PORT = os.getenv("POSTGRES_PORT")

        # 只有当所有必需的参数都存在时才构建 DATABASE_URL
        if all([POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT]):
            DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

    # 检测测试环境的多种方式
    _is_testing = (
        os.getenv("TESTING") == "1" or 
        os.getenv("PYTEST_CURRENT_TEST") is not None or
        "pytest" in os.getenv("_", "").lower()
    )

    # 只在非测试环境下强制要求数据库连接  
    if not DATABASE_URL and not _is_testing:
        raise ValueError(
            "Database connection is required. Please set either DATABASE_URL or "
            "individual database parameters (POSTGRES_USER, POSTGRES_PASSWORD, etc.) "
            "in your .env file or environment."
        )
    
    # 在测试环境下，如果没有设置任何数据库配置，使用内存数据库
    elif not DATABASE_URL and _is_testing:
        DATABASE_URL = "sqlite:///:memory:"

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # LLM 配置
    DEFAULT_LLM_PROVIDER: str = os.getenv("DEFAULT_LLM_PROVIDER", "qwen")

    # 千问（百炼）配置
    QWEN_API_KEY: str | None = os.getenv("QWEN_API_KEY")
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

    # JWT 配置 - 使用更安全的默认值
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    JWT_ACCESS_TOKEN_EXPIRES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "3600"))
    JWT_REFRESH_TOKEN_EXPIRES: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "2592000"))

    @staticmethod
    def from_env() -> "Config":
        return Config()
