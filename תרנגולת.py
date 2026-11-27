"""
Chicken Cross 3D - התרנגולת חוצה את הכביש בתלת מימד
--------------------------------------------------
התקנה:   pip install ursina
הרצה:    python chicken_cross_3d.py

מקשים:
  חיצים / WASD  - קפיצה
  R / SPACE     - משחק חדש (אחרי שנפסלים)
  ESC           - יציאה

המטרה: להתקדם כמה שיותר רחוק ולאסוף מטבעות.
היזהרו ממכוניות, משאיות ורכבות. בנהר קופצים רק על בולי עץ ועלי שושן!
ואל תתעכבו יותר מדי, כי המצלמה ממשיכה להתקדם.
"""

import json
import math
import random
from pathlib import Path

from panda3d.core import loadPrcFileData, AntialiasAttrib, TransparencyAttrib

# החלקת קצוות (Anti-aliasing) - חייב להיות לפני יצירת החלון
loadPrcFileData("", "framebuffer-multisample 1\nmultisamples 4\nsync-video 1")

from ursina import (Ursina, Entity, Text, Vec2, Vec3, Mesh, Shader, Texture, camera,  # noqa: E402
                    color, time, window, application, destroy, lerp, scene, curve, invoke)

app = Ursina(title="Chicken Cross 3D", borderless=False, size=(1100, 760),
             development_mode=False)
SKY = (0.62, 0.84, 0.97)
window.color = color.rgba(*SKY, 1)
window.exit_button.visible = False
window.fps_counter.enabled = False
try:
    from ursina import render
    render.setAntialias(AntialiasAttrib.MMultisample)
except Exception:
    pass
scene.setTwoSided(True)

# ---------- שיידר: תאורה רכה, ברק, רוח במים ובעצים ----------
LIT = Shader(name="soft_lit", language=Shader.GLSL, vertex="""
#version 140
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform float t;
uniform float sway;
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec4 p3d_Color;
out vec3 wn;
out vec3 wp;
out vec4 vcol;
out float dist;
void main() {
    vec4 v = p3d_Vertex;
    vec4 w = p3d_ModelMatrix * v;
    if (sway > 0.5) {
        float h = max(0.0, w.y - 0.5);
        float ph = w.x * 0.7 + w.z * 1.3;
        v.x += (sin(t * 1.7 + ph) * 0.6 + sin(t * 3.1 + ph * 1.7) * 0.25) * 0.045 * h * h;
        v.z += cos(t * 1.3 + ph) * 0.02 * h * h;
        w = p3d_ModelMatrix * v;
    }
    gl_Position = p3d_ModelViewProjectionMatrix * v;
    wn = transpose(inverse(mat3(p3d_ModelMatrix))) * p3d_Normal;
    wp = w.xyz;
    vcol = p3d_Color;
    dist = length((p3d_ModelViewMatrix * v).xyz);
}
""", fragment="""
#version 140
uniform vec4 p3d_ColorScale;
uniform vec3 sun_dir;
uniform vec3 fog_col;
uniform vec2 fog_range;
uniform vec3 cam_pos;
uniform float unlit;
uniform float gloss;
uniform float water;
uniform float t;
uniform vec3 grade;
uniform float dimf;
in vec3 wn;
in vec3 wp;
in vec4 vcol;
in float dist;
out vec4 fragColor;
void main() {
    vec4 base = vcol * p3d_ColorScale;
    if (unlit > 0.5) { fragColor = base; return; }
    vec3 n = normalize(wn);
    vec3 L = normalize(sun_dir);
    vec3 V = normalize(cam_pos - wp);
    if (water > 0.5) {
        float a = sin(wp.x * 1.6 + t * 1.2) * sin(wp.z * 2.4 - t * 0.8);
        float b = sin((wp.x - wp.z) * 3.3 + t * 2.1) * 0.5;
        n = normalize(n + vec3(a * 0.18, 0.0, b * 0.18));
        float sparkle = smoothstep(0.82, 1.0, a * 0.6 + b + 0.35);
        base.rgb = mix(base.rgb, vec3(0.75, 0.95, 1.0), sparkle * 0.55);
    }
    float d = smoothstep(0.0, 0.9, max(dot(n, L), 0.0));
    vec3 amb = mix(vec3(0.42, 0.40, 0.45), vec3(0.78, 0.86, 1.0), n.y * 0.5 + 0.5);
    vec3 c = base.rgb * (amb * 0.62 + vec3(1.0, 0.95, 0.84) * d * 0.56);
    c *= mix(0.76, 1.0, clamp(wp.y * 2.2 + 0.55, 0.0, 1.0));          // הצללה ליד הקרקע
    c += vec3(0.07, 0.08, 0.1) * pow(1.0 - max(dot(n, V), 0.0), 3.0);  // אור שוליים
    float sp = gloss + water * 0.8;
    if (sp > 0.0) {
        vec3 H = normalize(L + V);
        c += vec3(1.0, 0.97, 0.9) * pow(max(dot(n, H), 0.0), 40.0) * 0.6 * sp;
    }
    float lum = dot(c, vec3(0.299, 0.587, 0.114));
    c = mix(vec3(lum), c, 1.14);                                          // רוויית צבע
    c *= grade;                                                           // גוון לפי אזור
    float f = clamp((dist - fog_range.x) / (fog_range.y - fog_range.x), 0.0, 1.0);
    c = mix(c, fog_col, f) * dimf;
    fragColor = vec4(c, base.a);
}
""")
LIT.compile()
for k, v in (("sun_dir", Vec3(-0.5, 1.0, -0.45)), ("fog_col", Vec3(*SKY)), ("fog_range", Vec2(22, 42)),
             ("unlit", 0.0), ("gloss", 0.0), ("water", 0.0), ("sway", 0.0), ("t", 0.0),
             ("cam_pos", Vec3(0, 10, -10)), ("grade", Vec3(1, 1, 1)), ("dimf", 1.0)):
    scene.set_shader_input(k, v)

# ---------- הגדרות ----------
HALF = 6                      # השחקן זז בין x=-6 ל-x=6
GROUND_W = 46
WATER_Y = -0.16
CAR_COLORS = ["#ff5e57", "#3c9bff", "#ffd32a", "#a67cff", "#2bd9a5",
              "#ff9f43", "#f1f2f6", "#3d4a5c", "#ff7eb6", "#70e000"]


def C(h):
    return color.hex(h) if isinstance(h, str) else h


# ---------- יצירת צורות חלקות ----------
_cache = {}


def _mk(vertices, tris, normals, colors=None):
    return Mesh(vertices=vertices, triangles=tris, normals=normals, colors=colors, mode="triangle")


def rbox(sx, sy, sz, r=0.1, k=3):
    """קופסה מעוגלת עם נורמלים חלקים"""
    key = ("b", round(sx, 3), round(sy, 3), round(sz, 3), round(r, 3), k)
    if key in _cache:
        return _cache[key]
    h = (sx / 2, sy / 2, sz / 2)
    r = max(0.001, min(r, min(h) - 0.001))

    def samples(hh):
        out = [-(hh - r) - r * math.cos(i / k * math.pi / 2) for i in range(k + 1)]
        return out + [(hh - r) + r * math.sin(i / k * math.pi / 2) for i in range(k + 1)]

    verts, norms, tris = [], [], []
    for axis in range(3):
        for sign in (-1, 1):
            u, v = [a for a in range(3) if a != axis]
            su, sv = samples(h[u]), samples(h[v])
            base = len(verts)
            for a in su:
                for b in sv:
                    p = [0, 0, 0]
                    p[axis] = sign * h[axis]
                    p[u], p[v] = a, b
                    inner = [max(-(h[i] - r), min(h[i] - r, p[i])) for i in range(3)]
                    d = [p[i] - inner[i] for i in range(3)]
                    ln = math.sqrt(sum(x * x for x in d)) or 1
                    n = [x / ln for x in d]
                    verts.append(tuple(inner[i] + n[i] * r for i in range(3)))
                    norms.append(tuple(n))
            nv = len(sv)
            for i in range(len(su) - 1):
                for j in range(nv - 1):
                    a0 = base + i * nv + j
                    tris += [a0, a0 + nv, a0 + nv + 1, a0, a0 + nv + 1, a0 + 1]
    m = _mk(verts, tris, norms)
    _cache[key] = m
    return m


def lathe(profile, seg=20, key=None):
    """גוף סיבובי סביב ציר y. profile = [(רדיוס, גובה), ...] מלמטה למעלה"""
    if key and key in _cache:
        return _cache[key]
    pn = []
    for i in range(len(profile)):
        nsum = [0.0, 0.0]
        for a, b in ((i - 1, i), (i, i + 1)):
            if 0 <= a and b < len(profile):
                dr = profile[b][0] - profile[a][0]
                dy = profile[b][1] - profile[a][1]
                ln = math.hypot(dr, dy) or 1
                nsum[0] += dy / ln
                nsum[1] += -dr / ln
        ln = math.hypot(*nsum) or 1
        pn.append((nsum[0] / ln, nsum[1] / ln))
    verts, norms, tris = [], [], []
    for s in range(seg + 1):
        a = s / seg * 2 * math.pi
        c, sn = math.cos(a), math.sin(a)
        for (r, y), (nr, ny) in zip(profile, pn):
            verts.append((r * c, y, r * sn))
            norms.append((nr * c, ny, nr * sn))
    n = len(profile)
    for s in range(seg):
        for i in range(n - 1):
            a = s * n + i
            b = (s + 1) * n + i
            tris += [a, b, b + 1, a, b + 1, a + 1]
    m = _mk(verts, tris, norms)
    if key:
        _cache[key] = m
    return m


def sphere(r, seg=16):
    prof = [(math.sin(i / 10 * math.pi) * r, -math.cos(i / 10 * math.pi) * r) for i in range(11)]
    return lathe(prof, seg, key=("s", round(r, 3), seg))


def cylinder(r, h, bevel=0.03, seg=18):
    b = min(bevel, r * 0.9, h / 2.01)
    prof = [(0, 0)]
    for i in range(4):
        a = i / 3 * math.pi / 2
        prof.append((r - b + b * math.sin(a), b - b * math.cos(a)))
    for i in range(4):
        a = i / 3 * math.pi / 2
        prof.append((r - b + b * math.cos(a), h - b + b * math.sin(a)))
    prof.append((0, h))
    return lathe(prof, seg, key=("c", round(r, 3), round(h, 3), round(b, 3), seg))


def cone(r, h, seg=18):
    prof = [(0, 0), (r * 0.92, 0), (r, h * 0.06), (r * 0.5, h * 0.55), (r * 0.12, h * 0.94), (0, h)]
    return lathe(prof, seg, key=("k", round(r, 3), round(h, 3)))


def soft_shadow_mesh(w, d, soft=0.28, alpha=0.3):
    key = ("sh", round(w, 2), round(d, 2), round(soft, 2), alpha)
    if key in _cache:
        return _cache[key]
    iw, idp = max(0.02, w / 2 - soft / 2), max(0.02, d / 2 - soft / 2)
    ow, od = w / 2 + soft / 2, d / 2 + soft / 2
    verts = [(-iw, 0, -idp), (iw, 0, -idp), (iw, 0, idp), (-iw, 0, idp),
             (-ow, 0, -od), (ow, 0, -od), (ow, 0, od), (-ow, 0, od)]
    cols = [color.rgba(0, 0, 0, alpha)] * 4 + [color.rgba(0, 0, 0, 0)] * 4
    tris = [0, 1, 2, 0, 2, 3]
    for i in range(4):
        j = (i + 1) % 4
        tris += [i, i + 4, j + 4, i, j + 4, j]
    m = _mk(verts, tris, [(0, 1, 0)] * 8, cols)
    _cache[key] = m
    return m


def blob_mesh(seg=24):
    """עיגול רך: מרכז אטום וקצוות שקופים (לצללים של עננים, ענני עשן וכו')"""
    key = ("blob", seg)
    if key in _cache:
        return _cache[key]
    verts, cols, tris = [(0, 0, 0)], [color.rgba(1, 1, 1, 1)], []
    for ring, (r, a) in enumerate(((0.55, 0.85), (1.0, 0.0))):
        for s in range(seg):
            ang = s / seg * 2 * math.pi
            verts.append((math.cos(ang) * r, 0, math.sin(ang) * r))
            cols.append(color.rgba(1, 1, 1, a))
    for s in range(seg):
        n = (s + 1) % seg
        tris += [0, 1 + s, 1 + n]
        tris += [1 + s, 1 + seg + s, 1 + seg + n, 1 + s, 1 + seg + n, 1 + n]
    m = _mk(verts, tris, [(0, 1, 0)] * len(verts), cols)
    _cache[key] = m
    return m


