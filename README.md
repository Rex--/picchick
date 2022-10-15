# picchick
`piccchick` is a commandline utility written in python that interacts with
various programmers in order to flash the memory of a microcontroller.

The function is the same as `avrdude`, i.e. to provide a way to flash a compiled
.hex file onto a microcontroller. The typical development stack involving
picchick looks like:

> Developing (nano)      >   Compiling (xc8-cc)    >    Flashing (picchick)


The latest documentation is available in the `docs/` folder, or hosted online
at [rex.mckinnon.ninja/picchick](https://rex.mckinnon.ninja/picchick)


## Installation

### Requirements
- **xc8 compiler**
  - Available from [Microchip's website](https://www.microchip.com/en-us/tools-resources/develop/mplab-xc-compilers/downloads-documentation)
- **python >= 3.10**
  - pyserial
- **Compatible serial programmer**
  - Checkout the docs for a list of compatible programmers.


### From PyPi
`picchick` can be installed using pip:
```sh
$ pip install picchick
```

### From Source
Building the latest git version is as simple as pip installing the repo
directory. The -e, --editable flag can be added so a `git pull` will update the
`picchick` command automatically.
```sh
$ git clone https://github.com/Rex--/picchick.git
$ cd picchick/
$ pip install [-e] .
$ picchick -h
```

Instead of installing the package, `picchick` can also be run as a python module:
```sh
$ python -m picchick -h
```
A wrapper script is provided that does this, providing a bit cleaner interface:
```sh
$ chmod +x picchick.sh
$ ./picchick.sh -h
```
NOTE: You may have to install pyserial for the above methods.

## Usage
```sh
$ picchick -h
usage: picchick [--read addr] [--write addr word] [--erase [addr]] [--verify] [-f] [--map] [--list-ports] [hexfile]
       picchick -d <mcu> -c <programmer> -P <port> -B <baud> [--erase] [--verify] [--reset] -f <hexfile>
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
  --verify              verify device memory
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
```sh
$ picchick -d <mcu> -c <programmer> -P <port> -B <baud> [--erase] [--verify] -f <hexfile>
# e.g. Flash blink.hex to a pic16lf19197 using a picstick
$ picchick -c picstick -d 16lf19197 -P /dev/ttyACM0 -B 115200 --erase -f blink.hex
```


## Resources

**Documentation:** https://rex.mckinnon.ninja/picchick

**Github:** https://github.com/rex--/picchick

**PyPi:** https://pypi.org/project/picchick/


## Copying

Copyright (C) 2022 Rex McKinnon \
This software is released under the University of Illinois/NCSA
Open Source License. Check the LICENSE file for more details.
