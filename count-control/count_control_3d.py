"""
Count Control Legends — Pseudo-3D Edition
Move left/right → A/D or arrow keys
Pass through gates to change squad size
Crush enemies with more soldiers, beat the BOSS to win!
"""
import pygame
import random
import math
import sys

pygame.init()

W, H = 640, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Count Control Legends 3D")
clock = pygame.time.Clock()

# ── Colors ─────────────────────────────────────────────────────────────────────
SKY_TOP   = (10,  20,  60)
SKY_BOT   = (40, 100, 200)
GRASS1    = (30, 160,  50)
GRASS2    = (20, 120,  35)
ROAD1     = (70,  70,  90)
ROAD2     = (55,  55,  75)
LANE_W    = (220, 220, 240)
RUMBLE1   = (220,  50,  50)
RUMBLE2   = (240, 240, 240)
WHITE     = (255, 255, 255)
BLACK     = (0,   0,   0)
YELLOW    = (255, 230,  0)
GOLD      = (255, 200,  30)
ORANGE    = (255, 140,  0)
PLAYER_C  = (80, 180, 255)
ENEMY_C   = (255,  80,  80)
BOSS_C    = (200,  50, 200)
GATE_COLS = {'+': (50,220,50), '-': (220,80,80), 'x': (80,180,255), '/': (255,200,50)}

font_big  = pygame.font.SysFont("Arial", 52, bold=True)
font_med  = pygame.font.SysFont("Arial", 32, bold=True)
font_sm   = pygame.font.SysFont("Arial", 22, bold=True)
font_tiny = pygame.font.SysFont("Arial", 17)

# ── 3-D projection constants ───────────────────────────────────────────────────
HORIZON   = int(H * 0.42)      # y of horizon line
CAM_DEPTH = 0.84               # FOV control (lower = wider)
ROAD_W3D  = 1.8                # half-width of road in world units
NUM_SEGS  = 200                # visible road segments
SEG_LEN   = 220                # world units per segment
DRAW_DIST = NUM_SEGS           # segments to draw
CAM_HEIGHT = 1500              # camera height in world units

def project(world_x, world_y, world_z, cam_x, cam_z):
    """Project a 3-D world point to screen coords + scale."""
    dz = world_z - cam_z
    if dz <= 0:
        return None, None, 0
    scale = CAM_DEPTH / dz
    sx = W / 2 + (world_x - cam_x) * scale * W / 2
    sy = HORIZON  + world_y * scale * H
    return sx, sy, scale


