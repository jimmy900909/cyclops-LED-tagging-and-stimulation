#include <Cyclops.h>
#include <math.h>

Cyclops cyclops0(CH0, 1000);  // Initialize Cyclops LED driver

// Gaussian pulse parameters
const int num_points = 50;
const unsigned long pulse_duration_ms = 1000; // 1 second
const unsigned long step_delay_us = (pulse_duration_ms * 1000) / num_points;
const uint16_t max_dac_value = 4095;  // Full brightness (5V)

bool trigger_gaussian = false;

void setup() {
    Serial.begin(115200);
    Cyclops::begin();
}

void loop() {
    if (Serial.available()) {
        char command = Serial.read();
        
        if (command == '1') {
            trigger_gaussian = true;
        } else if (command == '0') {
            cyclops0.dac_load_voltage(0);  // Immediate OFF
            trigger_gaussian = false;     // Stop pending pulses
        }
    }

    if (trigger_gaussian) {
        generate_gaussian_pulse();
        trigger_gaussian = false;  // One pulse per '1' command
    }
}

void generate_gaussian_pulse() {
    const float sigma = 0.2;  // Standard deviation of Gaussian
    const float center = 0.5; // Center of Gaussian

    for (int i = 0; i < num_points; i++) {
        float x = (float)i / (num_points - 1);
        float gaussian = exp(-pow(x - center, 2) / (2 * sigma * sigma));
        uint16_t voltage = (uint16_t)(gaussian * max_dac_value);
        
        cyclops0.dac_load_voltage(voltage);
        delayMicroseconds(step_delay_us);
    }

    cyclops0.dac_load_voltage(0); // Make sure LED is OFF after the pulse
}
