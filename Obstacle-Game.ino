// Mistral Cat Obstacle Game - Single Channel EMG (A0 only)
// Based on Muscle BioAmp Shield example
// https://github.com/upsidedownlabs/DIY-Muscle-BioAmp-Shield

// Mistral Cat runs automatically and jumps when you flex your muscle!
// Collect coins and avoid obstacles. Game gets harder over time.

// Samples per second
#define SAMPLE_RATE 500

// Make sure to set the same baud rate on your Serial Monitor/Plotter
#define BAUD_RATE 115200

// Using only A0 analog pin (EXG pill fried compatibility)
#define INPUT_PIN A0

// Envelope buffer size for smoothing
#define BUFFER_SIZE 32

// EMG Threshold - lower = more sensitive
// Start low and increase if getting false jumps
#define EMG_THRESHOLD 5

// Jump cooldown to prevent multiple jumps from one flex (milliseconds)
#define JUMP_COOLDOWN 500

// Circular buffer for envelope detection
int circular_buffer[BUFFER_SIZE];
int data_index = 0;
int sum = 0;

// Jump state
bool canJump = true;
unsigned long lastJumpTime = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);
  
  // Initialize circular buffer
  for (int i = 0; i < BUFFER_SIZE; i++) {
    circular_buffer[i] = 0;
  }
  
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

  // Sample at SAMPLE_RATE
  if (timer < 0) {
    timer += 1000000 / SAMPLE_RATE;

    // Read raw EMG value from A0
    int sensor_value = analogRead(INPUT_PIN);

    // Filter the EMG signal
    int signal = EMGFilter(sensor_value);

    // Get the envelope (smoothed absolute value)
    int envelope = getEnvelope(abs(signal));

    // Check for jump
    checkJump(envelope);

    // Send current state: 1 if jumping, 0 if not
    // Also send envelope for debugging
    Serial.print(canJump ? "0" : "1");  // Inverted: 1 means currently in jump cooldown (jumping)
    Serial.print(",");
    Serial.println(envelope);
  }
}

// Check if muscle contraction exceeds threshold for jump
void checkJump(int envelope) {
  unsigned long current_time = millis();
  
  // If envelope exceeds threshold and we can jump
  if (envelope > EMG_THRESHOLD && canJump) {
    // Trigger jump
    canJump = false;
    lastJumpTime = current_time;
    Serial.println("JUMP!");  // Debug message
  }
  
  // Check if cooldown period has passed
  if (!canJump && (current_time - lastJumpTime >= JUMP_COOLDOWN)) {
    canJump = true;
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
float EMGFilter(float input) {
  float output = input;
  
  // First biquad section
  {
    static float z1, z2;
    float x = output - 0.05159732 * z1 - 0.36347401 * z2;
    output = 0.01856301 * x + 0.03712602 * z1 + 0.01856301 * z2;
    z2 = z1;
    z1 = x;
  }
  
  // Second biquad section
  {
    static float z1, z2;
    float x = output - -0.53945795 * z1 - 0.39764934 * z2;
    output = 1.00000000 * x + -2.00000000 * z1 + 1.00000000 * z2;
    z2 = z1;
    z1 = x;
  }
  
  // Third biquad section
  {
    static float z1, z2;
    float x = output - 0.47319594 * z1 - 0.70744137 * z2;
    output = 1.00000000 * x + 2.00000000 * z1 + 1.00000000 * z2;
    z2 = z1;
    z1 = x;
  }
  
  // Fourth biquad section
  {
    static float z1, z2;
    float x = output - -1.00211112 * z1 - 0.74520226 * z2;
    output = 1.00000000 * x + -2.00000000 * z1 + 1.00000000 * z2;
    z2 = z1;
    z1 = x;
  }
  
  return output;
}
