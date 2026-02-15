class Tile:
    WHEAT = 0
    TREE = 1
    SHEEP = 2
    MUD = 3
    ROCK = 4
    DESERT = 5

    def __init__(self, tile: int, value: int, has_knight: bool, pos: tuple[int, int]):
        self.tile: int = tile
        self.value: int = value
        self.has_knight: bool = has_knight
        self.owning_player_ids: set[int] = set()
        self.pos: tuple[int, int] = pos

    def __repr__(self):
        h = {0: "W", 1: "T", 2: "S", 3: "M", 4: "R", 5: "D"}
        v = str(self.value)
        if 0 < self.value and self.value < 10:
            v = "0" + v
        return h[self.tile] + "/" + v

    @staticmethod
    def to_name(resource: int) -> str:
        h = {0: "Wheat", 1: "Tree", 2: "Sheep", 3: "Mud", 4: "Rock", 5: "Desert"}
        return h[resource]
