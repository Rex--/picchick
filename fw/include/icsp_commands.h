
// ICSP Pins
#define PIN_ICSP_DAT 12
#define PIN_ICSP_CLK 11
#define PIN_ICSP_MCLR 10

// ICSP Commands

#define ICSP_STARTUP_KEY "MCHP"

#define ICSP_CMD_ADDR_LOAD 0x80
#define ICSP_CMD_ERASE_BULK 0x18
#define ICSP_CMD_ERASE_ROW 0xF0
#define ICSP_CMD_LOAD_DATA_INC 0x02
#define ICSP_CMD_LOAD_DATA 0x00
#define ICSP_CMD_READ_DATA_INC 0xFE
#define ICSP_CMD_READ_DATA 0xFC
#define ICSP_CMD_ADDR_INC 0xF8
#define ICSP_CMD_START_INT 0xE0
#define ICSP_CMD_START_EXT 0xC0
#define ICSP_CMD_STOP_EXT 0x82

// ICSP Timings

#define ICSP_DELAY_ENTH 250
// #define ICSP_DELAY_ENTS 10
#define ICSP_DELAY_CKL 1
#define ICSP_DELAY_CKH 1
// #define ICSP_DELAY_DS 10
// #define ICSP_DELAY_DH 10
// #define ICSP_DELAY_TCO 10
// #define ICSP_DELAY_LZD 10
// #define ICSP_DELAY_HZD 10
#define ICSP_DELAY_DLY 3
#define ICSP_DELAY_ERAB 9000  // Bulk erase time takes max 8.4 ms
#define ICSP_DELAY_ERAR 3500    // Row erase time is max 2.8 ms
#define ICSP_DELAY_PINT_PM 3500 // Program memory internal timed takes max 2.8ms
#define ICSP_DELAY_PINT_CW 6000 // Configuration word internally timed takes max 5.6 ms

void init_icsp(void);

void icsp_enter_program_mode(void);
void icsp_exit_program_mode(void);

void icsp_write_command(uint8_t command);

void icsp_write_address(uint16_t *address);

void icsp_write_payload(uint16_t *payload);

uint16_t icsp_read_word(void);
