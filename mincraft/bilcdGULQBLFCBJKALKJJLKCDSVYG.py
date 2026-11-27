import random
import sys

import pygame


WIDTH, HEIGHT = 1200, 760
FPS = 60

WORLD_W = 60
WORLD_H = 60
MIN_HEIGHT = -6
MAX_HEIGHT = 7

TILE_W = 48
TILE_H = 24
BLOCK_H = 24

SKY_COLOR = (141, 197, 255)
PLAYER_COLOR = (255, 60, 60)
PLAYER_SKIN = (242, 198, 160)
PLAYER_SHIRT = (48, 96, 214)
PLAYER_PANTS = (60, 60, 90)
PLAYER_SHOES = (35, 35, 35)

BLOCK_TYPES = {
	"grass": {
		"top": (118, 184, 82),
		"left": (95, 150, 67),
		"right": (73, 126, 50),
	},
	"dirt": {
		"top": (155, 119, 78),
		"left": (130, 94, 58),
		"right": (110, 76, 46),
	},
	"stone": {
		"top": (167, 167, 167),
		"left": (137, 137, 137),
		"right": (114, 114, 114),
	},
	"sand": {
		"top": (229, 216, 148),
		"left": (205, 189, 126),
		"right": (185, 167, 105),
	},
	"wood": {
		"top": (173, 126, 83),
		"left": (145, 101, 62),
		"right": (122, 80, 47),
	},
	"leaves": {
		"top": (78, 160, 74),
		"left": (62, 133, 56),
		"right": (48, 112, 45),
	},
	"brick": {
		"top": (195, 93, 76),
		"left": (164, 70, 56),
		"right": (141, 53, 42),
	},
	"diamond_ore": {
		"top": (115, 180, 194),
		"left": (92, 151, 166),
		"right": (70, 123, 139),
	},
	"tnt": {
		"top": (180, 80, 80),
		"left": (150, 60, 60),
		"right": (120, 40, 40),
	},
}

PALETTE_KEYS = [
	(pygame.K_1, "grass"),
	(pygame.K_2, "dirt"),
	(pygame.K_3, "stone"),
	(pygame.K_4, "sand"),
	(pygame.K_5, "wood"),
	(pygame.K_6, "tnt"),
]


def clamp(value, lo, hi):
	return max(lo, min(hi, value))


def generate_world(width, height):
	heights = [[0 for _ in range(height)] for _ in range(width)]
	blocks = [["grass" for _ in range(height)] for _ in range(width)]

	base = random.randint(0, 3)
	for x in range(width):
		for y in range(height):
			if x == 0 and y == 0:
				heights[x][y] = base
			elif x == 0:
				heights[x][y] = heights[x][y - 1]
			elif y == 0:
				heights[x][y] = heights[x - 1][y]
			else:
				avg = (heights[x - 1][y] + heights[x][y - 1]) // 2
				heights[x][y] = avg

			heights[x][y] += random.choice([-1, 0, 0, 0, 1])
			heights[x][y] = clamp(heights[x][y], MIN_HEIGHT, MAX_HEIGHT)

			h = heights[x][y]
			if h <= -1:
				blocks[x][y] = "sand"
			elif h >= 5:
				blocks[x][y] = "stone"
			else:
				blocks[x][y] = "grass"

	return heights, blocks


def area_is_flat(heights, sx, sy, w, h, tolerance=0):
	base = heights[sx][sy]
	for x in range(sx, sx + w):
		for y in range(sy, sy + h):
			if abs(heights[x][y] - base) > tolerance:
				return False
	return True


def can_place_reserved(reserved, sx, sy, w, h, padding=0):
	for x in range(sx - padding, sx + w + padding):
		for y in range(sy - padding, sy + h + padding):
			if (x, y) in reserved:
				return False
	return True


def mark_reserved(reserved, sx, sy, w, h, padding=0):
	for x in range(sx - padding, sx + w + padding):
		for y in range(sy - padding, sy + h + padding):
			reserved.add((x, y))


