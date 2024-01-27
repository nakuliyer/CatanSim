from board import *
from strategy import *
from cards import *
# from strategies_old import *

import random

def play():
    board = Board()
    print(board)
    cards = DevCardPile()
    stats = GameStats()
    players = [RandomStrategy(1), RandomStrategy(2), RandomStrategy(3)]
    for second in [False, True]:
        order = -1 if second else 1
        for player in players[::order]:
            for action in player.settle(board, second):
                player.submit_action(action, board, players, stats, cards)
    if VERBOSE:
        for player in players:
            player.print_resources()
    i = 0 # TODO: limit simulation
    turn = 0
    while True:
        d6 = random.randint(1, 6) + random.randint(1, 6)
        if VERBOSE:
            print("{} rolled".format(d6))
        for player in players:
            player.collect_resources(board, d6)
        action = players[turn].do(board)
        while action.action != Action.DO_NOTHING:
            players[turn].submit_action(action, board, players, stats, cards)
            if action.action == Action.USE_DEV_ROADS:
                players[turn].submit_action(players[turn].place_second_dev_roads(board), board, players, stats, cards)
            action = players[turn].do(board)
        vps = players[turn].vps(board, stats)
        if vps > 10:
            print("Player {} won!".format(players[turn].player_id))
            break
        turn = (turn + 1) % len(players)
        i += 1
        if i == 10000:
            return
    # strategy.do(board)
    # strategy.where_to_settle(board)

play()