from Detectors import *

if __name__ == '__main__':
    manager = DetectorManager(['BTCUSDT', 'ETHUSDT', 'BNBUSDT'], debug=False)
    manager.add(TrendShiftDetector)
    manager.add(MACrossDetector)
    manager.add(HammerDetector)
    manager.add(DivergenceDetector)

    try:
        last_call = pd.Timestamp(0)
        while True:
            t = pd.Timestamp(time.time(), unit='s')
            m, s = t.minute, t.second
            print(f"({t}) Looping ...")
            if m % 5 == 0 and 1 < s < 3:
                if pd.Timestamp(time.time(), unit='s') - last_call > pd.Timedelta(seconds=100):
                    last_call = pd.Timestamp(time.time(), unit='s')
                    manager.detect_all()

            time.sleep(1)

    except Exception as e:
        print('Agent Stopped!')
