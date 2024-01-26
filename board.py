from typing import List, Tuple
import numpy as np
import random


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


class Position:
    def __init__(
        self,
        row,
        col,
        adjacent_tiles=[],
        adjacent_port=None,
        left=None,
        right=None,
        up=None,
        down=None,
    ):
        self.pos = (row, col)
        self.adjacent_tiles: List[Tile] = adjacent_tiles
        self.adjacent_port = adjacent_port
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.left_road = None # player who owns
        self.right_road = None # player who owns
        self.up_road = None # player who owns
        self.down_road = None # player who owns
        self.fixture = None # player who owns
        self.fixture_type = None # 0 for house, 1 for city
        
    def adjacent_pos(self):
        adj = []
        if self.left: adj.append(self.left)
        if self.right: adj.append(self.right)
        if self.up: adj.append(self.up)
        if self.down: adj.append(self.down)
        return adj
        
    def add_adjacent_pos_to_queue(player: int, pos, next_q, seen, pos_path):
        def can_go(new_pos, route):
            if new_pos and (new_pos.pos not in seen) and \
                           (route == None or route == player) and \
                           (new_pos.fixture == None or new_pos.fixture == player):
                return True
            return False
        if can_go(pos.left, pos.left_road): next_q.append(pos_path + [pos.left])
        if can_go(pos.right, pos.right_road): next_q.append(pos_path + [pos.right])
        if can_go(pos.up, pos.up_road): next_q.append(pos_path + [pos.up])
        if can_go(pos.down, pos.down_road): next_q.append(pos_path + [pos.down])

    def dist_port(self, port: int, player: int):
        seen = set(self.pos)
        q: List[Position] = [[self]]
        while len(q):
            next_q = []
            soln = []
            for pos_path in q:
                pos = pos_path[-1]
                seen.add(pos)
                if pos.adjacent_port == port:
                    soln.append(pos_path)
                Position.add_adjacent_pos_to_queue(player, pos, next_q, seen, pos_path)
            if len(soln):
                return random.choice(soln)[1:]
            q = next_q
        
    
    def dist_res(self, resource: int):
        pass

    def __str__(self):
        h = {0: "W", 1: "T", 2: "S", 3: "M", 4: "R", 5: "3"}
        adj = "(" + ",".join(list(map(str, self.adjacent_tiles))) + ")"

        def gpos(pos_or_non):
            if pos_or_non:
                return pos_or_non.pos
            else:
                return "-"

        port = h[self.adjacent_port] if self.adjacent_port else "-"
        return "pos={} adj={} port={} left={} right={} up={} down={}".format(
            self.pos,
            adj,
            port,
            gpos(self.left),
            gpos(self.right),
            gpos(self.up),
            gpos(self.down),
        )
        
    def __repr__(self):
        return str(self.pos)


class Board:
    def __init__(self):
        self.tiles: List[List[Tile]] = []
        self.generate()
        self.positions: List[List[Position]] = []
        self.set_up_positions()

    def generate(self):
        tiles = [
            [Tile.WHEAT] * 4,
            [Tile.TREE] * 4,
            [Tile.SHEEP] * 4,
            [Tile.MUD] * 3,
            [Tile.ROCK] * 3,
            [Tile.DESERT],
        ]
        tiles = [item for row in tiles for item in row]
        nums = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        r = 0
        row = []
        while len(tiles):
            rand = np.random.randint(0, len(tiles))
            tile = tiles.pop(rand)
            if tile == Tile.DESERT:
                num = -1
            else:
                rand = np.random.randint(0, len(nums))
                num = nums.pop(rand)
            row.append(Tile(tile, num))
            if len(row) == 5 - abs(r - 2):
                self.tiles.append(row)
                row = []
                r += 1
                
    def can_settle(self, pos: Position):
        if pos.fixture == None:
            for adj in pos.adjacent_pos():
                if adj.fixture:
                    return False
            return True
        return False

    def set_up_positions(self):
        self.positions = [
            [Position(r, c) for c in range(j)]
            for r, j in [(0, 7), (1, 9), (2, 11), (3, 11), (4, 9), (5, 7)]
        ]
        grow = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 4}
        gadj = {1: 0, 2: 1, 3: 3, 4: 4}
        # figure out adjacent tiles
        for r, row in enumerate(self.positions):
            for c, pos in enumerate(row):
                # add self row
                pos.adjacent_tiles = []
                if c > 0:
                    pos.adjacent_tiles.append(self.tiles[grow[r]][(c - 1) // 2])
                if c % 2 == 0 and c < len(row) - 1:
                    pos.adjacent_tiles.append(self.tiles[grow[r]][c // 2])
                # add adj row
                if r in gadj and c > 0 and c < len(row) - 1:
                    if c > 1:
                        pos.adjacent_tiles.append(self.tiles[gadj[r]][(c - 2) // 2])
                    if (c - 1) % 2 == 0 and c < len(row) - 2:
                        pos.adjacent_tiles.append(self.tiles[gadj[r]][(c - 1) // 2])
        # link graph
        for r, row in enumerate(self.positions):
            for c, pos in enumerate(row):
                # link neighbors in row
                if c + 1 < len(row):
                    pos.right = row[c + 1]
                    row[c + 1].left = pos
                if c % 2 == 0 and r < 2:
                    pos.down = self.positions[r + 1][c + 1]
                    self.positions[r + 1][c + 1].up = pos
                if c % 2 == 0 and r == 2:
                    pos.down = self.positions[r + 1][c]
                    self.positions[r + 1][c].up = pos
                if c % 2 == 0 and r > 3:
                    pos.up = self.positions[r - 1][c + 1]
                    self.positions[r - 1][c + 1].down = pos
        # add ports
        self.positions[0][2].adjacent_port = Port.THREE_ONE
        self.positions[0][3].adjacent_port = Port.THREE_ONE
        self.positions[0][5].adjacent_port = Port.THREE_ONE
        self.positions[0][6].adjacent_port = Port.THREE_ONE
        self.positions[1][0].adjacent_port = Port.SHEEP
        self.positions[1][1].adjacent_port = Port.SHEEP
        self.positions[1][8].adjacent_port = Port.MUD
        self.positions[2][0].adjacent_port = Port.THREE_ONE
        self.positions[2][9].adjacent_port = Port.MUD
        self.positions[3][0].adjacent_port = Port.THREE_ONE
        self.positions[3][9].adjacent_port = Port.TREE
        self.positions[4][0].adjacent_port = Port.ROCK
        self.positions[4][1].adjacent_port = Port.ROCK
        self.positions[4][8].adjacent_port = Port.TREE
        self.positions[5][2].adjacent_port = Port.WHEAT
        self.positions[5][3].adjacent_port = Port.WHEAT
        self.positions[5][5].adjacent_port = Port.THREE_ONE
        self.positions[5][6].adjacent_port = Port.THREE_ONE

    def __str__(self):
        s = ""
        for r, row in enumerate(self.tiles):
            pad = " " * (abs(r - 2) * 2)
            s += pad + " ".join(list(map(str, row))) + pad + "\n"
        return s
    
class GameStats:
    longest_road_count = 0
    longest_road_player = -1
    largest_army_count = 0
    largest_army_player = -1
