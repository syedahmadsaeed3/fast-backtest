import pandas as pd
from binance.client import Client

from services.data_models import DataServiceResponse


class BinanceService:

    def __init__(self):
        self.client = Client()


    def get_n_day_data(self, days=None, symbol="BTCUSDT", interval=None):
        """
        Returns historical klines from past for given symbol and interval
        past_days: how many days back one wants to download the data
        :param days: int
        :param interval: str
        :return: dict
        """

        if not interval:
            interval = '1d'  # default interval 1 day
        if not days:
            days = 500  # default past days 500.

        start_str = str((pd.to_datetime('today') - pd.Timedelta(str(days) + ' days')).date())
        data = self.client.get_historical_klines(symbol=symbol, start_str=start_str, interval=interval)
        response = []
        for d in data:
            response.append(DataServiceResponse.parse_obj({
                "timestamp": d[6],
                "open": d[1],
                "high": d[2],
                "low": d[3],
                "close": d[4]
            }))

        return response

    def get_all_crypto(self):
        exchange_info = self.client.get_exchange_info()
        crypto_list = []
        for s in exchange_info['symbols']:
            data = {}
            data['symbol'] = s['symbol']
            data['option'] = False
            data['logo'] = None
            data['company_name'] = None
            data['is_crypto'] = True
            crypto_list.append(data)

        return crypto_list

    def update_db_crypto(self, db):
        crypto = self.get_all_crypto()
        for c in crypto:
            db.table("tickers").upsert(c, returning="minimal").execute()
        return crypto