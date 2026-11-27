from tkinter import *

root = Tk()
canvas = Canvas(root, width=400, height=250, bg="white")
canvas.pack()

rhombus  = canvas.create_polygon(100, 40, 150, 100, 100, 160, 50, 100, fill="lightblue")
pentagon = canvas.create_polygon(280, 40, 340, 85, 315, 150, 245, 150, 220, 85, fill="gold")

colors = ["lightblue", "pink", "lightgreen", "orange", "violet"]
i = [0]

def change_colors():
    i[0] = (i[0] + 1) % len(colors)
    canvas.itemconfig(rhombus,  fill=colors[i[0]])
    canvas.itemconfig(pentagon, fill=colors[(i[0] + 2) % len(colors)])

Button(root, text="שנה צבעים", command=change_colors).pack()

root.mainloop()
