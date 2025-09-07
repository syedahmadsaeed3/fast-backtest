from services.options_models import OptionStrategy
from services.vectorbt_opensource_service import VectorbtService
# from services.vectorbt_service import VectorbtService
from services.polygon_service import PolygonService
from services.yfinance_service import Yfinance
from datetime import datetime
import pandas as pd
import json
from services.thetadata_service import ThetadataService
from services.binance_service import BinanceService

input_mapping = {
    "buy": [
        {
            "HEIKEN_ASHI": {
                "candle_state": "bullish",
                "candle_number": 3
            },
        },
        {
            "HEIKEN_ASHI": {
                "candle_state": "bullish",
                "candle_number": 2
            },
        }
    ],
    "sell": [
        {
            "MA": {
                "timeperiod": 3
            },
        },
        {
            "HEIKEN_ASHI": {
                "candle_state": "bearish",
                "candle_number": 3
            },
        }
    ],
    "buy_exp": "HEIKEN_ASHI & HEIKEN_ASHI",
    "sell_exp": "HEIKEN_ASHI & MA",
}

for items in input_mapping["buy"]:
    for key, value in list(items.items()):
        name = key
        input_mappings = value
# input_mapping = {
#     "buy": {
#         "HEIKEN_ASHI": {
#             "candle_state": "bullish",
#             "candle_number": 3
#         },
#         "MA": {
#             "timeperiod": 14
#         }
#     },
#     "sell": {
#         "HEIKEN_ASHI": {
#             "candle_state": "bearish",
#             "candle_number": 2
#         },
#     },
#     "buy_exp": "HEIKEN_ASHI",
#     "sell_exp": "(HEIKEN_ASHI)"
# }

buy = []
for i in input_mapping['buy']:
    for j in i.values():
        for k in j.keys():
            buy.append(j[k])

sell = []
for i in input_mapping['sell']:
    for j in i.values():
        for k in j.keys():
            sell.append(j[k])

print("enter company symbol")
# symbol = input()

polygon = PolygonService()
res = polygon.get_n_day_data(500, "AAPL")

thetadata = ThetadataService()
expirations = thetadata.get_opt_expirations("AAPL")

"""
TODO: implement factory method to return either vectorbt or vectorbt pro
"""
vbt = VectorbtService()
# params = vbt.create_params(buy, sell)
close_list = [float(x.close) for x in res]
high = [float(x.high) for x in res]
low = [float(x.low) for x in res]


# for i in tqdm(range(len(params[0]))):
options = OptionStrategy.parse_obj({
    "Underlying": 'AAPL',
    "Direction": 1,
    "Right": "P",
    "DTE": 10,
    "Moneyness": "Out-Of-The-Money",
    "PctFromMktPrice": 10,
    "expirations": expirations
})

vbt.custom_indicator_backtester(res, close_list, high, low, input_mapping, options)
entries, exits = vbt.get_entries_and_exits()
close_list = pd.DataFrame([float(x.close) for x in res], index=[datetime.fromtimestamp(x.timestamp/1000) for x in res])
pf = vbt.run_portfolio(close_list, 1000000)
print(vbt.get_max_stats())






