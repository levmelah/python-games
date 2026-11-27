from tkinter import *

# שערי המרה יחסית לשקל (ILS)
RATES = {
    "₪  שקל":    1.0,
    "$  דולר":  0.27,
    "€  יורו":   0.25,
    "£  פאונד":  0.21,
    "₽  רובל":   25.0,
    "₴  גריבנה": 11.0,
    "¥  יין":    40.0,
}

root = Tk()
root.title("מחשבון מטבעות")
root.resizable(False, False)
root.configure(bg="#1e1e2e")

def label(text, row, col, bold=False):
    font = ("Arial", 13, "bold") if bold else ("Arial", 13)
    Label(root, text=text, font=font, bg="#1e1e2e", fg="white").grid(
        row=row, column=col, padx=10, pady=6, sticky="w")

label("המרת מטבעות", 0, 0, bold=True)
Label(root, text="", bg="#1e1e2e").grid(row=0, column=1)

# סכום
label("סכום:", 1, 0)
amount_var = StringVar(value="1")
Entry(root, textvariable=amount_var, font=("Arial", 16, "bold"),
    return {"planet": Planet(WIDTH//2, HEIGHT//2 - 20, 140), "score": 0, "weapon": "laser", "state": "play"}


game = reset_game()le=amount_var, font=("Arial", 16, "bold"),
      width=12, bg="#2a2a3e", fg="white", insertbackground="white", bd=0).grid(
      row=1, column=1, padx=10, pady=6, ipady=6)

# מטבע מקור
label("מ:", 2, 0)
from_var = StringVar(value="שקל  🇮🇱")
OptionMenu(root, from_var, *RATES.keys()).grid(row=2, column=1, padx=10, pady=6, sticky="ew")

# מטבע יעד
label("ל:", 3, 0)
to_var = StringVar(value="יורו  🇪🇺")
OptionMenu(root, to_var, *RATES.keys()).grid(row=3, column=1, padx=10, pady=6, sticky="ew")

# תוצאה
result_var = StringVar(value="")
Label(root, textvariable=result_var, font=("Arial", 18, "bold"),
      bg="#2a2a3e", fg="#98c379", width=22, anchor="center",
      pady=10).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

# שורת מידע
rate_var = StringVar(value="")
Label(root, textvariable=rate_var, font=("Arial", 11),
      bg="#1e1e2e", fg="#888").grid(row=6, column=0, columnspan=2, pady=(0, 10))

def convert(*args):
    try:
        amount = float(amount_var.get())
        from_cur = from_var.get()
        to_cur = to_var.get()

        # המרה דרך שקל
        amount_in_ils = amount / RATES[from_cur]
        result = amount_in_ils * RATES[to_cur]

        result_str = f"{result:,.2f}".rstrip("0").rstrip(".")
        amount_str = f"{amount:,.2f}".rstrip("0").rstrip(".")

        result_var.set(f"{amount_str} {from_cur.split()[0]}  =  {result_str} {to_cur.split()[0]}")

        # שיעור המרה
        one = RATES[to_cur] / RATES[from_cur]
        one_str = f"{one:,.4f}".rstrip("0").rstrip(".")
        rate_var.set(f"1 {from_cur.split()[0]} = {one_str} {to_cur.split()[0]}")
    except:
        result_var.set("סכום לא תקין")
        rate_var.set("")

Button(root, text="המר", font=("Arial", 14, "bold"),
       bg="#61afef", fg="white", bd=0, padx=20, pady=8,
       command=convert, cursor="hand2").grid(row=4, column=0, columnspan=2, pady=8)

# עדכון אוטומטי
from_var.trace("w", convert)
to_var.trace("w", convert)
amount_var.trace("w", convert)

# עיצוב OptionMenu
for widget in root.winfo_children():
    if isinstance(widget, OptionMenu):
        widget.config(bg="#3a3a52", fg="white", font=("Arial", 12),
                      activebackground="#61afef", bd=0, highlightthickness=0)
        widget["menu"].config(bg="#3a3a52", fg="white", font=("Arial", 12))

convert()
root.mainloop()
