from turtle import *
from tkinter import *
from tkinter import filedialog, simpledialog
from tkinter.colorchooser import askcolor
import json

# Set up turtle screen
screen = Screen()
screen.setup(width=800, height=600)
screen.bgcolor("white")
screen.title("Enhanced Turtle Drawing Studio")

# Create turtle
t = Turtle()
t.speed(0)
t.pensize(1)
t.pencolor("black")
t.hideturtle()

# Global variables
current_color = "black"
current_bg = "white"
pen_size = 1
stamp_mode = False
erase_mode = False
fill_mode = True
pen_down = True
turtle_speed = 0
text_to_place = None
text_size = 12
drawing_tool = None
start_x = None
start_y = None
shape_size = 50
rainbow_mode = False
fill_color = "black"
rainbow_colors = ["red", "orange", "yellow", "green", "blue", "purple", "pink"]
rainbow_index = 0
step_size = 50
circle_stamp_mode = False

# Functions
def set_pen_size(size):
    global pen_size
    pen_size = int(size)
    t.pensize(pen_size)

def set_color(color):
    global current_color
    current_color = color
    if not erase_mode:
        t.pencolor(current_color)

def set_fill_color(color):
    global fill_color
    fill_color = color
    t.fillcolor(fill_color)

def choose_fill_color():
    color = askcolor(title="Choose Fill Color")[1]
    if color:
        set_fill_color(color)

def toggle_rainbow():
    global rainbow_mode
    rainbow_mode = not rainbow_mode

def set_shape_size(size):
    global shape_size
    shape_size = int(size)

def set_step_size(size):
    global step_size
    step_size = int(size)

def toggle_circle_stamp():
    global circle_stamp_mode
    circle_stamp_mode = not circle_stamp_mode

def toggle_fill():
    global fill_mode
    fill_mode = not fill_mode
    update_status()

def update_status():
    status = f"Color: {current_color} | Fill: {fill_color} | Size: {pen_size} | Rainbow: {'ON' if rainbow_mode else 'OFF'} | Erase: {'ON' if erase_mode else 'OFF'} | Fill mode: {'ON' if fill_mode else 'OFF'}"
    status_label.config(text=status)

def set_bg_color(color):
    global current_bg
    current_bg = color
    screen.bgcolor(current_bg)

def toggle_stamp():
    global stamp_mode
    stamp_mode = not stamp_mode
    if stamp_mode:
        t.showturtle()
    else:
        t.hideturtle()

def toggle_erase():
    global erase_mode
    erase_mode = not erase_mode
    if erase_mode:
        t.pencolor(current_bg)
    else:
        t.pencolor(current_color)
    update_status()

def pen_up():
    global pen_down
    pen_down = False
    t.penup()

def pen_down_func():
    global pen_down
    pen_down = True
    t.pendown()

def set_speed(speed):
    global turtle_speed
    turtle_speed = int(speed)
    t.speed(turtle_speed)

def draw_circle():
    if fill_mode:
        t.fillcolor(fill_color)
        t.begin_fill()
    t.circle(shape_size)
    if fill_mode:
        t.end_fill()

def draw_square():
    if fill_mode:
        t.fillcolor(fill_color)
        t.begin_fill()
    for _ in range(4):
        t.forward(shape_size * 2)
        t.right(90)
    if fill_mode:
        t.end_fill()

def draw_triangle():
    if fill_mode:
        t.fillcolor(fill_color)
        t.begin_fill()
    for _ in range(3):
        t.forward(shape_size * 2)
        t.right(120)
    if fill_mode:
        t.end_fill()

def draw_star():
    if fill_mode:
        t.fillcolor(fill_color)
        t.begin_fill()
    for _ in range(5):
        t.forward(shape_size * 2)
        t.right(144)
    if fill_mode:
        t.end_fill()

def draw_hexagon():
    if fill_mode:
        t.fillcolor(fill_color)
        t.begin_fill()
    for _ in range(6):
        t.forward(shape_size * 1.6)
        t.right(60)
    if fill_mode:
        t.end_fill()

