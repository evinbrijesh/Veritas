"""
Central configuration. Every service (Neo4j, Postgres, Redis, Ollama)
is read from environment variables so the exact same image works
identically across every cyber cell's deployment — only the .env differs.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Neo4j ---
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "changeme_in_env"

    # --- Postgres ---
    DATABASE_URL: str = "postgresql://veritas:changeme_in_env@localhost:5432/veritas"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Ollama ---
    OLLAMA_HOST: str = "http://localhost:11434"
    LLM_MODEL_NAME: str = "qwen2.5:7b"

    # --- Auth ---
    JWT_SECRET_KEY: str = "insecure_dev_key_replace_me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480

    # --- ML ---
    SYNTHETIC_DETECTOR_MODEL_PATH: str = "app/ml/weights/efficientnet_b4_synthetic.pt"

    # --- Storage ---
    EVIDENCE_STORAGE_PATH: str = "/app/evidence_storage"

    # --- Deployment identity ---
    DEPLOYMENT_NAME: str = "unnamed_cybercell"

    class Config:
        env_file = ".env"


settings = Settings()
