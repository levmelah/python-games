from turtle import *

speed()


color("green")

def draw_square():
    begin_fill()
    forward(50)
    left(90)
    forward(50)
    left(90)
    forward(50)
    left(90)
    forward(50)
    left(90)
    # forward(50)
    # left(90)
    end_fill()

    penup()
    forward(100)
    pendown()

def draw_square_4_times():
    for item in range(0, 4):
        draw_square()


def go_to_start():
    penup()
    left(180)
    forward(400)
    left(90)
    forward(100)
    left(90)
    pendown()

draw_square_4_times()
go_to_start()
draw_square_4_times()
go_to_start()
draw_square_4_times()
go_to_start()
draw_square_4_times()


draw_square_4_times()
go_to_start()
draw_square_4_times()
go_to_start()
draw_square_4_times()
go_to_start()
draw_square_4_times()














mainloop()
