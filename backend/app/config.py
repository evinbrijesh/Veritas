"""Application configuration — single source of truth.

Every value comes from environment variables injected by docker-compose:

  env_file: .env          -> JWT_*, NEO4J_PASSWORD, LLM_MODEL_NAME, ...
  environment: block      -> NEO4J_URI, REDIS_URL, DATABASE_URL, OLLAMA_HOST
                             (container hostnames — only resolvable in Docker)

Field names match env vars case-insensitively (jwt_secret_key <- JWT_SECRET_KEY).

No defaults on purpose: a missing variable must fail the boot, never silently
produce a wrong deployment label in a report or audit trail.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Auth / JWT ---
    jwt_secret_key: str
    jwt_algorithm: str
    jwt_expire_minutes: int

    # --- Databases (URLs pre-composed by docker-compose) ---
    database_url: str      # postgresql://veritas:<pw>@postgres:5432/veritas
    neo4j_uri: str         # bolt://neo4j:7687
    neo4j_password: str    # driver auth — the URI carries no credentials
    redis_url: str         # redis://redis:6379/0

    # --- ML / LLM (all inference stays local) ---
    ollama_host: str
    synthetic_detector_model_path: str
    llm_model_name: str

    # --- Deployment identity (stamped into reports and audit logs) ---
    deployment_name: str


settings = Settings()
