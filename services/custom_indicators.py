import pandas as pd
import numpy as np
from datetime import datetime
import talib
from numba import njit

class CustomIndicators:

    @staticmethod
    def to_heiken_ashi(candles):
        ha = []
        for i in range(0, len(candles) - 1):
            ha.append(CustomIndicators.get_heiken_ashi(candles[i], candles[i + 1]))
        return ha

    @staticmethod
    def get_heiken_ashi(prev, curr):
        ha = {}
        ha['open'] = (float(prev['open']) + float(prev['close'])) / 2
        ha['close'] = (float(curr['open']) + float(curr['close']) + float(curr['low']) + float(curr['high'])) / 4
        ha['high'] = max(float(curr['high']), float(curr['open']), float(curr['close']))
        ha['low'] = max(float(curr['low']), float(curr['open']), float(curr['close']))

        return ha

    @staticmethod
    def heiken_ashi(aggregates, candle_number, candle_state, buy=True):
        bullish_candles = 0
        ha_candles = CustomIndicators.to_heiken_ashi(aggregates)
        trend = [False]
        for i in range(0, len(ha_candles)):

            if candle_state == 'bullish':
                if ha_candles[i]['open'] < ha_candles[i]['close']:
                    bullish_candles += 1
                    if bullish_candles == candle_number:
                        trend.append(True)
                    else:
                        trend.append(False)
                else:
                    bullish_candles = 0
                    trend.append(False)
            else:
                if ha_candles[i]['open'] > ha_candles[i]['close']:
                    bullish_candles += 1
                    if bullish_candles == candle_number:
                        trend.append(True)
                    else:
                        trend.append(False)
                else:
                    bullish_candles = 0
                    trend.append(False)

        return np.array(trend)

    @staticmethod
    def find_previous_occurences(data, direction, magnitude, timeperiod):
        """
        :param data: list
        :param direction: str
        :param magnitude: float
        :param timeperiod: int
        :return: list(list)
        """
        date_range = []
        close_list = pd.Series([float(x) for x in data['close']], index=[datetime.fromtimestamp(x/1000) for x in data['timestamp']])
        base = close_list[0]
        base_ind = 0
        i = 0
        while i < len(close_list):
            for ind, value in enumerate(close_list[i:i + timeperiod]):
                difference = ((value - base) / base) * 100.0
                if direction == "down":
                    if difference < 0 and abs((abs(value - base) / base) * 100.0) >= magnitude:
                        date_range.append([base_ind, base_ind + ind + 1])
                        i = i + ind + 1
                        break

                if direction == "up":
                    if difference >= magnitude:
                        date_range.append([base_ind, base_ind + ind + 1])
                        i = i + ind + 1
                        break
            base_ind = i
            base = close_list[base_ind]
            i += 1
        return date_range

    @staticmethod
    @njit
    def get_final_bands(close, upper, lower):
        trend = np.full(close.shape, np.nan)
        dir_ = np.full(close.shape, 1)
        long = np.full(close.shape, np.nan)
        short = np.full(close.shape, np.nan)

        for i in range(1, close.shape[0]):
            if close[i] > upper[i - 1]:
                dir_[i] = 1
            elif close[i] < lower[i - 1]:
                dir_[i] = -1
            else:
                dir_[i] = dir_[i - 1]
                if dir_[i] > 0 and lower[i] < lower[i - 1]:
                    lower[i] = lower[i - 1]
                if dir_[i] < 0 and upper[i] > upper[i - 1]:
                    upper[i] = upper[i - 1]
            if dir_[i] > 0:
                trend[i] = long[i] = lower[i]
            else:
                trend[i] = short[i] = upper[i]
        return trend, dir_, long, short

    @staticmethod
    def get_basic_bands(med_price, atr, multiplier):
        matr = multiplier * atr
        upper = med_price + matr
        lower = med_price - matr
        return upper, lower

    @staticmethod
    def super_trend(close, high, low, period, multiplier):
        try:
            avg_price = talib.MEDPRICE(high, low)
            atr = talib.ATR(high, low, close, period)
            upper, lower = CustomIndicators.get_basic_bands(avg_price, atr, multiplier)
            trend, dir_, long, short = CustomIndicators.get_final_bands(close, upper, lower)
            long = pd.Series(long)
            short = pd.Series(short)
            entries = (~long.isnull()).vbt.signals.fshift()
            exits = (~short.isnull()).vbt.signals.fshift()
        except Exception as e:
            print(e)

        return entries, exits

    @staticmethod
    def super_trend_return_values(close, high, low, period, multiplier, buy=True):
        high = np.array(high)
        close = np.array(close)
        low = np.array(low)
        avg_price = talib.MEDPRICE(high, low)
        atr = talib.ATR(high, low, close, period)
        upper, lower = CustomIndicators.get_basic_bands(avg_price, atr, multiplier)
        trend, dir_, long, short = CustomIndicators.get_final_bands(close, upper, lower)
        long = pd.Series(long)
        short = pd.Series(short)
        entries = (~long.isnull()).vbt.signals.fshift()
        exits = (~short.isnull()).vbt.signals.fshift()
        return entries if buy else exits




