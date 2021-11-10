import threading
import time

x = True

def print_work_a():
    while x:
        print('Starting of thread :', threading.currentThread().name)
        time.sleep(2)
        print('Finishing of thread :', threading.currentThread().name)


def print_work_b():
    while x:
        print('Starting of thread :', threading.currentThread().name)
        time.sleep(2)
        print('Finishing of thread :', threading.currentThread().name)

a = threading.Thread(target=print_work_a, name='Thread-a', daemon=True)
b = threading.Thread(target=print_work_b, name='Thread-b', daemon=True)

a.start()
b.start()

while True:
    x = input()
    if '#' in x:
        break