def draw_pentagon():
    if fill_mode:
        t.fillcolor(fill_color)
        t.begin_fill()
    for _ in range(5):
        t.forward(shape_size * 1.8)
        t.right(72)
    if fill_mode:
        t.end_fill()

def draw_polygon():
    sides = simpledialog.askinteger("Polygon", "Number of sides (3-20):", minvalue=3, maxvalue=20, initialvalue=6)
    if sides:
        angle = 360 / sides
        if fill_mode:
            t.fillcolor(fill_color)
            t.begin_fill()
        for _ in range(sides):
            t.forward(shape_size * 1.2)
            t.right(angle)
        if fill_mode:
            t.end_fill()

def draw_spiral():
    colors = ["red", "orange", "yellow", "green", "blue", "purple"]
    for i in range(36):
        t.pencolor(colors[i % len(colors)])
        t.forward(i * shape_size / 10)
        t.right(20)
    t.pencolor(current_color)

def clear_drawing():
    t.clear()
    t.penup()
    t.home()
    t.pendown()

def undo_last():
    t.undo()

def go_home():
    t.penup()
    t.home()
    t.pendown()

def random_position():
    import random
    x = random.randint(-350, 350)
    y = random.randint(-250, 250)
    t.penup()
    t.goto(x, y)
    if pen_down:
        t.pendown()

def add_text():
    global text_to_place, text_size
    text = simpledialog.askstring("Add Text", "Enter text to place:")
    if text:
        size = simpledialog.askinteger("Font Size", "Enter font size (10-50):", minvalue=10, maxvalue=50, initialvalue=12)
        if size:
            text_to_place = text
            text_size = size
            t.penup()
            t.goto(-380, 160)
            t.write("Click on canvas to place text", font=("Arial", 12, "normal"))
            t.goto(-380, 180)  # clear previous if any

def choose_color():
    color = askcolor(title="Choose Color")[1]
    if color:
        set_color(color)

def draw_rectangle():
    global drawing_tool
    drawing_tool = 'rectangle'
    t.penup()
    t.goto(-380, 160)
    t.write("Click start and end for rectangle", font=("Arial", 12, "normal"))

def draw_line():
    global drawing_tool
    drawing_tool = 'line'
    t.penup()
    t.goto(-380, 160)
    t.write("Click start and end for line", font=("Arial", 12, "normal"))

def save_drawing():
    filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
    if filename:
        drawing_data = {
            "bgcolor": current_bg,
            "pencolor": current_color,
            "pensize": pen_size
        }
        with open(filename, 'w') as f:
            json.dump(drawing_data, f)

def load_drawing():
    filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if filename:
        with open(filename, 'r') as f:
            drawing_data = json.load(f)
        global current_bg, current_color, pen_size
        current_bg = drawing_data.get("bgcolor", "white")
        current_color = drawing_data.get("pencolor", "black")
        pen_size = drawing_data.get("pensize", 1)
        screen.bgcolor(current_bg)
        t.pencolor(current_color)
        t.pensize(pen_size)

# Movement functions
def turtle_fd():
    if pen_down:
        t.forward(step_size)
    else:
        t.penup()
        t.forward(step_size)
        t.pendown()

def turtle_lt():
    t.left(90)

def turtle_bc():
    if pen_down:
        t.backward(step_size)
    else:
        t.penup()
        t.backward(step_size)
        t.pendown()

def turtle_rt():
    t.right(90)

def arrow_up():
    saved = t.heading()
    t.setheading(90)
    turtle_fd()
    t.setheading(saved)

def arrow_down():
    saved = t.heading()
    t.setheading(270)
    turtle_fd()
    t.setheading(saved)

def arrow_left():
    saved = t.heading()
    t.setheading(180)
    turtle_fd()
    t.setheading(saved)

def arrow_right():
    saved = t.heading()
    t.setheading(0)
    turtle_fd()
    t.setheading(saved)

