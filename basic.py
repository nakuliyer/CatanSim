
from typing import List, Set

def to_name(resource: int):
    h = {
        0: "WHEAT",
        1: "TREE",
        2: "SHEEP",
        3: "MUD",
        4: "ROCK"
    }
    return h[resource]


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

    def __init__(self, tile: int, value: int, has_knight: bool):
        self.tile: int = tile
        self.value: int = value
        self.has_knight: bool = has_knight
        self.owning_player_ids: Set[int] = set()

    def __repr__(self):
        h = {0: "W", 1: "T", 2: "S", 3: "M", 4: "R", 5: "D"}
        v = str(self.value)
        if 0 < self.value and self.value < 10:
            v = "0" + v
        return h[self.tile] + "/" + v
    
class Action:
    DO_NOTHING = -1
    GET_DEV_CARD = 0
    SETTLE_INIT = 1
    BUILD_CITY = 2
    BUILD_ROAD_INIT = 3
    FOUR_TO_ONE = 4
    THREE_TO_ONE = 5
    SETTLE = 6
    BUILD_ROAD = 7
    USE_KNIGHT = 8
    USE_MONOPOLY = 9
    USE_DEV_ROADS = 10
    USE_YEAR_OF_PLENTY = 11
    TWO_TO_ONE = 12
    SECOND_USE_DEV_ROADS = 13
    
    # TODO: trading
    
    def __init__(self, action: int, **params):
        self.action = action
        self.params = params
        self.__dict__.update(params)
        
    def __repr__(self) -> str:
        h = {v: k for k, v in Action.__dict__.items() if not k.startswith('__') and not callable(k)}
        return "Action {} with parameters {}".format(h[self.action], self.params)

VERBOSE = 1
