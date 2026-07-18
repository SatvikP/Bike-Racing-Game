#!/usr/bin/env python3
"""
Mistral Cat Obstacle Game
==========================

A game where Mistral Cat automatically runs and jumps when you flex your muscle.
Collect coins and avoid obstacles. The game gets harder over time.

Control: Flex your muscle to make Mistral Cat jump!

Requirements:
    pip install pygame pyserial

Usage:
    python mistral_cat_game.py
    python mistral_cat_game.py COM3
    python mistral_cat_game.py /dev/cu.usbmodem14101
"""

import sys
import serial
import serial.tools.list_ports
import pygame
import time
import random

# ========== CONFIGURATION ==========

BAUD_RATE = 115200
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
PURPLE = (150, 50, 255)

# Mistral brand color (purple)
MISTRAL_PURPLE = (102, 51, 153)

# Game settings
GROUND_Y = SCREEN_HEIGHT - 80
CAT_WIDTH = 40
CAT_HEIGHT = 50
JUMP_HEIGHT = 180
JUMP_DURATION = 300  # ms
GRAVITY = 0.8

# Spawn settings
OBSTACLE_MIN_DISTANCE = 200
OBSTACLE_MAX_DISTANCE = 400
COIN_MIN_DISTANCE = 150
COIN_MAX_DISTANCE = 300

# Difficulty scaling
BASE_SCROLL_SPEED = 3
SPEED_INCREASE_RATE = 0.00005  # Speed increase per ms


# ========== SERIAL COMMUNICATION ==========

