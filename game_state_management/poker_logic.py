from poker_signal_receiver import PokerSignalReceiver

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
        
        # Set current active player (initially after big blind)
        self.current_player = (self.x + 2) % self.n
        
        self.game_pot = {i: 0 for i in range(self.n)}
        self.active_players = set(range(self.n))
        
        # Game phase (preflop, flop, turn, river, showdown)
        self.phase = "setup"
    
    def start_game(self):
        # Table for each player's current bet in this round
        # All players have to match in order to play the game
        self.game_pot = {i: 0 for i in range(self.n)}
        
        # Current bet that all active players must match or fold
        self.current_bet = 0
        
        # Track active players (not folded)
        self.active_players = set(range(self.n))
        
        # Current active player (after the big blind)
        self.current_player = (self.x + 2) % self.n
        
        # Track players who have acted in this round
        self.players_acted = set()
        
        # Hands of each player (7 cards = 2 hole cards + 5 community)
        self.hands = {i: [] for i in range(self.n)}
        
        self.dispenser = PokerSignalReceiver(port='/dev/ttyACM0', baud_rate=9600)
        
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
        
        # Set the initial phase
        self.phase = "preflop"
        self.serve_phase()
        self.phase = "flop"
        self.serve_phase()
        self.phase = "turn"
        self.serve_phase()
        self.phase = "river"
        self.serve_phase()
        
    def serve_phase(self):
        """Serve the current phase of the game."""
        if self.phase == "preflop":
            # Handle preflop actions
            self.dispenser.send_command("P0\n")
            self.dispenser._read_serial_thread()
            
            
            
        elif self.phase == "flop":
            # Handle flop actions
            self.dispenser.send_command("P1\n")
            self.dispenser._read_serial_thread()
            
        elif self.phase == "turn":
            # Handle turn actions
            self.dispenser.send_command("P2\n")
            self.dispenser._read_serial_thread()
            
            
        elif self.phase == "river":
            # Handle river actions
            self.dispenser.send_command("P2\n")
            self.dispenser._read_serial_thread()
            
        elif self.phase == "showdown":
            # Handle showdown actions
            pass
    
    def deal_hole_cards(self):
        # This function will be called by the Pygame implementation
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
    
    def move_to_next_player(self):
        """Move to the next active player."""
        # Find the next active player
        initial_player = self.current_player
        while True:
            self.current_player = (self.current_player + 1) % self.n
            if self.current_player in self.active_players and self.current_player not in self.players_acted:
                break
            
            # Prevent infinite loop if no eligible players
            if self.current_player == initial_player:
                return True  # Round complete
        
        return False  # Round continues
    
    def advance_phase(self):
        """Advance to the next phase of the game."""
        if self.phase == "preflop":
            self.phase = "flop"
            # Deal the flop
            self.community = self.community_deck[:3]
        elif self.phase == "flop":
            self.phase = "turn"
            # Deal the turn
            self.community.append(self.community_deck[3])
        elif self.phase == "turn":
            self.phase = "river"
            # Deal the river
            self.community.append(self.community_deck[4])
        elif self.phase == "river":
            self.phase = "showdown"
            # Determine winner
            self.decide_winner()
            # Reset for the next hand
            self.phase = "setup"
        
        # Reset betting for the new phase
        self.current_bet = 0
        self.players_acted = set()
        self.current_player = self.x  # Start with small blind player
    
    def decide_winner(self):
        # Identify who is still playing
        playing = list(self.active_players)
            
        if not playing:
            return None
        
        best_score = -1
        best_player = []
        player_hands = {}
        
        # Get score for each player's hand
        for player in playing:
            # Combine player's hole cards with community cards
            full_hand = self.hands[player] + self.community
            
            # Evaluate the hand
            hand_result = evaluate_hand(full_hand)
            
            # Store the result
            player_hands[player] = hand_result
            
            if hand_result:
                cur_score = hand_result.get_score()
                
                if cur_score > best_score:
                    best_score = cur_score
                    best_player = [player]
                elif cur_score == best_score:
                    best_player.append(player)
        
        # Calculate total pot
        total_pot = sum(self.game_pot.values())
        
        # Determine result
        if len(best_player) == 1:
            # Single winner
            winner = best_player[0]
            self.pots[winner] += total_pot
            return {"winners": [winner], "amount": total_pot, "hand": player_hands[winner].category}
        else:
            # Tie: distribute to all winners
            split_amount = total_pot // len(best_player)
            remainder = total_pot % len(best_player)
            
            for winner in best_player:
                self.pots[winner] += split_amount
            
            return {"winners": best_player, "amount": split_amount, "hand": player_hands[best_player[0]].category, "remainder": remainder}