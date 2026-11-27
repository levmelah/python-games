import math
import os
import random
from array import array

import pygame


WIDTH, HEIGHT = 1280, 720
FPS = 60
SAMPLE_RATE = 44100

PALETTES = [
    {
        "top": (7, 8, 26),
        "bottom": (2, 1, 10),
        "neon_a": (0, 245, 255),
        "neon_b": (255, 0, 220),
        "wave": (40, 120, 255),
        "spark": (170, 220, 255),
    },
    {
        "top": (36, 18, 76),
        "bottom": (9, 4, 28),
        "neon_a": (190, 120, 255),
        "neon_b": (120, 70, 255),
        "wave": (95, 75, 220),
        "spark": (210, 190, 255),
    },
    {
        "top": (2, 32, 20),
        "bottom": (1, 8, 6),
        "neon_a": (40, 255, 170),
        "neon_b": (0, 180, 120),
        "wave": (0, 140, 88),
        "spark": (180, 255, 220),
    },
]


def lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def draw_vertical_gradient(surface, top, bottom):
    w, h = surface.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surface, lerp_color(top, bottom, t), (0, y), (w, y))


def palette_at(progress):
    idx = int(progress) % len(PALETTES)
    next_idx = (idx + 1) % len(PALETTES)
    t = progress - int(progress)
    return {key: lerp_color(PALETTES[idx][key], PALETTES[next_idx][key], t) for key in PALETTES[idx]}


def triangle_points(cx, cy, radius, angle):
    points = []
    for i in range(3):
        a = angle + i * (math.tau / 3)
        x = cx + math.cos(a) * radius
        y = cy + math.sin(a) * radius
        points.append((x, y))
    return points


def draw_wave_ribbons(surface, w, h, phase, wave_color, neon_color):
    wave_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    step = 24
    for i in range(9):
        base_y = h * (0.12 + i * 0.085)
        amp = 18 + i * 5
        thickness = 18 + i * 2
        upper = []
        lower = []
        for x in range(0, w + step, step):
            y = base_y
            y += math.sin(x * 0.008 + phase * (1.1 + i * 0.07) + i * 0.9) * amp
            y += math.sin(x * 0.0035 - phase * 1.8) * (amp * 0.6)
            upper.append((x, y - thickness))
            lower.append((x, y + thickness))
        poly = upper + list(reversed(lower))
        alpha = 30 + i * 9
        fill = (wave_color[0], wave_color[1], wave_color[2], alpha)
        stroke = (neon_color[0], neon_color[1], neon_color[2], 120)
        pygame.draw.polygon(wave_surface, fill, poly)
        pygame.draw.aalines(wave_surface, stroke, False, upper)
        pygame.draw.aalines(wave_surface, stroke, False, lower)
    surface.blit(wave_surface, (0, 0))


def draw_energy_arcs(surface, cx, cy, w, h, phase, neon_a, neon_b):
    arc_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(7):
        rx = w * (0.22 + i * 0.08)
        ry = h * (0.08 + i * 0.045)
        rot = phase * (0.2 + i * 0.05) + i * 0.6
        points = []
        for s in range(70):
            t = s / 69.0
            ang = (0.2 + t * 1.45) * math.pi
            x = cx + math.cos(ang + rot) * rx
            y = cy + math.sin(ang * 1.18 + rot * 0.5) * ry
            points.append((x, y))
        color = lerp_color(neon_a, neon_b, i / 6.0)
        alpha = 90 + i * 18
        pygame.draw.aalines(arc_surface, (color[0], color[1], color[2], alpha), False, points)
    surface.blit(arc_surface, (0, 0))


def draw_dot_matrix(surface, w, h, phase, color):
    dot_surface = pygame.Surface((w, h), pygame.SRCALPHA)
    origin_x = int(w * 0.63)
    origin_y = int(h * 0.55)
    for gy in range(16):
        for gx in range(36):
            x = origin_x + gx * 12
            y = origin_y + gy * 10
            if x >= w or y >= h:
                continue
            pulse = 0.5 + 0.5 * math.sin(phase * 3.5 + gx * 0.23 + gy * 0.35)
            a = int(35 + 110 * pulse)
            pygame.draw.circle(dot_surface, (color[0], color[1], color[2], a), (x, y), 1)
    surface.blit(dot_surface, (0, 0))