def generate_caves(heights, blocks, reserved, count=6):
	caves = []
	attempts = 0
	while len(caves) < count and attempts < 300:
		attempts += 1
		cx = random.randint(3, WORLD_W - 4)
		cy = random.randint(3, WORLD_H - 4)

		if not can_place_reserved(reserved, cx - 1, cy - 1, 3, 3, padding=2):
			continue

		for dx in range(-1, 2):
			for dy in range(-1, 2):
				tx = cx + dx
				ty = cy + dy
				if 0 <= tx < WORLD_W and 0 <= ty < WORLD_H:
					heights[tx][ty] = max(MIN_HEIGHT, heights[tx][ty] - random.randint(3, 6))
					blocks[tx][ty] = "stone"

		caves.append((cx, cy))
		mark_reserved(reserved, cx - 1, cy - 1, 3, 3, padding=2)

	return caves


def generate_diamonds(heights, extra_blocks, count=24):
	placed = 0
	attempts = 0
	while placed < count and attempts < 1200:
		attempts += 1
		x = random.randint(0, WORLD_W - 1)
		y = random.randint(0, WORLD_H - 1)
		if heights[x][y] > -2:
			continue

		depth = random.randint(1, 3)
		z = heights[x][y] - depth
		if z < MIN_HEIGHT:
			z = MIN_HEIGHT
		add_extra_block(extra_blocks, x, y, z, "diamond_ore")
		placed += 1


def add_extra_block(extra_blocks, x, y, z, block_type):
	if 0 <= x < WORLD_W and 0 <= y < WORLD_H:
		extra_blocks[(x, y, z)] = block_type


def top_height_at(x, y, heights, extra_blocks):
	top = heights[x][y]
	for bx, by, bz in extra_blocks:
		if bx == x and by == y and bz > top:
			top = bz
	return top


def generate_trees(heights, blocks, reserved, extra_blocks, count=45):
	placed = 0
	attempts = 0
	while placed < count and attempts < 1200:
		attempts += 1
		x = random.randint(1, WORLD_W - 2)
		y = random.randint(1, WORLD_H - 2)

		if (x, y) in reserved:
			continue
		if blocks[x][y] not in ("grass", "dirt"):
			continue

		trunk_h = random.randint(2, 4)
		ground = heights[x][y]

		for i in range(trunk_h):
			add_extra_block(extra_blocks, x, y, ground + 1 + i, "wood")

		leaf_z = ground + trunk_h + 1
		leaf_offsets = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
		for dx, dy in leaf_offsets:
			add_extra_block(extra_blocks, x + dx, y + dy, leaf_z, "leaves")

		mark_reserved(reserved, x, y, 1, 1, padding=1)
		placed += 1


