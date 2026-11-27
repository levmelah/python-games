import pygame
import random
import math
import sys

pygame.init()

W, H = 480, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Count Control Legends")
clock = pygame.time.Clock()

# Colors
BG_TOP    = (34, 180, 100)
BG_BOT    = (20, 120, 60)
ROAD_C    = (60, 60, 80)
LANE_C    = (255, 255, 255)
PLAYER_C  = (80, 180, 255)
ENEMY_C   = (255, 80, 80)
BOSS_C    = (200, 50, 200)
GATE_COLS = {'+': (50, 220, 50), '-': (220, 80, 80), 'x': (80, 180, 255), '/': (255, 200, 50)}
WHITE     = (255, 255, 255)
BLACK     = (0, 0, 0)
YELLOW    = (255, 230, 0)
ORANGE    = (255, 140, 0)
GOLD      = (255, 210, 50)
GRAY      = (160, 160, 170)

font_big   = pygame.font.SysFont("Arial", 52, bold=True)
font_med   = pygame.font.SysFont("Arial", 32, bold=True)
font_sm    = pygame.font.SysFont("Arial", 22, bold=True)
font_tiny  = pygame.font.SysFont("Arial", 17)

ROAD_LEFT  = 80
ROAD_RIGHT = 400
ROAD_W     = ROAD_RIGHT - ROAD_LEFT

# ── stickman drawing ──────────────────────────────────────────────────────────
def draw_stickman(surf, x, y, scale=1.0, color=PLAYER_C, anim=0):
    r = int(8 * scale)
    leg_swing = math.sin(anim * 0.3) * 6 * scale
    # shadow
    pygame.draw.ellipse(surf, (0,0,0,60), (int(x-r*1.2), int(y+r*3.8), int(r*2.4), int(r*0.8)))
    # legs
    pygame.draw.line(surf, color, (int(x), int(y+r*2)), (int(x - r + leg_swing), int(y + r*4)), max(1,int(2*scale)))
    pygame.draw.line(surf, color, (int(x), int(y+r*2)), (int(x + r - leg_swing), int(y + r*4)), max(1,int(2*scale)))
    # body
    pygame.draw.line(surf, color, (int(x), int(y-r*0.5)), (int(x), int(y+r*2)), max(1,int(2*scale)))
    # arms
    arm = math.sin(anim * 0.3 + 1.5) * 5 * scale
    pygame.draw.line(surf, color, (int(x), int(y+r*0.5)), (int(x-r*1.3+arm), int(y+r*1.8)), max(1,int(2*scale)))
    pygame.draw.line(surf, color, (int(x), int(y+r*0.5)), (int(x+r*1.3-arm), int(y+r*1.8)), max(1,int(2*scale)))
    # head
    pygame.draw.circle(surf, color, (int(x), int(y-r)), r)
    pygame.draw.circle(surf, WHITE,  (int(x), int(y-r)), r, 2)


# ── particles ─────────────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        self.x = x; self.y = y; self.color = color
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-5, -1)
        self.life = random.randint(20, 40)
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.2; self.life -= 1
    def draw(self, surf):
        if self.life > 0:
            alpha = max(0, int(255 * self.life / 40))
            r = max(1, self.life // 8)
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), r)


