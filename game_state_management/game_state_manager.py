class Card:
    def __init__(self, suit, rank):
        self.suit = suit # 'S', 'D', 'H', 'C'
        self.rank = rank 
        
class Score:
    def __init__(self, category, first=0, second=0, third=0, fourth=0, fifth=0, 
                higher=0, lower=0):
        
        self.category = category
        self.first = self.convert(first)
        self.second = self.convert(second)
        self.third = self.convert(third) 
        self.fourth = self.convert(fourth) 
        self.fifth = self.convert(fifth) 
        self.higher = self.convert(higher) 
        self.lower = self.convert(lower) 
        
        if category == 'straight flush':
            self.score += 8
        if category == 'four of a kind':
            self.score += 7
        if category == 'full house':
            self.score += 6
        if category == 'flush':
            self.score += 5
        if category == 'straight':
            self.score += 4
        if category == 'triple':
            self.score += 3
        if category == 'two pair':
            self.score += 2
        if category == 'one pair': 
            self.score += 1
        
        self.score *= 13**5
        if category == 'straight flush':
            self.score += self.higher 
        if category == 'four of a kind':
            self.score += self.higher * 13
            self.score += self.first
        if category == 'full house':
            self.score += self.higher * 13
            self.score += self.lower
        if category == 'flush':
            self.score += self.first * (13 ** 4)
            self.score += self.second * (13 ** 3)
            self.score += self.third * (13 ** 2)
            self.score += self.fourth * (13 ** 1)
            self.score += self.fifth 
        if category == 'straight':
            self.score += self.higher
        if category == 'triple':
            self.score += self.higher * (13 ** 2)
            self.score += self.first * 13
            self.score += self.second
        if category == 'two pair':
            self.score += self.higher * (13 ** 2)
            self.score += self.lower * 13
            self.score += self.first
        if category == 'one pair': 
            self.score += self.higher * (13 ** 3)
            self.score += self.first * (13 ** 2)
            self.score += self.second * 13
            self.score += self.third 
        if category == 'no pair':
            self.score += self.first * (13 ** 4)
            self.score += self.second * (13 ** 3)
            self.score += self.third * (13 ** 2)
            self.score += self.fourth * (13 ** 1)
            self.score += self.fifth 
        
    
    
    # convert rank so that ACE is most valuable
    def convert(self, rank):
        return 13 if rank == 1 else rank-1
        
    def get_score(self):
        return self.score

# cards are sorted
def remove_duplicates(cards):
    # use stack: O(n)
    stack = []
    i = 0
    n = len(cards)
    while i < n:
        if not stack:
            stack.append(cards[i])
        else:
            last = stack.pop()
            if last == cards[i]:
                while last == cards[i]:
                    i += 1
            else:
                stack.append(last)
                stack.append(cards[i])
    return stack

# hand is 7-length card list
def count_frequencies(hand):
    frequency = {}
    for card in hand:
        rank = card.rank
        if rank in frequency:
            frequency[rank] +=1
        else:
            frequency[rank] = 1
    
    quadruples = []
    triples = []
    pairs = []
    cards = []
    for rank in frequency:
        cards.append(rank)
        if frequency[rank] == 4:
            quadruples.append(rank)
        if frequency[rank] == 3:
            triples.append(rank)
        if frequency[rank] == 2:
            pairs.append(rank)

    no_dups = remove_duplicates(sorted(cards))
    reversed_no_dups = reversed(no_dups)
                
    num_triple = len(triples)
    num_pair = len(pairs)
    
    triples.sort()
    pairs.sort()
    
    triples.reverse()
    pairs.reverse()
    
    if quadruples:
        return Score('four of a kind', higher=quadruples[0], first=reversed_no_dups[0])
    if num_triple >= 2:
        return Score('full house', higher=triples[0], lower=triples[1])
    if (num_triple >= 1 and num_pair >= 1):
        return Score('full house', higher=triples[0], lower=pairs[0])
    if num_triple >= 1:
        return Score('triple', higher=triples[0], first=reversed_no_dups[0], 
                        second=reversed_no_dups[1])
    if num_pair >= 2:
        return Score('two pair', higher=pairs[0], lower=pairs[1], 
                        first=reversed_no_dups[0])
    if num_pair >= 1:
        return Score('one pair', higher=pairs[0], first=reversed_no_dups[0], 
                        second=reversed_no_dups[1], third=reversed_no_dups[2])
    
    return Score('no pair', first=reversed_no_dups[0], second=reversed_no_dups[1],
                    third=reversed_no_dups[2], fourth=reversed_no_dups[3],
                    fifth=reversed_no_dups[4])

