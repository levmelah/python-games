import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox

BASE_DIR = Path(__file__).resolve().parent / "arkanoid"

GAMES = [
    ("Classic Arkanoid", "arkanoid.py"),
    ("Classic Flower", "arkanoid_0.py"),
    ("Antarctic", "arkanoid_3.py"),
    ("Fish Hunter", "arkanoid_4.py"),
    ("Space Arkanoid", "arkanoid_5.py"),
    ("Tropical Arkanoid", "arkanoid_6.py"),
    ("Mouth Brick", "arkanoid_8.py"),
    ("Robot Edition", "arkanoid_9.py"),
    ("Dino Arkanoid", "arkanoid_10.py"),
]


class GameSelector(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Game Menu")
        self.geometry("860x560")
        self.configure(bg="#e9d8f4")
        self.resizable(False, False)
        self._draw_background()
        self._build_ui()

    def _draw_background(self):
        self.canvas = tk.Canvas(self, width=860, height=560, bg="#e9d8f4", highlightthickness=0)
        self.canvas.place(x=0, y=0)

        for cx, cy, r in [
            (120, 110, 90), (300, 90, 120), (520, 120, 110), (720, 100, 90),
            (200, 220, 80), (470, 210, 100), (680, 230, 95),
            (120, 340, 100), (380, 330, 120), (650, 350, 110),
        ]:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill="#f7ebf6", outline="", width=0)
            self.canvas.create_oval(cx-r*0.8, cy-r*0.7, cx+r*0.8, cy+r*0.7, fill="#f2dfe9", outline="", width=0)

        for x in range(0, 900, 80):
            self.canvas.create_rectangle(x, 0, x+40, 560, fill="#f5edf3", outline="", stipple="gray50")

        self.canvas.tag_lower("all")

    def _build_ui(self):
        title = tk.Label(
            self,
            text="Choose a game to play",
            font=("Arial", 28, "bold"),
            fg="#1f2937",
            bg="#e9d8f4",
            pady=18,
        )
        title.pack()

        subtitle = tk.Label(
            self,
            text="Pick one of the games below",
            font=("Arial", 12),
            fg="#374151",
            bg="#e9d8f4",
            pady=18,
        )
        subtitle.pack()

        button_frame = tk.Frame(self, bg="#e9d8f4")
        button_frame.pack(pady=8)

        row = 0
        col = 0
        for label, filename in GAMES:
            button = tk.Button(
                button_frame,
                text=label,
                width=22,
                height=2,
                font=("Arial", 12, "bold"),
                bg="#8b5cf6",
                fg="white",
                activebackground="#7c3aed",
                activeforeground="white",
                bd=0,
                cursor="hand2",
                relief="flat",
                padx=12,
                pady=8,
                command=lambda f=filename, n=label: self.launch_game(f, n),
            )
            button.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
            col += 1
            if col == 3:
                col = 0
                row += 1

        footer = tk.Label(
            self,
            text="Tip: select a game and it will open in a new window",
            font=("Arial", 10),
            fg="#4b5563",
            bg="#e9d8f4",
            pady=18,
        )
        footer.pack()

    def launch_game(self, filename, title):
        script_path = BASE_DIR / filename
        if not script_path.exists():
            messagebox.showerror("Error", f"File not found: {filename}")
            return

        try:
            self.withdraw()
            subprocess.Popen([sys.executable, str(script_path)], cwd=str(BASE_DIR))
            self.destroy()
        except Exception as exc:
            self.deiconify()
            messagebox.showerror("Launch failed", f"Could not open {title}\n\n{exc}")


if __name__ == "__main__":
    app = GameSelector()
    app.mainloop()
