import random
from typing import List, Set, Tuple


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

    @staticmethod
    def to_name(port: int) -> str:
        h = {0: "WHEAT", 1: "TREE", 2: "SHEEP", 3: "MUD", 4: "ROCK", 5: "THREE TO ONE"}
        return h[port]


class Tile:
    WHEAT = 0
    TREE = 1
    SHEEP = 2
    MUD = 3
    ROCK = 4
    DESERT = 5

    def __init__(self, tile: int, value: int, has_knight: bool, pos: Tuple[int, int]):
        self.tile: int = tile
        self.value: int = value
        self.has_knight: bool = has_knight
        self.owning_player_ids: Set[int] = set()
        self.pos: Tuple[int, int] = pos

    def __repr__(self):
        h = {0: "W", 1: "T", 2: "S", 3: "M", 4: "R", 5: "D"}
        v = str(self.value)
        if 0 < self.value and self.value < 10:
            v = "0" + v
        return h[self.tile] + "/" + v

    @staticmethod
    def to_name(resource: int) -> str:
        h = {0: "WHEAT", 1: "TREE", 2: "SHEEP", 3: "MUD", 4: "ROCK", 5: "DESERT"}
        return h[resource]


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
    ROB = 14
    PROPOSE_TRADE = 15
    TRADE = 16

    def __init__(self, action: int, **params):
        self.action = action
        self.params = params
        self.__dict__.update(params)

    def clean_params(self):
        # just here for pretty-ish printing
        h = {}
        for param in self.params:
            if param == "source" or param == "dest" or param.startswith("resource"):
                h[param] = Tile.to_name(self.params[param])
            elif param == "mine" or param == "theirs":
                h[param] = list(map(Tile.to_name, self.params[param]))
            else:
                h[param] = self.params[param]
        return ", ".join(["{}={}".format(k, v) for k, v in h.items()])

    def __repr__(self) -> str:
        h = {
            v: k
            for k, v in Action.__dict__.items()
            if not k.startswith("__") and not callable(k)
        }
        return "{}[{}]".format(h[self.action], self.clean_params())


class DevCard:
    KNIGHT = 0
    VP = 1
    ROADS = 2
    PLENTY = 3
    MONOPOLY = 4
    NO_OP = 5

    @staticmethod
    def to_name(card: int) -> str:
        h = {
            0: "KNIGHT",
            1: "VP",
            2: "BUILD ROADS",
            3: "YEAR OF PLENTY",
            4: "MONOPOLY",
            5: "NO OP",
        }
        return h[card]

    @staticmethod
    def to_names(list_of_cards: List[int]) -> str:
        return "[{}]".format(
            ", ".join(map(DevCard.to_name, filter(lambda x: x != 5, list_of_cards)))
        )


class DevCardPile:
    def __init__(self):
        self.pile = [
            [DevCard.KNIGHT] * 14,
            [DevCard.VP] * 5,
            [DevCard.ROADS] * 2,
            [DevCard.PLENTY] * 2,
            [DevCard.MONOPOLY] * 2,
        ]
        self.pile = [item for row in self.pile for item in row]
        random.shuffle(self.pile)

    def draw_top(self):
        if len(self.pile):
            return self.pile.pop(0)
        return DevCard.NO_OP
