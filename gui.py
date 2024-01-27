from typing import List
from math import sin, cos, pi
import pygame

from board import Board
from player import Player

bg_color = (0, 0, 0)
w, h = 640, 360

left_corner = (50, 50)

resource_colors = {
    0: (255,255,153),
    1: (0, 255, 0),
    2: (34, 139, 34),
    3: (165, 42, 42),
    4: (100, 100, 100),
    5: (255, 255, 255)
}

player_colors = {
    1: (255, 255, 255),
    2: (255, 0, 0),
    3: (0, 0, 255)
}

root = None
big_text = None

def init_gui():
    global root, big_text
    pygame.init()
    pygame.font.init()
    big_text = pygame.font.SysFont('Helvetica', 16)
    root = pygame.display.set_mode((w, h))
    
def draw_regular_polygon(surface, color, vertex_count,
						 radius, position, width=0):
    n, r = vertex_count, radius
    x, y = position
    pygame.draw.polygon(surface, color, [
        (x + r * cos(2 * pi * i / n + pi / 2),
		 y + r * sin(2 * pi * i / n + pi / 2))
        for i in range(n)
    ])
    
def quit_gui():
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
            
def write(s: str, pos):
    text = big_text.render(s, True, (255, 255, 255))
    temp_surface = pygame.Surface(text.get_size())
    temp_surface.fill((0, 0, 0))
    temp_surface.blit(text, (0, 0))
    root.blit(temp_surface, pos)
    
def draw_gui(board: Board, players: List[Player]):
    root.fill(bg_color)
    for row in board.tiles:
        for tile in row:
            r, c = tile.pos
            pad_row = abs(r - 2) * 30
            draw_regular_polygon(root, resource_colors[tile.tile], 6,
                                30, (left_corner[0] + pad_row + c * 60, left_corner[1] + r * 60),
                                2)
            text = str(tile.value)
            if tile.has_knight:
                text += "/K"
            write(text, (left_corner[0] + pad_row + c * 60 - 10, left_corner[1] + r * 60 - 20))
    for row in board.positions:
        for pos in row:
            r, c = pos.pos
            pad_row = abs(r - 2) * 30
            dot_pos = (0, 0)
            if r < 3:
                even_pad = -15 if c % 2 else 0
                dot_pos = (left_corner[0] + pad_row + c * 30 - 30, left_corner[1] + r * 60 - 22.5 + even_pad)
            else:
                even_pad = -15 if c % 2 == 0 else 0
                dot_pos = (left_corner[0] + pad_row + c * 30 - 60, left_corner[1] + r * 60 - 22.5 + even_pad)
            if pos.fixture != None:
                rad = 4 if pos.fixture_type == 0 else 7
                pygame.draw.circle(root, player_colors[pos.fixture], dot_pos, rad)
            else:
                pygame.draw.circle(root, (50, 50, 50), dot_pos, 3)
            if pos.right_road != None:
                d = 1 if c % 2 else -1
                d = d if r < 3 else -d
                pygame.draw.line(root, player_colors[pos.right_road], dot_pos, (dot_pos[0] + 30, dot_pos[1] + 18 * d), 3)
            if pos.down_road != None:
                pygame.draw.line(root, player_colors[pos.down_road], dot_pos, (dot_pos[0], dot_pos[1] + 40), 3)
            # text = str(tile.value)
            # if tile.has_knight:
            #     text += "/K"
            # write(text, (left_corner[0] + pad_row + c * 60 - 10, left_corner[1] + r * 60 - 20))
    pygame.display.flip()