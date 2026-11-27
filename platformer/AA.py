"""
Platform Adventure  v1.1
Arrow Keys / WASD to move & jump  |  Jump ON enemies to defeat them
ESC = pause  |  R = restart  |  M = menu
"""
import pygame, sys, math, random, json, os
import array as _arr

pygame.init()
try: pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
except: pass

W, H, FPS = 960, 560, 60
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Platform Adventure  v1.1")
clock = pygame.time.Clock()

GRAV = 0.55; SPD = 5.2; JUMP_V = -14.5; JUMP_CUT = 0.5
COYOTE_T = 9; JUMP_BUF = 9; IFRAMES = 90; MAX_LIVES = 3; MAX_HP = 5

SKY0=(12,8,28); SKY1=(22,14,52)
PL=(28,42,82); PT=(65,130,216); PB=(16,26,52)
PC=(72,198,112)
EC=(212,55,55)
CC=(255,212,0); GC=(188,55,255)
WH=(255,255,255); BK=(0,0,0)
RD=(220,50,50); GD=(255,212,0)
GR=(108,108,152); DG=(46,46,76)
HC=(50,212,80); HB=(55,14,14)
MOV_C=(100,180,255)

_FL = {k: pygame.font.SysFont("Arial", s, bold=bool(b))
       for k,s,b in [("T",68,1),("H",44,1),("M",26,1),("S",18,1),("X",13,0)]}
