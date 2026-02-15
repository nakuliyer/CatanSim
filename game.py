import random
import time

from basic import DevCardPile, GameStats, Action
from board import Board
from strategy import RandomStrategy
from player import Player
from gui import init_gui, draw_gui, quit_gui
import logger


def play(gui: bool, force_quit_after_round: int) -> None:
    if gui:
        init_gui()

    board = Board()
    logger.info("Board is\n{}".format(board))
    cards = DevCardPile()
    stats = GameStats()
    players = [
        RandomStrategy(1),
        RandomStrategy(2),
        RandomStrategy(3),
    ]
    for second in [False, True]:
        order = -1 if second else 1
        for player in players[::order]:
            for action in player.settle(board, second):
                player.submit_action(action, board, players, stats, cards)
    logger.info("\n".join([str(player) for player in players]))
    rnd = 0
    turn = 0
    gg = False
    while not gg:
        if gui:
            quit_gui()
        d6 = random.randint(1, 6) + random.randint(1, 6)
        logger.info("{} rolled".format(d6))
        for player in players:
            player.handle_dice_roll(board, d6)
        if d6 == 7:
            players[turn].submit_action(
                players[turn].choose_robber_action(board), board, players, stats, cards
            )
        action = players[turn].do(board, players, stats, cards)
        while action.action != Action.DO_NOTHING:
            if action.action == Action.PROPOSE_TRADE:
                logger.info(
                    "Player {} proposes trade {}".format(
                        players[turn].player_id, action
                    )
                )
                if Player.get_player_by_id(players, action.with_player).accepts_trade(
                    action
                ):
                    logger.info("Trade Accepted")
                    action.action = Action.TRADE
                    players[turn].submit_action(action, board, players, stats, cards)
                else:
                    logger.info("Trade Denied")
            else:
                players[turn].submit_action(action, board, players, stats, cards)
            if action.action == Action.USE_DEV_ROADS:
                players[turn].submit_action(
                    players[turn].place_second_dev_roads(board),
                    board,
                    players,
                    stats,
                    cards,
                )
            action = players[turn].do(board, players, stats, cards)
        vps = players[turn].vps(board, stats)
        if vps >= 10:
            logger.info("Player {} won!".format(players[turn].player_id))
            gg = True
        if gui:
            draw_gui(board, players)
            time.sleep(0.01)
        turn = (turn + 1) % len(players)
        if turn == 0:
            rnd += 1
        if rnd >= force_quit_after_round:
            raise ValueError("Game Lasted Too Long")
        for player in players:
            player.check_all_ok()
            player.turn_ended()
        logger.info("\n".join([str(player) for player in players]))
        print(logger.flush())
    if gui:
        while True:
            quit_gui()
            draw_gui(board, players)


def play_cli(force_quit_after_round: int) -> None:
    play(gui=False, force_quit_after_round=force_quit_after_round)


def play_gui(force_quit_after_round: int) -> None:
    play(gui=True, force_quit_after_round=force_quit_after_round)
