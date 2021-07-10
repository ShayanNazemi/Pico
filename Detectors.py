import pandas as pd
import time
import threading
import requests
from abc import abstractmethod
from DataHandler import DataHandler


class Detector:
    def __init__(self, symbols, debug):
        self.symbols = [symbol.upper() for symbol in symbols]
        self.debug = debug

        self.token = "1832200647:AAFPl1Bw7k8j6PiSCjJ9J9J2dLc4UX6Ki4Y"
        self.bot_endpoint = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.chat_id = "57466123"

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


class DetectorManager:
    def __init__(self, symbols, debug):
        self.datahandler = DataHandler()
        self.symbols = symbols
        self.debug = debug
        self.detectors = []

    def add(self, detector_cls):
        self.detectors.append(detector_cls(self.symbols, self.debug))

    def detect(self, symbol):
        data = self.datahandler.fetch(symbol)
        for detector in self.detectors:
            detector.signal(data, symbol)

    def detect_all(self):
        thread_queue = []
        for s in self.symbols:
            thread_queue.append(threading.Thread(target=self.detect, args=(s,)))

        for thread in thread_queue:
            thread.start()
            time.sleep(0.5)


class TrendShiftDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug)

    def signal(self, data, symbol):
        print(f"Called on : {pd.Timestamp(int(time.time()), unit='s')}")
        data['ma50'] = data.close.rolling(50).mean()
        data['ma200'] = data.close.rolling(200).mean()

        last2 = data.iloc[-3]
        last = data.iloc[-2]
        if (last.ma50 > last.ma200) and (last2.ma50 <= last2.ma200):
            print('Uptrend signal has been spotted ===> Notifying User ...')
            message = f"MA50-200 Cross ABOVE Detected\n50-200 Cross Above on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {data.close.iloc[-1]}"
            self.send_message(message)

        elif (last.ma50 < last.ma200) and (last2.ma50 >= last2.ma200):
            print('Downtrend signal has been spotted ===> Notifying User ...')
            message = f"MA50-200 Cross BELOW Detected\n50-200 Cross Below on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {data.close.iloc[-1]}"
            self.send_message(message)

        else:
            if self.debug:
                self.send_message(f"No MA50-200 Cross signal has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            print('No MA50-200 cross has been detected')


class MACrossDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug)

    def signal(self, data, symbol):
        data['ma200'] = data.close.rolling(200).mean()

        last2 = data.iloc[-3]
        last = data.iloc[-2]

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


class HammerDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug)

    def signal(self, data, symbol):
        last = data.iloc[-2]
        body = abs(last.close - last.open)
        shadow_up = abs(last.high - last.close) if last.close >= last.open else abs(last.high - last.open)
        shadow_down = abs(last.open - last.low) if last.close >= last.open else abs(last.close - last.low)
        if (shadow_up >= 5 * body) and (body >= 5 * shadow_down):
            # Shooting Star Candle
            print('Shooting star candle detected ===> Notifying User ...')
            message = f"Shooting star candle detected on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}"
            self.send_message(message)
        elif (shadow_down >= 5 * body) and (body >= 5 * shadow_up):
            # Hammer Candle
            print('Hammer candle detected ===> Notifying User ...')
            message = f"Hammer candle detected on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}"
            self.send_message(message)
        else:
            if self.debug:
                self.send_message(f"No Hammer or Shooting start candle has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            print('No Shooting Star nor Hammer candle has been detected')
