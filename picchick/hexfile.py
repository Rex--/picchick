import copy
import textwrap
from . import devices


# # Decode records into memory mapped to our device
# loaded_hex.word_size = device.word_size
# loaded_hex.decode_words(
#     word_size=loaded_hex.word_size,
#     byte_order=device.byte_order
# )

# # Sort memory into flash and config(fuses)
# # TODO: This might would work well as a `sort()` method implemented by
# # the device object. That way each device subclass could sort data into
# # whatever sections they have.
# if (device.flash and device.config) is not None:
#     for addr, word in loaded_hex.memory.items():
#         if addr <= device.flash.end:
#             loaded_hex.flash[addr] = word
#         elif device.config.start <= addr <= device.config.end:
#             loaded_hex.config[addr] = word
# else:
#     # Assume it's all flash
#     loaded_hex.flash = loaded_hex.memory

# # Chunk flash into rows to get ready to write to device.
# loaded_hex.row_size = device.row_size
# loaded_hex.chunk_flash(chunksize=loaded_hex.row_size)

def loadHexfile(path):
    with open(path) as hexfile:
        hexobj = INHX32Decoder.decode(hexfile)

    return hexobj


class Hexfile:
    # These contain the whole hexfile in various formats
    records = []    # list of decoded records. Each record is a dict
    memory = {}     # dict of addr: word

    # These are portions of the hexfile
    flash = {}      # Flash words
    config = {}     # Configuration words/fuses
    eeprom = {}     # Maybe an eeprom section? (was data- terrible name)
    # Flash words partitioned into chunks(rows) and chunks of chunks(pages)
    rows = {}       # Words in the flash region chunked into rows.
    pages = {}      # Words in the flash region chunked into pages.

    # Information about the hexfile (This comes from a device obj but we store
    # it here when we decode stuff)
    byte_order = None   # Device.byte_order
    word_size = None    # Device.word_size
    row_size = None     # Device.row_size
    page_size = None    # Programmer.page_size

    
    def decode_words(self, word_size=1, byte_order='little', hex_byte_order='little'):
        words = {}
        high_address = 0
        for record in self.records:
            if record['offset_addr'] != 0:
                low_address = record['offset_addr'] // word_size
            else:
                low_address = 0

            if record['record_type'] == 4 and record['data_len'] == 2:
                high_address = int.from_bytes(record['data'], 'big')
                high_address = (high_address << 16) // word_size
            elif record['record_type'] == 0:
                word_start = 0
                while word_start < (record['data_len']):
                    address = high_address + low_address
                    word = int.from_bytes(record['data'][word_start:word_start+word_size], hex_byte_order)
                    words[address] = word
                    word_start += word_size
                    low_address += 1

        self.word_size = word_size
        self.byte_order = byte_order
        self.memory = words

    def sort_memory(self, device):
        if (device.flash and device.config) is not None:
            for addr, word in self.memory.items():
                if addr <= device.flash.end:
                    self.flash[addr] = word
                elif device.config.start <= addr <= device.config.end:
                    self.config[addr] = word
        else:
            # Assume it's all flash
            self.flash = self.memory

    def chunk_flash(self, chunksize=64, padding=0, trim=False):
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
        
        for addr, row in rows.items():
            if trim:
                # Trim trailing padding if option is specified
                while (row[-1] == padding):
                    row.pop()
            # Convert list of ints to bytes
            row_bytes = bytearray()
            for word in row:
                row_bytes.extend(word.to_bytes(self.word_size, self.byte_order))
            rows[addr] = bytes(row_bytes)
        
        self.row_size = chunksize
        self.rows = rows
    
    def page_rows(self, page_size=1):
        '''Chunk rows into page sized blocks.'''
        pages = {}
        start_addr = sorted(self.rows)[0]

        for row_addr in sorted(self.rows):
            if (start_addr in pages) and (len(pages[start_addr])+len(self.rows[row_addr]) > page_size) \
                    or (row_addr-self.row_size not in self.rows):
                start_addr = row_addr
            if (start_addr not in pages):
                pages[start_addr] = bytearray()
            pages[start_addr].extend(self.rows[row_addr])
        
        # Convert to immutable bytes and store in pages
        self.pages = {}
        for addr, page in pages.items():
            self.pages[addr] = bytes(page)
    
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
        # hexfile_str += ' ' * self.word_size
        # hexfile_str += 'x0'
        for num in range(16):
            hexfile_str += (' ' * ((self.word_size*2)-2))
            if (num == 0) and ((self.word_size*2)-2 == 0):
                hexfile_str += ' '
            hexfile_str += ('x%.1X ' % num)
        hexfile_str += '\n-------+' + ('-' * ((3+((self.word_size-1)*2))*16)) + '\n'

        # Flash data
        for address, row in self.chunkFlash(chunksize=16, padding=' '*(self.word_size*2)).items():

            # Address label on side
            if address > 0xFFFFF:
                hexfile_str += f"{(('x%X|') % address):>8}"
            else:
                hexfile_str += f"{(('x%X |') % address):>8}"

            # Table data
            for data in row:
                if type(data) == int:
                    hexfile_str += (' %.' + str(self.word_size*2) + 'X') % data
                else:
                    hexfile_str += ' ' + data
            hexfile_str += '\n'
        
        # Configuration data
        for address, data in self.config.items():
            hexfile_str += ((' x%.4X = %.'+str(self.word_size*2)+'X\n') % (address, data))
        
        # if len(self.data) > 0:
        #     eeprom_str = ''
        #     for address, data in self.data.items():
        #         eeprom_str += ' %X' % data

        #     hexfile_str += textwrap.fill(eeprom_str, 100)
        
        # Remove trailing newline and whitespace
        return hexfile_str.rstrip()

