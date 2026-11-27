import sys
import math
import pygame


WIDTH, HEIGHT = 1000, 600
FPS = 60

SKY = (92, 148, 252)
LAVA = (255, 90, 10)
LAVA_DARK = (120, 20, 0)
LAVA_GLOW = (255, 200, 60)
HILL_GREEN = (0, 150, 0)
HILL_GREEN_LIGHT = (40, 190, 40)
BUSH_GREEN = (0, 140, 0)
BUSH_GREEN_LIGHT = (40, 180, 40)
BRICK = (198, 98, 40)
BRICK_LINE = (140, 60, 20)
QBLOCK = (255, 184, 28)
QBLOCK_DARK = (170, 110, 0)
PIPE_GREEN = (40, 176, 60)
PIPE_DARK = (10, 120, 30)
PIPE_HILITE = (140, 230, 140)
WHITE = (255, 255, 255)
BLACK = (25, 25, 25)
YELLOW = (255, 216, 0)

CAT_FUR = (240, 150, 60)
CAT_FUR_DARK = (200, 108, 40)
CAT_BELLY = (255, 235, 210)
CAT_EAR_INNER = (255, 190, 200)
CAT_EYE = (90, 200, 90)
CAT_NOSE = (255, 140, 165)

ROBE_BLACK = (16, 14, 18)
ROBE_BLACK_LIGHT = (34, 30, 38)
SKULL_CAVITY = (70, 8, 8)
SKULL_RED = (200, 30, 20)
SKULL_RED_BRIGHT = (255, 70, 40)
SKULL_RED_GLOW = (255, 130, 60)
CLAW_RED = (170, 20, 20)
BOOT_BLACK = (10, 10, 12)

POLE_GREY = (210, 210, 210)
FLAG_GREEN = (30, 170, 40)
CASTLE_GREY = (190, 190, 195)
CASTLE_DARK = (120, 120, 130)
CASTLE_WINDOW = (30, 20, 40)

CAVE_BG = (18, 16, 26)
CAVE_WALL = (58, 48, 66)
CAVE_WALL_DARK = (38, 30, 44)
STALACTITE = (48, 40, 56)


