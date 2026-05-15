from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CV_DIR = UPLOADS_DIR / "cv"
SCREENSHOTS_DIR = UPLOADS_DIR / "screenshots"


class Settings(BaseSettings):
    db_url: str = f"sqlite:///{DATA_DIR}/app.db"

    model_config = {"env_file": ".env"}


settings = Settings()
