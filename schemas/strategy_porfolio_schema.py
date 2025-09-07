from datetime import datetime, timedelta
from typing import Union, List, Optional
from pydantic import BaseModel


class SecurityGroupDB(BaseModel):
    user_id: Optional[str]
    name: Optional[str]
    security: str
    allocation: float
    shares: Optional[float]


class SecurityGroup(BaseModel):
    id: Optional[int]
    user_id: Optional[str]
    name: Optional[str]
    security: str
    allocation: float
    shares: Optional[float]


class CreateSecurityGroup(BaseModel):
    name: str
    security_group_list: List[SecurityGroupDB]


class StrategyGroup(BaseModel):
    id: int
    name: str
    portfolio: int = None
    security_group: List[SecurityGroup]
    buy_security_group: List[SecurityGroup] = None
    sell_security_group: List[SecurityGroup] = None
    signal_security_group: List[SecurityGroup] = None
    buy_exp: str
    sell_exp: str
    buy: list
    sell: list
    limit: int = None
    allocation: int = None
    resolution: str = "1d"


class CustomizedSignal(BaseModel):
    id: Optional[int]
    strategy: list
    expression: str
    security_group: str


class PaperPorfolio(BaseModel):
    id: int
    strategy_id: int = None
    user_id: str
    liquid_cash: float
    strategy_group: List[StrategyGroup]


class MetricsPortfolio(BaseModel):
    user_id: str
    ticker: str
    strategy_group: Union[str, StrategyGroup] = None
    start_timestamp: datetime
    end_timestamp: datetime
    period: timedelta
    start_value: float
    end_value: float
    total_return: float
    benchmark_return: float
    max_gross_exposure: float
    total_fees_paid: float
    max_drawdown: float
    max_drawdown_duration: timedelta
    total_trades: int
    total_closed_trades: int
    total_open_trades: int
    open_trade_pnl: float
    win_rate: float
    best_trade: float
    worst_trade: float
    avg_winning_trade: float
    avg_losing_trade: float
    avg_winning_trade_duration: timedelta
    avg_losing_trade_duration: timedelta
    profit_factor: float
    expectancy: float
    sharpe_ratio: float
    calmar_ratio: float
    omega_ratio: float
    sortino_ratio: float
