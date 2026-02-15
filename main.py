import argparse
import logger

from game import play_cli, play_gui

DEFAULT_VERBOSITY = 3
DEFAULT_FORCE_QUIT_AFTER_ROUND = 1000

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CatanSim")
    parser.add_argument("--verbosity", type=int, default=DEFAULT_VERBOSITY)
    parser.add_argument("--no-gui", action="store_false", default=True, dest="gui")
    parser.add_argument(
        "--force-quit-after-round", type=int, default=DEFAULT_FORCE_QUIT_AFTER_ROUND
    )
    args = parser.parse_args()

    logger.set_verbosity(args.verbosity)
    if args.gui:
        play_gui(args.force_quit_after_round)
    else:
        play_cli(args.force_quit_after_round)
