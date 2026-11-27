import math
import random
import pygame

pygame.init()

WIDTH, HEIGHT = 1280, 720
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Planet Destruction")
clock = pygame.time.Clock()

BG     = (5, 5, 18)
WHITE  = (240, 240, 255)
YELLOW = (255, 220, 60)
RED    = (240, 70, 60)
ORANGE = (255, 140, 40)
CYAN   = (60, 220, 255)
GREEN  = (80, 220, 120)
PURPLE = (200, 80, 240)
PINK   = (255, 100, 200)
LIME   = (170, 255, 60)

font       = pygame.font.SysFont("Arial", 24, bold=True)
small_font = pygame.font.SysFont("Arial", 16)
big_font   = pygame.font.SysFont("Arial", 64, bold=True)
med_font   = pygame.font.SysFont("Arial", 36, bold=True)

BG_IMAGE_PATH = "img/M31_09-01-2011_cropped-squared.jpg"
try:
    bg_image = pygame.image.load(BG_IMAGE_PATH).convert()
    bg_image = pygame.transform.smoothscale(bg_image, (WIDTH, HEIGHT))
except pygame.error:
    bg_image = None

EARTH_IMAGE_PATH = "img/314c4e13-5be3-49a0-b358-37710045fecb.png"
try:
    _earth_raw = pygame.image.load(EARTH_IMAGE_PATH).convert_alpha()
    earth_image = _earth_raw
except pygame.error:
    earth_image = None


class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, gravity=0.05):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.vx *= 0.98
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        ratio = max(0, self.life / self.max_life)
        r = min(255, int(self.color[0]))
        g = min(255, int(self.color[1] * ratio))
        b = min(255, int(self.color[2] * ratio * 0.5))
        size = max(1, int(self.size * ratio))
        pygame.draw.circle(surf, (r, g, b), (int(self.x), int(self.y)), size)


class LaserBeam:
    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2
        self.life = 20
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        w = max(1, self.life // 4)
        pygame.draw.line(surf, (255, 50, 50), (int(self.x1), int(self.y1)), (int(self.x2), int(self.y2)), w + 2)
        pygame.draw.line(surf, (255, 200, 200), (int(self.x1), int(self.y1)), (int(self.x2), int(self.y2)), max(1, w - 1))


class Asteroid:
    def __init__(self, target_x, target_y):
        side = random.randint(0, 3)
        if side == 0:
            self.x, self.y = random.randint(0, WIDTH), -60
        elif side == 1:
            self.x, self.y = WIDTH + 60, random.randint(0, HEIGHT)
        elif side == 2:
            self.x, self.y = random.randint(0, WIDTH), HEIGHT + 60
        else:
            self.x, self.y = -60, random.randint(0, HEIGHT)
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy) or 1
        speed = random.uniform(8, 14)
        self.vx = dx / dist * speed
        self.vy = dy / dist * speed
        self.size = random.randint(14, 28)
        self.angle = random.uniform(0, math.tau)
        self.spin = random.uniform(-0.08, 0.08)
        self.alive = True
        self.hit = False
        self.hit_x = target_x
        self.hit_y = target_y

    def update(self, planet):
        if not self.alive:
            return
        self.x += self.vx
        self.y += self.vy
        self.angle += self.spin
        dist = math.hypot(self.x - planet.x, self.y - planet.y)
        if dist < planet.radius + self.size:
            self.hit = True
            self.hit_x = int(self.x)
            self.hit_y = int(self.y)
            self.alive = False
        if self.x < -200 or self.x > WIDTH + 200 or self.y < -200 or self.y > HEIGHT + 200:
            self.alive = False

    def draw(self, surf):
        if not self.alive:
            return
        pts = []
        n = 7
        for i in range(n):
            a = self.angle + i * math.tau / n
            r = self.size * (0.7 if i % 2 == 0 else 0.6)
            pts.append((int(self.x + math.cos(a) * r), int(self.y + math.sin(a) * r)))
        pygame.draw.polygon(surf, (160, 140, 120), pts)
        pygame.draw.polygon(surf, (220, 200, 180), pts, 2)


