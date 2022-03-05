#include <Arduino.h>

#include "picchick.h"
#include "serial_commands.h"
#include "icsp_commands.h"

uint8_t input_buffer[INPUT_BUFFER_SIZE];
size_t recv_size;


bool cmd_is(const char *cmd)
{
    if (memcmp(input_buffer, cmd, strlen(cmd)) == 0) {
        return true;
    }
    return false;
}

void cmd_resp(const char *resp)
{
    Serial.write(resp);
    Serial.write(SERIAL_CMD_SEP);
}

void cmd_resp_error(uint8_t *msg, uint8_t msg_len)
{
    Serial.write(SERIAL_CMD_ERROR);
    Serial.write(SERIAL_CMD_SEP);
    Serial.write(msg, msg_len);
}

uint8_t cmd_hello(void)
{
    icsp_init_pins();
    cmd_resp(SERIAL_CMD_HELLO);
    return STATUS_CONNECTED;
}

uint8_t cmd_bye(void)
{
    icsp_reset_pins();
    cmd_resp(SERIAL_CMD_BYE);
    return STATUS_DISCONNECTED;
}

uint8_t cmd_start(void)
{
    icsp_enter_program_mode();
    cmd_resp(SERIAL_CMD_OK);
    return STATUS_PROGRAM;
}

uint8_t cmd_stop(void)
{
    icsp_exit_program_mode();
    cmd_resp(SERIAL_CMD_OK);
    return STATUS_CONNECTED;
}

uint8_t cmd_addr(void)
{
    Serial.readBytes(input_buffer, 2);
    uint16_t address = (input_buffer[0] << 8) | input_buffer[1];
    icsp_write_command(ICSP_CMD_ADDR_LOAD);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_address(&address);
    cmd_resp(SERIAL_CMD_OK);
    return STATUS_PROGRAM;
}

uint8_t cmd_word(void)
{
    Serial.readBytes(input_buffer, 5);
    if (input_buffer[2] != ':') {
        cmd_resp_error(input_buffer, 5);
        return STATUS_PROGRAM;
    }
    uint16_t address = (input_buffer[0] << 8) | input_buffer[1];
    uint16_t word = (input_buffer[3] << 8) | input_buffer[4];

    // Load address
    icsp_write_command(ICSP_CMD_ADDR_LOAD);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_address(&address);
    delayMicroseconds(ICSP_DELAY_DLY);

    // Write word
    icsp_write_command(ICSP_CMD_LOAD_DATA);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_payload(&word);
    delayMicroseconds(ICSP_DELAY_DLY);

    // Begin write command
    icsp_write_command(ICSP_CMD_START_INT);
    delayMicroseconds(ICSP_DELAY_PINT_CW);

    // verify data

    // Return response
    cmd_resp(SERIAL_CMD_OK);

    return STATUS_PROGRAM;
}

uint8_t cmd_row(void)
{
    // Get address
    recv_size = Serial.readBytesUntil(SERIAL_CMD_SEP, input_buffer, INPUT_BUFFER_SIZE);
    if (recv_size != 2) {
        cmd_resp_error(input_buffer, recv_size);
        return STATUS_PROGRAM;
    }
    uint16_t address = (input_buffer[0] << 8) | input_buffer[1];
    
    // Get row
    recv_size = Serial.readBytes(input_buffer, 128);
    if (recv_size != 128) {
        cmd_resp_error(input_buffer, recv_size);
        return STATUS_PROGRAM;
    }

    // Load address
    icsp_write_command(ICSP_CMD_ADDR_LOAD);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_address(&address);
    delayMicroseconds(ICSP_DELAY_DLY);

    // Write 63 words of data
    uint16_t word;
    uint8_t offset;
    for (offset=0; offset < 126; offset += 2) {
        // Write word
        word = (input_buffer[offset] << 8) | input_buffer[offset+1];
        icsp_write_command(ICSP_CMD_LOAD_DATA_INC);
        delayMicroseconds(ICSP_DELAY_DLY);
        icsp_write_payload(&word);
        delayMicroseconds(ICSP_DELAY_DLY);
    }

    //Write 64th word without incrementing address
    word = (input_buffer[offset] << 8) | input_buffer[offset+1];
    icsp_write_command(ICSP_CMD_LOAD_DATA);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_payload(&word);
    delayMicroseconds(ICSP_DELAY_DLY);


    // Begin write command
    icsp_write_command(ICSP_CMD_START_INT);
    delayMicroseconds(ICSP_DELAY_PINT_PM);

    // verify data

    // Return response
    cmd_resp(SERIAL_CMD_OK);

    return STATUS_PROGRAM;
}

uint8_t cmd_erase(void)
{
    recv_size = Serial.readBytes(input_buffer, 2);
    if (recv_size != 2) {
        cmd_resp_error(input_buffer, recv_size);
    }

    uint16_t address = (input_buffer[0] << 8) | input_buffer[1];
    uint8_t cmd = ICSP_CMD_ERASE_ROW;
    uint16_t delay_len = ICSP_DELAY_ERAR;

    // Bulk erase the whole device
    if (address == SERIAL_CMD_ERASE_ALL) {
        address = 0x8000;
        cmd = ICSP_CMD_ERASE_BULK;
        delay_len = ICSP_DELAY_ERAB;
        
    }
    // Bulk erase user flash
    else if (address == SERIAL_CMD_ERASE_FLASH) {
        address = 0x0000;
        cmd = ICSP_CMD_ERASE_BULK;
        delay_len = ICSP_DELAY_ERAB;
    }

    icsp_write_command(ICSP_CMD_ADDR_LOAD);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_address(&address);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_command(cmd);
    delayMicroseconds(delay_len);

    cmd_resp(SERIAL_CMD_OK);
    return STATUS_PROGRAM;
}

uint8_t cmd_read(void)
{
    recv_size = Serial.readBytes(input_buffer, 2);
    if (recv_size != 2) {
        cmd_resp_error(input_buffer, recv_size);
    }

    uint16_t address = (input_buffer[0] << 8) | input_buffer[1];

    icsp_write_command(ICSP_CMD_ADDR_LOAD);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_address(&address);
    delayMicroseconds(ICSP_DELAY_DLY);
    icsp_write_command(ICSP_CMD_READ_DATA);
    delayMicroseconds(ICSP_DELAY_DLY);
    uint16_t word = icsp_read_word();

    // Return response
    cmd_resp(SERIAL_CMD_OK);
    Serial.write((word >> 8));
    Serial.write(word);
    return STATUS_PROGRAM;
}


uint8_t handle_command(void)
{
    recv_size = Serial.readBytesUntil(':', input_buffer, INPUT_BUFFER_SIZE);

    // Greeting
    if (cmd_is(SERIAL_CMD_HELLO))
        return cmd_hello();

    else if (cmd_is(SERIAL_CMD_BYE))
        return cmd_bye();

    else if (cmd_is(SERIAL_CMD_START))
        return cmd_start();

    else if (cmd_is(SERIAL_CMD_STOP))
        return cmd_stop();

    // else if (cmd_is(SERIAL_CMD_ADDR)) This doesnt really need to be a command
    //     return cmd_addr();        since we specify address in all the others    
    
    else if (cmd_is(SERIAL_CMD_WORD))
        return cmd_word();
    
    else if (cmd_is(SERIAL_CMD_ROW))
        return cmd_row();
    
    else if (cmd_is(SERIAL_CMD_ERASE))
        return cmd_erase();
    
    else if (cmd_is(SERIAL_CMD_READ))
        return cmd_read();

    Serial.write("UNKOWN:");
    Serial.write(input_buffer, recv_size);
    return 0;
}