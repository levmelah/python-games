import colorsys
import math
import random
import time
import tkinter
from pathlib import Path
import turtle

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
MIN_POINTS = 25
MIN_RADIUS = 40
MAX_ANGLE_GAP = 60
ERROR_SENSITIVITY = 0.12
BACKGROUND_RINGS = (90, 170, 250)
CONFETTI_COLORS = ["#ff6b6b", "#feca57", "#1dd1a1", "#54a0ff", "#ff9ff3", "#f6e58d"]
HIGH_SCORE_FILE = Path(__file__).with_name("draw_perfect_circle_highscore.txt")

screen = turtle.Screen()
screen.title("Draw a Perfect Circle")
screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
screen.bgcolor("black")

pen = turtle.Turtle()
pen.hideturtle()
pen.color("#39ff14")
pen.pensize(3)
pen.speed(0)
pen.penup()

guide = turtle.Turtle()
guide.hideturtle()
guide.color("#555555")
guide.speed(0)
guide.penup()

ideal = turtle.Turtle()
ideal.hideturtle()
ideal.color("#555555")
ideal.pensize(1)
ideal.speed(0)
ideal.penup()

text_pen = turtle.Turtle()
text_pen.hideturtle()
text_pen.color("#aaaaaa")
text_pen.speed(0)
text_pen.penup()

center_pen = turtle.Turtle()
center_pen.hideturtle()
center_pen.color("#d4ff3d")
center_pen.speed(0)
center_pen.penup()

rings = turtle.Turtle()
rings.hideturtle()
rings.color("#161616")
rings.speed(0)
rings.penup()

confetti = turtle.Turtle()
confetti.hideturtle()
confetti.speed(0)
confetti.penup()

drawing = False
points = []
best_score = 0.0
start_time = time.time()


def load_best_score():
    try:
        return float(HIGH_SCORE_FILE.read_text(encoding="utf-8").strip() or "0")
    except (FileNotFoundError, ValueError):
        return 0.0


def save_best_score():
    HIGH_SCORE_FILE.write_text(str(best_score), encoding="utf-8")


def draw_background_rings():
    for radius in BACKGROUND_RINGS:
        rings.goto(0, -radius)
        rings.pendown()
        rings.circle(radius)
        rings.penup()


def pulse_center_dot():
    try:
        size = 7 + 2 * math.sin((time.time() - start_time) * 3)
        guide.clear()
        guide.color("white")
        guide.goto(0, 0)
        guide.dot(size)
        screen.ontimer(pulse_center_dot, 50)
    except (turtle.Terminator, tkinter.TclError):
        pass


def celebrate(cx, cy, mean_r):
    confetti.clear()
    for _ in range(30):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(mean_r * 0.2, mean_r * 1.4)
        confetti.goto(cx + dist * math.cos(angle), cy + dist * math.sin(angle))
        confetti.dot(random.randint(4, 8), random.choice(CONFETTI_COLORS))


def show_message(title, subtitle=""):
    text_pen.clear()
    text_pen.goto(0, SCREEN_HEIGHT // 2 - 50)
    text_pen.write(title, align="center", font=("Courier", 18, "normal"))
    if subtitle:
        text_pen.goto(0, SCREEN_HEIGHT // 2 - 78)
        text_pen.write(subtitle, align="center", font=("Courier", 13, "normal"))


def show_center_score(score, is_record):
    center_pen.clear()
    center_pen.goto(0, -18)
    center_pen.write(f"{score:.1f}%", align="center", font=("Courier", 54, "bold"))
    sub = "New best! Click to try again" if is_record else "Click to try again"
    center_pen.goto(0, -70)
    center_pen.write(sub, align="center", font=("Courier", 13, "normal"))


def reset_round():
    global points
    pen.clear()
    ideal.clear()
    center_pen.clear()
    confetti.clear()
    points = []
    show_message(f"Best score: {best_score:.1f}%", "Click and drag to draw a circle")


def error_color(ratio):
    ratio = max(0.0, min(1.0, ratio))
    hue = (1 - ratio) * (120 / 360)  # green (close to ideal) -> red (far off)
    return colorsys.hsv_to_rgb(hue, 0.85, 1.0)


def draw_gradient_stroke(pts, cx, cy, mean_r):
    screen.tracer(0)
    pen.clear()
    pen.pensize(5)
    pen.penup()
    pen.goto(pts[0])
    pen.pendown()
    for x, y in pts[1:]:
        error_ratio = abs(math.hypot(x - cx, y - cy) - mean_r) / mean_r
        pen.pencolor(error_color(error_ratio / ERROR_SENSITIVITY))
        pen.goto(x, y)
    pen.penup()
    screen.update()
    screen.tracer(1)


def angle_coverage_ok(cx, cy, pts):
    angles = sorted(math.atan2(y - cy, x - cx) for x, y in pts)
    angles.append(angles[0] + 2 * math.pi)
    max_gap = max(math.degrees(b - a) for a, b in zip(angles, angles[1:]))
    return max_gap <= MAX_ANGLE_GAP


def score_circle(pts):
    cx = sum(x for x, y in pts) / len(pts)
    cy = sum(y for x, y in pts) / len(pts)
    radii = [math.hypot(x - cx, y - cy) for x, y in pts]
    mean_r = sum(radii) / len(radii)
    variance = sum((r - mean_r) ** 2 for r in radii) / len(radii)
    std_r = math.sqrt(variance)
    closure_gap = math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1])

    variation_ratio = std_r / mean_r
    closure_ratio = closure_gap / mean_r
    score = 100 - variation_ratio * 300 - closure_ratio * 60
    score = max(0.0, min(100.0, score))
    return score, cx, cy, mean_r


def evaluate():
    global best_score

    if len(points) < MIN_POINTS:
        show_message("Too short!", "Draw a full loop, not just a click")
        return

    cx = sum(x for x, y in points) / len(points)
    cy = sum(y for x, y in points) / len(points)

    if not angle_coverage_ok(cx, cy, points):
        show_message("Not a closed loop!", "Draw all the way around the center")
        return

    score, cx, cy, mean_r = score_circle(points)
    if mean_r < MIN_RADIUS:
        show_message("Too small!", "Draw a bigger circle")
        return

    draw_gradient_stroke(points, cx, cy, mean_r)

    ideal.goto(cx, cy - mean_r)
    ideal.pendown()
    ideal.circle(mean_r)
    ideal.penup()

    is_record = score > best_score
    if is_record:
        best_score = score
        save_best_score()
        celebrate(cx, cy, mean_r)

    text_pen.clear()
    show_center_score(score, is_record)


def canvas_to_turtle_coords(event, canvas):
    # Turtle's canvas scrollregion is already centered on (0, 0),
    # so canvasx/canvasy come back pre-shifted; only the y-axis needs flipping.
    x = canvas.canvasx(event.x)
    y = -canvas.canvasy(event.y)
    return x, y


def on_press(event):
    global drawing, points
    x, y = canvas_to_turtle_coords(event, canvas)
    pen.clear()
    ideal.clear()
    center_pen.clear()
    confetti.clear()
    points = [(x, y)]
    pen.goto(x, y)
    pen.pendown()
    drawing = True
    text_pen.clear()


def on_drag(event):
    if not drawing:
        return
    x, y = canvas_to_turtle_coords(event, canvas)
    points.append((x, y))
    pen.goto(x, y)


def on_release(_event):
    global drawing
    if not drawing:
        return
    drawing = False
    pen.penup()
    evaluate()


best_score = load_best_score()
canvas = screen.getcanvas()
canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", on_release)

draw_background_rings()
reset_round()
pulse_center_dot()

screen.mainloop()
