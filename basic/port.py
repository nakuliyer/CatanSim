class Port:
    WHEAT = 0
    TREE = 1
    SHEEP = 2
    MUD = 3
    ROCK = 4
    THREE_ONE = 5

    @staticmethod
    def to_name(port: int) -> str:
        h = {0: "Wheat", 1: "Tree", 2: "Sheep", 3: "Mud", 4: "Rock", 5: "3:1"}
        return h[port]
