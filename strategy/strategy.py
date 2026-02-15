import random
from typing import List

from basic_old import GameStats, DevCardPile
from basic import Action
from board import Board
import logger

from .player import Player


class RandomStrategy(Player):
    def settle(self, board: Board, second: bool):
        while True:
            pos = random.choice(random.choice(board.positions))
            if pos.can_settle():
                road_names = ["left_road", "right_road", "up_road", "down_road"]
                road_to_dir = {
                    "left_road": "left",
                    "right_road": "right",
                    "up_road": "up",
                    "down_road": "down",
                }
                road_names = [
                    road_name
                    for road_name in road_names
                    if getattr(pos, road_name) is None
                    and getattr(pos, road_to_dir[road_name]) is not None
                ]
                if len(road_names):
                    road_name = random.choice(road_names)
                    if second:
                        for tile in pos.adjacent_tiles:
                            if tile.tile < 5:
                                self.resources[
                                    tile.tile
                                ] += 1  # collect initial resources
                    return [
                        Action(Action.SETTLE_INIT, pos=pos.pos),
                        Action(
                            Action.BUILD_ROAD_INIT, pos=pos.pos, road_name=road_name
                        ),
                    ]

    def discard_cards(self, num_to_discard: int) -> List[int]:
        cards = self.get_resource_cards()
        return random.sample(range(len(cards)), num_to_discard)

    def choose_robber_action(self, board: Board) -> Action:
        robber_options = self.get_robber_options(board)
        return random.choice(robber_options)

    def accepts_trade(self, propose_trade_action: Action) -> bool:
        # TODO: counter-offers?
        return random.random() < 0.5

    def finalizes_trade(
        self, propose_trade_action: Action, players: List[int]
    ) -> Action:
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
        dev_cards: DevCardPile,
    ) -> Action:
        legal_actions = self.get_legal_actions(board, dev_cards)
        logger.debug(
            "Player {} has legal actions {}".format(self.player_id, legal_actions)
        )
        r = random.random()
        if (len(legal_actions) and r < 0.3) or (not len(legal_actions) and r < 0.7):
            # do nothing chance
            return Action(Action.DO_NOTHING)
        elif (len(legal_actions) and r < 0.5) or (not len(legal_actions)):
            # propose trade chance
            if not self.has_any_resource():
                return Action(Action.DO_NOTHING)
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
        else:
            # do something else
            return random.choice(legal_actions)
