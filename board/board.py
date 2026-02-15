from basic_old import Tile, Port

from .position import Position


class Board:
    def __init__(self, tiles: list[list[Tile]]) -> None:
        assert len(tiles) == 5, "Board must have 5 rows"
        for i, row in enumerate(tiles):
            assert len(row) == 5 - abs(i - 2), "Row {} must have {} tiles".format(
                i, 5 - abs(i - 2)
            )

        self.tiles: list[list[Tile]] = tiles
        self.positions: list[list[Position]] = []

        self._set_up_positions()

    def __str__(self) -> str:
        s = ""
        for r, row in enumerate(self.tiles):
            pad = " " * (abs(r - 2) * 2)
            s += pad + " ".join(list(map(str, row))) + pad + "\n"
        return s

    def get_position(self, pos: tuple[int, int]) -> Position:
        r, c = pos
        return self.positions[r][c]

    def get_tile(self, pos: tuple[int, int]) -> Tile:
        r, c = pos
        return self.tiles[r][c]

    def get_positions_owned_by_player(self, player_id: int) -> list[Position]:
        return [
            pos for row in self.positions for pos in row if player_id == pos.fixture
        ]

    def get_road_options(self, player_id: int) -> list[tuple[Position, str]]:
        options: list[tuple[Position, str]] = []
        for row in self.positions:
            for pos in row:
                owns_road = (
                    (pos.left_road == player_id)
                    or (pos.right_road == player_id)
                    or (pos.up_road == player_id)
                    or (pos.down_road == player_id)
                )
                empty_road_names = pos.get_available_roads()
                if owns_road:
                    for road_name in empty_road_names:
                        options.append((pos, road_name))
        return options

    def get_knight_options(self, player_id: int) -> list[tuple[Tile, int | None]]:
        knight_options: list[tuple[Tile, int | None]] = []
        for row in self.tiles:
            for tile in row:
                if not tile.has_knight and not tile.tile == Tile.DESERT:
                    if len(tile.owning_player_ids):
                        for other_player_id in tile.owning_player_ids:
                            if other_player_id != player_id:
                                knight_options.append((tile, other_player_id))
                    else:
                        knight_options.append((tile, None))
        return knight_options

    def _set_up_positions(self) -> None:
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
