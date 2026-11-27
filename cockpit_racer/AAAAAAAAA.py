import math
import random
import re
import sys

import pygame

pygame.init()

WIDTH, HEIGHT = 1000, 600
FPS = 60
HORIZON_Y = HEIGHT / 2

_LTR_RUN_RE = re.compile(r"[A-Za-z0-9/.,%\-]+")


def rtl(text):
    """Crude bidi fix so Hebrew strings render correctly with pygame's
    LTR-only text rendering: reverse the whole string, then flip back
    any Latin/number runs so they stay left-to-right."""
    reversed_text = text[::-1]
    return _LTR_RUN_RE.sub(lambda m: m.group(0)[::-1], reversed_text)

SEGMENT_LENGTH = 200
ROAD_HALF_WIDTH = 1000
RUMBLE_LENGTH = 3
LANE_LENGTH = 6
CAMERA_HEIGHT = 900
CAMERA_DEPTH = 0.65
DRAW_DISTANCE = 160
CURVE_SCALE = 40

MAX_SPEED = 5400.0
ACCEL = MAX_SPEED / 2.2
BRAKE = MAX_SPEED / 1.0
DECEL = MAX_SPEED / 3.5
OFF_ROAD_MAX_SPEED = MAX_SPEED * 0.35
OFF_ROAD_DECEL = MAX_SPEED / 1.6
CENTRIFUGAL = 0.0022
STEER_RATE = 2.6
CAMERA_X_SCALE = 3.2

CRASH_SPEED_FACTOR = 0.22
CRASH_PUSH = 0.22
CRASH_FLASH_TIME = 0.6
COLLISION_THRESHOLD = 0.34
OBSTACLE_MIN_GAP = 7
OBSTACLE_MAX_GAP = 16
OBSTACLE_START_SEG = 35

FLY_DURATION = 0.9
FLY_LATERAL = 2.4
FLY_ARC_HEIGHT = 0.9
FLY_SPINS = 2.6

ZONE_LENGTH_KM = 100
RAMP_COOLDOWN = 1.5
AIR_DURATION = 1.0
JUMP_HEIGHT = 90

MONEY_VALUE = 100
CONE_BONUS_HITS = 7
CONE_BONUS_AMOUNT = 30
MONEY_MIN_GAP = 9
MONEY_MAX_GAP = 20
MONEY_START_SEG = 20
MONEY_COLLECT_RADIUS = 0.4
MONEY_COLLECT_TIME = 0.35
MONEY_GAUGE_CYCLE = 500

SKY_TOP = (64, 110, 200)
SKY_HORIZON = (170, 205, 245)
HILL_FAR = (60, 95, 70)
HILL_NEAR = (45, 80, 55)
GRASS_LIGHT = (24, 150, 40)
GRASS_DARK = (16, 132, 32)

DESERT_SKY_TOP = (255, 150, 80)
DESERT_SKY_HORIZON = (255, 220, 160)
DESERT_HILL_FAR = (205, 150, 90)
DESERT_HILL_NEAR = (222, 172, 110)
DESERT_SAND_LIGHT = (237, 201, 160)
DESERT_SAND_DARK = (222, 182, 138)

ROAD_LIGHT = (100, 100, 105)
ROAD_DARK = (90, 90, 95)
RUMBLE_LIGHT = (235, 235, 235)
RUMBLE_DARK = (170, 25, 25)
LANE_COLOR = (235, 235, 235)

CAR_BODY = (18, 20, 26)
CAR_ACCENT = (40, 44, 54)
WHEEL_COLOR = (12, 12, 15)
WHEEL_RIM = (200, 205, 215)
DASH_TEXT = (225, 230, 240)
WARN_COLOR = (230, 90, 70)
MONEY_COLOR = (60, 145, 75)
MONEY_BORDER = (225, 225, 200)
GOLD_COLOR = (255, 205, 60)

OBSTACLE_TYPES = {
    "cone": {"color": (235, 90, 20), "width": 0.3, "height": 0.72},
}

RAMP_COLOR = (205, 30, 30)
RAMP_DARK = (140, 15, 15)
RAMP_LEG_COLOR = (35, 35, 38)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cockpit Racer - נהיגה מגוף ראשון")
clock = pygame.time.Clock()
font_big = pygame.font.SysFont("Arial", 30, bold=True)
font_mid = pygame.font.SysFont("Arial", 22, bold=True)
font_small = pygame.font.SysFont("Arial", 16)


