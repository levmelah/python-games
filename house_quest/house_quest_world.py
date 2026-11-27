from ursina import *

EXTERIOR_ORIGIN = Vec3(0, 0, 0)
EXTERIOR_SPAWN = Vec3(0, 1, -10)
INTERIOR_ORIGIN = Vec3(0, 0, -60)
INTERIOR_SPAWN = INTERIOR_ORIGIN + Vec3(0, 1, -4)
MAZE_ORIGIN = Vec3(0, -6, -160)
MAZE_SPAWN = MAZE_ORIGIN + Vec3(0, 2.5, -8)
MAZE_FALL_Y = MAZE_ORIGIN.y - 4

WALL_COLOR = color.rgb(200, 190, 170)
WOOD_COLOR = color.rgb(110, 80, 55)


def build_lighting_and_sky():
    Sky(color=color.rgb(10, 12, 28))
    AmbientLight(color=color.rgba(100 / 255, 110 / 255, 150 / 255, 1))
    moon = DirectionalLight(shadows=True)
    moon.look_at(Vec3(1, -2, 1))
    moon.color = color.rgba(180 / 255, 195 / 255, 255 / 255, 1)


def build_exterior():
    ground = Entity(model='plane', scale=40, position=EXTERIOR_ORIGIN, color=color.rgb(28, 38, 28), collider='box')

    house_walls = [
        ('cube', (10.6, 3, 0.3), (0, 1.5, 5)),
        ('cube', (3.5, 3, 0.3), (-3.25, 1.5, -5)),
        ('cube', (3.5, 3, 0.3), (3.25, 1.5, -5)),
        ('cube', (0.3, 3, 10), (5, 1.5, 0)),
        ('cube', (0.3, 3, 10), (-5, 1.5, 0)),
        ('cube', (11, 0.3, 11), (0, 3.15, 0)),
    ]
    for model_name, scale, pos in house_walls:
        Entity(model=model_name, scale=scale, position=pos, color=WALL_COLOR, collider='box')

    door = Entity(model='cube', scale=(3, 2.8, 0.2), position=(-1.5, 1.4, -5), color=color.rgb(92, 56, 34), collider='box')

    post = Entity(model='cube', scale=(0.12, 1, 0.12), position=(2.2, 0.5, -6.5), color=color.rgb(70, 42, 26))
    mailbox_body = Entity(model='cube', scale=(0.65, 0.42, 0.42), position=(2.2, 1.05, -6.75), color=color.rgb(46, 90, 64), collider='box')
    mailbox_flap = Entity(model='cube', scale=(0.6, 0.06, 0.38), position=(2.2, 1.18, -6.54), color=color.rgb(32, 68, 48))
    key = Entity(model='cube', scale=(0.35, 0.08, 0.2), position=(2.2, 1.0, -6.6), color=color.rgb(255, 215, 0), collider='box', enabled=False)

    lamp = Entity(model='sphere', scale=0.25, position=(2.5, 2.7, -5.2), color=color.rgb(255, 233, 170))

    return {
        'door': door,
        'mailbox_body': mailbox_body,
        'mailbox_flap': mailbox_flap,
        'key': key,
        'ground': ground,
        'lamp': lamp,
    }


