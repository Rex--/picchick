# This module handles the device files that Microchip distributes with the xc8
# compiler. It searches through a list of common locations before deciding
# where to extract the needed data from. Currently it searches in the following
# order:
#
#   1. Command line flags
#       TODO: Not implemented. Maybe a --xc8-toolchain flag?
#
#   2. Enviornment Variable
#       NOTE: The default variable checked is ${XC8_TOOLCHAIN_ROOT}
#           This is a random environment variable that the aur package
#           'microchip-mplabxc8-bin' package creates, but I like it.
#
#   3. Default xc8 compiler installation paths
#

import os
import configparser
import pathlib



# This class holds information about a specific range of memory. It holds
# specific memory addresses and additional information about the type of memory.
class MemoryRange:
    start = None
    end = None
    length = None
    memtype = None

    # We can create a new memory range by either:
    #   1. A length that spans from start to length-1
    #   2. A start and end address
    def __init__(self, start=0x0, end=None, length=None):

        # (1) Length of memory range specified.
        if length and not end:
            self.start = start          # Start at given address (default 0)
            self.length = length        # Given length

            self.end = start + length   # Calculate length of memory range(# of words)

        # (2) End of range defined.
        elif end:
            # Verify range does not end before it starts.
            if end >= start:
                self.start = start  
                self.end = end

                self.length = end - start + 1
        
        # Blank memory range
        else:
            self.start = None
            self.end = None
            self.length = None

class Device:
    family = None   # Family of chip
    arch = None     # Chip architecture
    chip_id = None  # Chip identifier

    def __init__(self, chip_id):
        self.chip_id = chip_id.upper()
    
    def configure(self, *args, **kwargs):
        raise NotImplementedError


class PICDevice(Device):
    family = 'pic'
    # Memory Ranges
    flash = None    # Memory range that spans User Flash
    config = None   # Memory range that spans Config Words
    user_id = None
    eeprom = None

    blocksize = None

    def configure(self, devicefile):
        # Device arch
        #   'ARCH' : PIC12, PIC14, PIC16 etc.
        self.arch = devicefile.get(self.chip_id, 'ARCH')

        # (Flash) memory range from addresses 0x0 to the flash_size-1
        #   'ROMSIZE' : length of flashsize stored as a string in hexadecimal
        #   'FLASHTYPE' : Type of flash
        self.flash = MemoryRange(length=int(devicefile.get(self.chip_id, 'ROMSIZE'), base=16))
        self.flash.memtype = devicefile.get(self.chip_id, 'FLASHTYPE')

        # (Config Word) memory range that spans the configuration word addresses
        #   'CONFIG' : Range of addresses stored as hexadecimal separated by a '-'
        config_range = devicefile.get(self.chip_id, 'CONFIG')
        self.config = MemoryRange(
            start=int(config_range.split('-')[0], base=16),
            end=int(config_range.split('-')[1], base=16)
        )
        self.config.memtype = 'config'

        # (User ID) Memory range that spans the user id region
        #   'IDLOC' : <start>-<end>
        id_range = devicefile.get(self.chip_id, 'IDLOC').split('-')
        self.user_id = MemoryRange(
            start=int(id_range[0], base=16),
            end=int(id_range[1], base=16)
        )
        self.user_id.memtype = 'user_id'

        # (EEPROM) Memory range that spans the eeprom flash region
        #   'EEPROM' : start-end
        eeprom_range = devicefile.get(self.chip_id, 'EEPROM').split('-')
        self.eeprom = MemoryRange(
            start=int(eeprom_range[0], base=16),
            end=int(eeprom_range[1], base=16)
        )
        self.eeprom.memtype = 'eeprom'

        # (Blocksize) The size of a flash writing block
        #   'FLASH_WRITE' : <int>
        self.blocksize = int(devicefile.get(self.chip_id, 'FLASH_WRITE'), base=16)


# Default install paths for the xc8 compiler
XC8_DEFAULT_PATHS = [
    '/opt/microchip/xc8',                   # linux
    '/Applications/microchip/xc8',          # Mac (untested)
    'c:/Program Files (x86)/Microchip/xc8'  # Windows (untested)
]

# The name of the optional environment variable that holds the path to a
# specific xc8 compiler
XC8_ENV_VARIABLE = 'XC8_TOOLCHAIN_ROOT'


# This class handles searching the local filesystem for the xc8 compiler so
# we can use its device files
class XC8CompilerConfigurator:

    xc8_paths = {}      # Dict of 'ver':[path] of found xc8 toolchains
        # Also contains a 'default' key that points to single root path

    search_paths = []   # List of paths to search for toolchains. Could be a
        # toolchain root OR a directory that includes multiple toolchains.

    # Search_paths is the paths to search for compilers. If it is a list,
    # each path is added to the list of paths to search for toolchains. If it
    # is a single string, then only that single path is searched and an error
    # thrown if no compiler is found.
    def __init__(self, search_paths=XC8_DEFAULT_PATHS):

        # Check if search_paths is a string
        if isinstance(search_paths, str):
            self.search_paths.append(search_paths)
        
        # Assume its an iterable
        else:
            # Add environment variable path to search path.
            if XC8_ENV_VARIABLE in os.environ:
                self.search_paths.append(os.getenv(XC8_ENV_VARIABLE))
                # TODO: Skip other paths if this exists

            # Add given search_paths
            self.search_paths.extend(search_paths)
        
        # Find compilers using the given paths
        self._findCompilers()

        # Set default compiler to the latest version
        self.xc8_paths['default'] = self.xc8_paths[sorted(self.xc8_paths)[-1]][0]
    
    # Go through the various locations and find installed compilers
    def _findCompilers(self):

        # Each search path could be a toolchain dir, or a directory containing toolchains.
        for search_path in self.search_paths:

            test_path = pathlib.Path(search_path)

            if test_path.is_dir():
                # Directory exists:

                # Check if it is a toolchain directory by seeing if it is named
                # 'vX.X' and contains a directory called 'pic'.
                if test_path.name.startswith('v') and (test_path/'pic').is_dir():

                    # Create version in xc8 list if doesnt exist
                    if test_path.name not in self.xc8_paths:
                        self.xc8_paths[test_path.name] = [test_path]
                    
                    # Append path only if its not a duplicate
                    else:
                        if test_path not in self.xc8_paths[test_path.name]:
                            self.xc8_paths[test_path.name].append(test_path)
                
                # If its not a toolchain root, check if it contains toolchains
                else:

                    for test_subpath in test_path.iterdir():
                        # Check each subdir is a toolchain directory by seeing if it is named
                        # 'vX.X' and contains a directory called 'pic'.
                        if test_subpath.name.startswith('v') and (test_subpath/'pic').is_dir():

                            # Create version in xc8 list if doesn't exist
                            if test_subpath.name not in self.xc8_paths:
                                self.xc8_paths[test_subpath.name] = [test_subpath.name]
                            else:
                                if test_subpath not in self.xc8_paths[test_subpath.name]:
                                    self.xc8_paths[test_subpath.name].append(test_subpath)

    # Returns a XC8Device object corresponding to the given chip_id
    def readDeviceFile(self, chip_id):
        # Device files live at <toolchain_root>/pic/dat/ini/<chipID>.ini
        devicefile_path = self.xc8_paths['default'] / 'pic/dat/ini' / (chip_id.lower() + '.ini')

        devicefile = configparser.ConfigParser(strict=False)
        devicefile.read(devicefile_path)

        device = PICDevice(chip_id)     # Create device object
        device.configure(devicefile)    # Configure based on devicefile

        return device       # Return device

