#!usr/bin/python
#-*- coding: utf-8 -*-
from dataclasses import  asdict
from flask import Flask, render_template
from flask_serial import Serial, PortSettings
from flask_socketio import SocketIO
from flask_bootstrap import Bootstrap

import json

import eventlet


eventlet.monkey_patch()

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


ser = Serial()
socketio = SocketIO()
bootstrap = Bootstrap()


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('send')
def handle_send(json_str):
    data = json.loads(json_str)
    ser.send(data['message'])
    print("app: Sent message: %s"%data['message'])


@ser.on_message()
def handle_message(msg):
    print("app: Received message:", msg)
    socketio.emit("serial_message", data={"message":str(msg)})

@ser.log()
def handle_logging(level, info):
    print(level, info)



if __name__ == '__main__':
    # Warning!!!
    # this must use `debug=False`
    # if you use `debug=True`,it will open serial twice, it will open serial failed!!!
    ser.init_app(app)
    socketio.init_app(app)
    bootstrap.init_app(app)
    socketio.run(app, debug=False)
