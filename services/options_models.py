from enum import Enum
from thetadata import OptionRight
from decimal import Decimal
from datetime import date
from pydantic import BaseModel
from typing import TypeVar
PandasDataSeries = TypeVar('pandas.core.series.Series')


class OptionContract(BaseModel):
    Underlying: str
    Right: OptionRight
    StrikePrice: Decimal
    Expiry: date
    Multiplier: int = 100


class Moneyness(Enum):
    OTM = "Out-Of-The-Money"
    ITM = "In-The-Money"


class Direction(Enum):
    Buy = 1
    Sell = -1


class OptionStrategy(BaseModel):
    Underlying: str
    Direction: Direction
    Right: OptionRight
    PctFromMktPrice: float
    Moneyness: Moneyness
    DTE: int
    expirations: PandasDataSeries

    class Config:
        arbitrary_types_allowed = True






