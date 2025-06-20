from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Bella API Doc Gen"
    DATABASE_URL: str = Field("sqlite:///./test.db", env="DATABASE_URL") # Replace with your actual database URL

    # Temp directory for git clones
    GIT_REPOS_BASE_PATH: str = Field("data/repos", env="GIT_REPOS_BASE_PATH")

    # Code RAG service settings
    CODE_RAG_SERVICE_URL: str = Field("http://localhost:8002/v1/code-rag", env="CODE_RAG_SERVICE_URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

settings = Settings()
