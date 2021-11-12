# from gevent import monkey
# monkey.patch_all()


import threading
import time
import multiprocessing as mp

from serial import Serial

from aioserial_ import async_port

from flask import Flask, render_template
from flask_serial import PortSettings
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap



port = PortSettings(
    port     = 'COM5',
    timeout  = 0.1,
    baudrate = 9600,
    bytesize = 8,
    parity   = 'N',
    stopbits = 1
)

app = Flask(__name__)

app.config.from_mapping(**port.to_config_dict())


socketio = SocketIO(app, async_mode='threading')
bootstrap = Bootstrap(app)


@app.route('/')
def index():
    return render_template('index.html')

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


def listener(q: mp.Queue):
    line = bytearray()

    time.sleep(0.1)

    while True:
        byte: str = q.get()
        line.extend(byte.encode())
        print(byte, end='')
        if byte == '\n':
            print(line.decode())
            line.clear()
        # socketio.emit("serial_message", data={"message":str(line)})

if __name__ == '__main__':
    queue = mp.Queue()

    p = mp.Process(target=async_port, args=(queue, port,))
    p.start()

    t = threading.Thread(target=listener, args=(queue,), daemon=True)
    t.start()

    # queue.put(port)
    socketio.run(app, debug=False)

    # # Wait for the worker to finish
    queue.close()
    queue.join_thread()
    p.join()
