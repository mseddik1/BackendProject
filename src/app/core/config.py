from pathlib import Path
from pydantic_settings import BaseSettings


# Security Config
#This because i do have the 
APP_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = APP_DIR / ".env.prod"
class Settings(BaseSettings):
    backend_proj_secret_key: str
    algorithm: str
    access_token_expires: int
    refresh_token_expires: int
    smtp_server: str
    smtp_port: int
    backend_proj_sender_email: str
    backend_proj_sender_password: str

    # class Config:
    #     env_file = ".env.dev"

settings = Settings(_env_file=ENV_PATH)
