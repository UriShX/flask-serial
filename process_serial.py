import multiprocessing as mp
import threading
import time

from serial import Serial

# from flask import Flask, render_template
from flask_serial import PortSettings
# from flask_socketio import SocketIO
# from flask_bootstrap import Bootstrap


# from gevent import monkey
# monkey.patch_all()


# app = Flask(__name__)

port = PortSettings(
    port     = 'COM5',
    timeout  = 0.1,
    baudrate = 9600,
    bytesize = 8,
    parity   = 'N',
    stopbits = 1
)

# app.config.from_mapping(**port.to_config_dict())


# socketio = SocketIO(app)
# bootstrap = Bootstrap(app)


# @app.route('/')
# def index():
#     return render_template('index.html')

class ProcessSerial(object):

    def __init__(self, settings: PortSettings):
        self.settings = settings
        self.serial = Serial()

    def connect(self):
        self.serial.port     = self.settings.port
        self.serial.timeout  = self.settings.timeout
        self.serial.baudrate = self.settings.baudrate
        self.serial.bytesize = self.settings.bytesize
        self.serial.parity   = self.settings.parity
        self.serial.stopbits = self.settings.stopbits
        self.serial.open()


import sys

def worker(q: mp.Queue):
    settings: PortSettings = q.get()
    port = ProcessSerial(settings)
    port.connect()
    while True:
        line = port.serial.readline()
        if len(line) > 0:
            q.put(line)


def listener(q: mp.Queue):
    while True:
        while q.empty():
            time.sleep(0.3)

        line = q.get()
        print(line)
        # socketio.emit("serial_message", data={"message":str(line)})

if __name__ == '__main__':
    queue = mp.Queue()

    p = mp.Process(target=worker, args=(queue,))
    p.start()

    # t = threading.Thread(target=listener, args=(queue,), daemon=True)
    # t.start()

    queue.put(port)

    while True:
        while queue.empty():
            continue
        line = queue.get()
        print(line)

    p.join()


# if __name__ == '__main__':
#     socketio.run(app, debug=False)

#     queue.put(port)

#     # Wait for the worker to finish
#     queue.close()
#     queue.join_thread()
#     p.join()
