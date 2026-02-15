import random
from typing import List, Set, Tuple

from basic import Port, Tile, GameStats, Action, DevCard, DevCardPile, Messages
from board import Board
from position import Position


class Player:
    def __init__(self, player_id: int, messages: Messages, **params):
        self.player_id = player_id
        self.messages = messages
        self.resources = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.roads_remaining = 15
        self.settlements_remaining = 5
        self.cities_remaining = 4
        self.dev_cards: List[DevCard] = []
        self.unusable_dev_cards: List[DevCard] = []
        self.knights_played = 0
        self.controlled_ports: Set[Port] = set()
        self.longest_road_length = 1
        self.__dict__.update(params)

    ###################
    # General Methods #
    ###################

    def __repr__(self):
        return "Player {} (resources={}, roads_remaining={}, settlements_remaining={}, cities_remaining={}, dev_cards={}, knights_played={}, controlled_ports={}, longest_road_length={})".format(
            self.player_id,
            {Tile.to_name(k): v for k, v in self.resources.items()},
            self.roads_remaining,
            self.settlements_remaining,
            self.cities_remaining,
            DevCard.to_names(self.dev_cards),
            self.knights_played,
            list(map(Port.to_name, self.controlled_ports)),
            self.longest_road_length,
        )

    def has_resource(self, resource: int) -> bool:
        return self.resources[resource] > 0
    
    def has_any_resource(self) -> bool:
        return any(map(self.has_resource, self.resources))

    @staticmethod
    def get_player_by_id(players: List["Player"], player_id: int) -> "Player":
        for player in players:
            if player.player_id == player_id:
                return player
        raise ValueError("No player with specified ID")

    def get_resource_cards(self) -> List[int]:
        """Converts selfs resource cards from self's dictionary of counts to a list of cards, useful for actions like stealing a random card"""
        resource_cards = []
        for res in self.resources:
            for _ in range(self.resources[res]):
                resource_cards.append(res)
        return resource_cards

    def set_resource_cards(self, resource_cards: List[int]):
        """Converts a list of cards to self's dictionary of counts, see `get_resource_cards`"""
        self.resources = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        for card in resource_cards:
            self.resources[card] += 1
            
    def turn_ended(self):
        self.dev_cards += self.unusable_dev_cards
        self.unusable_dev_cards = []

    ########################
    # Verification Methods #
    ########################

    def check_longest_road(self, board: Board, stats: GameStats):
        def traverse(player: int, seen: List[Tuple[int, int]], node: Position):
            seen = seen + [node.pos]
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
            return 1 + max(options)

        max_road_size = 0
        for row in board.positions:
            for pos in row:
                max_road_size = max(max_road_size, traverse(self.player_id, [], pos))
        if max_road_size > stats.longest_road_count and max_road_size >= 5:
            stats.longest_road_count = max_road_size
            stats.longest_road_player = self.player_id
            self.messages.add(
                "Player {} now has plaque for longest road of size {}".format(
                    self.player_id, max_road_size
                ),
                1,
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
        for i in self.dev_cards:
            if i == DevCard.VP:
                vp += 1
                sources["num_vp_cards"] += 1
        for row in board.positions:
            for pos in row:
                if pos.fixture == self.player_id:
                    vp += pos.fixture_type + 1
                    if pos.fixture_type == 0:
                        sources["num_settlements"] += 1
                    else:
                        sources["num_cities"] += 1
        self.messages.add(
            "Player {} has {} VPs: {}".format(self.player_id, vp, sources), 2
        )
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
            cards_after_halving = (
                len(resource_cards) // 2
                if len(resource_cards) % 2 == 0
                else (len(resource_cards) + 1) // 2
            )
            resource_cards = random.sample(resource_cards, cards_after_halving)
            self.set_resource_cards(resource_cards)
            
    def collect_resource_from_tile(self, tile: Tile, pos: Position):
        if tile.has_knight:
            self.messages.add(
                "Player {} could NOT collect anything due to knight".format(
                    self.player_id
                ),
                2,
            )
        else:
            self.resources[tile.tile] += pos.fixture_type + 1
            self.messages.add(
                "Player {} collects {} {}".format(
                    self.player_id,
                    pos.fixture_type + 1,
                    Tile.to_name(tile.tile),
                ),
                2,
            )

    def collect_resources(self, board: Board, d6: int):
        for pos in board.get_positions(owned_by_player=self.player_id):
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

    def get_settlement_options(self, board: Board) -> List[Action]:
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

    def get_road_options(
        self,
        board: Board,
        action_type: int = Action.BUILD_ROAD
    ) -> List[Action]:
        options = []
        for row in board.positions:
            for pos in row:
                owns_road = (
                    (pos.left_road == self.player_id)
                    or (pos.right_road == self.player_id)
                    or (pos.up_road == self.player_id)
                    or (pos.down_road == self.player_id)
                )
                empty_road_names = pos.get_empty_road_names()
                if owns_road:
                    for road_name in empty_road_names:
                        options.append(Action(action_type, pos=pos, road_name=road_name))
        return options

    def get_knight_options(
        self, board: Board, action_type: int = Action.USE_KNIGHT
    ) -> List[Action]:
        knight_options: List[Action] = []
        for row in board.tiles:
            for tile in row:
                if not tile.has_knight and not tile.tile == Tile.DESERT:
                    if len(tile.owning_player_ids):
                        for player_id in tile.owning_player_ids:
                            knight_options.append(
                                Action(
                                    action_type,
                                    tile=tile,
                                    steal_from_id=player_id,
                                )
                            )
                    else:
                        knight_options.append(
                            Action(action_type, tile=tile, steal_from_id=None)
                        )
        return knight_options

    def get_robber_options(self, board: Board) -> List[Action]:
        return self.get_knight_options(board, Action.ROB)

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
        if DevCard.KNIGHT in self.dev_cards:
            legal_actions += self.get_knight_options(board)
        if DevCard.MONOPOLY in self.dev_cards:
            for res in range(5):
                legal_actions.append(Action(Action.USE_MONOPOLY, resource=res))
        if DevCard.PLENTY in self.dev_cards:
            for res1 in range(5):
                for res2 in range(5):
                    legal_actions.append(
                        Action(
                            Action.USE_YEAR_OF_PLENTY, resource1=res1, resource2=res2
                        )
                    )
        if DevCard.ROADS in self.dev_cards:
            # ROAD BUILDING REQUIRES THE STRATEGY TO MANUALLY DEFINE "place_second_dev_roads" to place the second road
            legal_actions += self.get_road_options(board, Action.USE_DEV_ROADS)
        return legal_actions

    def submit_action(
        self,
        action: Action,
        board: Board,
        players: List["Player"],
        stats: GameStats,
        dev_cards: DevCardPile,
    ) -> Action:
        self.messages.add("Player {} did {}".format(self.player_id, action), 1)
        if action.action in (Action.SETTLE_INIT, Action.SETTLE):
            self.settlements_remaining -= 1
            action.pos.fixture = self.player_id
            action.pos.fixture_type = 0
            if action.pos.adjacent_port:
                self.controlled_ports.add(action.pos.adjacent_port)
            for tile in action.pos.adjacent_tiles:
                tile.owning_player_ids.add(self.player_id)
            if action.action == Action.SETTLE:
                self.resources[Tile.MUD] -= 1
                self.resources[Tile.TREE] -= 1
                self.resources[Tile.WHEAT] -= 1
                self.resources[Tile.SHEEP] -= 1
        elif action.action in (
            Action.BUILD_ROAD_INIT,
            Action.BUILD_ROAD,
            Action.USE_DEV_ROADS,
            Action.SECOND_USE_DEV_ROADS,
        ):
            if self.roads_remaining == 0:
                if action.action == Action.USE_DEV_ROADS:
                    self.dev_cards.remove(DevCard.ROADS)
                return
            self.roads_remaining -= 1
            setattr(action.pos, action.road_name, self.player_id)
            # set opposite direction from the other edge endpoint
            road_to_dir = {
                "left_road": "left",
                "right_road": "right",
                "up_road": "up",
                "down_road": "down",
            }
            road_to_op = {
                "left_road": "right_road",
                "right_road": "left_road",
                "up_road": "down_road",
                "down_road": "up_road",
            }
            setattr(
                getattr(action.pos, road_to_dir[action.road_name]),
                road_to_op[action.road_name],
                self.player_id,
            )
            self.check_longest_road(board, stats)
            if action.action == Action.BUILD_ROAD:
                self.resources[Tile.MUD] -= 1
                self.resources[Tile.TREE] -= 1
            if action.action == Action.USE_DEV_ROADS:
                self.dev_cards.remove(DevCard.ROADS)
        elif action.action == Action.GET_DEV_CARD:
            self.resources[Tile.ROCK] -= 1
            self.resources[Tile.SHEEP] -= 1
            self.resources[Tile.WHEAT] -= 1
            card = dev_cards.draw_top()
            self.unusable_dev_cards.append(card)
            self.messages.add("Player {} got card {}".format(self.player_id, DevCard.to_name(card)))
        elif action.action == Action.BUILD_CITY:
            self.cities_remaining -= 1
            self.settlements_remaining += 1
            self.resources[Tile.ROCK] -= 3
            self.resources[Tile.WHEAT] -= 2
            action.pos.fixture_type = 1
        elif action.action == Action.FOUR_TO_ONE:
            self.resources[action.source] -= 4
            self.resources[action.dest] += 1
        elif action.action == Action.THREE_TO_ONE:
            self.resources[action.source] -= 3
            self.resources[action.dest] += 1
        elif action.action == Action.TWO_TO_ONE:
            self.resources[action.source] -= 2
            self.resources[action.dest] += 1
        elif action.action in (Action.USE_KNIGHT, Action.ROB):
            if action.action == Action.USE_KNIGHT:
                self.dev_cards.remove(DevCard.KNIGHT)
                self.knights_played += 1
            for row in board.tiles:
                for tile in row:
                    tile.has_knight = False
            action.tile.has_knight = True
            if action.steal_from_id is not None:
                player_to_steal_from: "Player" = Player.get_player_by_id(
                    players, action.steal_from_id
                )
                op_resource_cards = player_to_steal_from.get_resource_cards()
                if len(op_resource_cards):
                    stolen_card = op_resource_cards.pop(
                        random.randrange(len(op_resource_cards))
                    )
                    player_to_steal_from.set_resource_cards(op_resource_cards)
                    self.resources[stolen_card] += 1
                    self.messages.add(
                        "Player {} stole a {} from Player {}".format(
                            self.player_id,
                            Tile.to_name(stolen_card),
                            player_to_steal_from.player_id,
                        ),
                        1,
                    )
                else:
                    self.messages.add(
                        "Player {} tried to steal from Player {}, but nothing to steal".format(
                            self.player_id, player_to_steal_from.player_id
                        ),
                        1,
                    )
            self.check_largest_army(stats)
        elif action.action == Action.USE_MONOPOLY:
            self.dev_cards.remove(DevCard.MONOPOLY)
            total = 0
            for player_to_steal_from in players:
                stealing = player_to_steal_from.resources[action.resource]
                player_to_steal_from.resources[action.resource] = 0
                total += stealing
                self.messages.add(
                    "Stole {} {} from Player {} with Monopoly".format(
                        stealing,
                        Tile.to_name(action.resource),
                        player_to_steal_from.player_id,
                    ),
                    1,
                )
            self.resources[action.resource] = total
        elif action.action == Action.USE_YEAR_OF_PLENTY:
            self.dev_cards.remove(DevCard.PLENTY)
            self.resources[action.resource1] += 1
            self.resources[action.resource2] += 1
        elif action.action == Action.TRADE:
            other_player = Player.get_player_by_id(players, action.with_player)
            for res in action.mine:
                self.resources[res] -= 1
                other_player.resources[res] += 1
            for res in action.theirs:
                other_player.resources[res] -= 1
                self.resources[res] += 1
        else:
            raise ValueError("Unknown Action")
