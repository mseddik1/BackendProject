from pathlib import Path
from pydantic_settings import BaseSettings


# Security Config
#This because i do have the 
APP_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = APP_DIR / ".env.dev"
class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES: int
    REFRESH_TOKEN_EXPIRES: int
    SMTP_SERVER: str
    SMTP_PORT: int
    SENDER_EMAIL: str
    APP_PASSWORD: str
    DEMO_API_KEY: str | None = None  # optional

    # class Config:
    #     env_file = ".env.dev"

settings = Settings(_env_file=ENV_PATH)
