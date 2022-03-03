







#define SERIAL_CMD_SEP ':'
#define SERIAL_CMD_OK "OK"
#define SERIAL_CMD_ERROR "ERROR"
#define SERIAL_CMD_HELLO "HELLO"
#define SERIAL_CMD_BYE "BYE"
#define SERIAL_CMD_START "START"
#define SERIAL_CMD_STOP "STOP"
#define SERIAL_CMD_ADDR "ADDR"
#define SERIAL_CMD_ROW "ROW"
#define SERIAL_CMD_WORD "WORD"
#define SERIAL_CMD_READ "READ"
#define SERIAL_CMD_ERASE "ERASE"
#define SERIAL_CMD_ERASE_ALL 0xFFFF
#define SERIAL_CMD_ERASE_FLASH 0xFFFE





















#define INPUT_BUFFER_SIZE 128

#define PICCHICK_GREETING "HELLO"

#define SERIAL_CMD_FLASH "FLASH"


int handle_connection(void);

uint8_t handle_command(void);