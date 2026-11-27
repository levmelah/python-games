"""
גן של בנבן 3D – Ursina Engine
W/A/S/D = הליכה   עכבר = מבט   ESC = יציאה   R = שחק שוב
"""
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math, random

app = Ursina(title='Garten of Banban 3D', borderless=False)
window.color                = color.rgb(10, 5, 20)
window.exit_button.visible  = False
window.fps_counter.enabled  = True
camera.fog_density          = 0.05
camera.fog_color            = color.rgb(10, 5, 20)

# Hebrew-capable font
HEB_FONT = '/usr/share/fonts/truetype/freefont/FreeSans.ttf'
Text.default_font = HEB_FONT

# ── Map ───────────────────────────────────────────────────────────────────────
# W=wall  R=red-wall  D=locked-door  .=floor
# K=key  N=note  E=exit  B=banban  O=opila  P=banbaleena
_MAP = [
    "WWWWWWWWWWWWWWWWWWWW",
    "W........W.........W",
    "W........W.........W",
    "W..WWWW..W......K..W",
    "W..W..W..D.........W",
    "W..W..W..W.........W",
    "W..WWWW..W....WWWWRW",
    "W........W...B.....W",
    "W........WWWWW.....W",
    "W.N......W...W.....W",
    "W........W.O.W..N..W",
    "WWWWDWWWWW...W..W..W",
    "W........W...W..W..W",
    "W........W.P..EW...W",
    "WWWWWWWWWWWWWWWWWWWW",
]
GMAP    = [list(row) for row in _MAP]
MH      = len(GMAP)
MW      = max(len(r) for r in GMAP)

opened_doors: set = set()

def get_t(c, r):
    if c < 0 or r < 0 or c >= MW or r >= MH: return 'W'
    row = GMAP[r]
    return row[c] if c < len(row) else 'W'

def is_solid(c, r):
    t = get_t(c, r)
    return t in ('W', 'R') or (t == 'D' and (c, r) not in opened_doors)

# ── Game state ────────────────────────────────────────────────────────────────
gstate  = 'play'
p_hp    = 3
p_key   = False
p_score = 0
p_notes = 0
p_inv   = 0.0      # invincibility timer (seconds)
elapsed = 0.0      # animation clock

NOTES = [
    "Log:\n\nMy child is missing from the kindergarten.\nI must find them!",
    "WARNING!\n\nThe statues wake up at night!\nRUN! RUN! RUN!",
]

# ── Level containers ──────────────────────────────────────────────────────────
door_ents    = {}
item_ents    = {}
monster_list = []
all_built    = []

# ── Build level ───────────────────────────────────────────────────────────────
def build():
    global p_hp, p_key, p_score, p_notes, p_inv, elapsed

    door_ents.clear(); item_ents.clear()
    monster_list.clear(); opened_doors.clear()
    for e in all_built:
        try: destroy(e)
        except Exception: pass
    all_built.clear()

    p_hp = 3; p_key = False; p_score = 0; p_notes = 0
    p_inv = 0.0; elapsed = 0.0

    # Floor (collideable flat box)
    f = Entity(model='cube', scale=(MW + 2, .2, MH + 2),
               position=(MW/2 - .5, -.1, MH/2 - .5),
               color=color.rgb(35, 28, 50), collider='box')
    all_built.append(f)

    # Ceiling
    ce = Entity(model='cube', scale=(MW + 2, .2, MH + 2),
                position=(MW/2 - .5, 2.7, MH/2 - .5),
                color=color.rgb(10, 6, 22))
    all_built.append(ce)

    for r in range(MH):
        for c in range(MW):
            t = get_t(c, r)
            _place(t, c, r)

    upd_hud()

