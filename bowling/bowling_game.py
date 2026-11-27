import math
import random
import pygame

pygame.init()

WIDTH, HEIGHT = 900, 700
FPS = 60

LANE_X = 230
LANE_W = 440
LANE_TOP = 60
LANE_BOTTOM = 650

BALL_RADIUS = 14
BALL_START = pygame.Vector2(WIDTH // 2, LANE_BOTTOM - 24)

PIN_RADIUS = 9
PIN_SPACING_X = 22
PIN_SPACING_Y = 20
PIN_HEAD_Y = 90

FRICTION = 0.992
STOP_SPEED = 0.12

WHITE = (245, 245, 245)
BLACK = (20, 20, 20)
BG_TOP = (12, 28, 55)
BG_BOTTOM = (8, 12, 22)
LANE_LIGHT = (192, 149, 95)
LANE_DARK = (161, 120, 73)
LANE_EDGE = (82, 50, 22)
TEXT = (240, 240, 250)
PIN_COLOR = (250, 250, 252)
PIN_RED = (198, 40, 40)
BALL_COLOR = (40, 90, 200)
AIM_COLOR = (255, 230, 120)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bowling Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24, bold=True)
big_font = pygame.font.SysFont("Arial", 40, bold=True)


class Pin:
    def __init__(self, x: float, y: float):
        self.start = pygame.Vector2(x, y)
        self.pos = pygame.Vector2(x, y)
        self.vel = pygame.Vector2(0, 0)
        self.alive = True

    def update(self):
        if not self.alive:
            return
        self.pos += self.vel
        self.vel *= FRICTION
        if self.vel.length() < STOP_SPEED:
            self.vel.update(0, 0)

        # Pin considered knocked if moved enough or left lane.
        if self.pos.distance_to(self.start) > 22:
            self.alive = False
        elif self.pos.x < LANE_X + 6 or self.pos.x > LANE_X + LANE_W - 6:
            self.alive = False
        elif self.pos.y < LANE_TOP + 6 or self.pos.y > LANE_BOTTOM - 6:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return
        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.circle(surface, PIN_COLOR, (x, y), PIN_RADIUS)
        pygame.draw.circle(surface, PIN_RED, (x, y - 3), 4, 2)


def build_pins() -> list[Pin]:
    pins = []
    rows = 4
    center_x = WIDTH // 2
    for row in range(rows):
        count = row + 1
        y = PIN_HEAD_Y + row * PIN_SPACING_Y
        row_w = (count - 1) * PIN_SPACING_X
        x0 = center_x - row_w / 2
        for i in range(count):
            pins.append(Pin(x0 + i * PIN_SPACING_X, y))
    return pins


ball_pos = BALL_START.copy()
ball_vel = pygame.Vector2(0, 0)
ball_moving = False
ball_radius_current = BALL_RADIUS

pins = build_pins()

throw_power = 24.0
throw_angle_deg = -90.0

frame_index = 1
throw_in_frame = 1
frame_knocked = 0
all_throws = []
total_score = 0

message = "Press LEFT/RIGHT to aim, UP/DOWN for power, SPACE to throw"
end_game = False
jokers_left = 3
joker_armed = False
joker_shot_active = False


def reset_ball():
    global ball_pos, ball_vel, ball_moving, ball_radius_current, joker_shot_active, joker_armed
    ball_pos = BALL_START.copy()
    ball_vel = pygame.Vector2(0, 0)
    ball_moving = False
    ball_radius_current = BALL_RADIUS
    joker_shot_active = False
    joker_armed = False


def reset_match():
    global pins, frame_index, throw_in_frame, frame_knocked, all_throws
    global total_score, end_game, message, throw_power, throw_angle_deg, jokers_left
    pins = build_pins()
    frame_index = 1
    throw_in_frame = 1
    frame_knocked = 0
    all_throws = []
    total_score = 0
    end_game = False
    throw_power = 24.0
    throw_angle_deg = -90.0
    jokers_left = 3
    message = "Press LEFT/RIGHT to aim, UP/DOWN for power, SPACE to throw"
    reset_ball()


def count_alive_pins() -> int:
    return sum(1 for p in pins if p.alive)


def apply_ball_pin_collisions():
    global ball_vel
    for pin in pins:
        if not pin.alive:
            continue
        diff = pin.pos - ball_pos
        dist = diff.length()
        min_dist = PIN_RADIUS + ball_radius_current
        if dist <= min_dist and dist > 0:
            normal = diff.normalize()
            impact = max(2.0, ball_vel.length() * 0.65)
            if joker_shot_active:
                impact *= 1.45
            pin.vel += normal * impact
            ball_vel *= 0.64 if joker_shot_active else 0.52
            ball_pos_update = normal * (min_dist - dist + 0.5)
            pin.pos += ball_pos_update * 0.6


