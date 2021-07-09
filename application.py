import time
import threading
import pandas as pd
from MACrossNotifier import MACrossNotifier

if __name__ == '__main__':
    notifier_queue = [
        MACrossNotifier('BTCUSDT'),
        MACrossNotifier('ETHUSDT'),
        MACrossNotifier('XRPUSDT'),
        MACrossNotifier('DOGEUSDT'),
        MACrossNotifier('ETCUSDT'),
        MACrossNotifier('BNBUSDT')
    ]

    try:
        last_call = pd.Timestamp(0)
        while True:
            t = pd.Timestamp(time.time(), unit='s')
            m, s = t.minute, t.second
            print(f"({t}) Looping ...")
            if m % 5 == 0 and 0 < s < 2:
                if pd.Timestamp(time.time(), unit='s') - last_call > pd.Timedelta(seconds=100):
                    last_call = pd.Timestamp(time.time(), unit='s')
                    threads = []
                    for notif in notifier_queue:
                        threads.append(threading.Thread(target=notif.signal))

                    for thread in threads:
                        thread.start()
            time.sleep(1)

    except Exception as e:
        print('Agent Stopped!')
