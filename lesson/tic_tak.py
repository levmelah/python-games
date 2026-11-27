from turtle import *
from tkinter import *

tk = Tk()
tk.geometry("400x500")
tk.title("Turtle Control")

def turtle_fd():
    forward(100)

def turtle_lt():
    left(90)

def turtle_bc():
    backward(100)

def turtle_rt():
    right(90)

def change_color_red():
    pencolor("red")

def change_color_blue():
    pencolor("blue")

def change_color_green():
    pencolor("green")

def change_color_yellow():
    pencolor("yellow")

def change_color_black():
    pencolor("black")

rainbow_colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]
rainbow_index = 0

def change_color_rainbow():
    global rainbow_index
    pencolor(rainbow_colors[rainbow_index % len(rainbow_colors)])
    rainbow_index += 1

btn = Button(tk, text="Forward", height=2, width=10, command=turtle_fd)
btn.pack()

btn = Button(tk, text="Left", height=2, width=10, command=turtle_lt)
btn.pack()

btn = Button(tk, text="Backward", height=2, width=10, command=turtle_bc)
btn.pack()

btn = Button(tk, text="Right", height=2, width=10, command=turtle_rt)
btn.pack()

# Movement buttons row
movement_frame = Frame(tk)
movement_frame.pack()

btn_left = Button(movement_frame, text="Left", height=2, width=10, command=turtle_lt)
btn_left.grid(row=0, column=0, padx=2, pady=2)

btn_forward = Button(movement_frame, text="Forward", height=2, width=10, command=turtle_fd)
btn_forward.grid(row=0, column=1, padx=2, pady=2)

btn_right = Button(movement_frame, text="Right", height=2, width=10, command=turtle_rt)
btn_right.grid(row=0, column=2, padx=2, pady=2)

btn_backward = Button(movement_frame, text="Backward", height=2, width=10, command=turtle_bc)
btn_backward.grid(row=1, column=0, columnspan=3, padx=2, pady=2)

# Color buttons
# Color buttons
color_label = Label(tk, text="Choose Color:", font=("Arial", 12))
color_label.pack()

color_frame = Frame(tk)
color_frame.pack()

btn_red = Button(color_frame, text="Red", height=2, width=10, command=change_color_red, bg="red", fg="white")
btn_red.grid(row=0, column=0, padx=2, pady=2)

btn_blue = Button(color_frame, text="Blue", height=2, width=10, command=change_color_blue, bg="blue", fg="white")
btn_blue.grid(row=0, column=1, padx=2, pady=2)

btn_green = Button(color_frame, text="Green", height=2, width=10, command=change_color_green, bg="green", fg="white")
btn_green.grid(row=0, column=2, padx=2, pady=2)

btn_yellow = Button(color_frame, text="Yellow", height=2, width=10, command=change_color_yellow, bg="yellow", fg="black")
btn_yellow.grid(row=1, column=0, padx=2, pady=2)

btn_black = Button(color_frame, text="Black", height=2, width=10, command=change_color_black, bg="black", fg="white")
btn_black.grid(row=1, column=1, padx=2, pady=2)

btn_rainbow = Button(color_frame, text="Rainbow", height=2, width=10, command=change_color_rainbow, bg="purple", fg="white")
btn_rainbow.grid(row=1, column=2, padx=2, pady=2)

def draw_circle():
    
    circle(50)

action_frame = Frame(tk)
action_frame.pack()

btn_circle = Button(action_frame, text="Draw Circle", height=2, width=10, command=draw_circle)
btn_circle.grid(row=0, column=0, padx=2, pady=2)

def clear_drawing():
    clear()

btn_clear = Button(action_frame, text="Clear", height=2, width=10, command=clear_drawing)
btn_clear.grid(row=0, column=1, padx=2, pady=2)

def undo_last():
    undo()

btn_undo = Button(action_frame, text="Undo", height=2, width=10, command=undo_last)
btn_undo.grid(row=0, column=2, padx=2, pady=2)

mainloop()


