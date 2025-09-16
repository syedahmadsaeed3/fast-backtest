from pydantic import BaseModel
from typing import Any, Optional, List
from datetime import datetime

from schemas.strategy_porfolio_schema import CustomizedSignal


class Stoch(BaseModel):
    close: list
    high: list
    low: list
    slowk_period: int


class StochOutput(BaseModel):
    slowk: list
    slowd: list


class Dema(BaseModel):
    close: list
    timeperiod: int


class DemaOutput(BaseModel):
    close: list
    real: list


class Ma(BaseModel):
    close: list
    timeperiod: int


class MaOutput(BaseModel):
    close: list
    real: list


class Sma(BaseModel):
    close: list
    timeperiod: int


class SmaOutput(BaseModel):
    close: list
    real: list


class Macd(BaseModel):
    close: list
    slowperiod: int
    fastperiod: int
    signalperiod: int


class MacdOutput(BaseModel):
    macd: list
    macdsignal: list


class HeikenAshi(BaseModel):
    aggregates: list
    candle_number: int
    candle_state: str


class HeikenAshiOutput(BaseModel):
    trend: list


class Adx(BaseModel):
    close: list
    high: list
    low: list
    timeperiod: int


class AdxOutput(BaseModel):
    close: list
    real: list


class Bbands(BaseModel):
    close: list
    timeperiod: int
    nbdevup: int
    nbdevdn: int


class BbandsOutput(BaseModel):
    close: list
    real: list


class Rsi(BaseModel):
    close: list
    timeperiod: int


class RsiOutput(BaseModel):
    real: list
    close: list


class Sar(BaseModel):
    high: list
    low: list
    acceleration: int
    maximum: int


class SarOutput(BaseModel):
    real: list
    close: list


class Willr(BaseModel):
    close: list
    high: list
    low: list
    timeperiod: int


class WillrOutput(BaseModel):
    close: list
    real: list


class Supertrend(BaseModel):
    close: Any
    high: Any
    low: Any
    period: int
    multiplier: int

    class Config:
        arbitrary_types_allowed = True


class SupertrendOutput(BaseModel):
    trend: list


class DataServiceResponse(BaseModel):
    close: float
    open: float
    high: float
    low: float
    timestamp: datetime


class data(BaseModel):
    ticker: str
    limit: int  # 10 20 30
    resolution: str # 1d 1m 5m 5h
    buy: list
    sell: list
    buy_exp: str
    sell_exp: str
    # customized_buy_signal: Optional[List[CustomizedSignal]]
    # customized_sell_signal: Optional[List[CustomizedSignal]]


class LiveStrategy(BaseModel):
    strategy_name: str
    is_simulated: bool = True
    subscribe_alert: bool = True


class BacktestCustom(BaseModel):
    ticker: list
    days: int
    buy: dict
    sell: dict
    buy_exp: str
    sell_exp: str
    leverage: list
    allocation: list



class hypothesis_data(BaseModel):
    ticker: str
    magnitude: float
    direction: str
    timeperiod: int