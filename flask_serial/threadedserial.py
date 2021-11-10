import serial
from serial.threaded import ReaderThread, LineReader, FramedPacket
import time
import threading
# import multiprocessing
import collections
import flask

from typing import Callable
from dataclasses import dataclass



@dataclass
class PortSettings:
    port: str
    timeout: float
    baudrate: int
    bytesize: int
    parity: str
    stopbits: int


    def to_config_dict(self):
        return {
            "SERIAL_PORT"     : self.port,
            "SERIAL_TIMEOUT"  : self.timeout,
            "SERIAL_BAUDRATE" : self.baudrate,
            "SERIAL_BYTESIZE" : self.bytesize,
            "SERIAL_PARITY"   : self.parity,
            "SERIAL_STOPBITS" : self.stopbits,
        }


    @classmethod
    def from_config_dict(cls, config: dict):
        settings: PortSettings = cls(
            port     = config.get("SERIAL_PORT"),
            timeout  = config.get("SERIAL_TIMEOUT",  0.1),
            baudrate = config.get("SERIAL_BAUDRATE", 9600),
            bytesize = config.get("SERIAL_BYTESIZE", 8),
            parity   = config.get("SERIAL_PARITY",  "N"),
            stopbits = config.get("SERIAL_STOPBITS", 1),
        )
        if settings.port is None:
            raise IOError("Serial port name is not configured!")
        return settings



from .loglevel import LogLevel


class Reader(serial.threaded.LineReader):
    def __init__(self):
        super().__init__()
        self._on_message: Callable[[str], None] = None

    # def _on_message(self, str):
    #     pass

    def handle_line(self, data: str):
        self._on_message(data)
        # print("received message:", data)
        # (f'reply: {data[:-1]}')



class ThreadedSerial:
    def __init__(self, app: flask.Flask = None):
        self.serial: serial.Serial = None
        self.thread: ReaderThread = None
        self.reader: Reader = None
        if app is not None:
            self.init_app(app)

        self.__outgoing: collections.deque[bytes] = collections.deque()

        self.__run = False

        self.__on_message: Callable[[bytes], None] = None

        # self.__mutex = threading.Lock()


    def init_app(self, app: flask.Flask):
        settings = PortSettings.from_config_dict(app.config)

        self.serial = serial.serial_for_url(settings.port)
        self.serial.timeout  = settings.timeout
        self.serial.baudrate = settings.baudrate
        self.serial.bytesize = settings.bytesize
        self.serial.parity   = settings.parity
        self.serial.stopbits = settings.stopbits


    def open(self):
        self.thread = ReaderThread(self.serial, Reader)
        self.thread.start()
        _, self.reader = self.thread.connect()
        self.reader._on_message = self.__on_message
        # self.__read_thread = threading.Thread(target=self.__read_worker, daemon=True)
        # self.__write_thread = threading.Thread(target=self.__write_worker, daemon=True)

        # self.__run = True
        # self.__read_thread.start()
        # self.__write_thread.start()

        # TODO: Valutare l'utilità di questo ciclo
        # counter = 0
        # while counter < 4:
        #     try:
        #         self.serial.open()
        #     except serial.SerialException as e:
        #         counter += 1
        #     else:
        #         self.run = True
        #         self._read_worker = threading.Thread(target=self.__read_worker, daemon=True)
        #         self._write_worker = threading.Thread(target=self.__write_worker, daemon=True)
        #         break


    # def close(self):
    #     self.__run = False

    #     self.serial.close()


    def __read_worker(self):
        while self.__run:
            if self.serial.is_open:
                print(f'in_waiting: {self.serial.in_waiting}')
                print('reading')
                # with self.__mutex:
                msg = self.serial.read(512) # TODO: Irrobustire
                print('read', end=' ')
                print(msg)
                self.__on_message_received(msg)
                time.sleep(0.01)


    def write(self, msg: bytes):
        # print(f'appended: {msg} - in Q: {len(self.__outgoing)}')
        # self.__outgoing.appendleft(msg)
        self.thread.write(msg)


    def __write_worker(self):
        while self.__run:
            if self.serial.is_open and len(self.__outgoing) > 0:
                print('writing')
                msg = self.__outgoing.pop()
                print(msg)
                # with self.__mutex:
                self.serial.write(msg)
                print(f'sent: {msg} - in Q: {len(self.__outgoing)}')
                time.sleep(0.01)


    def on_message(self, callback: Callable[[str], None]):
        """Decorate a function with on_message to run it when a new message is received
        use：
            @serial.on_message
            def handle_message(msg):
                print("serial receive message：", msg)
        """
        print('on_message')
        print(callback)
        self.__on_message = callback
        # def decorator(callback: Callable[[str], None]):
        #     # type: (Callable) -> Callable
        #     self.reader._on_message = callback
        #     return callback

        return callback



class ThreadedSerial_:
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
                    self.on_message(b)
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
