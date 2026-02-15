from math import cos, pi, sin
from typing import List, Optional, Tuple

import pygame

from board import Board
from player import Player

BG_COLOR = (0, 0, 0)
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 360

LEFT_CORNER = (50, 50)

RESOURCE_COLORS = {
    0: (255, 255, 153),
    1: (0, 255, 0),
    2: (34, 139, 34),
    3: (165, 42, 42),
    4: (100, 100, 100),
    5: (255, 255, 255),
}

PLAYER_COLORS = {1: (255, 255, 255), 2: (255, 0, 0), 3: (0, 0, 255)}

root: Optional[pygame.Surface] = None
big_text: Optional[pygame.font.Font] = None


def init_gui() -> None:
    global root, big_text
    pygame.init()
    pygame.font.init()
    big_text = pygame.font.SysFont("Helvetica", 16)
    root = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def draw_regular_polygon(
    surface: pygame.Surface,
    color,
    vertex_count: int,
    radius: float,
    position: Tuple[float, float],
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


def write(s: str, pos: Tuple[int, int]) -> None:
    if not root or not big_text:
        return
    text = big_text.render(s, True, (255, 255, 255))
    temp_surface = pygame.Surface(text.get_size())
    temp_surface.fill((0, 0, 0))
    temp_surface.blit(text, (0, 0))
    root.blit(temp_surface, pos)


def draw_gui(board: Board, players: List[Player]) -> None:
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
            # text = str(tile.value)
            # if tile.has_knight:
            #     text += "/K"
            # write(text, (left_corner[0] + pad_row + c * 60 - 10, left_corner[1] + r * 60 - 20))
    pygame.display.flip()
