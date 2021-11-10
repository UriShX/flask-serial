import sys
import serial
from serial.threaded import ReaderThread, LineReader
import time
import typing

# from watchedserial import WatchedReaderThread

# ser = serial.Serial()
# ser = serial.serial_for_url('COM5', baudrate=9600, timeout=1)
ser: serial.Serial = serial.serial_for_url('COM5')
ser.timeout = 0.1
ser.baudrate = 9600
ser.bytesize = 8
ser.parity = 'N'
ser.stopbits = 1

class PrintLines(LineReader):
# class PrintLines(FramedPacket):
    # TERMINATOR = b'\r\n'
    # ENCODING = 'utf-8'
    # UNICODE_HANDLING = 'replace'

    def connection_made(self, transport):
        super(PrintLines, self).connection_made(transport)
        sys.stdout.write('port opened\n')
        # self.write_line('hello world')

    def handle_line(self, data):
        sys.stdout.write('line received: {!r}\n'.format(data))

    # def handle_packet(self, packet: bytes):
    #     print(packet.decode(self.ENCODING, self.UNICODE_HANDLING))

    def connection_lost(self, exc):
        if exc:
            print(exc)
        sys.stdout.write('port closed\n')

# with ReaderThread(ser, PrintLines) as protocol:
#     # protocol.write_line('hello')
#     while True:
#         time.sleep(0.1)

t = ReaderThread(ser, PrintLines)
t.start()
transport, protocol = t.connect()
# protocol.write_line('hello')
while True:
    time.sleep(0.1)
t.close()