# Mouse drawing
def mouse_click(x, y):
    global text_to_place, drawing_tool, start_x, start_y
    if text_to_place:
        t.penup()
        t.goto(x, y)
        t.color(current_color)
        t.write(text_to_place, align="center", font=("Arial", text_size, "normal"))
        text_to_place = None
        # Clear the instruction
        t.goto(-380, 160)
        t.color("black")
        t.write(" " * 35, font=("Arial", 12, "normal"))
    elif drawing_tool == 'rectangle':
        if start_x is None:
            start_x, start_y = x, y
        else:
            width = x - start_x
            height = y - start_y
            t.penup()
            t.goto(start_x, start_y)
            t.pendown()
            if fill_mode:
                t.begin_fill()
            for _ in range(2):
                t.forward(width)
                t.right(90)
                t.forward(height)
                t.right(90)
            if fill_mode:
                t.end_fill()
            start_x = None
            start_y = None
            drawing_tool = None
            # Clear instruction
            t.penup()
            t.goto(-380, 160)
            t.color("black")
            t.write(" " * 35, font=("Arial", 12, "normal"))
    elif drawing_tool == 'line':
        if start_x is None:
            start_x, start_y = x, y
        else:
            t.penup()
            t.goto(start_x, start_y)
            t.pendown()
            t.goto(x, y)
            start_x = None
            start_y = None
            drawing_tool = None
            # Clear instruction
            t.penup()
            t.goto(-380, 160)
            t.color("black")
            t.write(" " * 35, font=("Arial", 12, "normal"))
    elif circle_stamp_mode:
        t.penup()
        t.goto(x, y - shape_size)
        t.pendown()
        if fill_mode:
            t.fillcolor(fill_color)
            t.begin_fill()
        t.circle(shape_size)
        if fill_mode:
            t.end_fill()
    elif stamp_mode:
        t.goto(x, y)
        t.stamp()
    else:
        t.penup()
        t.goto(x, y)
        t.pendown()

def mouse_drag(x, y):
    global rainbow_index
    if not stamp_mode:
        if rainbow_mode:
            t.pencolor(rainbow_colors[rainbow_index % len(rainbow_colors)])
            rainbow_index += 1
        t.goto(x, y)

# Keyboard shortcuts
def key_1():
    set_color("black")

def key_2():
    set_color("red")

def key_3():
    set_color("blue")

def key_4():
    set_color("green")

def key_5():
    set_color("yellow")

def key_c():
    draw_circle()

def key_s():
    draw_square()

def key_t():
    draw_triangle()

def key_star():
    draw_star()

def key_h():
    draw_hexagon()

def key_p():
    draw_pentagon()

def key_9():
    draw_polygon()

def key_0():
    draw_spiral()

def key_clear():
    clear_drawing()

def key_stamp():
    toggle_stamp()

def key_erase():
    toggle_erase()

def key_fill():
    toggle_fill()

def key_undo():
    undo_last()

def key_home():
    go_home()

def key_random():
    random_position()

# Movement keys
def key_w():
    turtle_fd()

def key_a():
    turtle_lt()

def key_s():
    turtle_bc()

def key_d():
    turtle_rt()

def key_u():
    pen_up()

def key_o():
    pen_down_func()

# Bind events
screen.onclick(mouse_click)
t.ondrag(mouse_drag)

screen.onkey(key_1, "1")
screen.onkey(key_2, "2")
screen.onkey(key_3, "3")
screen.onkey(key_4, "4")
screen.onkey(key_5, "5")
screen.onkey(key_c, "c")
screen.onkey(key_s, "s")
screen.onkey(key_t, "6")
screen.onkey(key_star, "8")
screen.onkey(key_h, "h")
screen.onkey(key_p, "p")
screen.onkey(key_9, "9")
screen.onkey(key_0, "0")
screen.onkey(key_clear, "Delete")
screen.onkey(key_stamp, "Tab")
screen.onkey(key_erase, "e")
screen.onkey(key_fill, "f")
screen.onkey(key_undo, "z")
screen.onkey(key_home, "Home")
screen.onkey(key_random, "R")
screen.onkey(key_w, "w")
screen.onkey(key_a, "a")
screen.onkey(key_s, "s")
screen.onkey(key_d, "d")
screen.onkey(key_u, "u")
screen.onkey(key_o, "o")
screen.onkey(add_text, "T")
screen.onkey(draw_rectangle, "r")
screen.onkey(draw_line, "l")
screen.onkey(toggle_rainbow, "q")
screen.onkey(arrow_up, "Up")
screen.onkey(arrow_down, "Down")
screen.onkey(arrow_left, "Left")
screen.onkey(arrow_right, "Right")
screen.onkey(toggle_circle_stamp, "i")

