from typing import List

from basic import Port, Tile, GameStats, VERBOSE
from board import Board
from cards import DevCard
from position import Position

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