def build_interior():
    floor = Entity(model='plane', scale=14, position=INTERIOR_ORIGIN, color=color.rgb(98, 78, 56), collider='box')

    wall_h = 3
    fence = [
        ('cube', (14.6, wall_h, 0.3), (0, 1.5, 7)),
        ('cube', (14.6, wall_h, 0.3), (0, 1.5, -7)),
        ('cube', (0.3, wall_h, 14), (7, 1.5, 0)),
        ('cube', (0.3, wall_h, 14), (-7, 1.5, 0)),
        ('cube', (15, 0.3, 15), (0, 3.15, 0)),
    ]
    for model_name, scale, pos in fence:
        Entity(model=model_name, scale=scale, position=INTERIOR_ORIGIN + pos, color=WALL_COLOR, collider='box')

    floor_colors = [
        (Vec3(-3.5, 0, 3.5), 6.8, color.rgb(200, 170, 120)),
        (Vec3(3.5, 0, 3.5), 6.8, color.rgb(165, 145, 180)),
        (Vec3(-3.5, 0, -3.5), 6.8, color.rgb(120, 170, 190)),
        (Vec3(3.5, 0, -3.5), 6.8, color.rgb(170, 150, 110)),
    ]
    for pos, size, tint in floor_colors:
        Entity(model='plane', scale=size, position=INTERIOR_ORIGIN + pos + Vec3(0, 0.03, 0), color=tint)

    oven = Entity(model='cube', scale=(1.3, 1.2, 1), position=INTERIOR_ORIGIN + Vec3(-5.8, 0.6, 6.3), color=color.rgb(52, 54, 58), collider='box')
    oven_note = Entity(model='cube', scale=(0.45, 0.28, 0.04), position=INTERIOR_ORIGIN + Vec3(-5.8, 1.3, 5.78), color=color.rgb(250, 245, 220), collider='box')

    closet = Entity(model='cube', scale=(1.8, 2.4, 0.7), position=INTERIOR_ORIGIN + Vec3(5.8, 1.2, 6.3), origin=(-0.5, 0, 0), color=color.rgb(92, 64, 36), collider='box')
    safe = Entity(model='cube', scale=(0.9, 0.9, 0.9), position=INTERIOR_ORIGIN + Vec3(4.7, 0.45, 6.2), color=color.rgb(55, 60, 66), collider='box', enabled=False)

    mirror = Entity(model='cube', scale=(1.2, 1.5, 0.05), position=INTERIOR_ORIGIN + Vec3(-5.8, 1.6, -6.3), color=color.rgb(170, 210, 230), collider='box')
    mirror_note = Entity(model='cube', scale=(0.45, 0.28, 0.04), position=INTERIOR_ORIGIN + Vec3(-5.8, 0.85, -6.25), color=color.rgb(250, 245, 220), collider='box')

    desk = Entity(model='cube', scale=(1.8, 0.7, 1.0), position=INTERIOR_ORIGIN + Vec3(5.8, 0.35, -6.3), color=color.rgb(88, 68, 44), collider='box')
    desk_note = Entity(model='cube', scale=(0.42, 0.03, 0.28), position=INTERIOR_ORIGIN + Vec3(5.2, 0.72, -6.3), color=color.rgb(250, 245, 220), collider='box')

    shelf = Entity(model='cube', scale=(1.6, 0.12, 0.4), position=INTERIOR_ORIGIN + Vec3(6.6, 1.8, -4.2), color=color.rgb(90, 62, 36))
    golden_book = Entity(model='cube', scale=(0.38, 0.22, 0.3), position=INTERIOR_ORIGIN + Vec3(6.6, 1.96, -4.2), color=color.rgb(255, 200, 40), collider='box')
    secret_wall = Entity(model='cube', scale=(2.2, 3.2, 0.2), position=INTERIOR_ORIGIN + Vec3(6.7, 1.5, -5.0), color=color.rgb(130, 120, 110), collider='box')

    return {
        'oven_note': oven_note,
        'closet': closet,
        'safe': safe,
        'mirror_note': mirror_note,
        'desk_note': desk_note,
        'golden_book': golden_book,
        'secret_wall': secret_wall,
        'shelf': shelf,
    }


def build_maze():
    lava = Entity(model='plane', scale=80, position=MAZE_ORIGIN, color=color.rgb(200, 55, 15), texture='white_cube', texture_scale=(20, 20))

    path = [
        Vec3(0, 1, -6), Vec3(2.0, 1.1, -4), Vec3(-1.6, 1.2, -1.5),
        Vec3(1.8, 1.3, 1.2), Vec3(-1.5, 1.4, 4), Vec3(1.4, 1.5, 7.0),
        Vec3(-0.7, 1.6, 10.0), Vec3(1.8, 1.7, 13.0), Vec3(0, 2.0, 17.0)
    ]

    platforms = []
    for i, p in enumerate(path):
        scale = (1.8, 0.5, 1.8)
        color_value = [
            color.rgb(125, 85, 52),
            color.rgb(142, 85, 62),
            color.rgb(64, 100, 150),
            color.rgb(95, 145, 90),
            color.rgb(155, 120, 80),
            color.rgb(120, 90, 170),
            color.rgb(95, 130, 110),
            color.rgb(220, 130, 80),
            color.rgb(255, 200, 40),
        ][i % 9]
        platform = Entity(model='cube', scale=scale, position=MAZE_ORIGIN + p, color=color_value, collider='box')
        platforms.append(platform)

    trophy = Entity(model='cube', scale=(0.6, 0.8, 0.6), position=MAZE_ORIGIN + path[-1] + Vec3(0, 1.1, 0), color=color.rgb(255, 215, 0), collider='box')

    return {'lava': lava, 'platforms': platforms, 'trophy': trophy}


if __name__ == '__main__':
    app = Ursina()
    window.title = 'House Quest Preview'
    window.size = (1280, 720)
    window.color = color.rgb(18, 22, 30)
    window.borderless = False

    camera.position = (0, 4, -18)
    camera.rotation_x = 10
    camera.fov = 90

    build_lighting_and_sky()
    build_exterior()
    build_interior()
    build_maze()

    app.run()
