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
usage: picchick [-h] [--read addr] [--write addr word] [--erase [addr]] [-f] [--map] [--list-ports] [hexfile]
       picchick -d <mcu> -c <programmer> -P <port> -B <baud> [--erase] [--reset] -f <hexfile>
       picchick [-d mcu] --map [hexfile]

A utility to aid in programming PIC microcontrollers

positional arguments:
  hexfile               path to a hexfile

options:
  -h, --help            show this help message and exit
  -d mcu, --device mcu  device to be programmed
  -c programmer         type of programmer
  -P port, --port port  programmer serial port
  -B baud, --baud baud  serial connection baudrate
  --read addr           read word at specified address
  --write addr word     write word to specified address
  --erase [addr]        erase device or specified address
  -f, --flash           flash hexfile onto the device
  --reset               reset device
  --map                 display the hexfile
  --list-ports          list available serial ports

flag arguments:
  addr:			device memory address in hexadecimal
	'all'		all device memory areas
	'flash'		user flash area
```

### Examples
The typical command to erase then flash a hexfile onto a device looks like:
```
picchick -d <mcu> -c <programmer> -P <port> -B <baud> [--erase] -f <hexfile>

picchick -c picstick -d 16lf19196 -P /dev/ttyACM0 -B 115200 --erase -f blink.hex
```

## Displaying Hexfiles
There is a simple built-in utility to display hex files on the command line. If
the device is specified and found, the hexfile will be decoded and displayed
according to the specific device. The device flag can also be omitted, and the
utility will decode them according to the base INHX32 spec.\
In either case, the data will be output in table format.

**Example: Default byte map**
```
$> picchick --map tests/blink.hex

Using hexfile: tests/blink.hex
  ADDR | x0  x1  x2  x3  x4  x5  x6  x7  x8  x9  xA  xB  xC  xD  xE  xF 
-------+----------------------------------------------------------------
    x0 | x80 x31 x02 x28 x87 x31 xFD x2F                                
  xF20 |                                                         x87 x31
  xF30 | xA7 x27 x87 x31 x59 x01 x0C x17 x00 x32 x00 x32 x00 x00 x59 x01
  xF40 | x0C x13 x00 x32 x00 x32 x00 x00 x9A x2F x80 x31 x02 x28 x40 x01
  xF50 | x98 x01 x99 x01 x9A x01 x9B x01 x9C x01 x9D x01 x59 x01 x90 x01
  xF60 | x91 x01 x40 x01 x92 x01 x93 x01 x94 x01 x95 x01 x96 x01 x97 x01
  xF70 | x59 x01 x8E x01 x8F x01 x7E x01 xB8 x01 xC3 x01 xCE x01 xD9 x01
  xF80 | xE4 x01 x7C x01 xD0 x01 xDB x01 x7E x01 xB9 x01 xC4 x01 xCF x01
  xF90 | xDA x01 xE5 x01 x7C x01 xD1 x01 xDC x01 xE7 x01 x7E x01 xBA x01
  xFA0 | xC5 x01 xD0 x01 xDB x01 xE6 x01 x7C x01 xD2 x01 xDD x01 xE8 x01
  xFB0 | xFF x30 x7E x01 xBB x00 xFF x30 xC6 x00 xFF x30 xD1 x00 xFF x30
  xFC0 | xDC x00 xFF x30 xE7 x00 xFF x30 x7C x01 xD3 x00 xFF x30 xDE x00
  xFD0 | xFF x30 xE9 x00 xFF x30 x7E x01 xBC x00 xFF x30 xC7 x00 xFF x30
  xFE0 | xD2 x00 xFF x30 xDD x00 xFF x30 xE8 x00 xFF x30 x7C x01 xD4 x00
  xFF0 | xFF x30 xDF x00 xFF x30 xEA x00 x08 x00 x40 x01 x87 x31 x97 x2F
x10000 |                                                         xE8 x3F
x10010 |         x9F x3F
```
**Example: PIC 2-byte words**
```
$> picchick -d 16lf19197 --map tests/blink.hex
Found device: pic16lf19197
Using hexfile: tests/blink.hex
  ADDR |   x0    x1    x2    x3    x4    x5    x6    x7    x8    x9    xA    xB    xC    xD    xE    xF 
-------+------------------------------------------------------------------------------------------------
    x0 | x3180 x2802 x3187 x2FFD                                                                        
  x790 |                                           x3187 x27A7 x3187 x0159 x170C x3200 x3200 x0000 x0159
  x7A0 | x130C x3200 x3200 x0000 x2F9A x3180 x2802 x0140 x0198 x0199 x019A x019B x019C x019D x0159 x0190
  x7B0 | x0191 x0140 x0192 x0193 x0194 x0195 x0196 x0197 x0159 x018E x018F x017E x01B8 x01C3 x01CE x01D9
  x7C0 | x01E4 x017C x01D0 x01DB x017E x01B9 x01C4 x01CF x01DA x01E5 x017C x01D1 x01DC x01E7 x017E x01BA
  x7D0 | x01C5 x01D0 x01DB x01E6 x017C x01D2 x01DD x01E8 x30FF x017E x00BB x30FF x00C6 x30FF x00D1 x30FF
  x7E0 | x00DC x30FF x00E7 x30FF x017C x00D3 x30FF x00DE x30FF x00E9 x30FF x017E x00BC x30FF x00C7 x30FF
  x7F0 | x00D2 x30FF x00DD x30FF x00E8 x30FF x017C x00D4 x30FF x00DF x30FF x00EA x0008 x0140 x3187 x2F97
 x8007 = x3FE8
 x8009 = x3F9F
```
