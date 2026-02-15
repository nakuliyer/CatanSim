class Action:
    DO_NOTHING = 0
    SETTLE = 1
    BUILD_CITY = 2
    FOUR_TO_ONE = 3
    THREE_TO_ONE = 4
    BUILD_ROAD = 5
    USE_KNIGHT = 6
    USE_MONOPOLY = 7
    USE_DEV_ROADS = 8
    USE_YEAR_OF_PLENTY = 9
    TWO_TO_ONE = 10
    ROB = 11
    PROPOSE_TRADE = 12
    TRADE = 13
    GET_DEV_CARD = 14
    SETTLE_INIT = 15
    BUILD_ROAD_INIT = 16

    def __init__(self, action: int, **params):
        self.action = action
        self.params = params

    def get_name(self) -> str:
        h = {
            0: "Do nothing",
            1: "Settle",
            2: "Build city",
            3: "4-to-1",
            4: "3-to-1",
            5: "Build road",
            6: "Use knight",
            7: "Use monopoly",
            8: "Use dev roads",
            9: "Use year of plenty",
            10: "2-to-1",
            11: "Rob",
            12: "Propose trade",
            13: "Trade",
            14: "Get dev card",
            15: "Settle init",
            16: "Build road init",
        }
        return h[self.action]

    def __repr__(self):
        return f"Action[{self.get_name()}, {self.params}]"
