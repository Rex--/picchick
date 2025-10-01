Various Test Files for picchick
===============================


Blink Test Hexfiles
-------------------
These files contain super basic programs that toggle an I/O pin.

- `blink-pic14e-pic161454.hex` -
    Uses the internal oscillator with default POR values (500 kHz) to blink
    **RA5** (pin 1)

- `blink-pic14ex-pic16lf19197.hex` -
    Uses the internal oscillator with the HFINTOSC set to 1mHz to blink
    **RG7** (pin 19)

- `blink-pic18-pic18f25q10.hex` -
    Uses the internal oscillator with the HFINTOSC set to 1mHz to blink
    **RB5** (pin 26)


INI Data Files
--------------
Device config files for various MCUs.

- `xc8-*.ini` -
    These are device files provided by Microchip and distributed in
    Device Family Packs (DFUs).

- `custom-*.ini` -
    Custom device file examples.
