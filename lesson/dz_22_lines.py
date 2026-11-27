from tkinter import *

root = Tk()
root.title("Line Drawing Example")

canvas = Canvas(root, width=400, height=300, bg="white")
canvas.pack()

canvas.create_line(50, 80, 300, 80, width=3, fill="blue")
canvas.create_line(50, 80, 175, 220, width=3, fill="red")

root.mainloop()
