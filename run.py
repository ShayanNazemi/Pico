import time
import numpy as np

if __name__ == '__main__':
    x = 0
    process_num = np.random.randint(0, 10000)
    while True:
        time.sleep(2)
        x += 1
        print(f'Process : {process_num} - X = {x}')
