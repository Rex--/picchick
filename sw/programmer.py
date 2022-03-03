
import serial
import serial.tools.list_ports


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


# General Helper functions
def wait_print(string):
    print(string, end=' ', flush=True)



class Programmer:

    def __init__(self, port, baud=9600, timeout=30):
        self._conn = serial.Serial(timeout=timeout)
        self._port = self._conn.port = port
        self._baud = self._conn.baud = baud
    
    def connect(self):
        try:
            self._conn.open()
        except serial.SerialException:
            print(f"Failed to open serial port: { self._port }")
            return False
        wait_print(f"Connecting to device: { self._port }\nSending greeting...")
        self._conn.flushInput()
        self._conn.write(GREETING + SEP)
        if self.__check_response(expected_resp=GREETING) is not True:
            print('device failed to respond')
            self.disconnect()
            return False
        print("connected to programmer")
        return True
    
    def disconnect(self):
        wait_print('Disconnecting from programmer...')
        self._conn.write(BYE + SEP)
        resp = self.__check_response(expected_resp=BYE)
        self._conn.close()
        if resp is not True:
            print('GOODBYE')
            return False
        print('goodbye')
        return True

    def start(self):
        wait_print('Entering programming mode...')
        self._conn.flushInput()
        self._conn.write(START + SEP)
        if self.__check_response() is not True:
            print('failed. Closing connection')
            self.disconnect()
            return False
        print('success')
        return True
    
    def stop(self):
        wait_print('Leaving programming mode...')
        # print(self._conn.read_all())
        self._conn.flushInput()
        self._conn.write(STOP + SEP)
        if self.__check_response() is not True:
            print('failed. Closing connection')
            self.disconnect()
            return False
        print ('success')
        return True
    
    def address(self, address):
        wait_print("Setting start address to: 0x%.4X..." % address)
        self._conn.write(ADDR + SEP + INTBYTES(address))
        if self.__check_response() is not True:
            print('failed. Closing connection')
            self.disconnect()
            return False
        print('success')
        return True
    
    def word(self, address, word):
        wait_print("Writing Word: 0x%.4X | 0x%.4X..." % (address, word))
        self._conn.write(WORD + SEP + INTBYTES(address) + SEP + INTBYTES(word))
        if self.__check_response() is not True:
            print('failed')
            return False
        print('success')
        return True
    
    def row(self, address, row):
        wait_print("Writing Row: 0x%.4X..." % (address))
        cmd = ROW + SEP + INTBYTES(address) + SEP + ROWBYTES(row)
        # print(cmd)
        self._conn.write(cmd)
        if self.__check_response() is not True:
            print('failed')
            return False
        print('success')
        return True

    def read(self, address):
        wait_print("Reading from address: 0x%.4X..." % (address))
        self._conn.write(READ + SEP + INTBYTES(address))
        if self.__check_response() is not True:
            print('failed')
            return False
        resp = self._conn.read(size=2)
        print('0x' + resp.hex().upper())
        return True
    
    def erase(self, address):
        wait_print("Erasing Row: 0x%.4X..." % (address))
        self._conn.write(ERASE + SEP + INTBYTES(address))
        if self.__check_response() is not True:
            print('failed')
            return False
        print('success')
        return True


    def __check_response(self, expected_resp=OK):
        resp = self._conn.read_until(expected=SEP)
        # print(resp)
        if resp.rstrip(SEP) == expected_resp:
            return True
        else:
            return resp


# Utlity functions
def listPorts():
    ports = serial.tools.list_ports.comports()
    print(f"{ len(ports) } serial devices found:")
    for port in ports:
        print(f"{ port.device }\t{ port.product }")
