from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import json
import math
from pathlib import Path
import random
import time as pytime


app = Ursina()
window.title = 'Python Minecraft'
window.borderless = False
window.exit_button.visible = False
window.fps_counter.enabled = True

WORLD_SIZE = 24
TREE_COUNT = 18
WATER_LEVEL = 3
MAX_BUILD_HEIGHT = 18
INTERACTION_DISTANCE = 8
MOVE_SPEED = 5
ANIMAL_COUNT = 8
MONSTER_COUNT = 6
ATTACK_DISTANCE = 4
PLAYER_MAX_HEALTH = 100
MINE_INTERVAL = 0.12
SAVE_FILE = Path(__file__).with_name('12345678901234567890_save.json')

BLOCK_TYPES = {
	'grass': {'texture': 'grass', 'color': color.color(0, 0, 1)},
	'dirt': {'texture': 'white_cube', 'color': color.rgb(120, 72, 40)},
	'stone': {'texture': 'white_cube', 'color': color.rgb(140, 140, 140)},
	'sand': {'texture': 'white_cube', 'color': color.rgb(232, 214, 141)},
	'wood': {'texture': 'white_cube', 'color': color.rgb(111, 78, 55)},
	'leaves': {'texture': 'white_cube', 'color': color.rgba(72, 150, 76, 220)},
	'water': {'texture': 'white_cube', 'color': color.rgba(50, 120, 220, 170)},
}

INVENTORY_ORDER = ['grass', 'dirt', 'stone', 'sand', 'wood', 'leaves', 'water']
STARTING_INVENTORY = {
	'grass': 20,
	'dirt': 20,
	'stone': 18,
	'sand': 12,
	'wood': 12,
	'leaves': 10,
	'water': 8,
}

current_block = INVENTORY_ORDER[0]
selected_slot = 0
voxels = {}
placed_blocks = {}
removed_blocks = set()
inventory = STARTING_INVENTORY.copy()
player = None
hand = None
crosshair = None
block_label = None
help_label = None
health_bar = None
health_text = None
save_text = None
player_health = PLAYER_MAX_HEALTH
animals = []
monsters = []
inventory_slot_frames = []
inventory_slot_texts = []
last_damage_time = 0.0
last_mine_time = 0.0


class Voxel(Entity):
	def __init__(self, position=(0, 0, 0), block_type='grass'):
		block_data = BLOCK_TYPES[block_type]
		super().__init__(
			parent=scene,
			position=position,
			model='cube',
			origin_y=0.5,
			texture=block_data['texture'],
			color=block_data['color'],
			scale=1,
			collider='box',
		)
		self.block_type = block_type


class Animal(Entity):
	def __init__(self, position=(0, 0, 0)):
		super().__init__(
			parent=scene,
			position=position,
			model='cube',
			color=color.rgb(240, 240, 240),
			scale=(0.9, 0.9, 1.2),
			collider='box',
		)
		self.health = 3
		self.speed = random.uniform(0.7, 1.2)
		self.change_direction_time = 0
		self.move_direction = Vec3(0, 0, 0)
		self.head = Entity(parent=self, model='cube', color=color.rgb(248, 248, 248), position=(0, 0.45, 0.52), scale=(0.55, 0.5, 0.55))

	def take_damage(self, amount):
		self.health -= amount
		self.color = color.rgb(255, 180, 180)
		invoke(self.reset_color, delay=0.12)
		if self.health <= 0:
			if self in animals:
				animals.remove(self)
			heal_player(6)
			destroy(self)

	def reset_color(self):
		if self:
			self.color = color.rgb(240, 240, 240)

	def step(self):
		self.change_direction_time -= time.dt
		if self.change_direction_time <= 0:
			self.change_direction_time = random.uniform(1.5, 3.5)
			candidate = Vec3(random.uniform(-1, 1), 0, random.uniform(-1, 1))
			self.move_direction = candidate.normalized() if candidate.length() > 0 else Vec3(0, 0, 0)

		next_position = self.position + self.move_direction * self.speed * time.dt
		if abs(next_position.x) > WORLD_SIZE - 1 or abs(next_position.z) > WORLD_SIZE - 1:
			self.move_direction *= -1
			return

		ground_y = surface_y(round(next_position.x), round(next_position.z)) + 1
		if is_water_surface(round(next_position.x), round(next_position.z)):
			return
		self.position = Vec3(next_position.x, ground_y, next_position.z)
		if self.move_direction.length() > 0:
			self.look_at(self.position + self.move_direction)
			self.rotation_x = 0