def add_segment(segments, curve):
    idx = len(segments)
    light = (idx // RUMBLE_LENGTH) % 2 == 0
    segments.append({
        "index": idx,
        "curve": curve,
        "road": ROAD_LIGHT if light else ROAD_DARK,
        "grass": GRASS_LIGHT if light else GRASS_DARK,
        "grass_desert": DESERT_SAND_LIGHT if light else DESERT_SAND_DARK,
        "rumble": RUMBLE_LIGHT if light else RUMBLE_DARK,
        "lane": (idx // LANE_LENGTH) % 2 == 0,
    })


def add_road(segments, enter, hold, leave, curve):
    for i in range(enter):
        add_segment(segments, curve * (i / max(1, enter)))
    for i in range(hold):
        add_segment(segments, curve)
    for i in range(leave):
        add_segment(segments, curve * (1 - i / max(1, leave)))


def build_track():
    segments = []
    add_road(segments, 40, 60, 40, 0.0)
    add_road(segments, 30, 50, 30, -0.55)
    add_road(segments, 30, 40, 30, 0.0)
    add_road(segments, 25, 45, 25, 0.85)
    add_road(segments, 30, 50, 30, 0.0)
    add_road(segments, 20, 30, 20, -0.95)
    add_road(segments, 20, 20, 20, 0.95)
    add_road(segments, 30, 60, 30, 0.0)
    add_road(segments, 25, 35, 25, 0.4)
    add_road(segments, 25, 35, 25, -0.4)
    add_road(segments, 30, 50, 30, 0.0)
    return segments


TRACK = build_track()
TRACK_N = len(TRACK)
TRACK_LENGTH = TRACK_N * SEGMENT_LENGTH


def generate_obstacles():
    obstacles = []
    by_seg = {}
    idx = OBSTACLE_START_SEG
    while idx < TRACK_N - 6:
        idx += random.randint(OBSTACLE_MIN_GAP, OBSTACLE_MAX_GAP)
        if idx >= TRACK_N - 6:
            break
        seg_index = idx % TRACK_N
        obstacle = {
            "seg": seg_index,
            "offset": random.uniform(-0.8, 0.8),
            "kind": "cone",
            "hit": False,
            "fly_timer": 0.0,
            "fly_dir": 1.0,
            "ramp_cooldown": 0.0,
        }
        obstacles.append(obstacle)
        by_seg[seg_index] = obstacle
    return obstacles, by_seg


def rotate_xy(x, y, angle):
    ca, sa = math.cos(angle), math.sin(angle)
    return x * ca - y * sa, x * sa + y * ca


def draw_flying_cone(point, obstacle):
    spec = OBSTACLE_TYPES["cone"]
    progress = min(1.0, obstacle["fly_timer"] / FLY_DURATION)
    shrink = 1.0 - progress * 0.55

    lateral = obstacle["offset"] + obstacle["fly_dir"] * FLY_LATERAL * progress
    base_x = point["x"] + lateral * point["w"]
    arc = FLY_ARC_HEIGHT * point["w"] * 4 * progress * (1 - progress)
    center_y = point["y"] - point["w"] * spec["height"] * 0.55 * shrink - arc

    rotation = obstacle["fly_dir"] * progress * FLY_SPINS * 2 * math.pi
    w = max(3, point["w"] * spec["width"] * shrink)
    h = max(3, point["w"] * spec["height"] * 1.5 * shrink)
    orange = spec["color"]

    tri = [(0, -h * 0.55), (w * 0.42, h * 0.45), (-w * 0.42, h * 0.45)]
    tri_pts = [(base_x + rx, center_y + ry) for rx, ry in (rotate_xy(x, y, rotation) for x, y in tri)]
    pygame.draw.polygon(screen, orange, tri_pts)

    band = [(-w * 0.28, -h * 0.05), (w * 0.28, -h * 0.05), (w * 0.34, h * 0.15), (-w * 0.34, h * 0.15)]
    band_pts = [(base_x + rx, center_y + ry) for rx, ry in (rotate_xy(x, y, rotation) for x, y in band)]
    pygame.draw.polygon(screen, (240, 240, 240), band_pts)

    base_shape = [(-w * 0.5, h * 0.42), (w * 0.5, h * 0.42), (w * 0.5, h * 0.52), (-w * 0.5, h * 0.52)]
    base_pts = [(base_x + rx, center_y + ry) for rx, ry in (rotate_xy(x, y, rotation) for x, y in base_shape)]
    pygame.draw.polygon(screen, (20, 18, 18), base_pts)


def draw_ramp(point, obstacle):
    base_x = point["x"] + obstacle["offset"] * point["w"]
    ground_y = point["y"]
    w = point["w"] * 0.85
    h = point["w"] * 0.55

    leg_w = max(2, w * 0.05)
    for lx in (base_x - w * 0.42, base_x + w * 0.42):
        pygame.draw.line(screen, RAMP_LEG_COLOR, (lx, ground_y), (lx, ground_y - h * 0.35), max(1, int(leg_w)))

    ramp_pts = [
        (base_x - w / 2, ground_y),
        (base_x + w / 2, ground_y),
        (base_x + w / 2, ground_y - h),
        (base_x - w / 2, ground_y - h * 0.18),
    ]
    pygame.draw.polygon(screen, RAMP_COLOR, ramp_pts)
    pygame.draw.polygon(screen, RAMP_DARK, ramp_pts, max(1, int(w * 0.02)))

    stripe_pts = [
        (base_x - w * 0.12, ground_y - h * 0.06),
        (base_x + w * 0.5, ground_y - h * 0.86),
        (base_x + w * 0.5, ground_y - h * 0.62),
        (base_x - w * 0.12, ground_y + h * 0.02),
    ]
    pygame.draw.polygon(screen, (240, 240, 240), stripe_pts)


def draw_obstacle(point, obstacle, desert=False):
    if point["y"] <= HORIZON_Y or point["w"] < 2:
        return
    if desert:
        draw_ramp(point, obstacle)
        return
    if obstacle.get("hit"):
        draw_flying_cone(point, obstacle)
        return
    spec = OBSTACLE_TYPES["cone"]
    base_x = point["x"] + obstacle["offset"] * point["w"]
    ground_y = point["y"]
    w = max(4, point["w"] * spec["width"])
    h = max(5, point["w"] * spec["height"] * 1.6)
    orange = spec["color"]
    orange_dark = tuple(max(0, c - 45) for c in orange)

    base_w = w * 1.35
    base_h = h * 0.16
    base_rect = pygame.Rect(base_x - base_w / 2, ground_y - base_h, base_w, base_h)
    pygame.draw.ellipse(screen, (20, 18, 18), base_rect)

    body_top = ground_y - h
    body_bottom = ground_y - base_h * 0.6
    tip_round = max(1, w * 0.14)
    pygame.draw.polygon(screen, orange, [
        (base_x - tip_round, body_top), (base_x + tip_round, body_top),
        (base_x + w / 2, body_bottom), (base_x - w / 2, body_bottom),
    ])
    pygame.draw.circle(screen, orange, (int(base_x), int(body_top)), max(1, int(tip_round)))

    pygame.draw.polygon(screen, orange_dark, [
        (base_x - tip_round, body_top), (base_x, body_top),
        (base_x, body_bottom), (base_x - w / 2, body_bottom),
    ])

    for band_t, band_h_ratio in ((0.38, 0.16), (0.62, 0.16)):
        band_y = body_top + h * band_t
        band_half_w = (tip_round + (w / 2 - tip_round) * band_t) * 1.02
        band_h = max(1, h * band_h_ratio)
        pygame.draw.polygon(screen, (240, 240, 240), [
            (base_x - band_half_w, band_y), (base_x + band_half_w, band_y),
            (base_x + band_half_w * 1.12, band_y + band_h), (base_x - band_half_w * 1.12, band_y + band_h),
        ])

    pygame.draw.line(screen, orange_dark, (base_x, body_top), (base_x, body_bottom), max(1, int(w * 0.04)))


def generate_money(obstacles_by_seg):
    money_list = []
    by_seg = {}
    idx = MONEY_START_SEG
    while idx < TRACK_N - 6:
        idx += random.randint(MONEY_MIN_GAP, MONEY_MAX_GAP)
        if idx >= TRACK_N - 6:
            break
        seg_index = idx % TRACK_N
        if seg_index in obstacles_by_seg:
            continue
        bill = {
            "seg": seg_index,
            "offset": random.uniform(-0.75, 0.75),
            "collected": False,
            "collect_timer": 0.0,
        }
        money_list.append(bill)
        by_seg[seg_index] = bill
    return money_list, by_seg


def draw_money(point, bill, t):
    if point["y"] <= HORIZON_Y or point["w"] < 2:
        return
    bob = math.sin(t * 3.4 + bill["seg"] * 0.7) * point["w"] * 0.1
    base_x = point["x"] + bill["offset"] * point["w"]
    ground_y = point["y"] - point["w"] * 0.22 - bob

    scale = 1.0
    if bill["collected"]:
        progress = min(1.0, bill["collect_timer"] / MONEY_COLLECT_TIME)
        scale = 1.0 + progress * 0.9
        ground_y -= point["w"] * 0.9 * progress

    w = max(4, point["w"] * 0.34 * scale)
    h = w * 0.46

    rect = pygame.Rect(0, 0, w, h)
    rect.center = (base_x, ground_y)
    pygame.draw.rect(screen, MONEY_COLOR, rect, border_radius=max(1, int(h * 0.14)))
    pygame.draw.rect(screen, MONEY_BORDER, rect, width=max(1, int(h * 0.08)), border_radius=max(1, int(h * 0.14)))
    pygame.draw.ellipse(screen, (40, 110, 55), rect.inflate(-w * 0.42, -h * 0.42))

    corner = max(1, int(h * 0.16))
    for cx, cy in (
        (rect.left + corner, rect.top + corner), (rect.right - corner, rect.top + corner),
        (rect.left + corner, rect.bottom - corner), (rect.right - corner, rect.bottom - corner),
    ):
        pygame.draw.circle(screen, GOLD_COLOR, (int(cx), int(cy)), max(1, int(corner * 0.5)))


def draw_sky(offset, desert=False):
    sky_top = DESERT_SKY_TOP if desert else SKY_TOP
    sky_horizon = DESERT_SKY_HORIZON if desert else SKY_HORIZON
    hill_far = DESERT_HILL_FAR if desert else HILL_FAR
    hill_near = DESERT_HILL_NEAR if desert else HILL_NEAR

    for y in range(int(HORIZON_Y)):
        t = y / max(1, HORIZON_Y)
        color = (
            int(sky_top[0] + (sky_horizon[0] - sky_top[0]) * t),
            int(sky_top[1] + (sky_horizon[1] - sky_top[1]) * t),
            int(sky_top[2] + (sky_horizon[2] - sky_top[2]) * t),
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))

    sun_x = WIDTH * 0.78
    sun_y = HORIZON_Y * 0.35
    pygame.draw.circle(screen, (255, 230, 150), (int(sun_x), int(sun_y)), 46)

    for layer, base_color, amp, freq, speed, y_base in (
        (0, hill_far, 34, 0.012, 0.02, 0.72),
        (1, hill_near, 46, 0.02, 0.05, 0.85),
    ):
        points = [(0, HORIZON_Y)]
        for x in range(0, WIDTH + 20, 20):
            y = HORIZON_Y * y_base + amp * math.sin((x + offset * speed) * freq)
            points.append((x, y))
        points.append((WIDTH, HORIZON_Y))
        pygame.draw.polygon(screen, base_color, points)


def project_points(position, player_x):
    base_index = int(position // SEGMENT_LENGTH)
    x_accum = 0.0
    curve_accum = 0.0
    points = []
    for n in range(DRAW_DISTANCE + 1):
        global_index = base_index + n
        idx = global_index % TRACK_N
        seg = TRACK[idx]

        z = max(1.0, global_index * SEGMENT_LENGTH - position)
        scale = CAMERA_DEPTH / (z / SEGMENT_LENGTH)

        curve_accum += seg["curve"]
        x_accum += curve_accum * CURVE_SCALE

        world_x = x_accum - player_x * ROAD_HALF_WIDTH * CAMERA_X_SCALE
        screen_x = WIDTH / 2 + scale * world_x
        screen_y = HEIGHT / 2 + scale * CAMERA_HEIGHT * (HEIGHT / 900)
        half_w = scale * ROAD_HALF_WIDTH

        points.append({
            "x": screen_x,
            "y": screen_y,
            "w": half_w,
            "seg": seg,
        })
    return points


def draw_road(points, shake, obstacles_by_seg, money_by_seg, t, desert=False):
    for n in range(DRAW_DISTANCE - 1, -1, -1):
        p1 = points[n]
        p2 = points[n + 1]
        seg = p1["seg"]

        y1 = min(HEIGHT, p1["y"] + shake)
        y2 = min(HEIGHT, p2["y"] + shake)
        if y2 >= y1:
            continue
        if y1 < HORIZON_Y - 4:
            continue

        grass_color = seg["grass_desert"] if desert else seg["grass"]
        pygame.draw.polygon(screen, grass_color, [
            (0, y1), (WIDTH, y1), (WIDTH, y2), (0, y2),
        ])

        rumble_w1 = p1["w"] * 1.22 + 4
        rumble_w2 = p2["w"] * 1.22 + 4
        pygame.draw.polygon(screen, seg["rumble"], [
            (p1["x"] - rumble_w1, y1), (p1["x"] + rumble_w1, y1),
            (p2["x"] + rumble_w2, y2), (p2["x"] - rumble_w2, y2),
        ])

        pygame.draw.polygon(screen, seg["road"], [
            (p1["x"] - p1["w"], y1), (p1["x"] + p1["w"], y1),
            (p2["x"] + p2["w"], y2), (p2["x"] - p2["w"], y2),
        ])

        if seg["lane"]:
            lane_w1 = p1["w"] * 0.035 + 1
            lane_w2 = p2["w"] * 0.035 + 1
            pygame.draw.polygon(screen, LANE_COLOR, [
                (p1["x"] - lane_w1, y1), (p1["x"] + lane_w1, y1),
                (p2["x"] + lane_w2, y2), (p2["x"] - lane_w2, y2),
            ])

        shifted = dict(p1, y=y1)

        bill = money_by_seg.get(seg["index"])
        if bill is not None:
            draw_money(shifted, bill, t)

        obstacle = obstacles_by_seg.get(seg["index"])
        if obstacle is not None:
            draw_obstacle(shifted, obstacle, desert)


def draw_cockpit(wheel_angle, speed_ratio, money):
    pillar_w = WIDTH * 0.10
    pygame.draw.polygon(screen, CAR_ACCENT, [
        (0, 0), (pillar_w, 0), (pillar_w * 0.25, HEIGHT), (0, HEIGHT),
    ])
    pygame.draw.polygon(screen, CAR_ACCENT, [
        (WIDTH, 0), (WIDTH - pillar_w, 0), (WIDTH - pillar_w * 0.25, HEIGHT), (WIDTH, HEIGHT),
    ])

    mirror_w, mirror_h = 150, 46
    mirror_rect = pygame.Rect(WIDTH / 2 - mirror_w / 2, 14, mirror_w, mirror_h)
    pygame.draw.rect(screen, (90, 130, 160), mirror_rect, border_radius=8)
    pygame.draw.rect(screen, CAR_ACCENT, mirror_rect, width=5, border_radius=8)

    hood_top = HEIGHT * 0.80
    pygame.draw.polygon(screen, CAR_BODY, [
        (0, hood_top), (WIDTH, hood_top), (WIDTH, HEIGHT), (0, HEIGHT),
    ])
    pygame.draw.polygon(screen, CAR_ACCENT, [
        (WIDTH * 0.5 - 14, hood_top - 6), (WIDTH * 0.5 + 14, hood_top - 6),
        (WIDTH * 0.5 + 22, HEIGHT), (WIDTH * 0.5 - 22, HEIGHT),
    ])

    dash_rect = pygame.Rect(0, HEIGHT * 0.885, WIDTH, HEIGHT * 0.115)
    pygame.draw.rect(screen, CAR_ACCENT, dash_rect)

    center = (WIDTH / 2, HEIGHT * 0.99)
    radius = 92
    angle = math.radians(wheel_angle - 90)
    ring_rect = pygame.Rect(0, 0, radius * 2, radius * 2)
    ring_rect.center = center
    pygame.draw.ellipse(screen, WHEEL_COLOR, ring_rect)
    pygame.draw.ellipse(screen, WHEEL_RIM, ring_rect, width=10)

    hub_radius = 20
    pygame.draw.circle(screen, WHEEL_RIM, center, hub_radius)
    pygame.draw.circle(screen, WHEEL_COLOR, center, hub_radius, width=4)

    for spoke in range(3):
        a = angle + spoke * (2 * math.pi / 3)
        ex = center[0] + math.cos(a) * (radius - 6)
        ey = center[1] + math.sin(a) * (radius - 6)
        pygame.draw.line(screen, WHEEL_RIM, center, (ex, ey), 9)

    grip_len = 0.9
    for side in (0, math.pi):
        a = angle + side
        gx1 = center[0] + math.cos(a) * (radius - 22)
        gy1 = center[1] + math.sin(a) * (radius - 22)
        gx2 = center[0] + math.cos(a) * (radius - 2)
        gy2 = center[1] + math.sin(a) * (radius - 2)
        pygame.draw.line(screen, (230, 200, 60), (gx1, gy1), (gx2, gy2), 12)

    gauge_center = (150, HEIGHT * 0.935)
    gauge_radius = 38
    pygame.draw.circle(screen, (25, 27, 33), gauge_center, gauge_radius)
    pygame.draw.circle(screen, WHEEL_RIM, gauge_center, gauge_radius, width=3)
    start_a = math.radians(135)
    end_a = math.radians(135 + 270 * speed_ratio)
    needle_a = start_a + (end_a - start_a)
    nx = gauge_center[0] + math.cos(needle_a) * (gauge_radius - 6)
    ny = gauge_center[1] + math.sin(needle_a) * (gauge_radius - 6)
    pygame.draw.line(screen, WARN_COLOR, gauge_center, (nx, ny), 3)
    pygame.draw.circle(screen, WHEEL_RIM, gauge_center, 4)

    money_gauge_center = (WIDTH - 150, HEIGHT * 0.935)
    money_progress = (money % MONEY_GAUGE_CYCLE) / MONEY_GAUGE_CYCLE
    pygame.draw.circle(screen, (25, 27, 33), money_gauge_center, gauge_radius)
    pygame.draw.circle(screen, WHEEL_RIM, money_gauge_center, gauge_radius, width=3)
    for tick in range(9):
        tick_a = start_a + (2 * math.pi * 0.75) * (tick / 8)
        tx1 = money_gauge_center[0] + math.cos(tick_a) * (gauge_radius - 4)
        ty1 = money_gauge_center[1] + math.sin(tick_a) * (gauge_radius - 4)
        tx2 = money_gauge_center[0] + math.cos(tick_a) * (gauge_radius - 9)
        ty2 = money_gauge_center[1] + math.sin(tick_a) * (gauge_radius - 9)
        pygame.draw.line(screen, WHEEL_RIM, (tx1, ty1), (tx2, ty2), 2)
    money_needle_a = start_a + (270 * math.pi / 180) * money_progress
    mnx = money_gauge_center[0] + math.cos(money_needle_a) * (gauge_radius - 6)
    mny = money_gauge_center[1] + math.sin(money_needle_a) * (gauge_radius - 6)
    pygame.draw.line(screen, GOLD_COLOR, money_gauge_center, (mnx, mny), 3)
    pygame.draw.circle(screen, WHEEL_RIM, money_gauge_center, 4)

    money_label = font_small.render(rtl(f"${money}"), True, GOLD_COLOR)
    money_label_rect = money_label.get_rect(center=(money_gauge_center[0], HEIGHT * 0.965))
    screen.blit(money_label, money_label_rect)


def draw_crash_flash(crash_timer):
    if crash_timer <= 0:
        return
    alpha = int(140 * min(1.0, crash_timer / CRASH_FLASH_TIME))
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((200, 30, 20, alpha))
    screen.blit(overlay, (0, 0))


def draw_hud(speed_kmh, distance_km, off_road, hits, crash_timer, bonus_timer, air_elapsed, desert):
    txt = font_mid.render(rtl(f"{int(speed_kmh)} קמ״ש"), True, DASH_TEXT)
    screen.blit(txt, (100, HEIGHT * 0.965))

    dist_txt = font_small.render(rtl(f"מרחק: {distance_km:.2f} ק״מ"), True, DASH_TEXT)
    dist_txt_rect = dist_txt.get_rect(topright=(WIDTH - 16, 16))
    screen.blit(dist_txt, dist_txt_rect)

    hits_txt = font_small.render(rtl(f"פגיעות: {hits}"), True, DASH_TEXT)
    hits_rect = hits_txt.get_rect(topright=(WIDTH - 16, 38))
    screen.blit(hits_txt, hits_rect)

    zone_txt = font_small.render(rtl("מדבר" if desert else "כביש"), True, GOLD_COLOR if desert else DASH_TEXT)
    zone_rect = zone_txt.get_rect(topright=(WIDTH - 16, 60))
    screen.blit(zone_txt, zone_rect)

    if bonus_timer > 0:
        bonus = font_mid.render(rtl(f"כנס! -${CONE_BONUS_AMOUNT}"), True, WARN_COLOR)
        screen.blit(bonus, (WIDTH / 2 - bonus.get_width() / 2, HEIGHT * 0.42))

    if air_elapsed > 0:
        jump_txt = font_mid.render(rtl("קפיצה!"), True, GOLD_COLOR)
        screen.blit(jump_txt, (WIDTH / 2 - jump_txt.get_width() / 2, HEIGHT * 0.5))
    elif crash_timer > 0:
        warn = font_mid.render(rtl("התנגשות!"), True, WARN_COLOR)
        screen.blit(warn, (WIDTH / 2 - warn.get_width() / 2, HEIGHT * 0.5))
    elif off_road:
        warn = font_mid.render(rtl("שטח חול! האט"), True, WARN_COLOR)
        screen.blit(warn, (WIDTH / 2 - warn.get_width() / 2, HEIGHT * 0.5))

    help_txt = font_small.render(
        rtl("חיצים/WASD לנהיגה  |  R לאיפוס  |  ESC ליציאה"), True, DASH_TEXT
    )
    screen.blit(help_txt, (16, 16))


def reset_state():
    obstacles, obstacles_by_seg = generate_obstacles()
    money_list, money_by_seg = generate_money(obstacles_by_seg)
    return {
        "position": 0.0,
        "speed": 0.0,
        "player_x": 0.0,
        "wheel_angle": 0.0,
        "obstacles": obstacles,
        "obstacles_by_seg": obstacles_by_seg,
        "money_list": money_list,
        "money_by_seg": money_by_seg,
        "money": 0,
        "hits": 0,
        "crash_timer": 0.0,
        "bonus_timer": 0.0,
        "air_elapsed": 0.0,
        "total_distance": 0.0,
        "time": 0.0,
    }


def main():
    state = reset_state()
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 0.05)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_r:
                    state = reset_state()

        keys = pygame.key.get_pressed()
        steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            steer -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            steer += 1.0

        throttle = keys[pygame.K_UP] or keys[pygame.K_w]
        brake = keys[pygame.K_DOWN] or keys[pygame.K_s]

        if throttle:
            state["speed"] += ACCEL * dt
        elif brake:
            state["speed"] -= BRAKE * dt
        else:
            state["speed"] -= DECEL * dt

        base_index = int(state["position"] // SEGMENT_LENGTH) % TRACK_N
        current_curve = TRACK[base_index]["curve"]

        off_road = abs(state["player_x"]) > 1.0
        speed_cap = OFF_ROAD_MAX_SPEED if off_road else MAX_SPEED
        if off_road and state["speed"] > speed_cap:
            state["speed"] -= OFF_ROAD_DECEL * dt

        state["speed"] = max(0.0, min(state["speed"], MAX_SPEED))
        speed_ratio = state["speed"] / MAX_SPEED

        state["player_x"] += steer * STEER_RATE * speed_ratio * dt
        state["player_x"] -= current_curve * CENTRIFUGAL * speed_ratio * speed_ratio
        state["player_x"] = max(-2.2, min(2.2, state["player_x"]))

        move_delta = state["speed"] * dt
        prev_position = state["position"]
        state["position"] = (state["position"] + move_delta) % TRACK_LENGTH
        state["total_distance"] += move_delta

        zone_km = state["total_distance"] / 1000.0
        desert = (int(zone_km // ZONE_LENGTH_KM) % 2) == 1

        player_offset = max(-1.4, min(1.4, state["player_x"] * CAMERA_X_SCALE))
        prev_global = int(prev_position // SEGMENT_LENGTH)
        new_global = int((prev_position + move_delta) // SEGMENT_LENGTH)
        for global_idx in range(prev_global, new_global + 1):
            seg_idx = global_idx % TRACK_N
            obstacle = state["obstacles_by_seg"].get(seg_idx)
            if obstacle is None:
                continue
            if desert:
                if obstacle["ramp_cooldown"] > 0:
                    continue
                if abs(player_offset - obstacle["offset"]) < COLLISION_THRESHOLD:
                    obstacle["ramp_cooldown"] = RAMP_COOLDOWN
                    state["air_elapsed"] = 1e-4
            else:
                if obstacle["hit"]:
                    continue
                if abs(player_offset - obstacle["offset"]) < COLLISION_THRESHOLD:
                    obstacle["hit"] = True
                    obstacle["fly_timer"] = 0.0
                    obstacle["fly_dir"] = 1.0 if player_offset >= obstacle["offset"] else -1.0
                    state["hits"] += 1
                    if state["hits"] % CONE_BONUS_HITS == 0:
                        state["money"] = max(0, state["money"] - CONE_BONUS_AMOUNT)
                        state["bonus_timer"] = CRASH_FLASH_TIME * 2
                    state["speed"] *= CRASH_SPEED_FACTOR
                    state["crash_timer"] = CRASH_FLASH_TIME
                    push = CRASH_PUSH if player_offset >= obstacle["offset"] else -CRASH_PUSH
                    state["player_x"] = max(-2.2, min(2.2, state["player_x"] + push))

        for global_idx in range(prev_global, new_global + 1):
            seg_idx = global_idx % TRACK_N
            bill = state["money_by_seg"].get(seg_idx)
            if bill is None or bill["collected"]:
                continue
            if abs(player_offset - bill["offset"]) < MONEY_COLLECT_RADIUS:
                bill["collected"] = True
                bill["collect_timer"] = 0.0
                state["money"] += MONEY_VALUE

        state["crash_timer"] = max(0.0, state["crash_timer"] - dt)
        state["bonus_timer"] = max(0.0, state["bonus_timer"] - dt)
        if state["air_elapsed"] > 0:
            state["air_elapsed"] += dt
            if state["air_elapsed"] >= AIR_DURATION:
                state["air_elapsed"] = 0.0
        state["time"] += dt

        for obstacle in state["obstacles_by_seg"].values():
            if obstacle["ramp_cooldown"] > 0:
                obstacle["ramp_cooldown"] = max(0.0, obstacle["ramp_cooldown"] - dt)

        for seg_idx, obstacle in list(state["obstacles_by_seg"].items()):
            if not obstacle["hit"]:
                continue
            obstacle["fly_timer"] += dt
            if obstacle["fly_timer"] >= FLY_DURATION:
                del state["obstacles_by_seg"][seg_idx]

        for seg_idx, bill in list(state["money_by_seg"].items()):
            if not bill["collected"]:
                continue
            bill["collect_timer"] += dt
            if bill["collect_timer"] >= MONEY_COLLECT_TIME:
                del state["money_by_seg"][seg_idx]

        target_wheel_angle = steer * 55
        state["wheel_angle"] += (target_wheel_angle - state["wheel_angle"]) * min(1.0, dt * 7)

        shake = 0.0
        if off_road and state["speed"] > 20:
            shake = random.uniform(-3, 3) * min(1.0, state["speed"] / 800)
        if state["crash_timer"] > 0:
            shake += random.uniform(-6, 6)
        if state["air_elapsed"] > 0:
            jump_progress = min(1.0, state["air_elapsed"] / AIR_DURATION)
            shake += -JUMP_HEIGHT * 4 * jump_progress * (1 - jump_progress)

        draw_sky(state["position"] * 0.05, desert)
        points = project_points(state["position"], state["player_x"])
        draw_road(points, shake, state["obstacles_by_seg"], state["money_by_seg"], state["time"], desert)
        draw_cockpit(state["wheel_angle"], speed_ratio, state["money"])
        draw_hud(
            state["speed"] * 0.14,
            state["total_distance"] / 1000,
            off_road,
            state["hits"],
            state["crash_timer"],
            state["bonus_timer"],
            state["air_elapsed"],
            desert,
        )
        draw_crash_flash(state["crash_timer"])

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
