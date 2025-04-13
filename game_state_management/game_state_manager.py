class Card:
    def __init__(self, suit, rank):
        self.suit = suit  # 'S', 'D', 'H', 'C'
        self.rank = rank  # 1 (Ace) through 13 (King)
    
    def __str__(self):
        rank_map = {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}
        rank_str = rank_map.get(self.rank, str(self.rank))
        return f"{rank_str}{self.suit}"
        
class Score:
    def __init__(self, category, first=0, second=0, third=0, fourth=0, fifth=0, 
                higher=0, lower=0):
        
        self.category = category
        # Initialize score
        self.score = 0
        
        # Store original values (for testing)
        self.first = first
        self.second = second
        self.third = third 
        self.fourth = fourth 
        self.fifth = fifth 
        self.higher = higher 
        self.lower = lower 
        
        # Convert values for scoring
        first_converted = self.convert(first)
        second_converted = self.convert(second)
        third_converted = self.convert(third)
        fourth_converted = self.convert(fourth)
        fifth_converted = self.convert(fifth)
        higher_converted = self.convert(higher)
        lower_converted = self.convert(lower)
        
        if category == 'straight flush':
            self.score += 8
        elif category == 'four of a kind':
            self.score += 7
        elif category == 'full house':
            self.score += 6
        elif category == 'flush':
            self.score += 5
        elif category == 'straight':
            self.score += 4
        elif category == 'triple':
            self.score += 3
        elif category == 'two pair':
            self.score += 2
        elif category == 'one pair': 
            self.score += 1
        # No points for 'no pair'
        
        self.score *= (14**5)
        if category == 'straight flush':
            self.score += higher_converted 
        elif category == 'four of a kind':
            self.score += higher_converted * 14
            self.score += first_converted
        elif category == 'full house':
            self.score += higher_converted * 14
            self.score += lower_converted
        elif category == 'flush':
            self.score += first_converted * (14 ** 4)
            self.score += second_converted * (14 ** 3)
            self.score += third_converted * (14 ** 2)
            self.score += fourth_converted * (14 ** 1)
            self.score += fifth_converted 
        elif category == 'straight':
            self.score += higher_converted
        elif category == 'triple':
            self.score += higher_converted * (14 ** 2)
            self.score += first_converted * 14
            self.score += second_converted
        elif category == 'two pair':
            self.score += higher_converted * (14 ** 2)
            self.score += lower_converted * 14
            self.score += first_converted
        elif category == 'one pair': 
            self.score += higher_converted * (14 ** 3)
            self.score += first_converted * (14 ** 2)
            self.score += second_converted * 14
            self.score += third_converted 
        elif category == 'no pair':
            self.score += first_converted * (14 ** 4)
            self.score += second_converted * (14 ** 3)
            self.score += third_converted * (14 ** 2)
            self.score += fourth_converted * (14 ** 1)
            self.score += fifth_converted 
    
    # Convert rank so that ACE is most valuable
    def convert(self, rank):
        return 13 if rank == 1 else rank-1
        
    def get_score(self):
        return self.score
        
    def __str__(self):
        return f"{self.category} - Score: {self.score}"

# Takes a list of 7 Card objects
def count_frequencies(hand):
    frequency = {}
    for card in hand:
        rank = card.rank
        if rank in frequency:
            frequency[rank] += 1
        else:
            frequency[rank] = 1
    
    quadruples = []
    triples = []
    pairs = []
    
    for rank, count in frequency.items():
        if count == 4:
            quadruples.append(rank)
        elif count == 3:
            triples.append(rank)
        elif count == 2:
            pairs.append(rank)

    # Sort all ranks in descending order (high to low)
    # Get all unique ranks for kickers, sort with Ace (1) as highest
    unique_ranks = sorted(frequency.keys(), key=lambda r: (14 if r == 1 else r), reverse=True)
    
    # Ensure we have enough cards for kickers
    while len(unique_ranks) < 5:
        unique_ranks.append(0)  # Pad with 0s if not enough cards
    
    # Sort high to low (with Ace as highest)
    quadruples.sort(reverse=True)
    triples.sort(reverse=True)
    pairs.sort(reverse=True)
    
    if quadruples:
        # For four of a kind, get the highest kicker
        kickers = [r for r in unique_ranks if r != quadruples[0]]
        return Score('four of a kind', higher=quadruples[0], first=kickers[0])
    
    if len(triples) >= 2:
        return Score('full house', higher=triples[0], lower=triples[1])
    
    if triples and pairs:
        return Score('full house', higher=triples[0], lower=pairs[0])
    
    if triples:
        # Find the 2 highest cards that aren't in the triple
        kickers = [r for r in unique_ranks if r != triples[0]]
        return Score('triple', higher=triples[0], first=kickers[0], second=kickers[1])
    
    if len(pairs) >= 2:
        # Sort pairs with Ace high
        sorted_pairs = sorted(pairs, key=lambda r: (14 if r == 1 else r), reverse=True)
        # Find the highest card that isn't in either pair
        kickers = [r for r in unique_ranks if r != sorted_pairs[0] and r != sorted_pairs[1]]
        return Score('two pair', higher=sorted_pairs[0], lower=sorted_pairs[1], first=kickers[0])
    
    if pairs:
        # Find the 3 highest cards that aren't in the pair
        kickers = [r for r in unique_ranks if r != pairs[0]]
        return Score('one pair', higher=pairs[0], first=kickers[0], 
                    second=kickers[1], third=kickers[2])
    
    # No pair - use the 5 highest cards
    return Score('no pair', first=unique_ranks[0], second=unique_ranks[1],
                third=unique_ranks[2], fourth=unique_ranks[3],
                fifth=unique_ranks[4])

