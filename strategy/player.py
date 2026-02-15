from collections import defaultdict
from copy import deepcopy
import random
from abc import ABC, abstractmethod

from basic import Action, DevCard, DevCardPile, GameStats, Port, Tile
from board import Board
from board.position import Position
import logger

colors = ["red", "blue", "orange", "white", "green", "black"]


class Player(ABC):
    # Class variable to keep track of number of players created, used for assigning player IDs and colors
    num_players = 0

    def __init__(self) -> None:
        # Public attributes
        self.player_id = Player.num_players
        Player.num_players += 1
        assert self.player_id in range(6)
        self.color = colors[self.player_id]
        self.roads_remaining = 15
        self.settlements_remaining = 5
        self.cities_remaining = 4
        self.knights_played = 0
        self.controlled_ports: set[int] = set()
        self.longest_road_length = 1

        # Private attributes between game and player
        self.resources = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.cards: list[int] = []
        self.unusable_dev_cards: list[int] = []  # Need to wait a turn before using

    ###################
    # General Methods #
    ###################

    def __str__(self) -> str:
        return "Player {} (\n\tresources={},\n\troads_remaining={},\n\tsettlements_remaining={},\n\tcities_remaining={},\n\tdev_cards={},\n\tknights_played={},\n\tcontrolled_ports={},\n\tlongest_road_length={})".format(
            self.color,
            {Tile.to_name(k): v for k, v in self.resources.items()},
            self.roads_remaining,
            self.settlements_remaining,
            self.cities_remaining,
            DevCard.to_names(self.cards),
            self.knights_played,
            list(map(Port.to_name, self.controlled_ports)),
            self.longest_road_length,
        )

    # Private attributes between game and player
    def has_resource(self, resource: int) -> bool:
        return self.resources[resource] > 0

    # Private attributes between game and player
    def empty(self) -> bool:
        return sum(self.resources.values()) == 0

    # Private attributes between game and player
    def get_resource_cards(self) -> list[int]:
        """Converts selfs resource cards from self's dictionary of counts to a list of cards, useful for actions like stealing a random card"""
        resource_cards = []
        for res in self.resources:
            for _ in range(self.resources[res]):
                resource_cards.append(res)
        return resource_cards

    # Private attributes between game and player
    def set_resource_cards(self, resource_cards: list[int]):
        """Converts a list of cards to self's dictionary of counts, see `get_resource_cards`"""
        self.resources = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for card in resource_cards:
            self.resources[card] += 1

    def turn_ended(self):
        """Call at end of turn to update any attributes that need to wait until the end of the turn, such as dev cards that were just bought"""
        self.cards += self.unusable_dev_cards
        self.unusable_dev_cards = []

    ################################
    # Strategic Abstract Decisions #
    ################################

    @abstractmethod
    def settle(self, board: Board, second: bool) -> list[Action]:
        raise NotImplementedError()

    @abstractmethod
    def discard_cards(self, num_to_discard: int) -> list[int]:
        raise NotImplementedError()

    @abstractmethod
    def choose_robber_action(self, board: Board) -> Action:
        raise NotImplementedError()

    @abstractmethod
    def accepts_trade(self, propose_trade_action: Action) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def finalizes_trade(
        self, propose_trade_action: Action, players: list[int]
    ) -> Action:
        raise NotImplementedError()

    @abstractmethod
    def do(
        self,
        board: Board,
        stats: GameStats,
    ) -> Action:
        raise NotImplementedError()

    ########################
    # Verification Methods #
    ########################

    def check_longest_road(self, board: Board, stats: GameStats):
        """
        Computes the longest continuous road for this player and updates stats if necessary.
        """

        def traverse(pos, prev_pos, visited_edges):
            max_length = 0
            # For each direction, check if the road belongs to the player and hasn't been visited
            directions = [
                ("left", "left_road", "left"),
                ("right", "right_road", "right"),
                ("up", "up_road", "up"),
                ("down", "down_road", "down"),
            ]
            for dir_name, road_attr, next_attr in directions:
                if hasattr(pos, road_attr):
                    road_owner = getattr(pos, road_attr)
                    next_pos = getattr(pos, next_attr)
                    if (
                        road_owner == self.player_id
                        and next_pos is not None
                        and (pos.pos, next_pos.pos) not in visited_edges
                        and (next_pos.pos, pos.pos) not in visited_edges
                        and (prev_pos is None or next_pos.pos != prev_pos.pos)
                    ):
                        # Mark this edge as visited
                        visited_edges.add((pos.pos, next_pos.pos))
                        length = 1 + traverse(next_pos, pos, visited_edges)
                        max_length = max(max_length, length)
                        visited_edges.remove((pos.pos, next_pos.pos))
            return max_length

        max_road_size = 0
        for row in board.positions:
            for pos in row:
                # Start from every position that has a road belonging to the player
                directions = [
                    ("left", "left_road", "left"),
                    ("right", "right_road", "right"),
                    ("up", "up_road", "up"),
                    ("down", "down_road", "down"),
                ]
                for dir_name, road_attr, next_attr in directions:
                    if hasattr(pos, road_attr):
                        road_owner = getattr(pos, road_attr)
                        next_pos = getattr(pos, next_attr)
                        if road_owner == self.player_id and next_pos is not None:
                            visited_edges = set()
                            visited_edges.add((pos.pos, next_pos.pos))
                            length = 1 + traverse(next_pos, pos, visited_edges)
                            max_road_size = max(max_road_size, length)

        if max_road_size > stats.longest_road_count and max_road_size >= 5:
            stats.longest_road_count = max_road_size
            stats.longest_road_player = self.player_id
            logger.game(
                "Player {} now has plaque for longest road of size {}".format(
                    self.color, max_road_size
                )
            )
        self.longest_road_length = max_road_size

    def check_largest_army(self, stats: GameStats):
        if self.knights_played > stats.largest_army_count:
            stats.largest_army_count = self.knights_played
            stats.largest_army_player = self.player_id

    def vps(self, board: Board, stats: GameStats):
        sources = {  # for pretty printing
            "largest_army": False,
            "longest_road": False,
            "num_settlements": 0,
            "num_cities": 0,
            "num_vp_cards": 0,
        }
        vp = 0
        if stats.largest_army_player == self.player_id:
            vp += 2
            sources["largest_army"] = True
        if stats.longest_road_player == self.player_id:
            vp += 2
            sources["longest_road"] = True
        for i in self.cards:
            if i == DevCard.VP:
                vp += 1
                sources["num_vp_cards"] += 1
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player_id:
                    vp += pos.fixture_score
                    if pos.fixture_type == 0:
                        sources["num_settlements"] += 1
                    else:
                        sources["num_cities"] += 1
        logger.debug("Player {} has {} VPs: {}".format(self.color, vp, sources))
        return vp

    def check_all_ok(self):
        for res in self.resources:
            if self.resources[res] < 0:
                raise ValueError("Cannot have negative resources")
        if self.roads_remaining < 0:
            raise ValueError("Cannot build too many roads")
        if self.settlements_remaining < 0:
            raise ValueError("Cannot build too many settlements")
        if self.cities_remaining < 0:
            raise ValueError("Cannot build too many cities")

    ################################
    # Collecting Resources Methods #
    ################################

    def on_7_roll(self):
        resource_cards = self.get_resource_cards()
        if len(resource_cards) > 7:
            num_to_discard = len(resource_cards) // 2
            discard_cards = self.discard_cards(num_to_discard)
            new_cards = []
            for i, card in enumerate(resource_cards):
                if i in discard_cards:
                    continue
                new_cards.append(card)
            self.set_resource_cards(new_cards)

    def collect_resource_from_tile(self, tile: Tile, pos: Position):
        if tile.has_knight:
            logger.debug(
                "Player {} could NOT collect anything due to knight".format(self.color),
            )
        else:
            self.resources[tile.tile] += pos.fixture_score
            logger.debug(
                "Player {} collects {} {}".format(
                    self.color,
                    pos.fixture_score,
                    Tile.to_name(tile.tile),
                ),
            )

    def collect_resources(self, board: Board, d6: int):
        for pos in board.get_positions_owned_by_player(self.player_id):
            for tile in pos.adjacent_tiles:
                if tile.tile < 5 and tile.value == d6:
                    self.collect_resource_from_tile(tile, pos)

    def handle_dice_roll(self, board: Board, d6: int):
        if d6 == 7:
            self.on_7_roll()
        else:
            self.collect_resources(board, d6)

    #################################
    # Building Capabilities Methods #
    #################################

    def can_accept_trade(self, propose_trade_action: Action) -> bool:
        res_to_qty = defaultdict(int)
        for res in propose_trade_action.params["theirs"]:
            res_to_qty[res] += 1
        for res in propose_trade_action.params["theirs"]:
            if self.resources[res] < res_to_qty[res]:
                return False
        return True

    def can_build_dev_card(self):
        return (
            self.has_resource(Tile.ROCK)
            and self.has_resource(Tile.SHEEP)
            and self.has_resource(Tile.WHEAT)
        )

    def can_build_settlement(self):
        return (
            self.has_resource(Tile.WHEAT)
            and self.has_resource(Tile.SHEEP)
            and self.has_resource(Tile.TREE)
            and self.has_resource(Tile.MUD)
            and self.settlements_remaining
        )

    def can_build_road(self):
        return (
            self.has_resource(Tile.MUD)
            and self.has_resource(Tile.TREE)
            and self.roads_remaining
        )

    def can_build_city(self):
        return (
            self.resources[Tile.ROCK] >= 3
            and self.resources[Tile.WHEAT] >= 2
            and self.cities_remaining
        )

    #########################
    # Legal Actions Methods #
    #########################

    def get_settlement_options(self, board: Board) -> list[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                owns_road = [
                    pos.left_road == self.player_id,
                    pos.right_road == self.player_id,
                    pos.up_road == self.player_id,
                    pos.down_road == self.player_id,
                ]
                owns_road = owns_road.count(True) == 1
                if pos.can_settle() and owns_road:
                    options.append(Action(Action.SETTLE, pos=pos.pos))
        return options

    def get_city_options(self, board: Board) -> list[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player_id and pos.fixture_type == 0:
                    options.append(Action(Action.BUILD_CITY, pos=pos.pos))
        return options

    def get_robber_options(self, board: Board) -> list[Action]:
        knight_options = board.get_knight_options(self.player_id)
        return [
            Action(Action.ROB, tile=tile.pos, steal_from_id=steal_from_id)
            for tile, steal_from_id in knight_options
        ]

    def get_legal_actions(self, board: Board, stats: GameStats) -> list[Action]:
        legal_actions = []
        if self.can_build_dev_card() and stats.num_dev_cards > 0:
            legal_actions.append(Action(Action.GET_DEV_CARD))
        if self.can_build_settlement():
            settlement_options = self.get_settlement_options(board)
            legal_actions += settlement_options
        if self.can_build_road():
            legal_actions += [
                Action(Action.BUILD_ROAD, pos=pos.pos, road_name=road_name)
                for pos, road_name in board.get_road_options(self.player_id)
            ]
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
                            legal_actions.append(
                                Action(Action.THREE_TO_ONE, source=res, dest=new_res)
                            )
            else:
                if self.resources[res] >= 4:
                    for new_res in range(5):
                        if new_res != res:
                            legal_actions.append(
                                Action(Action.FOUR_TO_ONE, source=res, dest=new_res)
                            )
        # Ports
        for port in self.controlled_ports:
            if port != Port.THREE_ONE and self.resources[port] >= 2:
                for new_res in range(5):
                    if new_res != port:
                        legal_actions.append(
                            Action(Action.TWO_TO_ONE, source=port, dest=new_res)
                        )
        # Dev Cards
        if DevCard.KNIGHT in self.cards:
            knight_options = board.get_knight_options(self.player_id)
            legal_actions += [
                Action(Action.USE_KNIGHT, tile=tile.pos, steal_from_id=steal_from_id)
                for tile, steal_from_id in knight_options
            ]
        if DevCard.MONOPOLY in self.cards:
            for res in range(5):
                legal_actions.append(Action(Action.USE_MONOPOLY, resource=res))
        if DevCard.PLENTY in self.cards:
            for res1 in range(5):
                for res2 in range(5):
                    legal_actions.append(
                        Action(
                            Action.USE_YEAR_OF_PLENTY, resource1=res1, resource2=res2
                        )
                    )
        if DevCard.ROADS in self.cards:
            if self.roads_remaining >= 1:
                for pos1, road1 in board.get_road_options(self.player_id):
                    if self.roads_remaining >= 2:
                        new_board = deepcopy(board)
                        new_board.get_position(pos1.pos).build_road(
                            road1, self.player_id
                        )
                        for pos2, road2 in new_board.get_road_options(self.player_id):
                            legal_actions.append(
                                Action(
                                    Action.USE_DEV_ROADS,
                                    pos1=pos1.pos,
                                    road1=road1,
                                    pos2=pos2.pos,
                                    road2=road2,
                                )
                            )
                    else:
                        legal_actions.append(
                            Action(
                                Action.USE_DEV_ROADS,
                                pos1=pos1.pos,
                                road1=road1,
                                pos2=None,
                                road2=None,
                            )
                        )
        return legal_actions
