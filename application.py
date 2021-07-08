import time
import threading
import pandas as pd
from flask import Flask
from flask_cors import CORS
from MACrossNotifier import MACrossNotifier

application = Flask(__name__)
CORS(application, resources={r"/*": {"origins": "*"}}, support_credentials=True)


def run():
    btc_notifier = MACrossNotifier('BTCUSDT')
    eth_notifier = MACrossNotifier('ETHUSDT')
    xrp_notifier = MACrossNotifier('XRPUSDT')
    doge_notifier = MACrossNotifier('DOGEUSDT')

    try:
        last_call = pd.Timestamp(0)
        while True:
            m = pd.Timestamp(time.time(), unit='s').minute
            s = pd.Timestamp(time.time(), unit='s').second
            if m % 5 == 0 and 0 < s < 2:
                if pd.Timestamp(time.time(), unit='s') - last_call > pd.Timedelta(seconds=100):
                    last_call = pd.Timestamp(time.time(), unit='s')
                    t_btc = threading.Thread(target=btc_notifier.signal)
                    t_eth = threading.Thread(target=eth_notifier.signal)
                    t_xrp = threading.Thread(target=xrp_notifier.signal)
                    t_doge = threading.Thread(target=doge_notifier.signal)
                    t_btc.start()
                    t_eth.start()
                    t_xrp.start()
                    t_doge.start()
            time.sleep(1)
    except Exception as e:
        print('THE END')


@application.route("/")
def index():
    return "Hello from Analysor Agent!"
