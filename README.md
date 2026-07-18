# Mistral Cat Obstacle Game

A fun EMG-controlled game where **Mistral Cat** automatically runs and jumps when you flex your muscle! Collect coins and avoid obstacles. The game gets harder over time.

## Features

- **Mistral Cat** as the player character (in official Mistral purple)
- **Jump** by flexing your muscle (EMG signal triggers jump)
- **Collect yellow coins** for points
- **Avoid red obstacles** or it's game over
- **Difficulty increases** over time (scrolling gets faster)
- **Score tracking** - collect as many coins as you can
- **Real-time EMG visualization** - see your muscle power

## Hardware Requirements

- Arduino board (Uno, Nano, etc.)
- Muscle BioAmp Shield v0.3 (or just the EMG circuit connected to A0)
- Electrodes for muscle signal detection
- Optional: LED bar graph on pins 8-13 for visual feedback

## Files

- `Obstacle-Game.ino` - Arduino sketch for EMG jump detection
- `mistral_cat_game.py` - Python Pygame interface
- `requirements.txt` - Python dependencies

## Setup

### Arduino Setup

1. Upload the `Obstacle-Game.ino` sketch to your Arduino
2. Open Serial Monitor at 115200 baud to verify it's working
3. Attach electrodes to your muscle (typically forearm)
4. Flex your muscle to test jumps

### Python Interface Setup

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the game (auto-detects Arduino port)
python mistral_cat_game.py

# Or specify the port manually
python mistral_cat_game.py COM3          # Windows
python mistral_cat_game.py /dev/cu.usbmodem14101  # macOS/Linux
```

## How to Play

- **Flex your muscle** to make Mistral Cat jump
- **Collect yellow coins** for points (score increases)
- **Avoid red obstacles** by jumping over them
- **Game over** if you hit an obstacle
- **Press R** to restart after game over
- **Press ESC** to quit
- **Press SPACE** to test jumping without Arduino

## Game Mechanics

- The game auto-scrolls to the right
- Mistral Cat runs automatically
- Jump height and duration are fixed
- Coins and obstacles spawn randomly
- Game speed increases over time (gets harder!)
- Score = number of coins collected

## Calibration

1. Open Serial Monitor to see your EMG envelope values
2. Relax your muscle - note the baseline value
3. Flex your muscle - note the maximum value
4. Adjust `EMG_THRESHOLD` in `Obstacle-Game.ino` (default: 5)
   - Lower = more sensitive (jumps on small contractions)
   - Higher = less sensitive (needs stronger contractions)
5. Adjust `JUMP_COOLDOWN` to change how often you can jump (default: 500ms)

## Customization

Edit these `#define` values in `Obstacle-Game.ino`:

- `EMG_THRESHOLD` - Minimum EMG envelope to trigger a jump
- `JUMP_COOLDOWN` - Time between jumps (milliseconds)
- `SAMPLE_RATE` - Sampling frequency (Hz)
- `BUFFER_SIZE` - Envelope smoothing (larger = smoother)

Edit these in `mistral_cat_game.py`:

- `BASE_SCROLL_SPEED` - Starting scroll speed
- `SPEED_INCREASE_RATE` - How fast difficulty increases
- `OBSTACLE_MIN_DISTANCE` / `OBSTACLE_MAX_DISTANCE` - Obstacle spacing
- `COIN_MIN_DISTANCE` / `COIN_MAX_DISTANCE` - Coin spacing
- `GRAVITY` - Jump physics
- `JUMP_HEIGHT` - Jump height

## Troubleshooting

### Serial connection issues
- Close Arduino Serial Monitor (it locks the port)
- Check the port name with `ls /dev/cu.*` (macOS) or check Device Manager (Windows)
- Make sure the baud rate matches (115200)

### Cat not jumping
- Check EMG envelope values in Serial Monitor
- Lower `EMG_THRESHOLD` if values are too low
- Ensure electrodes have good contact
- Try flexing harder

### Game too easy/hard
- Adjust `BASE_SCROLL_SPEED` and `SPEED_INCREASE_RATE`
- Change obstacle/coin spawn distances

## License

This project is derived from the [Muscle-BioAmp-Arduino-Firmware](https://github.com/upsidedownlabs/DIY-Muscle-BioAmp-Shield) project by Upside Down Labs.
