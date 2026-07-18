// Mistral Cat Obstacle Game - Single Channel EMG (A0 only)
// Based on BioAmp EXG Pill EMGScrolling example
// https://github.com/upsidedownlabs/BioAmp-EXG-Pill

// Mistral Cat runs automatically and jumps when you flex your muscle!
// Press button SW1 (pin 4) to start/stop measuring signals.
// Collect coins and avoid obstacles. Game gets harder over time.

// Samples per second
#define SAMPLE_RATE 500

// Make sure to set the same baud rate on your Serial Monitor/Plotter
#define BAUD_RATE 115200

// Change if your sensor is connected to a different analog pin
#define INPUT_PIN A0

// Button to start the serial transaction (SW1)
const int buttonPin = 4;

// LED to show serial transaction status
// Note: Using pin 7 to avoid conflict with LED bar (pins 8-13)
const int ledPin = 7;

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

// LED bar pins (Muscle BioAmp Shield v0.3)
int led_bar[] = { 8, 9, 10, 11, 12, 13 };
int total_leds = sizeof(led_bar) / sizeof(led_bar[0]);

// LED bar scaling
#define EMG_ENVELOPE_BASELINE 4
#define EMG_ENVELOPE_DIVIDER 4

// Jump settings
#define JUMP_THRESHOLD 50  // EMG envelope threshold to trigger jump
#define JUMP_COOLDOWN 500   // Minimum time between jumps (milliseconds)

// Jump state
unsigned long lastJumpTime = 0;
bool canJump = true;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);

  // Initialize input pin
  pinMode(INPUT_PIN, INPUT);
  
  // Initialize button and status LED (from EMGScrolling reference)
  pinMode(buttonPin, INPUT);
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, ledState);
  
  // Initialize all the LED bar pins
  for (int i = 0; i < total_leds; i++) {
    pinMode(led_bar[i], OUTPUT);
  }
  
  // Initialize circular buffer
  for (int i = 0; i < BUFFER_SIZE; i++) {
    circular_buffer[i] = 0;
  }
  data_index = 0;
  sum = 0;
  
  Serial.println("Mistral Cat Obstacle Game - Ready!");
  Serial.println("Press SW1 (pin 4) to start measuring signals.");
}

void loop() {
  // Button debounce logic (from EMGScrolling reference)
  int reading = digitalRead(buttonPin);
  if (reading != lastButtonState) {
    // reset the debouncing timer
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    // if the button state has changed:
    if (reading != buttonState) {
      buttonState = reading;

      // only toggle the LED if the new button state is HIGH
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
    
    // Update LED bar graph to show muscle activity
    for (int i = 0; i < total_leds; i++) {
      if (i > (envelope / EMG_ENVELOPE_DIVIDER - EMG_ENVELOPE_BASELINE)) {
        digitalWrite(led_bar[i], LOW);
      } else {
        digitalWrite(led_bar[i], HIGH);
      }
    }
    
    // Only send serial data when ledState is HIGH (button pressed)
    if (ledState == HIGH) {
      // Check if cooldown has passed (allows new jump)
      unsigned long current_time = millis();
      if (!canJump && (current_time - lastJumpTime >= JUMP_COOLDOWN)) {
        canJump = true;
      }
      
      // Check for jump - send jump signal when threshold exceeded AND can jump
      if (envelope > JUMP_THRESHOLD && canJump) {
        // Trigger jump
        Serial.println("1");  // Send jump signal
        lastJumpTime = current_time;
        canJump = false;
      } else {
        // Not jumping
        Serial.println("0");  // Send no-jump signal
      }
      
      // Also output envelope for calibration (comment out if not needed)
      // Serial.print("ENVELOPE:");
      // Serial.println(envelope);
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
