import time
import pandas as pd
import requests
from binance.client import Client


class MACrossNotifier:
    def __init__(self, symbol='BTCUSDT'):
        self.symbol = symbol.upper()
        self.API_KEY = 'hACyfH2WFLuhlGC5wecVHF9l1MokEQ6OPKYq5GjMrIjPl8LtTQ2I21U69Kp1KU5n'
        self.SECRET_KEY = 'kO53EX9Az4zT1nCYJbVhUa0ab6jDelxqTIvCBIK8704Y1aodnilEc9Upl8fx5ORW'

        self.token = "1832200647:AAFPl1Bw7k8j6PiSCjJ9J9J2dLc4UX6Ki4Y"
        self.bot_endpoint = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.chat_id = "57466123"
        self.client = Client(self.API_KEY, self.SECRET_KEY)

    def fetch(self):
        t = "2 day ago UTC"
        klines = self.client.get_historical_klines(self.symbol, Client.KLINE_INTERVAL_5MINUTE, t)
        klines = pd.DataFrame(klines).iloc[:, [0, 4, 6]].astype(float)
        klines.columns = ['t', 'close', 't_close']
        klines.t = pd.to_datetime(klines.t, unit='ms')
        klines.t_close = pd.to_datetime(klines.t_close, unit='ms')
        klines.set_index('t', inplace=True)
        return klines

    def signal(self):
        print(f"Called on : {pd.Timestamp(int(time.time()), unit='s')}")
        price = self.fetch()
        price['ma50'] = price.close.rolling(50).mean()
        price['ma200'] = price.close.rolling(200).mean()

        last2 = price.iloc[-3]
        last = price.iloc[-2]
        if (last.ma50 > last.ma200) and (last2.ma50 <= last2.ma200):
            print('Uptrend signal has been spotted ===> Notifying User ...')
            signal = {'status': 'buy', 'price': price.close.iloc[-1]}
            self.notify(signal)

        elif (last.ma50 < last.ma200) and (last2.ma50 >= last2.ma200):
            print('Downtrend signal has been spotted ===> Notifying User ...')
            signal = {'status': 'sell', 'price': price.close.iloc[-1]}
            self.notify(signal)

        else:
            self.send_message(f"No signal has been spotted on {self.symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            print('No signal has been spotted')

    def send_message(self, message):
        params = f"?chat_id={self.chat_id}&text={message}"
        print(message)
        try:
            res = requests.get(self.bot_endpoint + params, timeout=10)
        except Exception as e:
            # one more try
            res = requests.get(self.bot_endpoint + params, timeout=10)
        if res.status_code == 200:
            print('Notification sent successfully ...')
        else:
            print('Failed to send notification!')

    def notify(self, signal):
        if signal['status'] == 'buy':
            message = f"50-200 Cross Above on {self.symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {signal['price']}"
            self.send_message(message)

        elif signal['status'] == 'sell':
            message = f"50-200 Cross Below on {self.symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {signal['price']}"
            self.send_message(message)
        else:
            pass