def _place(t, c, r):
    """Spawn the right entity for a map tile."""
    if t == 'W':
        e = Entity(model='cube', scale=(1, 2.5, 1), position=(c, 1.25, r),
                   color=color.rgb(90, 55, 125), collider='box')
        all_built.append(e)

    elif t == 'R':
        e = Entity(model='cube', scale=(1, 2.5, 1), position=(c, 1.25, r),
                   color=color.rgb(145, 50, 50), collider='box')
        all_built.append(e)

    elif t == 'D':
        e = Entity(model='cube', scale=(1, 2.5, 1), position=(c, 1.25, r),
                   color=color.rgb(145, 78, 30), collider='box')
        door_ents[(c, r)] = e; all_built.append(e)

    elif t == 'K':
        e = Entity(model='cube', scale=.4, position=(c, 1.1, r),
                   color=color.gold)
        e.item_type = 'key'; e.mpos = (c, r)
        item_ents[(c, r)] = e; all_built.append(e)

    elif t == 'N':
        e = Entity(model='cube', scale=(.22, .3, .04),
                   position=(c, 1.1, r), color=color.rgb(255, 248, 185))
        e.item_type = 'note'; e.mpos = (c, r)
        item_ents[(c, r)] = e; all_built.append(e)

    elif t == 'E':
        e = Entity(model='cube', scale=(.6, 2.1, .6),
                   position=(c, 1.05, r), color=color.lime)
        inner = Entity(parent=e, model='cube', scale=Vec3(.5, .92, .5),
                       color=color.rgb(200, 255, 200))
        all_built.append(inner)
        e.item_type = 'exit'; e.mpos = (c, r)
        item_ents[(c, r)] = e; all_built.append(e)

    elif t in ('B', 'O', 'P'):
        kinds = {'B': 'banban', 'O': 'opila', 'P': 'banbaleena'}
        _spawn_monster(kinds[t], c, r)

def _spawn_monster(kind, c, r):
    BODY_COLORS = {
        'banban':     color.rgb(60, 130, 230),
        'opila':      color.rgb(230, 200, 50),
        'banbaleena': color.rgb(240, 100, 180),
    }
    SCALES = {
        'banban':     Vec3(.65, 1.4, .65),
        'opila':      Vec3(.85, 1.75, .85),
        'banbaleena': Vec3(.60, 1.3, .60),
    }
    mc  = BODY_COLORS[kind]
    msc = SCALES[kind]

    body = Entity(model='cube', scale=msc,
                  position=Vec3(c, msc.y / 2, r), color=mc)

    # Head
    Entity(parent=body, model='sphere',
           scale=Vec3(.9, .75, .9), position=Vec3(0, .57, 0),
           color=mc)

    # Eyes
    eye_base = color.red if kind == 'opila' else color.white
    for ex in (-.22, .22):
        eye = Entity(parent=body, model='sphere',
                     scale=Vec3(.18, .18, .18),
                     position=Vec3(ex, .57, -.40), color=eye_base)
        Entity(parent=eye, model='sphere', scale=.5,
               position=Vec3(0, 0, -.5), color=color.black)

    # Banbaleena bow
    if kind == 'banbaleena':
        Entity(parent=body, model='cube', scale=Vec3(.45, .12, .08),
               position=Vec3(0, .78, -.31), color=color.red)

    # Opila crest
    if kind == 'opila':
        for i in range(4):
            Entity(parent=body, model='sphere', scale=.1,
                   position=Vec3((-1.5+i)*.12, .78, -.32),
                   color=color.orange)

    body.kind   = kind
    body.hp     = {'banban': 1, 'opila': 2, 'banbaleena': 1}[kind]
    body.spd    = {'banban': 2.2, 'opila': 1.6, 'banbaleena': 2.8}[kind]
    body.sgt    = {'banban': 8., 'opila': 12., 'banbaleena': 7.}[kind]
    body.stun   = 0.
    body.state  = 'wander'
    body.active = True
    body.wx     = float(c)
    body.wz     = float(r)
    ang         = random.uniform(0, 6.28)
    body.wvx    = math.cos(ang) * .55
    body.wvz    = math.sin(ang) * .55
    body.wt     = 0.

    monster_list.append(body)
    all_built.append(body)

# ── Player ────────────────────────────────────────────────────────────────────
player = FirstPersonController(position=Vec3(1.5, 2, 1.5))
player.speed             = 5
player.mouse_sensitivity = Vec2(40, 40)

