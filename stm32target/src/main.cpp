#include <Arduino.h>

// to program stm32f1x with openocd:
// reset halt; flash write_image erase unlock firmware.bin 0x08000000; program firmware.elf verify reset

void setup() {
  Serial.begin(9600);  // tx on A2 by default
  pinMode(PC13, OUTPUT);
}

void loop() {
  int loops = 0;
  int count = 0;
  int i = 0;
  int j = 0;

  digitalWrite(PC13, LOW);

  while(true) {
    count = 0;
    i = 0;
    j = 0;
    for(i=0; i < 5000; i++) {
      for(j=0; j < 5000; j++) {
        count++;
      }
    }
    Serial.print(count);
    Serial.print(" ");
    Serial.print(i);
    Serial.print(" ");
    Serial.print(j);
    Serial.print(" ");
    Serial.println(loops++);

    if(count != 25000000)
      break;
  }

  // should not get here
  Serial.println("#######");
  Serial.println("SUCCESSFUL GLITCH");
  Serial.println("#######");

  while(true) {
    digitalWrite(PC13, HIGH);
    delay(500);              
    digitalWrite(PC13, LOW);
    delay(500);
  }
}
