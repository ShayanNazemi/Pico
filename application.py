import time
import pandas as pd
from Detectors import MACrossDetector

if __name__ == '__main__':
    detector = MACrossDetector(['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'DOGEUSDT', 'ETCUSDT', 'BNBUSDT'])
    try:
        last_call = pd.Timestamp(0)
        while True:
            t = pd.Timestamp(time.time(), unit='s')
            m, s = t.minute, t.second
            print(f"({t}) Looping ...")
            if m % 5 == 0 and 0 < s < 2:
                if pd.Timestamp(time.time(), unit='s') - last_call > pd.Timedelta(seconds=100):
                    last_call = pd.Timestamp(time.time(), unit='s')
                    detector.signal_all()

            time.sleep(1)

    except Exception as e:
        print('Agent Stopped!')