# ── HUD ───────────────────────────────────────────────────────────────────────
hud_hp  = Text(parent=camera.ui, text='HP: 3',
               position=(-.84, .45), origin=(-.5, 0),
               scale=2.0, color=color.red)

hud_key = Text(parent=camera.ui, text='',
               position=(-.84, .36), origin=(-.5, 0),
               scale=1.5, color=color.gold)

hud_scr = Text(parent=camera.ui, text='Score: 0',
               position=(.52, .45), origin=(-.5, 0),
               scale=1.5, color=color.white)

hud_nt  = Text(parent=camera.ui, text='Notes: 0',
               position=(-.84, .28), origin=(-.5, 0),
               scale=1.5, color=color.yellow)

hint    = Text(parent=camera.ui,
               text='W/A/S/D=הליכה  עכבר=מבט  ESC=יציאה  R=שחק שוב',
               position=(0, -.46), origin=(0, 0),
               scale=1.0, color=color.rgba(120, 120, 150, 180))

# Crosshair
Entity(parent=camera.ui, model='quad', scale=(.010, .001),
       color=color.rgba(230, 230, 230, 200))
Entity(parent=camera.ui, model='quad', scale=(.001, .010),
       color=color.rgba(230, 230, 230, 200))

# Overlay (win / lose)
ov_bg  = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                color=color.rgba(0, 0, 0, 0), z=-.5)
ov_txt = Text(parent=camera.ui, text='',
              position=(0, .05), origin=(0, 0),
              scale=2.5, color=color.white)
ov_bg.visible  = False
ov_txt.visible = False

# Note card
nc_bg  = Entity(parent=camera.ui, model='quad', scale=(.9, .52),
                color=color.rgba(255, 248, 185, 215), z=-.5)
nc_txt = Text(parent=camera.ui, text='',
              position=(0, .01), origin=(0, 0),
              scale=1.6, color=color.rgb(50, 30, 10))
nc_bg.visible  = False
nc_txt.visible = False

# Damage flash overlay
dmg_flash = Entity(parent=camera.ui, model='quad', scale=(2, 2),
                   color=color.rgba(200, 0, 0, 0), z=-.4)

def upd_hud():
    hud_hp.text  = 'HP: ' + '♥' * p_hp + '♡' * (3 - p_hp)
    hud_key.text = 'מפתח! [KEY]' if p_key else ''
    hud_scr.text = f'ניקוד: {p_score}'
    hud_nt.text  = f'הערות: {p_notes}'

def show_ov(msg, col=color.white):
    ov_bg.visible  = True
    ov_bg.color    = color.rgba(0, 0, 0, 185)
    ov_txt.visible = True
    ov_txt.text    = msg
    ov_txt.color   = col

def hide_ov():
    ov_bg.visible  = False
    ov_txt.visible = False

# ── Game loop ─────────────────────────────────────────────────────────────────
build()

_flash_timer = 0.0   # for damage red flash

