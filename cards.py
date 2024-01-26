import random

class DevCard:
    KNIGHT = 0
    VP = 1
    ROADS = 2
    PLENTY = 3
    MONOPOLY = 4
    
class DevCardPile:
    def __init__(self):
        self.pile = [[DevCard.KNIGHT] * 14, [DevCard.VP] * 5, [DevCard.ROADS] * 2, [DevCard.PLENTY] * 2, [DevCard.MONOPOLY] * 2]
        self.pile = [item for row in self.pile for item in row]
        random.shuffle(self.pile)
        
    def draw_top(self):
        return self.pile.pop(0)