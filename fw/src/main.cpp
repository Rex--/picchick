#include <Arduino.h>

#include "picchick.h"
#include "icsp_commands.h"
#include "serial_commands.h"

void setup() {
  init_icsp();

  Serial.begin(9600);
  while (!Serial) {
    ;
  }
}

uint8_t status = STATUS_DISCONNECTED;

void loop() {
  if (Serial.available() > 0) {
    status = handle_command();
  }
}