#!usr/bin/python
#-*- coding: utf-8 -*-
"""flask-serial Package.
:author: Redfalsh <13693421942@163.com>
:license: MIT, see license file or https://opensource.org/licenses/MIT
:created on 2019-01-10 10:59:22
:last modified by:   Ketchu13
:last modified time: 2020-08-26 19:20:00
:describe:
        flask-serial package is used in flask website, it can receive or send serial's data,
        you can use it to send or receive some serial's data to show website with flask-socketio
"""
__version__ = "1.1.0"

import serial
import time
import threading
import collections
import flask

from enum import IntEnum, unique
from typing import Any



@unique
class LogLevel(IntEnum):
    INFO = 0
    NOTICE = 1
    WARNING = 2
    ERR = 3
    DEBUG = 4



class Ser:
    """serial class,use thire library: pyserial"""

    def __init__(self):
        # default serial args
        self.serial = serial.Serial()
        # self.serial.timeout  = 0.1
        # self.serial.port     = "COM1"
        # self.serial.baudrate = 9600
        # self.serial.bytesize = 8
        # self.serial.parity   = "N"
        # self.serial.stopbits = 1
        self.max_recv_buf_len = 255

        self._out_packet = collections.deque()
        # serial receive threading
        self._thread = None
        self._thread_terminate = False
        self.serial_alive = False

        self._on_message = None
        self._on_send = None
        self._log = None
        self._logger = None
        # callback mutex RLock
        self._callback_mutex = threading.RLock()
        self._open_mutex = threading.Lock()


    def loop_start(self):
        self._thread = threading.Thread(target=self.loop_forever)
        self._thread.setDaemon(True)
        self._thread.start()


    def loop_forever(self):
        run = True
        while run:
            if self.serial_alive:
                break
            else:
                with self._open_mutex:
                    self._open_serial()
            time.sleep(1)
        while self.serial_alive:
            time.sleep(0.1)
            while run:
                try:
                    b = self.serial.read(self.max_recv_buf_len)
                    if not b:
                        break
                    self._handle_on_message(b)
                    self._easy_log(LogLevel.INFO, "serial received message: %s", b)
                except Exception as e:
                    pass


    def _open_serial(self):
        """try to open the serial"""
        if self.serial.port and self.serial.baudrate:
            try:
                if self.serial.isOpen():
                    self._close_serial()
                self.serial.open()
            except serial.SerialException as e:
                # print("[LogLevel.ERR] open serial error!!! %s" % e)
                # self._easy_log(LogLevel.ERR, "open serial error!!! %s", e)
                raise
            else:
                self.serial_alive = True
                self._thread = threading.Thread(target=self._recv)
                self._thread.setDaemon(True)
                self._thread.start()
                # print("[LogLevel.INFO] open serial success: %s / %s"%(self.serial.port, self.serial.baudrate))
                self._easy_log(LogLevel.INFO, "open serial success: %s / %s",self.serial.port, self.serial.baudrate)
        else:
            print("[LogLevel.ERR] port is not setting!!!")
            self._easy_log(LogLevel.ERR, "port is not setting!!!")


    def _close_serial(self):
        try:
            self.serial.close()
            self.serial_alive = False
            self._thread_terminate = False
        except:
            pass


    def _recv(self):
        """serial recv thread"""
        while self.serial_alive:
            time.sleep(0.1)
            while self.serial_alive:
                try:
                    b = self.serial.read(self.max_recv_buf_len)
                    if not b:
                        break
                    # s = str(binascii.b2a_hex(b).decode('utf-8')).upper()
                    self._handle_on_message(b)
                    self._easy_log(LogLevel.INFO, "serial receive message: %s", b)
                except Exception as e:
                    pass
                    # self.serial_alive = False
                    # self._easy_log(LogLevel.ERR, "serial err:%s", e)


    @property
    def on_message(self):
        """ If implemented, called when the serial has receive message.
        Defined to allow receive.

        """
        return self._on_message


    @on_message.setter
    def on_message(self, func):
        with self._callback_mutex:
            self._on_message = func


    def _handle_on_message(self, message):
        """serial receive message handle"""
        self.on_message(message)


    def send(self, msg):
        """send msg,
        msg: type of bytes or str"""
        with self._callback_mutex:
            if msg:
                if isinstance(msg, bytes):
                    self.serial.write(msg)
                if isinstance(msg, str):
                    self.serial.write(msg.encode('utf-8'))
            self._easy_log(LogLevel.INFO, "serial send message: %s", msg)


    @property
    def log(self):
        """If implemented, called when the serial has log information.
        Defined to allow debugging."""
        return self._log


    @log.setter
    def log(self, func):
        """ Define the logging callback implementation.

        Expected signature is:
            log_callback(level, buf)

        level:      gives the severity of the message and will be one of
                    SERIAL_LOG_INFO, SERIAL_LOG_NOTICE, SERIAL_LOG_WARNING,
                    SERIAL_LOG_ERR, and SERIAL_LOG_DEBUG.
        buf:        the message itself
        """
        self._log = func


    def _easy_log(self, level: LogLevel, fmt, *args):
        if self.log is not None:
            buf = fmt % args
            try:
                self.log(f'[{level.name}]', buf)
            except Exception:
                pass



class Serial:
    def __init__(self, app: flask.Flask):
        self.ser = Ser()
        if app is not None:
            self.init_app(app)


    def init_app(self, app: flask.Flask):
        self.ser.serial.timeout  = app.config.get("SERIAL_TIMEOUT")
        self.ser.serial.port     = app.config.get("SERIAL_PORT")
        self.ser.serial.baudrate = app.config.get("SERIAL_BAUDRATE")
        self.ser.serial.bytesize = app.config.get("SERIAL_BYTESIZE")
        self.ser.serial.parity   = app.config.get("SERIAL_PARITY")
        self.ser.serial.stopbits = app.config.get("SERIAL_STOPBITS")

        # try open serial
        self.ser.loop_start()


    def on_message(self):
        """serial receive message use decorator
        use：
            @serial.on_message()
            def handle_message(msg):
                print("serial receive message：", msg)
        """
        def decorator(handler):
            # type: (Callable) -> Callable
            self.ser.on_message = handler
            return handler

        return decorator


    def send(self, msg):
        """serial send message
        use：
            serial.send("send a message to serial")
        """
        self.ser.send(msg)


    def log(self):
        """logging
        use：
            serial.log()
            def handle_logging(level, info)
                print(info)
        """
        def decorator(handler):
            # type: (Callable) -> Callable
            self.ser.log = handler
            return handler

        return decorator
