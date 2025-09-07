import vectorbt as vbt
from services.custom_indicators import CustomIndicators
from services.data_models import *

SuperTrend = vbt.IndicatorFactory(
    class_name='SuperTrend',
    short_name='st',
    input_names=['high', 'low', 'close'],
    param_names=['period', 'multiplier'],
    output_names=['supert', 'superd', 'superl', 'supers']
).from_apply_func(
    CustomIndicators.super_trend_return_values,
    period=7,
    multiplier=3,
    takes_1d=True
)


class SuperTrend(SuperTrend):
    def plot(self,
             column=None,
             close_kwargs=None,
             superl_kwargs=None,
             supers_kwargs=None,
             fig=None,
             **layout_kwargs):
        close_kwargs = close_kwargs if close_kwargs else {}
        superl_kwargs = superl_kwargs if superl_kwargs else {}
        supers_kwargs = supers_kwargs if supers_kwargs else {}

        close = self.select_col_from_obj(self.close, column).rename('Close')
        supers = self.select_col_from_obj(self.supers, column).rename('Short')
        superl = self.select_col_from_obj(self.superl, column).rename('Long')

        fig = close.vbt.plot(fig=fig, **close_kwargs, **layout_kwargs)
        supers.vbt.plot(fig=fig, **supers_kwargs)
        superl.vbt.plot(fig=fig, **superl_kwargs)

        return fig


def get_indicator(indicator):
    """
    TODO: implement a method to switch between pro and opensource version
    :param indicator: str
    :return: func
    """
    if indicator == "STOCH":
        return vbt.talib("STOCH"), Stoch, StochOutput
    if indicator == "DEMA":
        return vbt.talib("DEMA"), Dema, DemaOutput
    if indicator == "SMA":
        return vbt.talib("SMA"), Sma, SmaOutput
    if indicator == "MACD":
        return vbt.talib("MACD"), Macd, MacdOutput
    if indicator == "HEIKEN_ASHI":
        return CustomIndicators.heiken_ashi, HeikenAshi, HeikenAshiOutput
    if indicator == "MA":
        return vbt.talib("MA"), Ma, MaOutput
    if indicator == "SAR":
        return vbt.talib("SAR"), Sar, SarOutput
    if indicator == "ADX":
        return vbt.talib("ADX"), Adx, AdxOutput
    if indicator == "RSI":
        return vbt.talib("RSI"), Rsi, RsiOutput
    if indicator == "BBANDS":
        return vbt.talib("BBANDS"), Bbands, BbandsOutput
    if indicator == "WILLR":
        return vbt.talib("WILLR"), Willr, WillrOutput
    if indicator == "SUPER_TREND":
        return CustomIndicators.super_trend_return_values, Supertrend, SupertrendOutput
    if indicator == "ATR":
        return vbt.talib("ATR")
