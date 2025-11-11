"""
Application configuration
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Paths
    APP_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = APP_DIR / "data"
    SCANS_DIR: Path = DATA_DIR / "scans"
    REPORTS_DIR: Path = DATA_DIR / "reports"
    LOGS_DIR: Path = DATA_DIR / "logs"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR}/platform.db"
    
    # Application
    APP_NAME: str = "Offensive Security Platform"
    APP_VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = "change-this-in-production-to-a-random-string"
    TOKEN_EXPIRE_HOURS: int = 24
    
    # Tool settings
    DEFAULT_TIMEOUT: int = 300
    MAX_CONCURRENT_SCANS: int = 5
    
    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.SCANS_DIR.mkdir(exist_ok=True)
        self.REPORTS_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)

settings = Settings()