class SerialReader:
    """Reads jump signals from Arduino."""
    
    def __init__(self, port=None, baud_rate=BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.jumping = False
        self.connected = False
        
    def auto_detect_port(self):
        """Try to auto-detect Arduino port."""
        ports = serial.tools.list_ports.comports()
        arduino_ports = []
        
        for port in ports:
            if 'Arduino' in port.description or 'USB' in port.description:
                arduino_ports.append(port.device)
            elif 'usbmodem' in port.device or 'ttyACM' in port.device:
                arduino_ports.append(port.device)
            elif 'COM' in port.device:
                arduino_ports.append(port.device)
        
        return arduino_ports[0] if arduino_ports else None
    
    def connect(self):
        """Connect to the serial port."""
        port_to_use = self.port
        
        if port_to_use is None:
            port_to_use = self.auto_detect_port()
        
        if port_to_use is None:
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
                    time.sleep(3)
                    return True
                except (serial.SerialException, OSError):
                    continue
            
            print("Could not auto-connect.")
            return False
        
        try:
            self.serial_conn = serial.Serial(port_to_use, self.baud_rate, timeout=1)
            self.port = port_to_use
            self.connected = True
            print(f"Connected to {port_to_use}")
            time.sleep(3)
            return True
        except (serial.SerialException, OSError) as e:
            print(f"Failed to connect to {port_to_use}: {e}")
            return False
    
    def read_data(self):
        """Read jump state from serial port."""
        if not self.connected or self.serial_conn is None:
            return False
        
        try:
            while self.serial_conn.in_waiting > 0:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                # Skip debug messages like "Ready!"
                if line.startswith("Mistral") or line.startswith("Flex") or line.startswith("Ready"):
                    continue
                
                # Arduino sends "1" for jump, "0" for no jump
                if line == "1":
                    self.jumping = True
                    return True
                elif line == "0":
                    self.jumping = False
                    return True
        except (serial.SerialException, OSError):
            self.connected = False
        
        return False
    
    def close(self):
        """Close the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connected = False


# ========== GAME ELEMENTS ==========

class MistralCat:
    """The player character - Mistral Cat."""
    
    def __init__(self):
        self.x = 100
        self.y = GROUND_Y - CAT_HEIGHT
        self.width = CAT_WIDTH
        self.height = CAT_HEIGHT
        self.vel_y = 0
        self.is_jumping = False
        self.jump_start_time = 0
        self.color = MISTRAL_PURPLE
        
    def jump(self):
        """Start a jump."""
        if not self.is_jumping:
            self.is_jumping = True
            self.vel_y = -15  # Initial upward velocity
            self.jump_start_time = pygame.time.get_ticks()
    
    def update(self):
        """Update cat position with gravity."""
        # Apply gravity
        self.vel_y += GRAVITY
        self.y += self.vel_y
        
        # Check if landed
        if self.y >= GROUND_Y - self.height:
            self.y = GROUND_Y - self.height
            self.vel_y = 0
            self.is_jumping = False
    
    def draw(self, screen):
        """Draw Mistral Cat."""
        # Main body (purple oval)
        body_rect = pygame.Rect(self.x, self.y + 10, self.width, self.height - 10)
        pygame.draw.ellipse(screen, self.color, body_rect)
        
        # Head (circle)
        head_radius = self.width // 2 - 5
        pygame.draw.circle(screen, self.color, (self.x + head_radius + 5, self.y + head_radius), head_radius)
        
        # Ears
        ear_points_left = [
            (self.x + head_radius, self.y + head_radius - 10),
            (self.x + head_radius - 10, self.y + head_radius - 20),
            (self.x + head_radius + 5, self.y + head_radius)
        ]
        ear_points_right = [
            (self.x + head_radius + 10, self.y + head_radius - 10),
            (self.x + head_radius + 20, self.y + head_radius - 20),
            (self.x + head_radius + 15, self.y + head_radius)
        ]
        pygame.draw.polygon(screen, self.color, ear_points_left)
        pygame.draw.polygon(screen, self.color, ear_points_right)
        
        # Eyes
        pygame.draw.circle(screen, WHITE, (self.x + head_radius + 3, self.y + head_radius + 2), 4)
        pygame.draw.circle(screen, WHITE, (self.x + head_radius + 12, self.y + head_radius + 2), 4)
        pygame.draw.circle(screen, BLACK, (self.x + head_radius + 3, self.y + head_radius + 2), 2)
        pygame.draw.circle(screen, BLACK, (self.x + head_radius + 12, self.y + head_radius + 2), 2)
        
        # Legs
        pygame.draw.rect(screen, self.color, (self.x + 5, self.y + self.height - 20, 8, 20))
        pygame.draw.rect(screen, self.color, (self.x + 27, self.y + self.height - 20, 8, 20))
        
        # Tail
        tail_points = [
            (self.x + self.width, self.y + self.height // 2),
            (self.x + self.width + 20, self.y + self.height // 2 - 10),
            (self.x + self.width + 15, self.y + self.height // 2 + 5)
        ]
        pygame.draw.polygon(screen, self.color, tail_points)


class Obstacle:
    """An obstacle to avoid."""
    
    def __init__(self, x, width=30, height=40):
        self.x = x
        self.y = GROUND_Y - height
        self.width = width
        self.height = height
        self.color = RED
        
    def update(self, scroll_speed):
        """Move obstacle with scroll."""
        self.x -= scroll_speed
        
    def draw(self, screen):
        """Draw obstacle."""
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # Add some detail
        pygame.draw.rect(screen, (200, 20, 20), (self.x + 5, self.y + 5, self.width - 10, 10))
        pygame.draw.rect(screen, (200, 20, 20), (self.x + 5, self.y + 20, self.width - 10, 10))
        
    def collides_with(self, cat):
        """Check collision with cat."""
        cat_rect = pygame.Rect(cat.x, cat.y, cat.width, cat.height)
        obstacle_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        return cat_rect.colliderect(obstacle_rect)


class Coin:
    """A coin to collect."""
    
    def __init__(self, x):
        self.x = x
        self.y = GROUND_Y - 60 + random.randint(0, 30)
        self.radius = 12
        self.color = YELLOW
        self.collected = False
        
    def update(self, scroll_speed):
        """Move coin with scroll."""
        self.x -= scroll_speed
        
    def draw(self, screen):
        """Draw coin."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 215, 0), (int(self.x), int(self.y)), self.radius - 3)
        # Add shine
        pygame.draw.circle(screen, WHITE, (int(self.x) + 4, int(self.y) - 4), 3)
        
    def collides_with(self, cat):
        """Check if cat collected the coin."""
        if self.collected:
            return False
        
        # Simple circle-rect collision
        cat_rect = pygame.Rect(cat.x, cat.y, cat.width, cat.height)
        
        # Find closest point on rectangle to circle
        closest_x = max(cat_rect.left, min(self.x, cat_rect.right))
        closest_y = max(cat_rect.top, min(self.y, cat_rect.bottom))
        
        distance = ((self.x - closest_x) ** 2 + (self.y - closest_y) ** 2) ** 0.5
        return distance < self.radius


# ========== GAME INTERFACE ==========

class MistralCatGame:
    """Main game class."""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mistral Cat Obstacle Game - EMG Control")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)
        self.small_font = pygame.font.SysFont('Arial', 16)
        
        # Game state
        self.cat = MistralCat()
        self.obstacles = []
        self.coins = []
        self.score = 0
        self.game_over = False
        self.start_time = pygame.time.get_ticks()
        
        # Camera/scroll
        self.scroll_offset = 0
        self.base_scroll_speed = BASE_SCROLL_SPEED
        
        # Spawn timers
        self.last_obstacle_time = 0
        self.last_coin_time = 0
        self.obstacle_timer = random.randint(2000, 4000)  # ms
        self.coin_timer = random.randint(1500, 3000)  # ms
        
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:  # For testing without Arduino
                    self.cat.jump()
                if event.key == pygame.K_r and self.game_over:
                    self.reset()
        return True
    
    def spawn_obstacle(self):
        """Spawn a new obstacle."""
        obstacle = Obstacle(SCREEN_WIDTH + 50)
        self.obstacles.append(obstacle)
        self.last_obstacle_time = pygame.time.get_ticks()
        self.obstacle_timer = random.randint(OBSTACLE_MIN_DISTANCE, OBSTACLE_MAX_DISTANCE)
        
    def spawn_coin(self):
        """Spawn a new coin."""
        coin = Coin(SCREEN_WIDTH + 50)
        self.coins.append(coin)
        self.last_coin_time = pygame.time.get_ticks()
        self.coin_timer = random.randint(COIN_MIN_DISTANCE, COIN_MAX_DISTANCE)
    
    def update(self, jumping):
        """Update game state."""
        if self.game_over:
            return
        
        # Calculate scroll speed based on time
        elapsed = pygame.time.get_ticks() - self.start_time
        scroll_speed = self.base_scroll_speed + (elapsed * SPEED_INCREASE_RATE)
        
        # Trigger jump from EMG
        if jumping:
            self.cat.jump()
        
        # Update cat
        self.cat.update()
        
        # Update obstacles and coins
        for obstacle in self.obstacles[:]:
            obstacle.update(scroll_speed)
            if obstacle.x < -obstacle.width:
                self.obstacles.remove(obstacle)
            elif obstacle.collides_with(self.cat):
                self.game_over = True
        
        for coin in self.coins[:]:
            coin.update(scroll_speed)
            if coin.x < -coin.radius:
                self.coins.remove(coin)
            elif coin.collides_with(self.cat):
                coin.collected = True
                self.score += 1
                self.coins.remove(coin)
        
        # Spawn new obstacles
        if pygame.time.get_ticks() - self.last_obstacle_time > self.obstacle_timer:
            self.spawn_obstacle()
        
        # Spawn new coins
        if pygame.time.get_ticks() - self.last_coin_time > self.coin_timer:
            self.spawn_coin()
        
        # Update scroll offset
        self.scroll_offset += scroll_speed
    
    def draw_ground(self, screen):
        """Draw scrolling ground."""
        # Grass
        pygame.draw.rect(screen, (30, 150, 30), (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        
        # Ground line
        pygame.draw.line(screen, (50, 200, 50), (0, GROUND_Y), (SCREEN_WIDTH, GROUND_Y), 3)
        
        # Ground texture (scrolling)
        for x in range(-50, SCREEN_WIDTH + 50, 40):
            adjusted_x = (x - int(self.scroll_offset) % 40) % SCREEN_WIDTH
            pygame.draw.rect(screen, (40, 180, 40), (adjusted_x, GROUND_Y - 5, 20, 5))
    
    def draw_sky(self, screen):
        """Draw sky with clouds."""
        # Sky gradient
        for y in range(0, GROUND_Y, 2):
            ratio = y / GROUND_Y
            color = (135 + int(120 * ratio), 206 + int(30 * ratio), 235 + int(20 * ratio))
            pygame.draw.line(screen, color, (0, y), (SCREEN_WIDTH, y))
        
        # Clouds
        for i in range(5):
            cloud_x = (i * 200 - int(self.scroll_offset) * 0.3) % (SCREEN_WIDTH + 100) - 50
            if 0 < cloud_x < SCREEN_WIDTH:
                self.draw_cloud(screen, cloud_x, 100)
    
    def draw_cloud(self, screen, x, y):
        """Draw a simple cloud."""
        cloud_color = WHITE
        pygame.draw.ellipse(screen, cloud_color, (x, y, 60, 30))
        pygame.draw.ellipse(screen, cloud_color, (x + 20, y - 10, 50, 35))
        pygame.draw.ellipse(screen, cloud_color, (x + 40, y, 40, 25))
    
    def draw_hud(self, screen):
        """Draw heads-up display."""
        # Score
        score_text = self.big_font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 20))
        
        # Time
        elapsed = (pygame.time.get_ticks() - self.start_time) // 1000
        time_text = self.font.render(f"Time: {elapsed}s", True, WHITE)
        screen.blit(time_text, (20, 60))
        
        # Instructions
        if self.game_over:
            game_over_text = self.big_font.render("GAME OVER! Press R to restart", True, RED)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2))
        else:
            instructions = self.small_font.render("Flex to JUMP! Collect coins, avoid obstacles", True, WHITE)
            screen.blit(instructions, (SCREEN_WIDTH // 2 - 200, 20))
    
    def draw_connection_status(self, screen, connected):
        """Draw serial connection status."""
        status_text = self.small_font.render(
            f"Serial: {'CONNECTED' if connected else 'DISCONNECTED'} "
            f"{'(' + serial_reader.port + ')' if serial_reader.port and connected else ''}",
            True, GREEN if connected else RED
        )
        screen.blit(status_text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 25))
    
    def render(self, screen, connected):
        """Render the game."""
        # Draw sky
        self.draw_sky(screen)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            obstacle.draw(screen)
        
        # Draw coins
        for coin in self.coins:
            coin.draw(screen)
        
        # Draw ground
        self.draw_ground(screen)
        
        # Draw cat
        self.cat.draw(screen)
        
        # Draw HUD
        self.draw_hud(screen)
        
        # Draw connection status
        self.draw_connection_status(screen, connected)
    
    def reset(self):
        """Reset the game."""
        self.cat = MistralCat()
        self.obstacles = []
        self.coins = []
        self.score = 0
        self.game_over = False
        self.start_time = pygame.time.get_ticks()
        self.scroll_offset = 0
        self.last_obstacle_time = 0
        self.last_coin_time = 0


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
        print("Usage: python mistral_cat_game.py [PORT]")
        print("Example: python mistral_cat_game.py COM3")
        print("        python mistral_cat_game.py /dev/cu.usbmodem14101")
        sys.exit(1)
    
    # Initialize game
    game = MistralCatGame()
    
    # Main game loop
    running = True
    last_read_time = time.time()
    
    print("Mistral Cat Obstacle Game")
    print("========================")
    print("Flex your muscle to JUMP!")
    print("Collect coins, avoid obstacles")
    print("Press ESC to quit, R to restart")
    
    try:
        while running:
            # Handle events
            running = game.handle_events()
            
            # Read serial data
            if time.time() - last_read_time > 0.01:  # Read every 10ms
                if serial_reader.read_data():
                    last_read_time = time.time()
            
            # Update game with current jump state
            game.update(serial_reader.jumping)
            
            # Render
            game.render(game.screen, serial_reader.connected)
            
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
