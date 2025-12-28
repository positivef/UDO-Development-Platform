# Tier 2 Config Schema
from pydantic import BaseModel

class Config(BaseModel):
    env: str = 'dev'
    debug: bool = False
