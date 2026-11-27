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
    # Deep-water blue gradient
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + 10 * (1 - t))
        g = int(62 + 130 * (1 - t))
        b = int(112 + 115 * (1 - t))
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Sun glow near the top center
    for i in range(7):
        rad = 170 - i * 24
        glow = (180 + i * 8, 220 + i * 4, 245)
        pygame.draw.circle(screen, glow, (WIDTH // 2 + 30, 70), rad, 1)

    # Light rays in water
    for i in range(10):
        x0 = 60 + i * 90
        pygame.draw.polygon(
            screen,
            (130, 200, 235),
            [(x0, 0), (x0 + 24, 0), (x0 + 95, HEIGHT), (x0 + 65, HEIGHT)],
            0,
        )

    # Fade light rays
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 50, 90, 145))
    screen.blit(overlay, (0, 0))

    # Distant rocks
    pygame.draw.ellipse(screen, (36, 70, 88), (620, 470, 120, 46))
    pygame.draw.ellipse(screen, (34, 64, 82), (735, 505, 130, 44))
    pygame.draw.ellipse(screen, (32, 58, 77), (520, 530, 96, 36))

    # Coral ground
    pygame.draw.polygon(screen, (20, 88, 98), [(0, HEIGHT), (0, 560), (240, 530), (430, 565), (WIDTH, 545), (WIDTH, HEIGHT)])

    # Left coral group (orange)
    for i in range(12):
        x = 35 + i * 14
        h = 48 + (i % 4) * 16
        pygame.draw.ellipse(screen, (230, 123 + (i % 3) * 10, 52), (x, HEIGHT - h - 15, 13, h))

    # Right coral group (pink + blue)
    for i in range(11):
        x = 700 + i * 13
        h = 46 + (i % 5) * 14
        color = (232, 92 + (i % 3) * 20, 170) if i % 2 == 0 else (82, 188, 218)
        pygame.draw.ellipse(screen, color, (x, HEIGHT - h - 20, 12, h))

    # Mid coral stones
    pygame.draw.ellipse(screen, (110, 156, 140), (250, 575, 86, 30))
    pygame.draw.ellipse(screen, (96, 140, 130), (350, 590, 110, 30))
    pygame.draw.ellipse(screen, (102, 150, 132), (468, 575, 90, 32))

    # Bubbles
    for i in range(55):
        bx = (i * 77) % WIDTH
        by = 520 - (i * 31) % 500
        br = 1 + (i % 3)
        pygame.draw.circle(screen, (175, 220, 238), (bx, by), br, 1)

    # Small fish silhouettes
    fish_colors = [(248, 164, 54), (243, 124, 45), (250, 204, 88)]
    fish_pos = [(130, 138), (780, 182), (690, 128), (815, 290), (86, 320)]
    for i, (fx, fy) in enumerate(fish_pos):
        c = fish_colors[i % len(fish_colors)]
        pygame.draw.ellipse(screen, c, (fx, fy, 34, 16))
        pygame.draw.polygon(screen, c, [(fx + 34, fy + 8), (fx + 45, fy + 2), (fx + 45, fy + 14)])
        pygame.draw.circle(screen, (20, 20, 20), (fx + 9, fy + 7), 1)

    # Many more background turtles (dense, deterministic pattern)
    turtle_groups = []
    for row in range(6):
        for col in range(14):
            tx = 24 + col * 62 + (row % 2) * 22
            ty = 90 + row * 55 + ((col * 17 + row * 11) % 14) - 7
            s = 7 + ((row + col) % 5)
            if tx < WIDTH - 60 and ty < HEIGHT - 120:
                turtle_groups.append((tx, ty, s))
    for tx, ty, s in turtle_groups:
        shell = (118, 108, 82)
        outline = (76, 66, 45)
        skin = (140, 136, 108)

        # shell
        shell_rect = pygame.Rect(tx, ty, int(s * 2.3), int(s * 1.6))
        pygame.draw.ellipse(screen, shell, shell_rect)
        pygame.draw.ellipse(screen, outline, shell_rect, 1)

        # head
        hx = shell_rect.right + int(s * 0.3)
        hy = shell_rect.centery - int(s * 0.1)
        pygame.draw.circle(screen, skin, (hx, hy), max(2, int(s * 0.35)))

        # flippers
        pygame.draw.ellipse(screen, skin, (shell_rect.left + 1, shell_rect.top - 1, max(3, int(s * 0.6)), max(2, int(s * 0.35))))
        pygame.draw.ellipse(screen, skin, (shell_rect.left + 1, shell_rect.bottom - max(3, int(s * 0.4)), max(3, int(s * 0.6)), max(2, int(s * 0.35))))
        pygame.draw.ellipse(screen, skin, (shell_rect.right - max(3, int(s * 0.7)), shell_rect.top - 1, max(3, int(s * 0.6)), max(2, int(s * 0.35))))
        pygame.draw.ellipse(screen, skin, (shell_rect.right - max(3, int(s * 0.7)), shell_rect.bottom - max(3, int(s * 0.4)), max(3, int(s * 0.6)), max(2, int(s * 0.35))))

        # shell marks
        pygame.draw.line(screen, outline, (shell_rect.left + 4, shell_rect.centery), (shell_rect.right - 4, shell_rect.centery), 1)
        pygame.draw.line(screen, outline, (shell_rect.centerx, shell_rect.top + 3), (shell_rect.centerx, shell_rect.bottom - 3), 1)


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


