// Mistral Cat Obstacle Game - Single Channel EMG (A0 only)
// Based on BioAmp EXG Pill EMGScrolling example
// https://github.com/upsidedownlabs/BioAmp-EXG-Pill
// https://github.com/upsidedownlabs/Muscle-BioAmp-Arduino-Firmware

// Mistral Cat runs automatically and jumps when you flex your muscle!
// Collect coins and avoid obstacles. Game gets harder over time.

// Samples per second
#define SAMPLE_RATE 500

// Make sure to set the same baud rate on your Serial Monitor/Plotter
#define BAUD_RATE 115200

// Using only A0 analog pin (EXG pill fried compatibility)
#define INPUT_PIN A0

// CH1 status LED (using built-in LED on pin 13)
#define CH1_STATUS_LED 13

// Envelope buffer size
// High value -> smooth but less responsive
// Low value -> not smooth but responsive
#define BUFFER_SIZE 64

// Circular buffer and sum for envelope detection
int circular_buffer[BUFFER_SIZE];
int data_index, sum;

// Jump settings
#define JUMP_THRESHOLD 5  // EMG envelope threshold to trigger jump (lower = more sensitive)
#define JUMP_COOLDOWN 500   // Minimum time between jumps (milliseconds)

// Jump state
unsigned long lastJumpTime = 0;
bool canJump = true;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);

  // Initialize input pin
  pinMode(INPUT_PIN, INPUT);
  
  // Initialize status LED
  pinMode(CH1_STATUS_LED, OUTPUT);
  digitalWrite(CH1_STATUS_LED, LOW);
  
  // Initialize LED bar pins (Muscle BioAmp Shield v0.3: pins 8-13)
  // Set to OUTPUT and LOW to prevent floating (which causes LEDs to flicker)
  for (int i = 8; i <= 13; i++) {
    pinMode(i, OUTPUT);
    digitalWrite(i, LOW);
  }
  
  // Initialize circular buffer
  for (int i = 0; i < BUFFER_SIZE; i++) {
    circular_buffer[i] = 0;
  }
  data_index = 0;
  sum = 0;
  
  Serial.println("Mistral Cat Obstacle Game - Ready!");
  Serial.println("Flex to jump!");
}

void loop() {
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
    
    // Check if cooldown has passed (allows new jump)
    unsigned long current_time = millis();
    if (!canJump && (current_time - lastJumpTime >= JUMP_COOLDOWN)) {
      canJump = true;
      digitalWrite(CH1_STATUS_LED, LOW);
    }
    
    // Check for jump - send 1 only when threshold exceeded AND can jump
    if (envelope > JUMP_THRESHOLD && canJump) {
      // Trigger jump
      Serial.println("1");  // Send jump signal
      digitalWrite(CH1_STATUS_LED, HIGH);
      lastJumpTime = current_time;
      canJump = false;
    } else {
      // Not jumping
      Serial.println("0");  // Send no-jump signal
    }
    
    // Also send envelope for debugging (commented out by default for cleaner serial)
    // Serial.print(envelope);
    // Serial.println();
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

// Band-Pass Butterworth IIR digital filter
// Sampling rate: 500.0 Hz, frequency: [74.5, 149.5] Hz
// Filter is order 4, implemented as second-order sections (biquads)
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
