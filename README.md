# Bike Racing Game - Single Channel EMG

A simple Arduino-based bike racing game controlled by muscle contractions (EMG). This version uses only the A0 analog input channel, making it compatible with setups where the EXG pill is not available.

## Based On

This project is derived from the [Muscle-BioAmp-Arduino-Firmware](https://github.com/upsidedownlabs/DIY-Muscle-BioAmp-Shield) project by Upside Down Labs, specifically the Muscle Strength Game example.

## How It Works

1. The Arduino reads EMG signals from the A0 analog pin
2. A band-pass filter isolates the EMG frequency range (74.5-149.5 Hz)
3. An envelope detection algorithm smooths the signal
4. The envelope amplitude controls the bike's speed:
   - Stronger muscle contraction = higher speed
   - Relaxed muscle = deceleration
5. The LED bar graph (pins 8-13) shows your current power level
6. Serial monitor displays real-time speed, distance, and envelope data

## Files

- `Bike-Racing-Game.ino` - Arduino sketch for the game logic
- `bike_game_interface.py` - Python visual interface using Pygame
- `requirements.txt` - Python dependencies

## Hardware Requirements

- Arduino board (Uno, Nano, etc.)
- Muscle BioAmp Shield v0.3 (or just the EMG circuit connected to A0)
- Electrodes for muscle signal detection
- Optional: LED bar graph on pins 8-13 for visual feedback

## Setup

### Arduino Setup

1. Upload the `Bike-Racing-Game.ino` sketch to your Arduino
2. Open Serial Monitor at 115200 baud to verify it's working
3. Attach electrodes to your muscle (typically forearm)
4. Flex your muscle to see the speed and distance values

### Visual Interface Setup

For a full graphical experience, run the Python interface:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the game interface (auto-detects Arduino port)
python bike_game_interface.py

# Or specify the port manually
python bike_game_interface.py COM3          # Windows
python bike_game_interface.py /dev/cu.usbmodem14101  # macOS/Linux
```

The interface will:
- Display a scrolling track with your bike
- Show real-time speed (km/h) and distance (meters)
- Visualize your muscle power with a green power bar
- Show connection status in the bottom-left corner

**Controls:**
- Press `ESC` to quit
- Press `R` to reset distance

## Tips

- Use Serial Monitor first to calibrate `EMG_THRESHOLD` in the Arduino sketch
- The interface auto-detects common Arduino ports, but you can specify it manually
- For best results, ensure good electrode contact with your skin

## Game Mechanics

- **Speed**: 0-100% based on muscle contraction strength
- **Distance**: Accumulates as you ride (virtual meters)
- **Acceleration**: Smooth response to muscle activity
- **Deceleration**: Gradual slowdown when muscle is relaxed

## Customization

Adjust these `#define` values at the top of the sketch:

- `SAMPLE_RATE`: Sampling frequency (Hz)
- `EMG_THRESHOLD`: Minimum envelope value to register muscle activity
- `BUFFER_SIZE`: Envelope smoothing - larger = smoother but less responsive
- `ACCELERATION_FACTOR`: How quickly the bike responds to muscle contraction
- `DECELERATION_FACTOR`: How quickly the bike slows down
- `MAX_SPEED`: Maximum speed percentage
- `DISTANCE_PER_UPDATE`: Distance gained per game update at max speed

## Serial Output

The game outputs data in this format:
```
Speed | Distance | Envelope
25.5 | 12.3m | 45
```

- **Speed**: Current speed as percentage (0-100)
- **Distance**: Total distance traveled in meters
- **Envelope**: Current EMG envelope value (for calibration)

## Tips for Calibration

1. Open Serial Plotter to visualize the envelope signal
2. Relax your muscle and note the baseline envelope value
3. Flex your muscle strongly and note the maximum envelope value
4. Adjust `EMG_THRESHOLD` to be slightly above your baseline
5. Adjust `EMG_ENVELOPE_DIVIDER` to scale the LED bar appropriately

## Files

- `Bike-Racing-Game.ino` - Main Arduino sketch
- `README.md` - This file

## License

This project inherits the open-source license from the original Muscle BioAmp Shield project. See the header in `Bike-Racing-Game.ino` for details.