def apply_pin_pin_collisions():
    for i in range(len(pins)):
        a = pins[i]
        if not a.alive:
            continue
        for j in range(i + 1, len(pins)):
            b = pins[j]
            if not b.alive:
                continue
            delta = b.pos - a.pos
            dist = delta.length()
            min_dist = PIN_RADIUS * 2
            if 0 < dist < min_dist:
                n = delta.normalize()
                overlap = (min_dist - dist) * 0.5
                a.pos -= n * overlap
                b.pos += n * overlap
                va = a.vel.dot(n)
                vb = b.vel.dot(n)
                a.vel += n * (vb - va) * 0.45
                b.vel += n * (va - vb) * 0.45


def objects_stopped() -> bool:
    if ball_vel.length() >= STOP_SPEED:
        return False
    for pin in pins:
        if pin.alive and pin.vel.length() >= STOP_SPEED:
            return False
    return True


def next_throw_or_frame(knocked_this_throw: int):
    global frame_index, throw_in_frame, frame_knocked, total_score, end_game, message

    frame_knocked += knocked_this_throw
    total_score += knocked_this_throw
    all_throws.append(knocked_this_throw)

    # Strike in first throw.
    if throw_in_frame == 1 and knocked_this_throw == 10:
        message = f"Frame {frame_index}: Strike!"
        frame_index += 1
        throw_in_frame = 1
        frame_knocked = 0
        return

    # After second throw, move to next frame.
    if throw_in_frame == 2:
        if frame_knocked == 10:
            message = f"Frame {frame_index}: Spare!"
        else:
            message = f"Frame {frame_index}: {frame_knocked} pins"
        frame_index += 1
        throw_in_frame = 1
        frame_knocked = 0
    else:
        throw_in_frame = 2

    if frame_index > 10:
        end_game = True
        message = "Game Over - Press R to play again"


def setup_for_current_throw():
    # New frame -> full rack, second throw -> keep standing pins.
    if throw_in_frame == 1:
        return build_pins()
    return pins


def draw_gradient_background():
    # Bright autumn sky
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(212 + 35 * (1 - t))
        g = int(226 + 20 * (1 - t))
        b = int(235 + 18 * (1 - t))
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Calm lake horizon
    lake_top = 390
    pygame.draw.rect(screen, (172, 188, 196), (0, lake_top, WIDTH, HEIGHT - lake_top))
    for y in range(lake_top, HEIGHT):
        k = (y - lake_top) / (HEIGHT - lake_top)
        c = int(176 - 30 * k)
        pygame.draw.line(screen, (c, c + 8, c + 14), (0, y), (WIDTH, y))

    # Distant shoreline and rocks
    pygame.draw.polygon(screen, (122, 130, 130), [(0, 390), (180, 360), (410, 374), (620, 350), (WIDTH, 385), (WIDTH, 430), (0, 430)])
    pygame.draw.ellipse(screen, (78, 84, 80), (620, 520, 90, 32))
    pygame.draw.ellipse(screen, (92, 98, 94), (710, 540, 110, 30))
    pygame.draw.ellipse(screen, (70, 76, 74), (790, 510, 80, 28))

    # Ground covered with leaves
    pygame.draw.polygon(screen, (178, 126, 42), [(0, HEIGHT), (0, 470), (240, 450), (430, 520), (520, HEIGHT)])
    pygame.draw.polygon(screen, (162, 112, 36), [(0, HEIGHT), (280, 520), (530, HEIGHT)])

    # Big tree trunk and branches
    trunk = [(120, 520), (145, 300), (210, 220), (250, 245), (222, 360), (215, 520)]
    pygame.draw.polygon(screen, (58, 42, 30), trunk)
    pygame.draw.line(screen, (58, 42, 30), (180, 280), (300, 220), 16)
    pygame.draw.line(screen, (58, 42, 30), (165, 260), (95, 175), 12)
    pygame.draw.line(screen, (58, 42, 30), (240, 260), (340, 180), 10)

    # Golden canopy blobs
    canopy_colors = [(224, 166, 30), (208, 151, 22), (236, 178, 48)]
    canopy_points = [
        (120, 165, 88), (200, 155, 96), (285, 165, 86),
        (90, 230, 75), (180, 225, 86), (270, 230, 80), (340, 220, 62),
    ]
    for i, (cx, cy, r) in enumerate(canopy_points):
        pygame.draw.circle(screen, canopy_colors[i % len(canopy_colors)], (cx, cy), r)

    # Scattered leaves on the foreground
    for i in range(120):
        x = (i * 37) % WIDTH
        y = 520 + (i * 23) % (HEIGHT - 520)
        color = (210 + (i % 20), 138 + (i % 25), 30)
        pygame.draw.ellipse(screen, color, (x, y, 8, 4))