class Mine:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timer = 120
        self.alive = True
        self.exploded = False

    def update(self, planet):
        self.timer -= 1
        if self.timer <= 0:
            self.exploded = True
            self.alive = False

    def draw(self, surf):
        blink = (self.timer % 20) < 10
        color = RED if blink else ORANGE
        pygame.draw.circle(surf, color, (int(self.x), int(self.y)), 12)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 12, 2)
        for i in range(6):
            a = i * math.tau / 6
            ex = int(self.x + math.cos(a) * 18)
            ey = int(self.y + math.sin(a) * 18)
            pygame.draw.line(surf, color, (int(self.x), int(self.y)), (ex, ey), 2)
        t = small_font.render(str(self.timer // 30 + 1), True, WHITE)
        surf.blit(t, (int(self.x) - 4, int(self.y) - 8))


class BlackHole:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.life = 180
        self.radius = 0
        self.max_radius = 60
        self.alive = True

    def update(self):
        if self.radius < self.max_radius:
            self.radius = min(self.max_radius, self.radius + 2)
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        r = int(self.radius)
        pygame.draw.circle(surf, (0, 0, 0), (int(self.x), int(self.y)), r)
        for i in range(3):
            ring_r = r + 8 + i * 8
            c = max(0, 180 - i * 50)
            pygame.draw.circle(surf, (c, 0, c), (int(self.x), int(self.y)), ring_r, 2)
        pygame.draw.circle(surf, PURPLE, (int(self.x), int(self.y)), r, 3)


class Lightning:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.bolts = []
        self.life = 30
        self.alive = True
        for _ in range(8):
            end_x = x + random.randint(-80, 80)
            end_y = y + random.randint(-80, 80)
            pts = [(x, y)]
            steps = 8
            for j in range(1, steps):
                px = x + (end_x - x) * j / steps + random.randint(-20, 20)
                py = y + (end_y - y) * j / steps + random.randint(-20, 20)
                pts.append((px, py))
            pts.append((end_x, end_y))
            self.bolts.append(pts)

    def update(self):
        self.life -= 2
        if self.life <= 0:
            self.alive = False

    def draw(self, surf):
        for bolt in self.bolts:
            for i in range(len(bolt) - 1):
                pygame.draw.line(surf, (200, 200, 255),
                                 (int(bolt[i][0]), int(bolt[i][1])),
                                 (int(bolt[i+1][0]), int(bolt[i+1][1])), 3)
                pygame.draw.line(surf, WHITE,
                                 (int(bolt[i][0]), int(bolt[i][1])),
                                 (int(bolt[i+1][0]), int(bolt[i+1][1])), 1)


class City:
    def __init__(self, px, py, radius, angle):
        self.planet_x = px
        self.planet_y = py
        self.angle = angle
        self.alive = True
        self.burning = False
        self.size = random.randint(6, 12)

    def draw(self, surf, x, y, radius):
        if not self.alive:
            return
        cx = x + int(math.cos(self.angle) * (radius + 2))
        cy = y + int(math.sin(self.angle) * (radius + 2))
        color = (200 + random.randint(-20,20), 80, 20) if self.burning else (180, 180, 220)
        bw = max(2, self.size // 3)
        for i in range(3):
            bh = self.size - i * 2
            bx = cx + (i - 1) * (bw + 1) - bw // 2
            pygame.draw.rect(surf, color, (bx, cy - bh, bw, bh))
        if self.burning and random.random() < 0.3:
            fx = cx + random.randint(-self.size, self.size)
            fy = cy - random.randint(0, self.size)
            pygame.draw.circle(surf, ORANGE, (fx, fy), random.randint(2, 4))


class Planet:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = radius
        self.alive = True
        self.hp = 1000
        self.max_hp = 1000
        self.particles = []
        self.lasers = []
        self.mines = []
        self.asteroids = []
        self.black_holes = []
        self.lightnings = []
        self.impact_marks = []
        self.atmosphere = 255
        self.rotation = 0
        self.shake_x = 0
        self.shake_y = 0
        self.shake_timer = 0
        self.cities = [City(x, y, radius, random.uniform(0, math.tau)) for _ in range(14)]

    def _shake(self, strength):
        self.shake_timer = max(self.shake_timer, strength)

    def apply_damage(self, hit_x, hit_y, damage, weapon, hit_radius=0):
        # Ignore attacks that do not intersect the current planet radius.
        if math.hypot(hit_x - self.x, hit_y - self.y) > self.radius + hit_radius:
            return 0
        self.hp = max(0, self.hp - damage)
        hp_ratio = self.hp / self.max_hp
        self.radius = self.max_radius * (0.3 + 0.7 * hp_ratio)
        self.atmosphere = max(0, int(255 * hp_ratio))
        self._shake(int(damage // 8))

        angle = math.atan2(hit_y - self.y, hit_x - self.x)
        color_map = {
            "laser": RED, "missile": ORANGE, "bomb": (255,100,20),
            "asteroid": (160,140,120), "mine": YELLOW,
            "blackhole": PURPLE, "lightning": CYAN, "nuke": LIME
        }
        self.impact_marks.append([angle, 255, color_map.get(weapon, ORANGE)])

        for city in self.cities:
            dist = math.hypot(
                self.x + math.cos(city.angle) * self.radius - hit_x,
                self.y + math.sin(city.angle) * self.radius - hit_y
            )
            if dist < self.radius * 0.5:
                if random.random() < 0.5:
                    city.alive = False
                else:
                    city.burning = True

        num = int(8 + damage * 0.4)
        for _ in range(num):
            a = random.uniform(0, math.tau)
            sp = random.uniform(2, 10)
            c = random.choice([ORANGE, RED, YELLOW, (200,120,50)])
            self.particles.append(Particle(
                hit_x + random.randint(-10,10),
                hit_y + random.randint(-10,10),
                math.cos(a)*sp, math.sin(a)*sp, c,
                random.randint(4,12), random.randint(40,100)
            ))
        for _ in range(num // 2):
            a = random.uniform(0, math.tau)
            sp = random.uniform(1, 3)
            g = random.randint(80, 160)
            self.particles.append(Particle(
                hit_x + random.randint(-15,15),
                hit_y + random.randint(-15,15),
                math.cos(a)*sp, math.sin(a)*sp,
                (g, g, g), random.randint(5,14),
                random.randint(30,70), gravity=-0.02
            ))
        if self.hp <= 0:
            self.alive = False
            for _ in range(100):
                a = random.uniform(0, math.tau)
                sp = random.uniform(3, 14)
                c = random.choice([ORANGE, RED, YELLOW, WHITE, LIME])
                self.particles.append(Particle(
                    self.x + random.uniform(-self.radius, self.radius),
                    self.y + random.uniform(-self.radius, self.radius),
                    math.cos(a)*sp, math.sin(a)*sp, c,
                    random.randint(6,20), random.randint(60,160)
                ))
        return damage

    def fire_weapon(self, mx, my, weapon):
        damage_map = {
            "laser": 50, "missile": 70, "bomb": 130,
            "asteroid": 100, "mine": 0, "blackhole": 40,
            "lightning": 55, "nuke": 200,
            "tsunami": 85, "meteor": 90, "solar": 150,
            "gravity": 170, "antimatter": 400
        }
        damage = damage_map.get(weapon, 60)
        dealt_damage = 0

        if weapon == "laser":
            src_x = random.choice([0, WIDTH])
            src_y = random.randint(80, HEIGHT - 80)
            for i in range(3):
                self.lasers.append(LaserBeam(
                    src_x + random.randint(-20,20),
                    src_y + random.randint(-20,20),
                    mx + random.randint(-8,8),
                    my + random.randint(-8,8)
                ))
            dealt_damage += self.apply_damage(mx, my, damage, weapon)

        elif weapon == "missile":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for _ in range(24):
                a = random.uniform(0, math.tau)
                self.particles.append(Particle(mx, my,
                    math.cos(a)*random.uniform(3,8),
                    math.sin(a)*random.uniform(3,8),
                    ORANGE, random.randint(3,9), 45
                ))

        elif weapon == "bomb":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for i in range(4):
                ox = mx + random.randint(-40,40)
                oy = my + random.randint(-40,40)
                dealt_damage += self.apply_damage(ox, oy, damage // 4, weapon)

        elif weapon == "asteroid":
            self.asteroids.append(Asteroid(mx, my))

        elif weapon == "mine":
            self.mines.append(Mine(mx, my))

        elif weapon == "blackhole":
            self.black_holes.append(BlackHole(mx, my))

        elif weapon == "lightning":
            self.lightnings.append(Lightning(mx, my))
            dealt_damage += self.apply_damage(mx, my, damage, weapon)

        elif weapon == "nuke":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for i in range(8):
                a = i * math.tau / 8
                dealt_damage += self.apply_damage(
                    int(mx + math.cos(a)*55),
                    int(my + math.sin(a)*55),
                    damage // 4, weapon
                )
            for _ in range(80):
                a = random.uniform(0, math.tau)
                sp = random.uniform(4, 16)
                self.particles.append(Particle(mx, my,
                    math.cos(a)*sp, math.sin(a)*sp,
                    random.choice([WHITE, YELLOW, ORANGE, LIME]),
                    random.randint(5,18), 90
                ))

        elif weapon == "tsunami":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for i in range(6):
                ox = mx + random.randint(-60, 60)
                oy = my + random.randint(-20, 20)
                dealt_damage += self.apply_damage(ox, oy, damage // 6, weapon)
            for _ in range(50):
                a = random.uniform(math.pi, math.tau)
                sp = random.uniform(3, 10)
                self.particles.append(Particle(mx, my,
                    math.cos(a)*sp, math.sin(a)*sp,
                    (40, 160, 255), random.randint(4,10), 55
                ))

        elif weapon == "meteor":
            for _ in range(3):
                self.asteroids.append(Asteroid(
                    mx + random.randint(-50, 50),
                    my + random.randint(-50, 50)
                ))
            damage = 90  # each asteroid deals 100, reported total = 90 placeholder

        elif weapon == "solar":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for i in range(6):
                src_y = HEIGHT // 2 + (i - 3) * 50
                self.lasers.append(LaserBeam(0, src_y, mx + random.randint(-15,15), my + random.randint(-15,15)))
            for _ in range(40):
                a = random.uniform(0, math.tau)
                sp = random.uniform(3, 12)
                self.particles.append(Particle(mx, my,
                    math.cos(a)*sp, math.sin(a)*sp,
                    random.choice([YELLOW, ORANGE, (255,240,80)]),
                    random.randint(4,14), 70
                ))

        elif weapon == "gravity":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for i in range(12):
                a = i * math.tau / 12
                dealt_damage += self.apply_damage(
                    int(mx + math.cos(a)*70),
                    int(my + math.sin(a)*70),
                    damage // 5, weapon
                )
            for _ in range(60):
                a = random.uniform(0, math.tau)
                dist = random.uniform(40, 100)
                sp = random.uniform(2, 8)
                # particles fly inward
                self.particles.append(Particle(
                    mx + math.cos(a)*dist,
                    my + math.sin(a)*dist,
                    -math.cos(a)*sp, -math.sin(a)*sp,
                    (160, 80, 255), random.randint(4,10), 40
                ))

        elif weapon == "antimatter":
            dealt_damage += self.apply_damage(mx, my, damage, weapon)
            for i in range(16):
                a = i * math.tau / 16
                dealt_damage += self.apply_damage(
                    int(mx + math.cos(a)*80),
                    int(my + math.sin(a)*80),
                    damage // 3, weapon
                )
                dealt_damage += self.apply_damage(
                    int(mx + math.cos(a)*150),
                    int(my + math.sin(a)*150),
                    damage // 5, weapon
                )
            for _ in range(120):
                a = random.uniform(0, math.tau)
                sp = random.uniform(5, 20)
                self.particles.append(Particle(mx, my,
                    math.cos(a)*sp, math.sin(a)*sp,
                    random.choice([WHITE, (255,255,255), CYAN, LIME, (255,200,255)]),
                    random.randint(6,20), 110
                ))

        return dealt_damage

    def update(self):
        self.rotation += 0.003
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_x = random.randint(-self.shake_timer, self.shake_timer)
            self.shake_y = random.randint(-self.shake_timer, self.shake_timer)
        else:
            self.shake_x = self.shake_y = 0

        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]

        for l in self.lasers:
            l.update()
        self.lasers = [l for l in self.lasers if l.alive]

        for m in self.mines:
            m.update(self)
            if m.exploded:
                self.apply_damage(int(m.x), int(m.y), 160, "mine")
        self.mines = [m for m in self.mines if m.alive]

        for a in self.asteroids:
            a.update(self)
            if a.hit:
                self.apply_damage(a.hit_x, a.hit_y, 100, "asteroid", hit_radius=a.size)
        self.asteroids = [a for a in self.asteroids if a.alive]

        for bh in self.black_holes:
            bh.update()
            dist = math.hypot(bh.x - self.x, bh.y - self.y)
            if dist < self.radius + bh.radius and bh.life % 10 == 0:
                self.apply_damage(int(bh.x), int(bh.y), 15, "blackhole", hit_radius=bh.radius)
        self.black_holes = [bh for bh in self.black_holes if bh.alive]

        for l in self.lightnings:
            l.update()
        self.lightnings = [l for l in self.lightnings if l.alive]

        self.impact_marks = [[a, max(0, i-2), c] for a, i, c in self.impact_marks if i > 0]

    def draw(self, surf):
        ox, oy = self.shake_x, self.shake_y
        x = int(self.x) + ox
        y = int(self.y) + oy
        r = max(5, int(self.radius))

        for l in self.lasers:
            l.draw(surf)

        # Atmosphere
        if self.atmosphere > 0:
            ar = 60 + int(60 * (1 - self.hp / self.max_hp))
            ab = int(180 * self.atmosphere / 255)
            for i in range(20, 0, -2):
                fade = int(28 * (1 - i/20) * self.atmosphere/255)
                pygame.draw.circle(surf, (ar, 80, ab), (x, y), r + i, 1)

        # Shadow
        pygame.draw.circle(surf, (15, 25, 55), (x + int(r*0.18), y + int(r*0.1)), r)

        # Base or Earth image
        hp_ratio = self.hp / self.max_hp
        if earth_image is not None and r > 10:
            diameter = r * 2
            scaled = pygame.transform.smoothscale(earth_image, (diameter, diameter))
            # Circular mask
            mask_surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(mask_surf, (255, 255, 255, 255), (r, r), r)
            masked = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            masked.blit(scaled, (0, 0))
            masked.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            # Tint red as HP decreases
            if hp_ratio < 1.0:
                tint = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
                tint_alpha = int((1 - hp_ratio) * 180)
                pygame.draw.circle(tint, (180, 40, 0, tint_alpha), (r, r), r)
                masked.blit(tint, (0, 0))
            surf.blit(masked, (x - r, y - r))
        else:
            oc = (
                int(40*hp_ratio + 120*(1-hp_ratio)),
                int(100*hp_ratio + 60*(1-hp_ratio)),
                int(200*hp_ratio + 30*(1-hp_ratio))
            )
            pygame.draw.circle(surf, oc, (x, y), r)

        # Lava core
        if self.hp < 700:
            lv = min(int(r * (1 - self.hp/900)), r - 4)
            if lv > 3:
                pygame.draw.circle(surf, (255,100,20), (x, y), lv)
                pygame.draw.circle(surf, (255,200,60), (x, y), max(2,int(lv*0.55)))
                pygame.draw.circle(surf, (255,255,180), (x, y), max(1,int(lv*0.25)))

        # Impact craters
        for mark_angle, intensity, mark_color in self.impact_marks:
            if intensity <= 0:
                continue
            mx_p = x + int(math.cos(mark_angle) * r * 0.7)
            my_p = y + int(math.sin(mark_angle) * r * 0.7)
            cr = max(3, int(14 * intensity / 255))
            pygame.draw.circle(surf, (30,15,5), (mx_p, my_p), cr)
            pygame.draw.circle(surf, mark_color, (mx_p, my_p), cr, 2)
            if intensity > 100:
                pygame.draw.circle(surf, (255,200,100), (mx_p, my_p), max(2,cr//3))

        # Cities
        for city in self.cities:
            city.draw(surf, x, y, r)

        # Specular
        hl_x = x - int(r*0.35)
        hl_y = y - int(r*0.38)
        pygame.draw.circle(surf, (180,220,255), (hl_x, hl_y), max(2,int(r*0.18)))
        pygame.draw.circle(surf, (220,240,255), (hl_x+3, hl_y+3), max(1,int(r*0.08)))

        pygame.draw.circle(surf, (180,210,255), (x, y), r, 2)

        for m in self.mines:
            m.draw(surf)
        for a in self.asteroids:
            a.draw(surf)
        for bh in self.black_holes:
            bh.draw(surf)
        for l in self.lightnings:
            l.draw(surf)
        for p in self.particles:
            p.draw(surf)

        # % destroyed label
        if r > 30 and self.hp < self.max_hp:
            pct = int((1 - self.hp/self.max_hp)*100)
            txt = small_font.render(f"{pct}%", True, WHITE)
            surf.blit(txt, (x - txt.get_width()//2, y - 8))


STARS = [(random.randint(0,WIDTH), random.randint(0,HEIGHT),
          random.randint(1,3), random.uniform(0, math.tau)) for _ in range(350)]


def draw_background(surf, t):
    if bg_image is not None:
        surf.blit(bg_image, (0, 0))
        # Light twinkle layer so the scene keeps a bit of animation.
        for sx, sy, ss, sp in STARS:
            b = 80 + int(50 * math.sin(t + sp))
            pygame.draw.circle(surf, (b, b, min(255, b + 30)), (sx, sy), max(1, ss - 1))
    else:
        surf.fill(BG)
        for i in range(0, HEIGHT, 4):
            nb = int(8 + 4 * math.sin(t * 0.3 + i * 0.015))
            pygame.draw.line(surf, (nb, nb // 2, nb * 2), (0, i), (WIDTH, i), 4)
        for sx, sy, ss, sp in STARS:
            b = 130 + int(80 * math.sin(t + sp))
            pygame.draw.circle(surf, (b, b, min(255, b + 40)), (sx, sy), ss)


WEAPONS = [
    {"id": "laser",     "name": "LASER",      "key": "1", "color": RED,            "desc": "Beam • 50 dmg"},
    {"id": "missile",   "name": "MISSILE",    "key": "2", "color": ORANGE,         "desc": "Blast • 70 dmg"},
    {"id": "bomb",      "name": "BOMB",       "key": "3", "color": YELLOW,         "desc": "Area • 130 dmg"},
    {"id": "asteroid",  "name": "ASTEROID",   "key": "4", "color": (160,140,120),  "desc": "Rock • 100 dmg"},
    {"id": "mine",      "name": "MINE",       "key": "5", "color": CYAN,           "desc": "Delayed • 160 dmg"},
    {"id": "blackhole", "name": "BLACK HOLE", "key": "6", "color": PURPLE,         "desc": "Suck • continuous"},
    {"id": "lightning", "name": "LIGHTNING",  "key": "7", "color": (180,180,255),  "desc": "Zap • 55 dmg"},
    {"id": "nuke",      "name": "NUKE",       "key": "8", "color": LIME,           "desc": "MEGA • 200 dmg"},
    {"id": "tsunami",   "name": "TSUNAMI",    "key": "9", "color": (40,160,255),   "desc": "Wave • 85 dmg"},
    {"id": "meteor",    "name": "METEORS",    "key": "0", "color": (200,130,70),   "desc": "Storm • 90x3 dmg"},
    {"id": "solar",     "name": "SOLAR FLARE","key": "q", "color": (255,240,80),   "desc": "Sun • 150 dmg"},
    {"id": "gravity",   "name": "GRAV BOMB",  "key": "w", "color": (160,80,255),   "desc": "Implode • 170 dmg"},
    {"id": "antimatter","name": "ANTIMATTER", "key": "e", "color": (255,255,255),   "desc": "ULTRA • 400 dmg"},
]

EXTRA_WEAPON_KEYS = "rtyuiopasdfghj"
EXTRA_KEY_TO_WEAPON = {
    k: WEAPONS[i % len(WEAPONS)]["id"]
    for i, k in enumerate(EXTRA_WEAPON_KEYS)
}

# Support both English and Hebrew keyboard layouts for weapon selection.
HEBREW_EXTRA_WEAPON_KEYS = "ראטוןםפשדגכעיח"
HEBREW_EXTRA_KEY_TO_WEAPON = {
    k: WEAPONS[i % len(WEAPONS)]["id"]
    for i, k in enumerate(HEBREW_EXTRA_WEAPON_KEYS)
}

UNICODE_KEY_TO_WEAPON = {
    "/": "solar",      # q key on Hebrew layout
    "'": "gravity",    # w key on Hebrew layout (common apostrophe)
    "׳": "gravity",    # Hebrew geresh
    "ק": "antimatter", # e key on Hebrew layout
}
UNICODE_KEY_TO_WEAPON.update(EXTRA_KEY_TO_WEAPON)
UNICODE_KEY_TO_WEAPON.update(HEBREW_EXTRA_KEY_TO_WEAPON)


def draw_weapon_bar(surf, selected):
    bar_h = 76
    bar_y = HEIGHT - bar_h - 10
    total_w = len(WEAPONS) * 88 + 8
    bar_x = WIDTH//2 - total_w//2

    panel = pygame.Surface((total_w + 10, bar_h + 14), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 140))
    surf.blit(panel, (bar_x - 5, bar_y - 7))

    for i, w in enumerate(WEAPONS):
        bx = bar_x + i * 88
        is_sel = w["id"] == selected
        bg_c = tuple(min(255, int(c * (0.6 if is_sel else 0.3))) for c in w["color"])
        border_c = WHITE if is_sel else (70, 70, 90)
        pygame.draw.rect(surf, bg_c, (bx, bar_y, 84, bar_h), border_radius=8)
        pygame.draw.rect(surf, border_c, (bx, bar_y, 84, bar_h), 2, border_radius=8)
        surf.blit(small_font.render(f"[{w['key']}]", True, (200,200,200)), (bx+5, bar_y+5))
        surf.blit(small_font.render(w["name"], True, WHITE if is_sel else (180,180,200)), (bx+5, bar_y+22))
        surf.blit(small_font.render(w["desc"], True, (150,150,170)), (bx+5, bar_y+44))


def draw_hud(surf, planet, score):
    pct = max(0.0, 1.0 - planet.hp / planet.max_hp)
    bar_w = 500
    bar_h = 28
    bx = WIDTH//2 - bar_w//2
    by = 14
    pygame.draw.rect(surf, (30,30,50), (bx, by, bar_w, bar_h), border_radius=5)
    fill_c = (int(60+195*pct), int(220-180*pct), 40)
    pygame.draw.rect(surf, fill_c, (bx, by, int(bar_w*pct), bar_h), border_radius=5)
    pygame.draw.rect(surf, (160,160,200), (bx, by, bar_w, bar_h), 2, border_radius=5)
    t = font.render(f"DESTRUCTION  {int(pct*100)}%", True, WHITE)
    surf.blit(t, (WIDTH//2 - t.get_width()//2, by+3))
    surf.blit(font.render(f"SCORE: {score}", True, YELLOW), (20, 14))
    surf.blit(small_font.render(f"HP: {max(0,int(planet.hp))}", True, (200,160,160)), (WIDTH-110, 14))


def reset_game():
    return {"planet": Planet(WIDTH//2, HEIGHT//2 - 20, 140), "score": 0, "weapon": "laser", "state": "play"}


game = reset_game()
running = True

while running:
    clock.tick(FPS)
    t = pygame.time.get_ticks() / 1000.0

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False
            if e.key == pygame.K_F5:
                game = reset_game()
            selected_from_alias = False
            for w in WEAPONS:
                attr = f"K_{w['key']}"
                if hasattr(pygame, attr) and e.key == getattr(pygame, attr):
                    game["weapon"] = w["id"]
                    selected_from_alias = True
                    break
            if not selected_from_alias:
                for key_char, weapon_id in EXTRA_KEY_TO_WEAPON.items():
                    attr = f"K_{key_char}"
                    if hasattr(pygame, attr) and e.key == getattr(pygame, attr):
                        game["weapon"] = weapon_id
                        selected_from_alias = True
                        break
            if not selected_from_alias:
                typed = (e.unicode or "").lower()
                if typed in UNICODE_KEY_TO_WEAPON:
                    game["weapon"] = UNICODE_KEY_TO_WEAPON[typed]
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1 and game["state"] == "play":
                mx, my = pygame.mouse.get_pos()
                planet = game["planet"]
                dmg = planet.fire_weapon(mx, my, game["weapon"])
                game["score"] += int(dmg)

    if game["state"] == "play":
        game["planet"].update()
        if not game["planet"].alive:
            game["state"] = "win"

    draw_background(screen, t)
    game["planet"].draw(screen)
    draw_hud(screen, game["planet"], game["score"])
    draw_weapon_bar(screen, game["weapon"])

    if game["state"] == "win":
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        screen.blit(ov, (0, 0))
        txt = big_font.render("PLANET DESTROYED!", True, RED)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2 - 120))
        sc = med_font.render(f"Final Score: {game['score']}", True, YELLOW)
        screen.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//2 - 20))
        r2 = font.render("Press F5 to play again", True, WHITE)
        screen.blit(r2, (WIDTH//2 - r2.get_width()//2, HEIGHT//2 + 60))

    pygame.display.flip()

pygame.quit()