# ── gate ──────────────────────────────────────────────────────────────────────
class Gate:
    def __init__(self, y_pos):
        self.y = y_pos
        self.passed = False
        self.flash = 0
        mid = (ROAD_LEFT + ROAD_RIGHT) // 2
        gap = 20
        # left gate
        ops = ['+', '-', 'x', '/']
        op_l = random.choice(ops)
        val_l = self._rand_val(op_l)
        op_r = random.choice(ops)
        val_r = self._rand_val(op_r)
        self.gates = [
            {'x': ROAD_LEFT, 'w': mid - ROAD_LEFT - gap//2, 'op': op_l, 'val': val_l},
            {'x': mid + gap//2, 'w': ROAD_RIGHT - mid - gap//2, 'op': op_r, 'val': val_r},
        ]

    def _rand_val(self, op):
        if op == '+': return random.randint(2, 15)
        if op == '-': return random.randint(1, 8)
        if op == 'x': return random.choice([2, 3, 4, 5])
        if op == '/': return random.choice([2, 3])

    def label(self, g):
        sym = {'+':('+', g['val']), '-':('-', g['val']), 'x':('×', g['val']), '/':('÷', g['val'])}
        s, v = sym[g['op']]
        return f"{s}{v}"

    def apply(self, count, gate_idx):
        g = self.gates[gate_idx]
        op, val = g['op'], g['val']
        if op == '+': return max(1, count + val)
        if op == '-': return max(1, count - val)
        if op == 'x': return count * val
        if op == '/': return max(1, count // val)

    def draw(self, surf, scroll):
        sy = self.y - scroll
        if sy < -80 or sy > H + 80: return
        for i, g in enumerate(self.gates):
            col = GATE_COLS[g['op']]
            bright = tuple(min(255, c + (40 if self.flash > 0 else 0)) for c in col)
            rect = pygame.Rect(g['x'] + 4, int(sy) - 28, g['w'] - 8, 56)
            pygame.draw.rect(surf, bright, rect, border_radius=10)
            pygame.draw.rect(surf, WHITE, rect, 3, border_radius=10)
            txt = font_med.render(self.label(g), True, WHITE)
            surf.blit(txt, txt.get_rect(center=rect.center))
        if self.flash > 0: self.flash -= 1

    def get_rect(self, gate_idx, scroll):
        g = self.gates[gate_idx]
        sy = self.y - scroll
        return pygame.Rect(g['x'] + 4, int(sy) - 28, g['w'] - 8, 56)


# ── enemy group ───────────────────────────────────────────────────────────────
class EnemyGroup:
    def __init__(self, y_pos, count, is_boss=False):
        self.y = y_pos
        self.count = count
        self.is_boss = is_boss
        self.alive = True
        self.flash = 0
        self.x = (ROAD_LEFT + ROAD_RIGHT) // 2

    def draw(self, surf, scroll, anim):
        sy = self.y - scroll
        if sy < -100 or sy > H + 100: return
        col = BOSS_C if self.is_boss else ENEMY_C
        # draw stickmen
        n = min(self.count, 12)
        cols_n = min(n, 4)
        rows_n = math.ceil(n / cols_n)
        for i in range(n):
            cx = self.x + (i % cols_n - cols_n/2 + 0.5) * 22
            cy = sy - (i // cols_n) * 24
            draw_stickman(surf, cx, cy, scale=0.85, color=col, anim=anim+i)
        # count badge
        badge = font_med.render(str(self.count), True, WHITE)
        bx, by = self.x - badge.get_width()//2, int(sy) - rows_n*24 - 30
        pygame.draw.rect(surf, col, (bx-6, by-4, badge.get_width()+12, badge.get_height()+8), border_radius=8)
        surf.blit(badge, (bx, by))
        if self.is_boss:
            crown = font_sm.render("👑 BOSS", True, GOLD)
            surf.blit(crown, (self.x - crown.get_width()//2, by - 28))
        if self.flash > 0:
            self.flash -= 1

    def get_rect(self, scroll):
        sy = self.y - scroll
        return pygame.Rect(self.x - 50, int(sy) - 60, 100, 60)


# ── main game ─────────────────────────────────────────────────────────────────
class Game:
    def __init__(self):
        self.state = 'menu'  # menu / playing / win / lose / boss_fight
        self.reset()

    def reset(self):
        self.count   = 5
        self.px      = W // 2
        self.scroll  = 0
        self.speed   = 3.5
        self.anim    = 0
        self.particles = []
        self.score   = 0
        self.level   = 1
        self.track_len = 4000
        self.finish_y  = self.track_len - 200
        self.boss_beaten = False
        self.gates   = []
        self.enemies = []
        self._gen_level()
        self.shake = 0
        self.combo  = 0

    def _gen_level(self):
        self.gates   = []
        self.enemies = []
        y = 400
        while y < self.track_len - 400:
            self.gates.append(Gate(y))
            y += random.randint(220, 380)
            if random.random() < 0.4:
                cnt = random.randint(2, 6 + self.level)
                self.enemies.append(EnemyGroup(y, cnt))
                y += 200
        # boss at end
        self.enemies.append(EnemyGroup(self.track_len - 300, 10 + self.level * 5, is_boss=True))

    def handle_input(self, keys, dt):
        speed = 320
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.px -= speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.px += speed * dt
        self.px = max(ROAD_LEFT + 18, min(ROAD_RIGHT - 18, self.px))

    def player_rect(self):
        return pygame.Rect(self.px - 14, H - 130, 28, 70)

    def update(self, dt):
        if self.state != 'playing': return
        self.scroll += self.speed
        self.speed = min(6.0, self.speed + 0.0003)
        self.anim  += 1

        pr = self.player_rect()

        # gates
        for gate in self.gates:
            if gate.passed: continue
            sy = gate.y - self.scroll
            if abs(H - 130 - sy) < 40:
                for i, g in enumerate(gate.gates):
                    gr = gate.get_rect(i, self.scroll)
                    if pr.colliderect(gr):
                        old = self.count
                        self.count = gate.apply(self.count, i)
                        gate.passed = True
                        gate.flash = 10
                        diff = self.count - old
                        col = (50,230,50) if diff >= 0 else (255,80,80)
                        for _ in range(20): self.particles.append(Particle(self.px, H-130, col))
                        break

        # enemies
        for en in self.enemies:
            if not en.alive: continue
            er = en.get_rect(self.scroll)
            if pr.colliderect(er):
                if self.count > en.count:
                    self.score += en.count * 10 * (2 if en.is_boss else 1)
                    self.combo += 1
                    gain = en.count
                    self.count += gain // 2
                    en.alive = False
                    col = BOSS_C if en.is_boss else ENEMY_C
                    for _ in range(30): self.particles.append(Particle(en.x, en.y - self.scroll, col))
                    self.shake = 12
                    if en.is_boss:
                        self.boss_beaten = True
                else:
                    lose = en.count - self.count + 1
                    self.count = max(1, self.count - lose)
                    en.count   = max(0, en.count - self.count)
                    if en.count <= 0: en.alive = False
                    self.shake = 20
                    for _ in range(20): self.particles.append(Particle(self.px, H-130, (255,100,100)))
                    if self.count <= 0:
                        self.state = 'lose'
                        return

        # finish
        if self.scroll >= self.finish_y and self.boss_beaten:
            self.state = 'win'

        # particles
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update()
        if self.shake > 0: self.shake -= 1

    def draw_bg(self):
        # gradient road
        for i in range(H):
            t = i / H
            r = int(BG_TOP[0]*(1-t) + BG_BOT[0]*t)
            g = int(BG_TOP[1]*(1-t) + BG_BOT[1]*t)
            b = int(BG_TOP[2]*(1-t) + BG_BOT[2]*t)
            pygame.draw.line(screen, (r,g,b), (0,i),(W,i))
        # road
        pygame.draw.rect(screen, ROAD_C, (ROAD_LEFT, 0, ROAD_W, H))
        # lane dashes
        mid = (ROAD_LEFT + ROAD_RIGHT)//2
        dash_h = 40
        offset = self.scroll % (dash_h*2)
        y = -offset
        while y < H:
            pygame.draw.rect(screen, (200,200,220), (mid-3, int(y), 6, dash_h))
            y += dash_h * 2
        # road edges
        pygame.draw.rect(screen, (230,200,50), (ROAD_LEFT-6, 0, 6, H))
        pygame.draw.rect(screen, (230,200,50), (ROAD_RIGHT, 0, 6, H))

    def draw_finish_line(self):
        fy = self.finish_y - self.scroll
        if 0 < fy < H:
            for i in range(0, ROAD_W, 20):
                col = WHITE if (i//20)%2==0 else BLACK
                pygame.draw.rect(screen, col, (ROAD_LEFT+i, int(fy)-10, 20, 20))
            txt = font_med.render("FINISH", True, YELLOW)
            screen.blit(txt, (W//2 - txt.get_width()//2, int(fy)-40))

    def draw_player(self):
        sx = self.shake
        ox = random.randint(-sx, sx) if sx else 0
        oy = random.randint(-sx//2, sx//2) if sx else 0
        n = min(self.count, 15)
        cols_n = min(n, 5)
        rows_n = math.ceil(n / cols_n)
        for i in range(n):
            cx = self.px + (i % cols_n - cols_n/2 + 0.5) * 20 + ox
            cy = H - 110 - (i // cols_n) * 22 + oy
            draw_stickman(screen, cx, cy, scale=1.0, color=PLAYER_C, anim=self.anim+i*3)

    def draw_hud(self):
        # count panel
        panel = pygame.Surface((160, 60), pygame.SRCALPHA)
        panel.fill((0,0,0,140))
        screen.blit(panel, (10, 10))
        txt = font_big.render(str(self.count), True, YELLOW)
        screen.blit(txt, (18, 12))
        lbl = font_tiny.render("SQUAD", True, WHITE)
        screen.blit(lbl, (18 + txt.get_width() + 8, 28))

        # score
        stxt = font_sm.render(f"Score: {self.score}", True, WHITE)
        screen.blit(stxt, (W - stxt.get_width() - 14, 14))

        # progress bar
        prog = min(1.0, self.scroll / self.finish_y)
        bw = 200
        bx = W//2 - bw//2
        pygame.draw.rect(screen, (60,60,60), (bx, 10, bw, 18), border_radius=9)
        pygame.draw.rect(screen, GOLD, (bx, 10, int(bw*prog), 18), border_radius=9)
        pygame.draw.rect(screen, WHITE, (bx, 10, bw, 18), 2, border_radius=9)
        ptxt = font_tiny.render("FINISH", True, WHITE)
        screen.blit(ptxt, (bx + bw - ptxt.get_width() - 4, 13))

        # combo
        if self.combo >= 2:
            ctxt = font_sm.render(f"COMBO x{self.combo}!", True, ORANGE)
            screen.blit(ctxt, (W//2 - ctxt.get_width()//2, 50))

    def draw(self):
        self.draw_bg()
        self.draw_finish_line()
        for gate in self.gates: gate.draw(screen, self.scroll)
        for en   in self.enemies: en.draw(screen, self.scroll, self.anim)
        for p in self.particles: p.draw(screen)
        self.draw_player()
        self.draw_hud()

    def draw_menu(self):
        screen.fill((20, 60, 30))
        # title glow
        for off in range(5, 0, -1):
            t = font_big.render("COUNT CONTROL", True, (0, 100+off*20, 0))
            screen.blit(t, t.get_rect(center=(W//2+off, H//3+off)))
        t1 = font_big.render("COUNT CONTROL", True, YELLOW)
        t2 = font_big.render("LEGENDS", True, GOLD)
        screen.blit(t1, t1.get_rect(center=(W//2, H//3)))
        screen.blit(t2, t2.get_rect(center=(W//2, H//3+60)))
        # stickmen row
        for i in range(7):
            draw_stickman(screen, 60 + i*60, H//2, scale=1.2+(0.2*math.sin(pygame.time.get_ticks()*0.003+i)), color=PLAYER_C, anim=pygame.time.get_ticks()//30+i*5)
        inst = [
            "← → or A/D to move",
            "Go through gates to change squad size",
            "Beat enemies by having MORE soldiers",
            "Defeat the BOSS to win!",
        ]
        for i, line in enumerate(inst):
            t = font_tiny.render(line, True, WHITE)
            screen.blit(t, t.get_rect(center=(W//2, H*2//3 + i*26)))
        btn = pygame.Rect(W//2-90, H-110, 180, 55)
        pygame.draw.rect(screen, GOLD, btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        bt = font_med.render("PLAY!", True, BLACK)
        screen.blit(bt, bt.get_rect(center=btn.center))
        return btn

    def draw_win(self):
        screen.fill((20, 80, 30))
        t1 = font_big.render("YOU WIN! 🏆", True, GOLD)
        screen.blit(t1, t1.get_rect(center=(W//2, H//3)))
        t2 = font_med.render(f"Score: {self.score}", True, WHITE)
        screen.blit(t2, t2.get_rect(center=(W//2, H//3+70)))
        t3 = font_med.render(f"Squad left: {self.count}", True, PLAYER_C)
        screen.blit(t3, t3.get_rect(center=(W//2, H//3+110)))
        # draw winner pyramid
        for col in range(1, 4):
            for row in range(col):
                cx = W//2 + (row - col/2 + 0.5)*30
                cy = H//2 + (3-col)*40
                draw_stickman(screen, cx, cy, scale=1.0, color=PLAYER_C, anim=pygame.time.get_ticks()//30+col*3)
        btn = pygame.Rect(W//2-100, H-120, 200, 55)
        pygame.draw.rect(screen, GOLD, btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        bt = font_med.render("NEXT LEVEL", True, BLACK)
        screen.blit(bt, bt.get_rect(center=btn.center))
        return btn

    def draw_lose(self):
        screen.fill((60, 20, 20))
        t1 = font_big.render("GAME OVER", True, (255, 80, 80))
        screen.blit(t1, t1.get_rect(center=(W//2, H//3)))
        t2 = font_med.render(f"Score: {self.score}", True, WHITE)
        screen.blit(t2, t2.get_rect(center=(W//2, H//3+70)))
        t3 = font_sm.render("Your squad was wiped out!", True, GRAY)
        screen.blit(t3, t3.get_rect(center=(W//2, H//3+110)))
        draw_stickman(screen, W//2, H//2+40, scale=1.3, color=(200,80,80), anim=0)
        btn = pygame.Rect(W//2-90, H-120, 180, 55)
        pygame.draw.rect(screen, (200,60,60), btn, border_radius=14)
        pygame.draw.rect(screen, WHITE, btn, 3, border_radius=14)
        bt = font_med.render("RETRY", True, WHITE)
        screen.blit(bt, bt.get_rect(center=btn.center))
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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game.state == 'playing': game.state = 'menu'
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        if game.state == 'menu':
            btn = game.draw_menu()
            if click and btn.collidepoint(mpos):
                game.state = 'playing'

        elif game.state == 'playing':
            keys = pygame.key.get_pressed()
            game.handle_input(keys, dt)
            game.update(dt)
            game.draw()

        elif game.state == 'win':
            btn = game.draw_win()
            if click and btn.collidepoint(mpos):
                game.level += 1
                game.reset()
                game.state = 'playing'

        elif game.state == 'lose':
            btn = game.draw_lose()
            if click and btn.collidepoint(mpos):
                game.reset()
                game.state = 'playing'

        pygame.display.flip()

main()
