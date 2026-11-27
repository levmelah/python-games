"""בניית העולם התלת-ממדי למשחק חדר הבריחה (הבית + המבוך).

הקובץ הזה רק בונה גיאומטריה (קירות, רהיטים, פתקים, מלכודות לבה) ומחזיר
הפניות (references) לישויות החשובות. כל ההגיון של המשחק (מצבים, פתקים,
קוד לכספת וכו') נמצא בקובץ escape_house_quest.py.
"""

from ursina import Entity, Text, Sky, AmbientLight, DirectionalLight, color, Vec3


# מיקומי עוגן של כל אזור בעולם, כדי שלא יתנגשו אחד בשני
EXTERIOR_ORIGIN = Vec3(0, 0, 0)
EXTERIOR_SPAWN = Vec3(0, 1, -10)

INTERIOR_ORIGIN = Vec3(0, 0, -60)
INTERIOR_SPAWN = INTERIOR_ORIGIN + Vec3(0, 1, -4)

MAZE_ORIGIN = Vec3(0, -6, -160)
MAZE_SPAWN = MAZE_ORIGIN + Vec3(0, 3, -8)
MAZE_FALL_Y = MAZE_ORIGIN.y - 6

WALL_COLOR = color.rgb32(196, 178, 148)
FLOOR_COLOR = color.rgb32(120, 84, 56)


def build_lighting_and_sky():
    Sky(color=color.rgb32(8, 8, 28))
    AmbientLight(color=color.rgba(120 / 255, 120 / 255, 150 / 255, 1))
    moon = DirectionalLight(shadows=True)
    moon.look_at(Vec3(1, -2, 1))
    moon.color = color.rgba(180 / 255, 190 / 255, 255 / 255, 1)


def build_exterior():
    """בונה את חוץ הבית: קרקע, קירות, גג, תיבת דואר ודלת. מחזיר dict."""
    ground = Entity(
        model='plane', scale=60, position=EXTERIOR_ORIGIN,
        color=color.rgb32(18, 40, 20), texture='white_cube',
        texture_scale=(30, 30), collider='box',
    )

    wall_h = 3
    Entity(model='cube', scale=(10.6, wall_h, 0.3), position=(0, wall_h / 2, 5), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(3.5, wall_h, 0.3), position=(-3.25, wall_h / 2, -5), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(3.5, wall_h, 0.3), position=(3.25, wall_h / 2, -5), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(0.3, wall_h, 10), position=(5, wall_h / 2, 0), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(0.3, wall_h, 10), position=(-5, wall_h / 2, 0), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(11, 0.3, 11), position=(0, wall_h + 0.15, 0), color=color.rgb32(110, 40, 40))

    door = Entity(
        model='cube', scale=(3, 2.8, 0.2), origin=(-0.5, 0, 0),
        position=(-1.5, 1.4, -5), color=color.rgb32(90, 55, 30), collider='box',
    )

    post = Entity(model='cube', scale=(0.12, 1, 0.12), position=(2, 0.5, -6.5), color=color.rgb32(70, 45, 25))
    mailbox_body = Entity(
        model='cube', scale=(0.55, 0.4, 0.4), origin=(0, -0.5, -0.5),
        position=(2, 1, -6.7), color=color.rgb32(40, 90, 60), collider='box',
    )
    mailbox_flap = Entity(
        model='cube', scale=(0.5, 0.05, 0.38), origin=(0, 0, -0.5),
        position=(2, 1.2, -6.51), color=color.rgb32(30, 70, 45),
    )
    key = Entity(
        model='cube', scale=(0.35, 0.08, 0.08), position=(2, 1, -6.6),
        color=color.rgb32(255, 215, 0), collider='box', enabled=False,
    )

    porch_light = Entity(model='sphere', scale=0.25, position=(2.3, 2.6, -5.05), color=color.rgb32(255, 235, 180))

    return {
        'door': door,
        'mailbox_body': mailbox_body,
        'mailbox_flap': mailbox_flap,
        'key': key,
        'ground': ground,
    }


def _floor_patch(local_pos, size, tint):
    return Entity(
        model='plane', scale=size, position=INTERIOR_ORIGIN + local_pos + Vec3(0, 0.02, 0),
        color=tint,
    )


def _sign(text, local_pos, rot_y):
    Text(
        text=text, parent=None, position=INTERIOR_ORIGIN + local_pos,
        scale=6, color=color.white, rotation=(0, rot_y, 0), origin=(0, 0, 0),
        background=True,
    )


