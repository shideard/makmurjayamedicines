from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Klinik Makmur Jaya"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # SQLite Database
    DATABASE_URL: str = "sqlite:///./makmurjaya.db"
    
    # Security
    SECRET_KEY: str = "supersecretkey_change_this_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    class Config:
        env_file = ".env"

settings = Settings()