screen.listen()

# Instructions
t.penup()
t.goto(-380, 280)
t.write("Advanced Turtle Drawing Studio", font=("Arial", 16, "bold"))
t.goto(-380, 260)
t.write("Mouse: Click to draw, drag to draw lines", font=("Arial", 12, "normal"))
t.goto(-380, 240)
t.write("Keys: 1-5 colors, c-circle, s-square, 6-triangle, 8-star, h-hex, p-pent, 9-poly, 0-spiral", font=("Arial", 12, "normal"))
t.goto(-380, 220)
t.write("r-rectangle, l-line, T-text, w-a-s-d move, u-penup, o-pendown", font=("Arial", 12, "normal"))
t.goto(-380, 200)
t.write("f-fill, z-undo, Home-home, R-random, Tab-stamp, e-erase, Delete-clear, q-rainbow, i-circle stamp", font=("Arial", 11, "normal"))
t.goto(-380, 180)
t.write("Arrow keys: move in straight lines | w-a-s-d: move+rotate", font=("Arial", 12, "normal"))

# Tkinter window integrated with turtle
root = screen._root

# Pen size and speed
control_frame = Frame(root)
control_frame.pack(pady=5)

Label(control_frame, text="Pen Size:").grid(row=0, column=0)
size_var = IntVar(value=1)
size_scale = Scale(control_frame, from_=1, to=10, orient=HORIZONTAL, variable=size_var, command=set_pen_size)
size_scale.grid(row=0, column=1)

Label(control_frame, text="Speed:").grid(row=0, column=2)
speed_var = IntVar(value=0)
speed_scale = Scale(control_frame, from_=0, to=10, orient=HORIZONTAL, variable=speed_var, command=set_speed)
speed_scale.grid(row=0, column=3)

Label(control_frame, text="Shape Size:").grid(row=0, column=4)
shape_size_var = IntVar(value=50)
shape_scale = Scale(control_frame, from_=10, to=150, orient=HORIZONTAL, variable=shape_size_var, command=set_shape_size)
shape_scale.grid(row=0, column=5)

Label(control_frame, text="Step:").grid(row=0, column=6)
step_var = IntVar(value=50)
step_scale = Scale(control_frame, from_=5, to=200, orient=HORIZONTAL, variable=step_var, command=set_step_size)
step_scale.grid(row=0, column=7)

# Colors
color_frame = Frame(root)
color_frame.pack(pady=5)

