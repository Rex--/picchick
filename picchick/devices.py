import configparser
import pathlib


class MemoryRange:

    size = None
    start = None
    end = None

    def configure(self, size=None, addr_range=None):

        if size and not addr_range:
            self.size = int(size, base=16)
            self.start = 0
            self.end = self.size - 1

        if addr_range and not size:
            self.start = int(addr_range.split('-')[0], base=16)
            self.end = int(addr_range.split('-')[1], base=16)
            self.size = self.end - self.start + 1


# This class holds the device data needed for flashing etc.
class Device:

    flash = MemoryRange()
    config = MemoryRange()

    def __init__(self, chip_id):

        self.chip_id = chip_id.upper()
    
    def readDeviceFile(self, ccpath):
        self.device_file_path = ccpath / 'pic/dat/ini' / (self.chip_id.lower() + '.ini')
        self.device_file = configparser.ConfigParser(strict=False)
        self.device_file.read(self.device_file_path)
        self.flash.configure(size=self.device_file.get(self.chip_id, 'ROMSIZE'))
        self.config.configure(addr_range=self.device_file.get(self.chip_id, 'CONFIG'))


XC8_COMMON_PATHS = [
    '/opt/microchip/xc8'
]

# This class handles searching the local filesystem for the xc8 compiler so
# we can use its device files
class XC8Manager:

    # xc8_paths = []
    
    def findXC8Installs():

        found_installs = []

        for common_path in XC8_COMMON_PATHS:
            path = pathlib.Path(common_path)

            if path.is_dir():
                found_installs += [p for p in path.iterdir() if p.is_dir()]
        
        # self.xc8_paths += found_installs
        return found_installs




