from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./diseasegraph.db"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    kg_python: str = ""
    zhipu_api_key: str = ""
    zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_model: str = "glm-5.3-flash"
    graph_source: str = "csv"
    graph_data_dir: str = "experiments/platform_phase_b"
    max_graph_nodes: int = 200
    max_graph_depth: int = 2
    data_upload_dir: str = "data/raw/uploads"
    max_upload_bytes: int = 250_000_000

    # Resolve the project .env from this module instead of the process CWD.
    # Otherwise CLI scripts launched from the repository root silently fall
    # back to SQLite and can inspect or update the wrong database.
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")


settings = Settings()
