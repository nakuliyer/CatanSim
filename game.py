import random
import time

from basic_old import DevCardPile, GameStats
from basic import Action
from board import RandomBoard
from strategy import Player, RandomStrategy
from gui import init_gui, draw_gui, quit_gui
import logger


class Game:
    def __init__(self, players: list[Player]):
        pass


def play(gui: bool, force_quit_after_round: int) -> None:
    if gui:
        init_gui()

    board = RandomBoard()
    logger.game("Board is\n{}".format(board))
    cards = DevCardPile()
    stats = GameStats()
    players: list[Player] = [
        RandomStrategy(0),
        RandomStrategy(1),
        RandomStrategy(2),
    ]
    for second in [False, True]:
        order = -1 if second else 1
        for player in players[::order]:
            for action in player.settle(board, second):
                player.submit_action(action, board, players, stats, cards)
    for player in players:
        logger.debug(player)

    rnd = 0
    turn = 0
    gg = False
    while not gg:
        if gui:
            quit_gui()
        d6 = random.randint(1, 6) + random.randint(1, 6)
        logger.game("{} rolled".format(d6))
        for player in players:
            player.handle_dice_roll(board, d6)
        if d6 == 7:
            players[turn].submit_action(
                players[turn].choose_robber_action(board), board, players, stats, cards
            )
        action = players[turn].do(board, players, stats, cards)
        while action.action != Action.DO_NOTHING:
            if action.action == Action.PROPOSE_TRADE:
                logger.game(
                    "Player {} proposes trade {}".format(
                        players[turn].player_id, action
                    )
                )
                logger.debug(
                    "Player {} has cards {}".format(
                        players[turn].player_id, players[turn].get_resource_cards()
                    )
                )
                accepting_players: list[int] = []
                for other_player in players:
                    if other_player.player_id == players[turn].player_id:
                        continue
                    if other_player.can_accept_trade(
                        action
                    ) and other_player.accepts_trade(action):
                        logger.game(
                            "Player {} accepts the trade".format(other_player.player_id)
                        )
                        accepting_players.append(other_player.player_id)
                if not accepting_players:
                    logger.game("No players accepted the trade")
                else:
                    action = players[turn].finalizes_trade(action, accepting_players)
                    logger.debug(
                        "Other player chosen for trade {} with cards {}".format(
                            action.params["with_player"],
                            players[action.params["with_player"]].get_resource_cards(),
                        )
                    )
                    players[turn].submit_action(action, board, players, stats, cards)
            else:
                players[turn].submit_action(action, board, players, stats, cards)
            action = players[turn].do(board, players, stats, cards)
        vps = players[turn].vps(board, stats)
        if vps >= 10:
            logger.game("Player {} won!".format(players[turn].player_id))
            gg = True
        if gui:
            draw_gui(board)
            time.sleep(0.01)
        turn = (turn + 1) % len(players)
        if turn == 0:
            rnd += 1
        if rnd >= force_quit_after_round:
            raise ValueError("Game Lasted Too Long")
        for player in players:
            player.check_all_ok()
            player.turn_ended()
        for player in players:
            logger.debug(player)
        logger.print_all()
        logger.flush()
    if gui:
        while True:
            quit_gui()
            draw_gui(board)


def play_cli(force_quit_after_round: int) -> None:
    try:
        play(gui=False, force_quit_after_round=force_quit_after_round)
    except:
        logger.print_all()
        raise


def play_gui(force_quit_after_round: int) -> None:
    play(gui=True, force_quit_after_round=force_quit_after_round)
