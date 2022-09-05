import functools
import serial
import serial.tools.list_ports

# Simple programmer registry using decorators
registry = {}

def PicchickProgrammer(name):
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
    def __init__(self, port, baud=9600, timeout=2):
        self._conn = serial.Serial(timeout=timeout)
        self._port = self._conn.port = port
        self._baud = self._conn.baudrate = baud

    def connect(self):
        # Connect to the programmer. This may only open a serial port, it might
        # also send commands and evaluate the response.
        raise NotImplementedError

    def disconnect(self):
        # Disconnect from programmer.
        raise NotImplementedError

    def start(self):
        # Start programming the device. This should verify that there is indeed
        # a device attached to the programmer and prepare it for programming.
        raise NotImplementedError

    def stop(self):
        # Leave programming mode.
        raise NotImplementedError

    def word(self, address, word):
        # Write a single word to the device. This is mostly used for
        # configuration words and EEPROM.
        raise NotImplementedError
    
    def row(self, address, row):
        # Write a row (64 words) to the device. This is used to reprogram the
        # device's flash.
        raise NotImplementedError

    def read(self, address):
        # Read a single word from the device. This should be able to read the
        # entire flash memory of the device.
        raise NotImplementedError

    def erase(self, address):
        # Erase a particular address. Some addresses are reserved for special
        # cases.
        raise NotImplementedError
    
    def verify(self, memory):
        # Verify's the connected device against the given memory. If all of the
        # memory addresses are the same, it should return True, False otherwise.
        # Memory is a dict of address: word
        raise NotImplementedError
    
    def reset(self):
        # Reset device. This will occur after any other operations specified.
        raise NotImplementedError


# Utlity functions
def listPorts():
    ports = serial.tools.list_ports.comports()
    print(f"{ len(ports) } serial devices found:")
    for port in ports:
        print(f"{ port.device }\t{ port.product }")
