#include <Arduino.h>

#include "icsp_commands.h"

uint8_t icsp_startup_key_bytes[] = ICSP_STARTUP_KEY;

void icsp_init_pins(void)
{
    pinMode(PIN_ICSP_DAT, OUTPUT); // Configure our DAT pin as an output and set it low
    digitalWrite(PIN_ICSP_DAT, LOW);

    pinMode(PIN_ICSP_CLK, OUTPUT); // COnfigure our CLK pin and set it low
    digitalWrite(PIN_ICSP_CLK, LOW);

    pinMode(PIN_ICSP_MCLR, OUTPUT); // Configure our reset pin and set it high
    digitalWrite(PIN_ICSP_MCLR, HIGH);
}

void icsp_reset_pins(void)
{
    pinMode(PIN_ICSP_DAT, INPUT); // Configure our DAT pin as an input

    pinMode(PIN_ICSP_CLK, INPUT); // COnfigure our CLK pin as an input

    pinMode(PIN_ICSP_MCLR, INPUT); // Configure our reset pin as input
}


void icsp_enter_program_mode(void)
{
    // To enter program mode, we set MCLR low and shift in the 32 bit startup key
    digitalWrite(PIN_ICSP_MCLR, LOW);

    delayMicroseconds(ICSP_DELAY_ENTH); // Wait a bit

    int i, j;
    for (i=0; i < 4; i++) { // Start with the most significant byte
        for (j=7; j >= 0; j--) { // And the most significant bit
            digitalWrite(PIN_ICSP_CLK, HIGH); // CLK High
            digitalWrite(PIN_ICSP_DAT, bitRead(ICSP_STARTUP_KEY[i],j)); // Set data bit
            delayMicroseconds(ICSP_DELAY_CKH);
            digitalWrite(PIN_ICSP_CLK, LOW);    // CLK Low
            delayMicroseconds(ICSP_DELAY_CKL);
        }
    }
}

void icsp_exit_program_mode(void)
{
    // To exit program mode, we set mclr high
    digitalWrite(PIN_ICSP_MCLR, HIGH);
}

void icsp_write_command(uint8_t command)
{
    // Writes a command to the icsp interface, must be in programming mode.
    // It is the callers responsibilty to send or receive any data that follows the command
    int command_bit;
    for (command_bit=7;command_bit>=0;command_bit--) { // Start with the MSBit of the command
        digitalWrite(PIN_ICSP_CLK, HIGH); // CLK High
        digitalWrite(PIN_ICSP_DAT, bitRead(command, command_bit)); // Set data bit
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);    // CLK Low
        delayMicroseconds(ICSP_DELAY_CKL);
    }
}

void icsp_write_address(uint16_t *address) {

    int i;
    // Clock out 7 clock dummy clocks (1 start and 6 padding 0's)
    for (i=0; i<7; i++) {
        digitalWrite(PIN_ICSP_CLK, HIGH);
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);
        delayMicroseconds(ICSP_DELAY_CKL);
    }

    // Clock out our 16-bit address
    for (i=15; i>=0; i--) {
        digitalWrite(PIN_ICSP_CLK, HIGH);
        digitalWrite(PIN_ICSP_DAT, bitRead(*address, i));
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);
        delayMicroseconds(ICSP_DELAY_CKL);
    }

    // Clock out our stop bit totalling 24 bits
    digitalWrite(PIN_ICSP_CLK, HIGH);
    digitalWrite(PIN_ICSP_DAT, LOW);
    delayMicroseconds(ICSP_DELAY_CKH);
    digitalWrite(PIN_ICSP_CLK, LOW);
    delayMicroseconds(ICSP_DELAY_CKL);
}

void icsp_write_payload(uint16_t *payload)
{
    int i;

    // Clock out 9 dummy clocks
    for (i=0; i<9; i++) {
        digitalWrite(PIN_ICSP_CLK, HIGH);
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);
        delayMicroseconds(ICSP_DELAY_CKL);
    }

    // Clock out our 14-bit payload
    for (i=13; i>=0; i--) {
        digitalWrite(PIN_ICSP_CLK, HIGH);
        digitalWrite(PIN_ICSP_DAT, bitRead(*payload, i));
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);
        delayMicroseconds(ICSP_DELAY_CKL);
    }

    // Clock out our stop bit totalling 24 bits
    digitalWrite(PIN_ICSP_CLK, HIGH);
    digitalWrite(PIN_ICSP_DAT, LOW);
    delayMicroseconds(ICSP_DELAY_CKH);
    digitalWrite(PIN_ICSP_CLK, LOW);
    delayMicroseconds(ICSP_DELAY_CKL);
}

uint16_t icsp_read_word(void) {
    int i;
    uint16_t word = 0;

    // Configure our DAT pin as input
    pinMode(PIN_ICSP_DAT, INPUT);


    // Clock out 9 dummy clocks
    for (i=0; i<9; i++) {
        digitalWrite(PIN_ICSP_CLK, HIGH);
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);
        delayMicroseconds(ICSP_DELAY_CKL);
    }

    // Clock out 14 cycles and read the data bits
    for (i=13; i>=0; i--) {
        digitalWrite(PIN_ICSP_CLK, HIGH);
        delayMicroseconds(ICSP_DELAY_CKH);
        digitalWrite(PIN_ICSP_CLK, LOW);
        word = word | (digitalRead(PIN_ICSP_DAT) << i);
        delayMicroseconds(ICSP_DELAY_CKL);
    }

    // Clock out our stop bit totalling 24 bits
    digitalWrite(PIN_ICSP_CLK, HIGH);
    delayMicroseconds(ICSP_DELAY_CKH);
    digitalWrite(PIN_ICSP_CLK, LOW);
    delayMicroseconds(ICSP_DELAY_CKL);

    // Set DAT pin back to output
    pinMode(PIN_ICSP_DAT, OUTPUT);

    // return result
    return word;
}