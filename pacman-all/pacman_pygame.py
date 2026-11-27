import json
import random
from pathlib import Path

import pygame


class PacmanGame:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.assets_dir = self.base_dir / "assets"
        self.level_path = self.base_dir / "levels" / "level1.json"

        self.level = self.load_level()
        self.matrix = self.level["matrix"]
        self.rows = self.level["num_rows"]
        self.cols = self.level["num_cols"]
        self.tile_size = self.level.get("cell_width", 20)
        self.hud_height = 72

        self.width = self.cols * self.tile_size
        self.height = self.rows * self.tile_size + self.hud_height

        pygame.init()
        pygame.display.set_caption("Pacman - Pygame")
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 24)
        self.small_font = pygame.font.SysFont("consolas", 18)

        self.walls = set()
        self.elec_gates = set()
        self.dots = set()
        self.power_dots = set()
        self.ghost_den = tuple(self.level["ghost_den"])
        self.pacman_start = tuple(self.level["pacman_start"])
        self.power_duration_ms = int(self.level.get("power_up_time", 6000))

        self.parse_grid()
        self.load_assets()
        self.load_sounds()
        self.reset_round(full_reset=True)

    def load_level(self):
        with self.level_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def parse_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.matrix[r][c]
                if cell == "wall":
                    self.walls.add((r, c))
                elif cell == "elec":
                    self.elec_gates.add((r, c))
                elif cell == "dot":
                    self.dots.add((r, c))
                elif cell == "power":
                    self.power_dots.add((r, c))

    def load_image(self, relative_path, size, alpha=True):
        path = self.base_dir / relative_path
        try:
            image = pygame.image.load(path.as_posix())
            image = image.convert_alpha() if alpha else image.convert()
            return pygame.transform.smoothscale(image, size)
        except pygame.error:
            # Fallback surface keeps the game playable even if one asset is missing.
            surf = pygame.Surface(size, pygame.SRCALPHA)
            surf.fill((255, 0, 255, 200))
            return surf

    def load_assets(self):
        psize = int(self.tile_size * 1.6)
        self.pacman_frames = {
            "left": [
                self.load_image("assets/pacman-left/1.png", (psize, psize)),
                self.load_image("assets/pacman-left/2.png", (psize, psize)),
                self.load_image("assets/pacman-left/3.png", (psize, psize)),
            ],
            "right": [
                self.load_image("assets/pacman-right/1.png", (psize, psize)),
                self.load_image("assets/pacman-right/2.png", (psize, psize)),
                self.load_image("assets/pacman-right/3.png", (psize, psize)),
            ],
            "up": [
                self.load_image("assets/pacman-up/1.png", (psize, psize)),
                self.load_image("assets/pacman-up/2.png", (psize, psize)),
                self.load_image("assets/pacman-up/3.png", (psize, psize)),
            ],
            "down": [
                self.load_image("assets/pacman-down/1.png", (psize, psize)),
                self.load_image("assets/pacman-down/2.png", (psize, psize)),
                self.load_image("assets/pacman-down/3.png", (psize, psize)),
            ],
        }
        self.ghost_sprites = {
            "blinky": self.load_image("assets/ghosts/blinky.png", (psize, psize)),
            "pinky": self.load_image("assets/ghosts/pinky.png", (psize, psize)),
            "inky": self.load_image("assets/ghosts/inky.png", (psize, psize)),
            "clyde": self.load_image("assets/ghosts/clyde.png", (psize, psize)),
            "blue": self.load_image("assets/ghosts/blue_ghost.png", (psize, psize)),
        }
        self.dot_radius = max(3, self.tile_size // 6)
        self.power_radius = max(6, self.tile_size // 3)

    def load_sounds(self):
        self.sounds_enabled = False
        self.snd_dot = None
        self.snd_death = None
        self.snd_eat_ghost = None
        self.snd_begin = None

        # All sounds are intentionally disabled by user request.
        return

    def reset_round(self, full_reset=False):
        if full_reset:
            self.score = 0
            self.lives = 3
            self.game_state = "playing"

        self.pacman_cell = tuple(self.pacman_start)
        self.pacman_pos = self.cell_center(self.pacman_cell)
        self.pacman_dir = (0, 0)
        self.desired_dir = (0, 0)
        self.pacman_facing = "right"
        self.anim_timer = 0.0
        self.anim_index = 0

        spawn_cells = self.find_ghost_spawn_cells()
        self.ghosts = [
            self.make_ghost("blinky", spawn_cells[0]),
            self.make_ghost("pinky", spawn_cells[1]),
            self.make_ghost("inky", spawn_cells[2]),
            self.make_ghost("clyde", spawn_cells[3]),
        ]

        self.power_end_time = 0
        self.dot_sound_cooldown = 0

        if self.sounds_enabled and self.snd_begin and self.game_state == "playing":
            self.snd_begin.play()

    def make_ghost(self, name, cell):
        return {
            "name": name,
            "start": cell,
            "cell": cell,
            "pos": self.cell_center(cell),
            "dir": (-1, 0),
            "speed": 5.2,
        }

    def find_ghost_spawn_cells(self):
        base_r, base_c = self.ghost_den
        candidates = [
            (base_r - 2, base_c),
            (base_r - 2, base_c - 1),
            (base_r - 2, base_c + 1),
            (base_r - 3, base_c),
            (base_r - 1, base_c),
            (base_r, base_c),
            (base_r, base_c - 1),
            (base_r, base_c + 1),
            (base_r + 1, base_c),
        ]

        result = []
        for cell in candidates:
            if len(result) == 4:
                break
            if not self.can_enter(cell, is_ghost=True):
                continue
            if cell in result:
                continue
            result.append(cell)

        if len(result) < 4:
            # Fallback: safely duplicate a valid den cell to keep initialization stable.
            while len(result) < 4:
                result.append(result[-1] if result else self.ghost_den)

        return result

    def cell_center(self, cell):
        r, c = cell
        return pygame.Vector2(
            c * self.tile_size + self.tile_size / 2,
            r * self.tile_size + self.tile_size / 2,
        )

    def pos_to_cell(self, pos):
        c = int(pos.x // self.tile_size)
        r = int(pos.y // self.tile_size)
        c = max(0, min(self.cols - 1, c))
        r = max(0, min(self.rows - 1, r))
        return r, c

    def in_bounds(self, cell):
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def warp_column(self, c):
        if c < 0:
            return self.cols - 1
        if c >= self.cols:
            return 0
        return c

    def next_cell(self, cell, direction):
        dr, dc = direction
        r, c = cell
        nr = r + dr
        nc = self.warp_column(c + dc)
        return nr, nc

    def can_enter(self, cell, is_ghost=False):
        r, c = cell
        if not (0 <= r < self.rows):
            return False
        if not (0 <= c < self.cols):
            return False
        value = self.matrix[r][c]
        if value == "wall":
            return False
        if value == "elec" and not is_ghost:
            return False
        return True

    def is_centered(self, pos, cell, eps=0.25):
        center = self.cell_center(cell)
        return pos.distance_to(center) <= eps

    def try_apply_desired_direction(self):
        if self.desired_dir == (0, 0):
            return
        target = self.next_cell(self.pacman_cell, self.desired_dir)
        if self.can_enter(target, is_ghost=False):
            self.pacman_dir = self.desired_dir

    def move_entity(self, pos, cell, direction, speed, dt, is_ghost=False):
        if direction == (0, 0):
            return pos, cell

        target_cell = self.next_cell(cell, direction)
        if not self.can_enter(target_cell, is_ghost=is_ghost):
            return self.cell_center(cell), cell

        target_center = self.cell_center(target_cell)
        direction_vec = target_center - pos
        max_step = speed * self.tile_size * dt

        if direction_vec.length() <= max_step:
            return target_center, target_cell

        step = direction_vec.normalize() * max_step
        return pos + step, cell

    def update_pacman(self, dt):
        if self.is_centered(self.pacman_pos, self.pacman_cell):
            self.pacman_pos = self.cell_center(self.pacman_cell)
            self.try_apply_desired_direction()

            ahead = self.next_cell(self.pacman_cell, self.pacman_dir)
            if not self.can_enter(ahead, is_ghost=False):
                self.pacman_dir = (0, 0)

        self.pacman_pos, self.pacman_cell = self.move_entity(
            self.pacman_pos,
            self.pacman_cell,
            self.pacman_dir,
            speed=7.2,
            dt=dt,
            is_ghost=False,
        )

        if self.pacman_dir == (-1, 0):
            self.pacman_facing = "up"
        elif self.pacman_dir == (1, 0):
            self.pacman_facing = "down"
        elif self.pacman_dir == (0, -1):
            self.pacman_facing = "left"
        elif self.pacman_dir == (0, 1):
            self.pacman_facing = "right"

        if self.pacman_dir != (0, 0):
            self.anim_timer += dt
            if self.anim_timer >= 0.09:
                self.anim_timer = 0
                self.anim_index = (self.anim_index + 1) % 3

        self.consume_collectibles()

    def consume_collectibles(self):
        if self.pacman_cell in self.dots:
            self.dots.remove(self.pacman_cell)
            self.score += 10
            if self.sounds_enabled and self.snd_dot and self.dot_sound_cooldown <= 0:
                self.snd_dot.play()
                self.dot_sound_cooldown = 80
        elif self.pacman_cell in self.power_dots:
            self.power_dots.remove(self.pacman_cell)
            self.score += 50
            self.power_end_time = pygame.time.get_ticks() + self.power_duration_ms
            if self.sounds_enabled and self.snd_dot:
                self.snd_dot.play()

    def ghost_options(self, ghost, allow_reverse=False):
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        options = []
        for d in directions:
            if not allow_reverse and d == (-ghost["dir"][0], -ghost["dir"][1]):
                continue
            nxt = self.next_cell(ghost["cell"], d)
            if self.can_enter(nxt, is_ghost=True):
                options.append(d)
        if not options:
            for d in directions:
                nxt = self.next_cell(ghost["cell"], d)
                if self.can_enter(nxt, is_ghost=True):
                    options.append(d)
        return options

    def choose_ghost_direction(self, ghost, frightened):
        options = self.ghost_options(ghost)
        if not options:
            ghost["dir"] = (0, 0)
            return

        if frightened:
            ghost["dir"] = random.choice(options)
            return

        target = self.pacman_cell
        ranked = []
        for d in options:
            nr, nc = self.next_cell(ghost["cell"], d)
            dist = abs(target[0] - nr) + abs(target[1] - nc)
            ranked.append((dist, d))

        ranked.sort(key=lambda x: x[0])
        if len(ranked) > 1 and random.random() < 0.2:
            ghost["dir"] = ranked[1][1]
        else:
            ghost["dir"] = ranked[0][1]

    def update_ghosts(self, dt):
        frightened = pygame.time.get_ticks() < self.power_end_time
        for ghost in self.ghosts:
            if self.is_centered(ghost["pos"], ghost["cell"]):
                ghost["pos"] = self.cell_center(ghost["cell"])
                self.choose_ghost_direction(ghost, frightened)

            ghost["pos"], ghost["cell"] = self.move_entity(
                ghost["pos"],
                ghost["cell"],
                ghost["dir"],
                speed=ghost["speed"],
                dt=dt,
                is_ghost=True,
            )

    def check_collisions(self):
        frightened = pygame.time.get_ticks() < self.power_end_time
        for ghost in self.ghosts:
            if ghost["pos"].distance_to(self.pacman_pos) <= self.tile_size * 0.55:
                if frightened:
                    ghost["cell"] = ghost["start"]
                    ghost["pos"] = self.cell_center(ghost["start"])
                    ghost["dir"] = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
                    self.score += 200
                    if self.sounds_enabled and self.snd_eat_ghost:
                        self.snd_eat_ghost.play()
                else:
                    self.lives -= 1
                    if self.sounds_enabled and self.snd_death:
                        self.snd_death.play()
                    if self.lives <= 0:
                        self.game_state = "game_over"
                    else:
                        self.reset_round(full_reset=False)
                    break

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    return False
                if self.game_state in ("game_over", "win") and event.key == pygame.K_r:
                    self.dots.clear()
                    self.power_dots.clear()
                    self.parse_grid()
                    self.reset_round(full_reset=True)
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.desired_dir = (0, -1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.desired_dir = (0, 1)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.desired_dir = (-1, 0)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.desired_dir = (1, 0)
        return True

    def draw_board(self):
        self.screen.fill((0, 0, 0))

        wall_color = (22, 66, 210)
        for r, c in self.walls:
            rect = pygame.Rect(
                c * self.tile_size,
                r * self.tile_size,
                self.tile_size,
                self.tile_size,
            )
            pygame.draw.rect(self.screen, wall_color, rect, border_radius=4)

        for r, c in self.elec_gates:
            x = c * self.tile_size
            y = r * self.tile_size + self.tile_size // 2
            pygame.draw.line(
                self.screen,
                (220, 60, 70),
                (x + 2, y),
                (x + self.tile_size - 2, y),
                3,
            )

        for r, c in self.dots:
            cx = int(c * self.tile_size + self.tile_size / 2)
            cy = int(r * self.tile_size + self.tile_size / 2)
            pygame.draw.circle(self.screen, (245, 245, 245), (cx, cy), self.dot_radius)

        for r, c in self.power_dots:
            cx = int(c * self.tile_size + self.tile_size / 2)
            cy = int(r * self.tile_size + self.tile_size / 2)
            pygame.draw.circle(self.screen, (255, 210, 80), (cx, cy), self.power_radius)

    def draw_characters(self):
        pacman_img = self.pacman_frames[self.pacman_facing][self.anim_index]
        px = int(self.pacman_pos.x - pacman_img.get_width() / 2)
        py = int(self.pacman_pos.y - pacman_img.get_height() / 2)
        self.screen.blit(pacman_img, (px, py))

        frightened = pygame.time.get_ticks() < self.power_end_time
        for ghost in self.ghosts:
            sprite_key = "blue" if frightened else ghost["name"]
            img = self.ghost_sprites[sprite_key]
            gx = int(ghost["pos"].x - img.get_width() / 2)
            gy = int(ghost["pos"].y - img.get_height() / 2)
            self.screen.blit(img, (gx, gy))

    def draw_hud(self):
        hud_top = self.rows * self.tile_size
        hud_rect = pygame.Rect(0, hud_top, self.width, self.hud_height)
        pygame.draw.rect(self.screen, (10, 10, 10), hud_rect)
        pygame.draw.line(self.screen, (70, 70, 70), (0, hud_top), (self.width, hud_top), 2)

        score_text = self.font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 227, 70))
        self.screen.blit(score_text, (18, hud_top + 10))
        self.screen.blit(lives_text, (self.width - 170, hud_top + 10))

        status = "Arrows/WASD to move"
        if self.game_state == "win":
            status = "YOU WIN! Press R to restart"
        elif self.game_state == "game_over":
            status = "GAME OVER! Press R to restart"
        elif pygame.time.get_ticks() < self.power_end_time:
            status = "POWER MODE"

        status_text = self.small_font.render(status, True, (170, 200, 255))
        self.screen.blit(status_text, (18, hud_top + 42))

    def update(self, dt):
        if self.game_state != "playing":
            return

        if self.dot_sound_cooldown > 0:
            self.dot_sound_cooldown -= int(dt * 1000)

        self.update_pacman(dt)
        self.update_ghosts(dt)
        self.check_collisions()

        if not self.dots and not self.power_dots:
            self.game_state = "win"

    def draw(self):
        self.draw_board()
        self.draw_characters()
        self.draw_hud()
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            running = self.process_events()
            self.update(dt)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    PacmanGame().run()
