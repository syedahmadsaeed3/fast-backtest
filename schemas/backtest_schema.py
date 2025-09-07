from pydantic import BaseModel
from services.data_models import data


class Backtest(data):
    strategy_name: str
    status: str
    allocation: int = None
    win: int
    avg_trade: int
    return_perc: int
    trades: int
    type: str
    starred: bool
    is_deleted: bool

    class Config:
        orm_mode = True


class BacktestResponse(BaseModel):
    status: str
    ticker: str
    limit: int = None
    resolution: str = None
    type: str
    buy: list
    sell: list
    customized_buy_signal: list
    customized_sell_signal: list
    strategy_name: str
    allocation: int = None
    win: int
    avg_trade: int
    return_perc: int
    trades: int
    starred: bool

