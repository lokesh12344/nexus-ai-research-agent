import os
from dotenv import load_dotenv
from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API Key")
    GEMINI_MODEL: str = Field("gemini-2.5-flash", description="Google Gemini Model ID")
    FIRECRAWL_API_KEY: str = Field(..., description="Firecrawl API Key")

    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(None, description="Langfuse Public Key")
    LANGFUSE_SECRET_KEY: Optional[str] = Field(None, description="Langfuse Secret Key")
    LANGFUSE_BASE_URL: str = Field("https://cloud.langfuse.com", description="Langfuse Base URL")

    # App Settings
    APP_NAME: str = "AI Research Agent"
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode='after')
    def check_credentials(self):
        missing_keys = []
        if not self.GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not self.FIRECRAWL_API_KEY:
            missing_keys.append("FIRECRAWL_API_KEY")

        if missing_keys:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_keys)}")

        known_gemini_models = [
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-flash-latest", "gemini-pro-latest",
            "gemini-3.8-flash", # As per user's .env
            "gemini-omni-1.1-flash", "gemini-omni-flash-preview"
        ]
        if self.GEMINI_MODEL not in known_gemini_models:
            print(f"Warning: GEMINI_MODEL '{self.GEMINI_MODEL}' is not a well-known model. "
                  f"Available models (from .env or config default) should be one of: {', '.join(known_gemini_models)}")

        return self

_settings_instance: Optional[Settings] = None

def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        load_dotenv()
        _settings_instance = Settings()
    return _settings_instance