def draw_lane():
    lane = pygame.Rect(LANE_X, LANE_TOP, LANE_W, LANE_BOTTOM - LANE_TOP)
    pygame.draw.rect(screen, LANE_DARK, lane, border_radius=8)
    inner = lane.inflate(-14, -8)
    pygame.draw.rect(screen, LANE_LIGHT, inner, border_radius=8)

    for i in range(7):
        y = LANE_TOP + 25 + i * 80
        pygame.draw.line(screen, (195, 165, 122), (LANE_X + 18, y), (LANE_X + LANE_W - 18, y), 1)

    pygame.draw.rect(screen, LANE_EDGE, (LANE_X - 12, LANE_TOP, 10, LANE_BOTTOM - LANE_TOP), border_radius=6)
    pygame.draw.rect(screen, LANE_EDGE, (LANE_X + LANE_W + 2, LANE_TOP, 10, LANE_BOTTOM - LANE_TOP), border_radius=6)


def draw_ui():
    title = big_font.render("BOWLING", True, TEXT)
    screen.blit(title, (24, 16))

    info = [
        f"Frame: {min(frame_index, 10)} / 10",
        f"Throw: {throw_in_frame}",
        f"Score: {total_score}",
        f"Standing pins: {count_alive_pins()}",
        f"Power: {throw_power:.1f}",
        f"Jokers: {jokers_left}",
    ]
    for i, line in enumerate(info):
        txt = font.render(line, True, TEXT)
        screen.blit(txt, (24, 86 + i * 30))

    msg = font.render(message, True, (250, 232, 140))
    screen.blit(msg, (24, HEIGHT - 38))


def draw_ball_and_aim():
    ball_color = (90, 20, 190) if joker_armed or joker_shot_active else BALL_COLOR
    pygame.draw.circle(screen, ball_color, (int(ball_pos.x), int(ball_pos.y)), int(ball_radius_current))
    pygame.draw.circle(screen, (25, 45, 120), (int(ball_pos.x), int(ball_pos.y)), int(ball_radius_current), 2)

    if not ball_moving and not end_game:
        angle = math.radians(throw_angle_deg)
        target = ball_pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * (40 + throw_power * 4)
        pygame.draw.line(screen, AIM_COLOR, ball_pos, target, 3)
        pygame.draw.circle(screen, AIM_COLOR, (int(target.x), int(target.y)), 5)


def launch_ball():
    global ball_vel, ball_moving, message, jokers_left, joker_shot_active, joker_armed, ball_radius_current
    angle = math.radians(throw_angle_deg)
    direction = pygame.Vector2(math.cos(angle), math.sin(angle))
    power = throw_power
    if joker_armed and jokers_left > 0:
        power *= 1.35
        jokers_left -= 1
        joker_shot_active = True
        ball_radius_current = BALL_RADIUS * 1.4
        message = "Joker Shot!"
    else:
        message = "Ball rolling..."
    joker_armed = False
    ball_vel = direction * power
    ball_moving = True


running = True
while running:
    dt = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                reset_match()
            elif not ball_moving and not end_game:
                if event.key == pygame.K_LEFT:
                    throw_angle_deg = max(-160, throw_angle_deg - 4)
                elif event.key == pygame.K_RIGHT:
                    throw_angle_deg = min(-20, throw_angle_deg + 4)
                elif event.key == pygame.K_UP:
                    throw_power = min(36, throw_power + 0.5)
                elif event.key == pygame.K_DOWN:
                    throw_power = max(5, throw_power - 0.5)
                elif event.key == pygame.K_j:
                    if jokers_left > 0 and not joker_armed:
                        joker_armed = True
                        message = "Joker armed! Press SPACE to launch"
                    elif joker_armed:
                        joker_armed = False
                        message = "Joker canceled"
                elif event.key == pygame.K_SPACE:
                    launch_ball()

    if ball_moving:
        before_alive = count_alive_pins()

        ball_pos += ball_vel
        ball_vel *= FRICTION

        # Bounce from lane sides.
        if ball_pos.x - ball_radius_current < LANE_X + 8:
            ball_pos.x = LANE_X + 8 + ball_radius_current
            ball_vel.x *= -0.5
        elif ball_pos.x + ball_radius_current > LANE_X + LANE_W - 8:
            ball_pos.x = LANE_X + LANE_W - 8 - ball_radius_current
            ball_vel.x *= -0.5

        apply_ball_pin_collisions()
        apply_pin_pin_collisions()

        for p in pins:
            p.update()

        # Ball reached end or stopped.
        if ball_pos.y < LANE_TOP + 20 or ball_pos.y > LANE_BOTTOM + 30 or objects_stopped():
            after_alive = count_alive_pins()
            knocked = before_alive - after_alive
            next_throw_or_frame(knocked)

            if not end_game:
                pins = setup_for_current_throw()
                reset_ball()

    draw_gradient_background()
    draw_lane()

    for p in pins:
        p.draw(screen)

    draw_ball_and_aim()
    draw_ui()

    if end_game:
        over = big_font.render("GAME OVER", True, (255, 210, 150))
        sub = font.render("Press R to restart", True, TEXT)
        screen.blit(over, (WIDTH - 305, 28))
        screen.blit(sub, (WIDTH - 280, 74))

    pygame.display.flip()

pygame.quit()