def build_interior():
    """בונה את פנים הבית: מטבח, חדר שינה, שירותים ומשרד. מחזיר dict."""
    floor = Entity(
        model='plane', scale=14, position=INTERIOR_ORIGIN,
        color=FLOOR_COLOR, collider='box',
    )
    wall_h = 3
    Entity(model='cube', scale=(14.6, wall_h, 0.3), position=INTERIOR_ORIGIN + Vec3(0, wall_h / 2, 7), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(14.6, wall_h, 0.3), position=INTERIOR_ORIGIN + Vec3(0, wall_h / 2, -7), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(0.3, wall_h, 14), position=INTERIOR_ORIGIN + Vec3(7, wall_h / 2, 0), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(0.3, wall_h, 14), position=INTERIOR_ORIGIN + Vec3(-7, wall_h / 2, 0), color=WALL_COLOR, collider='box')
    Entity(model='cube', scale=(15, 0.3, 15), position=INTERIOR_ORIGIN + Vec3(0, wall_h + 0.15, 0), color=color.rgb32(80, 60, 60))

    _floor_patch(Vec3(-3.5, 0, 3.5), 6.8, color.rgb32(200, 170, 120))
    _sign('מטבח', Vec3(-3.5, 1.6, 1.2), 180)

    _floor_patch(Vec3(3.5, 0, 3.5), 6.8, color.rgb32(150, 120, 160))
    _sign('חדר שינה', Vec3(3.5, 1.6, 1.2), 180)

    _floor_patch(Vec3(-3.5, 0, -3.5), 6.8, color.rgb32(120, 170, 190))
    _sign('שירותים', Vec3(-3.5, 1.6, -1.2), 0)

    _floor_patch(Vec3(3.5, 0, -3.5), 6.8, color.rgb32(170, 150, 110))
    _sign('משרד', Vec3(3.5, 1.6, -1.2), 0)

    oven = Entity(
        model='cube', scale=(1.3, 1.2, 1), position=INTERIOR_ORIGIN + Vec3(-5.8, 0.6, 6.3),
        color=color.rgb32(50, 50, 55), collider='box',
    )
    oven_note = Entity(
        model='cube', scale=(0.5, 0.35, 0.02), position=INTERIOR_ORIGIN + Vec3(-5.8, 1.35, 5.78),
        color=color.rgb32(250, 245, 220), collider='box',
    )

    closet = Entity(
        model='cube', scale=(1.8, 2.4, 0.7), position=INTERIOR_ORIGIN + Vec3(5.8, 1.2, 6.3),
        origin=(-0.5, 0, 0), color=color.rgb32(90, 60, 35), collider='box',
    )
    safe = Entity(
        model='cube', scale=(0.9, 0.9, 0.9), position=INTERIOR_ORIGIN + Vec3(4.6, 0.45, 6.2),
        color=color.rgb32(60, 60, 65), collider='box', enabled=False,
    )

    mirror = Entity(
        model='cube', scale=(1.2, 1.5, 0.05), position=INTERIOR_ORIGIN + Vec3(-5.8, 1.6, -6.3),
        color=color.rgb32(180, 220, 230), collider='box',
    )
    mirror_note = Entity(
        model='cube', scale=(0.5, 0.35, 0.02), position=INTERIOR_ORIGIN + Vec3(-5.8, 0.9, -6.25),
        color=color.rgb32(250, 245, 220), collider='box',
    )

    desk = Entity(
        model='cube', scale=(1.8, 0.7, 1), position=INTERIOR_ORIGIN + Vec3(5.8, 0.35, -6.3),
        color=color.rgb32(100, 70, 45), collider='box',
    )
    desk_note = Entity(
        model='cube', scale=(0.4, 0.02, 0.3), position=INTERIOR_ORIGIN + Vec3(5.4, 0.72, -6.3),
        color=color.rgb32(250, 245, 220), collider='box',
    )

    shelf = Entity(
        model='cube', scale=(1.6, 0.1, 0.4), position=INTERIOR_ORIGIN + Vec3(6.6, 1.6, -4.2),
        color=color.rgb32(90, 60, 35),
    )
    golden_book = Entity(
        model='cube', scale=(0.35, 0.2, 0.3), position=INTERIOR_ORIGIN + Vec3(6.6, 1.72, -4.2),
        color=color.rgb32(255, 200, 40), collider='box',
    )
    secret_wall = Entity(
        model='cube', scale=(2, 3, 0.3), position=INTERIOR_ORIGIN + Vec3(6.85, 1.5, -4.9),
        origin=(0, -0.5, 0), color=color.rgb32(140, 120, 100),
    )

    return {
        'oven_note': oven_note,
        'closet': closet,
        'safe': safe,
        'mirror_note': mirror_note,
        'desk_note': desk_note,
        'golden_book': golden_book,
        'secret_wall': secret_wall,
    }


def build_maze():
    """בונה את מבוך הלבה: פלטפורמות רהיטים צפות מעל לבה, וגביע בסוף."""
    lava = Entity(
        model='plane', scale=80, position=MAZE_ORIGIN,
        color=color.rgb32(200, 60, 10), texture='white_cube', texture_scale=(20, 20),
    )

    path_local = [
        Vec3(0, 1, -6), Vec3(1.8, 1, -3.8), Vec3(-1.2, 1.1, -1.5),
        Vec3(1.5, 1.2, 1), Vec3(-1.6, 1, 3.5), Vec3(0.8, 1.3, 6),
        Vec3(-0.5, 1, 8.8), Vec3(1.6, 1.1, 11.5), Vec3(0, 1.2, 14.5),
        Vec3(0, 1, 17.5),
    ]
    furniture_models = ['cube', 'cube', 'sphere', 'cube']
    furniture_colors = [
        color.rgb32(120, 80, 50), color.rgb32(150, 40, 40),
        color.rgb32(90, 90, 200), color.rgb32(60, 130, 90),
    ]
    platforms = []
    for i, local_pos in enumerate(path_local):
        plat = Entity(
            model=furniture_models[i % len(furniture_models)],
            scale=(1.8, 0.5, 1.8) if furniture_models[i % len(furniture_models)] == 'cube' else 1.4,
            position=MAZE_ORIGIN + local_pos,
            color=furniture_colors[i % len(furniture_colors)],
            collider='box',
        )
        platforms.append(plat)

    trophy = Entity(
        model='cube', scale=(0.5, 0.7, 0.5),
        position=MAZE_ORIGIN + path_local[-1] + Vec3(0, 0.9, 0),
        color=color.rgb32(255, 215, 0), collider='box',
    )

    return {
        'lava': lava,
        'platforms': platforms,
        'trophy': trophy,
        'start_pos': MAZE_SPAWN,
    }
