# This modules handles the device files that are used by picchick to determine
# things like flashsize, flash/config/eeprom ranges, etc. Microchip distributes
# Device Family Packs (DFPs) which include these device files. Stripped down
# versions of the files are included in the module, however they could be out
# of date or missing a specific device. Because of that, other locations are
# searched first, in the following order:
#
#   0. Path to file
#       If the given device ID is a path to a file, then read the given file as
#       the device file. This allows custom devices.
#
#   1. Command line flag
#       TODO: Not implemented. Maybe a --dfp flag?
#
#   2. Enviornment Variable - 'MCHP_PACKS'
#       Checks to see if the enviornment vaiable 'MCHP_PACKS' is set to a
#       directory that contains the device file.
#
#   3. Default Microchip devce pack location - '~/.mchp_packs'
#       MPLAB stores these at:
#           '~/.mchp_packs/Microchip/<version>/xc8/pic/dat/ini/*.ini'
#       However, we detect any files in the '~/.mchp_packs' directory.
#
#   4. Included device files
#       The embedded device files are searched for the given device ID.
#

import os
import configparser
import pathlib
from importlib.resources import files


def get_device(dev_id):

    # Check to see if dev_id is a path by seeing if we have access.
    if os.access(dev_id, os.R_OK):
        # Interpret the file as a custom device.
        device = CustomDeviceConfigurator().readDeviceFile(dev_id)
    else:
        # We only support xc8 pic devices currently.
        device = MCHPDevicePackConfigurator().readDeviceFile(dev_id)

    return device


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

            # Calculate length of memory range(# of words)
            self.end = start + length - 1

        # (2) End of range defined.
        elif end and not length:
            # Verify range does not end before it starts.
            if end >= start:
                self.start = start  
                self.end = end

                self.length = end - start + 1
        
        elif end and length:
            raise Exception

        # Blank memory range
        else:
            self.start = None
            self.end = None
            self.length = None

    def __len__(self):
        return self.length
    
    def __repr__(self):
        ret = 'MemoryRange(0x%X - 0x%X)'
        return ret % (self.start, self.end)

# The following is an f-string template to use for device sub-classes that
# would like to add their own features in the string representation.
_DEVICE_TEMPLATE = "family='{self.family}', arch='{self.arch}', chip_id='{self.chip_id}', flash={self.flash}, config={self.config}, word_size={self.word_size}, row_size={self.row_size}"
# __DEVICE_DEFAULT = "family='{self.family}', arch='{self.arch}', chip_id='{self.chip_id}', flash={self.flash}, config={self.config}, word_size={self.word_size}, row_size={self.row_size}, page_size={self.page_size}"

class Device:
    # Device Identifiers
    family = None   # Family of chip
    arch = None     # Chip architecture
    chip_id = None  # Chip identifier

    # Memory Ranges
    flash = None    # Memory range that spans User Flash
    config = None   # Memory range that spans config words/fuses

    # Memory Format
    byte_order = 'big'   # The order of bytes in words. (big/little)
    word_size = 1    # The length of a word in bytes.
    row_size = 1     # The length of a row in words. A row is the smallest writeable block.
    # page_size = None    # The length of a page in words. A page is the largest transmittable block.

    def __init__(self, chip_id):
        self.chip_id = chip_id.upper()
    
    def configure(self, *args, **kwargs):
        raise NotImplementedError
    
    def __repr__(self):
        return eval('f"Device(%s)"' % _DEVICE_TEMPLATE)

class CustomDevice(Device):

    def configure(self, devicefile):

        dev_sect = devicefile[self.chip_id]
        self.family = dev_sect['FAMILY']
        self.arch = dev_sect['ARCH']
        self.byte_order = dev_sect['BYTE_ORDER']
        self.word_size = int(dev_sect['WORD_SIZE'])
        self.row_size = int(dev_sect['ROW_SIZE'])
        self.flash = MemoryRange(length=int(dev_sect['FLASH'], base=16))
        config_range = dev_sect['CONFIG']
        self.config = MemoryRange(
            start=int(config_range.split('-')[0], base=16),
            end=int(config_range.split('-')[1], base=16)
        )

    def __repr__(self):
        return eval('f"CustomDevice(%s)"' % _DEVICE_TEMPLATE)



class PICDevice(Device):
    # Fill in static information
    family = 'pic'
    byte_order = 'big'
    word_size = 2

    # Memory Ranges
    user_id = None
    eeprom = None

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
        self.row_size = int(devicefile.get(self.chip_id, 'FLASH_WRITE'), base=16)

    def __repr__(self):
        return eval('f"PICDevice(%s)"' % _DEVICE_TEMPLATE)


MCHP_PACKS_ENV = 'MCHP_PACKS'

class MCHPDevicePackConfigurator:

    # Functions that search for device file. Should be called in order
    search_funcs = None

    # CLI flag value will be set if needed
    cli_flag = None

    # device will be set if found
    device = None

    def __init__(self, cli_flag=None):
        self.search_funcs = [
            self.__searchCLIFlag,
            self.__searchEnvVar,
            self.__searchInstalledDFPs,
            self.__searchIncludedDFPs
        ]

    def readDeviceFile(self, chip_id):
        self.chip_id = chip_id
        for searchFunc in self.search_funcs:
            if searchFunc(chip_id):
                break
        return self.device
    
    def __searchCLIFlag(self, chip_id):
        return False

    def __searchEnvVar(self, chip_id):
        if MCHP_PACKS_ENV not in os.environ:
            # Env variable not set
            return False
        pack_env_path = os.getenv(MCHP_PACKS_ENV)
        if not pack_env_path.is_dir():
            # Env directory doesn't exist
            return False
        devicefile_paths = sorted(pack_env_path.rglob(chip_id.lower() + '.ini'))
        if len(devicefile_paths) == 0:
            # Env path doesn't contain device file
            return False
        self.__configureDeviceFromFile(devicefile_paths[0])
        return True

    
    def __searchInstalledDFPs(self, chip_id):
        pack_install_path = pathlib.Path.home() / ".mchp_packs"
        if not pack_install_path.is_dir():
            # Install directory does not exist
            return False
        devicefile_paths = sorted(pack_install_path.rglob(chip_id.lower() + '.ini'))
        if len(devicefile_paths) == 0:
            # Install path does not contain device file
            return False
        self.__configureDeviceFromFile(devicefile_paths[0]) # device file is first file we find
        return True

    def __searchIncludedDFPs(self, chip_id):
        devicefile_path = files('picchick.devices.ini') / (chip_id.lower() + '.ini')
        if devicefile_path.exists():
            self.__configureDeviceFromFile(devicefile_path)
            return True
        else:
            return False
    
    def __configureDeviceFromFile(self, devicefile_path):
        print(devicefile_path)
        devicefile = configparser.ConfigParser(strict=False)
        devicefile.read(devicefile_path)
        device = PICDevice(self.chip_id)     # Create device object
        device.configure(devicefile)    # Configure based on devicefile
        self.device = device


class CustomDeviceConfigurator:
    
    def __init__(self):
        pass

    def readDeviceFile(self, path):

        devicefile = configparser.ConfigParser()
        devicefile.read(path)

        mcu_str = devicefile.sections()[0]
        device = CustomDevice(mcu_str)
        device.configure(devicefile)
        
        return device
