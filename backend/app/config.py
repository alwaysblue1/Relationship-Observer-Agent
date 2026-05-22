from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/relationship_observer"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    spotify_mcp_url: str = ""

    bailian_api_key: str = ""

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    max_upload_size_mb: int = 50
    embedding_dim: int = 1536

    # Aliyun DashScope text-embedding-v4
    aliyun_embedding_model: str = "text-embedding-v4"
    aliyun_embedding_dim: int = 1024
    aliyun_embedding_url: str = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"

    # RAG settings
    rag_top_k: int = 3
    rag_similarity_threshold: float = 0.6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
