from pydantic import BaseModel


class BacktestActivity(BaseModel):
    days: int
    ticker: str
    buy_exp: str
    sell_exp: str
    buy: dict
    sell: dict

    class Config:
        orm_mode = True



