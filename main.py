import pygame
import random
import math

pygame.init()

FPS = 60
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 4, 4
RECT_WIDTH = WIDTH // COLS
RECT_HEIGHT = HEIGHT // ROWS

OUTLINE_COLOR = (187, 173, 160)
OUTLINE_THICKNESS = 8
BACKGROUND_COLOR = (205, 192, 180)
FONT_COLOR = (119, 110, 101)

WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2048")

FONT = pygame.font.SysFont("comicsans", 60, bold=True)
ANIMATION_SPEED = 30  # pixels per frame for sliding
MERGE_ANIM_DURATION = 8  # frames merge 'pop' animation lasts

class Tile:
    COLORS = [
        (237, 229, 218),  # 2
        (238, 225, 201),  # 4
        (243, 178, 122),  # 8
        (246, 150, 101),  # 16
        (247, 124, 95),   # 32
        (247, 95, 59),    # 64
        (237, 208, 115),  # 128
        (237, 204, 99),   # 256
        (236, 202, 80),   # 512+
    ]

    def __init__(self, value, row, col):
        self.value = value
        self.row = row
        self.col = col
        # Current pixel position for smooth animation
        self.x = col * RECT_WIDTH
        self.y = row * RECT_HEIGHT
        # Target pixel position after a move
        self.target_x = self.x
        self.target_y = self.y
        # Flags related to merge and animation
        self.merged = False  # Prevent multiple merges in one move
        self.to_remove = False  # Mark tile removal after merge
        self.merge_anim_counter = 0  # Countdown frames for merge animation

    def get_color(self):
        index = int(math.log2(self.value)) - 1
        if index >= len(self.COLORS):
            index = len(self.COLORS) - 1
        return self.COLORS[index]

    def update_position(self):
        moved = False
        # Move X
        if abs(self.x - self.target_x) > ANIMATION_SPEED:
            self.x += ANIMATION_SPEED if self.target_x > self.x else -ANIMATION_SPEED
            moved = True
        else:
            self.x = self.target_x
        # Move Y
        if abs(self.y - self.target_y) > ANIMATION_SPEED:
            self.y += ANIMATION_SPEED if self.target_y > self.y else -ANIMATION_SPEED
            moved = True
        else:
            self.y = self.target_y

        # Update logical grid position only after animation ends
        if not moved and self.merge_anim_counter == 0:
            self.row = int(self.target_y // RECT_HEIGHT)
            self.col = int(self.target_x // RECT_WIDTH)
        return moved

    def start_merge_animation(self):
        self.merge_anim_counter = MERGE_ANIM_DURATION

    def draw(self, window):
        # If merging animate scale 'pop'
        scale = 1.0
        if self.merge_anim_counter > 0:
            # Simple scale animation: scale goes from 1.3 down to 1.0
            progress = self.merge_anim_counter / MERGE_ANIM_DURATION
            scale = 1.0 + 0.3 * progress

        current_width = RECT_WIDTH * scale
        current_height = RECT_HEIGHT * scale
        # Center the tile rect accordingly for scale growth from center
        x = self.x + (RECT_WIDTH - current_width) / 2
        y = self.y + (RECT_HEIGHT - current_height) / 2

        pygame.draw.rect(window, self.get_color(), (x, y, current_width, current_height), border_radius=8)
        text = FONT.render(str(self.value), True, FONT_COLOR)
        window.blit(text, (
            x + (current_width - text.get_width()) / 2,
            y + (current_height - text.get_height()) / 2
        ))

        if self.merge_anim_counter > 0:
            self.merge_anim_counter -= 1

def draw_grid(window):
    window.fill(BACKGROUND_COLOR)
    for row in range(ROWS + 1):
        pygame.draw.line(window, OUTLINE_COLOR, (0, row * RECT_HEIGHT), (WIDTH, row * RECT_HEIGHT), OUTLINE_THICKNESS)
    for col in range(COLS + 1):
        pygame.draw.line(window, OUTLINE_COLOR, (col * RECT_WIDTH, 0), (col * RECT_WIDTH, HEIGHT), OUTLINE_THICKNESS)

def draw(window, tiles):
    draw_grid(window)
    for tile in tiles:
        tile.draw(window)
    pygame.display.update()

def spawn_tile(tiles):
    occupied = {(t.row, t.col) for t in tiles}
    available = [(r, c) for r in range(ROWS) for c in range(COLS) if (r, c) not in occupied]
    if not available:
        return False
    row, col = random.choice(available)
    new_value = 4 if random.random() < 0.1 else 2  # 10% chance for 4
    tiles.append(Tile(new_value, row, col))
    return True

def can_move(tiles):
    if len(tiles) < ROWS * COLS:
        return True
    grid = [[0]*COLS for _ in range(ROWS)]
    for t in tiles:
        grid[t.row][t.col] = t.value
    for r in range(ROWS):
        for c in range(COLS):
            if c + 1 < COLS and grid[r][c] == grid[r][c+1]:
                return True
            if r + 1 < ROWS and grid[r][c] == grid[r+1][c]:
                return True
    return False

def reset_merged_flags(tiles):
    for tile in tiles:
        tile.merged = False
        tile.to_remove = False

def move(tiles, direction):
    reset_merged_flags(tiles)
    moved = False

    # Build grid map of tiles
    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    for t in tiles:
        grid[t.row][t.col] = t

    def traverse():
        if direction == "left":
            return [(r, c) for r in range(ROWS) for c in range(COLS)]
        elif direction == "right":
            return [(r, c) for r in range(ROWS) for c in reversed(range(COLS))]
        elif direction == "up":
            return [(r, c) for c in range(COLS) for r in range(ROWS)]
        elif direction == "down":
            return [(r, c) for c in range(COLS) for r in reversed(range(ROWS))]

    def next_pos(r, c):
        if direction == "left":
            return r, c - 1
        elif direction == "right":
            return r, c + 1
        elif direction == "up":
            return r - 1, c
        elif direction == "down":
            return r + 1, c

    def within(r, c):
        return 0 <= r < ROWS and 0 <= c < COLS

    for r, c in traverse():
        tile = grid[r][c]
        if tile is None:
            continue
        current_r, current_c = r, c
        while True:
            nr, nc = next_pos(current_r, current_c)
            if not within(nr, nc):
                break
            next_tile = grid[nr][nc]
            if next_tile is None:
                # Move tile forward into empty
                grid[nr][nc] = tile
                grid[current_r][current_c] = None
                current_r, current_c = nr, nc
                moved = True
            elif next_tile.value == tile.value and not tile.merged and not next_tile.merged:
                # Merge tile into next tile
                next_tile.value *= 2
                next_tile.merged = True
                next_tile.start_merge_animation()  # trigger merge animation
                tile.to_remove = True
                grid[current_r][current_c] = None
                moved = True
                break
            else:
                # Blocked by different tile
                break

        tile.target_x = current_c * RECT_WIDTH
        tile.target_y = current_r * RECT_HEIGHT

    # Remove merged tiles
    tiles[:] = [t for t in tiles if not t.to_remove]

    return moved

def main():
    clock = pygame.time.Clock()
    tiles = []
    # Spawn two initial tiles
    spawn_tile(tiles)
    spawn_tile(tiles)

    running = True
    animating = False
    merge_animation_running = False

    while running:
        clock.tick(FPS)

        if not animating and not merge_animation_running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    direction = None
                    if event.key == pygame.K_LEFT:
                        direction = "left"
                    elif event.key == pygame.K_RIGHT:
                        direction = "right"
                    elif event.key == pygame.K_UP:
                        direction = "up"
                    elif event.key == pygame.K_DOWN:
                        direction = "down"

                    if direction:
                        moved = move(tiles, direction)
                        if moved:
                            animating = True
        else:
            # Animate sliding
            any_moving = False
            for tile in tiles:
                if tile.update_position():
                    any_moving = True

            if not any_moving:
                if not merge_animation_running:
                    # Check if any tile is still merging (merge_anim_counter > 0)
                    merging_tiles = [t for t in tiles if t.merge_anim_counter > 0]
                    if merging_tiles:
                        merge_animation_running = True

                if merge_animation_running:
                    # Progress all merge animations one frame
                    for t in tiles:
                        if t.merge_anim_counter > 0:
                            t.merge_anim_counter -= 1
                    # If all merge animations finished
                    if all(t.merge_anim_counter == 0 for t in tiles):
                        merge_animation_running = False
                        animating = False
                        # After merges finished, update grid positions & spawn
                        for tile in tiles:
                            tile.row = int(tile.target_y // RECT_HEIGHT)
                            tile.col = int(tile.target_x // RECT_WIDTH)
                        spawn_tile(tiles)
                        # Check game over
                        if not can_move(tiles):
                            print("Game Over! No moves left.")
                            running = False
                else:
                    # No merge animation, finish animation phase
                    animating = False
                    for tile in tiles:
                        tile.row = int(tile.target_y // RECT_HEIGHT)
                        tile.col = int(tile.target_x // RECT_WIDTH)
                    spawn_tile(tiles)
                    if not can_move(tiles):
                        print("Game Over! No moves left.")
                        running = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

        draw(WINDOW, tiles)

    pygame.quit()

if __name__ == "__main__":
    main()
