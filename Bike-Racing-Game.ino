// Bike Racing Game - Single Channel EMG (A0 only)
// Based on Muscle BioAmp Shield example
// https://github.com/upsidedownlabs/DIY-Muscle-BioAmp-Shield

// Simple bike racing game using only A0 analog input
// Flex your muscle to accelerate the bike!
// The stronger the contraction, the faster you go.

// Samples per second
#define SAMPLE_RATE 500

// Make sure to set the same baud rate on your Serial Monitor/Plotter
#define BAUD_RATE 115200

// Using only A0 analog pin (EXG pill fried, only A0 available)
#define INPUT_PIN A0

// Envelope buffer size for smoothing
// High value = smooth but less responsive
// Low value = less smooth but more responsive
#define BUFFER_SIZE 32

// EMG Threshold - adjust based on your baseline muscle activity
// Check by plotting EMG envelope on Serial Plotter
#define EMG_THRESHOLD 20

// EMG Envelope baseline (minimum value without flexing)
#define EMG_ENVELOPE_BASELINE 4

// EMG Envelope divider for LED bar scaling
#define EMG_ENVELOPE_DIVIDER 4

// LED bar pins (Muscle BioAmp Shield v0.3)
int led_bar[] = { 8, 9, 10, 11, 12, 13 };
int total_leds = sizeof(led_bar) / sizeof(led_bar[0]);

// Bike game variables
float bike_speed = 0.0;        // Current speed (0-100%)
float bike_distance = 0.0;     // Total distance traveled (meters)
unsigned long last_update = 0;
const unsigned long UPDATE_INTERVAL = 50; // ms between game updates

// Circular buffer for envelope detection
int circular_buffer[BUFFER_SIZE];
int data_index = 0;
int sum = 0;

// Track parameters
const float MAX_SPEED = 100.0;      // Maximum speed percentage
const float ACCELERATION_FACTOR = 0.5; // How quickly speed responds to EMG
const float DECELERATION_FACTOR = 0.2; // How quickly speed drops when relaxed
const float DISTANCE_PER_UPDATE = 0.1;  // Distance gained per update at max speed

void setup() {
  // Initialize serial communication
  Serial.begin(BAUD_RATE);
  
  // Initialize all the LED bar pins
  for (int i = 0; i < total_leds; i++) {
    pinMode(led_bar[i], OUTPUT);
    digitalWrite(led_bar[i], LOW);
  }
  
  // Initialize circular buffer
  for (int i = 0; i < BUFFER_SIZE; i++) {
    circular_buffer[i] = 0;
  }
  
  Serial.println("Bike Racing Game - Ready!");
  Serial.println("Flex your muscle to accelerate!");
  Serial.println("Speed | Distance | Envelope");
  Serial.println("---------------------");
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

    // Read raw EMG value from A0
    int sensor_value = analogRead(INPUT_PIN);

    // Filter the EMG signal (band-pass filter for EMG frequencies)
    int signal = EMGFilter(sensor_value);

    // Get the envelope (smoothed absolute value)
    int envelope = getEnvelope(abs(signal));

    // Update LED bar graph to show "power level"
    updateSpeedLEDs(envelope);

    // Update bike physics
    updateBikePhysics(envelope);

    // Print game data to Serial Monitor
    Serial.print(bike_speed, 1);
    Serial.print(" | ");
    Serial.print(bike_distance, 1);
    Serial.print("m | ");
    Serial.println(envelope);
  }
}

// Update the LED bar to show current speed/power
void updateSpeedLEDs(int envelope) {
  // Calculate how many LEDs to light based on envelope
  int leds_to_light = constrain(
    (envelope / EMG_ENVELOPE_DIVIDER - EMG_ENVELOPE_BASELINE), 
    0, 
    total_leds
  );
  
  // Light up the appropriate number of LEDs
  for (int i = 0; i < total_leds; i++) {
    if (i < leds_to_light) {
      digitalWrite(led_bar[i], HIGH);
    } else {
      digitalWrite(led_bar[i], LOW);
    }
  }
}

// Update bike speed and distance based on EMG envelope
void updateBikePhysics(int envelope) {
  unsigned long current_time = millis();
  
  // Only update game state at fixed intervals
  if (current_time - last_update >= UPDATE_INTERVAL) {
    last_update = current_time;
    
    // Map envelope to target speed (0-100%)
    float target_speed = map(envelope, EMG_THRESHOLD, 500, 0, MAX_SPEED);
    target_speed = constrain(target_speed, 0, MAX_SPEED);
    
    // If envelope is below threshold, target speed is 0
    if (envelope < EMG_THRESHOLD) {
      target_speed = 0;
    }
    
    // Smooth acceleration/deceleration
    if (target_speed > bike_speed) {
      // Accelerating - respond quickly
      bike_speed += (target_speed - bike_speed) * ACCELERATION_FACTOR;
    } else {
      // Decelerating - slower response for smoother gameplay
      bike_speed += (target_speed - bike_speed) * DECELERATION_FACTOR;
    }
    
    // Ensure speed stays within bounds
    bike_speed = constrain(bike_speed, 0, MAX_SPEED);
    
    // Calculate distance gained in this update
    // Speed is percentage, so scale distance accordingly
    float speed_percentage = bike_speed / MAX_SPEED;
    bike_distance += speed_percentage * DISTANCE_PER_UPDATE;
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
// This helps isolate the EMG signal from noise
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