class Monster(Entity):
	def __init__(self, position=(0, 0, 0)):
		super().__init__(
			parent=scene,
			position=position,
			model='cube',
			color=color.rgb(60, 150, 70),
			scale=(0.95, 1.8, 0.95),
			collider='box',
		)
		self.health = 5
		self.speed = random.uniform(1.4, 2.0)
		self.attack_cooldown = random.uniform(0.4, 0.9)
		self.head = Entity(parent=self, model='cube', color=color.rgb(70, 170, 80), position=(0, 0.62, 0), scale=(0.72, 0.52, 0.72))

	def take_damage(self, amount):
		self.health -= amount
		self.color = color.rgb(180, 240, 180)
		invoke(self.reset_color, delay=0.12)
		if self.health <= 0:
			if self in monsters:
				monsters.remove(self)
			destroy(self)

	def reset_color(self):
		if self:
			self.color = color.rgb(60, 150, 70)

	def step(self):
		direction = player.position - self.position
		direction.y = 0
		distance_to_player = direction.length()

		if distance_to_player > 0.1:
			move_direction = direction.normalized()
			if distance_to_player > 1.6:
				next_position = self.position + move_direction * self.speed * time.dt
				if not is_water_surface(round(next_position.x), round(next_position.z)):
					ground_y = surface_y(round(next_position.x), round(next_position.z)) + 1
					self.position = Vec3(next_position.x, ground_y, next_position.z)
			self.look_at(player.position)
			self.rotation_x = 0

		self.attack_cooldown -= time.dt
		if distance_to_player < 1.9 and self.attack_cooldown <= 0:
			damage_player(8)
			self.attack_cooldown = random.uniform(0.7, 1.1)


def serialize_position(position):
	return [int(position[0]), int(position[1]), int(position[2])]


def deserialize_position(raw_position):
	return (int(raw_position[0]), int(raw_position[1]), int(raw_position[2]))


def height_at(x, z):
	base = math.sin(x * 0.22) * 1.7 + math.cos(z * 0.19) * 1.4
	detail = math.sin((x + z) * 0.11) * 0.8
	return max(1, int(round(base + detail + 3)))


def cave_at(x, y, z):
	value = math.sin(x * 0.31) + math.cos(z * 0.27) + math.sin(y * 0.78)
	return 1 < y < 6 and value > 2.15


def is_water_surface(x, z):
	return height_at(x, z) < WATER_LEVEL


def surface_y(x, z):
	return WATER_LEVEL if is_water_surface(x, z) else height_at(x, z)


def ground_type(height):
	if height <= WATER_LEVEL + 1:
		return 'sand'
	if height >= 6:
		return 'stone'
	return 'grass'


def add_block(position, block_type, track_change=False):
	if position in voxels:
		destroy(voxels[position])

	voxel = Voxel(position=position, block_type=block_type)
	voxels[position] = voxel

	if track_change:
		placed_blocks[position] = block_type
		removed_blocks.discard(position)


def remove_block(position, add_to_inventory=False, track_change=False):
	voxel = voxels.pop(position, None)
	if not voxel:
		return

	block_type = voxel.block_type
	destroy(voxel)

	if add_to_inventory and block_type in inventory:
		inventory[block_type] += 1
		refresh_inventory_ui()

	if track_change:
		if position in placed_blocks:
			placed_blocks.pop(position, None)
		else:
			removed_blocks.add(position)


def generate_tree(base_x, base_y, base_z):
	trunk_height = random.randint(3, 4)
	for y in range(base_y + 1, base_y + 1 + trunk_height):
		add_block((base_x, y, base_z), 'wood')

	top_y = base_y + trunk_height
	for offset_x in range(-2, 3):
		for offset_z in range(-2, 3):
			for offset_y in range(0, 3):
				distance = abs(offset_x) + abs(offset_z) + offset_y
				if distance <= 4:
					leaf_position = (base_x + offset_x, top_y + offset_y, base_z + offset_z)
					if leaf_position not in voxels:
						add_block(leaf_position, 'leaves')


