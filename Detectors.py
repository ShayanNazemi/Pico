import pandas as pd
import time
import threading
import requests
from abc import abstractmethod
from binance.client import Client


class Detector:
    def __init__(self, symbols, debug):
        self.symbols = [symbol.upper() for symbol in symbols]
        self.debug = debug
        self.API_KEY = 'hACyfH2WFLuhlGC5wecVHF9l1MokEQ6OPKYq5GjMrIjPl8LtTQ2I21U69Kp1KU5n'
        self.SECRET_KEY = 'kO53EX9Az4zT1nCYJbVhUa0ab6jDelxqTIvCBIK8704Y1aodnilEc9Upl8fx5ORW'

        self.token = "1832200647:AAFPl1Bw7k8j6PiSCjJ9J9J2dLc4UX6Ki4Y"
        self.bot_endpoint = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.chat_id = "57466123"
        self.client = Client(self.API_KEY, self.SECRET_KEY)

    @abstractmethod
    def fetch(self):
        raise NotImplementedError

    @abstractmethod
    def signal(self):
        raise NotImplementedError

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


class MACrossDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug)

    def fetch(self, symbol):
        t = "1 day ago UTC"
        klines = self.client.get_historical_klines(symbol, Client.KLINE_INTERVAL_5MINUTE, t)
        klines = pd.DataFrame(klines).iloc[:, [0, 4, 6]].astype(float)
        klines.columns = ['t', 'close', 't_close']
        klines.t = pd.to_datetime(klines.t, unit='ms')
        klines.t_close = pd.to_datetime(klines.t_close, unit='ms')
        klines.set_index('t', inplace=True)
        return klines

    def signal(self, symbol):
        print(f"Called on : {pd.Timestamp(int(time.time()), unit='s')}")
        price = self.fetch(symbol)
        price['ma50'] = price.close.rolling(50).mean()
        price['ma200'] = price.close.rolling(200).mean()

        last2 = price.iloc[-3]
        last = price.iloc[-2]
        if (last.ma50 > last.ma200) and (last2.ma50 <= last2.ma200):
            print('Uptrend signal has been spotted ===> Notifying User ...')
            message = f"MA50-200 Cross ABOVE Detected\n50-200 Cross Above on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {price.close.iloc[-1]}"
            self.send_message(message)

        elif (last.ma50 < last.ma200) and (last2.ma50 >= last2.ma200):
            print('Downtrend signal has been spotted ===> Notifying User ...')
            signal = {'status': 'sell', 'price': price.close.iloc[-1], 'symbol': symbol}
            message = f"MA50-200 Cross BELOW Detected\n50-200 Cross Below on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {price.close.iloc[-1]}"
            self.send_message(message)

        else:
            if self.debug:
                self.send_message(f"No MA50-200 Cross signal has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            print('No MA50-200 cross has been detected')

        if (last2.close >= last2.ma200) and (last.close < last.ma200):
            print('Possible pullback to MA200 ===> Notifying User ...')
            message = f"MA200 Pullback Detected (Cross BELOW)\n{symbol} Price Crossed Below MA200 \n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {last.close}\n\tMA200 : {last.ma200}"
            self.send_message(message)

        elif (last2.close <= last2.ma200) and (last.close > last.ma200):
            print('Possible pullback to MA200 ===> Notifying User ...')
            message = f"MA200 Pullback Detected (Cross ABOVE)\n{symbol} Price Crossed Above MA200 \n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {last.close}\n\tMA200 : {last.ma200}"
            self.send_message(message)
        else:
            if self.debug:
                self.send_message(f"No MA200 pullback has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            print('No MA200 pullback has been detected')

    def signal_all(self):
        thread_queue = []
        for s in self.symbols:
            thread_queue.append(threading.Thread(target=self.signal, args=(s,)))

        for t in thread_queue:
            t.start()
            time.sleep(0.5)