def ring_mesh(seg=32):
    """טבעת רכה - לגלי מים ולאפקט נחיתה"""
    key = ("ring", seg)
    if key in _cache:
        return _cache[key]
    verts, cols, tris = [], [], []
    rings = ((0.7, 0.0), (0.85, 1.0), (1.0, 0.0))
    for r, a in rings:
        for s in range(seg):
            ang = s / seg * 2 * math.pi
            verts.append((math.cos(ang) * r, 0, math.sin(ang) * r))
            cols.append(color.rgba(1, 1, 1, a))
    for k in range(2):
        for s in range(seg):
            n = (s + 1) % seg
            a, b = k * seg + s, k * seg + n
            tris += [a, a + seg, b + seg, a, b + seg, b]
    m = _mk(verts, tris, [(0, 1, 0)] * len(verts), cols)
    _cache[key] = m
    return m


def put(parent, mesh, pos=(0, 0, 0), col="#ffffff", hpr=None, scale=None):
    """מעתיק צורה אל ההורה (צומת פשוט, ניתן למיזוג)"""
    np = mesh.copy_to(parent)
    np.set_pos(*pos)
    if col is not None:
        np.set_color_scale(C(col))
    if hpr:
        np.set_hpr(*hpr)
    if scale is not None:
        np.set_scale(*scale) if isinstance(scale, (tuple, list)) else np.set_scale(scale)
    return np


def make_transparent(np, unlit=True):
    if unlit:
        np.set_shader_input("unlit", 1.0)
    np.set_transparency(TransparencyAttrib.M_alpha)
    np.set_depth_write(False)
    np.set_bin("fixed", 0)


def shadow(parent, x, z, w, d, height=0.5, y=0.015):
    off = 0.12 + height * 0.3
    np = put(parent, soft_shadow_mesh(w + height * 0.2, d), (x + off, y, z + off * 0.7), None)
    make_transparent(np)
    return np


# ---------- אזורים ----------
ZONE_LEN = 50
ZONES = [
    dict(key="meadow", title="SUNNY MEADOW", sky=(0.62, 0.84, 0.97), grade=(1.0, 1.0, 1.0),
         grass=("#8ee05f", "#7fd453"), side=("#64aa45", "#5c9f40"), water="#2e9cf0", deep="#1b6fb5"),
    dict(key="autumn", title="AUTUMN FOREST", sky=(0.98, 0.8, 0.62), grade=(1.05, 0.98, 0.9),
         grass=("#d6b85c", "#cbab4f"), side=("#a8843a", "#9c7a35"), water="#3c8fd6", deep="#235e94"),
    dict(key="winter", title="WINTER WONDERLAND", sky=(0.8, 0.88, 0.97), grade=(0.95, 1.0, 1.08),
         grass=("#f4f8fc", "#e8eff7"), side=("#cfdbe8", "#c5d3e2"), water="#6cc4f0", deep="#3b8fc4"),
    dict(key="desert", title="DESERT DUNES", sky=(0.99, 0.9, 0.66), grade=(1.07, 1.0, 0.88),
         grass=("#f2d48f", "#e9c97f"), side=("#d9b06a", "#cfa661"), water="#2ec4b6", deep="#1a8f86"),
]


