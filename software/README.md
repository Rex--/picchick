# picchick
A utility to aid in programming PIC microcontrollers


## Overview

`piccchick` is a commandline utility written in python that attempts to implement Microchip's ICSP Low-Voltage with just a simple AVR device.

The function is the same as `avrdude`, i.e. to provide a way to flash a compiled .hex file onto a microcontroller. The typical development stack involving picchick looks like:

    Development (nano)    >    Compiling (xc8-cc)    >    Flashing (picchick)


## Installation

### Requirements
- **`xc8` compiler installed to one of**:
> (linux) /opt/microchip/xc8/

- **python >= 3.10**
  - pyserial

- **Arduino flashed with programmer firmware**

## Usage

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
  -p port, --port port  programmer serial port
  --baud baud           serial connection baudrate
  --map                 display the hexfile
  --list-ports          list available serial ports

flag arguments:
  [addr]:		device memory address in hexadecimal
	'all'		    all device memory areas
	'flash'		user flash area
```