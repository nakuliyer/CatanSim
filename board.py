from typing import List

import numpy as np

from basic import Tile, Port
from position import Position


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
        c = 0
        row = []
        while len(tiles):
            rand = np.random.randint(0, len(tiles))
            tile = tiles.pop(rand)
            if tile == Tile.DESERT:
                num = -1
                has_knight = True
            else:
                rand = np.random.randint(0, len(nums))
                num = nums.pop(rand)
                has_knight = False
            row.append(Tile(tile, num, has_knight, (r, c)))
            c += 1
            if len(row) == 5 - abs(r - 2):
                self.tiles.append(row)
                row = []
                r += 1
                c = 0

    def can_settle(self, pos: Position) -> bool:
        if pos.fixture is None:
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

    def get_positions(self, owned_by_player: int = None):
        return [
            pos
            for row in self.positions
            for pos in row
            if owned_by_player is None or owned_by_player == pos.fixture
        ]

    def __str__(self):
        s = ""
        for r, row in enumerate(self.tiles):
            pad = " " * (abs(r - 2) * 2)
            s += pad + " ".join(list(map(str, row))) + pad + "\n"
        return s
