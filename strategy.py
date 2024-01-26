from typing import Set, List, Tuple
from board import *
from cards import *
import random
import numpy as np

VERBOSE = 1

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
    
    # TODO: trading
    
    def __init__(self, action: int, **params):
        self.action = action
        self.params = params
        self.__dict__.update(params)
        
    def __repr__(self) -> str:
        h = {v: k for k, v in Action.__dict__.items() if not k.startswith('__') and not callable(k)}
        return "Action {} with parameters {}".format(h[self.action], self.params)
        
    def print(self, player: int):
        h = {v: k for k, v in Action.__dict__.items() if not k.startswith('__') and not callable(k)}
        print("Player {} did action {} with parameters {}".format(player, h[self.action], self.params))
        
    def submit(self, player, board: Board, players: List, stats: GameStats) -> 'Action':
        if VERBOSE: self.print(player)
        if self.action == Action.SETTLE_INIT:
            player.settlements_remaining -= 1
            self.pos.fixture = player.player
            self.pos.fixture_type = 0
            if self.pos.adjacent_port:
                player.controlled_ports.add(self.pos.adjacent_port)
                if VERBOSE:
                    print("Player controls {} ports".format(player.controlled_ports))
        elif self.action == Action.BUILD_ROAD_INIT:
            player.roads_remaining -= 1
            setattr(self.pos, self.road_name, player.player)
            # set opposite direction from the other edge endpoint
            road_to_dir = {"left_road": "left", "right_road": "right", "up_road": "up", "down_road": "down"}
            road_to_op = {"left_road": "right_road", "right_road": "left_road", "up_road": "down_road", "down_road": "up_road"}
            setattr(getattr(self.pos, road_to_dir[self.road_name]), road_to_op[self.road_name], player.player)
        elif self.action == Action.SETTLE:
            player.settlements_remaining -= 1
            player.resources[Tile.MUD] -= 1
            player.resources[Tile.TREE] -= 1
            player.resources[Tile.WHEAT] -= 1
            player.resources[Tile.SHEEP] -= 1
            self.pos.fixture = player.player
            self.pos.fixture_type = 0
            if self.pos.adjacent_port:
                player.controlled_ports.add(self.pos.adjacent_port)
                if VERBOSE:
                    print("Player controls {} ports".format(player.controlled_ports))
        elif self.action == Action.BUILD_ROAD:
            player.roads_remaining -= 1
            player.resources[Tile.MUD] -= 1
            player.resources[Tile.TREE] -= 1
            setattr(self.pos, self.road_name, player.player)
            # print("set {} from {}".format(self.road_name, self.pos.pos))
            # set opposite direction from the other edge endpoint
            road_to_dir = {"left_road": "left", "right_road": "right", "up_road": "up", "down_road": "down"}
            road_to_op = {"left_road": "right_road", "right_road": "left_road", "up_road": "down_road", "down_road": "up_road"}
            setattr(getattr(self.pos, road_to_dir[self.road_name]), road_to_op[self.road_name], player.player)
            # print("set {} from {}".format(road_to_op[self.road_name], getattr(self.pos, road_to_dir[self.road_name]).pos))
            player.check_longest_road(board, stats)
        elif self.action == Action.GET_DEV_CARD:
            print("Getting dev card! todo")
            player.resources[Tile.ROCK] -= 1
            player.resources[Tile.SHEEP] -= 1
            player.resources[Tile.WHEAT] -= 1
        elif self.action == Action.BUILD_CITY:
            player.cities_remaining -= 1
            player.settlements_remaining += 1
            player.resources[Tile.ROCK] -= 3
            player.resources[Tile.WHEAT] -= 2
            self.pos.fixture_type = 1
        elif self.action == Action.FOUR_TO_ONE:
            player.resources[self.source] -= 4
            player.resources[self.dest] += 1
        elif self.action == Action.THREE_TO_ONE:
            player.resources[self.source] -= 3
            player.resources[self.dest] += 1
        elif self.action == Action.TWO_TO_ONE:
            player.resources[self.source] -= 2
            player.resources[self.dest] += 1
            