def tx(s, k, c): return _FL[k].render(s, True, c)
def bc(surf, img, y): surf.blit(img, (W//2 - img.get_width()//2, y))

# ═══════════════════════════════════════════════════════════════ SOUND
def _bep(fr, ms, vol, sh="s"):
    rate=22050; n=rate*ms//1000; buf=_arr.array("h")
    for i in range(n):
        t=i/rate; e=max(0., 1-i/n)
        v = (math.sin(2*math.pi*fr*t) if sh=="s"
             else (1. if math.sin(2*math.pi*fr*t)>0 else -1.) if sh=="q"
             else random.uniform(-1,1))
        buf.append(max(-32768, min(32767, int(v*e*vol*32767))))
    try: return pygame.mixer.Sound(buffer=buf)
    except: return None
def _cho(fs, ms, vol):
    rate=22050; n=rate*ms//1000; buf=_arr.array("h")
    for i in range(n):
        t=i/rate; e=max(0., 1-i/n)
        v = sum(math.sin(2*math.pi*f*t) for f in fs)/len(fs)
        buf.append(max(-32768, min(32767, int(v*e*vol*32767))))
    try: return pygame.mixer.Sound(buffer=buf)
    except: return None
SFX = {}
for _n, _f in [("jmp",lambda:_bep(310,110,.22)),("coin",lambda:_bep(900,80,.18)),("gem",lambda:_cho([660,880,1100],220,.20)),
                ("stomp",lambda:_bep(110,140,.28,"q")),("hurt",lambda:_bep(170,210,.28,"q")),("done",lambda:_cho([440,554,660],420,.22)),
                ("sel",lambda:_bep(440,75,.15)),("die",lambda:_bep(90,500,.30,"q"))]:
    try: SFX[_n] = _f()
    except: pass
def sfx(k):
    s = SFX.get(k)
    if s:
        try: s.play()
        except: pass

# ═══════════════════════════════════════════════════════════════ HIGH SCORE
_HSF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "AA_highscore.json")
def load_hs():
    try:
        with open(_HSF) as f: return json.load(f).get("hs", 0)
    except: return 0
def save_hs(s):
    try:
        with open(_HSF, "w") as f: json.dump({"hs": s}, f)
    except: pass

# ═══════════════════════════════════════════════════════════════ PARTICLES
_ps = []
def emit(x, y, col, n=8, sp=3.5, g=.15):
    for _ in range(n):
        a=random.uniform(0,math.pi*2); v=random.uniform(sp*.3,sp)
        _ps.append([float(x),float(y),math.cos(a)*v,math.sin(a)*v,
                    random.randint(14,26),random.randint(14,26),random.randint(3,6),col,g])
def emit_up(x, y, col, n=6, sp=4.5):
    for _ in range(n):
        a=random.uniform(-math.pi*.85,-math.pi*.15); v=random.uniform(sp*.4,sp)
        _ps.append([float(x),float(y),math.cos(a)*v,math.sin(a)*v,
                    random.randint(18,32),random.randint(18,32),random.randint(2,5),col,.08])
def upd_ps():
    k=[]
    for p in _ps:
        p[2]*=.95; p[0]+=p[2]; p[1]+=p[3]; p[3]+=p[8]; p[4]-=1
        if p[4]>0: k.append(p)
    _ps[:] = k
def draw_ps(s, cx, cy):
    for p in _ps:
        a=p[4]/p[5]; r=max(1,int(p[6]*a))
        sx,sy=int(p[0]-cx),int(p[1]-cy)
        if -r<sx<W+r and -r<sy<H+r:
            pygame.draw.circle(s,(p[7][0],p[7][1],p[7][2],30),(sx,sy),int(r*1.8),1)
            pygame.draw.circle(s,p[7],(sx,sy),r)
            pygame.draw.circle(s,(255,255,255,100),(sx,sy),max(1,r//2))

# ═══════════════════════════════════════════════════════════════ BACKGROUND
random.seed(42)
_STARS = [(random.randint(0,5000), random.randint(0,H//2), random.uniform(.4,1.)) for _ in range(100)]
_HILLS = [(random.randint(0,5000), H, random.randint(50,160), random.randint(70,190)) for _ in range(28)]
random.seed()
def draw_bg(surf, cx, fr):
    for y in range(0, H, 3):
        t=y/H
        r=int(SKY0[0]*(1-t)+SKY1[0]*t); g=int(SKY0[1]*(1-t)+SKY1[1]*t); b=int(SKY0[2]*(1-t)+SKY1[2]*t)
        pygame.draw.rect(surf, (r,g,b), (0,y,W,3))
    for sx,sy,br in _STARS:
        px=int((sx-cx*.05)%W)
        a=int(140+math.sin(fr*.02+sx*.1)*50)
        pygame.draw.circle(surf,(a//2,a//2,a+40,80),(px,sy),int(2 if br<.6 else 3),1)
        pygame.draw.circle(surf,(a,a,min(255,a+30)),(px,sy),1 if br<.6 else 2)
    for hx,hy,hw,hh in _HILLS:
        px=int((hx-cx*.25)%W)
        pygame.draw.polygon(surf,(8,6,20),[(px-hw//2,hy),(px,hy-hh),(px+hw//2,hy)])
        pygame.draw.polygon(surf,(16,12,38),[(px-hw//2,hy),(px,hy-hh),(px+hw//2,hy)])
        pygame.draw.line(surf,(30,25,55),(px-hw//2+5,hy-2),(px,hy-hh+3),1)
def draw_world(surf, plats, mov, cx, cy, fr, finish_x):
    draw_bg(surf, cx, fr)
    fx=int(finish_x-cx)
    if -20<fx<W+60:
        p=int(math.sin(fr*.1)*3)
        pygame.draw.rect(surf,(0,0,0,80),(fx+2,380-p,6,130))
        pygame.draw.rect(surf,(55,175,55),(fx,380-p,10,130))
        pygame.draw.rect(surf,(80,200,80),(fx,380-p,3,130))
        pygame.draw.polygon(surf,(255,230,50,80),[(fx+10,380-p),(fx+52,400-p),(fx+10,420-p)])
        pygame.draw.polygon(surf,GD,[(fx+10,380-p),(fx+52,400-p),(fx+10,420-p)])
        pygame.draw.polygon(surf,(255,255,200),[(fx+12,383-p),(fx+50,400-p),(fx+12,417-p)],1)
        fi=tx("FINISH","S",GD); surf.blit(fi,(fx-fi.get_width()//2,362-p))
    for m in mov:
        sx=int(m["cx"]-cx); sy=int(m["cy"]-cy)
        if -20<sx<W+20:
            pygame.draw.rect(surf,(0,0,0,50),(sx+1,sy+m["h"],m["w"],3))
            pygame.draw.rect(surf,(100,180,255,50),(sx-2,sy-2,m["w"]+4,m["h"]+4),2,border_radius=3)
            pygame.draw.rect(surf,PL,(sx,sy,m["w"],m["h"]),border_radius=3)
            pygame.draw.rect(surf,MOV_C,(sx+3,sy,m["w"]-6,3))
            pygame.draw.rect(surf,(80,140,255),(sx,sy,m["w"],m["h"]),2,border_radius=3)
    for p in plats:
        sx=int(p[0]-cx); sy=int(p[1]-cy)
        if sx<-p[2] or sx>W: continue
        pygame.draw.rect(surf,(0,0,0,40),(sx+1,sy+p[3],p[2],2))
        pygame.draw.rect(surf,PL,(sx,sy,p[2],p[3]),border_radius=3)
        pygame.draw.rect(surf,PT,(sx+3,sy,p[2]-6,3))
        pygame.draw.rect(surf,PB,(sx,sy+3,2,p[3]-3))
        pygame.draw.rect(surf,(65,150,255,100),(sx-1,sy-1,p[2]+2,p[3]+2),1,border_radius=3)

# ═══════════════════════════════════════════════════════════════ MOVING PLATFORMS
def upd_mov(mov):
    for m in mov:
        m["t"] += 0.022 * m["spd"]
        offset = math.sin(m["t"]) * m["dist"]
        if m["axis"] == "h":
            nx = m["x0"]+offset; m["vel"]=nx-m["cx"]; m["cx"]=nx; m["cy"]=m["y0"]
        else:
            ny = m["y0"]+offset; m["vel"]=ny-m["cy"]; m["cy"]=ny; m["cx"]=m["x0"]

# ═══════════════════════════════════════════════════════════════ PLAYER
class Player:
    PW, PH = 30, 38
    def __init__(self, x, y):
        self.x=float(x); self.y=float(y)
        self.vx=0.; self.vy=0.
        self.on_ground=False; self.hp=MAX_HP
        self.iframes=0; self.coyote=0; self.jbuf=0
        self.facing=1; self.anim=0; self.lives=MAX_LIVES
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.PW, self.PH)
    def respawn(self, x, y):
        self.x=float(x); self.y=float(y)
        self.vx=0.; self.vy=0.; self.on_ground=False; self.iframes=IFRAMES
    def update(self, keys, plats, mov):
        self.anim += 1
        self.iframes = max(0, self.iframes-1)
        self.jbuf    = max(0, self.jbuf-1)
        self.vx = 0
        jump_held = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE]
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.vx=-SPD; self.facing=-1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.vx= SPD; self.facing= 1
        if jump_held:
            self.jbuf = JUMP_BUF
        if self.on_ground: self.coyote = COYOTE_T
        else:              self.coyote = max(0, self.coyote-1)
        if self.jbuf>0 and self.coyote>0:
            self.vy=JUMP_V; self.coyote=0; self.jbuf=0; sfx("jmp")
        # Variable jump height: releasing the jump key early cuts the ascent short
        elif not jump_held and self.vy < JUMP_V*JUMP_CUT:
            self.vy = JUMP_V*JUMP_CUT
        self.vy = min(self.vy+GRAV, 18)
        self.x += self.vx; self.y += self.vy
        self.on_ground = False
        all_p = list(plats) + [(int(m["cx"]),int(m["cy"]),m["w"],m["h"]) for m in mov]
        n_stat = len(plats)
        pr = self.rect()
        carry = 0.
        for i, p in enumerate(all_p):
            pr2 = pygame.Rect(p[0],p[1],p[2],p[3])
            if not pr.colliderect(pr2): continue
            ob=(self.y+self.PH)-p[1]; ot=(p[1]+p[3])-self.y
            ol=(self.x+self.PW)-p[0]; or_=(p[0]+p[2])-self.x
            mn=min(ob,ot,ol,or_)
            if mn==ob and self.vy>=0:
                self.y=p[1]-self.PH; self.vy=0; self.on_ground=True
                if i>=n_stat and mov[i-n_stat]["axis"]=="h":
                    carry = mov[i-n_stat]["vel"]
            elif mn==ot: self.y=p[1]+p[3]; self.vy=max(0,self.vy)
            elif mn==ol: self.x=p[0]-self.PW
            else:        self.x=p[0]+p[2]
            pr=self.rect()
        if carry and self.on_ground: self.x += carry
        self.x = max(0., self.x)
    def hurt(self, shake):
        if self.iframes > 0: return False
        self.hp -= 1; self.iframes = IFRAMES; sfx("hurt"); shake[0] = 14
        emit(self.x+15, self.y+19, RD, 10, 5)
        return True
    def draw(self, surf, cx, cy):
        sx=int(self.x-cx); sy=int(self.y-cy)
        if sx<-50 or sx>W+50: return
        if self.iframes>0 and (self.iframes//5)%2==1: return
        pygame.draw.ellipse(surf,(0,0,0,60),(sx+4,sy+self.PH+2,22,5))
        pygame.draw.rect(surf, PC, (sx,sy,self.PW,self.PH), border_radius=7)
        pygame.draw.rect(surf, (100,220,150), (sx,sy,self.PW,self.PH), 2, border_radius=7)
        ex = sx+18 if self.facing==1 else sx+4
        pygame.draw.rect(surf, WH, (ex, sy+10, 7, 7), border_radius=2)
        pygame.draw.rect(surf, BK, (ex+2, sy+12, 3, 3))
        pygame.draw.circle(surf, WH, (ex+4, sy+11), 1)
        pygame.draw.arc(surf, BK, (sx+9,sy+22,12,8), math.pi, 2*math.pi, 2)
        lv = int(math.sin(self.anim*.28)*5)
        pygame.draw.rect(surf,(40,150,80),(sx+4,  sy+self.PH,8,5+abs(lv)), border_radius=2)
        pygame.draw.rect(surf,(40,150,80),(sx+18, sy+self.PH,8,5-abs(lv)+3), border_radius=2)

# ═══════════════════════════════════════════════════════════════ ENEMY
class Enemy:
    EW, EH = 28, 28
    def __init__(self, x, y, x0, x1, spd):
        self.x=float(x); self.y=float(y)
        self.x0=x0; self.x1=x1; self.spd=spd; self.dir=1
        self.alive=True; self.anim=random.randint(0,40)
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.EW, self.EH)
    def update(self):
        if not self.alive: return
        self.anim+=1; self.x+=self.spd*self.dir
        if self.x>=self.x1 or self.x<=self.x0: self.dir*=-1
    def draw(self, surf, cx, cy):
        if not self.alive: return
        sx=int(self.x-cx); sy=int(self.y-cy)
        if sx<-40 or sx>W+40: return
        bob=int(math.sin(self.anim*.12)*2)
        pygame.draw.ellipse(surf,(0,0,0,50),(sx+2,sy+bob+self.EH,24,4))
        pygame.draw.circle(surf,(212,55,55,40),(sx+14,sy+bob+14),22,1)
        pygame.draw.rect(surf, EC, (sx,sy+bob,self.EW,self.EH), border_radius=5)
        pygame.draw.rect(surf, (255,100,100), (sx,sy+bob,self.EW,self.EH), 2, border_radius=5)
        pygame.draw.rect(surf, WH, (sx+4, sy+bob+5,7,7), border_radius=1)
        pygame.draw.rect(surf, WH, (sx+17,sy+bob+5,7,7), border_radius=1)
        pygame.draw.rect(surf, BK, (sx+6, sy+bob+7,3,3))
        pygame.draw.rect(surf, BK, (sx+19,sy+bob+7,3,3))
        pygame.draw.circle(surf, WH, (sx+8, sy+bob+6), 1)
        pygame.draw.circle(surf, WH, (sx+21, sy+bob+6), 1)
        pygame.draw.line(surf,BK,(sx+4,sy+bob+3),(sx+11,sy+bob+7),2)
        pygame.draw.line(surf,BK,(sx+24,sy+bob+3),(sx+17,sy+bob+7),2)

# ═══════════════════════════════════════════════════════════════ HUD & UI
def draw_hud(surf, player, score, cgot, ctot, level, hs, fr, ww):
    bar=pygame.Surface((W,54),pygame.SRCALPHA); bar.fill((0,0,0,145))
    surf.blit(bar,(0,0))
    pygame.draw.line(surf,(65,130,216),(0,0),(W,0),2)
    hx,hy,hw,hh = 10,10,140,14
    pygame.draw.rect(surf,(55,14,14,80),(hx-2,hy-2,hw+4,hh+4),border_radius=6)
    pygame.draw.rect(surf,HB,(hx,hy,hw,hh),border_radius=6)
    fill=max(0,int(hw*player.hp/MAX_HP))
    col=HC if player.hp>2 else (212,180,20) if player.hp>1 else RD
    pygame.draw.rect(surf,(col[0],col[1],col[2],100),(hx-1,hy-1,fill+2,hh+2),border_radius=6)
    pygame.draw.rect(surf,col,(hx,hy,fill,hh),border_radius=6)
    pygame.draw.rect(surf,WH,(hx,hy,hw,hh),2,border_radius=6)
    surf.blit(tx("HP","X",WH),(hx+3,hy))
    for i in range(player.lives):
        pygame.draw.circle(surf,RD,(hx+i*20,hy+30),7)
        pygame.draw.circle(surf,(255,120,120),(hx+i*20-2,hy+28),3)
    surf.blit(tx(f"Score: {score}","M",WH),(165,14))
    li=tx(f"Level  {level}  /  3","M",GR); bc(surf,li,14)
    pulse=int(math.sin(fr*.12)*2)
    pygame.draw.circle(surf,CC,(W-165,26+pulse),9)
    surf.blit(tx(f"{cgot}/{ctot}","M",CC),(W-148,14))
    surf.blit(tx(f"Best: {hs}","X",DG),(W-82,38))
    prog=max(0,min(1,player.x/max(1,ww)))
    pygame.draw.rect(surf,DG,(0,H-9,W,9))
    pygame.draw.rect(surf,PT,(0,H-9,int(W*prog),9))
    pygame.draw.circle(surf,PC,(max(5,int(W*prog)),H-4),5)
    surf.blit(tx("Progress","X",GR),(4,H-22))
    h=tx("ESC=Pause  R=Restart  M=Menu","X",DG)
    surf.blit(h,(W//2-h.get_width()//2,H-22))
def overlay(surf, alpha=160):
    o=pygame.Surface((W,H),pygame.SRCALPHA); o.fill((0,0,0,alpha)); surf.blit(o,(0,0))

# ═══════════════════════════════════════════════════════════════ LEVEL DATA
def get_level(n):
    if n == 1:
        G=520; WW=3100
        plats=[(0,G,900,22),(1000,G,850,22),(1960,G,700,22),(2770,G,330,22),
               (120,415,150,14),(310,355,130,14),(500,295,150,14),(710,385,120,14),(890,305,140,14),
               (1070,370,110,14),(1240,290,130,14),(1420,360,120,14),(1600,280,110,14),
               (1750,350,120,14),(1940,415,110,14),(2090,335,130,14),(2280,260,120,14),
               (2450,330,110,14),(2620,210,130,14),(2780,300,100,14),(2910,390,120,14),
               (2975,G-38,150,22),(200,285,100,14),(455,220,110,14),(685,190,100,14),(965,190,110,14),
               (1205,160,100,14),(1505,170,110,14),(1815,150,100,14),(2015,120,110,14),
               (2305,90,120,14),(2715,120,110,14)]
        mov = []
        ens = [(125,G-28,0,870,1.5),(390,327,310,435,1.3),(715,357,705,1015,1.7),
               (910,277,890,1035,1.4),(1250,260,1240,1375,1.5),(1610,250,1600,1715,1.6),
               (1950,387,1940,2005,1.8),(2100,307,2090,2215,1.5),(2640,180,2620,2755,1.3),
               (2290,G-28,1960,2760,2.0)]
        coins=[(155,385),(345,325),(535,265),(745,355),(920,275),(1100,340),(1270,260),
               (1450,330),(1630,250),(1780,320),(1970,385),(2120,305),(2310,230),
               (2480,300),(2650,180),(2810,270),(2940,360),(3005,G-58),
               (235,255),(485,190),(715,160),(995,160),(1235,130),(1535,140),
               (1845,120),(2045,90),(2335,60),(2745,90)]
        gems = [(965,160),(2015,90),(3005,G-58)]
        return WW,plats,mov,ens,coins,gems,(80,G-40),2980
    elif n == 2:
        G=520; WW=3750
        plats=[(0,G,600,22),(700,G,500,22),(1300,G,400,22),(1800,G,500,22),(2400,G,450,22),(2950,G,800,22),
               (100,415,140,14),(300,360,120,14),(500,300,130,14),(680,390,110,14),(850,310,140,14),
               (1040,385,110,14),(1210,300,130,14),(1395,385,110,14),(1570,250,140,14),
               (1780,345,120,14),(1960,265,130,14),(2130,200,110,14),(2310,285,120,14),
               (2510,205,130,14),(2710,275,110,14),(2880,195,130,14),(3010,285,120,14),(3160,205,130,14),
               (3600,G-38,165,22),(200,275,100,14),(450,210,110,14),(700,180,100,14),(955,175,110,14),
               (1255,145,100,14),(1560,115,110,14),(1890,145,100,14),(2210,100,110,14),
               (2610,115,100,14),(3020,95,120,14)]
        mov=[{"x0":620.,"y0":435.,"cx":620.,"cy":435.,"w":110,"h":14,"axis":"h","dist":75.,"spd":1.6,"t":0.,"vel":0.},
             {"x0":1255.,"y0":445.,"cx":1255.,"cy":445.,"w":110,"h":14,"axis":"h","dist":70.,"spd":1.9,"t":20.,"vel":0.},
             {"x0":2360.,"y0":435.,"cx":2360.,"cy":435.,"w":110,"h":14,"axis":"v","dist":70.,"spd":1.6,"t":0.,"vel":0.},
             {"x0":2910.,"y0":355.,"cx":2910.,"cy":355.,"w":110,"h":14,"axis":"v","dist":80.,"spd":1.9,"t":30.,"vel":0.}]
        ens=[(110,G-28,0,590,1.9),(310,332,300,420,1.7),(690,362,680,1050,2.1),
             (870,282,850,990,1.9),(1060,355,1040,1320,1.8),(1230,270,1210,1410,2.0),
             (1600,220,1570,1720,1.8),(1810,315,1780,1970,2.1),(1980,235,1960,2100,1.9),
             (2150,170,2130,2270,1.7),(2330,255,2310,2470,2.2),(2530,175,2510,2680,2.1),
             (2730,245,2710,2870,2.0),(2900,165,2880,3050,1.9),
             (1800,G-28,1800,2390,2.5),(2400,G-28,2400,2940,2.5)]
        coins=[(130,385),(330,330),(530,270),(710,360),(880,280),(1070,355),(1240,270),
               (1425,355),(1600,220),(1810,315),(1990,235),(2160,170),(2340,255),(2540,175),
               (2740,245),(2910,165),(3040,255),(3190,175),(3620,G-58),
               (230,245),(480,180),(730,150),(985,145),(1285,115),(1590,85),(1920,115),(2240,70),(2640,85),(3050,65)]
        gems=[(700,150),(1560,85),(3020,65),(3620,G-58)]
        return WW,plats,mov,ens,coins,gems,(80,G-40),3700
    else:
        G=520; WW=4200
        plats=[(0,G,400,22),(500,G,400,22),(1010,G,350,22),(1460,G,400,22),(2010,G,350,22),
               (2470,G,380,22),(2960,G,400,22),(3470,G,500,22),(4070,G-40,160,30),
               (80,420,130,14),(260,360,110,14),(440,300,130,14),(600,390,110,14),(760,310,130,14),
               (950,385,110,14),(1100,295,130,14),(1300,375,110,14),(1460,295,130,14),
               (1645,230,110,14),(1820,315,130,14),(2030,245,110,14),(2210,175,130,14),
               (2420,255,110,14),(2635,185,130,14),(2840,265,110,14),(3050,185,130,14),
               (3260,255,110,14),(3480,175,130,14),(3690,245,110,14),(3900,160,130,14),
               (150,280,90,14),(380,220,100,14),(600,180,90,14),(840,170,100,14),(1110,150,90,14),
               (1410,120,100,14),(1720,110,90,14),(2020,90,100,14),(2320,70,90,14),
               (2670,80,100,14),(3020,60,90,14),(3370,80,100,14),(3740,100,90,14)]
        mov=[{"x0":400.,"y0":445.,"cx":400.,"cy":445.,"w":90,"h":14,"axis":"h","dist":95.,"spd":2.3,"t":0.,"vel":0.},
             {"x0":970.,"y0":440.,"cx":970.,"cy":440.,"w":90,"h":14,"axis":"h","dist":85.,"spd":2.6,"t":15.,"vel":0.},
             {"x0":1930.,"y0":450.,"cx":1930.,"cy":450.,"w":90,"h":14,"axis":"v","dist":80.,"spd":2.3,"t":0.,"vel":0.},
             {"x0":2930.,"y0":445.,"cx":2930.,"cy":445.,"w":90,"h":14,"axis":"v","dist":90.,"spd":2.6,"t":10.,"vel":0.},
             {"x0":3440.,"y0":385.,"cx":3440.,"cy":385.,"w":90,"h":14,"axis":"h","dist":85.,"spd":2.9,"t":20.,"vel":0.},
             {"x0":3800.,"y0":360.,"cx":3800.,"cy":360.,"w":90,"h":14,"axis":"v","dist":70.,"spd":2.6,"t":5.,"vel":0.}]
        ens=[(90,G-28,0,390,2.3),(270,332,260,370,2.1),(450,272,440,570,2.4),(620,362,600,870,2.6),
             (770,282,760,870,2.3),(960,355,950,1250,2.1),(1120,265,1100,1300,2.5),(1320,345,1300,1440,2.3),
             (1480,265,1460,1630,2.6),(1665,200,1645,1790,2.4),(1840,285,1820,2010,2.1),(2050,215,2030,2190,2.5),
             (2230,145,2210,2400,2.3),(2440,225,2420,2615,2.6),(2655,155,2635,2820,2.4),(2860,235,2840,3030,2.1),
             (3070,155,3050,3240,2.5),(3280,225,3260,3460,2.3),(3500,145,3480,3670,2.6),(3710,215,3690,3880,2.4),
             (500,G-28,500,1000,2.9),(1460,G-28,1460,2000,2.9),(2470,G-28,2470,2950,2.9),(3470,G-28,3470,3970,2.9)]
        coins=[(110,390),(290,330),(470,270),(630,360),(790,280),(980,355),(1130,265),(1330,345),(1490,265),
               (1675,200),(1850,285),(2060,215),(2240,145),(2450,225),(2665,155),(2870,235),(3080,155),
               (3290,225),(3510,145),(3720,215),(4090,G-80),
               (180,250),(410,190),(630,150),(870,140),(1140,120),(1440,90),(1750,80),(2050,60),(2350,40),
               (2700,50),(3050,30),(3400,50),(3770,70)]
        gems=[(840,140),(2020,60),(3020,30),(4090,G-80)]
        return WW,plats,mov,ens,coins,gems,(80,G-40),4130

# ═══════════════════════════════════════════════════════════════ MAIN
def main():
    state = "MENU"
    sel   = 0
    level = 1
    hs    = load_hs()
    score = 0
    fr    = 0
    shake = [0]

    WW=3100; plats=[]; mov=[]; enemies=[]; coins=[]; gems=[]; start=(80,480); finish_x=3000
    player = Player(*start)
    cam_x  = 0.

    def load_lvl(n):
        nonlocal WW,plats,mov,enemies,coins,gems,start,finish_x,player,cam_x
        _ps.clear()
        WW,plats,mov,ens,co,gm,start,finish_x = get_level(n)
        enemies = [Enemy(e[0],e[1],e[2],e[3],e[4]) for e in ens]
        coins   = [[cx,cy,False] for cx,cy in co]
        gems    = [[gx,gy,False] for gx,gy in gm]
        player  = Player(*start)
        cam_x   = 0.

    while True:
        clock.tick(FPS)
        fr += 1
        keys = pygame.key.get_pressed()

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:

                if state == "MENU":
                    if ev.key in (pygame.K_UP,   pygame.K_w): sel=(sel-1)%3; sfx("sel")
                    if ev.key in (pygame.K_DOWN,  pygame.K_s): sel=(sel+1)%3; sfx("sel")
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if sel == 0:
                            level=1; score=0; load_lvl(1); state="PLAY"; sfx("done")
                        elif sel == 1:
                            state="HOWTO"; sfx("sel")
                        elif sel == 2:
                            pygame.quit(); sys.exit()

                elif state == "HOWTO":
                    if ev.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE, pygame.K_m):
                        state="MENU"

                elif state == "PAUSE":
                    if ev.key == pygame.K_ESCAPE: state="PLAY"
                    if ev.key == pygame.K_r:
                        score=0; load_lvl(level); state="PLAY"
                    if ev.key == pygame.K_m:
                        state="MENU"

                elif state == "PLAY":
                    if ev.key == pygame.K_ESCAPE: state="PAUSE"
                    if ev.key == pygame.K_r:
                        score=0; load_lvl(level)
                    if ev.key == pygame.K_m:
                        state="MENU"

                elif state == "CLEAR":
                    if ev.key in (pygame.K_RETURN,pygame.K_SPACE,pygame.K_n):
                        if level < 3:
                            level+=1; load_lvl(level); state="PLAY"
                        else:
                            state="WIN"

                elif state in ("OVER","WIN"):
                    if ev.key == pygame.K_r:
                        level=1; score=0; load_lvl(1); state="PLAY"
                    if ev.key == pygame.K_m:
                        state="MENU"

        # ── UPDATE ──────────────────────────────────────────
        if state == "PLAY":
            upd_mov(mov)
            player.update(keys, plats, mov)
            shake[0] = max(0, shake[0]-1)
            sx_off = random.randint(-shake[0],shake[0]) if shake[0]>0 else 0
            sy_off = random.randint(-shake[0],shake[0]) if shake[0]>0 else 0
            target_cx = player.x - W//3
            cam_x += (target_cx - cam_x) * .12
            cam_x = max(0, min(cam_x, WW-W))
            cx = cam_x + sx_off; cy = float(sy_off)
            if player.y > H+120:
                player.lives -= 1; sfx("hurt"); emit(player.x+15,H+20,RD,12,6)
                if player.lives <= 0:
                    sfx("die"); save_hs(max(hs,score)); hs=max(hs,score); state="OVER"
                else:
                    player.hp=MAX_HP; player.respawn(*start); cam_x=max(0.,player.x-W//3)
            for e in enemies:
                e.update()
                if e.alive and player.rect().colliderect(e.rect()):
                    if player.vy>0 and player.y+player.PH < e.y+e.EH//2+12:
                        e.alive=False; player.vy=JUMP_V*.65; score+=20; sfx("stomp")
                        emit_up(e.x+14, e.y, EC, 10, 5)
                    elif player.hurt(shake):
                        if player.hp <= 0:
                            player.lives -= 1
                            if player.lives <= 0:
                                sfx("die"); save_hs(max(hs,score)); hs=max(hs,score); state="OVER"
                            else:
                                player.hp=MAX_HP; player.respawn(*start); cam_x=max(0.,player.x-W//3)
            for c in coins:
                if not c[2] and math.hypot(player.x+15-c[0], player.y+19-c[1]) < 22:
                    c[2]=True; score+=10; sfx("coin"); emit_up(c[0],c[1],CC,6,3.5)
            for g in gems:
                if not g[2] and math.hypot(player.x+15-g[0], player.y+19-g[1]) < 22:
                    g[2]=True; score+=50; sfx("gem"); emit(g[0],g[1],GC,12,5)
            if player.x + player.PW >= finish_x:
                sfx("done"); save_hs(max(hs,score)); hs=max(hs,score); state="CLEAR"
            upd_ps()
        else:
            cx=cam_x; cy=0.

        # ── DRAW ────────────────────────────────────────────
        screen.fill(SKY0)

        if state == "MENU":
            draw_bg(screen, fr*.5, fr)
            overlay(screen, 85)
            shadow=tx("Platform Adventure","T",(40,40,90)); bc(screen,shadow,97)
            bc(screen, tx("Platform Adventure","T",WH), 92)
            bc(screen, tx("v 1.1","S",GR), 170)
            items=[("  Start Game  ",GD),("  How to Play  ",WH),("  Quit  ",(180,80,80))]
            for i,(it,ic) in enumerate(items):
                is_sel = i==sel
                sw,sh=300,44; bx=W//2-sw//2; by=238+i*62
                bg=(40,40,100) if is_sel else (20,20,50)
                pygame.draw.rect(screen,bg,(bx,by,sw,sh),border_radius=10)
                if is_sel:
                    pygame.draw.rect(screen,GD,(bx,by,sw,sh),2,border_radius=10)
                    pygame.draw.polygon(screen,GD,[(bx-22,by+sh//2),(bx-8,by+sh//2-9),(bx-8,by+sh//2+9)])
                s=tx(it,"M",ic); bc(screen,s,by+(sh-s.get_height())//2)
            bc(screen,tx(f"High Score: {hs}","S",CC),408)
            bc(screen,tx("Arrow Keys / WASD  ·  Space / Up = Jump","X",DG),H-28)

        elif state == "HOWTO":
            draw_bg(screen, fr*.3, fr)
            overlay(screen, 130)
            bc(screen, tx("How to Play","H",GD), 60)
            lines = [
                ("Move", "Arrow Keys or A / D"),
                ("Jump", "Up / W / Space  (hold longer = jump higher)"),
                ("Defeat enemies", "jump on top of them"),
                ("Coins & Gems", "collect for points"),
                ("Reach the flag", "to finish the level"),
                ("Pause", "ESC     Restart: R     Menu: M"),
            ]
            y = 150
            for label, desc in lines:
                l = tx(label + " :", "M", CC); bc(screen, l, y)
                d = tx(desc, "S", WH); bc(screen, d, y+36)
                y += 78
            bc(screen, tx("Press ESC / Enter to go back","X",GR), H-32)

        else:
            draw_world(screen, plats, mov, cx, cy, fr, finish_x)
            for c in coins:
                if not c[2]:
                    p=int(math.sin(fr*.1)*2); sx=int(c[0]-cx); sy=int(c[1]-cy)
                    if -20<sx<W+20:
                        pygame.draw.circle(screen,CC,(sx,sy),8+p)
                        pygame.draw.circle(screen,(255,248,200),(sx-2,sy-2),3)
            for g in gems:
                if not g[2]:
                    p=int(math.sin(fr*.12+1)*3); sx=int(g[0]-cx); sy=int(g[1]-cy)
                    if -20<sx<W+20:
                        pygame.draw.circle(screen,GC,(sx,sy),11+p)
                        pygame.draw.circle(screen,(220,150,255),(sx-3,sy-3),4)
            for e in enemies: e.draw(screen,cx,cy)
            draw_ps(screen,cx,cy)
            player.draw(screen,cx,cy)
            cgot=sum(1 for c in coins if c[2])+sum(1 for g in gems if g[2])
            ctot=len(coins)+len(gems)
            draw_hud(screen,player,score,cgot,ctot,level,hs,fr,WW)

            if state == "PAUSE":
                overlay(screen,155)
                bc(screen,tx("PAUSED","H",WH),H//2-110)
                for i,(t,c) in enumerate([("Resume  [ ESC ]",HC),("Restart  [ R ]",CC),("Menu  [ M ]",GR)]):
                    bc(screen,tx(t,"M",c),H//2-25+i*52)

            elif state == "CLEAR":
                overlay(screen,150)
                bc(screen,tx(f"Level {level} Complete!","H",GD),H//2-120)
                bc(screen,tx(f"Score: {score}","M",WH),H//2-45)
                cgot=sum(1 for c in coins if c[2])+sum(1 for g in gems if g[2])
                ctot=len(coins)+len(gems)
                bc(screen,tx(f"Collectibles: {cgot} / {ctot}","S",CC),H//2+5)
                nxt = "Next Level  [ Enter ]" if level<3 else "Enter the Final Stage!  [ Enter ]"
                bc(screen,tx(nxt,"M",GC),H//2+65)

            elif state == "OVER":
                overlay(screen,170)
                bc(screen,tx("GAME OVER","T",RD),H//2-130)
                bc(screen,tx(f"Score: {score}","H",WH),H//2-25)
                bc(screen,tx(f"High Score: {hs}","M",GD),H//2+45)
                bc(screen,tx("[ R ]  Try Again        [ M ]  Menu","S",GR),H//2+105)

            elif state == "WIN":
                overlay(screen,150)
                p=int(math.sin(fr*.08)*8)
                bc(screen,tx("YOU  WIN!","T",(min(255,200+p),min(255,200+p),0)),H//2-140)
                bc(screen,tx(f"Final Score: {score}","H",WH),H//2-35)
                bc(screen,tx(f"High Score: {hs}","M",GD),H//2+35)
                cgot=sum(1 for c in coins if c[2])+sum(1 for g in gems if g[2])
                ctot=len(coins)+len(gems)
                bc(screen,tx(f"Collectibles: {cgot} / {ctot}","S",CC),H//2+88)
                bc(screen,tx("[ R ]  Play Again        [ M ]  Menu","S",GR),H//2+132)

        pygame.display.flip()

main()