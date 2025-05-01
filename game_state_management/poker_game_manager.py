import sys
import os
import pygame
from pygame.locals import *
import time
import argparse
import socket


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
        
        # Store the socket connection
        self.socket_conn = socket_conn
        
        # Map sensors to player positions
        self.sensor_to_player = {1: 1, 2: 2, 3: 3, 4: 4}
        
        # Chip value conversion
        self.chip_weight = 10.0
        
        # Game state variables
        self.waiting_for_action = True
        self.active_player = 0
        
        # Status message display
        self.status_message = "Arduino " + ("connected" if signal_receiver.connected else "not connected")
        self.status_time = pygame.time.get_ticks()
        self.status_duration = 3000
        
        # Card detection variables
        self.detected_cards = []
        self.last_detected_card = None
        self.card_detection_time = 0
        self.card_display_duration = 5000  # Display detected card for 5 seconds

    def handle_card_detection(self, card):
        """Handle a card detection from the card detector."""
        # Store the detected card
        self.last_detected_card = card
        self.card_detection_time = pygame.time.get_ticks()
        
        # Add to our list of detected cards if it's not already in there
        if card not in self.detected_cards:
            self.detected_cards.append(card)
        
        # Update status message
        self.status_message = f"Detected card: {card}"
        self.status_time = pygame.time.get_ticks()
        
        print(f"Card detected: {card}")

    def handle_events(self):
        # First handle standard Pygame events
        super().handle_events()
        
        # Then check for Arduino events
        arduino_event = self.signal_receiver.get_next_event()
        if arduino_event:
            self.handle_arduino_event(arduino_event)
        
        # Check for card detection data
        if self.socket_conn:
            try:
                # Make socket non-blocking
                self.socket_conn.setblocking(False)
                
                try:
                    # Try to receive data
                    data = self.socket_conn.recv(1024)
                    if data:
                        # Process the card detection string
                        card_class = data.decode('utf-8').strip()
                        if card_class:  # If not empty
                            self.handle_card_detection(card_class)
                except BlockingIOError:
                    # No data available, this is normal in non-blocking mode
                    pass
                except Exception as e:
                    print(f"Error receiving data: {e}")
            except Exception as e:
                print(f"Socket error: {e}")
                self.socket_conn = None
    
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
        
        # Display status message if recent
        if current_time - self.status_time < self.status_duration:
            status_text = self.font_medium.render(self.status_message, True, (255, 255, 0))
            self.screen.blit(status_text, (50, 80))
        
        # Display Arduino connection status
        connection_status = "Arduino: " + ("Connected" if self.signal_receiver.connected else "Not Connected")
        connection_color = (0, 255, 0) if self.signal_receiver.connected else (255, 0, 0)
        status_text = self.font_small.render(connection_status, True, connection_color)
        self.screen.blit(status_text, (20, 40))
        
        # Display card detector connection status
        detector_status = "Card Detector: " + ("Connected" if self.socket_conn else "Not Connected")
        detector_color = (0, 255, 0) if self.socket_conn else (255, 0, 0)
        detector_text = self.font_small.render(detector_status, True, detector_color)
        self.screen.blit(detector_text, (20, 60))
        
        # Display the most recently detected card if detection is recent
        if self.last_detected_card and current_time - self.card_detection_time < self.card_display_duration:
            card_text = self.font_medium.render(f"Detected Card: {self.last_detected_card}", True, (255, 255, 255))
            self.screen.blit(card_text, (self.width // 2 - card_text.get_width() // 2, 120))
        
        # Display all detected cards
        if self.detected_cards:
            cards_text = self.font_small.render("Detected Cards: " + ", ".join(self.detected_cards[-5:]), True, (200, 200, 200))
            self.screen.blit(cards_text, (20, self.height - 30))
        
        # Update the display
        pygame.display.flip()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Poker Game with Arduino Integration')
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help='Serial port for Arduino connection')
    parser.add_argument('--baud', type=int, default=9600, help='Baud rate for serial connection')
    parser.add_argument('--players', type=int, default=4, help='Number of players')
    parser.add_argument('--host', type=str, default='localhost', help='Host for socket connection')
    parser.add_argument('--socket-port', type=int, default=12345, help='Port for socket connection')
    args = parser.parse_args()
    
    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Define host and port
    host = args.host if hasattr(args, 'host') else 'localhost'
    port = args.socket_port if hasattr(args, 'socket_port') else 12345
    
    # Bind the socket
    try:
        server_socket.bind((host, port))
        # Listen for connections
        server_socket.listen(1)
        server_socket.setblocking(False)  # Make socket non-blocking
        print(f"Server listening on {host}:{port}")
    except Exception as e:
        print(f"Failed to bind socket: {e}")
        sys.exit(1)
    
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
    
    # Socket connection
    conn = None
    
    # Main settings loop
    running = True
    while running:
        # Try to accept a connection from the card detector
        if conn is None:
            try:
                # Non-blocking accept
                conn, addr = server_socket.accept()
                conn.setblocking(False)  # Make the connection non-blocking too
                print(f"Card detector connected from {addr}")
            except BlockingIOError:
                # No connection available yet, which is fine
                pass
            except Exception as e:
                print(f"Error accepting connection: {e}")
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                if conn:
                    conn.close()
                server_socket.close()
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
        
        # Check for data from card detector during setup
        if conn:
            try:
                data = conn.recv(1024)
                if data:
                    print(f"Received from card detector during setup: {data.decode('utf-8').strip()}")
                    # No need to process further during setup
            except BlockingIOError:
                # No data available, which is fine
                pass
            except Exception as e:
                print(f"Error receiving data: {e}")
                conn = None
        
        # Clear the screen
        settings_screen.fill((50, 50, 50))
        
        # Draw title
        title_text = font.render("Arduino Poker - Settings", True, WHITE)
        settings_screen.blit(title_text, (50, 10))
        
        # Draw connection statuses
        arduino_status = f"Arduino: {'Connected' if signal_receiver.connected else 'Not Connected'}"
        arduino_color = GREEN if signal_receiver.connected else (255, 0, 0)
        arduino_text = small_font.render(arduino_status, True, arduino_color)
        settings_screen.blit(arduino_text, (50, 35))
        
        detector_status = f"Card Detector: {'Connected' if conn else 'Waiting...'}"
        detector_color = GREEN if conn else (255, 165, 0)  # Orange for waiting
        detector_text = small_font.render(detector_status, True, detector_color)
        settings_screen.blit(detector_text, (220, 35))
        
        # Draw input labels and fields
        player_label = font.render("Players:", True, WHITE)
        settings_screen.blit(player_label, (50, 60))
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
        
        # Small delay to reduce CPU usage
        pygame.time.delay(50)
    
    # Create and run the poker game with selected settings
    poker_game = ArduinoPokerGame(
        signal_receiver=signal_receiver,
        socket_conn=conn,
        n_players=n_players,
        small_blind=small_blind,
        initial_pot=initial_pot
    )
    
    try:
        poker_game.run()
    except KeyboardInterrupt:
        if conn:
            conn.close()
        server_socket.close()
        signal_receiver.disconnect()
        pygame.quit()
        sys.exit()
    finally:
        if conn:
            conn.close()
        server_socket.close()
        

if __name__ == "__main__":
    main()