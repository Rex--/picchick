# This file contains the programmer interface for the piccstick programmer.
# It supports the low-voltage ICSP interface for PICs. Design files and firmware
# is available in the github repo: https://github.com/rex--/picstick

from .programmer import *

import time

# PICSTICK protocol commands and responses
PICSTICK_PING = ASCII('I')
PICSTICK_START_MSB = ASCII('S')
PICSTICK_START_LSB = ASCII('L')
PICSTICK_QUIT = ASCII('Q')
PICSTICK_COMMAND = ASCII('C')
PICSTICK_PAYLOAD = ASCII('P')
PICSTICK_READ = ASCII('R')
# 6-bit commands
PICSTICK_SHORT_COMMAND = ASCII('c')
PICSTICK_SHORT_PAYLOAD = ASCII('p')
PICSTICK_SHORT_READ = ASCII('r')

RESP_PONG = ASCII('O')
RESP_OK = ASCII('K')
RESP_ERROR = ASCII('E')
RESP_UNKNOWN = ASCII('?')

# 8-bit ICSP commands
ICSP_ADDR_LOAD =    b'\x80'
ICSP_ADDR_INC =     b'\xF8'
ICSP_ERASE_BULK =   b'\x18'
ICSP_ERASE_SECT =   b'\xF0'
ICSP_READ =         b'\xFC'
ICSP_READ_INC =     b'\xFE'
# PIC14EX
ICSP_LOAD =         b'\x00'
ICSP_LOAD_INC =     b'\x02'
ICSP_BEGIN_INT =    b'\xE0'
ICSP_BEGIN_EXT =    b'\xC0'
ICSP_END_EXT =      b'\x82'
# PIC18
ICSP_WRITE_INC =    b'\xE0'
ICSP_WRITE =        b'\xC0'

# 6-bit ICSP commands
ICSP_S_ADDR_INC =   b'\x06'
ICSP_S_ADDR_RESET = b'\x16'
ICSP_S_ERASE_BULK = b'\x09'
ICSP_S_ERASE_ROW =  b'\x11'
ICSP_S_READ_DATA =  b'\x04'
ICSP_S_LOAD_CFG =   b'\x00'
ICSP_S_LOAD_DATA =  b'\x02'
ICSP_S_BEGIN_INT =  b'\x08'
ICSP_S_BEGIN_EXT =  b'\x18'
ICSP_S_END_EXT =    b'\x0A'


def ADDR_BYTES(addr):
    len=2
    if addr > 65535:
        len = 3
    return len.to_bytes(1, 'big') + addr.to_bytes(len, 'big')

def PAYLOAD_NUMBER(num):
    return num.to_bytes(3, 'big')

