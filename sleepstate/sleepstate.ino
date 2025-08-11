#include <Cyclops.h>
#include <math.h>

Cyclops cyclops0(CH0, 600);  // Cyclops LED driver

// Gaussian step parameters
const int num_steps = 100;
const unsigned long pulse_duration_ms = 1000;
const unsigned long step_duration_ms = pulse_duration_ms / num_steps;
const uint16_t max_dac_value = 4096;
uint16_t voltage_steps[num_steps];

// Loop timing
const unsigned long pulse_interval_ms = 3000;
unsigned long last_pulse_time = 0;
bool loop_enabled = false;

void setup() {
    Serial.begin(115200);
    Cyclops::begin();
    Serial.println("Send '1' to start stepped pulsing, '0' to stop.");

    // Precompute stepped Gaussian values
    const float sigma = 0.2;
    const float center = 0.5;
    for (int i = 0; i < num_steps; i++) {
        float x = (float)i / (num_steps - 1);
        float gaussian = exp(-pow(x - center, 2) / (2 * sigma * sigma));
        voltage_steps[i] = (uint16_t)(gaussian * max_dac_value);
    }
}

void loop() {
    // Serial input to toggle pulsing
    if (Serial.available()) {
        char command = Serial.read();
        if (command == '1') {
            loop_enabled = true;
            Serial.println("✅ Stepped Gaussian pulsing started.");
        } else if (command == '0') {
            loop_enabled = false;
            Serial.println("🛑 Stepped Gaussian pulsing stopped.");
        }
    }

    // Pulse loop
    unsigned long current_time = millis();
    if (loop_enabled && (current_time - last_pulse_time >= pulse_interval_ms)) {
        generate_stepped_gaussian_pulse();
        last_pulse_time = current_time;
    }
}

void generate_stepped_gaussian_pulse() {
    for (int i = 0; i < num_steps; i++) {
        cyclops0.dac_load_voltage(voltage_steps[i]);
        delay(step_duration_ms);
    }
    cyclops0.dac_load_voltage(0);  // Turn off after pulse
}
