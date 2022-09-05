import copy
import textwrap
from . import devices


def loadHexfile(path, device):
    with open(path) as hexfile:    
        if device.family == 'pic':
            hexobj = MCHIPHXDecoder.decode(hexfile, device)
        else:
            hexobj = INHX32Decoder.decode(hexfile)

    return hexobj


class Hexfile:
    records = [] # These contain the whole hexfile in various formats
    memory = {}

    flash = {}  # These are portions of the hexfile
    config = {}
    data = {}

    data_width = 1    # By default all data is 1 byte wide

    def chunkFlash(self, chunksize=64, padding=0x3FFF):
        rows = {}

        for word_address in sorted(self.flash):
            row_start_address = word_address - (word_address % chunksize)
            row_address_offset = word_address - row_start_address
            
            if row_start_address not in rows:
                if padding is not None:
                    rows[row_start_address] = [padding for _ in range(chunksize)]
                else:
                    rows[row_start_address] = []
            
            rows[row_start_address][row_address_offset] = self.flash[word_address]
        
        return rows
    
    def __repr__(self):
        hexfile_str = '  ADDR |'
        
        # Address labels across the top
        for num in range(16):
            hexfile_str += (' ' * ((self.data_width*2)-1))
            hexfile_str += ('x%.1X ' % num)
        hexfile_str += '\n-------+' + ('-' * ((4+((self.data_width-1)*2))*16)) + '\n'

        # Flash data
        for address, row in self.chunkFlash(chunksize=16, padding=' '*(self.data_width*8//4)).items():

            # Address label on side
            if address > 0xFFFFF:
                hexfile_str += f"{(('x%X|') % address):>8}"
            # elif address > 0xFFFF:
            #     hexfile_str += (('x%X |') % address)
            else:
                hexfile_str += f"{(('x%X |') % address):>8}"

            # Table data
            for data in row:
                if type(data) == int:
                    hexfile_str += (' x%.' + str(self.data_width*2) + 'X') % data
                else:
                    hexfile_str += ('  ' + data)
            hexfile_str += '\n'
        
        # Configuration data
        for address, data in self.config.items():
            hexfile_str += ((' x%.4X = x%.'+str(self.data_width*2)+'X\n') % (address, data))
        
        if len(self.data) > 0:
            eeprom_str = ''
            for address, data in self.data.items():
                eeprom_str += ' %X' % data

            hexfile_str += textwrap.fill(eeprom_str, 100)
        
        # Remove trailing newline and whitespace
        return hexfile_str.rstrip()

class INHX32Decoder:

    # Decodes a hexfile according to the Intel Hex 32-bit specification
    @staticmethod
    def decode(file):
        # Load up a Intel hexfile into its individual records.
        loaded_hex = Hexfile()
        ascii_records = INHX32Decoder.readFile(file)
        loaded_hex.records = INHX32Decoder.decodeAscii(ascii_records)

        # Default is to decode records into bytes
        loaded_hex.memory = INHX32Decoder.decodeBytes(loaded_hex.records)

        # And assume it's all flash
        loaded_hex.flash = loaded_hex.memory

        return loaded_hex

    # Read hexfile in and output a list of records
    # A record is an intel hex 'command'
    # Each record is proceeded by an ascii ':'
    @staticmethod
    def readFile(file):
        # Read the entire hexfile into memory.
        hexfile_data = file.read()

        # Remove newlines and split records at the colons.
        hexfile_data = hexfile_data.replace('\n', '')
        hexfile_data = hexfile_data.lstrip(':').split(':')
        return hexfile_data

    # Decode the list of ascii records to a list of dicts containing record information
    # TODO: This would be a good place for checksum verification of hexfile records.
    @staticmethod
    def decodeAscii(ascii_records):
        decoded_records = []
        for record in ascii_records:
            data_len = int(record[0:2], base=16) # First ASCII hex byte is the data length
            offset_addr = int(record[2:6], base=16) # Next two ASCII hex bytes is the offset address
            record_type = int(record[6:8], base=16) # Next byte is the record type
            data = record[8:(data_len*2)+8] # The data is data_len*2 long since 2 ascii chars represent one hex byte
            checksum = int(record[-2:], base=16) # The Last byte in the record is the checksum
            decoded_records.append(dict(data_len=data_len, offset_addr=offset_addr, record_type=record_type, data=data, checksum=checksum))
        return decoded_records

    # Decodes a list of record objects to a dictionary containing <addr> : <byte>
    # NOTE: This is untested and currently unused.
    @staticmethod
    def decodeBytes(decoded_records):
        data_bytes = {}
        high_address = 0 # The high address defaults to 0x0000 unless a hex record sets it otherwise
        for record in decoded_records: 
            if record['offset_addr'] != 0:
                low_address = record['offset_addr']
            else:
                low_address = 0
            byte_start = 0

            if record['record_type'] == 4 and record['data_len'] == 2: # A record with type 4 sets the high address
                high_address = int(record['data'], base=16)
                high_address = (high_address << 16)

            elif record['record_type'] == 0: # A record with type 0 is a data record
                # Loop through our 'data' and extract the bytes while calculating a direct address
                while byte_start <= (record['data_len'] * 2) - 2:
                    # The complete address is a combination of a high and low byte
                    address = high_address + low_address

                    dbyte = int(record['data'][byte_start:byte_start+2], base=16)
                    data_bytes[address] = dbyte

                    # Skip to the next byte and increment the address
                    byte_start += 2
                    low_address += 1
        return data_bytes


class MCHIPHXDecoder:

    # Decodes a hexfile according to microchip's specification for PICs
    @staticmethod
    def decode(file, device):
        # First decode the intel hexfile according to the spec
        loaded_hex = Hexfile()
        loaded_hex.data_width = 2   # Words are 2-byte wide
        ascii_records = INHX32Decoder.readFile(file)
        loaded_hex.records = INHX32Decoder.decodeAscii(ascii_records)

        # Translate these records according to Microchip's PIC spec
        # A 14-bit word is represented by two bytes in little endian
        loaded_hex.memory = MCHIPHXDecoder.decodeWords(loaded_hex.records)
        for addr, word in loaded_hex.memory.items():
            if addr <= device.flash.end:
                loaded_hex.flash[addr] = word
            elif device.config.start <= addr <= device.config.end:
                loaded_hex.config[addr] = word
            elif device.user_id.start <= addr <= device.user_id.end:
                loaded_hex.config[addr] = word
            # TODO: EEPROM not implemented
            elif device.eeprom.start <= addr <= device.eeprom.end:
                loaded_hex.data[addr] = word
        
        # Chunk up flash into rows if writes require it
        # if device.flash.memtype == 'READWRITE_A' or device.flash.memtype == 'READWRITE_B':
        #     loaded_hex.flash = MCHIPHXDecoder.chunkWords(flash_words, device.blocksize)
        # else:
        #     loaded_hex.flash = flash_words
        
        return loaded_hex

    # Decodes a list of record objects to a dictionary containing [Address]: <Word>
    # Records MUST be in the order they were in the hexfile
    # Hex records supported so far are:
    # - DATA: 0x00
    # - Ext Linear Address: 0x04
    @staticmethod
    def decodeWords(decoded_records):
        words = {}
        high_address = 0 # The high address defaults to 0x0000 unless a hex record sets it otherwise
        for record in decoded_records:
            if record['offset_addr'] != 0:
                low_address = record['offset_addr'] // 2    # Address are 2x that of the pic memory in the hex file since it takes 2 bytes per word
            else:
                low_address = 0

            if record['record_type'] == 4 and record['data_len'] == 2: # A record with type 4 sets the high address
                high_address = int(record['data'], base=16)
                high_address = (high_address << 16) // 2    # Address are double in the hex file

            elif record['record_type'] == 0: # A record with type 0 is a data record that holds words
                word_start = 0
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

    # Separates a dict of {addr: word} into rows <chunksize> words long
    # Returns a dict of {start_addr: [row_data]} with row data
    # being a list of words padded with <padding>
    @staticmethod
    def chunkWords(words, chunksize=64, padding=0x3FFF):
        rows = {}

        for word_address in sorted(words):
            row_start_address = word_address - (word_address % chunksize)
            row_address_offset = word_address - row_start_address
            
            if row_start_address not in rows:
                if padding is not None:
                    rows[row_start_address] = [padding for _ in range(chunksize)]
                else:
                    rows[row_start_address] = []

            rows[row_start_address][row_address_offset] = words[word_address]
        
        return rows
