import numpy as np
import pandas as pd
from binance.client import Client
import statsmodels.api as sm


class Pico:
    def __init__(self, configs, x_symbol, y_symbol, z_symbol):
        self.configs = configs
        self.x_symbol = x_symbol
        self.y_symbol = y_symbol
        self.z_symbol = z_symbol

        self.client = None
        self.connect()

        self.interval = Client.KLINE_INTERVAL_5MINUTE
        self.lookback = self.configs['train_lookback']
        self.strategy_lookback = self.configs['ma_lookback']

        self.model = None
        self.results = None

    def connect(self):
        self.client = Client(self.configs['api_key'], self.configs['api_secret'])
        print('Connected to Binance API successfully')

    def fetch(self, s, n, lookback):
        klines = self.client.get_historical_klines(s, self.interval, lookback)
        klines = pd.DataFrame(klines).iloc[:, :7].astype(float)
        klines.columns = ['o_t', 'o', 'h', 'l', 'c', 'v', 'c_t']

        klines.o_t = pd.to_datetime(klines.o_t, unit='ms')
        klines.c_t = pd.to_datetime(klines.c_t, unit='ms')

        klines.set_index('c_t', inplace=True)
        klines.index = klines.index + pd.Timedelta(seconds=0.001)
        return klines.c.iloc[-n:]  # klines.c.iloc[-self.configs['train']:]

    @staticmethod
    def ols(x, y):
        model = sm.OLS(y, x)
        results = model.fit()
        return model, results

    def compute_residual(self, x, y):
        return y - (x * self.results.params).sum(axis=1)

    def remodel(self):
        x = self.fetch(self.x_symbol, self.configs['train'], self.lookback)
        y = self.fetch(self.y_symbol, self.configs['train'], self.lookback)
        z = self.fetch(self.z_symbol, self.configs['train'], self.lookback)

        ind = np.stack([x.values, y.values]).T
        exo = z.values

        self.model, self.results = self.ols(ind, exo)

    @staticmethod
    def bollinger_band(x, w, dev):
        ma = x.rolling(w).mean()
        std = x.rolling(w).std()
        return ma + dev * std, ma - dev * std

    def signal(self):
        x = self.fetch(self.x_symbol, self.configs['ma_window'], self.strategy_lookback)
        y = self.fetch(self.y_symbol, self.configs['ma_window'], self.strategy_lookback)
        z = self.fetch(self.z_symbol, self.configs['ma_window'], self.strategy_lookback)

        ind = np.stack([x.values, y.values]).T
        exo = z.values
        e = self.compute_residual(ind, exo)
        e_ub, e_lb = self.bollinger_band(e, self.configs['ma_window'], self.configs['bb_dv'])
        if (e[-2] < e_ub[-2]) & (e[-1] >= e_ub[-1]):
            # Sell Spread
            pass
        elif (e[-2] > e_lb[-2]) & (e[-1] <= e_lb):
            # Buy Spread
            pass
        else:
            # No signal
            pass

        x_ub, x_lb = self.bollinger_band(x, self.configs['ma_window'], self.configs['bb_dv'])
        y_ub, y_lb = self.bollinger_band(y, self.configs['ma_window'], self.configs['bb_dv'])
        z_ub, z_lb = self.bollinger_band(z, self.configs['ma_window'], self.configs['bb_dv'])

    def run(self):
        pass
