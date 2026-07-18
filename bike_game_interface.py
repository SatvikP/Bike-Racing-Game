#!/usr/bin/env python3
"""
Bike Racing Game Interface
===========================

A visual interface for the Arduino Bike Racing Game.
Reads serial data from Arduino and displays a bike racing game.

Requirements:
    pip install pygame pyserial

Usage:
    python bike_game_interface.py
    or
    python bike_game_interface.py COM3   (on Windows)
    python bike_game_interface.py /dev/cu.usbmodem14101  (on macOS)
"""

import sys
import serial
import serial.tools.list_ports
import pygame
import time
import re

# ========== CONFIGURATION ==========

# Serial settings (must match Arduino sketch)
BAUD_RATE = 115200
DEFAULT_PORT = None  # Auto-detect if not specified

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Track settings
TRACK_COLOR = (100, 100, 100)
TRACK_WIDTH = 200
TRACK_Y = SCREEN_HEIGHT - 100

# Bike settings
BIKE_COLOR = BLUE
BIKE_WIDTH = 40
BIKE_HEIGHT = 60

# ========== SERIAL COMMUNICATION ==========

class SerialReader:
    """Reads and parses serial data from Arduino."""
    
    def __init__(self, port=None, baud_rate=BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.speed = 0.0
        self.distance = 0.0
        self.envelope = 0
        self.connected = False
        
    def auto_detect_port(self):
        """Try to auto-detect Arduino port."""
        ports = serial.tools.list_ports.comports()
        arduino_ports = []
        
        for port in ports:
            # Look for Arduino-like ports
            if 'Arduino' in port.description or 'USB' in port.description:
                arduino_ports.append(port.device)
            # On macOS, look for common patterns
            elif 'usbmodem' in port.device or 'ttyACM' in port.device:
                arduino_ports.append(port.device)
            # On Windows
            elif 'COM' in port.device:
                arduino_ports.append(port.device)
        
        if arduino_ports:
            # Prefer the first Arduino port found
            return arduino_ports[0]
        return None
    
    def connect(self):
        """Connect to the serial port."""
        global DEFAULT_PORT
        
        port_to_use = self.port
        
        if port_to_use is None:
            port_to_use = self.auto_detect_port()
        
        if port_to_use is None:
            print("No Arduino port detected. Trying common ports...")
            # Try common port names
            common_ports = [
                '/dev/cu.usbmodem14101', '/dev/cu.usbmodem14201',
                '/dev/cu.usbmodem14301', '/dev/cu.usbmodem14401',
                '/dev/ttyACM0', '/dev/ttyACM1',
                'COM3', 'COM4', 'COM5', 'COM6'
            ]
            for p in common_ports:
                try:
                    self.serial_conn = serial.Serial(p, self.baud_rate, timeout=1)
                    self.port = p
                    self.connected = True
                    print(f"Connected to {p}")
                    time.sleep(3)  # Wait for Arduino to initialize
                    return True
                except (serial.SerialException, OSError):
                    continue
            
            print("Could not auto-connect. Please specify the port.")
            print("Available ports:")
            for port in serial.tools.list_ports.comports():
                print(f"  {port.device}: {port.description}")
            return False
        
        try:
            self.serial_conn = serial.Serial(port_to_use, self.baud_rate, timeout=1)
            self.port = port_to_use
            self.connected = True
            print(f"Connected to {port_to_use}")
            time.sleep(3)  # Wait for Arduino to initialize
            return True
        except (serial.SerialException, OSError) as e:
            print(f"Failed to connect to {port_to_use}: {e}")
            return False
    
    def parse_line(self, line):
        """Parse a line of serial data: 'Speed | Distance | Envelope'"""
        line = line.strip()
        if not line:
            return None
        
        # Debug: print raw line
        print(f"DEBUG: Raw line: {line}", file=sys.stderr)
        
        # Try to match the expected format
        pattern = r'([\d.]+)\s*\|\s*([\d.]+)m\s*\|\s*(\d+)'
        match = re.match(pattern, line)
        
        if match:
            try:
                self.speed = float(match.group(1))
                self.distance = float(match.group(2))
                self.envelope = int(match.group(3))
                print(f"DEBUG: Parsed - speed={self.speed}, distance={self.distance}, envelope={self.envelope}", file=sys.stderr)
                return True
            except ValueError:
                return False
        
        # Fallback: try splitting by |
        parts = line.split('|')
        if len(parts) >= 3:
            try:
                self.speed = float(parts[0].strip())
                self.distance = float(parts[1].strip().replace('m', '').strip())
                self.envelope = int(parts[2].strip())
                print(f"DEBUG: Parsed (fallback) - speed={self.speed}, distance={self.distance}, envelope={self.envelope}", file=sys.stderr)
                return True
            except ValueError:
                return False
        
        return False
    
    def read_data(self):
        """Read and parse data from serial port."""
        if not self.connected or self.serial_conn is None:
            return False
        
        try:
            while self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore')
                if line and self.parse_line(line):
                    return True
        except (serial.SerialException, OSError) as e:
            print(f"DEBUG: Serial error: {e}", file=sys.stderr)
            self.connected = False
        
        return False
    
    def close(self):
        """Close the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False


# ========== GAME INTERFACE ==========

class BikeRacingGame:
    """Visual interface for the bike racing game."""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bike Racing Game - EMG Control")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)
        self.small_font = pygame.font.SysFont('Arial', 16)
        
        # Game state
        self.speed = 0.0
        self.distance = 0.0
        self.envelope = 0
        self.max_speed = 100.0
        self.max_envelope = 0
        
        # Bike position
        self.bike_x = SCREEN_WIDTH // 2
        self.bike_y = TRACK_Y - BIKE_HEIGHT // 2
        self.bike_speed_x = 0
        
        # Background scrolling
        self.scroll_offset = 0
        self.scroll_speed = 0
        
        # Load images or use simple shapes
        self.bike_surface = None
        
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_r:
                    # Reset distance
                    self.distance = 0
        return True
    
    def update(self, speed, distance, envelope):
        """Update game state with new data."""
        self.speed = speed
        self.distance = distance
        self.envelope = envelope
        
        # Debug
        print(f"DEBUG: Game update - speed={speed}, distance={distance}, envelope={envelope}", file=sys.stderr)
        
        # Track max envelope for scaling
        if envelope > self.max_envelope:
            self.max_envelope = envelope
        
        # Update bike position based on speed
        # Higher speed = more movement
        speed_factor = speed / self.max_speed if self.max_speed > 0 else 0
        self.scroll_speed = speed_factor * 5
        self.scroll_offset += self.scroll_speed
        
        # Debug scroll
        print(f"DEBUG: scroll_speed={self.scroll_speed}, scroll_offset={self.scroll_offset}", file=sys.stderr)
        
        # Wrap scroll offset
        if self.scroll_offset > SCREEN_WIDTH:
            self.scroll_offset = 0
    
    def draw_track(self):
        """Draw the racing track."""
        # Draw track background
        track_rect = pygame.Rect(0, TRACK_Y, SCREEN_WIDTH, TRACK_WIDTH)
        pygame.draw.rect(self.screen, TRACK_COLOR, track_rect)
        
        # Draw track markings (dotted lines)
        start_y = TRACK_Y + TRACK_WIDTH // 2
        for x in range(-50, SCREEN_WIDTH + 50, 40):
            adjusted_x = x - int(self.scroll_offset) % 40
            pygame.draw.rect(self.screen, WHITE, 
                           (adjusted_x, start_y, 20, 4))
        
        # Draw track borders
        pygame.draw.rect(self.screen, WHITE, 
                       (0, TRACK_Y, SCREEN_WIDTH, 2))
        pygame.draw.rect(self.screen, WHITE, 
                       (0, TRACK_Y + TRACK_WIDTH, SCREEN_WIDTH, 2))
    
    def draw_bike(self):
        """Draw the bike."""
        # Simple bike shape
        bike_rect = pygame.Rect(
            self.bike_x - BIKE_WIDTH // 2,
            self.bike_y,
            BIKE_WIDTH,
            BIKE_HEIGHT
        )
        
        # Bike body
        pygame.draw.rect(self.screen, BIKE_COLOR, bike_rect, border_radius=5)
        
        # Bike details
        pygame.draw.rect(self.screen, BLACK, 
                        (self.bike_x - 5, self.bike_y + 10, 10, 15))
        pygame.draw.circle(self.screen, BLACK, 
                          (self.bike_x - 15, self.bike_y + BIKE_HEIGHT - 5), 8)
        pygame.draw.circle(self.screen, BLACK, 
                          (self.bike_x + 15, self.bike_y + BIKE_HEIGHT - 5), 8)
        
        # Speed indicator on bike
        speed_color = self.get_speed_color(self.speed)
        pygame.draw.rect(self.screen, speed_color,
                        (self.bike_x - 10, self.bike_y - 20, 20, 10))
    
    def draw_hud(self):
        """Draw heads-up display."""
        # Speedometer
        speed_text = self.big_font.render(f"{self.speed:.0f} km/h", True, RED)
        self.screen.blit(speed_text, (50, 50))
        
        # Label
        speed_label = self.small_font.render("SPEED", True, WHITE)
        self.screen.blit(speed_label, (50, 80))
        
        # Distance
        distance_text = self.big_font.render(f"{self.distance:.1f} m", True, GREEN)
        self.screen.blit(distance_text, (SCREEN_WIDTH - 150, 50))
        
        # Label
        distance_label = self.small_font.render("DISTANCE", True, WHITE)
        self.screen.blit(distance_label, (SCREEN_WIDTH - 150, 80))
        
        # EMG Envelope (power meter)
        power_text = self.font.render(f"Power: {self.envelope}", True, YELLOW)
        self.screen.blit(power_text, (SCREEN_WIDTH // 2 - 80, 50))
        
        # Power bar
        bar_width = 200
        bar_height = 20
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = 80
        
        # Background
        pygame.draw.rect(self.screen, BLACK, (bar_x, bar_y, bar_width, bar_height))
        # Filled portion (based on envelope, capped at reasonable max)
        fill_width = min(int((self.envelope / max(self.max_envelope, 100)) * bar_width), bar_width)
        fill_width = max(fill_width, 0)
        pygame.draw.rect(self.screen, GREEN, (bar_x, bar_y, fill_width, bar_height))
        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Instructions
        if self.speed < 5:
            instructions = self.small_font.render("Flex your muscle to accelerate!", True, WHITE)
            self.screen.blit(instructions, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 30))
    
    def draw_scenery(self):
        """Draw scrolling background scenery."""
        # Draw grass
        pygame.draw.rect(self.screen, (30, 150, 30), 
                        (0, TRACK_Y + TRACK_WIDTH, SCREEN_WIDTH, SCREEN_HEIGHT - TRACK_Y - TRACK_WIDTH))
        
        # Draw sky
        pygame.draw.rect(self.screen, (135, 206, 235), 
                        (0, 0, SCREEN_WIDTH, TRACK_Y - 50))
        
        # Draw some trees in the distance
        for i in range(10):
            tree_x = (i * 100 - int(self.scroll_offset) * 0.3) % (SCREEN_WIDTH + 50) - 25
            if tree_x < SCREEN_WIDTH + 50:
                tree_color = (34, 139, 34)
                pygame.draw.rect(self.screen, tree_color, 
                                (tree_x, TRACK_Y - 40, 20, 40))
                pygame.draw.polygon(self.screen, (0, 100, 0), [
                    (tree_x - 10, TRACK_Y - 40),
                    (tree_x + 10, TRACK_Y - 60),
                    (tree_x + 30, TRACK_Y - 40)
                ])
    
    def get_speed_color(self, speed):
        """Get color based on speed."""
        if speed > 75:
            return RED
        elif speed > 50:
            return ORANGE
        elif speed > 25:
            return YELLOW
        else:
            return GREEN
    
    def draw_connection_status(self, connected):
        """Draw serial connection status."""
        status_text = self.small_font.render(
            f"Serial: {'CONNECTED' if connected else 'DISCONNECTED'} "
            f"{'(' + serial_reader.port + ')' if serial_reader.port else ''}",
            True, GREEN if connected else RED
        )
        self.screen.blit(status_text, (10, SCREEN_HEIGHT - 20))
    
    def render(self, connected):
        """Render the game."""
        # Clear screen
        self.screen.fill(BLACK)
        
        # Draw scenery
        self.draw_scenery()
        
        # Draw track
        self.draw_track()
        
        # Draw bike
        self.draw_bike()
        
        # Draw HUD
        self.draw_hud()
        
        # Draw connection status
        self.draw_connection_status(connected)
        
        # Update display
        pygame.display.flip()


# ========== MAIN ==========

def main():
    """Main entry point."""
    global serial_reader
    
    # Parse command line arguments for port
    port_arg = None
    if len(sys.argv) > 1:
        port_arg = sys.argv[1]
    
    # Initialize serial reader
    serial_reader = SerialReader(port=port_arg)
    
    if not serial_reader.connect():
        print("Failed to connect to Arduino.")
        print("Usage: python bike_game_interface.py [PORT]")
        print("Example: python bike_game_interface.py COM3")
        print("        python bike_game_interface.py /dev/cu.usbmodem14101")
        sys.exit(1)
    
    # Initialize game
    game = BikeRacingGame()
    
    # Main game loop
    running = True
    last_read_time = time.time()
    
    print("Bike Racing Game Interface")
    print("---------------------------")
    print("Press ESC to quit")
    print("Press R to reset distance")
    
    try:
        while running:
            # Handle events
            running = game.handle_events()
            
            # Read serial data
            if time.time() - last_read_time > 0.05:  # Throttle reads
                if serial_reader.read_data():
                    print(f"DEBUG: Data received, updating game", file=sys.stderr)
                    game.update(serial_reader.speed, serial_reader.distance, serial_reader.envelope)
                    last_read_time = time.time()
                else:
                    print(f"DEBUG: No data received (in_waiting={serial_reader.serial_conn.in_waiting if serial_reader.serial_conn else 0})", file=sys.stderr)
            
            # Update bike position
            # Bike sways side to side based on speed
            game.bike_x = SCREEN_WIDTH // 2 + int(10 * (game.speed / game.max_speed) * 
                                                   (0.5 if int(time.time() * 2) % 2 == 0 else -0.5))
            
            # Render
            game.render(serial_reader.connected)
            
            # Cap FPS
            game.clock.tick(FPS)
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        serial_reader.close()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
