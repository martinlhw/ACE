import sys
import os
import pygame
from pygame.locals import *
import time
import argparse

# Import local modules
from poker_logic import Game, Card
from poker_signal_receiver import PokerSignalReceiver
from poker_gui import PokerGameGUI

class ArduinoPokerGame(PokerGameGUI):
    def __init__(self, signal_receiver, n_players=4, small_blind=5, initial_pot=1000):
        # Initialize the parent class
        super().__init__(n_players, small_blind, initial_pot)
        
        # Store the signal receiver
        self.signal_receiver = signal_receiver
        
        # Map sensors to player positions (customize based on your setup)
        self.sensor_to_player = {1: 0, 2: 1, 3: 2, 4: 3}
        
        # Chip value conversion (10g = 1 chip)
        self.chip_weight = 10.0
        
        # Game state variables
        self.waiting_for_action = True
        self.active_player = 0
        
        # Status message display
        self.status_message = "Arduino " + ("connected" if signal_receiver.connected else "not connected")
        self.status_time = pygame.time.get_ticks()
        self.status_duration = 3000  # Display status for 3 seconds
    
    def handle_events(self):
        # First handle standard Pygame events
        super().handle_events()
        
        # Then check for Arduino events
        arduino_event = self.signal_receiver.get_next_event()
        if arduino_event:
            self.handle_arduino_event(arduino_event)
    
    def handle_arduino_event(self, event):
        """Handle events from the Arduino."""
        event_type = event['type']
        sensor_id = event['sensor']
        
        # Convert sensor ID to player ID
        if sensor_id in self.sensor_to_player:
            player_id = self.sensor_to_player[sensor_id]
            
            # Only handle events for the current player
            if player_id == self.active_player and self.waiting_for_action:
                if event_type == 'DOUBLE_TAP':
                    self.handle_player_action('check_call')
                    self.status_message = f"Player {player_id} performed check/call"
                    self.status_time = pygame.time.get_ticks()
                
                elif event_type == 'HOLD':
                    self.handle_player_action('fold')
                    self.status_message = f"Player {player_id} folded"
                    self.status_time = pygame.time.get_ticks()
                
                elif event_type == 'WEIGHT':
                    weight_value = event['value']
                    # Convert weight to chips
                    chips = int(weight_value / self.chip_weight)
                    
                    # Set slider value for raise
                    self.slider_value = chips
                    
                    # Handle the raise action
                    self.handle_player_action('raise')
                    self.status_message = f"Player {player_id} raised {chips} chips"
                    self.status_time = pygame.time.get_ticks()
            else:
                self.status_message = f"Ignored event from Player {player_id} - not their turn"
                self.status_time = pygame.time.get_ticks()
    
    def render(self):
        # Render the basic game first
        super().render()
        
        # Add Arduino status information
        current_time = pygame.time.get_ticks()
        if current_time - self.status_time < self.status_duration:
            # Display status message
            status_text = self.font_medium.render(self.status_message, True, (255, 255, 0))
            self.screen.blit(status_text, (50, 80))
        
        # Always display Arduino connection status
        connection_status = "Arduino: " + ("Connected" if self.signal_receiver.connected else "Not Connected")
        connection_color = (0, 255, 0) if self.signal_receiver.connected else (255, 0, 0)
        status_text = self.font_small.render(connection_status, True, connection_color)
        self.screen.blit(status_text, (20, 60))
        
        # Update the display
        pygame.display.flip()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Poker Game with Arduino Integration')
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help='Serial port for Arduino connection')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate for serial connection')
    parser.add_argument('--players', type=int, default=4, help='Number of players')
    args = parser.parse_args()
    
    # Initialize pygame
    pygame.init()
    
    # Create signal receiver
    signal_receiver = PokerSignalReceiver(port=args.port, baud_rate=args.baud)
    
    # Create settings window
    settings_screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Arduino Poker - Settings")
    
    # Set up fonts
    font = pygame.font.SysFont('Arial', 27)
    small_font = pygame.font.SysFont('Arial', 20)
    
    # Default settings
    n_players = args.players
    small_blind = 5
    initial_pot = 1000
    
    # Input fields
    player_input = pygame.Rect(200, 50, 150, 32)
    blind_input = pygame.Rect(200, 100, 150, 32)
    pot_input = pygame.Rect(200, 150, 150, 32)
    
    # Start button
    start_button = pygame.Rect(150, 220, 100, 40)
    
    # For text input
    active_input = None
    player_text = str(n_players)
    blind_text = str(small_blind)
    pot_text = str(initial_pot)
    
    # Colors
    WHITE = (255, 255, 255)
    GREEN = (0, 128, 0)
    BLACK = (0, 0, 0)
    
    # Main settings loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                signal_receiver.disconnect()
                pygame.quit()
                sys.exit()
                
            # Handle mouse clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check which input field was clicked
                if player_input.collidepoint(event.pos):
                    active_input = 'player'
                elif blind_input.collidepoint(event.pos):
                    active_input = 'blind'
                elif pot_input.collidepoint(event.pos):
                    active_input = 'pot'
                elif start_button.collidepoint(event.pos):
                    # Try to convert inputs to numbers
                    try:
                        n_players = max(2, min(10, int(player_text)))
                        small_blind = max(1, int(blind_text))
                        initial_pot = max(100, int(pot_text))
                        
                        # Start the poker game
                        running = False
                    except ValueError:
                        pass
                else:
                    active_input = None
                    
            # Handle key presses
            if event.type == pygame.KEYDOWN:
                if active_input == 'player':
                    if event.key == pygame.K_BACKSPACE:
                        player_text = player_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_input = None
                    elif event.unicode.isdigit():
                        player_text += event.unicode
                elif active_input == 'blind':
                    if event.key == pygame.K_BACKSPACE:
                        blind_text = blind_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_input = None
                    elif event.unicode.isdigit():
                        blind_text += event.unicode
                elif active_input == 'pot':
                    if event.key == pygame.K_BACKSPACE:
                        pot_text = pot_text[:-1]
                    elif event.key == pygame.K_RETURN:
                        active_input = None
                    elif event.unicode.isdigit():
                        pot_text += event.unicode
        
        # Clear the screen
        settings_screen.fill((50, 50, 50))
        
        # Draw title
        title_text = font.render("Arduino Poker - Settings", True, WHITE)
        settings_screen.blit(title_text, (50, 10))
        
        # Draw Arduino status
        status_text = small_font.render(
            f"Arduino {'Connected' if signal_receiver.connected else 'Not Connected'}",
            True, GREEN if signal_receiver.connected else (255, 0, 0))
        settings_screen.blit(status_text, (50, 35))
        
        # Draw input labels and fields
        player_label = font.render("Players:", True, WHITE)
        settings_screen.blit(player_label, (50, 50))
        pygame.draw.rect(settings_screen, WHITE, player_input)
        player_surface = small_font.render(player_text, True, BLACK)
        settings_screen.blit(player_surface, (player_input.x + 5, player_input.y + 5))
        
        blind_label = font.render("Small Blind:", True, WHITE)
        settings_screen.blit(blind_label, (50, 100))
        pygame.draw.rect(settings_screen, WHITE, blind_input)
        blind_surface = small_font.render(blind_text, True, BLACK)
        settings_screen.blit(blind_surface, (blind_input.x + 5, blind_input.y + 5))
        
        pot_label = font.render("Initial Money:", True, WHITE)
        settings_screen.blit(pot_label, (50, 150))
        pygame.draw.rect(settings_screen, WHITE, pot_input)
        pot_surface = small_font.render(pot_text, True, BLACK)
        settings_screen.blit(pot_surface, (pot_input.x + 5, pot_input.y + 5))
        
        # Draw start button
        pygame.draw.rect(settings_screen, GREEN, start_button)
        pygame.draw.rect(settings_screen, BLACK, start_button, 2)
        start_surface = font.render("Start", True, BLACK)
        settings_screen.blit(start_surface, (start_button.x + 25, start_button.y + 8))
        
        # Update the display
        pygame.display.flip()
    
    # Create and run the poker game with selected settings
    poker_game = ArduinoPokerGame(signal_receiver, n_players=n_players, 
                               small_blind=small_blind, initial_pot=initial_pot)
    
    try:
        poker_game.run()
    except KeyboardInterrupt:
        signal_receiver.disconnect()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()