# ── Particle ───────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = float(x); self.y = float(y); self.color = color
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.life = random.randint(20, 45)

    def update(self):
        self.x += self.vx; self.y += self.vy
        self.vy += 0.22; self.life -= 1

    def draw(self, surf):
        if self.life > 0:
            r = max(1, self.life // 9)
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


# ── Stickman in 3-D ────────────────────────────────────────────────────────────
def draw_stickman3d(surf, sx, sy, scale, color, anim=0):
    """Draw a stickman centred at (sx, sy) with depth-based scale."""
    r = max(1, int(9 * scale))
    leg = math.sin(anim * 0.25) * 6 * scale
    lw = max(1, int(2 * scale))
    # shadow ellipse
    pygame.draw.ellipse(surf, (0,0,0), (int(sx-r*1.3), int(sy+r*3.6), int(r*2.6), max(2,int(r*0.7))))
    # legs
    pygame.draw.line(surf, color, (int(sx), int(sy+r*1.8)), (int(sx-r+leg), int(sy+r*3.8)), lw)
    pygame.draw.line(surf, color, (int(sx), int(sy+r*1.8)), (int(sx+r-leg), int(sy+r*3.8)), lw)
    # body
    pygame.draw.line(surf, color, (int(sx), int(sy-r*0.3)), (int(sx), int(sy+r*1.8)), lw)
    # arms
    arm = math.sin(anim * 0.25 + 1.5) * 5 * scale
    pygame.draw.line(surf, color, (int(sx), int(sy+r*0.4)), (int(sx-r*1.4+arm), int(sy+r*1.5)), lw)
    pygame.draw.line(surf, color, (int(sx), int(sy+r*0.4)), (int(sx+r*1.4-arm), int(sy+r*1.5)), lw)
    # head
    pygame.draw.circle(surf, color, (int(sx), int(sy-r)), r)
    pygame.draw.circle(surf, WHITE,  (int(sx), int(sy-r)), r, max(1,lw-1))


# ── Gate ──────────────────────────────────────────────────────────────────────
class Gate:
    def __init__(self, z_pos):
        self.z   = z_pos
        self.passed = False
        self.flash  = 0
        ops = ['+', '-', 'x', '/']
        op_l = random.choice(ops);  val_l = Gate._rval(op_l)
        op_r = random.choice(ops);  val_r = Gate._rval(op_r)
        self.sides = [(-0.55, 0.95, op_l, val_l), (0.55, 0.95, op_r, val_r)]
        # left centre x, half-width, op, val

    @staticmethod
    def _rval(op):
        if op == '+': return random.randint(2, 15)
        if op == '-': return random.randint(1, 8)
        if op == 'x': return random.choice([2,3,4,5])
        if op == '/': return random.choice([2,3])

    def label(self, i):
        cx, hw, op, val = self.sides[i]
        sym = {'+':'+', '-':'-', 'x':'×', '/':'÷'}
        return f"{sym[op]}{val}"

    def apply(self, count, i):
        _, _, op, val = self.sides[i]
        if op == '+': return max(1, count + val)
        if op == '-': return max(1, count - val)
        if op == 'x': return count * val
        if op == '/': return max(1, count // val)

    def draw(self, surf, cam_x, cam_z, anim):
        dz = self.z - cam_z
        if dz <= 0 or dz > SEG_LEN * DRAW_DIST: return
        for i, (cx, hw, op, val) in enumerate(self.sides):
            col  = GATE_COLS[op]
            bright = tuple(min(255, c + (50 if self.flash > 0 else 0)) for c in col)
            # project the four corners of the gate arch
            left  = cx - hw * ROAD_W3D
            right = cx + hw * ROAD_W3D
            pts = []
            for wx, wy_frac in [(left, 0.0), (right, 0.0), (right, 0.55), (left, 0.55)]:
                sx, sy, sc = project(wx, -wy_frac * CAM_HEIGHT, self.z, cam_x, cam_z)
                if sx is None: pts = None; break
                pts.append((sx, sy))
            if pts is None: continue
            pygame.draw.polygon(surf, bright, pts)
            pygame.draw.polygon(surf, WHITE, pts, 2)
            # label
            _, sy_top, sc = project(cx, -0.28 * CAM_HEIGHT, self.z, cam_x, cam_z)
            sx_c, _, _   = project(cx, 0.0, self.z, cam_x, cam_z)
            if sy_top is None: continue
            fsize = max(10, int(28 * sc * 8))
            try:
                f = pygame.font.SysFont("Arial", fsize, bold=True)
            except Exception:
                f = font_sm
            txt = f.render(self.label(i), True, WHITE)
            surf.blit(txt, (int(sx_c) - txt.get_width()//2, int(sy_top) - txt.get_height()//2))
        if self.flash > 0: self.flash -= 1

    def collide_side(self, player_x, cam_x, cam_z):
        """Return index 0 or 1 if player passes through that side, else -1."""
        dz = self.z - cam_z
        if abs(dz) > SEG_LEN * 1.2: return -1
        if not (0 <= dz <= SEG_LEN * 1.6): return -1
        px = player_x
        for i, (cx, hw, op, val) in enumerate(self.sides):
            left  = (cx - hw * ROAD_W3D) * W * 0.30 + W/2
            right = (cx + hw * ROAD_W3D) * W * 0.30 + W/2
            if left <= px <= right:
                return i
        return -1


# ── Enemy ─────────────────────────────────────────────────────────────────────
class EnemyGroup:
    def __init__(self, z_pos, count, is_boss=False):
        self.z       = z_pos
        self.count   = count
        self.is_boss = is_boss
        self.alive   = True
        self.flash   = 0
        self.world_x = random.uniform(-0.5, 0.5)  # lane offset

    def draw(self, surf, cam_x, cam_z, anim):
        if not self.alive: return
        dz = self.z - cam_z
        if dz <= 0 or dz > SEG_LEN * DRAW_DIST: return
        sx, sy, sc = project(self.world_x, 0, self.z, cam_x, cam_z)
        if sx is None: return
        col = BOSS_C if self.is_boss else ENEMY_C
        n   = min(self.count, 10)
        cols_n = min(max(1, n), 5)
        for i in range(n):
            ocx = sx + (i % cols_n - cols_n / 2 + 0.5) * max(6, int(18 * sc * 4))
            ocy = sy - (i // cols_n) * max(4, int(16 * sc * 4))
            draw_stickman3d(surf, ocx, ocy, max(0.1, sc * 4), col, anim + i)
        # count badge
        fsize = max(10, int(26 * sc * 4))
        try:
            f = pygame.font.SysFont("Arial", fsize, bold=True)
        except Exception:
            f = font_sm
        badge = f.render(str(self.count), True, WHITE)
        rows_n = math.ceil(n / max(1, cols_n))
        bx = int(sx) - badge.get_width()//2
        by = int(sy) - rows_n * max(4, int(16*sc*4)) - badge.get_height() - 4
        pygame.draw.rect(surf, col, (bx-4, by-3, badge.get_width()+8, badge.get_height()+6), border_radius=6)
        surf.blit(badge, (bx, by))
        if self.is_boss:
            crown = font_tiny.render("👑 BOSS", True, GOLD)
            surf.blit(crown, (int(sx) - crown.get_width()//2, by - crown.get_height() - 2))
        if self.flash > 0: self.flash -= 1

    def collide(self, player_x, cam_x, cam_z):
        dz = self.z - cam_z
        if not (0 <= dz <= SEG_LEN * 2.0): return False
        sx, sy, sc = project(self.world_x, 0, self.z, cam_x, cam_z)
        if sx is None: return False
        return abs(player_x - sx) < max(20, int(60 * sc * 4))


# ── Road renderer ─────────────────────────────────────────────────────────────
def render_road(surf, cam_z, cam_x, scroll_frac):
    """Draw a pseudo-3D road using projected trapezoid strips."""
    prev_x1 = prev_x2 = prev_y = None

    for seg in range(1, NUM_SEGS + 1):
        z_near = cam_z + (seg - 1) * SEG_LEN / 8
        z_far  = cam_z +  seg      * SEG_LEN / 8

        def road_edge(z, side):
            dz = z - cam_z
            if dz <= 0: return W//2, H
            scale = CAM_DEPTH / dz
            sx = W/2 + side * ROAD_W3D * scale * W/2 - cam_x * scale * W/2
            sy = HORIZON + scale * CAM_HEIGHT
            return int(sx), int(sy)

        ln_x, ln_y = road_edge(z_near, -1)
        rn_x, rn_y = road_edge(z_near,  1)
        lf_x, lf_y = road_edge(z_far,  -1)
        rf_x, rf_y = road_edge(z_far,   1)

        if ln_y > H + 10: continue
        if rn_y < HORIZON: break

        alt = (int(cam_z / (SEG_LEN / 8)) + seg) % 2

        # grass
        pygame.draw.rect(surf, GRASS1 if alt else GRASS2, (0, lf_y, W, ln_y - lf_y + 1))

        # rumble strip (left & right edge)
        rumble_col = RUMBLE1 if alt else RUMBLE2
        rw = max(1, (rn_x - ln_x) // 20)
        pygame.draw.polygon(surf, rumble_col, [(ln_x-rw, ln_y), (lf_x-rw, lf_y), (lf_x, lf_y), (ln_x, ln_y)])
        pygame.draw.polygon(surf, rumble_col, [(rn_x, rn_y), (rf_x, rf_y), (rf_x+rw, rf_y), (rn_x+rw, rn_y)])

        # road surface
        road_col = ROAD1 if alt else ROAD2
        pygame.draw.polygon(surf, road_col, [(ln_x, ln_y), (lf_x, lf_y), (rf_x, rf_y), (rn_x, rn_y)])

        # centre lane dashes
        lc_x = (ln_x + rn_x)//2
        fc_x = (lf_x + rf_x)//2
        if alt:
            lane_w = max(1, (rn_x - ln_x)//40)
            pygame.draw.polygon(surf, LANE_W, [
                (lc_x - lane_w, ln_y), (fc_x - lane_w, lf_y),
                (fc_x + lane_w, lf_y), (lc_x + lane_w, ln_y)])


def draw_sky(surf):
    for i in range(HORIZON):
        t = i / HORIZON
        r = int(SKY_TOP[0]*(1-t) + SKY_BOT[0]*t)
        g = int(SKY_TOP[1]*(1-t) + SKY_BOT[1]*t)
        b = int(SKY_TOP[2]*(1-t) + SKY_BOT[2]*t)
        pygame.draw.line(surf, (r,g,b), (0,i), (W,i))
    # sun
    pygame.draw.circle(surf, (255, 240, 80), (W//2, HORIZON - 60), 38)
    pygame.draw.circle(surf, (255, 255, 200), (W//2, HORIZON - 60), 28)


# ── Main Game ─────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.state = 'menu'
        self.level = 1
        self.reset()

    def reset(self):
        self.count    = 5
        self.player_x = W // 2      # screen px, bottom centre
        self.cam_z    = 0.0         # camera Z in world units
        self.cam_x    = 0.0         # camera X offset (world)
        self.speed    = 0.35        # SEG_LEN units per frame
        self.anim     = 0
        self.score    = 0
        self.shake    = 0
        self.combo    = 0
        self.track_len = 800 + self.level * 200   # in SEG_LEN units
        self.finish_z  = self.track_len * SEG_LEN / 8
        self.boss_beaten = False
        self.particles = []
        self.gates    = []
        self.enemies  = []
        self._gen_level()

    def _gen_level(self):
        z = 60 * SEG_LEN / 8
        end_z = self.finish_z - 60 * SEG_LEN / 8
        while z < end_z:
            self.gates.append(Gate(z))
            z += random.uniform(40, 80) * SEG_LEN / 8
            if random.random() < 0.45:
                cnt = random.randint(2, 5 + self.level)
                self.enemies.append(EnemyGroup(z, cnt))
                z += 30 * SEG_LEN / 8
        # boss
        self.enemies.append(EnemyGroup(self.finish_z - 20 * SEG_LEN/8, 10 + self.level*5, is_boss=True))

    def handle_input(self, keys, dt):
        spd = 420
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.player_x -= spd * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.player_x += spd * dt
        # clamp inside road
        _, _, sc = project(0, 0, self.cam_z + SEG_LEN, self.cam_x, self.cam_z)
        road_px  = ROAD_W3D * (sc if sc else 0.4) * W/2
        margin   = int(road_px * 0.88)
        self.player_x = max(W//2 - margin, min(W//2 + margin, self.player_x))
        # sync cam_x
        self.cam_x = (self.player_x - W/2) / (W/2) * ROAD_W3D * 0.55

    def update(self, dt):
        if self.state != 'playing': return
        self.cam_z += self.speed * SEG_LEN / 8
        self.speed = min(1.2, self.speed + 0.0004)
        self.anim  += 1

        # gates
        for gate in self.gates:
            if gate.passed: continue
            idx = gate.collide_side(self.player_x, self.cam_x, self.cam_z)
            if idx >= 0:
                old = self.count
                self.count = gate.apply(self.count, idx)
                gate.passed = True
                gate.flash  = 12
                col = (50,220,50) if self.count >= old else (255,80,80)
                for _ in range(24): self.particles.append(Particle(self.player_x, H-120, col))

        # enemies
        for en in self.enemies:
            if not en.alive: continue
            if en.collide(self.player_x, self.cam_x, self.cam_z):
                if self.count > en.count:
                    self.score += en.count * 10 * (2 if en.is_boss else 1)
                    self.combo += 1
                    self.count += max(1, en.count // 2)
                    en.alive = False
                    col = BOSS_C if en.is_boss else ENEMY_C
                    for _ in range(35): self.particles.append(Particle(self.player_x, H-180, col))
                    self.shake = 14
                    if en.is_boss: self.boss_beaten = True
                else:
                    lose = en.count - self.count + 1
                    self.count = max(0, self.count - lose)
                    en.count   = max(0, en.count - self.count)
                    if en.count <= 0: en.alive = False
                    self.shake = 22
                    for _ in range(20): self.particles.append(Particle(self.player_x, H-120, (255,100,100)))
                    if self.count <= 0:
                        self.state = 'lose'; return

        # finish
        if self.cam_z >= self.finish_z and self.boss_beaten:
            self.state = 'win'

        # particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update()
        if self.shake > 0: self.shake -= 1

    def draw_world(self):
        ox = random.randint(-self.shake, self.shake) if self.shake else 0
        oy = random.randint(-self.shake//2, self.shake//2) if self.shake else 0
        draw_sky(screen)
        render_road(screen, self.cam_z, self.cam_x, 0)

        # depth-sort objects
        objs = []
        for g in self.gates:
            if not g.passed: objs.append(('gate', g, g.z))
        for en in self.enemies:
            if en.alive: objs.append(('enemy', en, en.z))
        # draw far→near
        objs.sort(key=lambda o: -o[2])
        for kind, obj, _ in objs:
            if kind == 'gate':  obj.draw(screen, self.cam_x, self.cam_z, self.anim)
            else:               obj.draw(screen, self.cam_x, self.cam_z, self.anim)

        # particles
        for p in self.particles: p.draw(screen)

        # finish ribbon
        fz = self.finish_z
        dz = fz - self.cam_z
        if 0 < dz < SEG_LEN * NUM_SEGS:
            lx, ly, _ = project(-ROAD_W3D, 0, fz, self.cam_x, self.cam_z)
            rx, ry, _ = project( ROAD_W3D, 0, fz, self.cam_x, self.cam_z)
            if lx and rx:
                h = max(4, int(abs(ry - HORIZON) * 0.06))
                for i in range(0, int(rx - lx), max(2, (int(rx-lx))//16)):
                    col = WHITE if (i//(max(2,(int(rx-lx))//16)))%2==0 else BLACK
                    pygame.draw.rect(screen, col, (int(lx)+i, int(ly)-h, max(2,(int(rx-lx))//16), h*2))
                ft = font_sm.render("FINISH", True, YELLOW)
                screen.blit(ft, (int((lx+rx)/2)-ft.get_width()//2, int(ly)-h-28))

        # player squad at bottom
        n   = min(self.count, 12)
        cols_n = min(max(1, n), 5)
        for i in range(n):
            cx = self.player_x + (i % cols_n - cols_n/2 + 0.5)*22 + ox
            cy = H - 110 - (i // cols_n) * 26 + oy
            draw_stickman3d(screen, cx, cy, 1.0, PLAYER_C, self.anim + i*3)

    def draw_hud(self):
        # count panel
        panel = pygame.Surface((170, 62), pygame.SRCALPHA)
        panel.fill((0,0,0,150))
        screen.blit(panel, (10, 10))
        ct = font_big.render(str(self.count), True, YELLOW)
        screen.blit(ct, (18, 12))
        lb = font_tiny.render("SQUAD", True, WHITE)
        screen.blit(lb, (18 + ct.get_width() + 8, 28))
        # score
        st = font_sm.render(f"Score: {self.score}", True, WHITE)
        screen.blit(st, (W - st.get_width() - 14, 14))
        # speed level
        sl = font_tiny.render(f"Lv {self.level}", True, GOLD)
        screen.blit(sl, (W - sl.get_width() - 14, 42))
        # progress bar
        prog = min(1.0, self.cam_z / self.finish_z)
        bw = 220; bx = W//2 - bw//2
        pygame.draw.rect(screen, (50,50,70), (bx, 10, bw, 20), border_radius=10)
        if prog > 0:
            pygame.draw.rect(screen, GOLD, (bx, 10, int(bw*prog), 20), border_radius=10)
        pygame.draw.rect(screen, WHITE, (bx, 10, bw, 20), 2, border_radius=10)
        pt = font_tiny.render("🏁 FINISH", True, WHITE)
        screen.blit(pt, (bx + bw - pt.get_width() - 4, 13))
        # combo
        if self.combo >= 2:
            ct2 = font_sm.render(f"COMBO ×{self.combo}!", True, ORANGE)
            screen.blit(ct2, (W//2 - ct2.get_width()//2, 42))

    # ── screens ───────────────────────────────────────────────────────────────
    def draw_menu(self):
        draw_sky(screen)
        # rolling road preview
        render_road(screen, pygame.time.get_ticks() * 0.04, 0.0, 0)
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0,0,0,140))
        screen.blit(overlay, (0,0))
        t1 = font_big.render("COUNT CONTROL", True, YELLOW)
        t2 = font_big.render("LEGENDS  3D", True, GOLD)
        screen.blit(t1, t1.get_rect(center=(W//2, H//3 - 10)))
        screen.blit(t2, t2.get_rect(center=(W//2, H//3 + 55)))
        for i in range(6):
            draw_stickman3d(screen, 80+i*90, H//2 - 10, 1.1+0.15*math.sin(pygame.time.get_ticks()*0.003+i),
                            PLAYER_C, pygame.time.get_ticks()//30+i*5)
        lines = ["← → or A/D to move", "Gates change squad size  (×2, +5, −3 …)",
                 "More soldiers than enemy → WIN fight", "Defeat BOSS to finish the level!"]
        for i, ln in enumerate(lines):
            t = font_tiny.render(ln, True, WHITE)
            screen.blit(t, t.get_rect(center=(W//2, H*11//18 + i*26)))
        btn = pygame.Rect(W//2-100, H-120, 200, 58)
        pygame.draw.rect(screen, GOLD, btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        screen.blit(font_med.render("PLAY!", True, BLACK), font_med.render("PLAY!", True, BLACK).get_rect(center=btn.center))
        return btn

    def draw_win(self):
        screen.fill((15, 60, 25))
        draw_sky(screen)
        overlay = pygame.Surface((W, H), pygame.SRCALPHA); overlay.fill((0,0,0,130)); screen.blit(overlay,(0,0))
        screen.blit(font_big.render("YOU WIN! 🏆", True, GOLD), font_big.render("YOU WIN! 🏆", True, GOLD).get_rect(center=(W//2, H//3)))
        screen.blit(font_med.render(f"Score: {self.score}", True, WHITE), font_med.render(f"Score: {self.score}", True, WHITE).get_rect(center=(W//2, H//3+70)))
        screen.blit(font_med.render(f"Squad: {self.count}", True, PLAYER_C), font_med.render(f"Squad: {self.count}", True, PLAYER_C).get_rect(center=(W//2, H//3+110)))
        # pyramid
        for col in range(1, 5):
            for row in range(col):
                draw_stickman3d(screen, W//2+(row-col/2+0.5)*32, H//2+(4-col)*38, 1.0, PLAYER_C, pygame.time.get_ticks()//30+col*3)
        btn = pygame.Rect(W//2-110, H-130, 220, 58)
        pygame.draw.rect(screen, GOLD, btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        screen.blit(font_med.render("NEXT LEVEL", True, BLACK), font_med.render("NEXT LEVEL", True, BLACK).get_rect(center=btn.center))
        return btn

    def draw_lose(self):
        screen.fill((50, 10, 10))
        overlay = pygame.Surface((W, H), pygame.SRCALPHA); overlay.fill((0,0,0,120)); screen.blit(overlay,(0,0))
        screen.blit(font_big.render("GAME OVER", True, (255,80,80)), font_big.render("GAME OVER", True, (255,80,80)).get_rect(center=(W//2, H//3)))
        screen.blit(font_med.render(f"Score: {self.score}", True, WHITE), font_med.render(f"Score: {self.score}", True, WHITE).get_rect(center=(W//2, H//3+70)))
        draw_stickman3d(screen, W//2, H//2+30, 1.4, (200,70,70), 0)
        btn = pygame.Rect(W//2-90, H-130, 180, 58)
        pygame.draw.rect(screen, (200,50,50), btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        screen.blit(font_med.render("RETRY", True, WHITE), font_med.render("RETRY", True, WHITE).get_rect(center=btn.center))
        return btn


def main():
    game = Game()
    while True:
        dt = clock.tick(60) / 1000.0
        click = False
        mpos  = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if game.state == 'playing': game.state = 'menu'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        if game.state == 'menu':
            btn = game.draw_menu()
            if click and btn.collidepoint(mpos): game.state = 'playing'

        elif game.state == 'playing':
            game.handle_input(pygame.key.get_pressed(), dt)
            game.update(dt)
            game.draw_world()
            game.draw_hud()

        elif game.state == 'win':
            btn = game.draw_win()
            if click and btn.collidepoint(mpos):
                game.level += 1; game.reset(); game.state = 'playing'

        elif game.state == 'lose':
            btn = game.draw_lose()
            if click and btn.collidepoint(mpos):
                game.reset(); game.state = 'playing'

        pygame.display.flip()

main()
