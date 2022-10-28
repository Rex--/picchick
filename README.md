# picchick
`picchick` is a command-line utility used for programming and debugging
microcontrollers.

The function is the same as `avrdude`, i.e. to provide a way to flash a compiled
.hex file onto a microcontroller. The typical development stack involving
picchick looks like:

> Developing (nano)      >   Compiling (xc8-cc)    >    Flashing (picchick)


The latest documentation is available in the `docs/` folder, or hosted online
at [rex.mckinnon.ninja/picchick](https://rex.mckinnon.ninja/picchick)


## Installation

### Requirements
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
usage: picchick [-d <mcu>] [-c <programmer>] [-r <addr> [len] | -w <addr> <word> | -f] [-e [addr]] [-v] [hexfile]
       picchick [-d <mcu>] [--map | --list-ports] [hexfile]

A utility for programming and debugging microcontrollers.

positional arguments:
  hexfile               path to a hexfile

options:
  -c programmer         type of programmer
  -d mcu, --device mcu  device to be programmed
  -h, --help            print this message and exit

actions:
  -r, --read addr [len]   read bytes from specified address
  -w, --write addr word   write word to specified address
  -f, --flash             flash hexfile onto the device
  -e, --erase [addr]      erase device or specified address
  -v, --verify            verify device memory
  --map                   display the hexfile
  --list-ports            list available serial ports
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
