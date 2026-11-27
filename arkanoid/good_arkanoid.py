import pygame, sys, math

W, H, FPS = 800, 450, 60
pygame.init()
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

class Player:
    def __init__(self, x, y):
        self.r = pygame.Rect(x, y, 20, 32)
        self.vx, self.vy, self.g = 0, 0, 0.5
        self.ground = False

    def update(self, plats):
        self.vy = min(10, self.vy + self.g)
        self.r.x += self.vx
        for p in plats:
            if self.r.colliderect(p):
                self.r.right = p.left if self.vx > 0 else self.r.right
                self.r.left = p.right if self.vx < 0 else self.r.left
        self.ground = False
        self.r.y += self.vy
        for p in plats:
            if self.r.colliderect(p):
                if self.vy > 0: self.r.bottom, self.vy, self.ground = p.top, 0, True
                elif self.vy < 0: self.r.top, self.vy = p.bottom, 0

class Saw:
    def __init__(self, x, y, r, rng=0, ax='x', spd=2):
        self.x, self.y, self.radius = x, y, r
        self.sx, self.sy, self.rng, self.ax, self.spd, self.d, self.ang = x, y, rng, ax, spd, 1, 0

    def update(self):
        self.ang += 0.1
        if self.rng > 0:
            if self.ax == 'x':
                self.x += self.d * self.spd
                if abs(self.x - self.sx) >= self.rng: self.d *= -1
            else:
                self.y += self.d * self.spd
                if abs(self.y - self.sy) >= self.rng: self.d *= -1

# בניית 10 שלבים (B = פלטפורמות, S = מסורים, A = תפוחים)
B_BASE = [pygame.Rect(0, 420, 800, 30), pygame.Rect(0, 0, 30, 450), pygame.Rect(770, 0, 30, 450)]
LEVELS = [
    {'p': (80,300), 'b': B_BASE + [pygame.Rect(200,300,150,30)], 's': [Saw(275,280,15)], 'a': [pygame.Rect(250,250,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(200,320,100,20), pygame.Rect(400,240,100,20)], 's': [Saw(350,400,20,100)], 'a': [pygame.Rect(440,200,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(180,280,100,20), pygame.Rect(400,280,100,20)], 's': [Saw(320,400,15)], 'a': [pygame.Rect(440,240,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(250,200,30,220), pygame.Rect(450,250,100,30)], 's': [Saw(350,250,20,80,'y')], 'a': [pygame.Rect(500,200,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(200,330,300,30)], 's': [Saw(300,310,15,100,spd=4)], 'a': [pygame.Rect(400,280,12,12)]},
    {'p': (80,150), 'b': B_BASE + [pygame.Rect(30,200,120,20), pygame.Rect(250,300,120,20)], 's': [Saw(200,400,20)], 'a': [pygame.Rect(300,260,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(200,340,300,20), pygame.Rect(350,240,100,20)], 's': [Saw(350,150,20,80)], 'a': [pygame.Rect(400,200,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(200,250,120,20), pygame.Rect(450,250,120,20)], 's': [Saw(380,250,20,100,'x',3)], 'a': [pygame.Rect(510,200,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(200,350,60,20), pygame.Rect(400,250,60,20)], 's': [Saw(300,400,20)], 'a': [pygame.Rect(420,200,12,12)]},
    {'p': (80,350), 'b': B_BASE + [pygame.Rect(150,200,20,220), pygame.Rect(450,200,20,220)], 's': [Saw(300,300,20,100,'y',4)], 'a': [pygame.Rect(550,350,12,12)]}
]

lvl_idx = 0
def load():
    global ply, blks, saws, apps; d = LEVELS[lvl_idx]
    ply = Player(*d['p']); blks = d['b']; saws = d['s']; apps = [pygame.Rect(a.x, a.y, 12, 12) for a in d['a']]

load()
run = True
while run:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: run = False
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w) and ply.ground: ply.vy = -20

    k = pygame.key.get_pressed()
    ply.vx = 4 if k[pygame.K_RIGHT] or k[pygame.K_d] else (-4 if k[pygame.K_LEFT] or k[pygame.K_a] else 0)

    if lvl_idx < 10:
        ply.update(blks)
        for s in saws:
            s.update()
            if math.hypot(s.x - max(ply.r.left, min(s.x, ply.r.right)), s.y - max(ply.r.top, min(s.y, ply.r.bottom))) < s.radius: load()
        for a in apps[:]:
            if ply.r.colliderect(a): apps.remove(a)
        if not apps:
            lvl_idx += 1
            if lvl_idx < 10: load()

    screen.fill((40, 44, 52))
    for b in blks:
        pygame.draw.rect(screen, (139,69,19), b)
        pygame.draw.rect(screen, (34,139,34), (b.x, b.y, b.width, min(6, b.height)))
    for s in saws:
        pygame.draw.circle(screen, (169,169,169), (int(s.x), int(s.y)), s.radius)
    for a in apps: pygame.draw.circle(screen, (255,69,0), a.center, 6)
    
    if lvl_idx < 10:
        pygame.draw.rect(screen, (0,180,255), ply.r, border_radius=4)
        txt = pygame.font.SysFont(None, 24).render(f"Lvl: {lvl_idx+1}/10 | Left: {len(apps)}", True, (255,255,255))
        screen.blit(txt, (20, 20))
    else:
        win = pygame.font.SysFont(None, 50).render("You Win!", True, (0,255,0))
        screen.blit(win, (330, 200))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