class INHX32Decoder:

    # Decodes a hexfile according to the Intel Hex 32-bit specification
    @staticmethod
    def decode(file):
        # Load up a Intel hexfile into its individual records.
        loaded_hex = Hexfile()
        ascii_records = INHX32Decoder.read_file(file)
        loaded_hex.records = INHX32Decoder.decode_ascii(ascii_records)



        return loaded_hex

    # Read hexfile in and output a list of records
    # A record is an intel hex 'command'
    # Each record is proceeded by an ascii ':'
    @staticmethod
    def read_file(file):
        # Read the entire hexfile into memory.
        hexfile_data = file.read()

        # Remove newlines and split records at the colons.
        hexfile_data = hexfile_data.replace('\n', '')
        hexfile_data = hexfile_data.lstrip(':').split(':')
        return hexfile_data

    # Decode the list of ascii records to a list of dicts containing record information
    # TODO: This would be a good place for checksum verification of hexfile records.
    @staticmethod
    def decode_ascii(ascii_records):
        decoded_records = []
        for record in ascii_records:
            data_len = int(record[0:2], base=16) # First ASCII hex byte is the data length
            offset_addr = int(record[2:6], base=16) # Next two ASCII hex bytes is the offset address
            record_type = int(record[6:8], base=16) # Next byte is the record type
            data = bytearray.fromhex(record[8:(data_len*2)+8]) # The data is data_len*2 long since 2 ascii chars represent one hex byte
            checksum = int(record[-2:], base=16) # The Last byte in the record is the checksum
            decoded_records.append(dict(data_len=data_len, offset_addr=offset_addr, record_type=record_type, data=data, checksum=checksum))
        return decoded_records

    # @staticmethod
    # def decode_words(records, word_size=1, byte_order='little'):
    #     words = {}
    #     high_address = 0
    #     for record in records:
    #         if record['offset_addr'] != 0:
    #             low_address = record['offset_addr'] // word_size
    #         else:
    #             low_address = 0

    #         if record['record_type'] == 4 and record['data_len'] == 2:
    #             high_address = int.from_bytes(record['data'], 'big')
    #             high_address = (high_address << 16) // word_size
    #         elif record['record_type'] == 0:
    #             word_start = 0
    #             while word_start < (record['data_len']):
    #                 address = high_address + low_address
    #                 word = int.from_bytes(record['data'][word_start:word_start+word_size], byte_order)
    #                 words[address] = word
    #                 word_start += word_size
    #                 low_address += 1

    #     return words

