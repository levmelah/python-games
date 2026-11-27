from tkinter import *

root = Tk()
canvas = Canvas(root, width=400, height=250, bg="white")
canvas.pack()

canvas.create_polygon(100, 40, 150, 100, 100, 160, 50, 100, fill="lightblue")
canvas.create_polygon(280, 40, 340, 85, 315, 150, 245, 150, 220, 85, fill="gold")

root.mainloop()
