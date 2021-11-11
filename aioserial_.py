import asyncio

import aioserial

from flask import Flask, render_template
from flask_serial import PortSettings
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap


from gevent import monkey
monkey.patch_all()


app = Flask(__name__)

port = PortSettings(
    port     = 'COM5',
    timeout  = 0.1,
    baudrate = 9600,
    bytesize = 8,
    parity   = 'N',
    stopbits = 1
)

app.config.from_mapping(**port.to_config_dict())


socketio = SocketIO(app, async_mode="gevent")
bootstrap = Bootstrap()


@app.route('/')
def index():
    return render_template('index.html')


async def read_and_print(aioserial_instance: aioserial.AioSerial):
    while True:
        print((await aioserial_instance.read_async()).decode(errors='ignore'), end='', flush=True)

asyncio.run(read_and_print(aioserial.AioSerial(port='COM5')))


bootstrap.init_app(app)
socketio.run(debug=True)
