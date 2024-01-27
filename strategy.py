from typing import Set, List, Tuple
import random

from basic import Port, Tile, GameStats, Action, VERBOSE
from board import Board
from cards import DevCard
from position import Position
from player import Player
            

class RandomStrategy(Player):    
    def __repr__(self):
        return "Random Strategy {}".format(self.player_id)
        
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
                
    def place_second_dev_roads(self, board: Board):
        legal_roads = self.get_road_options(board, second_road_building=True)
        return random.choice(legal_roads)
    
    def do(self, board: Board) -> Action:
        # the main function; look at the board state, take some action
        legal_actions = self.get_legal_actions(board)
        if VERBOSE:
            print("Player {} Legal Actions {}".format(self.player_id, legal_actions))
        r = random.random()
        if (len(legal_actions) and r < 0) or (not len(legal_actions) and r < 1):
            # do nothing chance
            return Action(Action.DO_NOTHING)
        elif (len(legal_actions) and False) or (not len(legal_actions) and False):
            # propose trade TODO
            pass
        else:
            return random.choice(legal_actions)