def draw_turtle_ball(surface: pygame.Surface, pos: pygame.Vector2, radius: float):
    x, y = int(pos.x), int(pos.y)
    # Visual-only scale (keeps physics unchanged, turtle looks bigger).
    r = max(10, int(radius * 1.35))

    # Natural turtle palette.
    shell_color = (146, 120, 78)
    shell_outline = (88, 67, 40)
    skin_color = (150, 132, 102)
    skin_shadow = (120, 103, 76)

    shell_rect = pygame.Rect(0, 0, int(r * 2.3), int(r * 1.8))
    shell_rect.center = (x, y)

    # Legs
    leg_w = max(8, int(r * 0.72))
    leg_h = max(12, int(r * 0.68))
    pygame.draw.ellipse(surface, skin_color, (shell_rect.left - int(leg_w * 0.55), shell_rect.top + 4, leg_w, leg_h))
    pygame.draw.ellipse(surface, skin_shadow, (shell_rect.left - int(leg_w * 0.45), shell_rect.bottom - leg_h - 4, leg_w, leg_h))
    pygame.draw.ellipse(surface, skin_color, (shell_rect.right - int(leg_w * 0.45), shell_rect.top + 4, leg_w, leg_h))
    pygame.draw.ellipse(surface, skin_shadow, (shell_rect.right - int(leg_w * 0.55), shell_rect.bottom - leg_h - 4, leg_w, leg_h))

    # Tail
    pygame.draw.polygon(surface, skin_color, [
        (shell_rect.left - max(4, r // 3), y),
        (shell_rect.left + 2, y - max(2, r // 5)),
        (shell_rect.left + 2, y + max(2, r // 5)),
    ])

    # Head (faces up lane)
    head_r = max(5, int(r * 0.4))
    head_center = (x, shell_rect.top - head_r + 3)
    pygame.draw.circle(surface, skin_color, head_center, head_r)
    pygame.draw.circle(surface, (30, 30, 30), (head_center[0] - 2, head_center[1] - 1), 1)
    pygame.draw.circle(surface, (30, 30, 30), (head_center[0] + 2, head_center[1] - 1), 1)

    # Shell
    pygame.draw.ellipse(surface, shell_color, shell_rect)
    pygame.draw.ellipse(surface, shell_outline, shell_rect, 2)

    # Shell pattern
    cx, cy = shell_rect.center
    pygame.draw.circle(surface, (124, 97, 56), (cx, cy), max(4, int(r * 0.42)), 2)
    pygame.draw.line(surface, shell_outline, (shell_rect.left + 6, cy), (shell_rect.right - 6, cy), 1)
    pygame.draw.line(surface, shell_outline, (cx, shell_rect.top + 5), (cx, shell_rect.bottom - 5), 1)
    pygame.draw.circle(surface, (110, 84, 48), (cx - max(3, r // 3), cy - max(2, r // 4)), max(2, r // 5), 1)
    pygame.draw.circle(surface, (110, 84, 48), (cx + max(3, r // 3), cy - max(2, r // 4)), max(2, r // 5), 1)
    pygame.draw.circle(surface, (110, 84, 48), (cx, cy + max(2, r // 4)), max(2, r // 5), 1)


def draw_ball_and_aim():
    draw_turtle_ball(screen, ball_pos, ball_radius_current)

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
