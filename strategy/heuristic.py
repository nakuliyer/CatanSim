from collections import defaultdict
import random
from itertools import chain

from basic import Action, Tile, Port, GameStats
from board import Board, Position
import logger

from .player import Player


class HeuristicStrategy(Player):
    # This strategy does not actually use reinforcement learning, but instead just uses some heuristics to make decisions.
    # It is meant to be a stronger baseline than the random strategy.

    def __init__(self):
        super().__init__()
        # the position we want to settle on, which we will use to guide our road building and other decisions
        self.target_pos: tuple[int, int] = 0, 0

    def pos_to_score(self, board: Board) -> dict[tuple[int, int], float]:
        controlled_resources_to_score: dict[int, int] = defaultdict(int)
        for pos in chain(*board.positions):
            if pos.fixture == self.player_id:
                for tile in pos.adjacent_tiles:
                    # score the tile based on how good it is
                    controlled_resources_to_score[tile.tile] += 10 - abs(tile.value - 7)
        pos_to_score: dict[tuple[int, int], float] = {}
        for pos in chain(*board.positions):
            if pos.can_settle():
                score = 0.0
                adj_tile_to_count = defaultdict(int)
                new_controlled_resources_to_score = controlled_resources_to_score.copy()
                for tile in pos.adjacent_tiles:
                    adj_tile_to_count[tile.tile] += 1
                    new_controlled_resources_to_score[tile.tile] += 10 - abs(
                        tile.value - 7
                    )
                for tile in pos.adjacent_tiles:
                    if tile.tile == Tile.DESERT:
                        # strongly penalize settling on desert
                        score -= 3
                        continue
                    multiplier = 1
                    # encourage settling on diverse resources
                    if controlled_resources_to_score[tile.tile] == 0:
                        # we don't have this resource yet, so encourage it more
                        multiplier = 1.4
                    if new_controlled_resources_to_score[tile.tile] > 10:
                        # we already have a lot of this resource, so encourage it less
                        multiplier = 0.7
                    probability_score = 10 - abs(tile.value - 7)
                    score += multiplier * probability_score
                # encourage ports
                if pos.adjacent_port is not None:
                    if pos.adjacent_port == Port.THREE_ONE:
                        score += 5
                    else:
                        # encourage settling on ports for resources we have a lot of
                        resource_score = new_controlled_resources_to_score[
                            pos.adjacent_port
                        ]
                        score += (resource_score + 1) * 0.6 + 4
                score = max(
                    score, 0.1
                )  # ensure score is positive for probability distribution
                pos_to_score[pos.pos] = score
        total_score = sum(pos_to_score.values())
        # normalize scores to be a probability distribution
        for pos in pos_to_score:
            pos_to_score[pos] /= total_score
        return pos_to_score

    def build_ideal_road(
        self, action_id: int, board: Board, pos: tuple[int, int] | None
    ) -> Action:
        while (
            board.get_position(self.target_pos).fixture is not None
            or not board.get_position(self.target_pos).can_settle()
        ):
            self.target_pos = random.choices(
                list(self.pos_to_score(board).keys()),
                weights=list(self.pos_to_score(board).values()),
                k=1,
            )[0]
        logger.debug(
            f"Heuristic agent targets position {self.target_pos} with score {self.pos_to_score(board)[self.target_pos]:.2f} from distribution {self.pos_to_score(board)}"
        )
        if pos is None:
            # pick the settlement that we own closest to our target position
            owned_positions = [
                p.pos for p in chain(*board.positions) if p.fixture == self.player_id
            ]
            pos = min(
                owned_positions,
                key=lambda p: abs(p[0] - self.target_pos[0])
                + abs(p[1] - self.target_pos[1]),
            )
        road_name = None
        x_dist = self.target_pos[0] - pos[0]
        y_dist = self.target_pos[1] - pos[1]
        road_name = ""
        if abs(x_dist) > abs(y_dist):
            road_name = "down_road" if x_dist > 0 else "up_road"
            if road_name not in board.get_position(pos).get_available_roads():
                road_name = ""
        if not road_name:
            road_name = "right_road" if y_dist > 0 else "left_road"
        if road_name in board.get_position(pos).get_available_roads():
            logger.debug(
                f"Heuristic agent builds road {road_name} from position {pos} towards target {self.target_pos}"
            )
            return Action(action_id, pos=pos, road_name=road_name)
        if board.get_position(pos).get_available_roads():
            logger.debug(
                f"Heuristic agent builds random road from position {pos} towards target {self.target_pos}"
            )
            return Action(
                action_id,
                pos=pos,
                road_name=random.choice(board.get_position(pos).get_available_roads()),
            )
        return Action(Action.DO_NOTHING)

    def settle(self, board: Board, second: bool) -> list[Action]:
        (settle1,) = random.choices(
            list(self.pos_to_score(board).keys()),
            weights=list(self.pos_to_score(board).values()),
            k=1,
        )
        logger.debug(
            f"Heuristic agent settles on {settle1} with score {self.pos_to_score(board)[settle1]:.2f} from distribution {self.pos_to_score(board)}"
        )
        build_ideal_road_action = self.build_ideal_road(
            Action.BUILD_ROAD_INIT, board=board, pos=settle1
        )
        return [
            Action(Action.SETTLE_INIT, pos=settle1, second=second),
            build_ideal_road_action,
        ]

    def discard_cards(self, num_to_discard: int) -> list[int]:
        cards = self.get_resource_cards()
        return random.sample(range(len(cards)), num_to_discard)

    def choose_robber_action(self, board: Board) -> Action:
        robber_options = self.get_robber_options(board)
        return random.choice(robber_options)

    def accepts_trade(self, propose_trade_action: Action) -> bool:
        # TODO: counter-offers?
        return random.random() < 0.5

    def finalizes_trade(
        self, propose_trade_action: Action, players: list[int]
    ) -> Action:
        # choose a random player to trade with out of the ones that accepted the trade
        return Action(
            Action.TRADE,
            with_player=random.choice(players),
            mine=propose_trade_action.params["mine"],
            theirs=propose_trade_action.params["theirs"],
        )

    def do(
        self,
        board: Board,
        stats: GameStats,
    ) -> Action:
        legal_actions = self.get_legal_actions(board, stats)
        logger.debug(
            "Player {} has legal actions {}".format(self.player_id, legal_actions)
        )
        r = random.random()
        if (len(legal_actions) and r < 0.3) or (not len(legal_actions) and r < 0.7):
            # do nothing chance
            return Action(Action.DO_NOTHING)
        elif not self.empty() and (
            (len(legal_actions) and r < 0.5) or (not len(legal_actions))
        ):
            # propose trade chance
            cards = self.get_resource_cards()
            # limit number of cards to give in trade to 3 to avoid too much trading
            num_of_cards_to_give = min(random.randint(1, 3), len(cards))
            cards_to_give = random.sample(cards, num_of_cards_to_give)
            num_cards_wanted = random.randint(1, 3)
            cards_wanted = random.choices([0, 1, 2, 3, 4], k=num_cards_wanted)
            action = Action(
                Action.PROPOSE_TRADE,
                # with_player=other_player_id,
                mine=cards_to_give,
                theirs=cards_wanted,
            )
            return action
        elif len(legal_actions):
            # do something else
            return random.choice(legal_actions)
        else:
            return Action(Action.DO_NOTHING)
