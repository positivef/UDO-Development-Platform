from pydantic import BaseSettings, Field
import os


class BackendConfig(BaseSettings):
    """Configuration for the backend server.
    Reads from environment variables or defaults.
    """

    host: str = Field(default="0.0.0.0", description="Host to bind the FastAPI server")
    port: int = Field(default=int(os.getenv("PORT", 8000)), description="Port for the FastAPI server")
    reload: bool = Field(default=False, description="Enable auto-reload (development)")
    environment: str = Field(default=os.getenv("ENVIRONMENT", "development"), description="Runtime environment")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
