class DevCard:
    KNIGHT = 0
    VP = 1
    ROADS = 2
    PLENTY = 3
    MONOPOLY = 4

    @staticmethod
    def to_name(card: int) -> str:
        h = {
            0: "Knight",
            1: "VP",
            2: "Road Building",
            3: "Year of Plenty",
            4: "Monopoly",
        }
        return h[card]

    @staticmethod
    def to_names(list_of_cards: list[int]) -> str:
        return "[{}]".format(
            ", ".join(map(DevCard.to_name, filter(lambda x: x != 5, list_of_cards)))
        )
