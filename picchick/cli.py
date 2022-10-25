
import argparse
import os.path
import sys

from . import hexfile
from . import programmer
from . import devices


DESCRIPTION = '''\
A utility to aid in programming PIC microcontrollers\
'''

USAGE = '''\
picchick [--read addr] [--write addr word] [--erase [addr]] [--verify] [-f] [--map] [--list-ports] [hexfile]
       picchick -d <mcu> -c <programmer> -P <port> -B <baud> [--erase] [--verify] [--reset] -f <hexfile>
       picchick [-d mcu] --map [hexfile]
'''

EPILOG = '''\
flag arguments:
  addr:\t\t\tdevice memory address in hexadecimal
\t'all'\t\tall device memory areas
\t'flash'\t\tuser flash area
'''

# Create our base ArgumentParser
parser = argparse.ArgumentParser('picchick',
description=DESCRIPTION,
usage=USAGE,
formatter_class=argparse.RawDescriptionHelpFormatter,
# epilog=EPILOG,
add_help=False)

def parse_argv():
    # Add programmer flag to parser
    parser.add_argument('-c',
    metavar='programmer',
    dest='programmer',
    choices=programmer.registry.keys(),
    help='type of programmer')

    # Before adding any other options, get our programmer option if it's set.
    # This is so we can add any programmer specific options to the parser.
    programmer_arg = parser.parse_known_args()[0].programmer

    # Base Options
    parser.add_argument('hexfile',
        nargs='?',
        default=None,
        help='path to a hexfile')
    parser.add_argument('-d', '--device',
        metavar='mcu',
        help='device to be programmed')
    parser.add_argument('-h', '--help',     # We wait until now to add -h so it
        action='help',                      # will print all arguments (And show
        help='print this message and exit') # up on the bottom of the list)

    # Action flags
    action_group = parser.add_argument_group('actions')
    action_group.add_argument('--read',
        nargs='+',
        metavar=('addr', 'byte_len'),
        help='read bytes from specified address')
    action_group.add_argument('--write',
        nargs=2,
        metavar=('addr', 'word'),
        help='write word to specified address')
    action_group.add_argument('-f', '--flash',
        action='store_true',
        help='flash hexfile onto the device')
    action_group.add_argument('--erase',
        nargs='?',
        const='all',
        metavar='addr',
        help='erase device or specified address')
    action_group.add_argument('--verify',
        action='store_true',
        help='verify device memory')
    # Informational Action flags
    action_group.add_argument('--map',
        action='store_true',
        help='display the hexfile')
    action_group.add_argument('--list-ports',
        action='store_true',
        help='list available serial ports')

    # Programmer options
    if programmer_arg is not None:
        po_group = parser.add_argument_group('programmer options')
        programmer.registry[programmer_arg].add_args(po_group)

    # Now we parse arguments and return them
    return parser.parse_args()


