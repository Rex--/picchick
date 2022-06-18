# picchick
A utility to aid in programming PIC microcontrollers


## Overview

`piccchick` is a commandline utility written in python that interfaces with a serial device in order to program PIC16 using the low-voltage ICSP interface.

The function is the same as `avrdude`, i.e. to provide a way to flash a compiled .hex file onto a microcontroller. The typical development stack involving picchick looks like:

> Developing (nano)      >   Compiling (xc8-cc)    >    Flashing (picchick)


## Installation

### Requirements
- **`xc8` compiler installed to one of**:
> (linux) /opt/microchip/xc8/                        \
> (Windows) c:\Program Files (x86)\Microchip\xc8\        *\*Windows not currently Supported*

- **python >= 3.10**
  - pyserial

- **Compatible serial programmer**
  - Currently the only compatible programmer is the [picstick](https://github.com/rex--/picstick).


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

### Flashing
The typical command to erase then flash a hexfile onto a device looks like:
```
picchick -P <port> -d <chipID> --erase -f <hexfile>
picchick -P /dev/ttyACM0 -d 16lf19196 --erase -f blink.hex
```

```
$> picchick -h

usage: picchick [options] [hexfile]

A utility for programming PIC microcontrollers

positional arguments:
  hexfile               path to the hexfile

options:
  -h, --help            show this help message and exit
  -f, --flash           flash hexfile onto the device
  --read addr           read specified address or chunk of memory
  --write addr word     write word to specified address
  --erase [addr]        erase device or specified address
  -d chipID, --device chipID
                        device to be programmed
  -P port, --port port  programmer serial port
  -B, --baud baud       serial connection baudrate
  --map                 display the hexfile
  --list-ports          list available serial ports

flag arguments:
  [addr]:		device memory address in hexadecimal
	'all'		    all device memory areas
	'flash'		user flash area
```
