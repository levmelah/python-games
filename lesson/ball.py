import random
import tkinter as tk

answers = [
    "!טלחהב ,ןכ",
    ".ןכ לע םיעיבצמ םינמיסה",
    ".ןכש הארנכ",
    "!ןכ םירמוא םיבכוכה",
    ".הרקי יאדו הז",
    ".ןפוא םושב ,אל",
    ".אל םירמוא םינמיסה",
    ".בר קפס",
    ".בוש לאש ,שטשוטמ דיתעה",
    ".הז לע ךומסת לא",
    ".רחמ הסנ ...םיקותוש םיבכוכה",
    "!ירשפא טלחהב",
    "!ןכ — ץבצבמ ןירותסמה",
    ".ךב יולת לכה .ילוא",
]


def ask():
    question = entry.get().strip()
    if not question:
        answer_label.config(text="!םדוק הלאש לאש ❓", fg="#ff4444")
        return
    answer_label.config(text="...בשוח ןולבה 🔮", fg="#aaaaff")
    root.after(1500, show_answer)


def show_answer():
    answer = random.choice(answers)
    answer_label.config(text=f"✨ {answer} ✨", fg="#ffe066")
    entry.delete(0, tk.END)


root = tk.Tk()
root.title("תודיתע הזוח ןולב 🔮")
root.configure(bg="#1a0033")
root.geometry("500x400")
root.resizable(False, False)

tk.Label(root, text="🔮 תודיתע הזוח ןולב 🔮",
         font=("Arial", 20, "bold"), bg="#1a0033", fg="#cc88ff").pack(pady=20)

tk.Label(root, text=":דיתעה לע הלאש יתוא לאש",
         font=("Arial", 13), bg="#1a0033", fg="#ddbbff").pack()

entry = tk.Entry(root, font=("Arial", 14), width=35, justify="right",
                 bg="#2d0055", fg="white", insertbackground="white",
                 relief="flat", bd=8)
entry.pack(pady=15)
entry.bind("<Return>", lambda e: ask())

tk.Button(root, text="!לאש", font=("Arial", 14, "bold"),
          bg="#7700cc", fg="white", activebackground="#9900ff",
          relief="flat", padx=20, pady=8, command=ask).pack()

answer_label = tk.Label(root, text="", font=("Arial", 15, "bold"),
                        bg="#1a0033", fg="#ffe066", wraplength=440)
answer_label.pack(pady=30)

root.mainloop()