def clear_world():
	for voxel in list(voxels.values()):
		destroy(voxel)
	voxels.clear()


def generate_world():
	clear_world()
	random.seed(7)

	for z in range(-WORLD_SIZE, WORLD_SIZE + 1):
		for x in range(-WORLD_SIZE, WORLD_SIZE + 1):
			top_y = height_at(x, z)
			top_block = ground_type(top_y)
			column_top = max(top_y, WATER_LEVEL)

			for y in range(0, column_top + 1):
				if y <= top_y:
					if cave_at(x, y, z):
						continue
					if y == top_y:
						block_type = top_block
					elif y >= top_y - 2:
						block_type = 'dirt' if top_block not in ('sand', 'stone') else top_block
					else:
						block_type = 'stone'
				else:
					block_type = 'water'
				add_block((x, y, z), block_type)

	tree_spots = 0
	attempts = 0
	while tree_spots < TREE_COUNT and attempts < TREE_COUNT * 8:
		attempts += 1
		x = random.randint(-WORLD_SIZE + 3, WORLD_SIZE - 3)
		z = random.randint(-WORLD_SIZE + 3, WORLD_SIZE - 3)
		y = height_at(x, z)
		if ground_type(y) != 'grass' or is_water_surface(x, z):
			continue
		if abs(x) < 4 and abs(z) < 4:
			continue
		generate_tree(x, y, z)
		tree_spots += 1


def update_health_ui():
	if health_bar:
		health_bar.scale_x = max(0, player_health / PLAYER_MAX_HEALTH) * 0.34
	if health_text:
		health_text.text = f'Health: {player_health}/{PLAYER_MAX_HEALTH}'


def damage_player(amount):
	global player_health, last_damage_time
	if pytime.time() - last_damage_time < 0.2:
		return
	last_damage_time = pytime.time()
	player_health = max(0, player_health - amount)
	update_health_ui()
	if player_health == 0:
		respawn_player()


def heal_player(amount):
	global player_health
	player_health = min(PLAYER_MAX_HEALTH, player_health + amount)
	update_health_ui()


def respawn_player():
	global player_health
	player.position = Vec3(0, surface_y(0, 0) + 3, 0)
	player_health = PLAYER_MAX_HEALTH
	update_health_ui()


def random_land_position(min_distance=0):
	for _ in range(100):
		x = random.randint(-WORLD_SIZE + 2, WORLD_SIZE - 2)
		z = random.randint(-WORLD_SIZE + 2, WORLD_SIZE - 2)
		if abs(x) < min_distance and abs(z) < min_distance:
			continue
		if is_water_surface(x, z):
			continue
		y = surface_y(x, z) + 1
		return Vec3(x, y, z)
	return Vec3(WORLD_SIZE - 2, surface_y(WORLD_SIZE - 2, WORLD_SIZE - 2) + 1, WORLD_SIZE - 2)


def spawn_animals():
	while len(animals) < ANIMAL_COUNT:
		animals.append(Animal(position=random_land_position(min_distance=5)))


def spawn_monsters():
	while len(monsters) < MONSTER_COUNT:
		monsters.append(Monster(position=random_land_position(min_distance=10)))


def get_target_mob(entity):
	current = entity
	while current:
		if isinstance(current, (Animal, Monster)):
			return current
		current = current.parent
	return None


def update_selected_block_by_slot(slot_index):
	global current_block, selected_slot
	selected_slot = slot_index
	current_block = INVENTORY_ORDER[slot_index]
	refresh_inventory_ui()


def refresh_inventory_ui():
	if not inventory_slot_frames:
		return

	for index, block_type in enumerate(INVENTORY_ORDER):
		is_selected = index == selected_slot
		inventory_slot_frames[index].color = color.azure if is_selected else color.rgba(30, 30, 30, 220)
		inventory_slot_texts[index].text = f'{index + 1}\n{block_type}\n{inventory[block_type]}'

	if block_label:
		block_label.text = f'Block: {current_block} x{inventory[current_block]}'