# hand is 7-length card list or less if called from check_flush
def check_straight(hand):
    mapping = [False]*14 # Ace is 0 and 13
    for card in hand:
        rank = card.rank
        mapping[rank-1] = True
        if rank == 1:
            mapping[13] = True
    
    # check for 5 consecutive entries
    # TODO: think of a way to optimize this.
    for i in reversed(range(5, 13)):
        if mapping[i] and mapping[i-1] and mapping[i-2] and mapping[i-3] and mapping[i-4]:
            return Score('straight', higher=i)
        
    return None

# hand is 7-length card list
def check_flush(hand):
    frequency = {}
    for card in hand:
        suit = card.suit
        rank = card.rank
        if suit in frequency:
            frequency[suit].append(card)
        else:
            frequency[suit] = [card]
    
    for suit in frequency:
        cards = frequency[suit]
        if len(cards) >= 5:
            # check straight flush
            straight = check_straight(cards)
            if straight:
                return Score('straight flush', higher=straight.higher)
            
            # then sort ranks for flush
            ranks = []
            for card in cards:
                ranks.append(card.rank)
            ranks.sort()
            ranks.reverse()
        
            return Score('flush', first=ranks[0], second=ranks[1],
                            third=ranks[2], fourth=ranks[3], fifth=ranks[4])
    

    return None


    

class Game:
    # int n : number of player
    # int blind_pot_size : fixed small blind amount
    # int initial_pot_size : initial amount of money distributed to each player
    def __init__(self, n, blind_pot_size, initial_pot_size): 
        #small blind size
        self.sb = blind_pot_size 
        
        # big blind size
        self.bb = blind_pot_size * 2
        
        # table for each player's pot size
        self.pots = {initial_pot_size for i in range(n)}
        
        
        # xth player who is small blind for this game
        self.x = 0 
        
        # number of total player
        self.n = n 
    
    def start_game(self):
        # table for each player's currently-playing pot size
        # all players have to match in order to play the game
        self.game_pot = {0 for i in range(self.n)}
        
        # hands of each player
        self.hands = {[] for i in range(self.n)}
        
        # community card
        self.community = []
        
        # resume game by calling each phases
        self.preflop_phase()
        self.flop_phase()
        self.turn_phase()
        self.river_phase()
        

    def decide_winner(self):
        # identify who is still playing
        playing = []
        largest = 0
        for player in self.game_pot:
            pot_size = self.game_pot[player]
            largest = max(largest, pot_size)
        
        for player in self.game_pot:
            pot_size = self.game_pot[player]
            if pot_size >= largest:
                playing.append()
        if not playing:
            print("no player still playing")
            return 0
        
        score_table = {}
        best_score = -1
        best_player = []
        # get score for each player's hand
        for player in playing:
            hands = self.hands[player]
            flush = check_flush(hands)
            straight = check_straight(hands)
            pairs = count_frequencies(hands)
            cur_score = max(flush.score if flush else 0, straight.score if straight else 0, pairs.score)
            
            if cur_score > best_score:
                best_score = cur_score
                best_player = [player]
            elif cur_score == best_score:
                best_player.append(player)
        
        # adjust pot accordingly
        if best_player:
            # add to winner's pot
            for money in self.game_pot:
                self.pots[best_player] += money
        else:
            # there was a tie: distribute to all winner's pot
            # if it isn't divisible, give the coin to ACE for tip :)
            price = 0
            for money in self.game_pot:
                price+= money
            for winner in best_player:
                self.pots[winner] += price // len(best_player) 
            
    
    def wait_for_bet(self, player):
        # receive user input by the following options:
        while True:
            continue
            # 1. notice weight difference in the weight scale. -> raise
            
            # 2. detect check motion -> check/no change in game_pot
            # 3. detect fold with the card thrown to the table -> 
            # fold/ no change in the game pot
        return
    
    def take_turns(self):
        # first set to the player next to big blind
        cur_player = (self.x + 2) % self.n
        
        while True:
            bet = self.wait_for_bet(cur_player)
            
            
            cur_player = (cur_player + 1) % self.n
        
        
    def preflop_phase(self):
        
        return 0

    def flop_phase(self):
        # receive input from rpi camera to detect the three community cards (flop)
        # assuming that worked
        three_cards = RECEIVED_INPUT_FROM_CAMERA()
        for card in three_cards:
            self.community.append(card)

        # then players take turns to bet
        self.take_turns()
        

    def turn_phase(self):
        # receive input from rpi camera to detect the fourth community card (turn)
        # assuming that worked
        card = RECEIVED_INPUT_FROM_CAMERA()
        self.community.append(card)

        # then players take turns to bet
        self.take_turns()

    def river_phase(self):
        # receive input from rpi camera to detect the fifth community card (river)
        # assuming that worked
        card = RECEIVED_INPUT_FROM_CAMERA()
        self.community.append(card)

        # then players take turns to bet
        self.take_turns()
        
        # finally, decide the winner + adjust player's pot
        self.decide_winner()
        
        # increment small blind for the next game
        self.x = (self.x + 1) % self.n


def main():
    
    return 0

def __main__():
    main()