@register_programmer('picstick')
class PicstickProgrammer(SerialProgrammer):

    def __init__(self, args, mcu=None):
        super().__init__(args, mcu)
        self._baud = self._conn.baudrate = args.baud
        self.page_size = 128
        self.use_bulk_erase = args.bulk_erase
        self._14e_address = 0xffffffffffffff
    
    @staticmethod
    def add_args(parser):
        parser.add_argument('-P', '--port',
            metavar='port',
            help='programmer serial port')
        parser.add_argument('-B', '--baud',
            type=int,
            default=76800,
            metavar='baud',
            help='serial connection baudrate',)
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
            print(FAIL)
            self._conn.close()
            return False
        print(SUCCESS)

        wait_print('Entering programming mode...')
        self._conn.flushInput()
        if self._mcu.arch == 'PIC14E':
            self._conn.write(PICSTICK_START_LSB)
        elif self._mcu.arch == 'PIC14EX' or self._mcu.arch == 'PIC18':
            self._conn.write(PICSTICK_START_MSB)
        else:
            print(f"Unsupported architecture: {self._mcu.arch}")
            self.disconnect()
            return False
        if not self.__check_response():
            print(FAIL)
            self.disconnect()
            return False
        print(SUCCESS)
        return True
    
    def disconnect(self):
        wait_print('Leaving programming mode...')
        self._conn.flushInput()
        self._conn.write(PICSTICK_QUIT)
        if not self.__check_response():
            print(FAIL)
            self._conn.close()
            return False
        print(SUCCESS)
        self._conn.close()
        return True

    def write(self, address, data):
        wait_print(f"Writing {len(data)} bytes to {hex(address)}...")
        if self._mcu.arch == 'PIC14E':
            return self._write_14e(address, data)
        elif self._mcu.arch == 'PIC14EX':
            return self._write_14ex(address, data)
        elif self._mcu.arch == 'PIC18':
            return self._write_18(address, data)
        else:
            print(f"Unsupported architecture: {self._mcu.arch}")
            return False

    def _write_14e(self, address, data):
        # First we either reset the PC to 0 or 0x8000 based on address
        if address > 0x7fff:
            # Location 0x8000 and above need load config command to set PC to 0x8000
            self._conn.write(PICSTICK_SHORT_PAYLOAD + ICSP_S_LOAD_CFG + b'\x00' + data)
            if not self.__check_response():
                print(FAIL)
                return 0
            self._14e_address = 0x8000
            inc_count = address - 0x8000
        else:
            if address > self._14e_address:
                # Only increment needed amount
                inc_count = address - self._14e_address
            else:
                # Reset PC to 0
                self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_RESET)
                if not self.__check_response():
                    print(FAIL)
                    return 0
                self._14e_address = 0
                inc_count = address

        # Next we increment the PC to the address
        for i in range(inc_count):
            self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_INC)
            if not self.__check_response():
                print(FAIL)
                return 0
            self._14e_address += 1

        # Load data latches if writing flash
        if address < 0x8000:
            for i in range(0, len(data), 2):
                self._conn.write(PICSTICK_SHORT_PAYLOAD + ICSP_S_LOAD_DATA + b'\x00' + data[i:i+2]) # Load data into latches
                if not self.__check_response():
                    print(FAIL)
                    return 0
                if i+2 < len(data):
                    self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_INC) # Increment address
                    if not self.__check_response():
                        print(FAIL)
                        return 0
                    self._14e_address += 1
        
        # Send begin programming command
        self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_BEGIN_INT)
        if not self.__check_response():
            print(FAIL)
            return 0

        print(SUCCESS)
        return len(data)

    def _write_14ex(self, address, data):
        # Set PC address
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print('failed to set PC')
            return False
        
        # Load data latches
        for i in range(0, len(data), 2):
                load_cmd = ICSP_LOAD
                if i+2 < len(data):
                    load_cmd = ICSP_LOAD_INC # If there is at least 2 bytes remaining, use the increment load command
                self._conn.write(PICSTICK_PAYLOAD + load_cmd + b'\x00' + data[i:i+2]) # Load data into latches
                if not self.__check_response():
                    print(FAIL)
                    return 0
        
        # Send write command
        self._conn.write(PICSTICK_COMMAND + ICSP_BEGIN_INT)
        if not self.__check_response():
            print(FAIL)
            return 0
        
        print(SUCCESS)
        return len(data)

        

    def _write_18(self, address, data):
        # Set PC address
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print('failed to set PC')
            return False

        # Write data to PC
        self._conn.write(PICSTICK_PAYLOAD + ICSP_WRITE + b'\x00' + bytes([data[1]]) + bytes([data[0]]))
        if not self.__check_response():
            print('failed to write data')
            return False

        print('success')
        return True

    def read(self, address, length):
        if self._mcu.arch == 'PIC14E':
            return self._read_14e(address, length)
        elif self._mcu.arch == 'PIC14EX':
            return self._read_14ex(address, length)
        elif self._mcu.arch == 'PIC18':
            return self._read_18(address, length)
        else:
            print(f"Unsupported architecture: {self._mcu.arch}")
            return {}

    def _read_14e(self, address, length):
        wait_print("Reading %i words from address: 0x%X..." % (length, address))
        read_resp = {}

        # First we either reset the PC to 0 or 0x8000 based on address
        if address > 0x7fff:
            # Location 0x8000 and above need load config command to set PC to 0x8000
            self._conn.write(PICSTICK_SHORT_PAYLOAD + ICSP_S_LOAD_CFG + PAYLOAD_NUMBER(0x3FFF))
            inc_count = address - 0x8000
        else:
            # Reset PC to 0
            self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_RESET)
            inc_count = address
        if not self.__check_response():
            print(FAIL)
            return {}

        # Next we increment the PC to the address
        for i in range(inc_count):
            self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_INC)
            if not self.__check_response():
                print(FAIL)
                return {}

        for word in range(length):
            self._conn.write(PICSTICK_SHORT_READ + ICSP_S_READ_DATA)
            resp = self._conn.read(size=3)
            resp_word = int.from_bytes(resp[1:3], 'big') >> 1
            resp_word = int('{:014b}'.format(resp_word)[::-1], 2) #reverse bit order
            read_resp[address] = resp_word & 0x3fff
            self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_INC)
            if not self.__check_response():
                print(FAIL)
                return {}
            address += 1

        print(SUCCESS)
        return read_resp

    def _read_14ex(self, address, length):
        wait_print("Reading %i words from address: 0x%.4X..." % (length, address))
        read_resp = {}
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print('failed')
            return {}
        for word in range(length):
            self._conn.write(PICSTICK_READ + ICSP_READ_INC)
            resp = self._conn.read(size=3)
            resp_word = int.from_bytes(resp, 'big') >> 1
            read_resp[address] = resp_word
            address += 1
        print('success')
        return read_resp

    def _read_18(self, address, length):
        wait_print("Reading %i words from address: 0x%X..." % (length, address))
        read_resp = {}
        self._conn.write(PICSTICK_PAYLOAD + ICSP_ADDR_LOAD + PAYLOAD_NUMBER(address))
        if not self.__check_response():
            print(FAIL)
            return {}
        for word in range(length):
            # print(bytes(PICSTICK_READ + ICSP_READ_INC))
            self._conn.write(PICSTICK_READ + ICSP_READ)
            resp = self._conn.read(size=3)
            resp_word = int.from_bytes(resp, 'big') >> 1
            read_resp[address+1] = resp_word >> 8
            read_resp[address] = resp_word & 0xFF
            self._conn.write(PICSTICK_COMMAND + ICSP_ADDR_INC)
            if not self.__check_response():
                print(FAIL)
                return {}
            address +=2

        print(SUCCESS)
        return read_resp
    
    def erase(self, address):
        if self._mcu.arch == 'PIC14E':
            return self._erase_14e(address)
        elif self._mcu.arch == 'PIC14EX':
            return self._erase_18(address)
        elif self._mcu.arch == 'PIC18':
            return self._erase_18(address)
        else:
            print(f"Unsupported architecture: {self._mcu.arch}")
            return False

    def _erase_14e(self, address):
        erase_command = ICSP_S_ERASE_ROW
        if self.use_bulk_erase:
            wait_print("Bulk erasing device with address: 0x%X" % address)
            erase_command = ICSP_S_ERASE_BULK
        else:
            wait_print("Erasing section with address: 0x%X..." % (address))

        # First we either reset the PC to 0 or 0x8000 based on address
        if address > 0x7fff:
            # Location 0x8000 and above need load config command to set PC to 0x8000
            self._conn.write(PICSTICK_SHORT_PAYLOAD + ICSP_S_LOAD_CFG + b'\x00' + data)
            inc_count = address - 0x8000
        else:
            # Reset PC to 0
            self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_RESET)
            inc_count = address
        if not self.__check_response():
            print(FAIL)
            return False

        # Next we increment the PC to the address
        for i in range(inc_count):
            self._conn.write(PICSTICK_SHORT_COMMAND + ICSP_S_ADDR_INC)
            if not self.__check_response():
                print(FAIL)
                return False
        
        # Send erase command
        self._conn.write(PICSTICK_SHORT_COMMAND + erase_command)
        if not self.__check_response():
            print(FAIL)
            return False

        print(SUCCESS)
        return True

    def _erase_18(self, address):
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

    def __check_response(self, expected_resp=RESP_OK):
        resp = self._conn.read()
        # print(resp)
        if resp == expected_resp:
            return True
        else:
            if resp == RESP_UNKNOWN:
                print('picchick: error: picstick: unknown command: ' + str(resp))
            else:
                print('picchick: error: picstick: unknown response: ' + str(resp))
            return False
