from typing import List
import random

from basic import Tile

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

    # def dist_port(self, port: int, player: int):
    #     seen = set(self.pos)
    #     q: List[Position] = [[self]]
    #     while len(q):
    #         next_q = []
    #         soln = []
    #         for pos_path in q:
    #             pos = pos_path[-1]
    #             seen.add(pos)
    #             if pos.adjacent_port == port:
    #                 soln.append(pos_path)
    #             Position.add_adjacent_pos_to_queue(player, pos, next_q, seen, pos_path)
    #         if len(soln):
    #             return random.choice(soln)[1:]
    #         q = next_q
        
    
    # def dist_res(self, resource: int):
    #     pass

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