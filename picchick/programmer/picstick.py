# This file contains the programmer interface for the piccstick programmer.
# It supports the low-voltage ICSP interface for PICs. Design files and firmware
# is available in the github repo: https://github.com/rex--/picstick

from .programmer import *

import time

# PreDefined Characters and Commands
SEP = ASCII(':')
OK = ASCII('OK')
GREETING = ASCII('HELLO')
BYE = ASCII('BYE')
START = ASCII('START')
STOP = ASCII('STOP')
ADDR = ASCII('ADDR')
ROW = ASCII('ROW')
WORD = ASCII('WORD')
READ = ASCII('READ')
ERASE = ASCII('ERASE')

# PICSTICK protocol commands and responses
PICSTICK_PING = ASCII('I')
PICSTICK_START = ASCII('S')
PICSTICK_QUIT = ASCII('Q')
PICSTICK_COMMAND = ASCII('C')
PICSTICK_PAYLOAD = ASCII('P')
PICSTICK_READ = ASCII('R')
PICSTICK_SHORT_COMMAND = ASCII('c')
PICSTICK_SHORT_PAYLOAD = ASCII('p')
PICSTICK_SHORT_READ = ASCII('r')

RESP_PONG = ASCII('O')
RESP_OK = ASCII('K')
RESP_ERROR = ASCII('E')
RESP_UNKNOWN = ASCII('?')

# ICSP commands and responses
ICSP_ADDR_LOAD =    b'\x80'
ICSP_ADDR_INC =     b'\xF8'
ICSP_ERASE_BULK =   b'\x18'
ICSP_ERASE_SECT =   b'\xF0'
ICSP_READ =         b'\xFC'
ICSP_READ_INC =     b'\xFE'
ICSP_WRITE =        b'\xC0'
ICSP_WRITE_INC =    b'\xE0'

def ADDR_BYTES(addr):
    len=2
    if addr > 65535:
        len = 3
    return len.to_bytes(1, 'big') + addr.to_bytes(len, 'big')

def PAYLOAD_NUMBER(num):
    return num.to_bytes(3, 'big')

