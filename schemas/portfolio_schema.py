from pydantic import BaseModel
from datetime import datetime

class Portfolio(BaseModel):
    portfolio_name: str
    securities: list

    class Config:
        orm_mode = True


class PortfolioResponse(BaseModel):
    portfolio_name: str
    securities: list


class Order(BaseModel):
    security_group_id: int
    total: float
    order_details: list
    user_id: int
    created_at: str = datetime.now()

    class Config:
        orm_mode = True