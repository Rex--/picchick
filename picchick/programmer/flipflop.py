# This file contains the programming interface for the flipflop bootloader.
# Flipflop is a serial based loader for PICs, so a USB-to-UART or similar is
# needed to communicate with it. Currently only 1-wire UART mode is supported.
# Github Repo: https://github.com/rex--/flipflop

from .programmer import *


# PreDefined Characters and Commands
OK = b'K'
GREETING = b'U'
START_APP = b'X'
RESET = b'U'
ROW = b'P'
WORD = b'C'
READ = b'R'
ERASE = b'D'


@PicchickProgrammer('flipflop')
class FlipflopProgrammer(ProgrammerInterface):

    def __init__(self, *args, timeout=0.5, **kwargs):
        super().__init__(*args, timeout=timeout, **kwargs)
        self._reset = False

    def connect(self):
        try:
            self._conn.open()
        except serial.SerialException:
            print(f"Failed to open serial port: { self._port }")
            return False
        wait_print(f"Connecting to device: { self._port } @ { self._baud }\nSending greeting...")
        self._conn.flushInput()
        self._conn.write(GREETING)
        self._conn.read(1)
        for timeout in range(20):
            self._conn.write(GREETING)
            self._conn.read(1)
            if self.__check_response(expected_resp=OK):
                print("connected to flipflop")
                return True

        print('device failed to respond')
        self.disconnect()
        return False

        # Disconnecting starts the user app by default. Override with --reset
    def disconnect(self):
        if not self._reset:
            print('Starting application...')
            self._conn.write(START_APP)
        wait_print('Disconnecting from flipflop...')
        self._conn.close()
        print('goodbye')
        return True

    def start(self):
        # print('Entering programming mode... success')
        return True
    
    def stop(self):
        # print ('Leaving programming mode... success')
        return True
    
    def word(self, address, word):
        # Flipflop currently doesn't support writing config words above 8009
        if (0x8009 < address < 0xF000):
            print("Error: Address out of flipflop's bounds: 0x%.4X"%address)
            return False
        wait_print("Writing Word: 0x%.4X | 0x%.4X..." % (address, word))
        self._conn.write(WORD + INTBYTES(address) + INTBYTES(word))
        self._conn.read(5)
        if self.__check_response() is not True:
            print('failed')
            return False
        print('success')
        return True
    
    def row(self, address, row):
        wait_print("Writing Row: 0x%.4X..." % (address))
        cmd = ROW + INTBYTES(address) + ROWBYTES(row)
        # print(cmd)
        self._conn.write(cmd)
        self._conn.read(131)
        if self.__check_response() is not True:
            print('failed')
            return False
        print('success', end='\r')
        return True

    def read(self, address):
        wait_print("Reading from address: 0x%.4X..." % (address))
        self._conn.write(READ + INTBYTES(address))
        self._conn.read(3)
        resp = self._conn.read(size=2)
        print('\r', end='')
        return resp
    
    def erase(self, address):
        wait_print("Erasing Row: 0x%.4X..." % (address))
        self._conn.write(ERASE + INTBYTES(address))
        self._conn.read(3)
        if self.__check_response() is not True:
            print('failed')
            return False
        print('success')
        return True
    
    def reset(self):
        print("Resetting device... ")
        self._conn.write(RESET)
        self._reset = True
        return True

    def __check_response(self, expected_resp=OK):
        resp = self._conn.read(1)
        # print(resp)
        if resp == expected_resp:
            return True
        else:
            return False