@register_programmer('picstick')
class PicstickProgrammer(SerialProgrammer):

    def __init__(self, args):
        super().__init__(args)
        self.page_size = 128
        self.use_bulk_erase = args.bulk_erase
        self.chip_id = args.device
    
    @staticmethod
    def add_args(parser):
        SerialProgrammer.add_args(parser)
        parser.add_argument('--bulk-erase',
            action='store_true',
            help='use bulk erase when erasing device')

    def connect(self):
        try:
            self._conn.open()
        except serial.SerialException:
            print(f"Failed to open serial port: { self._port }")
            return False

        wait_print(f"Connecting to picstick: { self._port } @ { self._baud }bps...")
        self._conn.flushInput()
        self._conn.write(PICSTICK_PING)
        if not self.__check_response(expected_resp=RESP_PONG):
            print('device failed to respond')
            self._conn.close()
            return False
        print("connected to programmer")

        wait_print('Entering programming mode...')
        self._conn.flushInput()
        self._conn.write(b'L')
        if not self.__check_response():
            print('failed. Closing connection')
            self.disconnect()
            return False
        print('success')
        return True
    
    def disconnect(self):
        wait_print('Leaving programming mode...')
        self._conn.flushInput()
        self._conn.write(PICSTICK_QUIT)
        if not self.__check_response():
            print('failed')
            self._conn.close()
            return False
        print('success')
        self._conn.close()
        return True

    def write(self, address, data):
        wait_print(f"Writing 0x{data.hex()} to {hex(address)}...")
        return self.write_14e(address, data)

    def write_18(self, address, data):
        # if len(data) == 2:
        #     # Write a single word
        #     cmd = WORD + SEP + ADDR_BYTES(address) + len(data).to_bytes(1, 'big') + data
        #     print("WORD:" + cmd[5:].hex())
        # elif len(data) == self.page_size:
        #     # Write a whole row
        #     cmd = ROW + SEP + INTBYTES(address) + SEP + data
        #     print("ROW:" + cmd[4:].hex())
        # else:
        #     # We should pad it or chunk to size.
        #     # Return an error until thats implemented.
        #     print(f'failed\nIncompatible data size: {len(data)}')
        #     return False
        # self._conn.write(cmd)

        # Set PC address
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print('failed to set PC')
            return False

        # Write data to PC
        self._conn.write(PICSTICK_PAYLOAD + ICSP_WRITE + b'\x00' + data)
        if not self.__check_response():
            print('failed to write data')
            return False

        print('success')
        return True

    def write_14e(self, address, data):
        # First we either reset the PC to 0 or 0x8000 based on address
        if address > 0x7fff:
            # Location 0x8000 and above need load config command to set PC to 0x8000
            self._conn.write(PICSTICK_SHORT_PAYLOAD + b'\x00\x00' + data)
            inc_count = address - 0x8000
        else:
            # Reset PC to 0
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x16')
            inc_count = address
        if not self.__check_response():
            print('failed')
            return False

        # Next we increment the PC to the address
        for i in range(inc_count):
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x06')
            if not self.__check_response():
                print('failed')
                return False
        
        # Right now we're expecting data to only be a single word
        if address < 0x8000:
            self._conn.write(PICSTICK_SHORT_PAYLOAD + b'\x02\x00' + data)
            if not self.__check_response():
                print('failed')
                return False
        
        # Send begin programming command
        self._conn.write(PICSTICK_SHORT_COMMAND + b'\x08')
        if not self.__check_response():
            print('failed')
            return False

        print('success')
        return True

    def read(self, address, length):
        
        return self.read_14e(address, length)

    def read_18(self, address, length):
        wait_print("Reading %i words from address: 0x%X..." % (length, address))
        read_resp = {}
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print('failed')
            return {}
        for word in range(length):
            # print(bytes(PICSTICK_READ + ICSP_READ_INC))
            self._conn.write(PICSTICK_READ + ICSP_READ)
            resp = self._conn.read(size=3)
            resp_word = int.from_bytes(resp, 'big') >> 1
            read_resp[address] = resp_word >> 8
            read_resp[address+1] = resp_word & 0xFF
            self._conn.write(PICSTICK_COMMAND + ICSP_ADDR_INC)
            if not self.__check_response():
                print('failed')
                return {}
            address +=2

        print('success')
        return read_resp

    def read_14e(self, address, length):
        wait_print("Reading %i words from address: 0x%X..." % (length, address))
        read_resp = {}

        # First we either reset the PC to 0 or 0x8000 based on address
        if address > 0x7fff:
            # Location 0x8000 and above need load config command to set PC to 0x8000
            self._conn.write(PICSTICK_SHORT_PAYLOAD + b'\x00' +PAYLOAD_NUMBER(0x3FFF))
            inc_count = address - 0x8000
        else:
            # Reset PC to 0
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x16')
            inc_count = address
        if not self.__check_response():
            print('failed')
            return {}

        # Next we increment the PC to the address
        for i in range(inc_count):
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x06')
            if not self.__check_response():
                print('failed')
                return {}

        for word in range(length):
            self._conn.write(PICSTICK_SHORT_READ + b'\x04')
            resp = self._conn.read(size=3)
            resp_word = int.from_bytes(resp[1:3], 'big') >> 1
            resp_word = int('{:014b}'.format(resp_word)[::-1], 2) #reverse bit order
            read_resp[address] = resp_word & 0x3fff
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x06')
            if not self.__check_response():
                print('failed')
                return {}
            address += 1

        print('success')
        return read_resp
    
    def erase(self, address):
        return self.erase_14e(address)

    def erase_18(self, address):
        erase_command = ICSP_ERASE_SECT
        if self.use_bulk_erase:
            wait_print("Bulk erasing device with address: 0x%X" % address)
            erase_command = ICSP_ERASE_BULK
        else:
            wait_print("Erasing section with address: 0x%X..." % (address))

        # Set PC to address that we want to erase (or section)
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print('failed')
            return False
        
        # Send erase command
        self._conn.write(PICSTICK_COMMAND + erase_command)
        if not self.__check_response():
            print('failed')
            return False

        print('success')
        return True
    
    def erase_14e(self, address):
        erase_command = b'\x11'
        if self.use_bulk_erase:
            wait_print("Bulk erasing device with address: 0x%X" % address)
            erase_command = b'\x09'
        else:
            wait_print("Erasing section with address: 0x%X..." % (address))

        # First we either reset the PC to 0 or 0x8000 based on address
        if address > 0x7fff:
            # Location 0x8000 and above need load config command to set PC to 0x8000
            self._conn.write(PICSTICK_SHORT_PAYLOAD + b'\x00\x00' + data)
            inc_count = address - 0x8000
        else:
            # Reset PC to 0
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x16')
            inc_count = address
        if not self.__check_response():
            print('failed')
            return False

        # Next we increment the PC to the address
        for i in range(inc_count):
            self._conn.write(PICSTICK_SHORT_COMMAND + b'\x06')
            if not self.__check_response():
                print('failed')
                return False
        
        # Send erase command
        self._conn.write(PICSTICK_SHORT_COMMAND + erase_command)
        if not self.__check_response():
            print('failed')
            return False

        print('success')
        return True

    def __check_response(self, expected_resp=RESP_OK):
        resp = self._conn.read()
        # print(resp)
        if resp == expected_resp:
            return True
        else:
            if resp == RESP_UNKNOWN:
                print('Error: Unknown Command')
            else:
                print('Error: Unknown Response: ' + str(resp))
            return False