def zone_idx(z):
    return (max(0, z) // ZONE_LEN) % len(ZONES)


# ---------- שמירה ----------
_here = globals().get("__file__")
SAVE_PATH = (Path(_here).resolve().parent if _here else Path.cwd()) / "chicken_cross_save.json"


def load_save():
    data = {"coins": 0, "best": 0, "owned": ["chicken"], "selected": "chicken"}
    try:
        data.update(json.loads(SAVE_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    if "chicken" not in data["owned"]:
        data["owned"].append("chicken")
    return data


def write_save(data):
    try:
        SAVE_PATH.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass


# ---------- דמויות ----------
CHARACTERS = [
    ("chicken", "Chicken", 0),
    ("duck", "Duck", 10),
    ("penguin", "Penguin", 15),
    ("frog", "Frog", 20),
    ("cool", "Cool Chicken", 30),
    ("ninja", "Ninja Chicken", 40),
    ("robot", "Robo Chicken", 60),
    ("golden", "Golden Chicken", 100),
]
CHAR_INFO = {c[0]: c for c in CHARACTERS}


def glow(np):
    np.set_shader_input("unlit", 1.0)
    return np


def build_bird(m, body="#ffffff", head=None, belly=None, beak="#ffa41b", beak2="#f08c00", comb="#ff3b3b",
               wing=None, feet="#ffa41b", eye="#1b1b1f", cheek="#ffb3b3", duck=False, tail=True,
               eye_patch=None, eye_glow=False):
    head = head or body
    wing = wing or C(body).tint(-0.04)
    put(m, rbox(0.62, 0.56, 0.68, 0.22), (0, 0.44, -0.02), body)                 # גוף
    put(m, rbox(0.46, 0.46, 0.44, 0.18), (0, 0.84, 0.1), head)                   # ראש
    if belly:
        put(m, rbox(0.44, 0.42, 0.1, 0.05), (0, 0.42, 0.3), belly)
    if tail:
        put(m, rbox(0.36, 0.34, 0.2, 0.1), (0, 0.5, -0.38), C(body).tint(-0.05), hpr=(0, 20, 0))
    if comb:
        for x, y, z, r in ((0, 1.1, 0.16, 0.08), (0, 1.13, 0.05, 0.09), (0, 1.1, -0.05, 0.07)):
            put(m, sphere(r), (x, y, z), comb)
        put(m, sphere(0.06), (0, 0.65, 0.33), comb)                              # זקן
    if duck:
        put(m, rbox(0.3, 0.08, 0.26, 0.04), (0, 0.79, 0.4), beak)
        put(m, rbox(0.26, 0.05, 0.22, 0.025), (0, 0.73, 0.38), beak2)
    else:
        put(m, rbox(0.2, 0.12, 0.2, 0.05), (0, 0.8, 0.38), beak)                 # מקור
        put(m, rbox(0.14, 0.06, 0.14, 0.03), (0, 0.72, 0.36), beak2)
    for sx in (-1, 1):
        if eye_patch:
            put(m, sphere(0.085, 12), (sx * 0.17, 0.87, 0.22), eye_patch)
        e = put(m, sphere(0.055), (sx * 0.2, 0.88, 0.26), eye)                  # עיניים
        if eye_glow:
            glow(e)
        put(m, sphere(0.018, 8), (sx * 0.215, 0.905, 0.31), "#ffffff")
        if cheek:
            put(m, sphere(0.05, 10), (sx * 0.22, 0.78, 0.22), cheek)
        put(m, cylinder(0.035, 0.22, 0.01, 8), (sx * 0.13, 0.0, 0.02), feet)    # רגליים
        put(m, rbox(0.14, 0.05, 0.2, 0.025), (sx * 0.13, 0.025, 0.08), feet)
    wings = []
    for sx in (-1, 1):
        w = Entity(parent=m, position=(sx * 0.31, 0.56, -0.02), shader=LIT)
        put(w, rbox(0.1, 0.32, 0.44, 0.05), (sx * 0.02, -0.12, 0), wing)
        w.side = sx
        wings.append(w)
    return wings


def build_character(m, cid):
    if cid == "duck":
        return build_bird(m, body="#ffd93d", beak="#ff9f1a", beak2="#f08c00", comb=None, duck=True,
                          wing="#f5c518", cheek="#ffb07a")
    if cid == "penguin":
        return build_bird(m, body="#2d3436", belly="#ffffff", beak="#ff9f1a", beak2="#e17a00", comb=None,
                          wing="#1e272e", cheek="#ff9fb2", tail=False, eye_patch="#ffffff")
    if cid == "frog":
        put(m, rbox(0.74, 0.44, 0.72, 0.21), (0, 0.3, 0), "#4cd137")
        put(m, rbox(0.5, 0.26, 0.1, 0.06), (0, 0.24, 0.33), "#b8f2a0")
        put(m, rbox(0.38, 0.035, 0.04, 0.015), (0, 0.36, 0.365), "#2d6a1f")     # פה
        for sx in (-1, 1):
            put(m, sphere(0.13, 16), (sx * 0.18, 0.58, 0.15), "#4cd137")
            put(m, sphere(0.1, 14), (sx * 0.18, 0.6, 0.2), "#ffffff")
            put(m, sphere(0.055, 10), (sx * 0.18, 0.61, 0.28), "#1b1b1f")
            put(m, sphere(0.018, 8), (sx * 0.17, 0.63, 0.33), "#ffffff")
            put(m, sphere(0.05, 10), (sx * 0.28, 0.36, 0.3), "#ff9fb2")
            put(m, rbox(0.14, 0.06, 0.18, 0.03), (sx * 0.2, 0.03, 0.28), "#3fb52e")   # כפות קדמיות
        legs = []
        for sx in (-1, 1):
            w = Entity(parent=m, position=(sx * 0.36, 0.16, -0.08), shader=LIT)
            put(w, rbox(0.16, 0.2, 0.4, 0.08), (0, 0, 0), "#3fb52e")
            put(w, rbox(0.2, 0.05, 0.22, 0.025), (sx * 0.03, -0.12, 0.12), "#3fb52e")
            w.side = sx
            legs.append(w)
        return legs
    if cid == "cool":
        wings = build_bird(m)
        put(m, rbox(0.5, 0.12, 0.05, 0.03), (0, 0.89, 0.32), "#111111")              # משקפי שמש
        for sx in (-1, 1):
            put(m, rbox(0.17, 0.13, 0.04, 0.04), (sx * 0.12, 0.88, 0.34), "#1e1e24")
            put(m, rbox(0.05, 0.03, 0.01, 0.01), (sx * 0.1 + 0.03, 0.91, 0.362), "#8fd3ff")
        for i in range(9):                                                          # שרשרת זהב
            a = math.pi * (0.15 + 0.7 * i / 8)
            put(m, sphere(0.03, 8), (math.cos(a) * 0.27, 0.66 - math.sin(a) * 0.08, math.sin(a) * 0.3),
                "#ffc312")
        put(m, rbox(0.12, 0.14, 0.04, 0.03), (0, 0.55, 0.35), "#ffc312")
        put(m, rbox(0.06, 0.07, 0.01, 0.01), (0, 0.55, 0.372), "#ff3b3b")
        return wings
    if cid == "ninja":
        wings = build_bird(m, body="#30336b", wing="#22254f", cheek=None, comb=None, beak="#ffa41b")
        put(m, rbox(0.5, 0.09, 0.48, 0.03), (0, 1.0, 0.1), "#e84118")               # סרט ראש
        tails = m.attach_new_node("tails")
        tails.set_pos(0, 1.0, -0.14)
        put(tails, rbox(0.06, 0.04, 0.3, 0.015), (0.05, -0.05, -0.12), "#e84118", hpr=(15, 25, 0))
        put(tails, rbox(0.06, 0.04, 0.26, 0.015), (-0.05, -0.07, -0.1), "#e84118", hpr=(-15, 35, 0))
        sw = m.attach_new_node("sword")
        sw.set_pos(0.12, 0.62, -0.36)
        sw.set_hpr(0, -50, 25)
        put(sw, rbox(0.05, 0.03, 0.7, 0.015), (0, 0, 0.12), "#dfe6e9")
        put(sw, rbox(0.06, 0.06, 0.2, 0.02), (0, 0, -0.32), "#2d3436")
        put(sw, rbox(0.14, 0.03, 0.04, 0.015), (0, 0, -0.22), "#ffc312")
        return wings
    if cid == "robot":
        wings = build_bird(m, body="#b2bec3", head="#dfe6e9", comb=None, beak="#636e72", beak2="#2d3436",
                           wing="#95a5a6", feet="#636e72", eye="#00d2ff", cheek=None, eye_glow=True)
        put(m, cylinder(0.02, 0.25, 0.01, 8), (0, 1.04, 0.1), "#636e72")             # אנטנה
        glow(put(m, sphere(0.06, 10), (0, 1.3, 0.1), "#ff3b3b"))
        put(m, rbox(0.3, 0.2, 0.05, 0.03), (0, 0.45, 0.33), "#2d3436")               # פאנל חזה
        for i, cc in enumerate(("#00d2ff", "#44bd32", "#fbc531")):
            glow(put(m, sphere(0.025, 8), (-0.08 + i * 0.08, 0.46, 0.36), cc))
        for sx in (-1, 1):
            for yy in (0.3, 0.6):
                put(m, sphere(0.02, 6), (sx * 0.31, yy, 0.25), "#7f8c8d")
        m.set_shader_input("gloss", 1.2)
        return wings
    if cid == "golden":
        wings = build_bird(m, body="#ffc312", head="#ffd23f", comb=None, wing="#f5b700", feet="#e1a100",
                           beak="#ff9f1a", cheek="#ffe08a")
        put(m, cylinder(0.17, 0.1, 0.02, 20), (0, 1.04, 0.1), "#ffb400")             # כתר
        for i in range(5):
            a = i / 5 * math.pi * 2
            put(m, cone(0.05, 0.12, 8), (math.cos(a) * 0.14, 1.13, 0.1 + math.sin(a) * 0.14), "#ffb400")
        put(m, sphere(0.04, 8), (0, 1.1, 0.27), "#ff3b3b")
        m.set_shader_input("gloss", 1.8)
        return wings
    return build_bird(m)


# ---------- אפקטים ----------
class Particle(Entity):
    def __init__(self, pos, col, vel, life=1.2, size=0.12, gravity=9, fade=False, grow=0.0,
                 floor=0.04, drag=1.5, glow=False, cube=False):
        super().__init__(position=pos, shader=LIT)
        put(self, rbox(1, 1, 1, 0.2) if cube else sphere(0.5, 8), col=None)
        self.spin = Vec3(random.uniform(-600, 600), random.uniform(-600, 600), random.uniform(-600, 600)) if cube else None
        if glow:
            self.set_shader_input("unlit", 1.0)
        self.base_col = C(col)
        self.setColorScale(self.base_col)
        self.scale = size
        self.size = size
        self.vel = Vec3(*vel)
        self.life = self.max_life = life
        self.gravity, self.fade, self.grow, self.floor, self.drag = gravity, fade, grow, floor, drag
        if fade:
            make_transparent(self, unlit=False)

    def update(self):
        dt = time.dt * Game.instance.ts
        self.life -= dt
        if self.life <= 0:
            destroy(self)
            return
        k = self.life / self.max_life
        self.vel.y -= self.gravity * dt
        self.vel *= max(0, 1 - self.drag * dt)
        self.position += self.vel * dt
        if self.spin is not None:
            self.rotation += self.spin * dt
        if self.y < self.floor:
            self.y = self.floor
            self.vel = Vec3(self.vel.x * 0.5, 0, self.vel.z * 0.5)
        if self.grow:
            self.scale = self.size * (1 + (1 - k) * self.grow)
        else:
            self.scale = self.size * (0.4 + 0.6 * min(1, k * 2))
        if self.fade:
            c = self.base_col
            self.setColorScale(color.rgba(c[0], c[1], c[2], c[3] * k))


class Ripple(Entity):
    """טבעת שמתרחבת ונעלמת"""
    def __init__(self, pos, col="#ffffff", size=1.2, life=0.7, alpha=0.8):
        super().__init__(position=pos, shader=LIT)
        put(self, ring_mesh(), col=None)
        make_transparent(self)
        self.c = C(col)
        self.size, self.life, self.max_life, self.alpha = size, life, life, alpha
        self.scale = 0.1

    def update(self):
        self.life -= time.dt
        if self.life <= 0:
            destroy(self)
            return
        k = 1 - self.life / self.max_life
        self.scale = 0.15 + self.size * (1 - (1 - k) ** 2)
        self.setColorScale(color.rgba(self.c[0], self.c[1], self.c[2], self.alpha * (1 - k)))


class Bullet(Entity):
    """כדור זוהר שננעל על המטרה"""
    def __init__(self, pos, target):
        super().__init__(position=pos, shader=LIT)
        put(self, sphere(0.5, 8), col="#fff3a0", scale=(0.09, 0.09, 0.42))
        put(self, sphere(0.5, 8), col="#ffb000", scale=(0.14, 0.14, 0.2), pos=(0, 0, -0.12))
        self.set_shader_input("unlit", 1.0)
        self.target = target
        self.life = 0.8
        self.dir = Vec3(0, 0, 1)

    def update(self):
        g = Game.instance
        dt = time.dt
        self.life -= dt
        tgt = self.target
        if tgt is not None and not tgt.dead:
            aim = g.target_pos(tgt)
            d = aim - self.position
            if d.length() < 0.55:
                g.blast(tgt)
                destroy(self)
                return
            self.dir = d.normalized()
            self.look_at(aim)
        if self.life <= 0:
            if tgt is not None:
                tgt.pending = max(0, tgt.pending - 1)
            destroy(self)
            return
        self.position += self.dir * 38 * dt
        if random.random() < 0.6:
            Particle(self.position, "#ffd84d", (0, 0.2, 0), life=0.15, size=0.08, gravity=0, glow=True, fade=True)


class Target:
    """עטיפה למכונית / רכבת שאפשר לירות בהן"""
    def __init__(self, row, kind, obj):
        self.row, self.kind, self.obj = row, kind, obj
        self.dead = False
        self.pending = 0


class Flyer:
    """רכב שהתפוצץ ועף באוויר"""
    def __init__(self, e, vel, spin):
        self.e, self.vel, self.spin = e, vel, spin
        self.bounces = 0
        self.smoke_t = 0
        self.done = False


# ---------- תרנגולת ----------
class Chicken(Entity):
    def __init__(self, cid="chicken"):
        super().__init__(shader=LIT)
        self.model_root = Entity(parent=self, shader=LIT)
        m = self.model_root
        self.wings = build_character(m, cid)
        # רובה (מוסתר עד שלוחצים ENTER)
        self.gun = Entity(parent=self, position=(0.34, 0.45, 0.1), shader=LIT, enabled=False)
        self.gun_body = Entity(parent=self.gun, shader=LIT)
        gb = self.gun_body
        put(gb, rbox(0.15, 0.17, 0.5, 0.06), (0, 0, 0.08), "#2d3436")             # גוף
        put(gb, rbox(0.1, 0.1, 0.42, 0.045), (0, 0.02, 0.48), "#636e72")          # קנה
        put(gb, rbox(0.13, 0.13, 0.07, 0.04), (0, 0.02, 0.7), "#ff6b00")          # קצה כתום
        put(gb, rbox(0.1, 0.22, 0.12, 0.04), (0, -0.16, -0.04), "#4b3621")        # ידית
        put(gb, rbox(0.12, 0.18, 0.16, 0.05), (0, -0.12, 0.22), "#d63031")        # מחסנית
        put(gb, rbox(0.06, 0.07, 0.22, 0.03), (0, 0.13, 0.1), "#1e272e")          # כוונת
        put(gb, sphere(0.03, 8), (0, 0.13, 0.22), "#ff3b3b")
        self.gun_tip = Entity(parent=gb, position=(0, 0.02, 0.76))
        self.gun.set_shader_input("gloss", 1.0)
        self.shadow = Entity(shader=LIT)
        put(self.shadow, soft_shadow_mesh(0.55, 0.55, 0.35), col=None)
        make_transparent(self.shadow)
        self.ground_y = 0.0

    def update(self):
        self.shadow.x = self.x + 0.08
        self.shadow.z = self.z + 0.05
        self.shadow.y = self.ground_y + 0.02
        self.shadow.scale = max(0.45, 1 - (self.y - self.ground_y) * 0.9)

    def flatten(self):
        self.model_root.scale = (1.35, 0.14, 1.35)


# ---------- שורות ----------
class Row:
    def __init__(self, z, kind):
        self.z = z
        self.kind = kind            # grass / road / rail / river
        self.root = Entity(z=z, shader=LIT)
        self.static = Entity(parent=self.root, shader=LIT)
        self.blocked = set()
        self.cars = []
        self.logs = []
        self.pads = set()
        self.coin = None
        self.train = None
        self.train_timer = random.uniform(2, 6)
        self.signal = None
        self.dir = 1

    def finish(self):
        self.static.flattenStrong()   # מאחד את כל העצמים הסטטיים - הרבה יותר מהיר

    def destroy(self):
        destroy(self.root)


class Mover:
    """מכונית או בול עץ שזזים לאורך השורה"""
    def __init__(self, row, x, speed, direction, length):
        self.row, self.dir, self.speed, self.length = row, direction, speed, length
        self.e = Entity(parent=row.root, x=x, rotation_y=0 if direction > 0 else 180, shader=LIT)
        self.g = Entity(parent=self.e, shader=LIT)
        self.phase = random.uniform(0, 6.28)
        self.puff_t = random.uniform(0, 0.5)

    @property
    def x(self):
        return self.e.x


class Car(Mover):
    def __init__(self, row, x, speed, direction):
        truck = random.random() < 0.22
        super().__init__(row, x, speed, direction, 2.6 if truck else random.choice([1.5, 1.7]))
        self.truck = truck
        self.build()
        self.g.set_shader_input("gloss", 1.0)
        self.g.flattenStrong()

    def build(self):
        g, L = self.g, self.length
        shadow(g, 0, 0, L, 0.92, height=1.0 if self.truck else 0.6)
        col = random.choice(CAR_COLORS)
        dark = C(col).tint(-0.25)
        wheels = (-L / 2 + 0.36, L / 2 - 0.36) if not self.truck else (-L / 2 + 0.42, -L / 2 + 0.98, L / 2 - 0.4)
        for wx in wheels:
            for wz in (-1, 1):
                put(g, cylinder(0.19, 0.16, 0.05), (wx, 0.19, wz * 0.34), "#202227", hpr=(0, 90, 0))
                put(g, cylinder(0.09, 0.17, 0.02, 10), (wx, 0.19, wz * 0.34), "#c8ccd4", hpr=(0, 90, 0))
        if self.truck:
            box_col = random.choice(["#f1f2f6", "#dfe4ea", "#ffeaa7", "#fab1a0", "#81ecec"])
            put(g, rbox(L - 0.85, 1.0, 0.86, 0.16), (-0.37, 0.82, 0), box_col)              # ארגז
            put(g, rbox(L - 0.95, 0.08, 0.7, 0.03), (-0.37, 0.62, 0.44), C(box_col).tint(-0.15))
            put(g, rbox(L - 0.95, 0.08, 0.7, 0.03), (-0.37, 0.62, -0.44), C(box_col).tint(-0.15))
            put(g, rbox(0.7, 0.8, 0.84, 0.24), (L / 2 - 0.36, 0.62, 0), col)              # תא נהג
            put(g, rbox(0.12, 0.34, 0.7, 0.05), (L / 2 - 0.06, 0.78, 0), "#2c3e57")        # שמשה
            put(g, rbox(0.04, 0.12, 0.5, 0.02), (L / 2 - 0.0, 0.85, 0), "#8fd3ff")
            put(g, cylinder(0.04, 0.5, 0.01, 8), (L / 2 - 0.6, 0.9, -0.4), "#8a8f99")      # אגזוז
            front = L / 2 + 0.01
        else:
            put(g, rbox(L, 0.46, 0.86, 0.21), (0, 0.42, 0), col)                         # גוף
            put(g, rbox(L - 0.1, 0.06, 0.88, 0.03), (0, 0.35, 0), dark)                  # פס צד
            put(g, rbox(L * 0.54, 0.42, 0.74, 0.19), (-0.08, 0.74, 0), "#2c3e57")        # תא זכוכית
            put(g, rbox(L * 0.46, 0.12, 0.76, 0.06), (-0.1, 0.95, 0), col)               # גג
            put(g, rbox(0.06, 0.2, 0.62, 0.03), (L * 0.18 + 0.02, 0.77, 0), "#8fd3ff")   # ברק בשמשה
            if random.random() < 0.15:   # מונית / משטרה
                put(g, rbox(0.3, 0.12, 0.3, 0.05), (-0.1, 1.06, 0), random.choice(["#ffd32a", "#ff3b3b"]))
            front = L / 2
        for z in (-0.27, 0.27):
            put(g, sphere(0.07, 10), (front - 0.03, 0.47, z), "#fffbe0")                  # פנסים
            put(g, sphere(0.06, 10), (-L / 2 + 0.03, 0.47, z), "#ff3030")
        put(g, rbox(0.08, 0.1, 0.8, 0.04), (front - 0.02, 0.3, 0), "#9aa0aa")            # פגוש
        put(g, rbox(0.08, 0.1, 0.8, 0.04), (-L / 2 + 0.02, 0.3, 0), "#9aa0aa")


class Log(Mover):
    def __init__(self, row, x, speed, direction, length, snowy=False):
        super().__init__(row, x, speed, direction, length)
        g = self.g
        if snowy:
            put(g, rbox(length - 0.3, 0.06, 0.44, 0.03), (0.05, 0.15, 0), "#ffffff")
        s = put(g, soft_shadow_mesh(length + 0.2, 0.9, 0.4, 0.25), (0.15, WATER_Y + 0.012, 0.12), None)
        make_transparent(s)
        put(g, rbox(length, 0.36, 0.66, 0.17), (0, -0.04, 0), "#8b5a2b")
        put(g, rbox(length - 0.1, 0.06, 0.5, 0.03), (0, 0.13, 0), "#9d6b38")
        for sx in (-1, 1):
            put(g, cylinder(0.25, 0.04, 0.015, 16), (sx * length / 2, -0.04, 0), "#d4a373", hpr=(0, 0, 90))
            put(g, cylinder(0.12, 0.045, 0.01, 12), (sx * length / 2, -0.04, 0), "#b07d4f", hpr=(0, 0, 90))
        for _ in range(int(length)):   # בליטות בקליפה
            put(g, rbox(0.12, 0.08, 0.5, 0.03), (random.uniform(-length / 2 + 0.3, length / 2 - 0.3), 0.12, 0),
                "#7a4b26")
        g.flattenStrong()


def smooth(t):
    return t * t * (3 - 2 * t)


def make_vignette():
    from PIL import Image
    size = 256
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            dx, dy = (x / size - 0.5) * 2, (y / size - 0.5) * 2
            d = math.sqrt(dx * dx + dy * dy)
            a = max(0.0, min(1.0, (d - 0.55) / 0.8))
            px[x, y] = (10, 20, 40, int(255 * a * a * 0.7))
    return Texture(img)


# ---------- משחק ----------
class Game(Entity):
    instance = None

    def __init__(self):
        super().__init__()
        Game.instance = self
        self.ts = 1.0
        self.save = load_save()
        self.best = self.save["best"]
        self.coins = self.save["coins"]
        self.shop_open = False
        self.shop_ui = []
        self.sky = Vec3(*SKY)
        self.grade = Vec3(1, 1, 1)
        self.zone_now = 0
        self.zone_token = 0
        self.weather_t = 0
        tl, tr = window.top_left, window.top_right
        vig = Entity(parent=camera.ui, model="quad", texture=make_vignette(), scale=(window.aspect_ratio, 1), z=5)
        vig.setTransparency(TransparencyAttrib.M_alpha)
        self.flash = Entity(parent=camera.ui, model="quad", scale=(window.aspect_ratio, 1), z=4,
                            color=color.rgba(1, 1, 1, 0))
        self.score_text = Text("0", position=tl + Vec2(0.04, -0.03), scale=4, color=color.white)
        self.best_text = Text("", position=tl + Vec2(0.045, -0.15), scale=1.6, color=C("#ffeaa7"))
        self.coin_icon = Entity(parent=camera.ui, model="circle", scale=0.045, color=C("#ffc312"),
                                position=tr + Vec2(-0.17, -0.06))
        Entity(parent=self.coin_icon, model="circle", scale=0.68, color=C("#ffe066"), z=-0.01)
        self.coin_text = Text(str(self.coins), position=tr + Vec2(-0.135, -0.04), scale=2.4, color=C("#ffe066"))
        self.zone_text = Text("", origin=(0, 0), y=0.27, scale=3, color=color.white, enabled=False)
        self.panel = Entity(parent=camera.ui, model="quad", scale=(0.95, 0.42), y=0.03, z=1,
                            color=color.rgba(0.05, 0.07, 0.15, 0.6), enabled=False)
        self.center_text = Text("", origin=(0, 0), y=0.1, scale=3.2, color=color.white)
        self.sub_text = Text("", origin=(0, 0), y=-0.02, scale=1.6, color=C("#ffeaa7"))
        self.hint = Text("Arrows / WASD = hop     ENTER = gun     C = character shop", origin=(0, 0), y=-0.4,
                         scale=1.5, color=color.white)
        self.gun_text = Text("GUN MODE  (ENTER to stop)", origin=(0, 0), y=0.44, scale=1.8,
                             color=C("#ff6b3b"), enabled=False)
        self.gun_on = False
        self.fire_t = 0
        self.bullets = []
        self.flyers = []
        self.targets = {}
        self.rows = {}
        self.chicken = None
        self.shake_t = 0
        self.shake_amp = 0.15
        self.make_ambient()
        self.reset()

    def make_ambient(self):
        # צללי עננים שעוברים על הקרקע
        self.clouds = []
        for i in range(5):
            c = Entity(shader=LIT, y=0.03)
            put(c, blob_mesh(), col=None)
            make_transparent(c)
            c.setColorScale(color.rgba(0.05, 0.1, 0.2, 0.13))
            c.scale = (random.uniform(3, 5), 1, random.uniform(2, 3.2))
            c.x = random.uniform(-20, 20)
            c.offz = random.uniform(-4, 20)
            c.speed = random.uniform(0.5, 0.9)
            self.clouds.append(c)
        # פרפרים
        self.butterflies = []
        for i in range(4):
            b = Entity(shader=LIT)
            col = random.choice(["#ff9ff3", "#feca57", "#54a0ff", "#ffffff", "#ff6b6b"])
            put(b, rbox(0.03, 0.03, 0.12, 0.012), (0, 0, 0), "#2d3436")
            b.wings = []
            for sx in (-1, 1):
                w = Entity(parent=b, shader=LIT)
                put(w, rbox(0.16, 0.01, 0.14, 0.006), (sx * 0.08, 0, 0.01), col)
                w.side = sx
                b.wings.append(w)
            b.home = Vec3(random.uniform(-6, 6), 0.9, random.uniform(0, 12))
            b.phase = random.uniform(0, 10)
            self.butterflies.append(b)

    # --- בנייה ---
    def reset(self):
        for r in self.rows.values():
            r.destroy()
        self.rows = {}
        if self.chicken:
            destroy(self.chicken.shadow)
            destroy(self.chicken)
        for f in getattr(self, "flyers", []):
            destroy(f.e)
        self.flyers = []
        self.targets = {}
        self.gun_on = False
        self.gun_text.enabled = False
        self.chicken = Chicken(self.save.get("selected", "chicken"))
        self.zone_now = 0
        self.zone_text.enabled = False
        scene.set_shader_input("dimf", 1.0)
        self.gx, self.gz = 0, 0
        self.hop_t = 1.0
        self.hop_from = Vec3(0, 0, 0)
        self.hop_to = Vec3(0, 0, 0)
        self.queued = None
        self.ride = None
        self.ride_off = 0
        self.carrier = None
        self.max_z = 0
        self.alive = True
        self.started = False
        self.dead_time = 0
        self.ts = 1.0
        self.cam_z = -1.0
        self.next_z = -8
        self.pending = []
        while self.next_z < 26:
            self.add_row()
        self.score_text.text = "0"
        self.best_text.text = f"BEST {self.best}" if self.best else ""
        self.center_text.text = ""
        self.sub_text.text = ""
        self.panel.enabled = False
        self.hint.enabled = True
        self.update_camera(instant=True)

    def plan_rows(self):
        z = self.next_z
        if z < 3:
            return ["safe"]
        d = min(1.0, z / 150)
        roll = random.random()
        if roll < 0.12 + 0.06 * d and z > 12:
            return ["rail"] + ["grass"] * random.randint(1, 2)
        if roll < 0.32 and z > 7:
            n = random.randint(1, 2 + int(d * 2))
            return ["river"] * n + ["grass"] * random.randint(1, 2)
        n = random.randint(1, 3 + int(d * 2))
        return ["road"] * n + ["grass"] * random.randint(1, 2)

    def add_row(self):
        if not self.pending:
            self.pending = self.plan_rows()
        kind = self.pending.pop(0)
        z = self.next_z
        self.next_z += 1
        prev = self.rows.get(z - 1)
        row = Row(z, "grass" if kind == "safe" else kind)
        self.rows[z] = row
        s = row.static
        side_w = GROUND_W / 2 - HALF - 0.5
        side_x = HALF + 0.5 + side_w / 2

        zi = zone_idx(z)
        Z = ZONES[zi]
        row.zone = zi
        if row.kind == "grass":
            s.set_shader_input("sway", 1.0)
            light = z % 2 == 0
            put(s, rbox(2 * HALF + 1, 0.4, 1.0, 0.06), (0, -0.2, 0), Z["grass"][0 if light else 1])
            for sx in (-1, 1):
                put(s, rbox(side_w, 0.5, 1.0, 0.06), (sx * side_x, -0.2, 0), Z["side"][0 if light else 1])
            for x in range(-HALF - 8, HALF + 9):
                if abs(x) > HALF and random.random() < 0.55:
                    self.make_tree(s, x, 0.05, zi)
            if kind != "safe" and z > 0:
                cols = random.sample(range(-HALF, HALF + 1), random.randint(0, 4))
                for x in cols:
                    if random.random() < 0.75:
                        self.make_tree(s, x, 0.0, zi)
                    else:
                        self.make_rock(s, x, zi)
                    row.blocked.add(x)
                if random.random() < 0.3:
                    free = [x for x in range(-HALF, HALF + 1) if x not in row.blocked]
                    if free:
                        self.make_coin(row, random.choice(free))
            elif z < 0:
                for x in range(-HALF, HALF + 1):
                    if random.random() < 0.45 or z < -2:
                        self.make_tree(s, x, 0.0, zi)
                        row.blocked.add(x)
            for _ in range(random.randint(2, 6)):        # קישוטים קטנים על הקרקע
                fx = random.randint(-HALF, HALF)
                if fx not in row.blocked:
                    self.make_flora(s, fx + random.uniform(-0.35, 0.35), random.uniform(-0.35, 0.35), zi)

        elif row.kind == "road":
            put(s, rbox(GROUND_W, 0.4, 1.0, 0.02), (0, -0.2, 0), "#4b4f5c")
            put(s, rbox(2 * HALF + 1, 0.4, 1.0, 0.02), (0, -0.199, 0), "#555a68")
            for _ in range(3):   # כתמי אספלט
                put(s, rbox(random.uniform(0.3, 1.2), 0.02, random.uniform(0.15, 0.4), 0.01),
                    (random.uniform(-HALF, HALF), 0.0, random.uniform(-0.3, 0.3)), "#515665")
            if prev and prev.kind == "road":
                for x in range(-HALF - 12, HALF + 13, 2):
                    put(s, rbox(0.9, 0.04, 0.08, 0.02), (x, 0.0, -0.5), "#f5f6fa")
            else:
                put(s, rbox(GROUND_W, 0.14, 0.14, 0.05), (0, 0.0, -0.48), "#d2d5dc")
            d = min(1.0, z / 160)
            row.dir = random.choice([-1, 1])
            speed = random.uniform(2.2, 3.8) + d * 4
            count = random.randint(2, 3)
            spacing = 26 / count
            start = random.uniform(-13, 0)
            for i in range(count):
                row.cars.append(Car(row, start + i * spacing + random.uniform(0, spacing * 0.3), speed, row.dir))

        elif row.kind == "rail":
            put(s, rbox(GROUND_W, 0.36, 1.0, 0.05), (0, -0.16, 0), "#9c8a75")
            for _ in range(30):   # חצץ
                put(s, sphere(0.04, 6), (random.uniform(-HALF - 3, HALF + 3), 0.02, random.uniform(-0.45, 0.45)),
                    random.choice(["#8a7a68", "#b0a08c", "#7d6e5d"]))
            for x in range(-22, 23):
                put(s, rbox(0.26, 0.08, 0.92, 0.03), (x, 0.04, 0), "#7a5640")
            for zz in (-0.25, 0.25):
                put(s, rbox(GROUND_W, 0.08, 0.08, 0.03), (0, 0.12, zz), "#c3cad3")
            pole = Entity(parent=row.root, x=HALF + 0.6, z=-0.55, shader=LIT)
            put(pole, cylinder(0.05, 1.25, 0.02, 10), (0, 0, 0), "#6c757d")
            put(pole, rbox(0.42, 0.26, 0.16, 0.08), (0, 1.25, 0), "#2d3436")
            put(pole, rbox(0.5, 0.08, 0.04, 0.02), (0, 0.95, 0), "#ffffff", hpr=(0, 0, 35))
            put(pole, rbox(0.5, 0.08, 0.04, 0.02), (0, 0.95, 0), "#ffffff", hpr=(0, 0, -35))
            row.signal = Entity(parent=pole, position=(0, 1.25, -0.08), shader=LIT)
            put(row.signal, sphere(0.08, 10), col=None)
            row.signal.setColorScale(C("#5a0000"))
            row.signal.set_shader_input("unlit", 1.0)
            row.dir = random.choice([-1, 1])

        elif row.kind == "river":
            water = put(s, rbox(GROUND_W, 0.3, 1.02, 0.02), (0, WATER_Y - 0.15, 0), Z["water"])
            water.set_shader_input("water", 1.0)
            put(s, rbox(GROUND_W, 0.3, 1.0, 0.02), (0, -0.5, 0), Z["deep"])
            if not (prev and prev.kind == "river"):   # גדה עם קצף
                put(s, rbox(GROUND_W, 0.05, 0.12, 0.025), (0, WATER_Y + 0.01, -0.44), "#e8f7ff")
            if random.random() < 0.3 and not (prev and prev.kind == "river" and not prev.logs):
                # שורת עלי שושן
                cols = random.sample(range(-HALF, HALF + 1), random.randint(4, 7))
                for x in cols:
                    row.pads.add(x)
                    if Z["key"] == "winter":      # גושי קרח
                        put(s, rbox(0.78, 0.12, 0.74, 0.05), (x, WATER_Y + 0.02, 0), "#e3f4ff")
                        put(s, rbox(0.5, 0.04, 0.4, 0.02), (x - 0.08, WATER_Y + 0.08, 0.05), "#ffffff")
                        continue
                    put(s, cylinder(0.38, 0.04, 0.015, 20), (x, WATER_Y + 0.0, 0), "#3cb371")
                    put(s, cylinder(0.3, 0.045, 0.01, 16), (x + 0.03, WATER_Y + 0.003, 0.02), "#4ccf82")
                    if random.random() < 0.3:
                        put(s, sphere(0.08, 10), (x + 0.15, WATER_Y + 0.08, -0.1), "#ff9ff3")
            else:
                row.dir = -prev.dir if (prev and prev.kind == "river" and prev.logs) else random.choice([-1, 1])
                speed = random.uniform(1.2, 2.2) + min(1.0, z / 160) * 1.5
                x = -25
                while x < 24:
                    L = random.choice([2, 3, 3, 4])
                    row.logs.append(Log(row, x + L / 2, speed, row.dir, L, snowy=Z["key"] == "winter"))
                    x += L + random.uniform(1.3, 2.6)

        if prev and prev.kind == "road" and row.kind != "road":
            put(s, rbox(GROUND_W, 0.14, 0.14, 0.05), (0, 0.0, -0.52), "#d2d5dc")
        if prev and prev.kind == "river" and row.kind != "river":
            put(s, rbox(GROUND_W, 0.05, 0.12, 0.025), (0, WATER_Y + 0.01, -0.56), "#e8f7ff")
        row.finish()

    def make_coin(self, row, x):
        c = Entity(parent=row.root, x=x, y=0.45, shader=LIT)
        put(c, cylinder(0.24, 0.08, 0.03, 24), (0, 0, -0.04), "#ffb400", hpr=(0, 90, 0))
        put(c, cylinder(0.17, 0.1, 0.02, 20), (0, 0, -0.05), "#ffd84d", hpr=(0, 90, 0))
        c.set_shader_input("gloss", 1.5)
        c.col = x
        sh = Entity(parent=row.root, x=x + 0.1, y=0.02, z=0.07, shader=LIT)
        put(sh, soft_shadow_mesh(0.35, 0.3, 0.3), col=None)
        make_transparent(sh)
        c.sh = sh
        row.coin = c

    def round_tree(self, s, x, y, colors, fruit="#ff4757", fruit_p=0.25):
        big = random.uniform(0.36, 0.46)
        trunk = random.uniform(0.45, 0.7)
        shadow(s, x, 0, 0.9, 0.85, height=trunk + big * 2)
        put(s, cylinder(0.12, trunk + 0.2, 0.04, 12), (x, y, 0), "#8b5a2b")
        g = C(random.choice(colors))
        cy = y + trunk + big * 0.8
        put(s, sphere(big, 20), (x, cy, 0), g)
        for dx, dy, dz, k in ((-0.22, -0.1, 0.08, 0.62), (0.22, -0.06, -0.05, 0.6),
                              (0.02, 0.24, 0.02, 0.6), (0.05, -0.05, -0.22, 0.55)):
            put(s, sphere(big * k, 16), (x + dx, cy + dy, dz), g.tint(0.06 if dy > 0 else -0.03))
        if fruit and random.random() < fruit_p:
            for _ in range(3):
                a = random.uniform(-2.6, -0.5)
                put(s, sphere(0.05, 8), (x + math.cos(a) * big * 0.95, cy + random.uniform(-0.15, 0.15),
                                         math.sin(a) * big * 0.95), fruit)
        return cy, big

    def pine(self, s, x, y, col="#1f9e5a", snow=False):
        h = random.choice([2, 3])
        shadow(s, x, 0, 0.75, 0.75, height=1.2)
        put(s, cylinder(0.1, 0.4, 0.03, 10), (x, y, 0), "#7a4b26")
        for i in range(h):
            r = 0.46 - i * 0.1
            put(s, cone(r, 0.62, 16), (x, y + 0.32 + i * 0.36, 0), C(col).tint(i * 0.07))
            if snow:
                put(s, cone(r * 0.62, 0.36, 14), (x, y + 0.6 + i * 0.36, 0), "#ffffff")

    def make_tree(self, s, x, y=0.0, zi=0):
        key = ZONES[zi]["key"]
        k = random.random()
        if key == "meadow":
            if k < 0.55:
                self.round_tree(s, x, y, ["#2ecc71", "#27ae60", "#3fbf5f", "#52c96b", "#6ad46f"])
            elif k < 0.85:
                self.pine(s, x, y)
            else:
                self.bush(s, x, y, "#3cb95a", "#ff4757")
        elif key == "autumn":
            if k < 0.65:
                self.round_tree(s, x, y, ["#e67e22", "#d35400", "#f39c12", "#c0392b", "#e1b12c"],
                                fruit="#8b3a1a", fruit_p=0.15)
            elif k < 0.85:
                self.pine(s, x, y, "#2f7a4f")
            else:
                self.bush(s, x, y, "#b5651d", "#ffd32a")
        elif key == "winter":
            if k < 0.6:
                self.pine(s, x, y, "#1d7a52", snow=True)
            elif k < 0.85:
                cy, big = self.round_tree(s, x, y, ["#eef5fb", "#e3eef8"], fruit=None)
                put(s, sphere(big * 0.5, 12), (x - 0.1, cy + big * 0.7, -0.05), "#ffffff")
            else:
                self.bush(s, x, y, "#f4f8fc", "#ff4757")
        else:  # desert
            if k < 0.6:
                self.cactus(s, x, y)
            elif k < 0.8:
                self.palm(s, x, y)
            else:
                self.bush(s, x, y, "#a3a35a", None)

    def bush(self, s, x, y, col, berry):
        shadow(s, x, 0, 0.8, 0.7, height=0.4)
        for dx, dz, r in ((-0.15, 0, 0.26), (0.16, 0.05, 0.24), (0, -0.08, 0.3)):
            put(s, sphere(r, 14), (x + dx, y + r * 0.85, dz), col)
        if berry:
            put(s, sphere(0.05, 8), (x + 0.1, y + 0.5, -0.2), berry)
            put(s, sphere(0.05, 8), (x - 0.18, y + 0.35, -0.2), berry)

    def cactus(self, s, x, y):
        h = random.uniform(0.8, 1.2)
        shadow(s, x, 0, 0.6, 0.5, height=h)
        g = "#3a9d4f"
        put(s, cylinder(0.17, h, 0.15, 14), (x, y, 0), g)
        for side in random.sample([-1, 1], random.randint(1, 2)):
            ay = y + random.uniform(0.35, 0.55) * h
            put(s, rbox(0.3, 0.16, 0.16, 0.075), (x + side * 0.24, ay, 0), g)
            put(s, rbox(0.16, 0.36, 0.16, 0.075), (x + side * 0.36, ay + 0.15, 0), g)
        for i in range(6):   # קוצים
            a = random.uniform(0, 6.28)
            put(s, sphere(0.015, 4), (x + math.cos(a) * 0.17, y + random.uniform(0.2, h - 0.1),
                                      math.sin(a) * 0.17), "#fff3c4")
        if random.random() < 0.5:
            put(s, sphere(0.07, 10), (x, y + h + 0.02, 0), "#ff6b9a")    # פרח

    def palm(self, s, x, y):
        h = random.uniform(1.1, 1.5)
        shadow(s, x, 0, 1.2, 1.0, height=h)
        for i in range(5):
            put(s, cylinder(0.1 - i * 0.01, h / 5 + 0.03, 0.03, 10), (x + i * 0.02, y + i * h / 5, 0),
                "#a0703c" if i % 2 else "#8b5e34")
        top = s.attach_new_node("palm_top")
        top.set_pos(x + 0.1, y + h, 0)
        for i in range(7):
            leaf = top.attach_new_node("leaf")
            leaf.set_h(i * 360 / 7 + random.uniform(-10, 10))
            put(leaf, rbox(0.8, 0.05, 0.22, 0.025), (0.38, -0.12, 0), random.choice(["#2ecc71", "#27ae60"]),
                hpr=(0, 0, -22))
        for i in range(3):
            put(top, sphere(0.07, 8), (math.cos(i * 2) * 0.08, -0.06, math.sin(i * 2) * 0.08), "#6b4423")

    def make_rock(self, s, x, zi=0):
        key = ZONES[zi]["key"]
        if key == "autumn":      # דלעת
            shadow(s, x, 0, 0.7, 0.6, height=0.4)
            put(s, sphere(0.3, 18), (x, 0.24, 0), "#ff8c1a", scale=(1.2, 0.85, 1.1))
            for dx in (-0.14, 0.14):
                put(s, sphere(0.22, 14), (x + dx, 0.22, 0), "#f77f00", scale=(0.9, 1, 1.25))
            put(s, cylinder(0.04, 0.14, 0.02, 8), (x, 0.46, 0), "#4b7f2a")
            return
        if key == "winter":      # איש שלג
            shadow(s, x, 0, 0.7, 0.6, height=0.9)
            put(s, sphere(0.3, 18), (x, 0.28, 0), "#ffffff")
            put(s, sphere(0.21, 16), (x, 0.7, 0), "#ffffff")
            put(s, cone(0.04, 0.2, 8), (x, 0.7, 0.2), "#ff7f11", hpr=(0, -90, 0))
            for sx in (-1, 1):
                put(s, sphere(0.03, 8), (x + sx * 0.07, 0.78, 0.18), "#1b1b1f")
            put(s, rbox(0.46, 0.08, 0.36, 0.04), (x, 0.54, 0), "#e84118")              # צעיף
            put(s, cylinder(0.14, 0.18, 0.02, 14), (x, 0.86, 0), "#2d3436")           # כובע
            put(s, cylinder(0.2, 0.03, 0.01, 16), (x, 0.86, 0), "#2d3436")
            return
        col1, col2 = ("#d98e5a", "#e8a873") if key == "desert" else ("#9aa5ad", "#b8c2c9")
        shadow(s, x, 0, 0.7, 0.6, height=0.3)
        put(s, rbox(0.72, 0.42, 0.62, 0.18), (x, 0.2, 0), col1)
        put(s, rbox(0.4, 0.2, 0.36, 0.09), (x + 0.12, 0.44, -0.04), col2)
        put(s, sphere(0.1, 10), (x - 0.25, 0.08, -0.25), C(col1).tint(-0.08))

    def make_flora(self, s, px, pz, zi):
        key = ZONES[zi]["key"]
        r = random.random()
        if key == "meadow":
            if r < 0.5:
                fc = random.choice(["#ffffff", "#ff7eb3", "#ffd93d", "#b39cff", "#ff6b6b"])
                put(s, cylinder(0.015, 0.12, 0.005, 6), (px, 0, pz), "#4caf50")
                put(s, sphere(0.06, 10), (px, 0.14, pz), fc)
                put(s, sphere(0.03, 8), (px, 0.17, pz - 0.03), "#ffe066")
            else:
                for k in range(3):
                    put(s, cone(0.04, 0.16 + k * 0.03, 6), (px + k * 0.05 - 0.05, 0, pz), "#5cb83a")
        elif key == "autumn":
            if r < 0.6:   # עלים שנשרו
                for _ in range(3):
                    put(s, rbox(0.12, 0.02, 0.08, 0.01), (px + random.uniform(-.2, .2), 0.01, pz + random.uniform(-.2, .2)),
                        random.choice(["#e67e22", "#c0392b", "#f1c40f", "#d35400"]))
            else:         # פטרייה
                put(s, cylinder(0.03, 0.12, 0.01, 8), (px, 0, pz), "#f5f0e1")
                put(s, sphere(0.08, 12), (px, 0.13, pz), "#e84118", scale=(1, 0.6, 1))
                put(s, sphere(0.015, 6), (px + 0.03, 0.17, pz + 0.03), "#ffffff")
        elif key == "winter":
            if r < 0.6:   # ערמת שלג
                put(s, sphere(0.14, 12), (px, 0.0, pz), "#ffffff", scale=(1.3, 0.5, 1))
            else:         # גביש קרח
                put(s, cone(0.05, 0.2, 6), (px, 0, pz), "#a5d8ff")
                put(s, cone(0.035, 0.14, 6), (px + 0.06, 0, pz), "#d0ebff")
        else:
            if r < 0.5:   # עשב יבש
                for k in range(3):
                    put(s, cone(0.035, 0.14 + k * 0.03, 5), (px + k * 0.05 - 0.05, 0, pz), "#c9a95a")
            else:         # חלוקי אבן
                put(s, sphere(0.06, 8), (px, 0.02, pz), "#c98c5a", scale=(1.3, 0.6, 1))
                put(s, sphere(0.04, 8), (px + 0.09, 0.01, pz + 0.04), "#b87a4b")

    # --- קלט ---
    def input(self, key):
        if self.shop_open:
            self.shop_input(key)
            return
        if key == "escape":
            application.quit()
        if key in ("c", "tab") and ((self.alive and not self.started) or (not self.alive and self.dead_time > 0.9)):
            self.open_shop()
            return
        if not self.alive:
            if key in ("r", "space") and self.dead_time > 0.9:
                self.reset()
            return
        if key in ("enter", "return", "numpad enter"):
            self.toggle_gun()
            return
        moves = {"up arrow": (0, 1), "w": (0, 1), "down arrow": (0, -1), "s": (0, -1),
                 "left arrow": (-1, 0), "a": (-1, 0), "right arrow": (1, 0), "d": (1, 0)}
        if key in moves:
            if self.hop_t < 1:
                self.queued = moves[key]
            else:
                self.try_move(*moves[key])

    def try_move(self, dx, dz):
        self.started = True
        self.hint.enabled = False
        ch = self.chicken
        target_rot = {(0, 1): 0, (0, -1): 180, (-1, 0): -90, (1, 0): 90}[(dx, dz)]
        ch.model_root.animate("rotation_y", target_rot, 0.06)
        nz = self.gz + dz
        row = self.rows.get(nz)
        if row is None:
            return
        tx = ch.x + dx if row.kind == "river" else round(ch.x) + dx
        if abs(round(tx)) > HALF:
            return
        if round(tx) in row.blocked:
            ch.model_root.animate_scale((1.1, 0.85, 1.1), 0.05)
            ch.model_root.animate_scale((1, 1, 1), 0.1, delay=0.05)
            return
        self.carrier = self.ride
        self.ride = None
        self.hop_from = Vec3(ch.x, ch.y, ch.z)
        self.hop_to = Vec3(tx, 0.12 if row.kind == "river" else 0, nz)
        self.gz = nz
        self.hop_t = 0
        if nz > self.max_z:
            self.max_z = nz
            self.score_text.text = str(nz)
            self.score_text.animate_scale(4.6, 0.05)
            self.score_text.animate_scale(4, 0.15, delay=0.05)

    # --- נחיתה ---
    def land(self):
        ch = self.chicken
        row = self.rows.get(self.gz)
        ch.model_root.scale = (1.12, 0.88, 1.12)
        ch.model_root.animate_scale((1, 1, 1), 0.12)
        for w in ch.wings:
            w.rotation_z = 0
        if row and row.kind == "river":
            px = round(ch.x)
            if px in row.pads and abs(ch.x - px) < 0.45:
                ch.x = px
                ch.y = WATER_Y + 0.05
                ch.ground_y = WATER_Y
                Ripple(Vec3(px, WATER_Y + 0.06, ch.z), size=0.9, life=0.6, alpha=0.6)
            else:
                best = None
                for lg in row.logs:
                    dist = abs(lg.x - ch.x)
                    if dist < lg.length / 2 + 0.35 and (best is None or dist < abs(best.x - ch.x)):
                        best = lg
                if best is None:
                    self.drown()
                    return
                self.ride = best
                self.ride_off = max(-best.length / 2 + 0.3, min(best.length / 2 - 0.3, ch.x - best.x))
                ch.ground_y = 0.12
                for _ in range(4):
                    Particle(Vec3(ch.x, 0.15, ch.z), "#a9744a",
                             (random.uniform(-1, 1), random.uniform(0.6, 1.2), random.uniform(-1, 1)),
                             life=0.35, size=0.07, gravity=3)
        else:
            ch.x = round(ch.x)
            ch.y = 0
            ch.ground_y = 0.0
            for i in range(6):   # ענן אבק בנחיתה
                a = i / 6 * 6.28
                Particle(ch.position + Vec3(math.cos(a) * 0.15, 0.05, math.sin(a) * 0.15), "#f4efe3",
                         (math.cos(a) * 1.2, random.uniform(0.3, 0.8), math.sin(a) * 1.2),
                         life=0.4, size=0.1, gravity=1, fade=True, grow=1.2, drag=4)
            if row and row.coin and row.coin.col == round(ch.x):
                self.collect_coin(row)
        self.gx = round(ch.x)
        if self.queued and self.alive:
            q, self.queued = self.queued, None
            self.try_move(*q)

    def collect_coin(self, row):
        c = row.coin
        row.coin = None
        pos = Vec3(c.world_x, 0.5, c.world_z)
        destroy(c.sh)
        c.animate_position(c.position + Vec3(0, 1.2, 0), 0.3, curve=curve.out_quad)
        c.animate_scale(0.01, 0.3)
        destroy(c, delay=0.32)
        for _ in range(14):
            Particle(pos, random.choice(["#ffe066", "#ffd32a", "#fff6c4"]),
                     (random.uniform(-2.5, 2.5), random.uniform(2, 4.5), random.uniform(-2.5, 2.5)),
                     life=0.6, size=0.07, gravity=7)
        Ripple(Vec3(pos.x, 0.03, pos.z), "#ffe066", size=1.0, life=0.5)
        self.coins += 1
        self.coin_text.text = str(self.coins)
        self.save["coins"] = self.coins
        write_save(self.save)
        self.coin_icon.animate_scale(0.065, 0.06)
        self.coin_icon.animate_scale(0.045, 0.2, delay=0.06)

    # --- עדכון ---
    def update(self):
        rdt = min(time.dt, 0.05)
        if self.shop_open and self.preview_model:
            self.preview_model.rotation_y += 50 * rdt
            fl = math.sin(time.time() * 5) if hasattr(time, "time") else 0
            for w in self.preview_wings:
                w.rotation_z = -max(0, fl) * 30 * w.side
        if not self.alive:
            self.ts = min(1.0, self.ts + rdt * 0.8)
        dt = rdt * self.ts
        tnow = getattr(self, "game_clock", 0) + dt
        self.game_clock = tnow
        scene.set_shader_input("t", tnow)
        scene.set_shader_input("cam_pos", camera.world_position)
        ch = self.chicken

        # קפיצה
        if self.hop_t < 1 and self.alive:
            self.hop_t = min(1, self.hop_t + dt / 0.14)
            if self.carrier is not None and abs(self.hop_to.z - self.carrier.row.z) < 0.1:
                shift = self.carrier.speed * self.carrier.dir * dt
                self.hop_from.x += shift
                self.hop_to.x += shift
            t = self.hop_t
            p = lerp(self.hop_from, self.hop_to, smooth(t))
            p.y = lerp(self.hop_from.y, self.hop_to.y, t) + math.sin(t * math.pi) * 0.45
            ch.position = p
            st = 1 + 0.16 * math.sin(t * math.pi)
            ch.model_root.scale = (1 / st ** 0.5, st, 1 / st ** 0.5)
            for w in ch.wings:
                w.rotation_z = -math.sin(t * math.pi) * 55 * w.side
            if self.hop_t >= 1:
                self.land()
        elif self.alive and self.ride is not None:
            lg = self.ride
            ch.x = lg.x + self.ride_off
            ch.y = 0.12 + math.sin(tnow * 2.5 + lg.phase) * 0.025
            self.gx = round(ch.x)
            if abs(ch.x) > HALF + 0.7:
                self.drown("Swept away!")

        # מכוניות, בולי עץ, רכבות, מטבעות
        for row in self.rows.values():
            for car in row.cars:
                car.e.x += car.speed * car.dir * dt
                if car.dir > 0 and car.e.x > 23:
                    car.e.x -= 46
                elif car.dir < 0 and car.e.x < -23:
                    car.e.x += 46
                car.puff_t -= dt
                if car.puff_t <= 0:
                    car.puff_t = random.uniform(0.35, 0.6)
                    if abs(car.e.x) < 11 and self.cam_z - 2 < row.z < self.cam_z + 14:
                        Particle(Vec3(car.e.x - car.dir * (car.length / 2 + 0.1), 0.3, row.z + 0.25),
                                 color.rgba(0.85, 0.86, 0.9, 0.55),
                                 (-car.dir * 0.5, 0.5, 0), life=0.9, size=0.14, gravity=-0.3,
                                 fade=True, grow=2.2, floor=0.2, drag=1)
            for lg in row.logs:
                lg.e.x += lg.speed * lg.dir * dt
                lg.e.y = math.sin(tnow * 2.5 + lg.phase) * 0.025
                if lg.dir > 0 and lg.e.x > 25:
                    lg.e.x -= 50
                elif lg.dir < 0 and lg.e.x < -25:
                    lg.e.x += 50
            if row.coin:
                row.coin.rotation_y += 160 * dt
                row.coin.y = 0.45 + math.sin(tnow * 3 + row.z) * 0.06
            if row.kind == "rail":
                self.update_rail(row, dt)

        self.update_ambient(dt, tnow)
        self.update_zone(rdt)
        if self.gun_on and self.alive:
            self.update_gun(rdt)
        self.update_flyers(rdt)

        if self.alive:
            self.check_collisions()
            if self.started:
                self.cam_z += (0.35 + min(0.9, self.max_z / 120)) * dt
            self.cam_z = max(self.cam_z, lerp(self.cam_z, self.gz - 1, min(1, dt * 3)))
            if self.gz < self.cam_z - 5.5 and self.hop_t >= 1:
                self.die("Too slow!", squash=False)
            while self.next_z < self.gz + 26:
                self.add_row()
            old = [z for z in self.rows if z < self.cam_z - 14]
            for z in old:
                r = self.rows.pop(z)
                self.targets = {k: t for k, t in self.targets.items() if t.row is not r}
                r.destroy()
        else:
            self.dead_time += rdt

        a = self.flash.color[3]
        if a > 0:
            self.flash.color = color.rgba(1, 1, 1, max(0, a - rdt * 2.5))
        self.update_camera()

    def update_ambient(self, dt, tnow):
        for c in self.clouds:
            c.x += c.speed * dt
            if c.x > 22:
                c.x = -22
                c.offz = random.uniform(-4, 20)
            c.z = self.cam_z + c.offz
        meadow = ZONES[zone_idx(round(self.cam_z + 7))]["key"] == "meadow"
        for b in self.butterflies:
            b.enabled = meadow and not self.shop_open
            if b.home.z < self.cam_z - 3:
                b.home = Vec3(random.uniform(-6, 6), 0.9, self.cam_z + random.uniform(8, 16))
            ph = tnow * 0.7 + b.phase
            target = b.home + Vec3(math.sin(ph) * 1.6, math.sin(ph * 2.3) * 0.25, math.cos(ph * 0.8) * 1.2)
            vel = target - b.position
            b.position = lerp(b.position, target, min(1, dt * 2))
            if vel.length() > 0.01:
                b.rotation_y = math.degrees(math.atan2(vel.x, vel.z))
            flap = math.sin(tnow * 22 + b.phase) * 60
            for w in b.wings:
                w.rotation_z = flap * w.side

    def update_rail(self, row, dt):
        if row.train is None:
            row.train_timer -= dt
            on = row.train_timer < 1.3 and int(row.train_timer * 8) % 2 == 0
            row.signal.setColorScale(C("#ff3030") if on else C("#5a0000"))
            if row.train_timer <= 0:
                self.spawn_train(row)
        else:
            tr = row.train
            tr.x += row.dir * 32 * dt
            if abs(row.z - self.gz) <= 2 and abs(tr.x - self.chicken.x) < 12 and self.alive:
                self.shake_t = max(self.shake_t, 0.05)
                self.shake_amp = 0.06
            if abs(tr.x) > 60:
                destroy(tr)
                row.train = None
                row.train_timer = random.uniform(3, 8)
                row.signal.setColorScale(C("#5a0000"))

    def spawn_train(self, row):
        tr = Entity(parent=row.root, x=-40 * row.dir, rotation_y=0 if row.dir > 0 else 180, shader=LIT)
        g = Entity(parent=tr, shader=LIT)
        shadow(g, 0, 0, 14, 0.95, height=1.4)
        base = random.choice(["#e74c3c", "#2e86de", "#f39c12", "#10ac84"])
        for i in range(4):
            cx = 5.25 - i * 3.5
            put(g, rbox(3.3, 1.3, 0.92, 0.22 if i else 0.3), (cx, 0.8, 0), base if i == 0 else "#f1f2f6")
            put(g, rbox(3.2, 0.12, 0.94, 0.05), (cx, 0.5, 0), C(base).tint(-0.15))
            for wx in (-1.1, -0.35, 0.4, 1.15):
                for zs in (-1, 1):
                    put(g, rbox(0.5, 0.36, 0.04, 0.06), (cx + wx, 1.0, zs * 0.465), "#2c3e57")
            put(g, rbox(3.0, 0.22, 0.72, 0.08), (cx, 0.12, 0), "#2d3436")
        put(g, sphere(0.12, 12), (6.92, 0.9, 0), "#fffbe0")
        g.set_shader_input("gloss", 1.0)
        g.flattenStrong()
        row.train = tr

    # ---------- אזורים ----------
    def update_zone(self, dt):
        zi = zone_idx(round(self.cam_z + 7))
        Z = ZONES[zi]
        k = min(1, dt * 0.8)
        self.sky = lerp(self.sky, Vec3(*Z["sky"]), k)
        self.grade = lerp(self.grade, Vec3(*Z["grade"]), k)
        window.color = color.rgba(self.sky.x, self.sky.y, self.sky.z, 1)
        scene.set_shader_input("fog_col", self.sky)
        scene.set_shader_input("grade", self.grade)
        # כרזה כשנכנסים לאזור חדש
        gzi = zone_idx(self.gz)
        if self.alive and gzi != self.zone_now:
            self.zone_now = gzi
            self.zone_token += 1
            self.zone_text.text = ZONES[gzi]["title"]
            self.zone_text.enabled = True
            self.zone_text.scale = 0.5
            self.zone_text.animate_scale(3, 0.4, curve=curve.out_back)
            invoke(self.hide_zone_text, self.zone_token, delay=2.4)
        # מזג אוויר
        if self.shop_open:
            return
        self.weather_t -= dt
        key = Z["key"]
        cx, cz = self.chicken.x, self.cam_z
        if key == "winter":
            while self.weather_t <= 0:
                self.weather_t += 1 / 40
                Particle(Vec3(cx + random.uniform(-13, 13), random.uniform(5, 8), cz + random.uniform(-2, 18)),
                         "#ffffff", (random.uniform(-0.3, 0.5), -1.6, 0), life=4.5, size=random.uniform(0.05, 0.09),
                         gravity=0, drag=0, glow=True)
        elif key == "autumn":
            while self.weather_t <= 0:
                self.weather_t += 1 / 6
                Particle(Vec3(cx + random.uniform(-12, 12), random.uniform(4, 6), cz + random.uniform(0, 16)),
                         random.choice(["#e67e22", "#d35400", "#f1c40f", "#c0392b"]),
                         (random.uniform(0.3, 0.9), -0.2, 0), life=6, size=0.1, gravity=0.5, drag=0.6, cube=True)
        elif key == "desert":
            while self.weather_t <= 0:
                self.weather_t += 1 / 7
                Particle(Vec3(cx + random.uniform(-14, 6), random.uniform(0.1, 1.0), cz + random.uniform(0, 14)),
                         color.rgba(0.95, 0.85, 0.65, 0.5), (random.uniform(2, 3.5), 0.1, 0), life=2.5, size=0.12,
                         gravity=0, drag=0, fade=True, grow=2.5, floor=0.05)
        else:
            self.weather_t = 0

    def hide_zone_text(self, token):
        if token == self.zone_token:
            self.zone_text.animate_scale(0.01, 0.25)
            invoke(setattr, self.zone_text, "enabled", False, delay=0.26)

    # ---------- חנות דמויות ----------
    def open_shop(self):
        self.shop_open = True
        self.hint.enabled = False
        self.panel.enabled = False
        self.center_text.text = ""
        self.sub_text.text = ""
        for e in self.butterflies:
            e.enabled = False
        scene.set_shader_input("dimf", 0.38)
        ids = [c[0] for c in CHARACTERS]
        self.shop_idx = ids.index(self.save.get("selected", "chicken"))
        ar = window.aspect_ratio
        ui = []
        top = Entity(parent=camera.ui, model="quad", scale=(ar, 0.2), y=0.4, z=2, color=color.rgba(0.05, 0.07, 0.15, 0.7))
        bot = Entity(parent=camera.ui, model="quad", scale=(ar, 0.34), y=-0.33, z=2,
                     color=color.rgba(0.05, 0.07, 0.15, 0.7))
        ui += [top, bot]
        ui.append(Text("CHARACTER SHOP", origin=(0, 0), y=0.4, scale=3, color=C("#ffe066")))
        self.shop_name = Text("", origin=(0, 0), y=-0.22, scale=2.8, color=color.white)
        self.shop_status = Text("", origin=(0, 0), y=-0.3, scale=1.7, color=color.white)
        self.shop_count = Text("", origin=(0, 0), y=-0.36, scale=1.2, color=color.light_gray)
        ui += [self.shop_name, self.shop_status, self.shop_count]
        for sx in (-1, 1):
            tri = Mesh(vertices=[(-0.5, 0, 0), (0.5, 0.5, 0), (0.5, -0.5, 0)], triangles=[0, 1, 2])
            ui.append(Entity(parent=camera.ui, model=tri, x=sx * 0.32, scale=(0.05, 0.08),
                             rotation_z=0 if sx < 0 else 180, color=color.rgba(1, 1, 1, 0.85), double_sided=True))
        ui.append(Text("LEFT / RIGHT = browse      ENTER = buy / select      C = back to game",
                       origin=(0, 0), y=-0.44, scale=1.2, color=C("#dfe6e9")))
        self.shop_ui = ui
        # במה תלת מימדית לתצוגה
        self.preview = Entity(parent=camera, position=(0, -0.2, 5.6), shader=LIT)
        self.chicken.enabled = False
        self.chicken.shadow.enabled = False
        self.preview.set_shader_input("dimf", 1.0)
        ped = Entity(parent=self.preview, shader=LIT, y=-0.62)
        put(ped, cylinder(0.8, 0.16, 0.05, 32), (0, -0.16, 0), "#ffd84d")
        put(ped, cylinder(0.68, 0.18, 0.05, 32), (0, -0.14, 0), "#fff3b0")
        ped.set_shader_input("gloss", 1.0)
        self.preview_ped = ped
        self.preview_model = None
        self.shop_show()

    def shop_show(self):
        cid, name, price = CHARACTERS[self.shop_idx]
        if self.preview_model:
            destroy(self.preview_model)
        m = Entity(parent=self.preview, shader=LIT, y=-0.62, rotation_y=180)
        self.preview_wings = build_character(m, cid)
        m.scale = 0.01
        m.animate_scale(1.0, 0.3, curve=curve.out_back)
        self.preview_model = m
        self.shop_name.text = name
        self.shop_count.text = f"{self.shop_idx + 1} / {len(CHARACTERS)}"
        owned = cid in self.save["owned"]
        if self.save.get("selected") == cid:
            self.shop_status.text, self.shop_status.color = "SELECTED", C("#7bed9f")
        elif owned:
            self.shop_status.text, self.shop_status.color = "OWNED  -  ENTER to select", color.white
        elif self.coins >= price:
            self.shop_status.text, self.shop_status.color = f"{price} coins  -  ENTER to buy", C("#ffe066")
        else:
            self.shop_status.text = f"{price} coins  (need {price - self.coins} more)"
            self.shop_status.color = C("#ff6b6b")

    def shop_input(self, key):
        if key in ("left arrow", "a"):
            self.shop_idx = (self.shop_idx - 1) % len(CHARACTERS)
            self.shop_show()
        elif key in ("right arrow", "d"):
            self.shop_idx = (self.shop_idx + 1) % len(CHARACTERS)
            self.shop_show()
        elif key in ("enter", "return", "space"):
            cid, name, price = CHARACTERS[self.shop_idx]
            if cid in self.save["owned"]:
                self.save["selected"] = cid
                write_save(self.save)
                self.shop_show()
            elif self.coins >= price:
                self.coins -= price
                self.coin_text.text = str(self.coins)
                self.save["coins"] = self.coins
                self.save["owned"].append(cid)
                self.save["selected"] = cid
                write_save(self.save)
                p = self.preview.world_position + Vec3(0, 0.3, 0)
                for _ in range(30):
                    Particle(p, random.choice(["#ffe066", "#ffffff", "#ff9ff3", "#7bed9f"]),
                             (random.uniform(-3, 3), random.uniform(1, 4), random.uniform(-3, 3)),
                             life=0.9, size=0.06, gravity=5, glow=True, floor=-50)
                self.shop_show()
            else:
                self.shop_status.animate_x(0.02, 0.05)
                self.shop_status.animate_x(-0.02, 0.05, delay=0.05)
                self.shop_status.animate_x(0, 0.05, delay=0.1)
        elif key in ("c", "tab", "escape"):
            self.close_shop()

    def close_shop(self):
        self.shop_open = False
        for e in self.shop_ui:
            destroy(e)
        self.shop_ui = []
        destroy(self.preview)
        self.preview_model = None
        self.reset()

    # ---------- מצב רובה ----------
    def toggle_gun(self):
        ch = self.chicken
        self.gun_on = not self.gun_on
        self.gun_text.enabled = self.gun_on
        self.hint.enabled = False
        if self.gun_on:
            ch.gun.enabled = True
            ch.gun.scale = 0.01
            ch.gun.animate_scale(1.45, 0.35, curve=curve.out_back)
            Ripple(Vec3(ch.x, ch.ground_y + 0.05, ch.z), "#ffd32a", size=1.6, life=0.5)
            for _ in range(12):
                Particle(ch.position + Vec3(0, 0.6, 0), random.choice(["#ffe066", "#ffffff"]),
                         (random.uniform(-2, 2), random.uniform(1, 3), random.uniform(-2, 2)),
                         life=0.5, size=0.07, gravity=4, glow=True)
        else:
            ch.gun.animate_scale(0.01, 0.15)
            invoke(setattr, ch.gun, "enabled", False, delay=0.16)

    def get_target(self, row, kind, obj):
        key = id(obj)
        if key not in self.targets:
            self.targets[key] = Target(row, kind, obj)
        return self.targets[key]

    def target_pos(self, t):
        if t.kind == "car":
            p = t.obj.e.world_position
            return Vec3(p.x, 0.5, p.z)
        tr = t.obj
        p = tr.world_position
        return Vec3(max(p.x - 6.5, min(p.x + 6.5, self.chicken.x)), 0.8, p.z)

    def update_gun(self, dt):
        ch = self.chicken
        self.gun_text.scale = 1.8 + math.sin(self.game_clock * 8) * 0.08
        # בחירת מטרה: הרכב הקרוב ביותר שעדיין לא נורה
        cands = []
        for z in range(self.gz - 2, self.gz + 8):
            row = self.rows.get(z)
            if not row:
                continue
            for car in row.cars:
                t = self.get_target(row, "car", car)
                if not t.dead and abs(car.x - ch.x) < 12:
                    cands.append(t)
            if row.train is not None and abs(row.train.x - ch.x) < 14:
                t = self.get_target(row, "train", row.train)
                if not t.dead:
                    cands.append(t)
        aim = None
        if cands:
            cands.sort(key=lambda t: (t.pending > 0, (self.target_pos(t) - ch.position).length()))
            aim = cands[0]
        if aim is None:
            return
        tp = self.target_pos(aim)
        d = tp - ch.position
        ang = math.degrees(math.atan2(d.x, d.z))
        g = ch.gun
        g.rotation_y = ang
        a = math.radians(ang)
        g.position = Vec3(math.cos(a) * 0.36 + math.sin(a) * 0.12, 0.45, -math.sin(a) * 0.36 + math.cos(a) * 0.12)
        if self.hop_t >= 1:
            ch.model_root.rotation_y = ang
        self.fire_t -= dt
        if self.fire_t <= 0 and aim.pending < 1:
            self.fire_t = 0.09
            self.fire(aim)

    def fire(self, target):
        ch = self.chicken
        tip = ch.gun_tip.world_position
        target.pending += 1
        Bullet(tip, target)
        # הבזק לוע
        f = Entity(position=tip, shader=LIT)
        put(f, sphere(0.5, 10), col="#fff6c4")
        put(f, sphere(0.5, 10), col="#ff9f1a", scale=1.5)
        f.set_shader_input("unlit", 1.0)
        f.scale = 0.35
        f.animate_scale(0.01, 0.07)
        destroy(f, delay=0.08)
        # רתע ותרמיל
        ch.gun_body.z = -0.1
        ch.gun_body.animate_z(0, 0.08)
        Particle(tip, "#e1b12c", (random.uniform(-1.5, 1.5), random.uniform(2, 3), random.uniform(-1.5, 1.5)),
                 life=0.7, size=0.05, gravity=12, cube=True)

    def explosion(self, pos, col, big=1.0):
        for _ in range(int(16 * big)):     # כדור אש
            Particle(pos + Vec3(random.uniform(-.3, .3), random.uniform(0, .3), random.uniform(-.3, .3)),
                     random.choice(["#fff3b0", "#ffd32a", "#ff9f1a", "#ff5e1a", "#ff3b1a"]),
                     (random.uniform(-3, 3) * big, random.uniform(1, 4), random.uniform(-3, 3) * big),
                     life=random.uniform(0.45, 0.9), size=0.38 * big, gravity=-2, fade=True, grow=2.5,
                     glow=True, drag=4, floor=0.1)
        for _ in range(int(10 * big)):     # עשן
            Particle(pos + Vec3(0, 0.3, 0), color.rgba(0.22, 0.22, 0.25, 0.75),
                     (random.uniform(-1.5, 1.5), random.uniform(1, 2.5), random.uniform(-1.5, 1.5)),
                     life=random.uniform(1.4, 2.4), size=0.4 * big, gravity=-1.2, fade=True, grow=3,
                     drag=2, floor=0.2)
        for _ in range(int(18 * big)):     # ניצוצות
            Particle(pos, "#ffe066", (random.uniform(-8, 8), random.uniform(3, 8), random.uniform(-8, 8)),
                     life=random.uniform(0.3, 0.6), size=0.06, gravity=14, glow=True, drag=1)
        for _ in range(int(10 * big)):     # חלקים
            Particle(pos + Vec3(0, 0.4, 0), random.choice([col, col, "#202227", "#c8ccd4"]),
                     (random.uniform(-5, 5), random.uniform(4, 9), random.uniform(-5, 5)),
                     life=random.uniform(1.2, 1.8), size=random.uniform(0.1, 0.22), gravity=16, cube=True, drag=0.5)
        Ripple(Vec3(pos.x, 0.06, pos.z), "#ffb347", size=3.2 * big, life=0.5, alpha=0.9)
        Ripple(Vec3(pos.x, 0.07, pos.z), "#ffffff", size=2.0 * big, life=0.35, alpha=0.7)
        self.shake_t = max(self.shake_t, 0.25)
        self.shake_amp = 0.12 * big
        self.flash.color = color.rgba(1, 0.9, 0.7, max(self.flash.color[3], 0.15))

    def blast(self, t):
        if t.dead:
            return
        t.dead = True
        row = t.row
        if t.kind == "car":
            car = t.obj
            if car in row.cars:
                row.cars.remove(car)
            e, lift, mass = car.e, 0.45, 1.0
            col = random.choice(CAR_COLORS)
        else:
            if row.train is not t.obj:
                return
            row.train = None
            row.train_timer = random.uniform(4, 9)
            row.signal.setColorScale(C("#5a0000"))
            e, lift, mass = t.obj, 0.8, 2.2
            col = "#f1f2f6"
        pos = self.target_pos(t)
        self.explosion(pos, col, big=1.0 if mass < 2 else 1.6)
        # סימן חריכה על הכביש
        sc = Entity(parent=row.root, x=pos.x - row.root.x, y=0.025, shader=LIT)
        put(sc, blob_mesh(), col=None)
        make_transparent(sc)
        sc.setColorScale(color.rgba(0.05, 0.04, 0.04, 0.55))
        sc.scale = (1.3 * mass, 1, 0.6)
        # הרכב עף באוויר
        wp, wr = e.world_position, e.world_rotation
        e.world_parent = scene
        e.world_position = wp
        e.world_rotation = wr
        for ch_ in e.children:
            ch_.y -= lift
        e.y += lift
        e.setColorScale(0.42, 0.38, 0.36, 1)
        side = 1 if pos.x >= self.chicken.x else -1
        vel = Vec3(side * random.uniform(2, 5) / mass, random.uniform(9, 13) / (mass ** 0.5), random.uniform(1, 4))
        spin = Vec3(random.uniform(-400, 400), random.uniform(-500, 500), random.uniform(-400, 400)) / mass
        self.flyers.append(Flyer(e, vel, spin))
        self.targets.pop(id(t.obj), None)

    def update_flyers(self, dt):
        for f in list(self.flyers):
            if f.done:
                continue
            f.vel.y -= 20 * dt
            f.e.position += f.vel * dt
            f.e.rotation += f.spin * dt
            f.smoke_t -= dt
            if f.smoke_t <= 0:
                f.smoke_t = 0.05
                Particle(f.e.position, color.rgba(0.15, 0.15, 0.17, 0.7), (0, 0.6, 0), life=0.9, size=0.3,
                         gravity=-0.5, fade=True, grow=2.2, floor=-5)
                Particle(f.e.position, random.choice(["#ff9f1a", "#ffd32a"]), (0, 0.3, 0), life=0.3, size=0.3,
                         gravity=0, fade=True, grow=1.5, glow=True, floor=-5)
            if f.e.y < 0.45 and f.vel.y < 0:
                if f.bounces == 0:
                    f.bounces = 1
                    f.vel = Vec3(f.vel.x * 0.5, -f.vel.y * 0.35, f.vel.z * 0.5)
                    f.spin *= 0.4
                    self.explosion(f.e.position, "#555555", big=0.5)
                else:
                    f.done = True
                    self.explosion(f.e.position, "#555555", big=0.6)
                    f.e.animate_scale(0.01, 0.25)
                    destroy(f.e, delay=0.27)
                    self.flyers.remove(f)
            elif f.e.y < -6 or abs(f.e.x) > 40:
                destroy(f.e)
                self.flyers.remove(f)

    def check_collisions(self):
        ch = self.chicken
        row = self.rows.get(round(ch.z))
        if not row or ch.y > 0.35:
            return
        for car in list(row.cars):
            if abs(car.x - ch.x) < car.length / 2 + 0.28:
                if self.gun_on:          # ברובה - הרכב מתפוצץ והתרנגולת ממשיכה בשלווה
                    self.blast(self.get_target(row, "car", car))
                    continue
                self.die("Splat!")
                return
        if row.train is not None and abs(row.train.x - ch.x) < 7.3:
            if self.gun_on:
                self.blast(self.get_target(row, "train", row.train))
                return
            self.die("Choo choo!")

    def drown(self, msg="Splash!"):
        ch = self.chicken
        pos = Vec3(ch.x, WATER_Y + 0.05, ch.z)
        for _ in range(24):
            Particle(pos, random.choice(["#ffffff", "#cfefff", "#8fd3ff"]),
                     (random.uniform(-1.8, 1.8), random.uniform(3, 6), random.uniform(-1.8, 1.8)),
                     life=random.uniform(0.6, 1.1), size=random.uniform(0.07, 0.14), gravity=12,
                     floor=WATER_Y)
        Ripple(pos, size=1.4, life=0.9)
        Ripple(pos, size=2.2, life=1.4, alpha=0.5)
        ch.animate_y(WATER_Y - 1.2, 0.6, curve=curve.in_quad)
        ch.shadow.enabled = False
        self.die(msg, squash=False, effect=False)

    def die(self, msg, squash=True, effect=True):
        if not self.alive:
            return
        self.alive = False
        self.dead_time = 0
        self.ts = 0.2            # הילוך איטי לרגע
        ch = self.chicken
        if squash:
            ch.flatten()
            ch.y = ch.ground_y + 0.02
            self.hop_t = 1
            self.flash.color = color.rgba(1, 1, 1, 0.55)
            for _ in range(28):
                Particle(ch.position + Vec3(0, 0.4, 0), random.choice(["#ffffff", "#f5f5f5", "#e6e6e6"]),
                         (random.uniform(-3, 3), random.uniform(2, 6), random.uniform(-3, 3)),
                         life=random.uniform(1.2, 2.2), size=random.uniform(0.1, 0.18), gravity=4, drag=2.5)
            for _ in range(8):
                Particle(ch.position + Vec3(0, 0.3, 0), random.choice(["#ffd32a", "#ff3b3b"]),
                         (random.uniform(-3, 3), random.uniform(2, 4), random.uniform(-3, 3)), life=0.8, size=0.09)
            Ripple(Vec3(ch.x, ch.ground_y + 0.03, ch.z), size=1.8, life=0.6)
        elif effect:
            ch.animate_position(ch.position + Vec3(0, 6, -3), 0.8)
        self.best = max(self.best, self.max_z)
        self.best_text.text = f"BEST {self.best}"
        self.save["best"] = self.best
        self.save["coins"] = self.coins
        write_save(self.save)
        self.hint.enabled = False
        invoke(self.show_game_over, msg, self.max_z, delay=0.8)
        self.shake_t = 0.35
        self.shake_amp = 0.18

    def show_game_over(self, msg, score):
        if self.alive or score != self.max_z:
            return
        self.center_text.text = msg
        self.center_text.scale = 0.1
        self.center_text.animate_scale(3.2, 0.35, curve=curve.out_back)
        self.sub_text.text = f"Score {score}   Best {self.best}\n\nR / SPACE = play again     C = shop"
        self.panel.enabled = True
        self.panel.scale = (0.95, 0.01)
        self.panel.animate_scale((0.95, 0.42), 0.25, curve=curve.out_quad)

    def update_camera(self, instant=False):
        ch = self.chicken
        zoom = 0 if self.alive else min(1.5, self.dead_time * 2)
        target = Vec3(ch.x * 0.45 + 2.6 - zoom * 0.3, 13.5 - zoom * 2, self.cam_z - 7.6 + zoom * 1.2)
        if instant:
            camera.position = target
        else:
            camera.position = lerp(camera.position, target, min(1, time.dt * 5))
        if self.shake_t > 0:
            self.shake_t -= time.dt
            camera.position += Vec3(random.uniform(-1, 1), random.uniform(-1, 1), 0) * self.shake_amp
        camera.rotation = (58, -14, 0)


camera.fov = 45
game = Game()
app.run()