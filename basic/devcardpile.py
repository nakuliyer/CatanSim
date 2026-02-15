from itertools import chain
import random

from .devcard import DevCard


class DevCardPile:
    def __init__(self):
        self.pile: list[int] = list(
            chain(
                [DevCard.KNIGHT] * 14,
                [DevCard.VP] * 5,
                [DevCard.ROADS] * 2,
                [DevCard.PLENTY] * 2,
                [DevCard.MONOPOLY] * 2,
            )
        )
        random.shuffle(self.pile)

    def has_cards(self) -> bool:
        return len(self.pile) > 0

    def draw_top(self) -> int:
        if len(self.pile):
            return self.pile.pop(0)
        raise ValueError("No more dev cards left in pile")