# hand is a list of Card objects
def check_straight(hand):
    # Create rank presence array (0-indexed, with Ace at both 0 and 13)
    mapping = [False] * 14
    
    for card in hand:
        rank = card.rank
        mapping[rank-1] = True
        if rank == 1:  # Ace can be low (A-5) or high (10-A)
            mapping[13] = True
    
    # Check for 5 consecutive cards, starting from the highest possible straight
    for i in range(13, 3, -1):
        if mapping[i] and mapping[i-1] and mapping[i-2] and mapping[i-3] and mapping[i-4]:
            # Return the highest card in the straight
            return Score('straight', higher=i+1 if i < 13 else 1)
    
    # Check A-5 straight specifically
    if mapping[0] and mapping[1] and mapping[2] and mapping[3] and mapping[12]:
        return Score('straight', higher=5)  # 5-high straight
        
    return None

# hand is a list of Card objects
def check_flush(hand):
    # Group cards by suit
    suit_groups = {}
    for card in hand:
        suit = card.suit
        if suit in suit_groups:
            suit_groups[suit].append(card)
        else:
            suit_groups[suit] = [card]
    
    # Check each suit group for a flush
    for suit, cards in suit_groups.items():
        if len(cards) >= 5:
            # Check for straight flush first
            straight = check_straight(cards)
            if straight:
                return Score('straight flush', higher=straight.higher)
            
            # Otherwise, it's a regular flush
            # Sort cards by rank in descending order (Ace high)
            # We need to handle Ace (1) as highest card
            cards_sorted = sorted(cards, key=lambda card: (14 if card.rank == 1 else card.rank), reverse=True)
            
            # Get the top 5 cards for the flush
            return Score('flush', 
                        first=cards_sorted[0].rank, 
                        second=cards_sorted[1].rank,
                        third=cards_sorted[2].rank, 
                        fourth=cards_sorted[3].rank, 
                        fifth=cards_sorted[4].rank,
                        )
    
    return None

# Evaluate a 7-card hand and return the best 5-card hand and its score
def evaluate_hand(hand):
    # Check for flush and straight flush
    flush_result = check_flush(hand)
    
    # Check for straight
    straight_result = check_straight(hand)
    
    # Check for pairs, trips, etc.
    pairs_result = count_frequencies(hand)
    
    # Find the best hand
    best_score = -1
    best_hand = None
    
    if flush_result and flush_result.get_score() > best_score:
        best_score = flush_result.get_score()
        best_hand = flush_result
        
    if straight_result and straight_result.get_score() > best_score:
        best_score = straight_result.get_score()
        best_hand = straight_result
        
    if pairs_result and pairs_result.get_score() > best_score:
        best_score = pairs_result.get_score()
        best_hand = pairs_result
        
    return best_hand

