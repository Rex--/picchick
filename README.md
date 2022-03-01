# picchick
A utility to program PIC microcontrollers


## Overview

piccchick is a commandline utility written in python that attempts to implement Microchip's PIC ICSP Low-Voltage with just a simple AVR device.

It attempts to do the majority of the work on the host computer, and sends a simple byte stream to an arduino for converting directly into digital signals.

## Usage

```
usage: picchick.py [options] [hexfile]

A utility for programming PIC19196 microcontrollers

positional arguments:
  hexfile               path to the hexfile

options:
  -h, --help            show this help message and exit
  -f, --flash           flash hexfile onto the device
  --read addr           read specified address or chunk of memory
  --write addr word     write word to specified address or chunk of memory
  --erase addr          erase specified address or chunk of memory
  -p port, --port port  programmer serial port
  --baud baud           serial connection baudrate
  --map                 display the hexfile
  --list-ports          list available serial ports
  --list-devices        list available device configurations
```


#### Files:
- `hexfile.py` - This file contains all functions related to manipulating hexfiles
- `programmer.py` - This module communicates with the programmer over serial. Exposes some simple functions to send and receive data.
- `picchick.py` - This module implements the CLI.
