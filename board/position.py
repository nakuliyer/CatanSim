from basic import Tile, Port


class Position:
    def __init__(
        self,
        row,
        col,
        adjacent_tiles: list[Tile] | None = None,
        adjacent_port=None,
        left=None,
        right=None,
        up=None,
        down=None,
    ):
        self.pos = (row, col)
        self.adjacent_tiles: list[Tile] = adjacent_tiles or []
        self.adjacent_port = adjacent_port
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        self.left_road: int | None = None  # player who owns
        self.right_road: int | None = None  # player who owns
        self.up_road: int | None = None  # player who owns
        self.down_road: int | None = None  # player who owns
        self.fixture: int | None = None  # player who owns
        self.fixture_type: int | None = None  # 0 for house, 1 for city

    @property
    def fixture_score(self) -> int:
        if self.fixture_type is not None:
            return self.fixture_type + 1
        return 0

    def adjacent_pos(self):
        adj = []
        if self.left:
            adj.append(self.left)
        if self.right:
            adj.append(self.right)
        if self.up:
            adj.append(self.up)
        if self.down:
            adj.append(self.down)
        return adj

    @staticmethod
    def add_adjacent_pos_to_queue(player: int, pos, next_q, seen, pos_path):
        def can_go(new_pos, route):
            if (
                new_pos
                and (new_pos.pos not in seen)
                and (route is None or route == player)
                and (new_pos.fixture is None or new_pos.fixture == player)
            ):
                return True
            return False

        if can_go(pos.left, pos.left_road):
            next_q.append(pos_path + [pos.left])
        if can_go(pos.right, pos.right_road):
            next_q.append(pos_path + [pos.right])
        if can_go(pos.up, pos.up_road):
            next_q.append(pos_path + [pos.up])
        if can_go(pos.down, pos.down_road):
            next_q.append(pos_path + [pos.down])

    def get_available_roads(self) -> list[str]:
        empty_road_names = ["left_road", "right_road", "up_road", "down_road"]
        road_to_dir = {
            "left_road": "left",
            "right_road": "right",
            "up_road": "up",
            "down_road": "down",
        }
        empty_road_names = [
            road_name
            for road_name in empty_road_names
            if getattr(self, road_name) is None
            and getattr(self, road_to_dir[road_name]) is not None
        ]
        return empty_road_names

    def build_road(self, road_name: str, player_id: int):
        if road_name == "left_road":
            assert self.left and self.left_road is None
            self.left_road = player_id
            self.left.right_road = player_id
        elif road_name == "right_road":
            assert self.right and self.right_road is None
            self.right_road = player_id
            self.right.left_road = player_id
        elif road_name == "up_road":
            assert self.up and self.up_road is None
            self.up_road = player_id
            self.up.down_road = player_id
        elif road_name == "down_road":
            assert self.down and self.down_road is None
            self.down_road = player_id
            self.down.up_road = player_id

    def can_settle(self):
        if self.fixture is None:
            for adj in self.adjacent_pos():
                if adj.fixture:
                    return False
            return True
        return False

    def __str__(self):
        adj = "(" + ",".join(list(map(str, self.adjacent_tiles))) + ")"

        def gpos(pos_or_non):
            if pos_or_non:
                return pos_or_non.pos
            else:
                return "-"

        port = Port.to_name(self.adjacent_port) if self.adjacent_port else "-"
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