class Game:
    # int n : number of player
    # int blind_pot_size : fixed small blind amount
    # int initial_pot_size : initial amount of money distributed to each player
    def __init__(self, n, blind_pot_size, initial_pot_size): 
        # Small blind size
        self.sb = blind_pot_size 
        
        # Big blind size
        self.bb = blind_pot_size * 2
        
        # Table for each player's total pot size
        self.pots = {i: initial_pot_size for i in range(n)}
        
        # Player index who is small blind for this game
        self.x = 0 
        
        # Number of total players
        self.n = n 
    
    def start_game(self):
        # Table for each player's current bet in this round
        # All players have to match in order to play the game
        self.game_pot = {i: 0 for i in range(self.n)}
        
        # Current bet that all active players must match or fold
        self.current_bet = 0
        
        # Track active players (not folded)
        self.active_players = set(range(self.n))
        
        # Hands of each player (7 cards = 2 hole cards + 5 community)
        self.hands = {i: [] for i in range(self.n)}
        
        # Community cards
        self.community = []
        
        # Deal initial hole cards (would be handled by actual input)
        self.deal_hole_cards()
        
        # Set initial blinds
        self.game_pot[self.x] = self.sb  # Small blind
        self.pots[self.x] -= self.sb    # Deduct from player's total pot
        
        self.game_pot[(self.x + 1) % self.n] = self.bb  # Big blind
        self.pots[(self.x + 1) % self.n] -= self.bb    # Deduct from player's total pot
        
        self.current_bet = self.bb
        
        # Resume game by calling each phase
        self.preflop_phase()
        
        # Only continue if more than one player is active
        if len(self.active_players) > 1:
            self.flop_phase()
            
            # Continue only if more than one player is active
            if len(self.active_players) > 1:
                self.turn_phase()
                
                # Continue only if more than one player is active
                if len(self.active_players) > 1:
                    self.river_phase()
        
        # If only one player is left, they win automatically
        if len(self.active_players) == 1:
            winner = list(self.active_players)[0]
            total_pot = sum(self.game_pot.values())
            self.pots[winner] += total_pot
            print(f"Player {winner} wins ${total_pot} as all other players folded!")
    
    # Tap Detected by 
    def tap_detection(self):
        
    
    # This function is written by Claude Sonnet 3.7, only used for interim demo
    # This function will be replaced when card detection works.
    def deal_hole_cards(self):
        # For a terminal-based implementation, we'll simulate dealing cards
        # In a real implementation, this would receive input from cameras
        
        # Create a deck of cards
        suits = ['H', 'D', 'S', 'C']
        ranks = list(range(1, 14))  # 1=Ace, 2-10, 11=Jack, 12=Queen, 13=King
        
        deck = []
        for suit in suits:
            for rank in ranks:
                deck.append(Card(suit, rank))
        
        # Shuffle the deck
        import random
        random.shuffle(deck)
        
        # Deal 2 cards to each player
        for player in range(self.n):
            self.hands[player] = [deck.pop(), deck.pop()]
            
        # Set aside 5 cards for the community cards
        self.community_deck = [deck.pop() for _ in range(5)]
        
    # This function is written by Claude Sonnet 3.7, only used for interim demo
    # This function will be replaced when card detection works.
    def display_cards(self, player=None):
        # Display community cards
        print("\nCommunity Cards:", end=" ")
        if not self.community:
            print("None yet")
        else:
            for card in self.community:
                print(card, end=" ")
            print()
        
        # Display player's hand if specified
        if player is not None:
            print(f"\nPlayer {player}'s Hand:", end=" ")
            for card in self.hands[player]:
                print(card, end=" ")
            print()

    def decide_winner(self):
        print("\n=== SHOWDOWN ===")
        
        # Identify who is still playing
        playing = list(self.active_players)
            
        if not playing:
            print("No players still playing")
            return
        
        best_score = -1
        best_player = []
        player_hands = {}
        
        # Display all community cards
        print("\nCommunity Cards:", end=" ")
        for card in self.community:
            print(card, end=" ")
        print("\n")
        
        # Get score for each player's hand
        for player in playing:
            # Combine player's hole cards with community cards
            full_hand = self.hands[player] + self.community
            
            # Evaluate the hand
            hand_result = evaluate_hand(full_hand)
            
            # Store the result
            player_hands[player] = hand_result
            
            # Show player's cards and hand
            print(f"Player {player}'s Hand:", end=" ")
            for card in self.hands[player]:
                print(card, end=" ")
            print(f" → {hand_result.category}")
            
            if hand_result:
                cur_score = hand_result.get_score()
                
                if cur_score > best_score:
                    best_score = cur_score
                    best_player = [player]
                elif cur_score == best_score:
                    best_player.append(player)
        
        # Calculate total pot
        total_pot = sum(self.game_pot.values())
        
        print("\n--- Result ---")
        
        # Adjust pot accordingly
        if len(best_player) == 1:
            # Add to winner's pot
            winner = best_player[0]
            self.pots[winner] += total_pot
            print(f"Player {winner} wins ${total_pot} with {player_hands[winner].category}!")
        else:
            # There was a tie: distribute to all winners
            split_amount = total_pot // len(best_player)
            remainder = total_pot % len(best_player)
            
            winners_str = ", ".join([str(p) for p in best_player])
            print(f"Tie between players {winners_str}!")
            print(f"Each wins ${split_amount} with {player_hands[best_player[0]].category}!")
            
            for winner in best_player:
                self.pots[winner] += split_amount
            
            if remainder > 0:
                print(f"Remainder ${remainder} goes to the house.")
                
        # Show updated pot sizes
        print("\nUpdated pot sizes:")
        for player in range(self.n):
            if player in self.active_players:
                status = "active"
            else:
                status = "folded"
            print(f"Player {player}: ${self.pots[player]} ({status})")

    def wait_for_bet(self, player):
        # Get actual user input from terminal
        print(f"\nPlayer {player}'s turn")
        print(f"Current pot: {sum(self.game_pot.values())}")
        print(f"Current bet to match: {self.current_bet}")
        print(f"Your current bet: {self.game_pot[player]}")
        print(f"Your remaining money: {self.pots[player]}")
        
        # Calculate how much the player needs to call
        amount_to_call = self.current_bet - self.game_pot[player]
        
        # Show available options based on current game state
        options = []
        
        # Always show fold option
        options.append("fold")
        
        if amount_to_call > 0:
            # Need to at least call or fold
            options.append(f"call {amount_to_call}")
        else:
            # Can check
            options.append("check")
        
        # Can always raise if you have money
        if self.pots[player] > amount_to_call:
            options.append("raise [amount]")
        
        # Display options to the player
        print("\nAvailable actions:")
        for i, option in enumerate(options):
            print(f"{i+1}. {option}")
            
        # Get player's choice
        while True:
            action = input("\nEnter your action (type the number or the action): ").strip().lower()
            
            # Handle numeric input
            if action.isdigit():
                action_num = int(action)
                if 1 <= action_num <= len(options):
                    action = options[action_num-1]
                    # Handle "call X" option by extracting just "call"
                    if action.startswith("call "):
                        action = "call"
                else:
                    print("Invalid option number. Try again.")
                    continue
            
            # Process text input
            if action == "fold":
                return "fold"
                
            elif action == "call":
                # Check if player has enough money
                if self.pots[player] < amount_to_call:
                    print(f"You don't have enough money to call. You need {amount_to_call} but only have {self.pots[player]}.")
                    continue
                return "call"
                
            elif action == "check":
                if amount_to_call > 0:
                    print(f"You can't check. You need to call {amount_to_call} or fold.")
                    continue
                return "check"
                
            elif action.startswith("raise"):
                # Extract the raise amount
                try:
                    if " " in action:
                        raise_amount = int(action.split(" ")[1])
                    else:
                        raise_amount = int(input("Enter raise amount: "))
                        
                    # Validate the raise amount
                    if raise_amount <= 0:
                        print("Raise amount must be positive.")
                        continue
                        
                    total_needed = amount_to_call + raise_amount
                    
                    if total_needed > self.pots[player]:
                        print(f"You don't have enough money. Maximum raise: {self.pots[player] - amount_to_call}")
                        continue
                        
                    return f"raise:{raise_amount}"
                except ValueError:
                    print("Please enter a valid number for the raise amount.")
                    continue
            
            else:
                print("Invalid action. Please try again.")
                continue

    def take_turns(self):
        # First set to the player next to big blind in preflop, or small blind in later rounds
        if not self.community:  # Preflop
            cur_player = (self.x + 2) % self.n
        else:
            cur_player = self.x
        
        # Track whether everyone has had a chance to act after the last raise
        players_acted = set()
        last_raiser = None
        round_complete = False
        
        while not round_complete:
            # Skip players who folded
            if cur_player not in self.active_players:
                cur_player = (cur_player + 1) % self.n
                continue
            
            # Show divider for readability
            print("\n" + "-" * 50)    
                
            # Display current game state
            print(f"\nCurrent pot: {sum(self.game_pot.values())}")
            print(f"Current bet to match: {self.current_bet}")
            
            # Show the player their cards
            self.display_cards(cur_player)
            
            # Get player's action
            action = self.wait_for_bet(cur_player)
            
            if action == "fold": # sensing card throw with CV
                self.active_players.remove(cur_player)
                print(f"Player {cur_player} folds")
                
            elif action == "call": # sensing weight scale
                amount_to_call = self.current_bet - self.game_pot[cur_player]
                self.game_pot[cur_player] += amount_to_call
                self.pots[cur_player] -= amount_to_call
                print(f"Player {cur_player} calls {amount_to_call}")
                players_acted.add(cur_player)
                
            elif action == "check": # sensing from from resistive sensor
                print(f"Player {cur_player} checks")
                players_acted.add(cur_player)
                
            elif action.startswith("raise:"): # sensing weight scale
                raise_amount = int(action.split(":")[1])
                amount_to_call = self.current_bet - self.game_pot[cur_player]
                total_amount = amount_to_call + raise_amount
                
                self.game_pot[cur_player] += total_amount
                self.pots[cur_player] -= total_amount
                self.current_bet += raise_amount
                
                print(f"Player {cur_player} raises by {raise_amount} to {self.current_bet}")
                
                # When a player raises, we need to give others a chance to respond
                players_acted = {cur_player}
                last_raiser = cur_player
            
            # Add a small pause between players for readability
            input("\nPress Enter to continue to next player...")
            
            # Move to the next player
            cur_player = (cur_player + 1) % self.n
            
            # Check if the round is complete
            if len(self.active_players) <= 1:
                # Only one player left, round complete
                round_complete = True
            elif players_acted == self.active_players:
                # All active players have acted since the last raise
                round_complete = True
            elif cur_player == last_raiser and last_raiser is not None:
                # We've gone full circle back to the last raiser
                round_complete = True
        
        print("\nBetting round complete")
    
    def preflop_phase(self):
        input("\nPress Enter to start game...")
        
        print("\n=== PREFLOP PHASE ===")
        # Players take turns to bet
        self.take_turns()
        return 0

    def flop_phase(self):
        print("\n=== FLOP PHASE ===")
        
        # In a real implementation, receive input from camera to detect cards
        # For our terminal implementation, we'll use the pre-dealt community cards
        # Add the first three community cards (the flop)
        self.community = self.community_deck[:3]
        
        print("Dealing the flop...")
        self.display_cards()
        
        # Reset current bet for new round
        self.current_bet = 0
        
        # Then players take turns to bet
        self.take_turns()

    def turn_phase(self):
        print("\n=== TURN PHASE ===")
        
        # Add the fourth community card (the turn)
        self.community.append(self.community_deck[3])
        
        print("Dealing the turn...")
        self.display_cards()
        
        # Reset current bet for new round
        self.current_bet = 0
        
        # Then players take turns to bet
        self.take_turns()

    def river_phase(self):
        print("\n=== RIVER PHASE ===")
        
        # Add the fifth community card (the river)
        self.community.append(self.community_deck[4])
        
        print("Dealing the river...")
        self.display_cards()
        
        # Reset current bet for new round
        self.current_bet = 0
        
        # Then players take turns to bet
        self.take_turns()
        
        # Finally, decide the winner and adjust player's pot
        self.decide_winner()
        
        # Increment small blind for the next game
        self.x = (self.x + 1) % self.n


def main():
    # Get user input from terminal
    try:
        print("Welcome to the Poker Hand Evaluator!")
        n = int(input("Enter the number of players (2-10): "))
        
        # Validate number of players
        if n < 2 or n > 10:
            print("Invalid number of players. Setting to default 4 players.")
            n = 4
            
        blind_pot_size = int(input("Enter the small blind amount: "))
        
        # Validate small blind
        if blind_pot_size <= 0:
            print("Invalid small blind amount. Setting to default 5.")
            blind_pot_size = 5
            
        initial_pot_size = int(input("Enter the initial pot size for each player: "))
        
        # Validate initial pot
        if initial_pot_size <= 0:
            print("Invalid initial pot size. Setting to default 1000.")
            initial_pot_size = 1000
        
        # Create and start the game with user input values
        game = Game(n, blind_pot_size, initial_pot_size)
        while True:
            game.start_game()
        
    except ValueError:
        print("Invalid input. Please enter numeric values.")
        print("Starting with default values: 4 players, small blind 5, initial pot 1000")
        game = Game(4, 5, 1000)
        while True:
            game.start_game()
        
    return 0

if __name__ == "__main__":
    main()