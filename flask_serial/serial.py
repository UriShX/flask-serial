import flask

from dataclasses import dataclass

from .loglevel import LogLevel
from .threadedserial import ThreadedSerial



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



class Serial:
    def __init__(self, app: flask.Flask = None):
        self.ser = ThreadedSerial()
        if app is not None:
            self.init_app(app)


    def init_app(self, app: flask.Flask):
        # self.ser.serial.timeout  = app.config.get("SERIAL_TIMEOUT",  0.1)
        # self.ser.serial.baudrate = app.config.get("SERIAL_BAUDRATE", 9600)
        # self.ser.serial.bytesize = app.config.get("SERIAL_BYTESIZE", 8)
        # self.ser.serial.parity   = app.config.get("SERIAL_PARITY",  "N")
        # self.ser.serial.stopbits = app.config.get("SERIAL_STOPBITS", 1)
        # self.ser.serial.port     = app.config.get("SERIAL_PORT")
        # if self.ser.serial.port is None:
        #     raise IOError("Serial port name is not configured!")
        settings = PortSettings.from_config_dict(app.config)
        self.ser.serial.port     = settings.port
        self.ser.serial.timeout  = settings.timeout
        self.ser.serial.baudrate = settings.baudrate
        self.ser.serial.bytesize = settings.bytesize
        self.ser.serial.parity   = settings.parity
        self.ser.serial.stopbits = settings.stopbits

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
