import random
import time

from basic_old import DevCardPile, GameStats
from basic import Action
from board import Board, RandomBoard, board
from strategy import Player, RandomStrategy
from gui import init_gui, draw_gui, quit_gui
import logger


class Game:
    def __init__(
        self,
        gui: bool,
        force_quit_after_round: int,
        players: list[Player],
        board: Board,
    ) -> None:
        self.gui = gui
        self.force_quit_after_round = force_quit_after_round
        self.players = players
        self.board = board

        logger.game("Board is\n{}".format(board))

        self.cards = DevCardPile()
        self.stats = GameStats()

    def init_game(self) -> None:
        if self.gui:
            init_gui()

        logger.game("Initializing settlements and roads")
        for second in [False, True]:
            order = -1 if second else 1
            for player in self.players[::order]:
                for action in player.settle(self.board, second):
                    player.submit_action(
                        action, self.board, self.players, self.stats, self.cards
                    )
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
            self.players[turn].submit_action(
                self.players[turn].choose_robber_action(self.board),
                self.board,
                self.players,
                self.stats,
                self.cards,
            )
        action = self.players[turn].do(self.board, self.stats, self.cards)
        while action.action != Action.DO_NOTHING:
            if action.action == Action.PROPOSE_TRADE:
                logger.game(
                    "Player {} proposes trade {}".format(
                        self.players[turn].color, action
                    )
                )
                logger.debug(
                    "Player {} has cards {}".format(
                        self.players[turn].color,
                        self.players[turn].get_resource_cards(),
                    )
                )
                accepting_players: list[int] = []
                for other_player in self.players:
                    if other_player.player_id == self.players[turn].player_id:
                        continue
                    if other_player.can_accept_trade(
                        action
                    ) and other_player.accepts_trade(action):
                        logger.game(
                            "Player {} accepts the trade".format(other_player.color)
                        )
                        accepting_players.append(other_player.player_id)
                if not accepting_players:
                    logger.game("No players accepted the trade")
                else:
                    action = self.players[turn].finalizes_trade(
                        action, accepting_players
                    )
                    logger.debug(
                        "Other player chosen for trade {} with cards {}".format(
                            self.players[action.params["with_player"]].color,
                            self.players[
                                action.params["with_player"]
                            ].get_resource_cards(),
                        )
                    )
                    self.players[turn].submit_action(
                        action, self.board, self.players, self.stats, self.cards
                    )
            else:
                self.players[turn].submit_action(
                    action, self.board, self.players, self.stats, self.cards
                )
            action = self.players[turn].do(self.board, self.stats, self.cards)
        vps = self.players[turn].vps(self.board, self.stats)
        if vps >= 10:
            logger.game("Player {} won!".format(self.players[turn].color))
            return False
        if self.gui:
            draw_gui(self.board)
            time.sleep(0.01)
        for player in self.players:
            player.check_all_ok()
            player.turn_ended()
        for player in self.players:
            logger.debug(player)
        logger.print_all()
        logger.flush()
        return True

    def post_game(self) -> None:
        if self.gui:
            while True:
                # Wait for user to close the window
                quit_gui()
                draw_gui(self.board)

    def play(self) -> None:
        try:
            self.init_game()
            rnd = 0
            turn = 0
            while self.game_loop(turn):
                turn = (turn + 1) % len(self.players)
                if turn == 0:
                    rnd += 1
                if rnd >= self.force_quit_after_round:
                    raise ValueError("Game Lasted Too Long")
            self.post_game()
        except:
            logger.game("Game crashed")
            for player in self.players:
                logger.game(player)
            logger.print_all()
            raise


def play(gui: bool, force_quit_after_round: int) -> None:
    board = RandomBoard()
    players: list[Player] = [
        RandomStrategy(),
        RandomStrategy(),
        RandomStrategy(),
    ]
    Game(gui, force_quit_after_round, players, board).play()


def play_cli(force_quit_after_round: int) -> None:
    try:
        play(gui=False, force_quit_after_round=force_quit_after_round)
    except:
        logger.print_all()
        raise


def play_gui(force_quit_after_round: int) -> None:
    play(gui=True, force_quit_after_round=force_quit_after_round)
