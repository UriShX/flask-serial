import flask

from dataclasses import dataclass

from .loglevel import LogLevel
from ._serial import _Serial


@dataclass
class PortSettings:
    _name: str
    _timeout: float
    _baudRate: int
    _byteSize: int
    _parity: str
    _stopBits: int


    @property
    def name(self) -> str:
        return self._name


    @name.setter
    def name(self, name_: str) -> None:
        self._name = name_


    SERIAL_PORT     = "SERIAL_PORT"
    SERIAL_TIMEOUT  = "SERIAL_TIMEOUT"
    SERIAL_BAUDRATE = "SERIAL_BAUDRATE"
    SERIAL_BYTESIZE = "SERIAL_BYTESIZE"
    SERIAL_PARITY   = "SERIAL_PARITY"
    SERIAL_STOPBITS = "SERIAL_STOPBITS"



class Serial:
    def __init__(self, app: flask.Flask):
        self.ser = _Serial()
        if app is not None:
            self.init_app(app)


    def init_app(self, app: flask.Flask):
        self.ser.serial.timeout  = app.config.get("SERIAL_TIMEOUT",  0.1)
        self.ser.serial.baudrate = app.config.get("SERIAL_BAUDRATE", 9600)
        self.ser.serial.bytesize = app.config.get("SERIAL_BYTESIZE", 8)
        self.ser.serial.parity   = app.config.get("SERIAL_PARITY",  "N")
        self.ser.serial.stopbits = app.config.get("SERIAL_STOPBITS", 1)
        self.ser.serial.port     = app.config.get("SERIAL_PORT")
        if self.ser.serial.port is None:
            raise IOError("Serial port name is not configured!")

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


    def send(self, msg: bytes):
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
