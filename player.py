from typing import Set, List, Tuple
import random

from basic import Port, Tile, GameStats, Action, VERBOSE, to_name
from board import Board
from cards import DevCard, DevCardPile
from position import Position

class Player:
    def __init__(self, player_id: int, **params):
        self.player_id = player_id
        self.resources = {0: 0, 1: 10, 2: 0, 3: 10, 4: 0}
        self.roads_remaining = 15
        self.settlements_remaining = 5
        self.cities_remaining = 4
        self.dev_cards: List[DevCard] = []
        self.knights_played = 0
        self.controlled_ports: Set[Port] = set()
        self.__dict__.update(params)
        
    def __repr__(self):
        # TODO: include more info here?
        return "Player {}".format(self.player_id)
    
    def get_player_by_id(players: List['Player'], player_id: int) -> 'Player':
        for player in players:
            if player.player_id == player_id:
                return player
        raise ValueError("No player with specified ID")
    
    def print_resources(self):
        h = {v: k for k, v in Tile.__dict__.items() if not k.startswith('__') and not callable(k)}
        res = {}
        for k in self.resources:
            res[h[k]] = self.resources[k]
        print("Player {} has resources {}".format(self.player_id, res))
        
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
                max_road_size = max(max_road_size, traverse(self.player_id, [], pos))
        if max_road_size > stats.longest_road_count and max_road_size >= 5:
            stats.longest_road_count = max_road_size
            stats.longest_road_player = self.player_id
            if VERBOSE:
                print("Player {} now has plaque for longest road of size {}".format(self.player_id, max_road_size))
        if VERBOSE:
            print("Player {}'s longest road is size {}".format(self.player_id, max_road_size))
            
    def check_largest_army(self, stats: GameStats):
        if self.knights_played > stats.largest_army_count:
            stats.largest_army_count = self.knights_played
            stats.largest_army_player = self.player_id
            
    def vps(self, board: Board, stats: GameStats):
        sources = { # for pretty printing
            "largest_army": False,
            "longest_road": False,
            "num_settlements": 0,
            "num_cities": 0,
            "num_vp_cards": 0
        }
        vp = 0
        if stats.largest_army_player == self.player_id:
            vp += 2
            sources["largest_army"] = True
        if stats.longest_road_player == self.player_id:
            vp += 2
            sources["longest_road"] = True
        for i in self.dev_cards:
            if i == DevCard.VP:
                vp += 1
                sources["num_vp_cards"] += 1
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player_id:
                    vp += (pos.fixture_type + 1)
                    if pos.fixture_type == 0:
                        sources["num_settlements"] += 1
                    else:
                        sources["num_cities"] += 1
        if VERBOSE:
            print("Player {} has {} VPs: {}".format(self.player_id, vp, sources))
        return vp
    
    def get_resource_cards(self) -> List[int]:
        resource_cards = []
        for res in self.resources:
            for _ in range(self.resources[res]):
                resource_cards.append(res)
        return resource_cards
    
    def set_resource_cards(self, resource_cards: List[int]):
        self.resources = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for card in resource_cards:
            self.resources[card] += 1
    
    def collect_resources(self, board: Board, d6: int):
        if d6 == 7:
            resource_cards = self.get_resource_cards()
            if len(resource_cards) > 7:
                cards_after_halving = len(resource_cards) // 2 if len(resource_cards) % 2 == 0 else (len(resource_cards) + 1) // 2
                resource_cards = random.sample(resource_cards, cards_after_halving)
                self.set_resource_cards(resource_cards)
        else:
            for row in board.positions:
                for pos in row:
                    if pos.fixture == self.player_id:
                        for tile in pos.adjacent_tiles:
                            if tile.tile < 5 and tile.value == d6:
                                if tile.has_knight:
                                    if VERBOSE:
                                        print("Player {} could NOT collect anything due to knight".format(self.player_id))
                                else:
                                    self.resources[tile.tile] += (pos.fixture_type + 1)
                                    if VERBOSE:
                                        h = {v: k for k, v in Tile.__dict__.items() if not k.startswith('__') and not callable(k)}
                                        print("Player {} collects {} {}".format(self.player_id, pos.fixture_type + 1, h[tile.tile]))
        if VERBOSE:
            self.print_resources()
            
    def has_resource(self, resource: int):
        return self.resources[resource] > 0
    
    def get_settlement_options(self, board: Board) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                owns_road = [pos.left_road == self.player_id, pos.right_road == self.player_id, pos.up_road == self.player_id, pos.down_road == self.player_id]
                owns_road = (owns_road.count(True) == 1)
                if board.can_settle(pos) and owns_road:
                    options.append(Action(Action.SETTLE, pos=pos))
        return options
    
    def get_city_options(self, board: Board) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player_id and pos.fixture_type == 0:
                    options.append(Action(Action.BUILD_CITY, pos=pos))
        return options
    
    def get_road_options(self, board: Board, road_building: bool = False, second_road_building: bool = False) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                owns_road = (pos.left_road == self.player_id) or (pos.right_road == self.player_id) or (pos.up_road == self.player_id) or (pos.down_road == self.player_id)
                empty_road_names = ["left_road", "right_road", "up_road", "down_road"]
                road_to_dir = {"left_road": "left", "right_road": "right", "up_road": "up", "down_road": "down"}
                empty_road_names = [road_name for road_name in empty_road_names if getattr(pos, road_name) == None and getattr(pos, road_to_dir[road_name]) != None]
                if owns_road:
                    # print("terminal node {}", pos.pos)
                    for road_name in empty_road_names:
                        action = Action.USE_DEV_ROADS if road_building else Action.BUILD_ROAD
                        action = Action.SECOND_USE_DEV_ROADS if second_road_building else action
                        options.append(Action(action, pos=pos, road_name=road_name))
        return options
    
    def can_build_dev_card(self):
        return self.has_resource(Tile.ROCK) and self.has_resource(Tile.SHEEP) and self.has_resource(Tile.WHEAT)

    def can_build_settlement(self):
        return self.has_resource(Tile.WHEAT) and self.has_resource(Tile.SHEEP) and self.has_resource(Tile.TREE) and self.has_resource(Tile.MUD) and self.settlements_remaining

    def can_build_road(self):
        return self.has_resource(Tile.MUD) and self.has_resource(Tile.TREE) and self.roads_remaining
    
    def can_build_city(self):
        return self.resources[Tile.ROCK] >= 3 and self.resources[Tile.WHEAT] >= 2 and self.cities_remaining

    def get_legal_actions(self, board: Board) -> List[Action]:
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
        # 4:1 or 3:1
        has_3_to_1 = Port.THREE_ONE in self.controlled_ports
        for res in self.resources:
            if has_3_to_1:
                if self.resources[res] >= 3:
                    for new_res in range(5):
                        if new_res != res:
                            legal_actions.append(Action(Action.THREE_TO_ONE, source=res, dest=new_res))
            else:
                if self.resources[res] >= 4:
                    for new_res in range(5):
                        if new_res != res:
                            legal_actions.append(Action(Action.FOUR_TO_ONE, source=res, dest=new_res))
        # Ports
        for port in self.controlled_ports:
            if port != Port.THREE_ONE and self.resources[port] >= 2:
                for new_res in range(5):
                    if new_res != port:
                        legal_actions.append(Action(Action.TWO_TO_ONE, source=port, dest=new_res))
        # Dev Cards
        if DevCard.KNIGHT in self.dev_cards:
            for row in board.tiles:
                for tile in row:
                    if not tile.has_knight and not tile.tile == Tile.DESERT:
                        if len(tile.owning_player_ids):
                            for player_id in tile.owning_player_ids:
                                legal_actions.append(Action(Action.USE_KNIGHT, tile=tile, steal_from_id=player_id))
                        else:
                            legal_actions.append(Action(Action.USE_KNIGHT, tile=tile, steal_from_id=None))
        if DevCard.MONOPOLY in self.dev_cards:
            for res in range(5):
                legal_actions.append(Action(Action.USE_MONOPOLY, resource=res))
        if DevCard.PLENTY in self.dev_cards:
            for res1 in range(5):
                for res2 in range(5):
                    legal_actions.append(Action(Action.USE_YEAR_OF_PLENTY, resource1=res1, resource2=res2))
        if DevCard.ROADS in self.dev_cards:
            # ROAD BUILDING REQUIRES THE STRATEGY TO MANUALLY DEFINE "place_second_dev_roads" to place the second road
            legal_actions += self.get_road_options(board, road_building=True) # this param makes sure we dont use up the player's resources
        return legal_actions
    
    def submit_action(self, action: Action, board: Board, players: List['Player'], stats: GameStats, dev_cards: DevCardPile) -> Action:
        if VERBOSE:
            print("Player {} did {}".format(self.player_id, action))
        if action.action == Action.SETTLE_INIT or action.action == Action.SETTLE:
            self.settlements_remaining -= 1
            action.pos.fixture = self.player_id
            action.pos.fixture_type = 0
            if action.pos.adjacent_port:
                self.controlled_ports.add(action.pos.adjacent_port)
                if VERBOSE:
                    print("Player controls {} ports".format(self.controlled_ports))
            for tile in action.pos.adjacent_tiles:
                tile.owning_player_ids.add(self.player_id)
            if action.action == Action.SETTLE:
                self.resources[Tile.MUD] -= 1
                self.resources[Tile.TREE] -= 1
                self.resources[Tile.WHEAT] -= 1
                self.resources[Tile.SHEEP] -= 1
        elif action.action == Action.BUILD_ROAD_INIT or action.action == Action.BUILD_ROAD or action.action == Action.USE_DEV_ROADS or action.action == Action.SECOND_USE_DEV_ROADS:
            self.roads_remaining -= 1
            setattr(action.pos, action.road_name, self.player_id)
            # set opposite direction from the other edge endpoint
            road_to_dir = {"left_road": "left", "right_road": "right", "up_road": "up", "down_road": "down"}
            road_to_op = {"left_road": "right_road", "right_road": "left_road", "up_road": "down_road", "down_road": "up_road"}
            setattr(getattr(action.pos, road_to_dir[action.road_name]), road_to_op[action.road_name], self.player_id)
            if action.action == Action.BUILD_ROAD:
                self.resources[Tile.MUD] -= 1
                self.resources[Tile.TREE] -= 1
                self.check_longest_road(board, stats)
            if action.action == Action.USE_DEV_ROADS:
                self.dev_cards.remove(DevCard.ROADS)
                self.check_longest_road(board, stats)
            if action.action == Action.SECOND_USE_DEV_ROADS:
                self.check_longest_road(board, stats)
        elif action.action == Action.GET_DEV_CARD:
            self.resources[Tile.ROCK] -= 1
            self.resources[Tile.SHEEP] -= 1
            self.resources[Tile.WHEAT] -= 1
            self.dev_cards.append(dev_cards.draw_top())
        elif action.action == Action.BUILD_CITY:
            self.cities_remaining -= 1
            self.settlements_remaining += 1
            self.resources[Tile.ROCK] -= 3
            self.resources[Tile.WHEAT] -= 2
            action.pos.fixture_type = 1
        elif action.action == Action.FOUR_TO_ONE:
            self.resources[action.source] -= 4
            self.resources[action.dest] += 1
            if VERBOSE:
                self.print_resources()
        elif action.action == Action.THREE_TO_ONE:
            self.resources[action.source] -= 3
            self.resources[action.dest] += 1
            if VERBOSE:
                self.print_resources()
        elif action.action == Action.TWO_TO_ONE:
            self.resources[action.source] -= 2
            self.resources[action.dest] += 1
            if VERBOSE:
                self.print_resources()
        elif action.action == Action.USE_KNIGHT:
            self.dev_cards.remove(DevCard.KNIGHT)
            self.knights_played += 1
            for row in board.tiles:
                for tile in row:
                    tile.has_knight = False
            action.tile.has_knight = True
            if action.steal_from_id != None:
                player_to_steal_from: 'Player' = Player.get_player_by_id(players, action.steal_from_id)
                if VERBOSE:
                    player_to_steal_from.print_resources()
                    if VERBOSE:
                        self.print_resources()
                op_resource_cards = player_to_steal_from.get_resource_cards()
                if len(op_resource_cards):
                    stolen_card = op_resource_cards.pop(random.randrange(len(op_resource_cards)))
                    player_to_steal_from.set_resource_cards(op_resource_cards)
                    self.resources[stolen_card] += 1
                    if VERBOSE:
                        print("Player {} stole a {} from Player {}".format(self.player_id, stolen_card, player_to_steal_from.player_id))
                        player_to_steal_from.print_resources()
                        if VERBOSE:
                            self.print_resources()
                elif VERBOSE:
                    print("Nothing to steal")
            self.check_largest_army(stats)
        elif action.action == Action.USE_MONOPOLY:
            self.dev_cards.remove(DevCard.MONOPOLY)
            total = 0
            for player_to_steal_from in players:
                stealing = player_to_steal_from.resources[action.resource]
                player_to_steal_from.resources[action.resource] = 0
                total += stealing
                if VERBOSE:
                    print("Stole {} {} from Player {}".format(stealing, to_name(action.resource), player_to_steal_from.player_id))
            self.resources[action.resource] = total
            if VERBOSE:
                self.print_resources()
        elif action.action == Action.USE_YEAR_OF_PLENTY:
            self.dev_cards.remove(DevCard.PLENTY)
            self.resources[action.resource1] += 1
            self.resources[action.resource2] += 1

        for res in self.resources:
            if self.resources[res] < 0:
                raise ValueError("Cannot have negative resources")