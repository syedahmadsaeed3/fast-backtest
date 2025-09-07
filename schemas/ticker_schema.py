from pydantic import BaseModel
from typing import Optional


class Ticker(BaseModel):
    symbol: str
    company_name: str
    logo: Optional[str] = None
    option: bool

    class Config:
        orm_mode = True