class Player:
	def __init__(self, x, y):
		self.rect = pygame.Rect(x, y, 34, 50)
		self.vx = 0
		self.vy = 0
		self.speed = 4.2
		self.jump_force = 12.5
		self.gravity = 0.62
		self.max_fall = 12
		self.on_ground = False
		self.coins = 0
		self.lives = 3
		self.invuln_timer = 0
		self.facing = 1
		self.anim_timer = 0

	def input(self):
		keys = pygame.key.get_pressed()
		self.vx = 0
		if keys[pygame.K_LEFT] or keys[pygame.K_a]:
			self.vx = -self.speed
			self.facing = -1
		if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
			self.vx = self.speed
			self.facing = 1
		if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
			self.vy = -self.jump_force
			self.on_ground = False

	def apply_gravity(self):
		self.vy += self.gravity
		if self.vy > self.max_fall:
			self.vy = self.max_fall

	def move_and_collide(self, solids):
		self.rect.x += int(self.vx)
		for tile in solids:
			if self.rect.colliderect(tile):
				if self.vx > 0:
					self.rect.right = tile.left
				elif self.vx < 0:
					self.rect.left = tile.right

		self.rect.y += int(self.vy)
		self.on_ground = False
		for tile in solids:
			if self.rect.colliderect(tile):
				if self.vy > 0:
					self.rect.bottom = tile.top
					self.vy = 0
					self.on_ground = True
				elif self.vy < 0:
					self.rect.top = tile.bottom
					self.vy = 0

	def draw(self, screen, cam_x):
		self.anim_timer += 1
		if self.invuln_timer > 0 and (self.invuln_timer // 4) % 2 == 0:
			return

		x = int(self.rect.x - cam_x)
		y = int(self.rect.y)
		facing = self.facing
		moving = self.on_ground and abs(self.vx) > 0.1
		airborne = not self.on_ground

		# tail (trails behind facing direction, swaying while walking)
		back = -1 if facing >= 0 else 1
		sway = 8 if moving and (self.anim_timer // 10) % 2 == 0 else 2
		tail_base = (x + 17 + back * 12, y + 30)
		tail_mid = (tail_base[0] + back * 8, y + 18 - sway // 2)
		tail_tip = (tail_base[0] + back * 6, y + 8 - sway)
		pygame.draw.line(screen, CAT_FUR_DARK, tail_base, tail_mid, 6)
		pygame.draw.line(screen, CAT_FUR_DARK, tail_mid, tail_tip, 5)
		pygame.draw.circle(screen, CAT_FUR_DARK, tail_tip, 3)

		# legs / paws
		if airborne:
			pygame.draw.ellipse(screen, CAT_FUR, (x + 4, y + 40, 10, 10))
			pygame.draw.ellipse(screen, CAT_FUR, (x + 20, y + 38, 10, 11))
		elif moving and (self.anim_timer // 6) % 2 == 0:
			pygame.draw.ellipse(screen, CAT_FUR, (x + 2, y + 38, 10, 11))
			pygame.draw.ellipse(screen, CAT_FUR, (x + 22, y + 41, 10, 8))
		else:
			pygame.draw.ellipse(screen, CAT_FUR, (x + 3, y + 41, 10, 8))
			pygame.draw.ellipse(screen, CAT_FUR, (x + 21, y + 38, 10, 11))

		# body
		pygame.draw.ellipse(screen, CAT_FUR, (x + 3, y + 19, 28, 25))
		pygame.draw.ellipse(screen, CAT_BELLY, (x + 10, y + 27, 14, 15))

		# front paws
		pygame.draw.circle(screen, CAT_FUR, (x + 2, y + 33), 5)
		pygame.draw.circle(screen, CAT_FUR, (x + 32, y + 33), 5)

		# head + ears
		pygame.draw.polygon(screen, CAT_FUR, [(x + 4, y + 8), (x + 9, y - 4), (x + 14, y + 7)])
		pygame.draw.polygon(screen, CAT_FUR, [(x + 20, y + 7), (x + 25, y - 4), (x + 30, y + 8)])
		pygame.draw.polygon(screen, CAT_EAR_INNER, [(x + 7, y + 5), (x + 9, y), (x + 12, y + 5)])
		pygame.draw.polygon(screen, CAT_EAR_INNER, [(x + 22, y + 5), (x + 25, y), (x + 27, y + 5)])
		pygame.draw.circle(screen, CAT_FUR, (x + 17, y + 14), 13)
		pygame.draw.line(screen, CAT_FUR_DARK, (x + 6, y + 6), (x + 10, y + 9), 2)
		pygame.draw.line(screen, CAT_FUR_DARK, (x + 28, y + 6), (x + 24, y + 9), 2)

		# eyes (pupils shift toward facing direction)
		pupil_off = 1 if facing >= 0 else -1
		for ex in (x + 11, x + 23):
			pygame.draw.circle(screen, WHITE, (ex, y + 14), 4)
			pygame.draw.circle(screen, CAT_EYE, (ex + pupil_off, y + 14), 3)
			pygame.draw.circle(screen, BLACK, (ex + pupil_off, y + 14), 1)

		# nose + mouth
		pygame.draw.polygon(screen, CAT_NOSE, [(x + 15, y + 18), (x + 19, y + 18), (x + 17, y + 21)])
		pygame.draw.line(screen, BLACK, (x + 17, y + 21), (x + 13, y + 24), 1)
		pygame.draw.line(screen, BLACK, (x + 17, y + 21), (x + 21, y + 24), 1)

		# whiskers
		for dy in (-3, 0, 3):
			pygame.draw.line(screen, WHITE, (x + 1, y + 17 + dy), (x + 9, y + 17 + dy), 1)
			pygame.draw.line(screen, WHITE, (x + 33, y + 17 + dy), (x + 25, y + 17 + dy), 1)


class Enemy:
	def __init__(self, x, y, left_limit, right_limit):
		self.rect = pygame.Rect(x, y, 34, 30)
		self.vx = -1.4
		self.left_limit = left_limit
		self.right_limit = right_limit
		self.alive = True
		self.anim_timer = 0

	def update(self):
		if not self.alive:
			return
		self.anim_timer += 1
		self.rect.x += int(self.vx)
		if self.rect.left <= self.left_limit or self.rect.right >= self.right_limit:
			self.vx *= -1

	def draw(self, screen, cam_x):
		if not self.alive:
			return
		x = self.rect.x - cam_x
		y = self.rect.y
		sway = 2 if (self.anim_timer // 20) % 2 == 0 else -2
		glow = (self.anim_timer // 15) % 2 == 0
		eye_color = SKULL_RED_BRIGHT if glow else SKULL_RED_GLOW

		# tattered hood (jagged top edge)
		hood_pts = [
			(x + 2, y + 10), (x + 4, y - 6), (x + 8, y - 14), (x + 11, y - 6),
			(x + 14, y - 16), (x + 17, y - 6), (x + 20, y - 16), (x + 23, y - 6),
			(x + 26, y - 14), (x + 30, y - 6), (x + 32, y + 10),
			(x + 27, y + 14), (x + 7, y + 14),
		]
		pygame.draw.polygon(screen, ROBE_BLACK, hood_pts)

		# glowing skull face inside the hood
		pygame.draw.ellipse(screen, SKULL_CAVITY, (x + 9, y + 0, 16, 14))
		pygame.draw.ellipse(screen, eye_color, (x + 11, y + 3, 4, 5))
		pygame.draw.ellipse(screen, eye_color, (x + 19, y + 3, 4, 5))
		pygame.draw.rect(screen, SKULL_RED, (x + 12, y + 9, 10, 3))
		for tx in range(0, 10, 2):
			pygame.draw.line(screen, BLACK, (x + 12 + tx, y + 9), (x + 12 + tx, y + 12), 1)

		# flowing tattered robe (wider than the hitbox, jagged hem)
		robe_pts = [
			(x + 8, y + 12), (x + 26, y + 12), (x + 31, y + 22),
			(x + 29, y + 30), (x + 33, y + 34), (x + 25, y + 31), (x + 21, y + 35),
			(x + 17, y + 31), (x + 13, y + 35), (x + 9, y + 31), (x + 5, y + 34),
			(x + 3, y + 30), (x + 1, y + 22),
		]
		pygame.draw.polygon(screen, ROBE_BLACK, robe_pts)
		pygame.draw.line(screen, ROBE_BLACK_LIGHT, (x + 17, y + 14), (x + 17, y + 30), 2)

		# boots peeking out from under the hem
		pygame.draw.ellipse(screen, BOOT_BLACK, (x + 6, y + 32, 8, 5))
		pygame.draw.ellipse(screen, BOOT_BLACK, (x + 20, y + 32, 8, 5))

		# sleeves + clawed hands
		for side in (-1, 1):
			sx = x + 17 + side * 15
			hand_y = y + 24 + (sway if side > 0 else -sway)
			sleeve_pts = [(sx - 4, y + 13), (sx + 4, y + 13), (sx + 2, hand_y), (sx - 3, hand_y)]
			pygame.draw.polygon(screen, ROBE_BLACK, sleeve_pts)
			pygame.draw.ellipse(screen, CLAW_RED, (sx - 5, hand_y - 2, 10, 7))
			for i in range(3):
				cx = sx - 3 + i * 3
				pygame.draw.polygon(screen, CLAW_RED, [(cx, hand_y + 3), (cx + 2, hand_y + 3), (cx + 1, hand_y + 7)])


class Coin:
	def __init__(self, x, y):
		self.rect = pygame.Rect(x, y, 20, 20)
		self.t = 0
		self.collected = False

	def update(self):
		self.t += 0.1

	def draw(self, screen, cam_x):
		if self.collected:
			return
		x = self.rect.x - cam_x
		y = self.rect.y + int(2 * pygame.math.Vector2(1, 0).rotate(self.t * 50).y)
		pygame.draw.ellipse(screen, (245, 200, 30), (x, y, 20, 20))
		pygame.draw.ellipse(screen, YELLOW, (x + 3, y + 3, 14, 14), 2)
		pygame.draw.line(screen, WHITE, (x + 6, y + 4), (x + 6, y + 10), 2)


def make_level():
	solids = []
	ground_y = 540

	ground_rect = pygame.Rect(-200, ground_y, 2600, 80)
	solids.append(ground_rect)

	platform_specs = [
		(220, 460, 120, 20, "brick"),
		(420, 400, 120, 20, "question"),
		(620, 340, 140, 20, "brick"),
		(850, 450, 180, 20, "brick"),
		(1170, 390, 140, 20, "question"),
		(1400, 330, 140, 20, "brick"),
		(1620, 270, 140, 20, "question"),
		(1840, 420, 180, 20, "brick"),
	]
	blocks = []
	for bx, by, bw, bh, kind in platform_specs:
		r = pygame.Rect(bx, by, bw, bh)
		blocks.append((r, kind))
		solids.append(r)

	pipes = [
		pygame.Rect(520, 470, 70, 70),
		pygame.Rect(980, 430, 70, 110),
		pygame.Rect(1520, 410, 70, 130),
	]
	solids.extend(pipes)

	enemies = [
		Enemy(720, 510, 640, 940),
		Enemy(1260, 360, 1170, 1310),
		Enemy(1880, 390, 1840, 2020),
	]

	coins = [
		Coin(250, 420), Coin(290, 420),
		Coin(450, 360), Coin(490, 360),
		Coin(655, 300), Coin(700, 300),
		Coin(910, 410), Coin(960, 410),
		Coin(1210, 350), Coin(1450, 290),
		Coin(1670, 230), Coin(1710, 230),
		Coin(1900, 380), Coin(1950, 380),
	]

	flag_x = 2200
	flag_rect = pygame.Rect(flag_x, 250, 18, 290)

	return solids, blocks, pipes, enemies, coins, flag_rect, ground_y, ground_rect


def make_underground_level():
	solids = []
	ground_y = 540
	ceiling_y = 70

	ground_rect = pygame.Rect(-200, ground_y, 2600, 80)
	ceiling_rect = pygame.Rect(-200, 0, 2600, ceiling_y)
	solids.append(ground_rect)
	solids.append(ceiling_rect)

	platform_specs = [
		(150, 470, 70, 18, "brick"),
		(280, 420, 60, 18, "brick"),
		(400, 460, 55, 18, "question"),
		(520, 380, 60, 18, "brick"),
		(650, 440, 55, 18, "brick"),
		(780, 340, 60, 18, "question"),
		(900, 420, 50, 18, "brick"),
		(1020, 300, 60, 18, "brick"),
		(1150, 400, 50, 18, "question"),
		(1270, 460, 60, 18, "brick"),
		(1400, 340, 55, 18, "brick"),
		(1530, 420, 50, 18, "question"),
		(1650, 460, 70, 18, "brick"),
	]
	blocks = []
	for bx, by, bw, bh, kind in platform_specs:
		r = pygame.Rect(bx, by, bw, bh)
		blocks.append((r, kind))
		solids.append(r)

	exit_pipe = pygame.Rect(1850, ground_y - 70, 70, 70)
	pipes = [exit_pipe]
	solids.extend(pipes)

	enemy_platforms = [0, 2, 4, 6, 8, 10]
	enemies = []
	for i in enemy_platforms:
		px, py, pw, ph, kind = platform_specs[i]
		ew = 34
		left = px
		right = max(px + pw - ew, px)
		enemies.append(Enemy(px, py - 30, left, right))
	enemies.extend([
		Enemy(500, 510, 400, 700),
		Enemy(1100, 510, 950, 1300),
		Enemy(1750, 510, 1650, 1920),
	])

	coins = [
		Coin(290, 380), Coin(410, 420),
		Coin(530, 340), Coin(660, 400),
		Coin(790, 300), Coin(910, 380),
		Coin(1030, 260), Coin(1160, 360),
		Coin(1280, 420), Coin(1410, 300),
		Coin(1540, 380), Coin(1660, 420),
	]

	world_width = 2000

	return solids, blocks, pipes, enemies, coins, ground_y, ceiling_y, exit_pipe, world_width, ground_rect


def build_surface_level():
	solids, blocks, pipes, enemies, coins, flag_rect, ground_y, ground_rect = make_level()
	return {
		"kind": "surface",
		"solids": solids,
		"blocks": blocks,
		"pipes": pipes,
		"enemies": enemies,
		"coins": coins,
		"flag_rect": flag_rect,
		"ground_y": ground_y,
		"ground_rect": ground_rect,
		"ceiling_y": None,
		"exit_pipe": None,
		"world_width": 2400,
		"spawn": (80, 470),
	}


def build_underground_level():
	solids, blocks, pipes, enemies, coins, ground_y, ceiling_y, exit_pipe, world_width, ground_rect = make_underground_level()
	return {
		"kind": "underground",
		"solids": solids,
		"blocks": blocks,
		"pipes": pipes,
		"enemies": enemies,
		"coins": coins,
		"flag_rect": None,
		"ground_y": ground_y,
		"ground_rect": ground_rect,
		"ceiling_y": ceiling_y,
		"exit_pipe": exit_pipe,
		"world_width": world_width,
		"spawn": (100, 470),
	}


def generate_background(world_width):
	clouds = []
	x, i = 60, 0
	while x < world_width + 200:
		y = 50 + (i % 3) * 35
		scale = 0.9 + (i % 2) * 0.3
		clouds.append((x, y, scale))
		x += 260 + (i % 2) * 80
		i += 1

	hills = []
	x, i = -50, 0
	while x < world_width + 200:
		size = 80 + (i % 3) * 20
		hills.append((x, size))
		x += 340 + (i % 2) * 120
		i += 1

	bushes = []
	x, i = 40, 0
	while x < world_width + 100:
		count = 2 + (i % 3)
		bushes.append((x, count))
		x += 220 + (i % 2) * 100
		i += 1

	return clouds, hills, bushes


def draw_cloud(screen, x, y, scale):
	r = 16 * scale
	pygame.draw.ellipse(screen, WHITE, (x, y + r * 0.4, r * 2.2, r * 1.3))
	pygame.draw.ellipse(screen, WHITE, (x + r * 0.9, y, r * 1.8, r * 1.6))
	pygame.draw.ellipse(screen, WHITE, (x + r * 1.9, y + r * 0.5, r * 1.6, r * 1.2))


def draw_hill(screen, x, ground_y, size):
	pygame.draw.circle(screen, HILL_GREEN, (int(x), ground_y), size)
	pygame.draw.circle(screen, HILL_GREEN_LIGHT, (int(x - size * 0.3), ground_y - int(size * 0.15)), int(size * 0.55))


def draw_bush(screen, x, ground_y, count):
	r = 13
	for i in range(count):
		pygame.draw.circle(screen, BUSH_GREEN, (int(x + i * r * 1.2), ground_y - r // 2), r)
	pygame.draw.circle(screen, BUSH_GREEN_LIGHT, (int(x + count * 0.6 * r), ground_y - r - 2), r - 3)


def draw_lava_floor(screen, ground_y, cam_x):
	pygame.draw.rect(screen, LAVA_DARK, (0, ground_y, WIDTH, HEIGHT - ground_y))

	t = pygame.time.get_ticks() / 200.0
	cam_i = int(cam_x)
	step = 16
	top_pts = []
	x = -step
	while x <= WIDTH + step:
		wave_y = ground_y + math.sin((x + cam_i) * 0.05 + t) * 4
		top_pts.append((x, wave_y))
		x += step
	pygame.draw.polygon(screen, LAVA, top_pts + [(WIDTH + step, HEIGHT), (-step, HEIGHT)])
	for i in range(len(top_pts) - 1):
		pygame.draw.line(screen, LAVA_GLOW, top_pts[i], top_pts[i + 1], 2)

	ticks = pygame.time.get_ticks()
	for i in range(14):
		seed = i * 733
		bx = ((seed + cam_i // 3 + ticks // 6) % (WIDTH + 200)) - 100
		cycle = (ticks // 12 + seed) % 90
		if cycle < 24:
			by = ground_y + 22 - cycle
			r = max(1, 4 - cycle // 7)
			pygame.draw.circle(screen, LAVA_GLOW, (int(bx), int(by)), r)


def draw_stalactite(screen, x, y, w, h):
	pygame.draw.polygon(screen, STALACTITE, [(x, y), (x + w, y), (x + w / 2, y + h)])


def draw_blocks_and_pipes(screen, blocks, pipes, cam_x, block_font):
	for rect, kind in blocks:
		x = rect.x - cam_x
		y = rect.y
		if x + rect.width < -20 or x > WIDTH + 20:
			continue
		if kind == "question":
			pygame.draw.rect(screen, QBLOCK, (x, y, rect.width, rect.height), border_radius=3)
			pygame.draw.rect(screen, QBLOCK_DARK, (x, y, rect.width, rect.height), 3, border_radius=3)
			pygame.draw.circle(screen, QBLOCK_DARK, (x + 5, y + 5), 2)
			pygame.draw.circle(screen, QBLOCK_DARK, (x + rect.width - 5, y + 5), 2)
			pygame.draw.circle(screen, QBLOCK_DARK, (x + 5, y + rect.height - 5), 2)
			pygame.draw.circle(screen, QBLOCK_DARK, (x + rect.width - 5, y + rect.height - 5), 2)
			q = block_font.render("?", True, WHITE)
			screen.blit(q, (x + rect.width // 2 - q.get_width() // 2, y + rect.height // 2 - q.get_height() // 2))
		else:
			pygame.draw.rect(screen, BRICK, (x, y, rect.width, rect.height), border_radius=3)
			pygame.draw.rect(screen, BRICK_LINE, (x, y, rect.width, rect.height), 2, border_radius=3)
			pygame.draw.line(screen, BRICK_LINE, (x, y + rect.height // 2), (x + rect.width, y + rect.height // 2), 2)
			seg = rect.width // 3 or 1
			for lx in range(seg, rect.width, seg):
				pygame.draw.line(screen, BRICK_LINE, (x + lx, y), (x + lx, y + rect.height // 2), 1)
			for lx in range(seg // 2, rect.width, seg):
				pygame.draw.line(screen, BRICK_LINE, (x + lx, y + rect.height // 2), (x + lx, y + rect.height), 1)

	for p in pipes:
		x = p.x - cam_x
		y = p.y
		pygame.draw.rect(screen, PIPE_DARK, (x, y, p.width, p.height))
		pygame.draw.rect(screen, PIPE_GREEN, (x + 4, y, p.width - 8, p.height))
		pygame.draw.rect(screen, PIPE_HILITE, (x + 6, y + 4, 6, p.height - 8))
		pygame.draw.rect(screen, PIPE_DARK, (x - 8, y - 14, p.width + 16, 18), border_radius=3)
		pygame.draw.rect(screen, PIPE_GREEN, (x - 4, y - 14, p.width + 8, 16), border_radius=3)
		pygame.draw.rect(screen, PIPE_HILITE, (x, y - 12, 6, 12))


def draw_world(screen, blocks, pipes, ground_y, cam_x, clouds, hills, bushes, block_font):
	screen.fill(SKY)

	cloud_cam = cam_x * 0.3
	for cx, cy, scale in clouds:
		sx = cx - cloud_cam
		if -80 < sx < WIDTH + 80:
			draw_cloud(screen, sx, cy, scale)

	hill_cam = cam_x * 0.55
	for hx, size in hills:
		sx = hx - hill_cam
		if -size < sx < WIDTH + size:
			draw_hill(screen, sx, ground_y, size)

	for bx, count in bushes:
		sx = bx - cam_x
		if -80 < sx < WIDTH + 80:
			draw_bush(screen, sx, ground_y, count)

	draw_lava_floor(screen, ground_y, cam_x)

	draw_blocks_and_pipes(screen, blocks, pipes, cam_x, block_font)


def draw_underground(screen, blocks, pipes, ground_y, ceiling_y, cam_x, block_font):
	screen.fill(CAVE_BG)

	pygame.draw.rect(screen, CAVE_WALL, (0, 0, WIDTH, ceiling_y))
	pygame.draw.rect(screen, CAVE_WALL_DARK, (0, ceiling_y - 4, WIDTH, 4))

	tile = 70
	cam_i = int(cam_x)
	sx = -(cam_i % tile) - tile
	i = 0
	while sx < WIDTH + tile:
		h = 14 + (i % 3) * 8
		draw_stalactite(screen, sx, ceiling_y - 4, 22, h)
		sx += tile
		i += 1

	draw_lava_floor(screen, ground_y, cam_x)

	draw_blocks_and_pipes(screen, blocks, pipes, cam_x, block_font)


def draw_flag(screen, flag_rect, cam_x):
	x = flag_rect.x - cam_x

	castle_x = x + 70
	base_y = flag_rect.y + flag_rect.height - 90
	for tx in range(0, 150, 20):
		pygame.draw.rect(screen, CASTLE_GREY, (castle_x + tx - 10, base_y - 14, 14, 14))
	pygame.draw.rect(screen, CASTLE_GREY, (castle_x, base_y, 140, 90))
	pygame.draw.rect(screen, CASTLE_DARK, (castle_x, base_y, 140, 90), 3)
	pygame.draw.rect(screen, CASTLE_DARK, (castle_x + 55, base_y + 30, 30, 60))
	pygame.draw.circle(screen, CASTLE_WINDOW, (castle_x + 70, base_y + 55), 10)
	pygame.draw.circle(screen, CASTLE_WINDOW, (castle_x + 30, base_y + 25), 6)
	pygame.draw.circle(screen, CASTLE_WINDOW, (castle_x + 110, base_y + 25), 6)

	pygame.draw.rect(screen, POLE_GREY, (x, flag_rect.y, 6, flag_rect.height))
	pygame.draw.circle(screen, YELLOW, (x + 3, flag_rect.y), 8)
	pygame.draw.polygon(
		screen,
		FLAG_GREEN,
		[(x + 6, flag_rect.y + 18), (x + 46, flag_rect.y + 30), (x + 6, flag_rect.y + 42)],
	)


def draw_hud(screen, font, player, win, area_kind):
	pygame.draw.rect(screen, (15, 15, 20), (0, 0, WIDTH, 42))

	pygame.draw.ellipse(screen, (245, 200, 30), (18, 10, 20, 20))
	pygame.draw.ellipse(screen, YELLOW, (21, 13, 14, 14), 2)
	coin_txt = font.render(f"x{player.coins:02d}", True, WHITE)
	screen.blit(coin_txt, (44, 9))

	pygame.draw.polygon(screen, CAT_FUR, [(166, 15), (169, 8), (172, 15)])
	pygame.draw.polygon(screen, CAT_FUR, [(176, 15), (179, 8), (182, 15)])
	pygame.draw.circle(screen, CAT_FUR, (174, 20), 9)
	pygame.draw.circle(screen, BLACK, (170, 19), 1)
	pygame.draw.circle(screen, BLACK, (178, 19), 1)
	pygame.draw.circle(screen, CAT_NOSE, (174, 22), 1)
	lives_txt = font.render(f"x{player.lives}", True, WHITE)
	screen.blit(lives_txt, (190, 9))

	if area_kind == "underground":
		area_txt = font.render("UNDERGROUND", True, SKULL_RED_BRIGHT)
		screen.blit(area_txt, (WIDTH - area_txt.get_width() - 18, 9))

	if win:
		t2 = font.render("YOU WIN! Press R to restart", True, YELLOW)
		screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, 9))


def draw_hint(screen, font, text):
	t = font.render(text, True, WHITE)
	bg = pygame.Rect(WIDTH // 2 - t.get_width() // 2 - 10, HEIGHT - 46, t.get_width() + 20, 30)
	pygame.draw.rect(screen, (15, 15, 20), bg, border_radius=6)
	screen.blit(t, (bg.x + 10, bg.y + 5))


def reset_game():
	player = Player(80, 470)
	levels = {
		"surface": build_surface_level(),
		"underground": build_underground_level(),
	}
	return player, levels


def main():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Mini Mario - Pygame")
	clock = pygame.time.Clock()
	font = pygame.font.SysFont("consolas", 26)
	small_font = pygame.font.SysFont("consolas", 18)
	block_font = pygame.font.SysFont("consolas", 20, bold=True)

	player, levels = reset_game()
	clouds, hills, bushes = generate_background(levels["surface"]["world_width"])
	current_key = "surface"
	entry_pipe_x = None
	win = False

	while True:
		dt = clock.tick(FPS)
		keys = pygame.key.get_pressed()

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN and event.key == pygame.K_r and (win or player.lives <= 0):
				player, levels = reset_game()
				current_key = "surface"
				entry_pipe_x = None
				win = False

		lvl = levels[current_key]
		teleported = False
		hint = None

		if not win and player.lives > 0:
			if current_key == "surface":
				for p in lvl["pipes"]:
					standing = player.on_ground and p.left + 6 < player.rect.centerx < p.right - 6 and abs(player.rect.bottom - p.top) <= 3
					if standing:
						hint = "Press DOWN to go underground"
						if keys[pygame.K_DOWN] or keys[pygame.K_s]:
							entry_pipe_x = p.x
							current_key = "underground"
							lvl = levels[current_key]
							player.rect.topleft = lvl["spawn"]
							player.vx = 0
							player.vy = 0
							player.on_ground = True
							teleported = True
						break
			else:
				p = lvl["exit_pipe"]
				standing = p and player.on_ground and p.left + 6 < player.rect.centerx < p.right - 6 and abs(player.rect.bottom - p.top) <= 3
				if standing:
					hint = "Press UP to return to the surface"
					if keys[pygame.K_UP] or keys[pygame.K_w]:
						current_key = "surface"
						lvl = levels[current_key]
						rx = (entry_pipe_x + 90) if entry_pipe_x is not None else lvl["spawn"][0]
						player.rect.midbottom = (rx, lvl["ground_y"])
						player.vx = 0
						player.vy = 0
						player.on_ground = True
						teleported = True

		if not win and player.lives > 0 and not teleported:
			player.input()
			player.apply_gravity()
			player.move_and_collide(lvl["solids"])

			if player.invuln_timer > 0:
				player.invuln_timer -= 1

			if lvl["ground_rect"] and player.rect.colliderect(lvl["ground_rect"]) and player.invuln_timer == 0:
				player.lives -= 1
				player.invuln_timer = 90
				player.rect.topleft = lvl["spawn"]
				player.vx = 0
				player.vy = 0

			for coin in lvl["coins"]:
				coin.update()
				if not coin.collected and player.rect.colliderect(coin.rect):
					coin.collected = True
					player.coins += 1

			for enemy in lvl["enemies"]:
				enemy.update()
				if not enemy.alive:
					continue

				if player.rect.colliderect(enemy.rect):
					# Stomp enemy from above.
					if player.vy > 0 and player.rect.bottom - enemy.rect.top < 18:
						enemy.alive = False
						player.vy = -9
					elif player.invuln_timer == 0:
						player.lives -= 1
						player.invuln_timer = 90
						player.rect.topleft = lvl["spawn"]
						player.vx = 0
						player.vy = 0

			if lvl["flag_rect"] and player.rect.colliderect(lvl["flag_rect"]):
				win = True

			if player.rect.top > HEIGHT + 120:
				player.lives -= 1
				player.rect.topleft = lvl["spawn"]
				player.vx = 0
				player.vy = 0
				player.invuln_timer = 90

		cam_x = int(player.rect.centerx - WIDTH * 0.35)
		cam_x = max(0, min(cam_x, lvl["world_width"] - WIDTH))

		if lvl["kind"] == "surface":
			draw_world(screen, lvl["blocks"], lvl["pipes"], lvl["ground_y"], cam_x, clouds, hills, bushes, block_font)
		else:
			draw_underground(screen, lvl["blocks"], lvl["pipes"], lvl["ground_y"], lvl["ceiling_y"], cam_x, block_font)

		for coin in lvl["coins"]:
			coin.draw(screen, cam_x)
		for enemy in lvl["enemies"]:
			enemy.draw(screen, cam_x)
		if lvl["flag_rect"]:
			draw_flag(screen, lvl["flag_rect"], cam_x)
		player.draw(screen, cam_x)
		draw_hud(screen, font, player, win, lvl["kind"])

		if hint:
			draw_hint(screen, small_font, hint)

		if player.lives <= 0:
			over = font.render("GAME OVER - Press R to restart", True, WHITE)
			screen.blit(over, (WIDTH // 2 - over.get_width() // 2, HEIGHT // 2 - 20))

		pygame.display.flip()


if __name__ == "__main__":
	main()
