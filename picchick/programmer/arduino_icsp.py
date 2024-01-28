# This file contains the interface for the arduino-icsp programmer.
# arduino-icsp is a simple sketch similiar to arduino-isp, but for PIC micros.
# This allows programming PICs that support LVP.

import time
from .programmer import *

@register_programmer('arduino-icsp')
class ArduinoICSPProgrammer(SerialProgrammer):


    def __init__(self, args):
        super().__init__(args)
        self._conn.timeout = 5 # Increase timeout
        # Max number of bytes we can write at once
        self.page_size = 128 # Very important! - required


    def connect(self):
        try:
            self._conn.open()
        except:
            print(f"Failed to open serial port: { self._port }")
            return False

        wait_print(f"Connecting to programmer: { self._port } @ { self._baud }\nEntering Programming mode...")
        time.sleep(2) # Wait for arduino to reset
        self._conn.write(b's')
        resp = self._conn.read()
        if resp != b'K':
            print('failed. Disconnecting.')
            return False
        print('success')
        return True

    def disconnect(self):
        wait_print('Exiting programming mode...')
        self._conn.write(b'x')
        self._conn.flush()
        self._conn.close()
        print('goodbye :)')
        return True
    
    def read(self, address, length):
        wait_print("Reading %i words from address: 0x%.4X..." % (length, address))
        self._conn.write(b'r') # Read command
        self._conn.write(INTBYTES(address)) # start address
        self._conn.write(INTBYTES(length)) # num of words
        resp = self._conn.read(length*2) # receive words*2 bytes
        if len(resp) != length*2:
            print('failed: ' + str(len(resp)))
            return None
        print('success')
        return resp

    def write(self, address, data):
        wait_print(f"Writing {len(data)//2} words to {hex(address)}...")
        if len(data) > 128:
            print('failed\nERROR: Max data size exceeded (128 bytes)')
            return False
        elif (len(data) % 2) == 1:
            print('failed.\nERROR: uneven data size: %i' % len(data))
            return False

        self._conn.write(b'w') # Write command
        self._conn.write(INTBYTES(address)) # Start address
        self._conn.write(INTBYTES(len(data)//2)) # Num words
        self._conn.write(data) # data
        resp = self._conn.read()
        if resp != b'K':
            print('failed: ' + str(resp))
            return False
        print('success')
        return True

    def erase(self, address):
        wait_print("Erasing Row: 0x%.4X..." % (address))
        self._conn.write(b'e') # Erase row command
        self._conn.write(INTBYTES(address))
        if self._conn.read() != b'K':
            print('failed: ' + str(resp))
            return False
        print('success')
        return True

    
