
import re


PFM_START = 0x0000
USER_ID_START = 0x8000
CONFIG_WORD_START = 0x8007

# Return a dict with the keys being the start address of a data block,
# and the value being a list of words that form the data block
def getMemoryFromHexfile(path_to_hexfile):
    ascii_records = readHexfile(path_to_hexfile)
    decoded_records = decodeAsciiRecords(ascii_records)
    words = decodeWordsFromRecords(decoded_records)
    memory = seperateDataBlocks(words)
    return memory


def printMemory(memory):
    print('\n PFM   :   x0     x1     x2     x3     x4     x5     x6     x7     x8     x9     xA     xB     xC     xD     xE     xF')
    print('-------:-----------------------------------------------------------------------------------------------------------------')
    for start_addy, data_block in memory.items():
        if start_addy < USER_ID_START:
            first_column = False
            if start_addy % 16 != 0 and start_addy != 0:
                offset = (start_addy % 16)
                print('\n       :\n0x%.4X | ' % (start_addy - offset), end='')
                while offset > 0:
                    print('  --   ', end='')
                    offset -= 1
            elif start_addy == 0:
                print('0x%.4X | ' % start_addy, end='')
                first_column = True
            else:
                first_column = True
                print('\n       :\n0x%.4X | ' % start_addy, end='')
            word_address = start_addy
            for word in data_block:
                if word_address % 16 == 0 and not first_column:# and  word_address != 0:
                    if word_address % 64 == 0:
                        print('\n       +', end='')
                    print('\n0x%.4X | ' % word_address, end='')
                    first_column = True
                print('0x%.4X ' % word, end='')
                first_column = False
                word_address += 1
            
            if word_address % 16 != 0 and word_address != 0:
                offset = 16 - (word_address % 16)
                while offset > 0:
                    print('  --   ', end='')
                    offset -= 1

    print('\n       :\nUSER ID:\n-------:--------')
    for word_address, data_block in memory.items():
        if USER_ID_START <= word_address < CONFIG_WORD_START:
            if len(data_block) == 1:
                print ('0x%.4X | 0x%.4X' % (word_address, data_block[0]))
            else:
                for config_word in data_block:
                    print('0x%.4X | 0x%.4X' % (word_address, config_word))
                    word_address += 1

    print('       :\nCONFIG :\n-------:--------')
    for word_address, data_block in memory.items():
        if word_address >= CONFIG_WORD_START:
            if len(data_block) == 1:
                print ('0x%.4X | 0x%.4X' % (word_address, data_block[0]))
            else:
                for config_word in data_block:
                    print('0x%.4X | 0x%.4X' % (word_address, config_word))
                    word_address += 1
    print('')


# Read the hexfile in and output a list of records
def readHexfile(path_to_hexfile):
    # Read the entire hexfile (Shouldn't be more than 56k * 2)
    with open(path_to_hexfile) as hexfile:
        hex_from_file = hexfile.read()
    
    # Remove newlines and spaces
    hex_from_file = re.sub(r'[\n\t\s]*', '', hex_from_file)

    # Split the file at the record marks ':' to get a list of records
    return hex_from_file.lstrip(':').split(':')

# Decode the list of ascii records to a list of dicts containing record information
def decodeAsciiRecords(ascii_records):
    decoded_records = []
    for record in ascii_records:
        data_len = int(record[0:2], base=16) # First ASCII hex byte is the data length
        offset_addr = int(record[2:6], base=16) # Next two ASCII hex bytes is the offset address
        record_type = int(record[6:8], base=16) # Next byte is the record type
        data = record[8:(data_len*2)+8] # The data is data_len*2 long since 2 ascii chars represent one hex byte
        checksum = int(record[-2:], base=16) # The Last byte in the record is the checksum
        decoded_records.append(dict(data_len=data_len, offset_addr=offset_addr, record_type=record_type, data=data, checksum=checksum))
    return decoded_records

# Decodes a list of record object to a dictionary containg [Address]: <Word>
def decodeWordsFromRecords(decoded_records):
    words = {}
    high_address = 0 # The high address defaults to 0x0000 unless a hex record sets it otherwise
    for record in decoded_records: 
        if record['offset_addr'] != 0:
            low_address = record['offset_addr'] // 2    # Address are 2x that of the pic in the hex file since it takes 2 bytes per word
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


def seperateDataBlocks(words):
    memory = {}
    mem_start = min(words.keys())
    # Seperate the memory into blocks to be written via icsp
    while len(words) > 0:
        address = block_start = min(words.keys())
        memory[block_start] = [words.pop(address)]
        while True:
            address += 1
            try:
                memory[block_start].append(words.pop(address))
            except KeyError:
                break
    return memory


# Separates the blocks of data into rows of 64-words and pads them with 0x3FFF
def rowifyDataBlock(memory):
    rowmem = {}
    for start_address, data in memory.items():
        if start_address < USER_ID_START:
            # Pad blocks to the nearest row and 
            # store it in a new dict at its new address (if changed)
            new_address, data = padRow(start_address, data)
            rowmem[new_address]  = data
            # Split padded blocks into rows of 64 words
            while len(rowmem[new_address]) > 64:
                old_address = new_address
                new_address += 64
                rowmem[new_address] = rowmem[old_address][64:]
                # print(rowmem[new_address])
                del rowmem[old_address][64:]
                #rowmem[start_address + 64] = padRow(start_address+64, data[64:])

        if start_address >= USER_ID_START:
            if len(data) == 1:
                rowmem[start_address] = data
            else:
                for word in data:
                    rowmem[start_address] = [word]
                    start_address += 1
    return rowmem


def padRow(start_address, data):
    # Pad Ends
    if (start_address + len(data)) % 64 != 0:
        offset = 64 - (start_address + len(data) % 64)
        # print(f"Padding end of { start_address } with {offset} words")
        data = data + [0x3FF for _ in range(offset)]
    # Pad beginning
    if start_address % 64 != 0 and start_address != 0:
        offset = (start_address % 64)
        # print(f"Padding start of { start_address } with { offset } words")
        data = [0x3FF for _ in range(offset)] + data
        start_address -= offset
    return (start_address, data)