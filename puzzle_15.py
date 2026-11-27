from tkinter import *
import random

SIZE = 4
TILE = 100

def new_game():
    nums = list(range(1, SIZE * SIZE)) + [0]
    random.shuffle(nums)
    for i in range(SIZE * SIZE):
        board[i // SIZE][i % SIZE] = nums[i]
    draw()

def draw():
    canvas.delete("all")
    for r in range(SIZE):
        for c in range(SIZE):
            val = board[r][c]
            x, y = c * TILE, r * TILE
            if val == 0:
                canvas.create_rectangle(x, y, x + TILE, y + TILE, fill="gray90", outline="white", width=3)
            else:
                canvas.create_rectangle(x, y, x + TILE, y + TILE, fill="#4a90d9", outline="white", width=3)
                canvas.create_text(x + TILE // 2, y + TILE // 2, text=str(val), font=("Arial", 28, "bold"), fill="white")
    if check_win():
        canvas.create_text(SIZE * TILE // 2, SIZE * TILE // 2, text="ניצחת! 🎉", font=("Arial", 36, "bold"), fill="gold")

def click(event):
    c = event.x // TILE
    r = event.y // TILE
    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr][nc] == 0:
            board[nr][nc] = board[r][c]
            board[r][c] = 0
            draw()
            return

def check_win():
    nums = [board[r][c] for r in range(SIZE) for c in range(SIZE)]
    return nums == list(range(1, SIZE * SIZE)) + [0]

root = Tk()
root.title("פאזל 15")
root.resizable(False, False)

board = [[0]*SIZE for _ in range(SIZE)]

canvas = Canvas(root, width=SIZE*TILE, height=SIZE*TILE, bg="gray90")
canvas.pack()
canvas.bind("<Button-1>", click)

Button(root, text="משחק חדש", font=("Arial", 14), command=new_game).pack(fill=X, pady=5)

new_game()
root.mainloop()
