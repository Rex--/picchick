
import argparse
import os.path
import sys

from . import hexfile
from . import programmer


DESCRIPTION = '''\
A utility to aid in programming PIC microcontrollers\
'''

USAGE = '''\
picchick [options] [hexfile]\
'''

EPILOG = '''\
flag arguments:
  [addr]:\t\tdevice memory address in hexadecimal
\tall\t\tall device memory areas
\tflash\t\tuser flash area
'''

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=DESCRIPTION,
    usage=USAGE,
    epilog=EPILOG)

parser.add_argument('hexfile',
    nargs='?',
    default=None,
    help='path to the hexfile')

parser.add_argument('-f', '--flash',
    action='store_true',
    help='flash hexfile onto the device')
parser.add_argument('--read',
    metavar='addr',
    help='read specified address or chunk  of memory')
parser.add_argument('--write',
    nargs=2,
    metavar=('addr', 'word'),
    help='write word to specified address')
parser.add_argument('--erase',
    nargs='?',
    const='all',
    metavar='addr',
    help='erase device or specified address')

parser.add_argument('-d', '--device',
    metavar='chipID',
    help='device to be programmed')
parser.add_argument('-p', '--port',
    metavar='port',
    help='programmer serial port')
parser.add_argument('--baud',
    type=int,
    default=9600,
    metavar='baud',
    help='serial connection baudrate',)

parser.add_argument('--map',
    action='store_true',
    help='display the hexfile')
parser.add_argument('--list-ports',
    action='store_true',
    help='list available serial ports')
parser.add_argument('--list-devices',
    action='store_true',
    help='list available device configurations')

def parseArgv():
    args = parser.parse_args()

    # Requirements tree

    # Flash flag requires both the hexfile and the programmer (port)
    both_reqd = (args.flash)
    # The read and erase flags only require the programmer connection (and port flag)
    programmer_reqd = both_reqd or (args.read or args.erase or args.write)
    # The map flag only requires the hexfile to be present
    hexfile_reqd = both_reqd or (args.map)

    # If we don't need to do anything, print help because
    # the user needs it
    if not hexfile_reqd and not programmer_reqd:
        parser.print_help()
        sys.exit(0)


    # Firstly, if we need the hexfile, check if it exists
    # If not, immediatly exit with a helpful message
    if hexfile_reqd:
        if args.hexfile is None:
            print(f"Missing argument: hexfile")
            sys.exit(1)
        elif args.device is None:
            print("Missing argument: -d, --device chipID")
        elif not os.path.isfile(args.hexfile):
            print(f"Could not find hexfile: { args.hexfile}")
            sys.exit(1)
        else:
            print(f"Using hexfile: { args.hexfile }")
        hex_decoder = hexfile.HexfileDecoder(args.hexfile, args.device)

    # We now have all the hexfile reqs, so take care of the actions
    # that only require the hexfile
    if args.map:
        hex_decoder.printMemory()


    # Second if we need the programmer, we check:
    # - If the -p argument is specified
    # - If the path exists (This may not work on windows)
    if programmer_reqd:
        if args.port is None:
            print("Missing argument: -p port")
            sys.exit(1)
        elif not os.path.exists(args.port):
            print(f"Could not find port: { args.port }")
            sys.exit(1)
        else:
            dev = programmer.Programmer(args.port, baud=args.baud)
            if not dev.connect():
                print(f"ERROR: Failed to connect to device: { args.port } Exiting...")
                sys.exit(1)


    # We now have all the programmer reqs, so do the actions that only
    # need the programmer:
    # Display information about ports if flag was included
    if args.list_ports:
        # if args.port is None:
        programmer.listPorts()
        # else:
            # print("Not including port-list due to valid port flag")


    if args.erase or args.flash or args.read or args.write:
        dev.start()

        if args.erase:
            if args.erase == 'all':
                dev.erase(0xFFFF)
            elif args.erase == 'flash':
                dev.erase(0xEFFF)
            else:
                dev.erase(int(args.erase, base=16))
        
        if args.flash:
            

            for start_address, row in hex_decoder.memory.items():
                if start_address < hexfile.USER_ID_START:
                    dev.row(start_address, row)
            for start_address, word in hex_decoder.memory.items():
                if hexfile.USER_ID_START <= start_address < hexfile.CONFIG_WORD_START:
                    dev.word(start_address, word[0])
            for start_address, word in hex_decoder.memory.items():
                if hexfile.CONFIG_WORD_START <= start_address:
                    dev.word(start_address, word[0])
        elif args.write:
            dev.word(int(args.write[0], base=16), int(args.write[1], base=16))
        
        if args.read:
            dev.read(int(args.read, base=16))
        dev.stop() 
        dev.disconnect()
