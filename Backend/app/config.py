from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CLUE - Financial Health Check"


settings = Settings()