def draw_center_glow(surface, cx, cy, max_radius, color):
    glow = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for i in range(5):
        r = int(max_radius * (0.18 + i * 0.09))
        a = int(65 / (i + 1))
        pygame.draw.circle(glow, (color[0], color[1], color[2], a), (cx, cy), r)
    surface.blit(glow, (0, 0), special_flags=pygame.BLEND_ADD)


def draw_keyboard_pulses(surface, pulses, palette, dt):
    pulse_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    keep = []
    for p in pulses:
        p["age"] += dt
        life_t = p["age"] / p["life"]
        if life_t >= 1.0:
            continue
        keep.append(p)
        r = int(20 + p["power"] * 380 * life_t)
        a = int(190 * (1.0 - life_t) ** 1.8)
        col = lerp_color(palette["neon_a"], palette["neon_b"], p["hue"])
        pygame.draw.circle(pulse_surface, (col[0], col[1], col[2], a), p["pos"], r, max(2, int(8 * (1.0 - life_t))))
        tri_r = int(r * 0.55)
        tri = triangle_points(p["pos"][0], p["pos"][1], tri_r, p["spin"] + p["age"] * 2.6)
        pygame.draw.polygon(pulse_surface, (col[0], col[1], col[2], int(a * 0.7)), tri, 2)
    pulses[:] = keep
    surface.blit(pulse_surface, (0, 0), special_flags=pygame.BLEND_ADD)


def make_tone(freq, duration=0.12, volume=0.14, wave="sine"):
    count = max(1, int(SAMPLE_RATE * duration))
    attack = int(count * 0.08)
    release = int(count * 0.20)
    buf = array("h")
    for i in range(count):
        t = i / SAMPLE_RATE
        if wave == "triangle":
            p = (t * freq) % 1.0
            sample = 4.0 * abs(p - 0.5) - 1.0
        elif wave == "square":
            sample = 1.0 if math.sin(math.tau * freq * t) >= 0 else -1.0
        else:
            sample = math.sin(math.tau * freq * t)

        env = 1.0
        if i < attack:
            env = i / max(1, attack)
        elif i > count - release:
            env = (count - i) / max(1, release)

        buf.append(int(32767 * volume * env * sample))
    return pygame.mixer.Sound(buffer=buf.tobytes())


def make_ambient_loop(duration=8.0, volume=0.34):
    count = max(1, int(SAMPLE_RATE * duration))
    buf = array("h")
    chords = [55.0, 65.41, 82.41, 98.0]
    arp = [220.0, 246.94, 261.63, 329.63, 392.0, 329.63, 261.63, 246.94]

    for i in range(count):
        t = i / SAMPLE_RATE
        ch_idx = int((t / duration) * len(chords)) % len(chords)
        root = chords[ch_idx]
        third = root * 1.2599
        fifth = root * 1.4983

        pad = (
            0.56 * math.sin(math.tau * root * t)
            + 0.26 * math.sin(math.tau * third * t)
            + 0.18 * math.sin(math.tau * fifth * t)
        )

        arp_idx = int(t * 4.0) % len(arp)
        arp_env = 0.5 + 0.5 * math.sin(math.tau * 2.0 * t)
        arp_wave = math.sin(math.tau * arp[arp_idx] * t) * arp_env

        bass = math.sin(math.tau * (root * 0.5) * t) * (0.5 + 0.5 * math.sin(math.tau * 1.0 * t))

        sample = pad * 0.62 + arp_wave * 0.28 + bass * 0.18
        sample = max(-1.0, min(1.0, sample))
        buf.append(int(32767 * volume * sample))

    return pygame.mixer.Sound(buffer=buf.tobytes())