def update():
    global gstate, p_hp, p_key, p_score, p_notes, p_inv, elapsed, _flash_timer

    elapsed    += time.dt
    _flash_timer = max(0., _flash_timer - time.dt * 3)
    dmg_flash.color = color.rgba(200, 0, 0, int(_flash_timer * 180))

    if gstate != 'play':
        return

    p_inv = max(0., p_inv - time.dt)
    px, pz = player.x, player.z
    pc, pr = round(px), round(pz)

    # ── Animate items ────────────────────────────────────────────────────────
    for pos, e in item_ents.items():
        if e is None: continue
        e.rotation_y += 80 * time.dt
        e.y = 1.1 + math.sin(elapsed * 2.5 + pos[0] * 1.3) * .12

    # ── Monsters ─────────────────────────────────────────────────────────────
    for m in monster_list:
        if not m.active: continue

        m.stun = max(0., m.stun - time.dt)
        if m.stun > 0:
            continue

        dx   = px - m.wx
        dz   = pz - m.wz
        dist = math.sqrt(dx * dx + dz * dz)

        # State switch
        if dist < m.sgt:
            m.state = 'chase'
        elif dist > m.sgt * 1.6:
            m.state = 'wander'

        if m.state == 'chase':
            if dist > .35:
                nd = Vec3(dx, 0, dz).normalized()
                nx = m.wx + nd.x * m.spd * time.dt
                nz = m.wz + nd.z * m.spd * time.dt
                if not is_solid(round(nx), round(m.wz)): m.wx = nx
                if not is_solid(round(m.wx), round(nz)): m.wz = nz
        else:
            m.wt += time.dt
            if m.wt > 2.5:
                m.wt  = 0.
                ang   = random.uniform(0, 6.28)
                m.wvx = math.cos(ang) * .55
                m.wvz = math.sin(ang) * .55
            nx = m.wx + m.wvx * m.spd * .4 * time.dt
            nz = m.wz + m.wvz * m.spd * .4 * time.dt
            if not is_solid(round(nx), round(m.wz)):
                m.wx = nx
            else:
                m.wvx = -m.wvx
            if not is_solid(round(m.wx), round(nz)):
                m.wz = nz
            else:
                m.wvz = -m.wvz

        # Keep grounded and face player
        m.position = Vec3(m.wx, m.scale_y / 2, m.wz)
        if dist > .15:
            m.rotation_y = math.degrees(math.atan2(dx, dz))

        # Attack
        if dist < 1.25 and p_inv <= 0:
            p_hp       -= 1
            p_inv       = 1.5
            _flash_timer = 1.0
            upd_hud()
            if p_hp <= 0:
                gstate         = 'lose'
                player.enabled = False
                show_ov(
                    'נתפסת!\n\n'
                    'הבנבן אכל אותך...\n\n'
                    '[R] שחק שוב   [ESC] יציאה',
                    color.red)

    # ── Item pickups ─────────────────────────────────────────────────────────
    for pos, e in list(item_ents.items()):
        if e is None: continue
        d2 = math.sqrt((px - e.x) ** 2 + (pz - e.z) ** 2)
        if d2 >= 1.1: continue

        it = e.item_type

        if it == 'key':
            destroy(e)
            item_ents[pos] = None
            p_key    = True
            p_score += 50
            upd_hud()

        elif it == 'note':
            destroy(e)
            item_ents[pos]  = None
            idx             = p_notes % len(NOTES)
            p_notes        += 1
            p_score        += 30
            upd_hud()
            gstate         = 'note'
            nc_bg.visible  = True
            nc_txt.visible = True
            nc_txt.text    = NOTES[idx]
            mouse.locked   = False

        elif it == 'exit':
            gstate         = 'win'
            player.enabled = False
            p_score       += 500
            upd_hud()
            show_ov(
                    f'ניצחת!\n\n'
                f'[R] שחק שוב   [ESC] יציאה',
                color.lime)

    # ── Unlock doors near player ──────────────────────────────────────────────
    if p_key:
        for dr, dc in ((0,0),(-1,0),(1,0),(0,-1),(0,1)):
            nr, nc = pr + dr, pc + dc
            if 0 <= nr < MH and 0 <= nc < MW and get_t(nc, nr) == 'D' \
                    and (nc, nr) not in opened_doors:
                opened_doors.add((nc, nr))
                de = door_ents.get((nc, nr))
                if de:
                    destroy(de)
                    door_ents[(nc, nr)] = None
                p_key    = False
                p_score += 100
                upd_hud()
                break


def input(key):
    global gstate

    if key == 'escape':
        application.quit()

    # Dismiss note card
    if gstate == 'note' and key in ('space', 'enter', 'e', 'left mouse button'):
        gstate         = 'play'
        nc_bg.visible  = False
        nc_txt.visible = False
        mouse.locked   = True

    # Restart after win / lose
    if gstate in ('win', 'lose') and key == 'r':
        player.position = Vec3(1.5, 2, 1.5)
        player.enabled  = True
        gstate          = 'play'
        hide_ov()
        build()


app.run()
