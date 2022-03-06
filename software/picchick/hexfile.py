
import copy

from . import devices

# PFM_START = 0x0000
# USER_ID_START = 0x8000
# CONFIG_WORD_START = 0x8007


class HexfileDecoder:

    def __init__(self, path, device):
        self.path = path

        self.device = devices.Device(device)
        self.device.readDeviceFile(devices.XC8Manager.findXC8Installs()[0])

        self.ascii_records = self._readHexfile(path)
        self.records = self._decodeAsciiRecords(self.ascii_records)
        self.word_list = self._decodeWordsFromRecords(self.records)

        self.userflash_words = [addr for addr in self.word_list.keys() if addr <= self.device.flash.end]
        self.config_words = [addr for addr in self.word_list.keys() if addr > self.device.flash.end]
        
        self.memory = self._separateRows(self.word_list)

    
    def getMemory(self):
        return self.memory

    def printMemory(self):
        print('\n PFM   :   x0     x1     x2     x3     x4     x5     x6     x7     x8     x9     xA     xB     xC     xD     xE     xF')
        print('-------:-----------------------------------------------------------------------------------------------------------------')
        for word_address in self.userflash_words:
            if word_address % 16 == 0 or word_address == 0:
                if word_address % 64 == 0:
                    if word_address == 0:
                        print('0x%.4X + ' % word_address, end='')
                    else:
                        print('\n0x%.4X + ' % word_address, end='')
                else:
                    print('\n0x%.4X | ' % word_address, end='')
            print('0x%.4X ' % self.word_list[word_address], end='')

        print('\n       :\nCONFIG :\n-------:--------')
        for word_address in self.config_words:
            print ('0x%.4X | 0x%.4X' % (word_address, self.word_list[word_address]))
        print('')

    # Read hexfile in and output a list of records
    # A record is an intel hex 'command'
    # Each record is proceeded by an ascii ':'
    def _readHexfile(self, path_to_hexfile):
        # Read the entire hexfile (Shouldn't be more than 56k * 2)
        with open(path_to_hexfile) as hexfile:
            hexfile_data = hexfile.read()

        hexfile_data = hexfile_data.replace('\n', '') # Remove newlines
        hexfile_data = hexfile_data.lstrip(':').split(':') # Split the file at the record marks ':' to get a list of records
        return hexfile_data

    # Decode the list of ascii records to a list of dicts containing record information
    def _decodeAsciiRecords(self, ascii_records):
        decoded_records = []
        for record in ascii_records:
            data_len = int(record[0:2], base=16) # First ASCII hex byte is the data length
            offset_addr = int(record[2:6], base=16) # Next two ASCII hex bytes is the offset address
            record_type = int(record[6:8], base=16) # Next byte is the record type
            data = record[8:(data_len*2)+8] # The data is data_len*2 long since 2 ascii chars represent one hex byte
            checksum = int(record[-2:], base=16) # The Last byte in the record is the checksum
            decoded_records.append(dict(data_len=data_len, offset_addr=offset_addr, record_type=record_type, data=data, checksum=checksum))
        return decoded_records

    # Decodes a list of record objects to a dictionary containg [Address]: <Word>
    # Records MUST be in the order they were in the hexfile
    # Hex records supported so far are:
    # - DATA: 0x00
    # - Ext Linear Address: 0x04
    def _decodeWordsFromRecords(self, decoded_records):
        words = {}
        high_address = 0 # The high address defaults to 0x0000 unless a hex record sets it otherwise
        for record in decoded_records: 
            if record['offset_addr'] != 0:
                low_address = record['offset_addr'] // 2    # Address are 2x that of the pic memory in the hex file since it takes 2 bytes per word
            else:
                low_address = 0
            word_start = 0

            if record['record_type'] == 4 and record['data_len'] == 2: # A record with type 4 sets the high address
                high_address = int(record['data'], base=16)
                high_address = (high_address << 16) // 2    # Address are double in the hex file

            elif record['record_type'] == 0: # A record with type 0 is a data record that holds words
                # Loop through our 'data' and extract the words while calculating a direct address
                while word_start <= (record['data_len'] * 2) - 4:
                    # The complete address is a combination of 2 high bytes and 2 low bytes which represent a 15-bit address
                    address = high_address + low_address
                    # The ascii hex representation of a word is MSB second, LSB byte first. So we swap those around and convert it to a number
                    word = int(record['data'][word_start+2:word_start+4] + record['data'][word_start:word_start+2], base=16)
                    words[address] = word

                    # Skip to the next word and increment the address
                    word_start += 4
                    low_address += 1

        return words

    # Separates a dict of {addr: word} into rows 64 words long
    # Returns a dict of {start_addr: [row_data]} with row data
    # being a list of words paded with 0x3FFF
    def _separateRows(self, words):
        rows = {}

        for word_address in self.userflash_words:
            
            row_start_address = word_address - (word_address % 64)
            row_address_offset = word_address - row_start_address
            
            if row_start_address not in rows:
                rows[row_start_address] = [0x3FFF for _ in range(64)]
            
            rows[row_start_address][row_address_offset] = words[word_address]
        
        for word_address in self.config_words:
            rows[word_address] = [words[word_address]]
        
        return rows