def main():
    pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
    pygame.init()

    try:
        pygame.mixer.init()
    except pygame.error:
        pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Infinite Neon Background X")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)

    bg_image_original = None
    bg_image_scaled = None
    bg_size_cached = None
    bg_path = os.path.join(os.path.dirname(__file__), "img", "download (4).jpeg")
    if os.path.exists(bg_path):
        try:
            bg_image_original = pygame.image.load(bg_path).convert()
        except pygame.error:
            bg_image_original = None

    speed = 0.7
    phase = 0.0
    running = True
    palette_phase = 0.0
    auto_palette = True
    beat_energy = 0.0
    pulses = []
    help_visible = True

    audio_muted = False
    audio_enabled = pygame.mixer.get_init() is not None
    ambient_channel = None
    key_sounds = []
    audio_message = "audio off"

    if audio_enabled:
        scale = [220.0, 246.94, 261.63, 293.66, 329.63, 392.0, 440.0, 493.88]
        for i, f in enumerate(scale):
            wave = "sine" if i % 2 == 0 else "triangle"
            key_sounds.append(make_tone(f * 2, duration=0.12, volume=0.14, wave=wave))
        ambient_loop = make_ambient_loop(duration=8.0, volume=0.34)
        ambient_channel = pygame.mixer.Channel(0)
        ambient_channel.play(ambient_loop, loops=-1)
        audio_message = "audio on"

    ring_layers = [i / 30.0 for i in range(30)]
    tri_layers = [i / 26.0 for i in range(26)]

    stars = [
        [
            random.uniform(0, WIDTH),
            random.uniform(0, HEIGHT),
            random.uniform(0.3, 1.8),
            random.uniform(30.0, 180.0),
        ]
        for _ in range(260)
    ]

    fullscreen = False
    palette_keys = {
        pygame.K_1: 0.0,
        pygame.K_2: 1.0,
        pygame.K_3: 2.0,
        pygame.K_KP1: 0.0,
        pygame.K_KP2: 1.0,
        pygame.K_KP3: 2.0,
    }

    while running:
        dt = clock.tick(FPS) / 1000.0
        beat_energy = max(0.0, beat_energy - dt * 1.35)
        phase += dt * speed * (1.0 + beat_energy * 0.35)
        if auto_palette:
            palette_phase += dt * 0.12

        w, h = screen.get_size()
        cx, cy = w // 2, h // 2

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                    continue

                beat_energy = min(1.0, beat_energy + 0.28)

                if audio_enabled and not audio_muted and key_sounds:
                    key_sounds[event.key % len(key_sounds)].play()

                px = int(cx + random.uniform(-w * 0.2, w * 0.2))
                py = int(cy + random.uniform(-h * 0.15, h * 0.15))
                pulses.append(
                    {
                        "pos": (px, py),
                        "power": random.uniform(0.65, 1.15),
                        "age": 0.0,
                        "life": random.uniform(0.55, 1.15),
                        "hue": random.random(),
                        "spin": random.uniform(0.0, math.tau),
                    }
                )

                if event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                elif event.key == pygame.K_c:
                    auto_palette = not auto_palette
                elif event.key in palette_keys:
                    auto_palette = False
                    palette_phase = palette_keys[event.key]
                elif event.key == pygame.K_h:
                    help_visible = not help_visible
                elif event.key == pygame.K_m:
                    audio_muted = not audio_muted
                    if audio_enabled and ambient_channel is not None:
                        if audio_muted:
                            ambient_channel.pause()
                            audio_message = "audio muted"
                        else:
                            ambient_channel.unpause()
                            audio_message = "audio on"
                elif event.key == pygame.K_UP:
                    speed = min(2.2, speed + 0.08)
                elif event.key == pygame.K_DOWN:
                    speed = max(0.2, speed - 0.08)
            elif event.type == pygame.VIDEORESIZE and not fullscreen:
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

        max_r = math.hypot(w, h) * 0.72
        palette = palette_at(palette_phase)
        energy = 0.6 + beat_energy * 1.25

        if bg_image_original is not None:
            if bg_size_cached != (w, h):
                bg_image_scaled = pygame.transform.smoothscale(bg_image_original, (w, h))
                bg_size_cached = (w, h)
            screen.blit(bg_image_scaled, (0, 0))
            image_tint = pygame.Surface((w, h), pygame.SRCALPHA)
            image_tint.fill((8, 18, 14, 55))
            screen.blit(image_tint, (0, 0))
        else:
            draw_vertical_gradient(screen, palette["top"], palette["bottom"])
        draw_wave_ribbons(screen, w, h, phase * (1.0 + beat_energy * 0.4), palette["wave"], palette["neon_b"])

        for s in stars:
            s[0] -= s[2] * 110.0 * dt
            if s[0] < -10:
                s[0] = w + random.uniform(0, 60)
                s[1] = random.uniform(0, h)
            pulse = 0.5 + 0.5 * math.sin(phase * 4.2 * energy + s[3])
            star_color = lerp_color(palette["spark"], palette["neon_a"], pulse)
            pygame.draw.circle(screen, star_color, (int(s[0]), int(s[1])), int(s[2]))

        draw_center_glow(screen, cx, cy, max_r, palette["neon_a"])

        ring_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        for i, base in enumerate(ring_layers):
            p = (base + phase * (0.9 + beat_energy * 0.35)) % 1.0
            r = 12 + (p**2.15) * max_r
            alpha = int((220 + beat_energy * 45) * (1.0 - p) ** 1.4)
            width = 1 + int((1.0 - p) * 3)
            c_rgb = lerp_color(palette["neon_a"], palette["neon_b"], i / max(1, len(ring_layers) - 1))
            c = (c_rgb[0], c_rgb[1], c_rgb[2], alpha)
            pygame.draw.circle(ring_surface, c, (cx, cy), int(r), width)
        screen.blit(ring_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        tri_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        for base in tri_layers:
            p = (base + phase * (1.1 + beat_energy * 0.45)) % 1.0
            r = 18 + (p**2.0) * max_r * 0.9
            a = phase * (1.0 + beat_energy * 0.2) + p * 1.8
            alpha = int(255 * (1.0 - p) ** 1.3)
            rgb = lerp_color(palette["neon_a"], palette["neon_b"], p)
            pygame.draw.polygon(tri_surface, (rgb[0], rgb[1], rgb[2], alpha), triangle_points(cx, cy, r, a), 2)
        screen.blit(tri_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        draw_energy_arcs(screen, cx, cy, w, h, phase * energy, palette["neon_a"], palette["neon_b"])
        draw_dot_matrix(screen, w, h, phase, palette["spark"])
        draw_keyboard_pulses(screen, pulses, palette, dt)

        rail_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        shift = (phase * 480) % 180
        for i in range(-2, 8):
            x1 = i * 220 - shift
            x2 = x1 + 260
            rgb = lerp_color(palette["neon_b"], palette["neon_a"], (i + 2) / 10.0)
            pygame.draw.line(rail_surface, (rgb[0], rgb[1], rgb[2], 95), (x1, h), (x2, 0), 2)
            pygame.draw.line(rail_surface, (rgb[0], rgb[1], rgb[2], 60), (w - x1, h), (w - x2, 0), 2)
        screen.blit(rail_surface, (0, 0), special_flags=pygame.BLEND_ADD)

        grain = pygame.Surface((w, h), pygame.SRCALPHA)
        for _ in range(max(120, (w * h) // 9000)):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            grain.set_at((x, y), (255, 255, 255, random.randint(8, 20)))
        screen.blit(grain, (0, 0))

        for y in range(0, h, 3):
            pygame.draw.line(screen, (0, 0, 0), (0, y), (w, y), 1)

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(5):
            pad = i * 24
            a = 16 + i * 8
            pygame.draw.rect(overlay, (0, 0, 0, a), (pad, pad, w - 2 * pad, h - 2 * pad), 0, 22)
        screen.blit(overlay, (0, 0))

        if help_visible:
            help_text = "Reactive mode: keys make sound | M mute | C auto color | 1-3 palette | Up/Down speed | H help | F fullscreen"
            status_text = audio_message
            label = font.render(help_text, True, palette["spark"])
            status = font.render(status_text, True, palette["neon_a"])
            shadow = font.render(help_text, True, (0, 0, 0))
            status_shadow = font.render(status_text, True, (0, 0, 0))
            screen.blit(shadow, (15, h - 31))
            screen.blit(label, (14, h - 32))
            screen.blit(status_shadow, (15, 17))
            screen.blit(status, (14, 16))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
