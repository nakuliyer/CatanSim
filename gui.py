from math import cos, pi, sin

import pygame

from board import Board

BG_COLOR = (0, 0, 0)
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 360

LEFT_CORNER = (50, 50)

RESOURCE_COLORS = {
    # wheat
    0: (255, 255, 35),
    # tree
    1: (34, 139, 34),
    # sheep
    2: (0, 255, 0),
    # mud
    3: (165, 42, 42),
    # rock
    4: (100, 100, 100),
    # desert
    5: (255, 255, 255),
}

PLAYER_COLORS = {
    # red
    0: (255, 0, 0),
    # blue
    1: (0, 0, 255),
    # orange
    2: (255, 165, 0),
    # white
    3: (255, 255, 255),
    # green
    4: (0, 255, 0),
    # black
    5: (0, 0, 0),
}

root: pygame.Surface | None = None
big_text: pygame.font.Font | None = None
msg_text: pygame.font.Font | None = None


def init_gui() -> None:
    global root, big_text, msg_text
    pygame.init()
    pygame.font.init()
    big_text = pygame.font.SysFont("Helvetica", 16)
    msg_text = pygame.font.SysFont("Helvetica", 8)
    root = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def draw_regular_polygon(
    surface: pygame.Surface,
    color,
    vertex_count: int,
    radius: float,
    position: tuple[float, float],
    width: int = 0,
) -> None:
    n, r = vertex_count, radius
    x, y = position
    pygame.draw.polygon(
        surface,
        color,
        [
            (x + r * cos(2 * pi * i / n + pi / 2), y + r * sin(2 * pi * i / n + pi / 2))
            for i in range(n)
        ],
        width,
    )


def quit_gui() -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit


def write(s: str, pos: tuple[int, int]) -> None:
    if not root or not big_text:
        return
    text = big_text.render(s, True, (255, 255, 255))
    temp_surface = pygame.Surface(text.get_size())
    temp_surface.fill((0, 0, 0))
    temp_surface.blit(text, (0, 0))
    root.blit(temp_surface, pos)


# Store log messages globally
log_messages: list[str] = []


def add_messages(messages: list[str]) -> None:
    global log_messages
    log_messages.extend(messages)


def draw_messages() -> None:
    if not root or not msg_text:
        return
    x = SCREEN_WIDTH - 300
    y = 10
    width = 290
    height = SCREEN_HEIGHT - 20
    # Draw background for log area
    pygame.draw.rect(root, (30, 30, 30), (x, y, width, height))
    # Draw border
    pygame.draw.rect(root, (80, 80, 80), (x, y, width, height), 2)
    # Draw each log message
    chunked = []
    for msg in log_messages:
        i = 0
        while len(msg):
            if i > 0:
                chunked.append("    " + msg[:70])
                msg = msg[70:]
            else:
                chunked.append(msg[:74])
                msg = msg[74:]
            i += 1
    chunked = chunked[-27:]
    for i, msg in enumerate(chunked):
        text = msg_text.render(msg, True, (255, 255, 255))
        root.blit(text, (x + 10, y + 10 + i * 12))


def draw_gui(board: Board) -> None:
    if not root:
        return
    root.fill(BG_COLOR)
    for row in board.tiles:
        for tile in row:
            r, c = tile.pos
            pad_row = abs(r - 2) * 30
            draw_regular_polygon(
                root,
                RESOURCE_COLORS[tile.tile],
                6,
                30,
                (LEFT_CORNER[0] + pad_row + c * 60, LEFT_CORNER[1] + r * 60),
                2,
            )
            text = str(tile.value)
            if tile.has_knight:
                text += "/K"
            write(
                text,
                (LEFT_CORNER[0] + pad_row + c * 60 - 10, LEFT_CORNER[1] + r * 60 - 20),
            )
    for row in board.positions:
        for pos in row:
            r, c = pos.pos
            pad_row = abs(r - 2) * 30
            dot_pos = (0, 0)
            if r < 3:
                even_pad = -15 if c % 2 else 0
                dot_pos = (
                    LEFT_CORNER[0] + pad_row + c * 30 - 30,
                    LEFT_CORNER[1] + r * 60 - 22.5 + even_pad,
                )
            else:
                even_pad = -15 if c % 2 == 0 else 0
                dot_pos = (
                    LEFT_CORNER[0] + pad_row + c * 30 - 60,
                    LEFT_CORNER[1] + r * 60 - 22.5 + even_pad,
                )
            if pos.fixture is not None:
                rad = 4 if pos.fixture_type == 0 else 7
                pygame.draw.circle(root, PLAYER_COLORS[pos.fixture], dot_pos, rad)
            else:
                pygame.draw.circle(root, (50, 50, 50), dot_pos, 3)
            if pos.right_road is not None:
                d = 1 if c % 2 else -1
                d = d if r < 3 else -d
                pygame.draw.line(
                    root,
                    PLAYER_COLORS[pos.right_road],
                    dot_pos,
                    (dot_pos[0] + 30, dot_pos[1] + 18 * d),
                    3,
                )
            if pos.down_road is not None:
                pygame.draw.line(
                    root,
                    PLAYER_COLORS[pos.down_road],
                    dot_pos,
                    (dot_pos[0], dot_pos[1] + 40),
                    3,
                )
            if pos.adjacent_port is not None:
                port_color = (
                    RESOURCE_COLORS[pos.adjacent_port]
                    if pos.adjacent_port != 5
                    else (255, 0, 255)
                )
                pygame.draw.circle(root, port_color, dot_pos, 10, 2)
    draw_messages()
    pygame.display.flip()
