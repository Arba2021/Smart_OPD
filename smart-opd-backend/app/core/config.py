import json
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    MSG91_AUTH_KEY: str
    MSG91_SENDER_ID: str
    INTERNAL_API_KEY: str
    BUFFER_TIME_SECONDS: int = 180
    NOSHOW_TIME_SECONDS: int = 300
    BOOKING_CUTOFF_HOUR: int = 8
    DEFAULT_MAX_TOKENS: int = 80
    CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:8000", "*"]'

    @property
    def cors_origins(self) -> List[str]:
        try:
            if isinstance(self.CORS_ORIGINS, list):
                return self.CORS_ORIGINS
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        return ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()