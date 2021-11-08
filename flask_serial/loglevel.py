from enum import IntEnum, unique


@unique
class LogLevel(IntEnum):
    INFO = 0
    NOTICE = 1
    WARNING = 2
    ERR = 3
    DEBUG = 4
