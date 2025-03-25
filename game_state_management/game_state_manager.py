class Card:
    def __init__(self, suit, rank):
        self.suit = suit # 'S', 'D', 'H', 'C'
        self.rank = rank 
        
class Score:
    def __init__(self, category, first=0, second=0, third=0, fourth=0, fifth=0, 
                higher=0, lower=0):
        self.category = category
        self.score = 0
        
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
        # TODO: finish this
        


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

# hand is 7-length card list
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
            frequency[suit].append(rank)
        else:
            frequency[suit] = [rank]
    
    for suit in frequency:
        ranks = frequency[suit]
        if len(ranks) >= 5:
            ranks.sort()
            ranks.reverse()
            return Score('flush', first=ranks[0], second=ranks[1],
                            third=ranks[2], fourth=ranks[3], fifth=ranks[4])

    return None

class Game:
    def __init__(self, x, n):
        self.x = x # xth player who is small blind for this game
        self.n = n # number of total player
            

    def preflop_phase(self):
        #
        return 0

    def flop_phase(self):
        return 0

    def turn_phase(self):
        return 0

    def river_phase(self):
        return 0
    

def main():
    
    return 0

def __main__():
    main()