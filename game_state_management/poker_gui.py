import sys
import os
import random
import math
import pygame
from pygame.locals import *

# Import game logic
from poker_logic import Game, Card, evaluate_hand

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 128, 0)
DARK_GREEN = (0, 80, 0)
FELT_GREEN = (34, 139, 34)
TABLE_BORDER = (120, 81, 45)  # Brown wood color
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GOLD = (212, 175, 55)

# Card dimensions
CARD_WIDTH = 80
CARD_HEIGHT = 120

# Table dimensions
TABLE_WIDTH = 900  # Increased size
TABLE_HEIGHT = 600  # Increased size

class PokerGameGUI:
    def __init__(self, n_players=4, small_blind=5, initial_pot=1000):
        # Set up the screen
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Poker Table Monitor")
        self.clock = pygame.time.Clock()
        
        # Create the game logic
        self.game = Game(n_players, small_blind, initial_pot)
        
        # Load resources
        self.load_assets()
        
        # Set up the table
        self.setup_table()
        
        # State variables
        self.current_phase = "setup"  # setup, preflop, flop, turn, river, showdown
        self.active_player = 0
        self.waiting_for_action = False
        self.action_buttons = []
        
        # External updates tracking
        self.last_update_time = pygame.time.get_ticks()
        self.update_interval = 1000  # Update every 1 second (adjust as needed)
        
    def load_assets(self):
        # Load card images
        self.card_images = {}
        self.card_back = pygame.image.load(os.path.join('assets', 'cards', 'back.png'))
        self.card_back = pygame.transform.scale(self.card_back, (CARD_WIDTH, CARD_HEIGHT))
        
        # Load card fronts
        suits = ['H', 'D', 'S', 'C']
        ranks = list(range(1, 14))  # 1=Ace, 2-10, 11=Jack, 12=Queen, 13=King
        
        for suit in suits:
            for rank in ranks:
                # Convert rank to card name format
                if rank == 1:
                    rank_str = 'A'
                elif rank == 11:
                    rank_str = 'J'
                elif rank == 12:
                    rank_str = 'Q'
                elif rank == 13:
                    rank_str = 'K'
                else:
                    rank_str = str(rank)
                
                file_name = f"{rank_str}{suit}.png"
                card_img = pygame.image.load(os.path.join('assets', 'cards', file_name))
                card_img = pygame.transform.scale(card_img, (CARD_WIDTH, CARD_HEIGHT))
                self.card_images[(suit, rank)] = card_img
        
        # Define chip colors instead of loading images
        self.chip_colors = {
            1: (255, 255, 255),    # White for $1
            5: (255, 0, 0),        # Red for $5
            10: (0, 0, 255),       # Blue for $10
            25: (0, 255, 0),       # Green for $25
            100: (0, 0, 0),        # Black for $100
            500: (128, 0, 128)     # Purple for $500
        }
            
        # Load fonts
        self.font_small = pygame.font.SysFont('Arial', 20)
        self.font_medium = pygame.font.SysFont('Arial', 27)
        self.font_large = pygame.font.SysFont('Arial', 40)
        
    def setup_table(self):
        # Set up player positions around the table
        self.player_positions = []
        
        # Calculate positions in an oval around the table
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        table_radius_x = TABLE_WIDTH // 2 + 40  # Add some padding
        table_radius_y = TABLE_HEIGHT // 2 + 40  # Add some padding
        
        for i in range(self.game.n):
            # Distribute players evenly around an oval
            angle = i * (360 / self.game.n)
            # Convert angle to radians
            angle_rad = angle * (3.14159 / 180)
            
            # Calculate position on an oval
            x = center_x + table_radius_x * math.cos(angle_rad)
            y = center_y + table_radius_y * math.sin(angle_rad)
            
            self.player_positions.append((x, y))
        
        # Create action buttons
        button_width, button_height = 100, 40
        button_margin = 10
        button_x = SCREEN_WIDTH - button_width - 20
        button_start_y = SCREEN_HEIGHT - (button_height + button_margin) * 4 - 20
        
        self.action_buttons = [
            {"rect": pygame.Rect(button_x, button_start_y, button_width, button_height),
             "text": "FOLD", "action": "fold", "color": RED},
            {"rect": pygame.Rect(button_x, button_start_y + (button_height + button_margin), button_width, button_height),
             "text": "CHECK/CALL", "action": "check_call", "color": BLUE},
            {"rect": pygame.Rect(button_x, button_start_y + 2 * (button_height + button_margin), button_width, button_height),
             "text": "RAISE", "action": "raise", "color": GREEN},
            {"rect": pygame.Rect(button_x, button_start_y + 3 * (button_height + button_margin), button_width, button_height),
             "text": "ALL IN", "action": "all_in", "color": GOLD}
        ]
        
        # Set up betting slider
        self.slider_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, 300, 20)
        self.slider_button_rect = pygame.Rect(50, SCREEN_HEIGHT - 110, 20, 40)
        self.slider_min = 0
        self.slider_max = 100
        self.slider_value = 0
        self.dragging_slider = False
        
    def start_game(self):
        # Initialize a new game
        self.game.start_game()
        self.current_phase = self.game.phase
        self.active_player = self.game.current_player
        self.waiting_for_action = True
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_SPACE and self.current_phase == "setup":
                    self.start_game()
            
            if self.waiting_for_action and self.active_player == self.game.current_player:

                # Handle button clicks
                if event.type == MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # Check if a button was clicked
                    for button in self.action_buttons:
                        if button["rect"].collidepoint(mouse_pos):
                            self.handle_player_action(button["action"])
                    
                    # Check if slider was clicked
                    if self.slider_rect.collidepoint(mouse_pos) or self.slider_button_rect.collidepoint(mouse_pos):
                        self.dragging_slider = True
                
                # Handle slider dragging
                elif event.type == MOUSEBUTTONUP:
                    self.dragging_slider = False
                
                elif event.type == MOUSEMOTION and self.dragging_slider:
                    mouse_x = max(self.slider_rect.left, min(event.pos[0], self.slider_rect.right))
                    self.slider_button_rect.centerx = mouse_x
                    
                    # Calculate slider value
                    slider_range = self.slider_rect.width
                    relative_pos = mouse_x - self.slider_rect.left
                    self.slider_value = int(self.slider_min + (relative_pos / slider_range) * (self.slider_max - self.slider_min))
    
    def handle_player_action(self, action):
        if action == "fold":
            self.game.active_players.discard(self.active_player)
            print(f"Player {self.active_player} folds")
        
        elif action == "check_call":
            # Determine if it's a check or call based on the current bet
            amount_to_call = self.game.current_bet - self.game.game_pot[self.active_player]
            
            if amount_to_call == 0:
                # Check
                print(f"Player {self.active_player} checks")
            else:
                # Call
                self.game.game_pot[self.active_player] += amount_to_call
                self.game.pots[self.active_player] -= amount_to_call
                print(f"Player {self.active_player} calls {amount_to_call}")
        
        elif action == "raise":
            # Use the slider value for the raise amount
            raise_amount = self.slider_value
            amount_to_call = self.game.current_bet - self.game.game_pot[self.active_player]
            total_amount = amount_to_call + raise_amount
            
            if total_amount <= self.game.pots[self.active_player]:
                self.game.game_pot[self.active_player] += total_amount
                self.game.pots[self.active_player] -= total_amount
                self.game.current_bet = self.game.game_pot[self.active_player]
                
                print(f"Player {self.active_player} raises by {raise_amount} to {self.game.current_bet}")
                # Reset players_acted as everyone needs to respond to the raise
                self.game.players_acted = set([self.active_player])
            else:
                # Not enough chips, treat as all-in
                self.handle_player_action("all_in")
                return
        
        elif action == "all_in":
            # Put all of player's remaining money in the pot
            player_money = self.game.pots[self.active_player]
            if player_money > 0:
                # This might be a raise
                new_bet = self.game.game_pot[self.active_player] + player_money
                if new_bet > self.game.current_bet:
                    self.game.current_bet = new_bet
                    # Reset players_acted as everyone needs to respond to the raise
                    self.game.players_acted = set([self.active_player])
                
                self.game.game_pot[self.active_player] += player_money
                self.game.pots[self.active_player] = 0
                
                print(f"Player {self.active_player} goes ALL IN with {player_money}")
        
        # Add the player to those who have acted
        self.game.players_acted.add(self.active_player)
        
        # Check if round is complete
        round_complete = self.advance_game()
        if round_complete:
            # Advance to the next phase
            self.game.advance_phase()
            self.current_phase = self.game.phase
        
        # Update the active player
        self.active_player = self.game.current_player
        
    def advance_game(self):
        """Move to the next player or phase if all players have acted."""
        # Check if only one player remains
        if len(self.game.active_players) == 1:
            winner = list(self.game.active_players)[0]
            total_pot = sum(self.game.game_pot.values())
            self.game.pots[winner] += total_pot
            print(f"Player {winner} wins {total_pot} (all others folded)")
            self.current_phase = "setup"
            return False  # Don't advance further
        
        # Check if all active players have acted and their bets match
        all_acted = True
        for player in self.game.active_players:
            if player not in self.game.players_acted:
                all_acted = False
                break
            if self.game.game_pot[player] < self.game.current_bet:
                # Player needs to call, check, raise, or fold
                all_acted = False
                break
        
        if all_acted:
            return True  # Round is complete, advance phase
        
        # Move to the next player
        return self.game.move_to_next_player()
        
    def render(self):
        # Clear the screen
        self.screen.fill((50, 50, 50))  # Dark gray background
        
        # Draw the poker table
        center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        
        # Draw table border (wooden rim)
        pygame.draw.ellipse(self.screen, TABLE_BORDER, 
                          (center_x - TABLE_WIDTH//2 - 15, 
                           center_y - TABLE_HEIGHT//2 - 15,
                           TABLE_WIDTH + 30, 
                           TABLE_HEIGHT + 30))
        
        # Draw the felt table surface
        pygame.draw.ellipse(self.screen, FELT_GREEN, 
                          (center_x - TABLE_WIDTH//2, 
                           center_y - TABLE_HEIGHT//2,
                           TABLE_WIDTH, 
                           TABLE_HEIGHT))
        
        # Draw a darker felt inner area
        pygame.draw.ellipse(self.screen, DARK_GREEN, 
                          (center_x - TABLE_WIDTH//2 + 20, 
                           center_y - TABLE_HEIGHT//2 + 20,
                           TABLE_WIDTH - 40, 
                           TABLE_HEIGHT - 40))
        
        # Draw dealer button 
        dealer_button_pos = self.player_positions[self.game.x]
        button_x = dealer_button_pos[0] + 40
        button_y = dealer_button_pos[1] - 20
        pygame.draw.circle(self.screen, WHITE, (int(button_x), int(button_y)), 15)
        dealer_text = self.font_small.render("D", True, BLACK)
        self.screen.blit(dealer_text, (button_x - dealer_text.get_width()//2, button_y - dealer_text.get_height()//2))
        
        # Draw the pot
        pot_amount = sum(self.game.game_pot.values())
        pot_text = self.font_medium.render(f"Pot: ${pot_amount}", True, WHITE)
        self.screen.blit(pot_text, (SCREEN_WIDTH // 2 - pot_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
        
        # Draw chips for the pot in the center of the table
        if pot_amount > 0:
            self.draw_chips(pot_amount, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, spread=True)
        
        # Draw community cards if any
        if hasattr(self.game, 'community') and self.game.community:
            card_spacing = 10
            total_width = len(self.game.community) * (CARD_WIDTH + card_spacing) - card_spacing
            start_x = (SCREEN_WIDTH - total_width) // 2
            
            for i, card in enumerate(self.game.community):
                card_x = start_x + i * (CARD_WIDTH + card_spacing)
                card_y = SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 - 50
                self.draw_card(card, card_x, card_y)
        
        # Draw players and their cards
        for i in range(self.game.n):
            x, y = self.player_positions[i]
            
            # Draw player position marker
            if i in self.game.active_players:
                if i == self.active_player and self.waiting_for_action:
                    # Highlight active player
                    pygame.draw.circle(self.screen, GOLD, (int(x), int(y)), 60)
                pygame.draw.circle(self.screen, GREEN, (int(x), int(y)), 50)
            else:
                # Folded player
                pygame.draw.circle(self.screen, RED, (int(x), int(y)), 50)
            
            # Draw player label
            player_text = self.font_small.render(f"Player {i}", True, WHITE)
            self.screen.blit(player_text, (x - player_text.get_width() // 2, y - 5))
            
            # Draw player's pot
            pot_text = self.font_small.render(f"${self.game.pots[i]}", True, WHITE)
            self.screen.blit(pot_text, (x - pot_text.get_width() // 2, y + 15))
            
            # Draw player's current bet
            bet_amount = self.game.game_pot[i]
            bet_text = self.font_small.render(f"Bet: ${bet_amount}", True, WHITE)
            self.screen.blit(bet_text, (x - bet_text.get_width() // 2, y + 35))
            
            # Draw chips for the current bet
            if bet_amount > 0:
                # Position the chips between the player and the center of the table
                center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                chip_x = x + (center_x - x) // 3
                chip_y = y + (center_y - y) // 3
                self.draw_chips(bet_amount, chip_x, chip_y, spread=False)
            
            # Draw player's cards - always face down except during showdown
            if hasattr(self.game, 'hands') and i in self.game.hands:
                # Calculate positions for the two cards
                card1_x = x - CARD_WIDTH - 5
                card2_x = x + 5
                card_y = y - CARD_HEIGHT - 20
                
                # Only show cards face-up during showdown, otherwise face down for all except active player
                if self.current_phase == "showdown":
                    for j, card in enumerate(self.game.hands[i]):
                        self.draw_card(card, card1_x if j == 0 else card2_x, card_y)
                else:
                    # Face down for all players
                    self.screen.blit(self.card_back, (card1_x, card_y))
                    self.screen.blit(self.card_back, (card2_x, card_y))
        
        # Draw action buttons if waiting for player action
        if self.waiting_for_action and self.active_player == 0:  # Only draw buttons for human player
            for button in self.action_buttons:
                pygame.draw.rect(self.screen, button["color"], button["rect"])
                pygame.draw.rect(self.screen, BLACK, button["rect"], 2)
                
                button_text = self.font_small.render(button["text"], True, BLACK)
                text_x = button["rect"].centerx - button_text.get_width() // 2
                text_y = button["rect"].centery - button_text.get_height() // 2
                self.screen.blit(button_text, (text_x, text_y))
            
            # Draw slider for raise amount
            pygame.draw.rect(self.screen, WHITE, self.slider_rect)
            pygame.draw.rect(self.screen, BLACK, self.slider_rect, 2)
            pygame.draw.rect(self.screen, BLUE, self.slider_button_rect)
            
            # Draw slider value
            value_text = self.font_small.render(f"Raise: ${self.slider_value}", True, WHITE)
            self.screen.blit(value_text, (self.slider_rect.x, self.slider_rect.y - 20))
        
        # Draw current phase
        phase_text = self.font_large.render(self.current_phase.upper(), True, WHITE)
        self.screen.blit(phase_text, (20, 20))
        
        # Draw prompt for starting the game if in setup phase
        if self.current_phase == "setup":
            start_text = self.font_medium.render("Press SPACE to start new game", True, WHITE)
            self.screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT - 50))
            
        # Update the display
        pygame.display.flip()
        
    def draw_card(self, card, x, y):
        # Draw a card at the specified position
        card_key = (card.suit, card.rank)
        if card_key in self.card_images:
            self.screen.blit(self.card_images[card_key], (x, y))
            
    def draw_chips(self, amount, x, y, spread=True):
        # Draw chips as colored circles with text
        # Break down the amount into standard poker chip denominations
        remaining = amount
        chips = []
        
        # Standard chip denominations in descending order
        denominations = [500, 100, 25, 10, 5, 1]
        
        # Calculate how many chips of each denomination we need
        for denom in denominations:
            count = remaining // denom
            remaining %= denom
            
            if count > 0:
                chips.extend([denom] * min(count, 5))  # Limit to 5 chips per denomination for visual clarity
        
        # If we still have remaining amount, add a chip for it
        if remaining > 0:
            chips.append(remaining)
        
        # Draw the chips in a stack or spread
        chip_size = 30
        spacing = 15 if spread else 5
        
        for i, chip_value in enumerate(chips[:10]):  # Limit to 10 chips max for visual clarity
            # Determine position (stacked or in a row)
            if spread:
                chip_x = x + i * spacing
                chip_y = y
            else:
                chip_x = x
                chip_y = y - i * spacing
            
            # Get chip color
            color = self.chip_colors.get(chip_value, (200, 200, 0))  # Default to gold for non-standard values
            
            # Draw chip as a circle
            pygame.draw.circle(self.screen, color, (int(chip_x), int(chip_y)), chip_size)
            pygame.draw.circle(self.screen, WHITE, (int(chip_x), int(chip_y)), chip_size, 2)  # White border
            
            # Draw chip value as text
            value_text = self.font_small.render(f"${chip_value}", True, BLACK)
            text_x = chip_x - value_text.get_width() // 2
            text_y = chip_y - value_text.get_height() // 2
            self.screen.blit(value_text, (text_x, text_y))
        
        # If there are more chips than we're showing, indicate that
        if len(chips) > 10:
            more_text = self.font_small.render(f"+{len(chips) - 10} more", True, WHITE)
            if spread:
                text_x = x + 10 * spacing
                text_y = y
            else:
                text_x = x
                text_y = y - 10 * spacing
            self.screen.blit(more_text, (text_x, text_y))
        
    def run(self):
        while True:
            self.handle_events()
            self.render()
            self.clock.tick(FPS)