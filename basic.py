
class GameStats:
    longest_road_count = 0
    longest_road_player = -1
    largest_army_count = 0
    largest_army_player = -1
    
class Port:
    WHEAT = 0
    TREE = 1
    SHEEP = 2
    MUD = 3
    ROCK = 4
    THREE_ONE = 5


class Tile:
    WHEAT = 0
    TREE = 1
    SHEEP = 2
    MUD = 3
    ROCK = 4
    DESERT = 5

    def __init__(self, tile, value):
        self.tile: int = tile
        self.value: int = value

    def __str__(self):
        h = {0: "W", 1: "T", 2: "S", 3: "M", 4: "R", 5: "D"}
        v = str(self.value)
        if 0 < self.value and self.value < 10:
            v = "0" + v
        return h[self.tile] + "/" + v

VERBOSE = 1