def block_from_key(key):
	mapping = {
		'1': 0,
		'2': 1,
		'3': 2,
		'4': 3,
		'5': 4,
		'6': 5,
		'7': 6,
	}
	return mapping.get(key)


def swing_hand():
	if not hand.enabled:
		return
	hand.animate_rotation((20, -30, 10), duration=0.06, curve=curve.out_expo)
	hand.animate_rotation((28, -42, 14), duration=0.08, delay=0.06, curve=curve.in_out_sine)


def can_place_block(position):
	if position[1] < 0 or position[1] > MAX_BUILD_HEIGHT:
		return False
	if position in voxels:
		return False

	player_feet = (round(player.x), round(player.y - 1), round(player.z))
	player_head = (round(player.x), round(player.y), round(player.z))
	if position == player_feet or position == player_head:
		return False
	return True


def show_save_message(text_value):
	if save_text:
		save_text.text = text_value
		invoke(clear_save_message, delay=1.4)


def clear_save_message():
	if save_text:
		save_text.text = ''


def setup_ui():
	global crosshair, block_label, help_label, health_bar, health_text, save_text
	crosshair = Text(text='+', origin=(0, 0), scale=2, color=color.white)
	block_label = Text(text='', position=(-0.86, 0.45), scale=1.2, color=color.white)
	help_label = Text(
		text='WASD / Arrows move | Space jump | Hold LMB mine/attack | RMB place | 1-7 inventory | F5 save | ESC quit',
		position=(-0.86, 0.4),
		scale=1,
		color=color.light_gray,
	)
	Entity(parent=camera.ui, model='quad', color=color.black, scale=(0.36, 0.028), position=(-0.64, 0.34))
	health_bar = Entity(parent=camera.ui, model='quad', color=color.red, scale=(0.34, 0.02), position=(-0.64, 0.34), origin_x=-0.5)
	health_text = Text(text='', position=(-0.86, 0.3), scale=1.1, color=color.white)
	save_text = Text(text='', origin=(0, 0), y=0.42, scale=1.3, color=color.lime)

	slot_start_x = -0.42
	for index, block_type in enumerate(INVENTORY_ORDER):
		frame = Entity(parent=camera.ui, model='quad', scale=(0.11, 0.12), position=(slot_start_x + index * 0.13, -0.42), color=color.rgba(30, 30, 30, 220))
		label = Text(parent=frame, text='', origin=(0, 0), scale=0.75, y=0.02, color=BLOCK_TYPES[block_type]['color'])
		inventory_slot_frames.append(frame)
		inventory_slot_texts.append(label)

	update_health_ui()
	refresh_inventory_ui()


def setup_player():
	global player, hand
	player = FirstPersonController(model='cube', y=surface_y(0, 0) + 2, speed=0, origin_y=-0.5)
	player.cursor.visible = False
	player.gravity = 0.45
	player.jump_height = 1.2
	player.mouse_sensitivity = Vec2(40, 40)

	hand = Entity(
		parent=camera.ui,
		model='cube',
		color=color.rgb(214, 178, 122),
		scale=(0.18, 0.28, 0.65),
		rotation=(28, -42, 14),
		position=(0.62, -0.5),
	)


def world_hit():
	return raycast(camera.world_position, camera.forward, distance=INTERACTION_DISTANCE, ignore=(player, hand))


def try_mine_or_attack(force=False):
	global last_mine_time
	if not force and pytime.time() - last_mine_time < MINE_INTERVAL:
		return

	hit_info = world_hit()
	if not hit_info.hit:
		return

	target_mob = get_target_mob(hit_info.entity)
	if target_mob and distance(player.position, target_mob.position) <= ATTACK_DISTANCE:
		last_mine_time = pytime.time()
		target_mob.take_damage(1)
		swing_hand()
		return

	if not isinstance(hit_info.entity, Voxel):
		return

	target_position = tuple(int(value) for value in hit_info.entity.position)
	if target_position[1] <= 0:
		return

	last_mine_time = pytime.time()
	remove_block(target_position, add_to_inventory=True, track_change=True)
	swing_hand()


