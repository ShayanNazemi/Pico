import pandas as pd
from binance.client import Client


class DataHandler:
    def __init__(self):
        self.API_KEY = 'hACyfH2WFLuhlGC5wecVHF9l1MokEQ6OPKYq5GjMrIjPl8LtTQ2I21U69Kp1KU5n'
        self.SECRET_KEY = 'kO53EX9Az4zT1nCYJbVhUa0ab6jDelxqTIvCBIK8704Y1aodnilEc9Upl8fx5ORW'
        self.client = Client(self.API_KEY, self.SECRET_KEY)

    def fetch(self, symbol):
        t = "1 day ago UTC"
        klines = self.client.get_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE, t)
        klines = pd.DataFrame(klines).iloc[:, [0, 1, 2, 3, 4, 6]].astype(float)
        klines.columns = ['t', 'open', 'high', 'low', 'close', 't_close']
        klines.t = pd.to_datetime(klines.t, unit='ms')
        klines.t_close = pd.to_datetime(klines.t_close, unit='ms')
        klines.set_index('t', inplace=True)
        return klines
