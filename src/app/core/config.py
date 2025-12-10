

# Security Config

class Settings:
    SECRET_KEY = "backEndProject"
    ALGORITHM ="HS256"
    ACCESS_TOKEN_EXPIRES = 30
    REFRESH_TOKEN_EXPIRES = 1 #in days


settings = Settings()
