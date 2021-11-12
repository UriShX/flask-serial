import asyncio

import aioserial

import multiprocessing as mp

from flask_serial import PortSettings

import serial

class ProcessSerial(object):

    def __init__(self, settings: PortSettings):
        self.settings = settings
        self.serial = serial.Serial()

    def connect(self):
        self.serial.port     = self.settings.port
        self.serial.timeout  = self.settings.timeout
        self.serial.baudrate = self.settings.baudrate
        self.serial.bytesize = self.settings.bytesize
        self.serial.parity   = self.settings.parity
        self.serial.stopbits = self.settings.stopbits
        self.serial.open()


async def read_and_forward(q: mp.Queue, aioserial_instance: aioserial.AioSerial):
    while True:
        q.put((await aioserial_instance.read_async()).decode(errors='ignore'))


def async_port(q: mp.Queue, settings: PortSettings):
    serial = aioserial.AioSerial(port=settings.port, baudrate=settings.baudrate)
    asyncio.run(read_and_forward(q, serial))


def thread_port(q: mp.Queue, settings: PortSettings):
    ps = ProcessSerial(settings)
    ps.connect()

    while True:
        line = ps.serial.readline()
        q.put(line)