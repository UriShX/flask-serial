import serial
import time
import threading
import collections
import flask

from .loglevel import LogLevel

from flask import current_app



class ThreadedSerial:
    """Threaded serial port using pySerial"""

    def __init__(self, debug: bool = False):
        # default serial args
        self.serial = serial.Serial()
        # self.serial.port     = "COM1"
        # self.serial.timeout  = 0.1
        # self.serial.baudrate = 9600
        # self.serial.bytesize = 8
        # self.serial.parity   = "N"
        # self.serial.stopbits = 1
        self.max_recv_buf_len = 255
        self.is_open = False

        self._out_packet = collections.deque()
        # serial receive threading
        self._thread = None
        self._thread_run = False
        self.serial_alive = False

        self._on_message = None
        self._on_send = None
        self._log = None
        self._logger = None
        # callback mutex RLock
        self._callback_mutex = threading.RLock()
        self._open_mutex = threading.Lock()


    def loop_start(self):
        self._open_serial()
        self._thread_run = True
        self._thread = threading.Thread(target=self.loop_forever)
        self._thread.setDaemon(True)
        self._thread.start()


    def loop_forever(self):
        while self._thread_run:
            if self.serial_alive:
                break
            time.sleep(1)
        while self.serial_alive:
            time.sleep(0.1)
            while self._thread_run:
                try:
                    b = self.serial.read(self.max_recv_buf_len)
                    if not b:
                        break
                    self._handle_on_message(b)
                    self._easy_log(LogLevel.INFO, "Received message: %s", b)
                except Exception as e:
                    pass


    def _open_serial(self):
        """try to open the serial"""
        if not self.serial.port or not self.serial.baudrate:
            msg = "The serial port is not configured!"
            print(f"[{LogLevel.ERR}] {msg}")
            self._easy_log(LogLevel.ERR, msg)
            return

        try:
            if self.is_open:
                self.serial.close()
                time.sleep(0.1)
                self.is_open = False
            self.serial.open()
            self.is_open = True
            # self.serial_alive = True
            # self._thread_run = True
        except serial.SerialException as e:
            # print("[LogLevel.ERR] open serial error!!! %s" % e)
            # self._easy_log(LogLevel.ERR, "open serial error!!! %s", e)
            raise
        else:
            self.serial_alive = True
            self._easy_log(LogLevel.INFO, "Serial port open: %s / %s",self.serial.port, self.serial.baudrate)
            self._recv()


    def _close_serial(self):
        self.serial.close()
        self.serial_alive = False
        self._thread_run = False
        self.is_open = False


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
                    self._easy_log(LogLevel.INFO, "Received message: %s", b)
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


    def send(self, msg: bytes):
        """send msg,
        msg: type of bytes or str"""
        with self._callback_mutex:
            self.serial.write(msg + b'\n')
            self._easy_log(LogLevel.INFO, "Sent message: %s", msg)


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
