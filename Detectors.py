import pandas as pd
import time
import threading
import requests
from ta.momentum import rsi
from utils import *
from abc import abstractmethod
from DataHandler import DataHandler


class Messenger:
    def __init__(self):
        self.message = None

    def set(self, message):
        self.message = message

    def add(self, message_queue):
        message_queue.append(self.message)

    def clear(self):
        self.message = ""


class Detector:
    def __init__(self, symbols, debug, name):
        self.symbols = [symbol.upper() for symbol in symbols]
        self.debug = debug
        self.name = name
        self.messenger = Messenger()

    @abstractmethod
    def signal(self):
        raise NotImplementedError

    # def send_message(self, message):
    #     message = f"* {self.name}\n{message}"
    #     params = f"?chat_id={self.chat_id}&text={message}"
    #     print(message)
    #     try:
    #         res = requests.get(self.bot_endpoint + params, timeout=10)
    #     except Exception as e:
    #         # one more try
    #         res = requests.get(self.bot_endpoint + params, timeout=10)
    #     if res.status_code == 200:
    #         print('Notification sent successfully ...')
    #     else:
    #         print('Failed to send notification!')

    def log(self, string_):
        print(f"({self.name.upper()}) {string_}")


class DetectorManager:
    def __init__(self, symbols, debug):
        self.datahandler = DataHandler()
        self.symbols = symbols
        self.debug = debug
        self.detectors = []
        self.message_queue = []

        self.token = "1832200647:AAFPl1Bw7k8j6PiSCjJ9J9J2dLc4UX6Ki4Y"
        self.bot_endpoint = f"https://api.telegram.org/bot{self.token}/sendMessage"
        self.chat_id = "57466123"

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

        for thread in thread_queue:
            thread.join()

        for d in self.detectors:
            d.messenger.add(self.message_queue)

        self.send_message()

        for d in self.detectors:
            d.messenger.clear()

    def send_message(self):
        message = ""
        for msg in self.message_queue:
            if msg:
                message += f"{msg}\n"

        print(f"From Detector Manager :\n{message}")
        if message:
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


class TrendShiftDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug, "Trend Shift")

    def signal(self, data, symbol):
        data['ma50'] = data.close.rolling(50).mean()
        data['ma200'] = data.close.rolling(200).mean()

        last2 = data.iloc[-3]
        last = data.iloc[-2]
        if (last.ma50 > last.ma200) and (last2.ma50 <= last2.ma200):
            self.log('Uptrend signal has been spotted ===> Notifying User ...')
            message = f"MA50-200 Cross ABOVE Detected\n50-200 Cross Above on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {data.close.iloc[-1]}"
            self.messenger.set(message)
            # self.send_message(message)

        elif (last.ma50 < last.ma200) and (last2.ma50 >= last2.ma200):
            self.log('Downtrend signal has been spotted ===> Notifying User ...')
            message = f"MA50-200 Cross BELOW Detected\n50-200 Cross Below on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {data.close.iloc[-1]}"
            self.messenger.set(message)
            # self.send_message(message)

        else:
            if self.debug:
                self.messenger.set(f"No MA50-200 Cross signal has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
                # self.send_message(f"No MA50-200 Cross signal has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")

            self.log('No MA50-200 cross has been detected')


class MACrossDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug, 'MA Cross')

    def signal(self, data, symbol):
        data['ma200'] = data.close.rolling(200).mean()

        last2 = data.iloc[-3]
        last = data.iloc[-2]

        if (last2.close >= last2.ma200) and (last.close < last.ma200):
            self.log('Possible pullback to MA200 ===> Notifying User ...')
            message = f"MA200 Pullback Detected (Cross BELOW)\n{symbol} Price Crossed Below MA200 \n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {last.close}\n\tMA200 : {last.ma200}"
            self.messenger.set(message)
            # self.send_message(message)

        elif (last2.close <= last2.ma200) and (last.close > last.ma200):
            self.log('Possible pullback to MA200 ===> Notifying User ...')
            message = f"MA200 Pullback Detected (Cross ABOVE)\n{symbol} Price Crossed Above MA200 \n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tPrice : {last.close}\n\tMA200 : {last.ma200}"
            self.messenger.set(message)
            # self.send_message(message)
        else:
            if self.debug:
                self.messenger.set(f"No MA200 pullback has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
                # self.send_message(f"No MA200 pullback has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            self.log('No MA200 pullback has been detected')


class HammerDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug, 'Hammer Candle')

    def signal(self, data, symbol):
        last = data.iloc[-2]
        body = abs(last.close - last.open)
        shadow_up = abs(last.high - last.close) if last.close >= last.open else abs(last.high - last.open)
        shadow_down = abs(last.open - last.low) if last.close >= last.open else abs(last.close - last.low)
        if (shadow_up >= 5 * body) and (body >= 5 * shadow_down):
            # Shooting Star Candle
            self.log('Shooting star candle detected ===> Notifying User ...')
            message = f"Shooting star candle detected on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}"
            self.messenger.set(message)
            # self.send_message(message)
        elif (shadow_down >= 5 * body) and (body >= 5 * shadow_up):
            # Hammer Candle
            self.log('Hammer candle detected ===> Notifying User ...')
            message = f"Hammer candle detected on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}"
            self.messenger.set(message)
            # self.send_message(message)
        else:
            if self.debug:
                self.messenger.set(f"No Hammer or Shooting start candle has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
                # self.send_message(f"No Hammer or Shooting start candle has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            self.log('No Shooting Star nor Hammer candle has been detected')


class DivergenceDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug, 'RSI Divergence')

    def signal(self, data, symbol):
        rsi_ = rsi(data.iloc[:-1].close).dropna()
        rsi_pivots = peak_valley_pivots(rsi_, 0.1, -0.1)
        peaks, valleys = rsi_pivots == 1, rsi_pivots == -1

        if rsi_[peaks][-2] > rsi_[peaks][-1] and data.loc[rsi_.index, 'close'][peaks][-2] < data.loc[rsi_.index, 'close'][peaks][-1]:
            self.log('RSI Divergence on PEAK detected ===> Notifying User ...')
            message = f"RSI Divergence on PEAK has been detected on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tFirst Peak : {rsi_[peaks].index[-2]}\n\tSecond Peak : {rsi_[peaks].index[-1]}"
            self.messenger.set(message)
            # self.send_message(message)

        elif rsi_[valleys][-2] < rsi_[valleys][-1] and data.loc[rsi_.index, 'close'][valleys][-2] > data.loc[rsi_.index, 'close'][valleys][-1]:
            self.log('RSI Divergence on VALLEY detected ===> Notifying User ...')
            message = f"RSI Divergence on VALLEY has been detected on {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n\tFirst Valley : {rsi_[valleys].index[-2]}\n\tSecond Valley : {rsi_[valleys].index[-1]}"
            self.messenger.set(message)
            # self.send_message(message)

        else:
            if self.debug:
                # self.send_message(f"No RSI Divergence has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
                self.messenger.set(f"No RSI Divergence has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            self.log('No RSI Divergence has been detected')


class BBDetector(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug, 'Bollinger Bands')
        self.ma_window = 24
        self.bb_dev = 3.9

    def signal(self, data, symbol):
        data_ = data.iloc[:-1].close
        ma = data_.rolling(self.ma_window).mean().iloc[-1]
        std = data_.rolling(self.ma_window).std().iloc[-1]
        ub = ma + self.bb_dev * std
        lb = ma - self.bb_dev * std

        last = data.iloc[-2]

        if last.low < lb:
            self.log('Price crossed below BB4 lower bound')
            if last.close < lb:
                message = f"Price crossed and closed BELOW BB4 lower bound in {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n"
            else:
                message = f"Price crossed BELOW BB4 lower bound in {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n"
            self.messenger.set(message)
            # self.send_message(message)

        elif last.high > ub:
            self.log('Price crossed above BB4 upper bound')
            if last.close > ub:
                message = f"Price crossed and closed ABOVE BB4 upper bound in {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n"
            else:
                message = f"Price crossed ABOVE BB4 upper bound in {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n"
            self.messenger.set(message)
            # self.send_message(message)

        else:
            if self.debug:
                self.messenger.set(f"No BB4 crossing has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
                # self.send_message(f"No BB4 crossing has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            self.log('No BB4 crossing has been detected')


class ThreeMACross(Detector):
    def __init__(self, symbols, debug):
        super().__init__(symbols, debug, 'Three MA Cross')
        self.w1 = 21
        self.w2 = 50
        self.w3 = 200

    def signal(self, data, symbol):
        data_ = data.iloc[:-1].close
        ma1 = data_.rolling(self.w1).mean()
        ma2 = data_.rolling(self.w2).mean()
        ma3 = data_.rolling(self.w3).mean()

        if (ma1.iloc[-1] > ma2.iloc[-1] > ma3.iloc[-1]) and (not (ma1.iloc[-2] > ma2.iloc[-2] > ma3.iloc[-2])):
            self.log('Three MA uptrend formation detected')
            message = f"Three MA uptrend formation detected in {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n"
            self.messenger.set(message)
            # self.send_message(message)

        elif (ma1.iloc[-1] < ma2.iloc[-1] < ma3.iloc[-1]) and (not (ma1.iloc[-2] < ma2.iloc[-2] < ma3.iloc[-2])):
            self.log('Three MA downtrend formation detected')
            message = f"Three MA downtrend formation detected in {symbol}\n\tTime : {pd.Timestamp(int(time.time()), unit='s')}\n"
            self.messenger.set(message)
            # self.send_message(message)

        else:
            if self.debug:
                self.messenger.set(f"No three MA formation has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
                # self.send_message(f"No three MA formation has been detected on {symbol}\n{pd.Timestamp(int(time.time()), unit='s')}")
            self.log('No three MA formation has been detected')
