import pandas as pd
import vectorbtpro as vbt
import numpy as np
import datetime


end = datetime.datetime.now()
start = end - datetime.timedelta(days=10)
btc_price_1d = vbt.YFData.fetch(["BTC-USD", "ETH-USD"],
        missing_index='drop').get('Close')


def combine_indicators(close, rsi_window=14, ma_window=14):
    rsi = vbt.RSI.run(close, window=rsi_window).rsi.to_numpy()
    ma = vbt.MA.run(close, ma_window).ma.to_numpy()
    trend = np.where(rsi > 70, -1, 0)
    trend = np.where((rsi < 70) & (close < ma), 1, trend)
    return trend

myInd = vbt.IndicatorFactory(
        class_name="Combination",
        short_name="comb",
        input_names=["close"],
        param_names=["rsi_window", "ma_window"],
        output_names=["value"]
        ).with_apply_func(
            combine_indicators,
            rsi_window=14,
            ma_window=14,
        )

res = myInd.run(btc_price_1d, [14, 17], [14, 17], param_product=True)
entries = res.value == 1.0
exits = res.value == -1.0

pf = vbt.Portfolio.from_signals(btc_price_1d, entries, exits)
pf.plot_cash().show()