def run():
    # Parse arguments
    args = parse_argv()

    # Requirements tree

    # Flash flag requires both the hexfile and the programmer
    both_reqd = (args.flash or args.verify)
    # The read and erase flags only require the programmer connection
    programmer_reqd = both_reqd or (args.read or args.erase or args.write)
    # The map flag only requires the hexfile to be present
    hexfile_reqd = both_reqd or args.map
    # Device object required
    device_reqd = hexfile_reqd
    # list_ports flag doesn't require anything
    nothing_reqd = (args.list_ports)

    # If we don't need to do anything, print help because
    # the user needs it
    if not hexfile_reqd and not programmer_reqd and not nothing_reqd:
        parser.error('at least one action argument is required')


    # Firstly, if we need the hexfile, check if it exists and load it.
    # If not, immediatly exit with a helpful message
    if hexfile_reqd:
        if args.hexfile is None:
            print(f"Missing argument: hexfile")
            sys.exit(1)
        elif args.device is None:
            if programmer_reqd:
                # Allow local operations on hexfile without specifying device
                print("Missing argument: -d, --device chipID")
                sys.exit(1)
        elif not os.path.isfile(args.hexfile):
            print(f"Could not find hexfile: { args.hexfile}")
            sys.exit(1)

        if args.device is None:
            # Device flag not defined, create empty one
            xdevice = devices.Device('')
        else:
            try:
                xdevice = devices.XC8CompilerConfigurator().readDeviceFile(args.device)
                print(f"Found device: { xdevice.family }{ args.device }")
            except:
                print(f"WARNING: Could not find device: { args.device } -- Using defaults")
                if not programmer_reqd:
                    # We allow local operations with a skeleton device
                    xdevice = devices.Device(args.device)
                else:
                    print(f"Could not find device: { args.device }")
                    sys.exit(1)

        print(f"Using hexfile: { args.hexfile }")
        hexobj = hexfile.loadHexfile(args.hexfile, xdevice)

    # We now have all the hexfile reqs, so take care of the actions
    # that only require the hexfile
    if args.map:
        print(hexobj)
        # hexfile.printHexfile(hexobj)
        # hex_decoder.printMemory()


    # Second if we need the programmer, we check:
    # - If the -c argument is specified
    # - If the specified programmer exists (argparse does this when we specify choices)
    # - If the -p argument is specified
    # - If the path exists (This may not work on windows)
    if programmer_reqd:

        # Check if programmer exists
        if args.programmer is None:
            print("Missing argument: -c")
            sys.exit(1)
        else:
            chosen_programmer = programmer.registry[args.programmer]

        # Check if port exists
        if args.port is None:
            print("Missing argument: -P port")
            sys.exit(1)
        elif not os.path.exists(args.port):
            print(f"Could not find port: { args.port }")
            sys.exit(1)
        else:
            dev = chosen_programmer(args)
            if not dev.connect():
                print(f"ERROR: Failed to connect to device: { args.port } Exiting...")
                sys.exit(1)


    # We now have all the programmer reqs, so do the actions that only
    # need the programmer:
    # Display information about ports if flag was included
    if args.list_ports:
        programmer.listPorts()
        if args.port is not None:
            print("INFO: --list-ports flag included with valid programmer")


    if args.erase or args.flash or args.read or args.write or args.verify:

        if args.erase:
            if args.erase == 'all':
                dev.erase(0xFFFF)
            elif args.erase == 'flash':
                dev.erase(0xEFFF)
            else:
                dev.erase(int(args.erase, base=16))
        
        if args.flash:
            success_blocks = 0
            print(f"Starting write of flash...")
            for address, block in hexobj.chunkFlash().items():
                byte_block = bytearray()
                for word in block:
                    byte_block.extend(word.to_bytes(2, 'big'))
                if dev.write(address, byte_block):
                    success_blocks += 1
            print(f"Successfully wrote  bytes in {success_blocks} chunks.")

            for address, word in hexobj.config.items():
                dev.write(address, programmer.INTBYTES(word))
        elif args.write:
            dev.word(int(args.write[0], base=16), int(args.write[1], base=16))
        
        if args.read:
            if (len(args.read) < 2):
                args.read.extend('2')
            read_resp = dev.read(int(args.read[0], base=16), int(args.read[1]))
            print(read_resp.hex(' ', -2))
        
        if args.verify:
            print('Verifying memory...')
            fail = False
            if hexfile_reqd:
                # If we have loaded the hexfile verify against that
                for address, word in hexobj.memory.items():
                    word_verify = dev.read(address)
                    if word != int.from_bytes(word_verify, 'big'):
                        print(f"ERROR: Verification failed at address: x{address:X}")
                        fail = True
                        break
            elif args.write:
                # Else verify the written word
                word_verify = dev.read(int(args.write[0], base=16))
                if int(args.write[1], base=16) != int.from_bytes(word_verify, 'big'):
                    fail = True
                    print(f"ERROR: Verification failed: x{int(args.write[0], base=16):X} - {int(args.write[1], base=16)} != {int.from_bytes(word_verify, 'little')}")

            if not fail:
                print('Successfully verified memory')

    if programmer_reqd:
        dev.disconnect()
