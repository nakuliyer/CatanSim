import numpy as np
from itertools import chain

from basic_old import Tile

from .board import Board


class RandomBoard(Board):
    def __init__(self) -> None:
        super().__init__(RandomBoard._generate())

    @staticmethod
    def _generate() -> list[list[Tile]]:
        tiles = list(
            chain(
                [Tile.WHEAT] * 4,
                [Tile.TREE] * 4,
                [Tile.SHEEP] * 4,
                [Tile.MUD] * 3,
                [Tile.ROCK] * 3,
                [Tile.DESERT],
            )
        )
        nums = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        r = 0
        c = 0
        row = []
        cols = []
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
                cols.append(row)
                row = []
                r += 1
                c = 0
        return cols