def generate_houses(heights, blocks, reserved, extra_blocks, count=4):
	placed = 0
	attempts = 0
	while placed < count and attempts < 900:
		attempts += 1
		w = random.randint(3, 5)
		h = random.randint(3, 5)
		sx = random.randint(1, WORLD_W - w - 2)
		sy = random.randint(1, WORLD_H - h - 2)

		if not can_place_reserved(reserved, sx, sy, w, h, padding=2):
			continue
		if not area_is_flat(heights, sx, sy, w, h, tolerance=1):
			continue

		base = heights[sx][sy]
		for x in range(sx, sx + w):
			for y in range(sy, sy + h):
				heights[x][y] = base
				blocks[x][y] = "dirt"

		door_x = sx + (w // 2)
		door_y = sy + h - 1
		wall_h = random.randint(2, 3)

		for x in range(sx, sx + w):
			for y in range(sy, sy + h):
				on_edge = x in (sx, sx + w - 1) or y in (sy, sy + h - 1)
				for z in range(base + 1, base + wall_h + 1):
					if on_edge and (x, y) == (door_x, door_y) and z <= base + 2:
						continue
					if on_edge:
						add_extra_block(extra_blocks, x, y, z, "brick")

		roof_z = base + wall_h + 1
		for x in range(sx, sx + w):
			for y in range(sy, sy + h):
				add_extra_block(extra_blocks, x, y, roof_z, "wood")

		mark_reserved(reserved, sx, sy, w, h, padding=2)
		placed += 1


def iso_to_screen(ix, iy, iz, cam_x, cam_y):
	sx = (ix - iy) * (TILE_W // 2) + cam_x
	sy = (ix + iy) * (TILE_H // 2) - iz * BLOCK_H + cam_y
	return sx, sy


def top_polygon(ix, iy, iz, cam_x, cam_y):
	cx, cy = iso_to_screen(ix, iy, iz, cam_x, cam_y)
	return [
		(cx, cy - TILE_H // 2),
		(cx + TILE_W // 2, cy),
		(cx, cy + TILE_H // 2),
		(cx - TILE_W // 2, cy),
	]


def left_polygon(ix, iy, iz, cam_x, cam_y):
	top = top_polygon(ix, iy, iz, cam_x, cam_y)
	return [
		top[3],
		top[2],
		(top[2][0], top[2][1] + BLOCK_H),
		(top[3][0], top[3][1] + BLOCK_H),
	]


def right_polygon(ix, iy, iz, cam_x, cam_y):
	top = top_polygon(ix, iy, iz, cam_x, cam_y)
	return [
		top[1],
		top[2],
		(top[2][0], top[2][1] + BLOCK_H),
		(top[1][0], top[1][1] + BLOCK_H),
	]


def draw_block(screen, ix, iy, iz, block_type, cam_x, cam_y):
	style = BLOCK_TYPES[block_type]

	left = left_polygon(ix, iy, iz, cam_x, cam_y)
	right = right_polygon(ix, iy, iz, cam_x, cam_y)
	top = top_polygon(ix, iy, iz, cam_x, cam_y)

	pygame.draw.polygon(screen, style["left"], left)
	pygame.draw.polygon(screen, style["right"], right)
	pygame.draw.polygon(screen, style["top"], top)

	edge = (30, 30, 30)
	pygame.draw.polygon(screen, edge, left, 1)
	pygame.draw.polygon(screen, edge, right, 1)
	pygame.draw.polygon(screen, edge, top, 1)


def draw_cave_mouth(screen, x, y, heights, cam_x, cam_y):
	top = top_polygon(x, y, heights[x][y], cam_x, cam_y)
	center_x = int(sum(p[0] for p in top) / 4)
	center_y = int(sum(p[1] for p in top) / 4)
	pygame.draw.ellipse(screen, (20, 20, 20), (center_x - 10, center_y - 6, 20, 12))


def draw_player(screen, center_x, center_y):
	blocks = [
		(pygame.Rect(center_x - 12, center_y - 36, 24, 12), PLAYER_SKIN),
		(pygame.Rect(center_x - 16, center_y - 24, 32, 12), PLAYER_SKIN),
		(pygame.Rect(center_x - 12, center_y - 12, 24, 24), PLAYER_SHIRT),
		(pygame.Rect(center_x - 20, center_y - 12, 8, 24), PLAYER_SKIN),
		(pygame.Rect(center_x + 12, center_y - 12, 8, 24), PLAYER_SKIN),
		(pygame.Rect(center_x - 12, center_y + 12, 10, 24), PLAYER_PANTS),
		(pygame.Rect(center_x + 2, center_y + 12, 10, 24), PLAYER_PANTS),
		(pygame.Rect(center_x - 12, center_y + 36, 10, 6), PLAYER_SHOES),
		(pygame.Rect(center_x + 2, center_y + 36, 10, 6), PLAYER_SHOES),
	]

	for rect, color in blocks:
		pygame.draw.rect(screen, color, rect)
		pygame.draw.rect(screen, (35, 35, 35), rect, 1)

	pygame.draw.rect(screen, (40, 25, 15), pygame.Rect(center_x - 6, center_y - 29, 3, 3))
	pygame.draw.rect(screen, (40, 25, 15), pygame.Rect(center_x + 3, center_y - 29, 3, 3))


def point_in_poly(point, poly):
	x, y = point
	inside = False
	j = len(poly) - 1
	for i in range(len(poly)):
		xi, yi = poly[i]
		xj, yj = poly[j]
		intersects = (yi > y) != (yj > y)
		if intersects:
			x_on_edge = (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi
			if x < x_on_edge:
				inside = not inside
		j = i
	return inside


def pick_tile(mouse_pos, render_order, cam_x, cam_y, heights, extra_blocks):
	# Check from front to back so the closest drawn top wins.
	for x, y in reversed(render_order):
		z = top_height_at(x, y, heights, extra_blocks)
		top = top_polygon(x, y, z, cam_x, cam_y)
		if point_in_poly(mouse_pos, top):
			return x, y
	return None


def get_follow_camera(player_x, player_y, player_z):
	half_w = TILE_W // 2
	half_h = TILE_H // 2

	cam_x = WIDTH // 2 - (player_x - player_y) * half_w
	cam_y = HEIGHT // 2 + 80 - ((player_x + player_y) * half_h - player_z * BLOCK_H)
	return cam_x, cam_y


def try_move_player(player_x, player_y, dx, dy, heights, extra_blocks):
	nx = clamp(player_x + dx, 0, WORLD_W - 1)
	ny = clamp(player_y + dy, 0, WORLD_H - 1)
	from_h = top_height_at(player_x, player_y, heights, extra_blocks)
	to_h = top_height_at(nx, ny, heights, extra_blocks)

	# Limit step height difference for a more game-like movement feel.
	if abs(to_h - from_h) <= 1:
		return nx, ny
	return player_x, player_y


def get_top_extra_z(x, y, heights, extra_blocks):
	ground = heights[x][y]
	top_z = None
	for bx, by, bz in extra_blocks:
		if bx == x and by == y and bz > ground:
			if top_z is None or bz > top_z:
				top_z = bz
	return top_z


def explode_tnt(tx, ty, tz, extra_blocks, heights, inventory, radius=3):
	to_remove = []
	for bx, by, bz in extra_blocks:
		dist = abs(bx - tx) + abs(by - ty) + abs(bz - tz)
		if dist <= radius and (bx, by, bz) != (tx, ty, tz):
			to_remove.append((bx, by, bz))

	for key in to_remove:
		removed = extra_blocks.pop(key, None)
		if removed is not None:
			if removed == "diamond_ore":
				inventory["diamond"] = inventory.get("diamond", 0) + 1
			else:
				inventory[removed] = inventory.get(removed, 0) + 1

	extra_blocks.pop((tx, ty, tz), None)


def target_tile_from_direction(player_x, player_y, player_dir):
	dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
	dx, dy = dirs[player_dir]
	tx = clamp(player_x + dx, 0, WORLD_W - 1)
	ty = clamp(player_y + dy, 0, WORLD_H - 1)
	return tx, ty


def break_target_block(tx, ty, heights, blocks, extra_blocks, inventory):
	top_extra_z = get_top_extra_z(tx, ty, heights, extra_blocks)
	if top_extra_z is not None:
		if extra_blocks.get((tx, ty, top_extra_z)) == "tnt":
			explode_tnt(tx, ty, top_extra_z, extra_blocks, heights, inventory)
		else:
			removed = extra_blocks.pop((tx, ty, top_extra_z), None)
			if removed is not None:
				if removed == "diamond_ore":
					inventory["diamond"] = inventory.get("diamond", 0) + 1
				else:
					inventory[removed] = inventory.get(removed, 0) + 1
		return

	if heights[tx][ty] > MIN_HEIGHT:
		inventory[blocks[tx][ty]] = inventory.get(blocks[tx][ty], 0) + 1
		heights[tx][ty] -= 1
		if heights[tx][ty] <= -1:
			blocks[tx][ty] = "sand"
		elif heights[tx][ty] >= 5:
			blocks[tx][ty] = "stone"
		else:
			blocks[tx][ty] = "dirt"


def place_target_block(tx, ty, selected_type, heights, extra_blocks, inventory):
	if inventory.get(selected_type, 0) <= 0:
		return
	place_z = top_height_at(tx, ty, heights, extra_blocks) + 1
	extra_blocks[(tx, ty, place_z)] = selected_type
	inventory[selected_type] -= 1


def draw_ui(screen, font, selected_type, inventory):
	hint = "WASD/Arrows=Move | E/Space/F=Break | R/Enter/G=Place | 1-6=Select"
	label = font.render(hint, True, (20, 20, 20))
	screen.blit(label, (16, 12))

	selected_count = inventory.get(selected_type, 0)
	palette = "Selected: " + selected_type.upper() + " | Count: " + str(selected_count)
	ptxt = font.render(palette, True, (20, 20, 20))
	screen.blit(ptxt, (16, 40))

	counts = "1:grass {}  2:dirt {}  3:stone {}  4:sand {}  5:wood {}  6:TNT {}  diamonds {}".format(
		inventory.get("grass", 0),
		inventory.get("dirt", 0),
		inventory.get("stone", 0),
		inventory.get("sand", 0),
		inventory.get("wood", 0),
		inventory.get("tnt", 0),
		inventory.get("diamond", 0),
	)
	ctxt = font.render(counts, True, (20, 20, 20))
	screen.blit(ctxt, (16, 68))


def draw_game():
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	pygame.display.set_caption("Minecraft Style Sandbox")
	clock = pygame.time.Clock()
	font = pygame.font.SysFont("arial", 22)

	heights, blocks = generate_world(WORLD_W, WORLD_H)
	extra_blocks = {}
	reserved = set()
	caves = generate_caves(heights, blocks, reserved)
	generate_diamonds(heights, extra_blocks)
	generate_houses(heights, blocks, reserved, extra_blocks)
	generate_trees(heights, blocks, reserved, extra_blocks)

	render_order = [(x, y) for x in range(WORLD_W) for y in range(WORLD_H)]
	render_order.sort(key=lambda pos: pos[0] + pos[1])
	
	player_x = WORLD_W // 2
	player_y = WORLD_H // 2
	cam_x, cam_y = get_follow_camera(player_x, player_y, top_height_at(player_x, player_y, heights, extra_blocks))
	selected_type = "grass"
	inventory = {name: 0 for name in BLOCK_TYPES}
	inventory["grass"] = 20
	inventory["dirt"] = 20
	inventory["stone"] = 20
	inventory["wood"] = 10
	inventory["tnt"] = 5
	player_dir = 0

	running = True
	while running:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False

			if event.type == pygame.KEYDOWN:
				for key, btype in PALETTE_KEYS:
					if event.key == key:
						selected_type = btype

				if event.key in (pygame.K_a, pygame.K_LEFT):
					player_x, player_y = try_move_player(player_x, player_y, -1, 0, heights, extra_blocks)
					player_dir = 0
				if event.key in (pygame.K_d, pygame.K_RIGHT):
					player_x, player_y = try_move_player(player_x, player_y, 1, 0, heights, extra_blocks)
					player_dir = 1
				if event.key in (pygame.K_w, pygame.K_UP):
					player_x, player_y = try_move_player(player_x, player_y, 0, -1, heights, extra_blocks)
					player_dir = 2
				if event.key in (pygame.K_s, pygame.K_DOWN):
					player_x, player_y = try_move_player(player_x, player_y, 0, 1, heights, extra_blocks)
					player_dir = 3

				if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_f):
					tx, ty = target_tile_from_direction(player_x, player_y, player_dir)
					break_target_block(tx, ty, heights, blocks, extra_blocks, inventory)

				if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_g):
					tx, ty = target_tile_from_direction(player_x, player_y, player_dir)
					place_target_block(tx, ty, selected_type, heights, extra_blocks, inventory)

		cam_x, cam_y = get_follow_camera(player_x, player_y, top_height_at(player_x, player_y, heights, extra_blocks))
		screen.fill(SKY_COLOR)

		for x, y in render_order:
			draw_block(screen, x, y, heights[x][y], blocks[x][y], cam_x, cam_y)

		extra_draw = sorted(extra_blocks.items(), key=lambda item: (item[0][0] + item[0][1], item[0][2]))
		for (x, y, z), btype in extra_draw:
			draw_block(screen, x, y, z, btype, cam_x, cam_y)

		for x, y in caves:
			draw_cave_mouth(screen, x, y, heights, cam_x, cam_y)

		dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
		dx, dy = dirs[player_dir]
		front_x = clamp(player_x + dx, 0, WORLD_W - 1)
		front_y = clamp(player_y + dy, 0, WORLD_H - 1)
		hz = top_height_at(front_x, front_y, heights, extra_blocks)
		outline = top_polygon(front_x, front_y, hz, cam_x, cam_y)
		pygame.draw.polygon(screen, (200, 200, 100), outline, 3)

		player_pos = iso_to_screen(player_x, player_y, top_height_at(player_x, player_y, heights, extra_blocks) + 1, cam_x, cam_y)
		draw_player(screen, player_pos[0], player_pos[1])

		draw_ui(screen, font, selected_type, inventory)

		pygame.display.flip()
		clock.tick(FPS)

	pygame.quit()
	sys.exit()


if __name__ == "__main__":
	draw_game()
