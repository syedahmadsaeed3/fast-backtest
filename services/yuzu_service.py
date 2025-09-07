import datetime

import requests
import json
from datetime import datetime, timedelta


class YuzuService:

    def __init__(self, token=None):
        self.token = token

        self.url = 'https://graph.yuzu.dev/graphql'
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}'
        }
        self.session = requests.session()
        self.session.headers.update(self.headers)

        self.query = """
            query FigiLookup($symbol: String!, $limit: Int, $period: SecurityAggregatePeriod, $before:DateTime, $after:DateTime) {
              securities(input: {symbols: [$symbol]}) {
                symbol
                aggregates(input: {limit: $limit, period: $period, before:$before, after:$after}) {
                  time
                  open
                  high
                  low
                  close
                }
              }
            }
        """

    def get_data(self, variables={}):
        data = json.dumps({
            'query': self.query,
            'variables': variables
            })
        return self.session.post(self.url, data=data)

    def get_data_in_date_range(self, start_date, end_date, ticker):
        data = json.dumps({
            'query': self.query,
            'variables': {
                "period": "DAY",
                "after": str(start_date),
                "before": str(end_date),
                "symbol": ticker
            }
        })

        return self.session.post(self.url, data=data).json()['data']['securities'][0]['aggregates']

    def get_n_day_data(self, days, ticker):
        date = datetime.now()
        res = []
        for i in range(days // 500):
            data = json.dumps({
                'query': self.query,
                'variables': {
                    "limit": 500,
                    "period": "DAY",
                    "before": str(date),
                    "symbol": ticker
                }
            })
            date = date - timedelta(500)
            res += self.session.post(self.url, data=data).json()['data']['securities'][0][
                'aggregates']

        days = days - (500 * (days // 500))
        data = json.dumps({
            'query': self.query,
            'variables': {
                "limit": days,
                "period": "DAY",
                "before": str(date),
                "symbol": ticker
            }
        })

        res += self.session.post(self.url, data=data).json()['data']['securities'][0][
            'aggregates']

        return res


