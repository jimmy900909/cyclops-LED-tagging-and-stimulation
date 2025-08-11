#include <Cyclops.h>

Cyclops cyclops0(CH0, 300);  // Initialize Cyclops LED driver

void setup() {
    Serial.begin(115200);  // Start USB Serial communication
    Cyclops::begin();      // Initialize Cyclops
}

void loop() {
    if (Serial.available()) {
        char command = Serial.read();  // Read incoming serial data
        
        if (command == '1') {
            cyclops0.dac_load_voltage(4095);  // Turn LED ON (Full Brightness)

        } else if (command == '0') {
            cyclops0.dac_load_voltage(0);  // Turn LED OFF
        }
    }

}
