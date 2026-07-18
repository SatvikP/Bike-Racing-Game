// Mistral Cat Obstacle Game - Single Channel EMG
// Based on BioAmp EXG Pill EMGScrolling example
// https://github.com/upsidedownlabs/BioAmp-EXG-Pill

// Samples per second
#define SAMPLE_RATE 500

// Make sure to set the same baud rate on your Serial Monitor/Plotter
#define BAUD_RATE 115200

// Change if your sensor is connected to a different analog pin
#define INPUT_PIN A0

// Button to start the serial transaction (SW1)
const int buttonPin = 4;

// LED to show serial transaction status
const int ledPin = 8;

// Envelope buffer size
// High value -> smooth but less responsive
// Low value -> not smooth but responsive
#define BUFFER_SIZE 64

int circular_buffer[BUFFER_SIZE];
int data_index, sum;

// Device working status variables
int ledState = LOW;
int buttonState;
int lastButtonState = LOW;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Jump settings - EDGE-BASED DETECTION
#define JUMP_THRESHOLD 50  // EMG envelope threshold to trigger jump
#define JUMP_COOLDOWN 500   // Minimum time between jumps (milliseconds)

unsigned long lastJumpTime = 0;
bool jumpTriggered = false;  // Edge detection: jump currently triggered
bool lastStateAboveThreshold = false;  // Previous state for edge detection

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);

  // Initialize input pin
  pinMode(INPUT_PIN, INPUT);

  // Initialize button and status LED
  pinMode(buttonPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, ledState);

  // Initialize circular buffer
  for (int i = 0; i < BUFFER_SIZE; i++) {
    circular_buffer[i] = 0;
  }
  data_index = 0;
  sum = 0;
}

void loop() {
  // Button debounce logic
  int reading = digitalRead(buttonPin);
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      if (buttonState == HIGH) {
        ledState = !ledState;
      }
    }
  }
  digitalWrite(ledPin, ledState);
  lastButtonState = reading;

  // Calculate elapsed time
  static unsigned long past = 0;
  unsigned long present = micros();
  unsigned long interval = present - past;
  past = present;

  // Run timer
  static long timer = 0;
  timer -= interval;

  // Sample and get envelope
  if (timer < 0) {
    timer += 1000000 / SAMPLE_RATE;

    // Raw EMG value
    int sensor_value = analogRead(INPUT_PIN);

    // Filtered EMG signal
    int signal = EMGFilter(sensor_value);

    // EMG envelope
    int envelope = getEnvelope(abs(signal));

    // Only send serial data when ledState is HIGH (button pressed)
    if (ledState == HIGH) {
      bool currentAboveThreshold = (envelope > JUMP_THRESHOLD);
      unsigned long current_time = millis();

      // EDGE DETECTION: Rising edge (spike start) triggers jump
      if (currentAboveThreshold && !lastStateAboveThreshold && !jumpTriggered) {
        // Check cooldown
        if (current_time - lastJumpTime >= JUMP_COOLDOWN) {
          Serial.println("1");  // SINGLE PULSE: Jump triggered
          jumpTriggered = true;
          lastJumpTime = current_time;
        }
      }

      // Reset when signal drops below threshold (flex ended)
      if (!currentAboveThreshold && lastStateAboveThreshold) {
        jumpTriggered = false;
      }

      // Always send "0" when not actively triggering a jump
      if (!jumpTriggered) {
        Serial.println("0");
      }

      // Update last state for next iteration
      lastStateAboveThreshold = currentAboveThreshold;
    }
  }
}

// Envelope detection algorithm
// Returns smoothed absolute value of EMG signal
int getEnvelope(int abs_emg) {
  sum -= circular_buffer[data_index];
  sum += abs_emg;
  circular_buffer[data_index] = abs_emg;
  data_index = (data_index + 1) % BUFFER_SIZE;
  return (sum / BUFFER_SIZE) * 2;
}

// Band-Pass Butterworth IIR digital filter, generated using filter_gen.py.
// Sampling rate: 500.0 Hz, frequency: [74.5, 149.5] Hz.
// Filter is order 4, implemented as second-order sections (biquads).
// Reference:
// https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html
// https://courses.ideate.cmu.edu/16-223/f2020/Arduino/FilterDemos/filter_gen.py
float EMGFilter(float input) {
  float output = input;
  
  // First biquad section
  {
    static float z1, z2;  // filter section state
    float x = output - 0.05159732 * z1 - 0.36347401 * z2;
    output = 0.01856301 * x + 0.03712602 * z1 + 0.01856301 * z2;
    z2 = z1;
    z1 = x;
  }
  
  // Second biquad section
  {
    static float z1, z2;  // filter section state
    float x = output - -0.53945795 * z1 - 0.39764934 * z2;
    output = 1.00000000 * x + -2.00000000 * z1 + 1.00000000 * z2;
    z2 = z1;
    z1 = x;
  }
  
  // Third biquad section
  {
    static float z1, z2;  // filter section state
    float x = output - 0.47319594 * z1 - 0.70744137 * z2;
    output = 1.00000000 * x + 2.00000000 * z1 + 1.00000000 * z2;
    z2 = z1;
    z1 = x;
  }
  
  // Fourth biquad section
  {
    static float z1, z2;  // filter section state
    float x = output - -1.00211112 * z1 - 0.74520226 * z2;
    output = 1.00000000 * x + -2.00000000 * z1 + 1.00000000 * z2;
    z2 = z1;
    z1 = x;
  }
  
  return output;
}
