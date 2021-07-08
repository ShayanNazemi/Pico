import time
import threading
import pandas as pd
from MACrossNotifier import MACrossNotifier

if __name__ == '__main__':
    btc_notifier = MACrossNotifier('BTCUSDT')
    eth_notifier = MACrossNotifier('ETHUSDT')

    try:
        last_call = pd.Timestamp(0)
        while True:
            t = pd.Timestamp(time.time(), unit='s')
            m, s = t.minute, t.second
            if m % 5 == 0 and 0 < s < 2:
                print(f"({t}) Looping ...")
                if pd.Timestamp(time.time(), unit='s') - last_call > pd.Timedelta(seconds=100):
                    last_call = pd.Timestamp(time.time(), unit='s')
                    t_btc = threading.Thread(target=btc_notifier.signal)
                    t_eth = threading.Thread(target=eth_notifier.signal)

                    t_btc.start()
                    t_eth.start()
            time.sleep(1)

    except Exception as e:
        print('Agent Stopped!')
