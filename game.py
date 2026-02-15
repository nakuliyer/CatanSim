import random
import time

from basic import Action, DevCardPile, DevCard, GameStats, Tile
from board import Board, RandomBoard, Position
from strategy import Player, RandomStrategy
from gui import init_gui, draw_gui, quit_gui, add_messages
import logger


class Game:
    def __init__(
        self,
        players: list[Player],
        board: Board,
        gui: bool,
        force_quit_after_round: int,
        speed: float,
    ) -> None:
        self.players = players
        self.board = board
        self.gui = gui
        self.force_quit_after_round = force_quit_after_round
        self.speed = speed

        logger.game("Board is\n{}".format(board))

        self.cards = DevCardPile()
        self.stats = GameStats()

        self.turn = 0  # player id of current turn

    ###################
    # General Methods #
    ###################

    def get_player_by_id(self, player_id: int) -> "Player":
        for player in self.players:
            if player.player_id == player_id:
                return player
        raise ValueError("No player with specified ID")

    #####################
    # Game Loop Methods #
    #####################

    def init_game(self) -> None:
        if self.gui:
            init_gui()

        logger.game("Initializing settlements and roads")
        for second in [False, True]:
            order = -1 if second else 1
            for player in self.players[::order]:
                if self.gui:
                    quit_gui()
                for action in player.settle(self.board, second):
                    self.handle_action(action, player)
                    if self.gui:
                        self.write()
                        draw_gui(self.board)
                time.sleep(1 / self.speed)
        for player in self.players:
            logger.debug(player)

    def game_loop(self, turn: int) -> bool:
        if self.gui:
            quit_gui()
        d6 = random.randint(1, 6) + random.randint(1, 6)
        logger.game("{} rolled".format(d6))
        for player in self.players:
            player.handle_dice_roll(self.board, d6)
        if d6 == 7:
            self.handle_action(
                self.players[turn].choose_robber_action(self.board),
                self.players[turn],
            )
        action = self.players[turn].do(self.board, self.stats)
        while action.action != Action.DO_NOTHING:
            self.handle_action(action, self.players[turn])
            action = self.players[turn].do(self.board, self.stats)
        if self.gui:
            self.write()
            draw_gui(self.board)
        time.sleep(1 / self.speed)
        for player in self.players:
            player.check_all_ok()
            player.turn_ended()
        for player in self.players:
            logger.debug(player)
        self.stats.num_dev_cards = len(self.cards.pile)
        vps = self.players[turn].vps(self.board, self.stats)
        if vps >= 10:
            logger.game("Player {} won!".format(self.players[turn].color))
            return False
        else:
            return True

    def post_game(self) -> None:
        if self.gui:
            while True:
                # Wait for user to close the window
                quit_gui()
                draw_gui(self.board)

    def write(self) -> None:
        if self.gui:
            add_messages(logger.messages)
            logger.print_all()
            logger.flush()
        else:
            logger.print_all()
            logger.flush()

    def play(self) -> None:
        try:
            self.init_game()
            rnd = 0
            turn = 0
            while self.game_loop(turn):
                self.write()
                turn = (turn + 1) % len(self.players)
                if turn == 0:
                    rnd += 1
                if rnd >= self.force_quit_after_round:
                    raise ValueError("Game Lasted Too Long")
            self.write()
            self.post_game()
        except:
            logger.game("Game crashed")
            for player in self.players:
                logger.game(player)
            logger.print_all()
            raise

    ########################
    # Verification Methods #
    ########################

    def check_longest_road(self, player: Player):
        """
        Computes the longest continuous road for this player and updates stats if necessary.
        """

        def traverse(player, pos, prev_pos, visited_edges):
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
                        road_owner == player.player_id
                        and next_pos is not None
                        and (pos.pos, next_pos.pos) not in visited_edges
                        and (next_pos.pos, pos.pos) not in visited_edges
                        and (prev_pos is None or next_pos.pos != prev_pos.pos)
                    ):
                        # Mark this edge as visited
                        visited_edges.add((pos.pos, next_pos.pos))
                        length = 1 + traverse(player, next_pos, pos, visited_edges)
                        max_length = max(max_length, length)
                        visited_edges.remove((pos.pos, next_pos.pos))
            return max_length

        max_road_size = 0
        for row in self.board.positions:
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
                        if road_owner == player.player_id and next_pos is not None:
                            visited_edges = set()
                            visited_edges.add((pos.pos, next_pos.pos))
                            length = 1 + traverse(player, next_pos, pos, visited_edges)
                            max_road_size = max(max_road_size, length)

        if max_road_size > self.stats.longest_road_count and max_road_size >= 5:
            self.stats.longest_road_count = max_road_size
            self.stats.longest_road_player = player.player_id
            logger.game(
                "Player {} now has plaque for longest road of size {}".format(
                    player.color, max_road_size
                )
            )
        player.longest_road_length = max_road_size

    def check_largest_army(self, player: Player):
        if player.knights_played > self.stats.largest_army_count:
            self.stats.largest_army_count = player.knights_played
            self.stats.largest_army_player = player.player_id

    ##########################
    # Handle Actions Methods #
    ##########################

    def handle_settlement(self, action: Action, player: Player) -> None:
        player.settlements_remaining -= 1
        pos_tuple: tuple[int, int] = action.params["pos"]
        pos: Position = self.board.get_position(pos_tuple)
        pos.fixture = player.player_id
        pos.fixture_type = 0
        if pos.adjacent_port:
            player.controlled_ports.add(pos.adjacent_port)
        for tile in pos.adjacent_tiles:
            tile.owning_player_ids.add(player.player_id)
        if action.action == Action.SETTLE:
            player.resources[Tile.MUD] -= 1
            player.resources[Tile.TREE] -= 1
            player.resources[Tile.WHEAT] -= 1
            player.resources[Tile.SHEEP] -= 1

    def handle_build_road(self, action: Action, player: Player) -> None:
        if player.roads_remaining == 0:
            return
        player.roads_remaining -= 1
        pos_tuple: tuple[int, int] = action.params["pos"]
        pos: Position = self.board.get_position(pos_tuple)
        road_name: str = action.params["road_name"]
        pos.build_road(road_name, player.player_id)
        self.check_longest_road(player)
        if action.action == Action.BUILD_ROAD:
            player.resources[Tile.MUD] -= 1
            player.resources[Tile.TREE] -= 1

    def handle_use_dev_roads(self, action: Action, player: Player) -> None:
        player.cards.remove(DevCard.ROADS)
        if player.roads_remaining == 0:
            return
        pos1_tuple: tuple[int, int] = action.params["pos1"]
        pos1: Position = self.board.get_position(pos1_tuple)
        road1: str = action.params["road1"]
        pos1.build_road(road1, player.player_id)
        player.roads_remaining -= 1
        if player.roads_remaining == 0:
            return
        pos2_tuple: tuple[int, int] = action.params["pos2"]
        pos2: Position = self.board.get_position(pos2_tuple)
        road2: str = action.params["road2"]
        pos2.build_road(road2, player.player_id)
        player.roads_remaining -= 1

    def handle_get_dev_card(self, action: Action, player: Player) -> None:
        player.resources[Tile.ROCK] -= 1
        player.resources[Tile.SHEEP] -= 1
        player.resources[Tile.WHEAT] -= 1
        card = self.cards.draw_top()
        player.unusable_dev_cards.append(card)
        logger.debug(
            "Player {} got card {}".format(player.color, DevCard.to_name(card))
        )

    def handle_build_city(self, action: Action, player: Player) -> None:
        player.cities_remaining -= 1
        player.settlements_remaining += 1
        player.resources[Tile.ROCK] -= 3
        player.resources[Tile.WHEAT] -= 2
        pos_tuple: tuple[int, int] = action.params["pos"]
        pos: Position = self.board.get_position(pos_tuple)
        pos.fixture_type = 1

    def handle_four_to_one(self, action: Action, player: Player) -> None:
        source: int = action.params["source"]
        dest: int = action.params["dest"]
        player.resources[source] -= 4
        player.resources[dest] += 1

    def handle_three_to_one(self, action: Action, player: Player) -> None:
        source: int = action.params["source"]
        dest: int = action.params["dest"]
        player.resources[source] -= 3
        player.resources[dest] += 1

    def handle_two_to_one(self, action: Action, player: Player) -> None:
        source: int = action.params["source"]
        dest: int = action.params["dest"]
        player.resources[source] -= 2
        player.resources[dest] += 1

    def handle_year_of_plenty(self, action: Action, player: Player) -> None:
        resource1: int = action.params["resource1"]
        resource2: int = action.params["resource2"]
        player.cards.remove(DevCard.PLENTY)
        player.resources[resource1] += 1
        player.resources[resource2] += 1

    def handle_rob(self, action: Action, player: Player) -> None:
        if action.action == Action.USE_KNIGHT:
            player.cards.remove(DevCard.KNIGHT)
            player.knights_played += 1
            self.check_largest_army(player)
        for row in self.board.tiles:
            for tile in row:
                tile.has_knight = False
        tile_tuple: tuple[int, int] = action.params["tile"]
        tile: Tile = self.board.get_tile(tile_tuple)
        steal_from_id: int | None = action.params["steal_from_id"]
        tile.has_knight = True
        if steal_from_id is not None:
            player_to_steal_from: "Player" = self.get_player_by_id(steal_from_id)
            op_resource_cards = player_to_steal_from.get_resource_cards()
            if len(op_resource_cards):
                stolen_card = op_resource_cards.pop(
                    random.randrange(len(op_resource_cards))
                )
                player_to_steal_from.set_resource_cards(op_resource_cards)
                player.resources[stolen_card] += 1
                logger.debug(
                    "Player {} stole a {} from Player {}".format(
                        player.color,
                        Tile.to_name(stolen_card),
                        player_to_steal_from.color,
                    )
                )
                logger.game(
                    "Player {} stole a resource from Player {}".format(
                        player.color, player_to_steal_from.color
                    )
                )
            else:
                logger.game(
                    "Player {} tried to steal from Player {}, but nothing to steal".format(
                        player.color, player_to_steal_from.color
                    )
                )

    def handle_monopoly(self, action: Action, player: Player) -> None:
        resource: int = action.params["resource"]
        player.cards.remove(DevCard.MONOPOLY)
        total = 0
        for player_to_steal_from in self.players:
            if player_to_steal_from.player_id == player.player_id:
                continue
            stealing = player_to_steal_from.resources[resource]
            player_to_steal_from.resources[resource] = 0
            total += stealing
            logger.game(
                "Stole {} {} from Player {} with Monopoly".format(
                    stealing,
                    Tile.to_name(resource),
                    player_to_steal_from.color,
                )
            )
        player.resources[resource] += total

    def handle_trade(self, action: Action, player: Player) -> None:
        with_player_id: int = action.params["with_player"]
        mine: list[int] = action.params["mine"]
        theirs: list[int] = action.params["theirs"]
        other_player = self.get_player_by_id(with_player_id)
        for res in mine:
            player.resources[res] -= 1
            other_player.resources[res] += 1
        for res in theirs:
            other_player.resources[res] -= 1
            player.resources[res] += 1

    def handle_propose_trade(self, action: Action, player: Player) -> None:
        logger.game("Player {} proposes trade {}".format(player.color, action))
        logger.debug(
            "Player {} has cards {}".format(
                player.color,
                player.get_resource_cards(),
            )
        )
        accepting_players: list[int] = []
        for other_player in self.players:
            if other_player.player_id == player.player_id:
                continue
            if other_player.can_accept_trade(action) and other_player.accepts_trade(
                action
            ):
                logger.game("Player {} accepts the trade".format(other_player.color))
                accepting_players.append(other_player.player_id)
        if not accepting_players:
            logger.game("No players accepted the trade")
        else:
            action = player.finalizes_trade(action, accepting_players)
            logger.debug(
                "Other player chosen for trade {} with cards {}".format(
                    self.players[action.params["with_player"]].color,
                    self.players[action.params["with_player"]].get_resource_cards(),
                )
            )
            self.handle_action(action, player)

    def handle_action(self, action: Action, player: Player) -> None:
        action_handlers = {
            Action.DO_NOTHING: lambda *_: None,
            Action.SETTLE: self.handle_settlement,
            Action.BUILD_CITY: self.handle_build_city,
            Action.FOUR_TO_ONE: self.handle_four_to_one,
            Action.THREE_TO_ONE: self.handle_three_to_one,
            Action.BUILD_ROAD: self.handle_build_road,
            Action.USE_KNIGHT: self.handle_rob,
            Action.USE_MONOPOLY: self.handle_monopoly,
            Action.USE_DEV_ROADS: self.handle_use_dev_roads,
            Action.USE_YEAR_OF_PLENTY: self.handle_year_of_plenty,
            Action.TWO_TO_ONE: self.handle_two_to_one,
            Action.ROB: self.handle_rob,
            Action.TRADE: self.handle_trade,
            Action.PROPOSE_TRADE: self.handle_propose_trade,
            Action.GET_DEV_CARD: self.handle_get_dev_card,
            Action.SETTLE_INIT: self.handle_settlement,
            Action.BUILD_ROAD_INIT: self.handle_build_road,
        }

        if action.action not in action_handlers:
            raise ValueError("Invalid action {}".format(action))
        action_handlers[action.action](action, player)


def play(gui: bool, force_quit_after_round: int, speed: float) -> None:
    board = RandomBoard()
    players: list[Player] = [
        RandomStrategy(),
        RandomStrategy(),
        RandomStrategy(),
    ]
    Game(players, board, gui, force_quit_after_round, speed).play()


def play_cli(force_quit_after_round: int, speed: float) -> None:
    try:
        play(gui=False, force_quit_after_round=force_quit_after_round, speed=speed)
    except:
        logger.print_all()
        raise


def play_gui(force_quit_after_round: int, speed: float) -> None:
    play(gui=True, force_quit_after_round=force_quit_after_round, speed=speed)