Label(color_frame, text="Colors:").grid(row=0, column=0, columnspan=5)
colors = ["black", "red", "blue", "green", "yellow", "orange", "purple", "pink"]
for i, color in enumerate(colors):
    btn = Button(color_frame, bg=color, width=3, height=1, command=lambda c=color: set_color(c))
    btn.grid(row=(i//4)+1, column=i%4, padx=1, pady=1)

Button(color_frame, text="Picker", command=choose_color).grid(row=1, column=4, padx=1, pady=1)
Button(color_frame, text="Fill Color", command=choose_fill_color).grid(row=2, column=4, padx=1, pady=1)
Label(color_frame, text="Fill:").grid(row=2, column=0)
fill_colors = ["black", "red", "blue", "green", "yellow", "orange", "purple", "pink"]
for i, color in enumerate(fill_colors):
    btn = Button(color_frame, bg=color, width=3, height=1, command=lambda c=color: set_fill_color(c))
    btn.grid(row=(i//4)+2, column=i%4, padx=1, pady=1)

# Background
bg_frame = Frame(root)
bg_frame.pack(pady=5)

Label(bg_frame, text="Background:").grid(row=0, column=0, columnspan=4)
bg_colors = ["white", "lightblue", "lightgreen", "lightyellow", "pink", "lightgray"]
for i, color in enumerate(bg_colors):
    btn = Button(bg_frame, bg=color, width=3, height=1, command=lambda c=color: set_bg_color(c))
    btn.grid(row=(i//3)+1, column=i%3, padx=1, pady=1)

# Movement buttons
movement_frame = Frame(root)
movement_frame.pack(pady=5)

Label(movement_frame, text="Movement:").grid(row=0, column=0, columnspan=3)
btn_left = Button(movement_frame, text="Left", height=2, width=8, command=turtle_lt)
btn_left.grid(row=1, column=0, padx=2, pady=2)

btn_forward = Button(movement_frame, text="Forward", height=2, width=8, command=turtle_fd)
btn_forward.grid(row=1, column=1, padx=2, pady=2)

btn_right = Button(movement_frame, text="Right", height=2, width=8, command=turtle_rt)
btn_right.grid(row=1, column=2, padx=2, pady=2)

btn_backward = Button(movement_frame, text="Backward", height=2, width=8, command=turtle_bc)
btn_backward.grid(row=2, column=0, columnspan=3, padx=2, pady=2)

btn_penup = Button(movement_frame, text="Pen Up", height=1, width=8, command=pen_up)
btn_penup.grid(row=3, column=0, padx=2, pady=2)

btn_pendown = Button(movement_frame, text="Pen Down", height=1, width=8, command=pen_down_func)
btn_pendown.grid(row=3, column=1, padx=2, pady=2)

btn_home = Button(movement_frame, text="Home", height=1, width=8, command=go_home)
btn_home.grid(row=3, column=2, padx=2, pady=2)

# Actions
action_frame = Frame(root)
action_frame.pack(pady=5)

Button(action_frame, text="Circle", command=draw_circle).grid(row=0, column=0, padx=2)
Button(action_frame, text="Square", command=draw_square).grid(row=0, column=1, padx=2)
Button(action_frame, text="Triangle", command=draw_triangle).grid(row=0, column=2, padx=2)
Button(action_frame, text="Star", command=draw_star).grid(row=0, column=3, padx=2)
Button(action_frame, text="Hexagon", command=draw_hexagon).grid(row=0, column=4, padx=2)
Button(action_frame, text="Pentagon", command=draw_pentagon).grid(row=0, column=5, padx=2)
Button(action_frame, text="Polygon", command=draw_polygon).grid(row=0, column=6, padx=2)
Button(action_frame, text="Spiral", command=draw_spiral).grid(row=0, column=7, padx=2)
Button(action_frame, text="Rectangle", command=draw_rectangle).grid(row=1, column=0, padx=2)
Button(action_frame, text="Line", command=draw_line).grid(row=1, column=1, padx=2)
Button(action_frame, text="Text", command=add_text).grid(row=1, column=2, padx=2)
Button(action_frame, text="Fill", command=toggle_fill).grid(row=1, column=0, padx=2)
Button(action_frame, text="Clear", command=clear_drawing).grid(row=1, column=1, padx=2)
Button(action_frame, text="Undo", command=undo_last).grid(row=1, column=2, padx=2)
Button(action_frame, text="Stamp", command=toggle_stamp).grid(row=1, column=3, padx=2)
Button(action_frame, text="Erase", command=toggle_erase).grid(row=1, column=4, padx=2)
Button(action_frame, text="Random Pos", command=random_position).grid(row=1, column=5, padx=2)
Button(action_frame, text="Circle Stamp", command=toggle_circle_stamp, bg="cyan").grid(row=2, column=3, padx=2)
Button(action_frame, text="Rainbow", command=toggle_rainbow, bg="violet").grid(row=2, column=2, padx=2)
Button(action_frame, text="Save", command=save_drawing).grid(row=2, column=0, padx=2)
Button(action_frame, text="Load", command=load_drawing).grid(row=2, column=1, padx=2)

# Status bar
status_label = Label(root, text="Color: black | Fill: black | Size: 1 | Rainbow: OFF | Erase: OFF | Fill mode: ON", relief=SUNKEN, anchor="w", font=("Arial", 10))
status_label.pack(fill=X, padx=5, pady=2)

# Start the Tkinter main loop to keep the window open
root.mainloop()