class RandomStrategy:
    def __init__(self, player, **params):
        self.player = player
        self.resources = {0: 0, 1: 10, 2: 0, 3: 10, 4: 0}
        self.roads_remaining = 15
        self.settlements_remaining = 5
        self.cities_remaining = 4
        self.dev_cards: List[DevCard] = []
        self.knights_played = 0
        self.controlled_ports: Set[Port] = set()
        self.__dict__.update(params)
        
    def check_longest_road(self, board: Board, stats: GameStats):
        def traverse(player: int, seen: List[Tuple[int, int]], node: Position):
            seen += [node.pos]
            options = []
            if node.left_road == player and node.left.pos not in seen:
                options.append(traverse(player, seen, node.left))
            if node.right_road == player and node.right.pos not in seen:
                options.append(traverse(player, seen, node.right))
            if node.up_road == player and node.up.pos not in seen:
                options.append(traverse(player, seen, node.up))
            if node.down_road == player and node.down.pos not in seen:
                options.append(traverse(player, seen, node.down))
            if not options:
                return 0
            else:
                return 1 + max(options)
        max_road_size = 0
        for row in board.positions:
            for pos in row:
                max_road_size = max(max_road_size, traverse(self.player, [], pos))
        if max_road_size > stats.longest_road_count and max_road_size >= 5:
            stats.longest_road_count = max_road_size
            stats.longest_road_player = self.player
            if VERBOSE:
                print("Player {} now has plaque for longest road of size {}".format(self.player, max_road_size))
        if VERBOSE:
            print("Player {}'s longest road is size {}".format(self.player, max_road_size))
        
    def vps(self, board: Board, stats: GameStats):
        sources = { # for pretty printing
            "largest_army": False,
            "longest_road": False,
            "num_settlements": 0,
            "num_cities": 0,
            "num_vp_cards": 0
        }
        vp = 0
        if stats.largest_army_player == self.player:
            vp += 2
            sources["largest_army"] = True
        if stats.longest_road_player == self.player:
            vp += 2
            sources["longest_road"] = True
        for i in self.dev_cards:
            if i == DevCard.VP:
                vp += 1
                sources["num_vp_cards"] += 1
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player:
                    vp += (pos.fixture_type + 1)
                    if pos.fixture_type == 0:
                        sources["num_settlements"] += 1
                    else:
                        sources["num_cities"] += 1
        if VERBOSE:
            print("Player {} has {} VPs: {}".format(self.player, vp, sources))
        return vp
        
    def __repr__(self):
        return "Random Strategy {}".format(self.player)
        
    def settle(self, board: Board, second: bool):
        while True:
            pos = random.choice(random.choice(board.positions))
            if board.can_settle(pos):
                road_names = ["left_road", "right_road", "up_road", "down_road"]
                road_to_dir = {"left_road": "left", "right_road": "right", "up_road": "up", "down_road": "down"}
                road_names = [road_name for road_name in road_names if getattr(pos, road_name) == None and getattr(pos, road_to_dir[road_name]) != None]
                if len(road_names):
                    road_name = random.choice(road_names)
                    if second:
                        for tile in pos.adjacent_tiles:
                            if tile.tile < 5:
                                self.resources[tile.tile] += 1 # collect initial resources
                    return [Action(Action.SETTLE_INIT, pos=pos), Action(Action.BUILD_ROAD_INIT, pos=pos, road_name=road_name)]
    
    def print_resources(self):
        h = {v: k for k, v in Tile.__dict__.items() if not k.startswith('__') and not callable(k)}
        res = {}
        for k in self.resources:
            res[h[k]] = self.resources[k]
        print("Player {} has resources {}".format(self.player, res))
                
    def collect_resources(self, board: Board, d6: int):
        if d6 == 7:
            resource_cards = []
            for res in self.resources:
                for _ in range(self.resources[res]):
                    resource_cards.append(res)
            if len(resource_cards) > 7:
                cards_after_halving = len(resource_cards) // 2 if len(resource_cards) % 2 == 0 else (len(resource_cards) + 1) // 2
                resource_cards = random.sample(resource_cards, cards_after_halving)
                self.resources = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
                for card in resource_cards:
                    self.resources[card] += 1
        else:
            for row in board.positions:
                for pos in row:
                    if pos.fixture == self.player:
                        for tile in pos.adjacent_tiles:
                            if tile.tile < 5 and tile.value == d6:
                                self.resources[tile.tile] += (pos.fixture_type + 1)
                                if VERBOSE:
                                    h = {v: k for k, v in Tile.__dict__.items() if not k.startswith('__') and not callable(k)}
                                    print("Player {} collects {} {}".format(self.player, pos.fixture_type + 1, h[tile.tile]))
        if VERBOSE:
            self.print_resources()
            
    def has_resource(self, resource: int):
        return self.resources[resource] > 0
    
    def get_settlement_options(self, board: Board) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                owns_road = [pos.left_road == self.player, pos.right_road == self.player, pos.up_road == self.player, pos.down_road == self.player]
                owns_road = (owns_road.count(True) == 1)
                if board.can_settle(pos) and owns_road:
                    options.append(Action(Action.SETTLE, pos=pos))
        return options
    
    def get_city_options(self, board: Board) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player and pos.fixture_type == 0:
                    options.append(Action(Action.BUILD_CITY, pos=pos))
        return options
    
    def get_road_options(self, board: Board) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                owns_road = (pos.left_road == self.player) or (pos.right_road == self.player) or (pos.up_road == self.player) or (pos.down_road == self.player)
                # print("{} l{} r{} t{} d{}".format(pos.pos, pos.left_road, pos.right_road, pos.up_road, pos.down_road))
                empty_road_names = ["left_road", "right_road", "up_road", "down_road"]
                road_to_dir = {"left_road": "left", "right_road": "right", "up_road": "up", "down_road": "down"}
                empty_road_names = [road_name for road_name in empty_road_names if getattr(pos, road_name) == None and getattr(pos, road_to_dir[road_name]) != None]
                if owns_road:
                    print("terminal node {}", pos.pos)
                    for road_name in empty_road_names:
                        options.append(Action(Action.BUILD_ROAD, pos=pos, road_name=road_name))
        return options
    
    def can_build_dev_card(self):
        return self.has_resource(Tile.ROCK) and self.has_resource(Tile.SHEEP) and self.has_resource(Tile.WHEAT)

    def can_build_settlement(self):
        return self.has_resource(Tile.WHEAT) and self.has_resource(Tile.SHEEP) and self.has_resource(Tile.TREE) and self.has_resource(Tile.MUD) and self.settlements_remaining

    def can_build_road(self):
        return self.has_resource(Tile.MUD) and self.has_resource(Tile.TREE) and self.roads_remaining
    
    def can_build_city(self):
        return self.resources[Tile.ROCK] >= 3 and self.resources[Tile.WHEAT] >= 2 and self.cities_remaining

    def get_legal_actions(self, board: Board):
        legal_actions = []
        if self.can_build_dev_card():
            legal_actions.append(Action(Action.GET_DEV_CARD))
        if self.can_build_settlement():
            settlement_options = self.get_settlement_options(board)
            legal_actions += settlement_options
        if self.can_build_road():
            road_options = self.get_road_options(board)
            legal_actions += road_options
        if self.can_build_city():
            city_options = self.get_city_options(board)
            legal_actions += city_options
        # 4:1
        for res in self.resources:
            if self.resources[res] >= 4:
                for new_res in range(5):
                    if new_res != res:
                        legal_actions.append(Action(Action.FOUR_TO_ONE, source=res, dest=new_res))
        # Ports
        for port in self.controlled_ports:
            if port == Port.THREE_ONE:
                if self.resources[res] >= 3:
                    for new_res in range(5):
                        if new_res != res:
                            legal_actions.append(Action(Action.THREE_TO_ONE, source=res, dest=new_res))
            elif self.resources[port] >= 2:
                for new_res in range(5):
                    if new_res != res:
                        legal_actions.append(Action(Action.TWO_TO_ONE, source=res, dest=new_res))
        return legal_actions
    
    def do(self, board: Board) -> Action:
        # the main function; look at the board state, take some action
        legal_actions = self.get_legal_actions(board)
        if VERBOSE:
            print("Player {} Legal Actions {}".format(self.player, legal_actions))
        r = random.random()
        if (len(legal_actions) and r < 0) or (not len(legal_actions) and r < 1):
            # do nothing chance
            return Action(Action.DO_NOTHING)
        elif (len(legal_actions) and False) or (not len(legal_actions) and False):
            # propose trade TODO
            pass
        else:
            return random.choice(legal_actions)