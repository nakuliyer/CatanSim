import argparse
import random
import time

from basic import DevCardPile, GameStats, Action, Messages
from board import Board
from strategy import RandomStrategy
from player import Player
from gui import init_gui, draw_gui, quit_gui

DEFAULT_VERBOSITY = 3
DEFAULT_GUI = 1
DEFAULT_FORCE_QUIT_AFTER_ROUND = 1000

def play(verbosity: int, gui: bool, force_quit_after_round: int) -> None:
    if gui:
        init_gui()
    
    messages = Messages(verbosity)
    board = Board()
    messages.add("Board is\n{}".format(board), 3)
    cards = DevCardPile()
    stats = GameStats()
    players = [
        RandomStrategy(1, messages), 
        RandomStrategy(2, messages), 
        RandomStrategy(3, messages)
    ]
    for second in [False, True]:
        order = -1 if second else 1
        for player in players[::order]:
            for action in player.settle(board, second):
                player.submit_action(action, board, players, stats, cards)
    messages.add("\n".join([str(player) for player in players]), 3)
    messages.print_all()
    rnd = 0
    turn = 0
    gg = False
    while not gg:
        if gui:
            quit_gui()
        d6 = random.randint(1, 6) + random.randint(1, 6)
        messages.add("{} rolled".format(d6), 1)
        for player in players:
            player.handle_dice_roll(board, d6)
        if d6 == 7:
            players[turn].submit_action(
                players[turn].choose_robber_action(board),
                board,
                players,
                stats,
                cards
            )
        action = players[turn].do(board, players, stats, cards)
        while action.action != Action.DO_NOTHING:
            if action.action == Action.PROPOSE_TRADE:
                messages.add(
                    "Player {} proposes trade {}".format(players[turn].player_id, action),
                    1,
                )
                if Player.get_player_by_id(players, action.with_player).accepts_trade(action):
                    messages.add("Trade Accepted", 1)
                    action.action = Action.TRADE
                    players[turn].submit_action(action, board, players, stats, cards)
                else:
                    messages.add("Trade Denied", 1)
            else:
                players[turn].submit_action(action, board, players, stats, cards)
            if action.action == Action.USE_DEV_ROADS:
                players[turn].submit_action(players[turn].place_second_dev_roads(board), board, players, stats, cards)
            action = players[turn].do(board, players, stats, cards)
        vps = players[turn].vps(board, stats)
        if vps >= 10:
            messages.add("Player {} won!".format(players[turn].player_id), 0)
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
        messages.add("\n".join([str(player) for player in players]), 3)
        messages.print_all()
    if gui:
        while True:
            quit_gui()
            draw_gui(board, players)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CatanSim")
    parser.add_argument("--verbosity", type=int, default=DEFAULT_VERBOSITY)
    parser.add_argument("--gui", action="store_true", default=DEFAULT_GUI)
    parser.add_argument("--force-quit-after-round", type=int, default=DEFAULT_FORCE_QUIT_AFTER_ROUND)
    args = parser.parse_args()
    play(args.verbosity, args.gui, args.force_quit_after_round)