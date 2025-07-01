from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "b2a7e8f3a4e6c8a1b5d7c9e0f1d3e5f6a8b7c9d0e2f4a6c8")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "SUA_API_KEY_AQUI")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    
    # Caminho para o armazenamento persistente do ChromaDB
    CHROMA_PATH: str = os.environ.get("CHROMA_PATH", "chroma_db_storage")

settings = Settings()

