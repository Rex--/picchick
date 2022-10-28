import functools
from argparse import ArgumentParser, Namespace
from abc import abstractmethod
import serial
import serial.tools.list_ports

# Simple programmer registry using decorators
registry = {}

def register_programmer(name):
    def decoratedRegister(programmer):
        registry[name] = programmer
        return programmer
    return decoratedRegister

# Helper functions to deal with ascii and binary
def ASCII(string):
    return string.encode(encoding='ascii')

def INTBYTES(number, len=2):
    return number.to_bytes(len, 'big')

def ROWBYTES(row):
    word_bytes = bytearray()
    for word in row:
        word_bytes += INTBYTES(word)
    return word_bytes

# General Helper functions
def wait_print(string):
    print(string, end=' ', flush=True)


class ProgrammerInterface:

    page_size = NotImplemented

    def __init__(self, args):
        pass

    @staticmethod
    def add_args(parser):
        '''Add additional command line arguments needed by programmer.'''
        pass

    @abstractmethod
    def connect(self):
        # Connect to the programmer. This may only open a serial port, it might
        # also send commands and evaluate the response.
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        ''' Disconnect from device and programmer(if applicable). '''
        raise NotImplementedError

    @abstractmethod
    def write(self, address: int, data: bytes):
        ''' Write data to address.'''
        raise NotImplementedError

    @abstractmethod
    def read(self, address: int, length: int) -> bytes:
        '''Read the given length from address.'''
        raise NotImplementedError

    @abstractmethod
    def erase(self, address):
        '''Erase address.'''
        raise NotImplementedError

class SerialProgrammer(ProgrammerInterface):
    def __init__(self, args, timeout=2):
        self._conn = serial.Serial(timeout=timeout)
        self._port = self._conn.port = args.port
        self._baud = self._conn.baudrate = args.baud

    @staticmethod
    def add_args(parser):
        parser.add_argument('-P', '--port',
            metavar='port',
            help='programmer serial port')
        parser.add_argument('-B', '--baud',
            type=int,
            default=9600,
            metavar='baud',
            help='serial connection baudrate',)


# Utlity functions
def listPorts():
    ports = serial.tools.list_ports.comports()
    print(f"{ len(ports) } serial devices found:")
    for port in ports:
        print(f"{ port.device }\t{ port.product }")
