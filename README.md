# picchick
A utility to aid in programming PIC microcontrollers.

## Overview

`piccchick` is a commandline utility written in python that interacts with
various programmers in order to flash the memory of a PIC microcontroller.

The function is the same as `avrdude`, i.e. to provide a way to flash a compiled
.hex file onto a microcontroller. The typical development stack involving
picchick looks like:

> Developing (nano)      >   Compiling (xc8-cc)    >    Flashing (picchick)
<!-- TODO: Better diagram of program dependency -->

A hardware device is needed to interface between picchick and the microcontroller
to be programmed. Currently, picchick supports two programmers:
1. **picstick** - Another personal project. This USB stick holds an ATtiny44 and
  a USB-to-UART bridge. It supply's the needed connections for low-voltage ICSP.
  Project files available in the [github repo](https://github.com/rex--/picstick).

2. **flipflop** - A serial bootloader for PICs. Currently only supports 1-wire
  mode. A USB-to-UART bridge is needed, unless your computer has a physical
  serial port. Project files also available in the 
  [github repo](https://github.com/rex--/flipflop).


## Installation

<!-- Device files from Microchip are needed to extract interesting memory addresses for specific chips, e.g.
the Configuration Words or Device Information Area. These device files are  -->

### Requirements
- **`xc8` compiler installed to one of**:
> (linux) /opt/microchip/xc8/                        \
> (Windows) c:\Program Files (x86)\Microchip\xc8\        *\*Windows not currently Supported*

- **python >= 3.10**
  - pyserial

- **Compatible serial programmer**
  - See above for information about programmers.


#### From PyPi
`picchick` can be installed using pip:
```
pip install picchick
<...>
picchick -h
```

#### From Source
`picchick` can also be run as a python module:
```
python -m picchick -h
```
A wrapper script is also provided:
```
./picchick.sh -h
```

## Usage
```
$> picchick -h
usage: picchick [-h] [-d chipID] [-c programmer] [-P port] [-B baud] [-f] [--read addr] [--write addr word] [--erase [addr]] [--reset] [--map] [--list-ports] [hexfile]

A utility to aid in programming PIC microcontrollers

positional arguments:
  hexfile               path to a hexfile

options:
  -h, --help            show this help message and exit
  -d chipID, --device chipID
                        device to be programmed
  -c programmer         type of programmer
  -P port, --port port  programmer serial port
  -B baud, --baud baud  serial connection baudrate
  -f, --flash           flash hexfile onto the device
  --read addr           read word at specified address
  --write addr word     write word to specified address
  --erase [addr]        erase device or specified address
  --reset               reset device
  --map                 display the hexfile
  --list-ports          list available serial ports
```

### Examples
The typical command to erase then flash a hexfile onto a device looks like:
```
picchick -c <programmer> -d <chipID> -P <port> -B <baud> [--erase] -f <hexfile>

picchick -c picstick -d 16lf19196 -P /dev/ttyACM0 -B 115200 --erase -f blink.hex
```