def try_place_block():
	if inventory[current_block] <= 0:
		show_save_message('No blocks in slot')
		return

	hit_info = world_hit()
	if not hit_info.hit or not isinstance(hit_info.entity, Voxel):
		return

	place_position = tuple(int(value) for value in (hit_info.entity.position + hit_info.normal))
	if not can_place_block(place_position):
		return

	add_block(place_position, current_block, track_change=True)
	inventory[current_block] -= 1
	refresh_inventory_ui()
	swing_hand()


def save_game(show_message=True):
	data = {
		'player_position': [float(player.x), float(player.y), float(player.z)],
		'player_health': player_health,
		'inventory': inventory,
		'selected_slot': selected_slot,
		'placed_blocks': [{'position': serialize_position(position), 'block_type': block_type} for position, block_type in placed_blocks.items()],
		'removed_blocks': [serialize_position(position) for position in sorted(removed_blocks)],
	}
	SAVE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
	if show_message:
		show_save_message('Game saved')


def load_game():
	global player_health, inventory, selected_slot, current_block
	if not SAVE_FILE.exists():
		refresh_inventory_ui()
		update_health_ui()
		return

	data = json.loads(SAVE_FILE.read_text(encoding='utf-8'))
	for raw_position in data.get('removed_blocks', []):
		position = deserialize_position(raw_position)
		removed_blocks.add(position)
		remove_block(position)

	for block_info in data.get('placed_blocks', []):
		position = deserialize_position(block_info['position'])
		block_type = block_info['block_type']
		placed_blocks[position] = block_type
		add_block(position, block_type)

	loaded_inventory = data.get('inventory', {})
	for block_type in INVENTORY_ORDER:
		inventory[block_type] = int(loaded_inventory.get(block_type, STARTING_INVENTORY[block_type]))

	selected_slot = int(data.get('selected_slot', 0))
	selected_slot = max(0, min(selected_slot, len(INVENTORY_ORDER) - 1))
	current_block = INVENTORY_ORDER[selected_slot]

	position = data.get('player_position', [0, surface_y(0, 0) + 3, 0])
	player.position = Vec3(float(position[0]), float(position[1]), float(position[2]))
	player_health = int(data.get('player_health', PLAYER_MAX_HEALTH))
	player_health = max(1, min(player_health, PLAYER_MAX_HEALTH))

	refresh_inventory_ui()
	update_health_ui()
	show_save_message('Save loaded')


def input(key):
	chosen_slot = block_from_key(key)
	if chosen_slot is not None:
		update_selected_block_by_slot(chosen_slot)
		return

	if key == 'f5':
		save_game(show_message=True)
		return

	if key == 'escape':
		save_game(show_message=False)
		application.quit()
		return

	if key == 'left mouse down':
		try_mine_or_attack(force=True)
		return

	if key == 'right mouse down':
		try_place_block()


def update():
	movement = Vec3(0, 0, 0)
	if held_keys['w'] or held_keys['up arrow']:
		movement += player.forward
	if held_keys['s'] or held_keys['down arrow']:
		movement -= player.forward
	if held_keys['d'] or held_keys['right arrow']:
		movement += player.right
	if held_keys['a'] or held_keys['left arrow']:
		movement -= player.right

	movement.y = 0
	if movement.length() > 0:
		player.position += movement.normalized() * MOVE_SPEED * time.dt

	if held_keys['left mouse']:
		try_mine_or_attack(force=False)

	for animal in list(animals):
		animal.step()

	for monster in list(monsters):
		monster.step()

	if len(animals) < ANIMAL_COUNT:
		spawn_animals()
	if len(monsters) < MONSTER_COUNT:
		spawn_monsters()

	if player.y < -20:
		respawn_player()


generate_world()
setup_player()
setup_ui()
load_game()
spawn_animals()
spawn_monsters()
Sky(color=color.rgb(120, 190, 255))
AmbientLight(color=color.rgba(180, 180, 180, 0.65))
DirectionalLight(y=2, z=3, rotation=(45, -45, 0), shadows=False)

app.run()
